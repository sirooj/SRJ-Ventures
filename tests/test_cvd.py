"""Tests for tick-rule CVD: values, session reset, rolling, no-lookahead."""
from datetime import datetime, timezone

import polars as pl

from core.indicators.cvd import cvd_from_bars, cvd_from_ticks


def _ticks():
    base = datetime(2023, 6, 1, 12, tzinfo=timezone.utc)
    return pl.DataFrame(
        {
            "ts": [base.replace(second=s) for s in (1, 2, 3, 4)],
            "bid": [1.0, 1.1, 1.1, 1.0],
            "ask": [1.0001] * 4,
            "bid_vol": [1.0] * 4,
            "ask_vol": [1.0] * 4,
            "spread": [0.0001] * 4,
            "session": ["a", "a", "b", "b"],
        },
        schema={
            "ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
            "bid": pl.Float64, "ask": pl.Float64,
            "bid_vol": pl.Float64, "ask_vol": pl.Float64,
            "spread": pl.Float64, "session": pl.String,
        },
    )


def test_cvd_unit_values_and_session_reset():
    # carry: [0, 1, 1, -1]
    out = cvd_from_ticks(_ticks(), roll_windows=())
    assert out["cvd"].to_list() == [0, 1, 2, 1]
    out = cvd_from_ticks(_ticks(), session_col="session", roll_windows=())
    assert out["cvd"].to_list() == [0, 1, 1, 0]  # session b restarts: 1, 1-1


def test_cvd_rolling_and_volume_weight():
    # carry = [0, 1, 1, -1]; rolling-2 sums: [0, 1, 2, 0]
    out = cvd_from_ticks(_ticks(), roll_windows=(2,))
    assert out["cvd_roll_2"].to_list() == [0, 1, 2, 0]
    out = cvd_from_ticks(_ticks(), weight_col="bid_vol", roll_windows=())
    assert out["cvd"].to_list() == [0, 1, 2, 1]


def test_cvd_from_bars():
    base = datetime(2023, 6, 1, 12, tzinfo=timezone.utc)
    bars = pl.DataFrame({
        "ts": [base.replace(minute=m) for m in (0, 1, 2)],
        "delta_tick_carry": [3, -1, 2],
    }, schema={"ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
               "delta_tick_carry": pl.Int32})
    out = cvd_from_bars(bars, roll_windows=(2,))
    assert out["cvd"].to_list() == [3, 2, 4]
    assert out["cvd_roll_2"].to_list() == [3, 2, 1]


def test_cvd_no_lookahead():
    full = cvd_from_ticks(_ticks(), roll_windows=(2,))
    trunc = cvd_from_ticks(_ticks().head(2), roll_windows=(2,))
    assert full["cvd"][:2].to_list() == trunc["cvd"].to_list()
    assert full["cvd_roll_2"][:2].to_list() == trunc["cvd_roll_2"].to_list()

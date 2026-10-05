"""Tests for tick-rule deltas, 1m bars, and resampling."""
from datetime import datetime, timezone

import polars as pl
import pytest

from core.data.bars import add_tick_rule, resample_bars, ticks_to_1m

T0 = datetime(2023, 6, 1, 12, tzinfo=timezone.utc)


def _ticks():
    # Minute 12:00 — bids: 1.0, 1.1 (up), 1.1 (flat), 1.0 (down)
    # Minute 12:01 — bids: 1.0 (flat, carry -1), 1.2 (up)
    ts = [T0.replace(second=s) for s in (5, 10, 20, 40)]
    ts += [T0.replace(minute=1, second=s) for s in (5, 30)]
    return pl.DataFrame(
        {
            "ts": ts,
            "bid": [1.0, 1.1, 1.1, 1.0, 1.0, 1.2],
            "ask": [1.0002, 1.1002, 1.1002, 1.0002, 1.0002, 1.2002],
            "bid_vol": [1.0] * 6,
            "ask_vol": [2.0] * 6,
            "spread": [0.0002] * 6,
        },
        schema={
            "ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
            "bid": pl.Float64, "ask": pl.Float64,
            "bid_vol": pl.Float64, "ask_vol": pl.Float64, "spread": pl.Float64,
        },
    )


def test_tick_rule_and_carry():
    out = add_tick_rule(_ticks())
    assert out["delta_tick"].to_list() == [0, 1, 0, -1, 0, 1]
    assert out["delta_tick_carry"].to_list() == [0, 1, 1, -1, -1, 1]


def test_ticks_to_1m_ohlc_and_sums():
    bars = ticks_to_1m(_ticks())
    assert len(bars) == 2
    r0, r1 = bars.iter_rows(named=True)
    assert (r0["open"], r0["high"], r0["low"], r0["close"]) == (1.0, 1.1, 1.0, 1.0)
    assert r0["tick_count"] == 4
    assert r0["delta_tick"] == 0 and r0["delta_tick_carry"] == 1  # 0+1+1-1
    assert r1["delta_tick"] == 1 and r1["delta_tick_carry"] == 0  # -1+1
    assert r0["spread_mean"] == pytest.approx(0.0002)
    assert r0["bid_vol_sum"] == pytest.approx(4.0)


def test_ticks_to_1m_empty():
    assert len(ticks_to_1m(_ticks().clear())) == 0


def test_resample_5m():
    bars = ticks_to_1m(_ticks())
    r = resample_bars(bars, "5m")
    assert len(r) == 1
    row = r.row(0, named=True)
    assert row["open"] == 1.0 and row["close"] == 1.2
    assert row["high"] == 1.2 and row["low"] == 1.0
    assert row["tick_count"] == 6
    assert row["delta_tick_carry"] == 1


def test_resample_bad_tf():
    with pytest.raises(ValueError):
        resample_bars(ticks_to_1m(_ticks()), "2m")


def test_find_gaps_skips_weekends():
    from core.data.qa import find_gaps

    schema = {"ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
              "open": pl.Float64, "high": pl.Float64, "low": pl.Float64,
              "close": pl.Float64}
    # Fri 2026-02-20 21:59 → Mon 00:00 UTC: normal weekend, not a gap.
    # Plus a genuine 10-min hole on Monday.
    bars = pl.DataFrame(
        {"ts": [datetime(2026, 2, 20, 21, 59, tzinfo=timezone.utc),
                datetime(2026, 2, 23, 0, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 23, 0, 10, tzinfo=timezone.utc)],
         "open": [1.0] * 3, "high": [1.0] * 3,
         "low": [1.0] * 3, "close": [1.0] * 3},
        schema=schema,
    )
    gaps = find_gaps(bars)
    assert len(gaps) == 1
    assert gaps["gap_minutes"][0] == pytest.approx(10.0)

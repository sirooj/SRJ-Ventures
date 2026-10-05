"""Hand-built equity-path tests for the challenge simulator (issue #4)."""
import dataclasses
from datetime import datetime, timedelta, timezone

import polars as pl
import pytest

from core.data.paths import repo_file
from core.propfirm.rules import DailyLoss, load_rules
from core.propfirm.sim import AttemptResult, run_attempt

UTC = timezone.utc
RULES = repo_file("docs", "propfirm_rules")
R2 = load_rules(RULES / "ftmo_2step_standard.yaml")
R1 = load_rules(RULES / "ftmo_1step.yaml")


def _bars(spec):
    """spec: list of (day_offset, minute, low, high). Days start 2026-01-05 (Mon)."""
    base = datetime(2026, 1, 5, tzinfo=UTC)
    rows = [(base + timedelta(days=d, minutes=m), lo, hi) for d, m, lo, hi in spec]
    return pl.DataFrame(
        {"ts": [r[0] for r in rows], "low": [r[1] for r in rows],
         "high": [r[2] for r in rows],
         "spread_max": [0.0] * len(rows)},
        schema={"ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
                "low": pl.Float64, "high": pl.Float64, "spread_max": pl.Float64},
    )


def _t(day, m_in, m_out, entry, exit, side=1, size=1000):
    base = datetime(2026, 1, 5, tzinfo=UTC) + timedelta(days=day)
    return {"entry_ts": base + timedelta(minutes=m_in),
            "exit_ts": base + timedelta(minutes=m_out),
            "symbol": "EURUSD", "side": side, "size": size,
            "entry_price": entry, "exit_price": exit,
            "multiplier": 1.0, "costs": 0.0}


def test_intraday_dip_breaches_daily_despite_recovery():
    bars = _bars([(0, 0, 100, 101), (0, 1, 100, 101), (0, 2, 94, 95),
                  (0, 3, 101, 102), (0, 4, 101, 102)])
    out: AttemptResult = run_attempt([_t(0, 1, 3, 100, 101)], bars, R2, 100_000)
    assert not out.passed and out.breach_rule == "daily_loss"
    assert "00:02" in (out.breach_ts or "")


def test_static_max_binds_after_realized_losses():
    bars = _bars([(0, 0, 100, 101), (0, 1, 100, 101), (0, 2, 96, 97),
                  (0, 3, 94, 95), (0, 4, 94, 95),
                  (1, 0, 94, 95), (1, 1, 94, 95), (1, 2, 89.5, 90.5),
                  (1, 3, 95, 96), (1, 4, 95, 96)])
    trades = [_t(0, 1, 3, 100, 94), _t(1, 1, 3, 94, 95)]
    out = run_attempt(trades, bars, R2, 100_000)
    assert not out.passed and out.breach_rule == "max_loss"


def test_eod_ratchet_rises():
    wide = dataclasses.replace(
        R1, daily_loss=DailyLoss(50.0, "initial", "initial", "equity",
                                 "Europe/Prague", "00:00"))
    bars = _bars([(0, 0, 100, 101), (0, 1, 100, 101), (0, 2, 99, 100),
                  (0, 3, 106, 107), (0, 4, 106, 107),
                  (1, 0, 106, 107), (1, 1, 106, 107), (1, 2, 95.5, 96.5),
                  (1, 3, 104, 105), (1, 4, 104, 105)])
    trades = [_t(0, 1, 3, 100, 106), _t(1, 1, 3, 106, 104)]
    out = run_attempt(trades, bars, wide, 100_000)
    assert not out.passed and out.breach_rule == "max_loss"


def test_best_day_failure():
    bars = _bars([(0, m, 100, 105) for m in range(5)]
                 + [(1, m, 100, 105) for m in range(5)])
    trades = [_t(0, 1, 3, 100, 104), _t(1, 1, 3, 100, 101)]
    out = run_attempt(trades, bars, R1, 100_000)
    assert not out.passed and out.breach_rule == "consistency"
    assert out.best_day_ratio == pytest.approx(0.8)


def test_minimum_days_gate():
    bars = _bars([(0, m, 100, 110) for m in range(5)]
                 + [(1, m, 100, 110) for m in range(5)])
    out = run_attempt([_t(0, 1, 3, 100, 106), _t(1, 1, 3, 100, 104)],
                      bars, R2, 100_000)
    assert not out.passed and out.breach_rule is None
    assert out.trading_days == 2


def test_min_hold_null_is_na_and_violation_fails():
    bars = _bars([(0, m, 100, 101) for m in range(5)])
    out = run_attempt([_t(0, 1, 3, 100, 100)], bars, R2, 100_000)
    assert out.min_hold == "n/a"
    strict = dataclasses.replace(
        R2, trading_limits=dataclasses.replace(
            R2.trading_limits, min_hold_seconds=300))
    out = run_attempt([_t(0, 1, 2, 100, 100)], bars, strict, 100_000)
    assert out.min_hold == "violation" and out.breach_rule == "min_hold"

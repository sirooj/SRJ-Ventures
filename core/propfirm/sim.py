"""Challenge simulator v0: replay trades on 1m bid bars, adverse-extreme marking.

Method (D-004, D-010): every minute, open trades are marked at the adverse
extreme — longs at bid ``low``, shorts at bid ``high`` + ``spread_max`` (ask
high proxy). Breach = the lowest equity touch (``<=`` floor), even momentary.
Each rule is evaluated in its own reset timezone. Rules flagged
``modeled_in_sim: false`` are reported as ``unmodeled``, never as passed; a
null firm limit is reported as ``n/a``.

Trade P/L is computed in account currency as
``side × (exit − entry) × size × multiplier − costs``; the caller supplies
``multiplier`` (quote→account conversion × contract size) and per-trade costs.
The trailing ratchet is owned here: the running trail value is seeded with
``initial`` and never falls (amendment to #4).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import polars as pl

from .rules import FirmRules, daily_floor, max_floor

UNMODELED_ALWAYS = ("device_ip",)  # never modelable from trades + bars


@dataclass
class AttemptResult:
    passed: bool
    breach_rule: str | None
    breach_ts: str | None
    days_to_pass: int | None
    trading_days: int
    profitable_days: int
    best_day_ratio: float | None
    unmodeled: list[str]
    min_hold: str  # "ok" | "violation" | "n/a"


def _reset_date(ts: datetime, tz_name: str) -> str:
    tz = ZoneInfo(tz_name) if not tz_name.startswith("UTC") else timezone.utc
    if tz_name.startswith("UTC") and tz_name != "UTC":
        off = int(tz_name[3:])
        tz = timezone(timedelta(hours=off))
    return str(ts.astimezone(tz).date())


def _day_pnl_by_exit(trades: list[dict], tz_name: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for t in trades:
        d = _reset_date(t["exit_ts"], tz_name)
        pnl = t["side"] * (t["exit_price"] - t["entry_price"]) * t["size"] * t.get(
            "multiplier", 1.0) - t.get("costs", 0.0)
        out[d] = out.get(d, 0.0) + pnl
    return out


def run_attempt(
    trades: list[dict],
    bars_1m: pl.DataFrame,
    rules: FirmRules,
    initial: float,
    phase: int = 0,
) -> AttemptResult:
    """Replay one challenge phase over 1m bars. See module docstring."""
    spec = rules.phases[phase]
    target = initial * (1 + spec.profit_target_pct / 100)
    rtz = rules.daily_loss.reset_tz

    realized = [
        (t, t["side"] * (t["exit_price"] - t["entry_price"]) * t["size"]
         * t.get("multiplier", 1.0) - t.get("costs", 0.0))
        for t in trades
    ]
    day_pnl = _day_pnl_by_exit(trades, rtz)
    trading_days = len({ _reset_date(t["entry_ts"], rtz) for t in trades })

    def _ratio(closed_before: datetime | None = None) -> float | None:
        by_day: dict[str, float] = {}
        for t, v in realized:
            if closed_before is not None and t["exit_ts"] > closed_before:
                continue
            d = _reset_date(t["exit_ts"], rtz)
            by_day[d] = by_day.get(d, 0.0) + v
        pos = [v for v in by_day.values() if v > 0]
        return max(pos) / sum(pos) if pos else None

    best_ratio = _ratio()
    pos_days = sorted(d for d, v in day_pnl.items() if v > 0)

    def _consistent(ratio: float | None) -> bool:
        cap = rules.consistency.best_day_max_pct_of_positive_days
        return not (cap is not None and ratio is not None and ratio * 100 > cap)

    # min-hold: null firm limit → n/a (never "passed").
    min_hold_spec = rules.trading_limits.min_hold_seconds
    if min_hold_spec is None:
        min_hold = "n/a"
    else:
        bad = [t for t in trades
               if (t["exit_ts"] - t["entry_ts"]).total_seconds() < min_hold_spec]
        min_hold = "violation" if bad else "ok"

    unmodeled = sorted([k for k, v in rules.modeled_in_sim.items() if not v]
                       + list(UNMODELED_ALWAYS))

    # Minute walk: balance (realized) + adverse-extreme floating.
    b = bars_1m.sort("ts")
    ts_list = b["ts"].to_list()
    lows = b["low"].to_list()
    highs = [h + s for h, s in zip(b["high"].to_list(), b["spread_max"].to_list())]

    balance = initial
    cur_day: str | None = None
    ref_balance = initial   # daily reference (reset)
    ref_equity = initial    # for reset_max_balance_equity
    trail = initial         # ratchet seed (never falls)
    trail_eq = initial      # running max equity (highest_equity mode)
    day_floor = daily_floor(rules, initial, initial)

    def max_ref() -> float:
        if rules.max_loss.type == "static":
            return initial
        return trail
    closed: set[int] = set()
    passed = False
    breach_rule: str | None = None
    breach_ts: str | None = None
    pass_day: str | None = None

    for ts, lo, hi in zip(ts_list, lows, highs):
        day = _reset_date(ts, rtz)
        if day != cur_day:
            # Realize trades closed before this reset (attribute at exit).
            for i, t in enumerate(trades):
                if i in closed or t["exit_ts"] >= ts:
                    continue
                balance += (t["side"] * (t["exit_price"] - t["entry_price"])
                            * t["size"] * t.get("multiplier", 1.0)
                            - t.get("costs", 0.0))
                closed.add(i)
            # New reset: reference = reset balance (or max w/ equity).
            ref_balance = balance
            ref_equity = max(ref_equity, balance)
            ref = (max(ref_balance, ref_equity)
                   if rules.daily_loss.reference == "reset_max_balance_equity"
                   else (ref_balance if rules.daily_loss.reference == "reset_balance"
                         else initial))
            day_floor = daily_floor(rules, initial, ref)
            if rules.max_loss.type != "static":
                trail = max(trail, ref_balance if
                            rules.max_loss.trail_reference == "highest_reset_balance"
                            else trail_eq)
            cur_day = day
        # Floating at adverse extreme over trades open at this minute.
        floating = 0.0
        any_open = False
        for t in trades:
            if t["entry_ts"] <= ts < t["exit_ts"]:
                any_open = True
                mark = lo if t["side"] > 0 else hi
                floating += (t["side"] * (mark - t["entry_price"])
                             * t["size"] * t.get("multiplier", 1.0))
        equity = balance + floating
        trail_eq = max(trail_eq, equity)
        if rules.max_loss.type != "static":
            if rules.max_loss.trail_reference == "highest_equity":
                trail = max(trail, trail_eq)
            # highest_reset_balance ratchets at resets (see day rollover above)
        # Attribution (LuxAlgo rule-semantics): falling equity crosses the
        # HIGHER floor first; report that rule. Tie → daily_loss.
        mfloor = max_floor(rules, initial, max_ref())
        if equity <= day_floor or equity <= mfloor:
            if mfloor > day_floor:
                breach_rule, breach_ts = "max_loss", str(ts)
            else:
                breach_rule, breach_ts = "daily_loss", str(ts)
            break
        if equity >= target and (not spec.target_requires_flat or not any_open):
            # min-days gates the pass; keep walking if unmet.
            if trading_days >= spec.min_trading_days and \
                    len(pos_days) >= spec.min_profitable_days:
                if not _consistent(_ratio(ts)):
                    breach_rule, breach_ts = "consistency", str(ts)
                    break
                passed = True
                pass_day = day
                break

    # Settle any trades still open at the end (conservative: close at last bar).
    for i, t in enumerate(trades):
        if i not in closed:
            balance += (t["side"] * (t["exit_price"] - t["entry_price"])
                        * t["size"] * t.get("multiplier", 1.0) - t.get("costs", 0.0))
            closed.add(i)

    if not passed and breach_rule is None and min_hold == "violation":
        breach_rule, breach_ts = "min_hold", None
    if (not passed and breach_rule is None
            and not _consistent(best_ratio)):
        breach_rule, breach_ts = "consistency", None

    days_to_pass = None
    if passed and pass_day is not None and ts_list:
        d0 = datetime.fromisoformat(_reset_date(ts_list[0], rtz))
        d1 = datetime.fromisoformat(pass_day)
        days_to_pass = (d1.date() - d0.date()).days + 1

    return AttemptResult(
        passed=passed, breach_rule=breach_rule, breach_ts=breach_ts,
        days_to_pass=days_to_pass, trading_days=trading_days,
        profitable_days=len(pos_days), best_day_ratio=best_ratio,
        unmodeled=unmodeled, min_hold=min_hold)


def block_bootstrap(trades: list[dict], seed: int = 42, block_days: int = 5,
                    n_paths: int = 200) -> list[list[dict]]:
    """Resample consecutive day-blocks of trades (daily blocks preserve streaks).

    Days are keyed by exit date (UTC); blocks wrap around the calendar.
    """
    import random

    rng = random.Random(seed)
    by_day: dict[str, list[dict]] = {}
    for t in trades:
        by_day.setdefault(str(t["exit_ts"].date()), []).append(t)
    days = sorted(by_day)
    if not days:
        return [[] for _ in range(n_paths)]
    paths = []
    for _ in range(n_paths):
        seq: list[dict] = []
        while len({str(t["exit_ts"].date()) for t in seq}) < len(days):
            start = rng.randrange(len(days))
            for k in range(block_days):
                seq.extend(by_day[days[(start + k) % len(days)]])
                if len({str(t["exit_ts"].date()) for t in seq}) >= len(days):
                    break
        paths.append(seq)
    return paths


def _stagnation(path_trades: list[dict]) -> int:
    """Longest run of days without a new cumulative-PnL high (LuxAlgo metric)."""
    by_day: dict[str, float] = {}
    for t in path_trades:
        d = str(t["exit_ts"].date())
        by_day[d] = by_day.get(d, 0.0) + (
            t["side"] * (t["exit_price"] - t["entry_price"]) * t["size"]
            * t.get("multiplier", 1.0) - t.get("costs", 0.0))
    eq = high = 0.0
    run = worst = 0
    for d in sorted(by_day):
        eq += by_day[d]
        if eq > high:
            high, run = eq, 0
        else:
            run += 1
            worst = max(worst, run)
    return worst


def monte_carlo(trades: list[dict], bars_1m: pl.DataFrame, rules: FirmRules,
                initial: float, fee: float, seed: int = 42,
                n_paths: int = 200) -> dict:
    """Seeded MC over bootstrapped day-blocks; sequential phases; EV per fee."""
    from collections import Counter

    paths = block_bootstrap(trades, seed=seed, n_paths=n_paths)
    p1 = [run_attempt(p, bars_1m, rules, initial, phase=0) for p in paths]
    ok1 = [r for r in p1 if r.passed]
    p2 = [run_attempt(p, bars_1m, rules, initial, phase=1)
          for p, r in zip(paths, p1) if r.passed] if len(rules.phases) > 1 else []
    ok2 = [r for r in p2 if r.passed]
    breaches = Counter(r.breach_rule for r in p1 if r.breach_rule)
    finals = []
    for p, r in zip(paths, p1):
        if r.passed:
            finals.append(sum(
                t["side"] * (t["exit_price"] - t["entry_price"]) * t["size"]
                * t.get("multiplier", 1.0) - t.get("costs", 0.0) for t in p))
    first_payout = (rules.payout.split_pct or 0) / 100 * (
        sorted(finals)[len(finals) // 2] if finals else 0.0)
    p_all = len(ok2) / n_paths if p2 else len(ok1) / n_paths
    days = sorted(r.days_to_pass for r in ok1 if r.days_to_pass)
    stagn = sorted(_stagnation(p) for p in paths)
    return {
        "n_paths": n_paths,
        "p_pass_phase1": len(ok1) / n_paths,
        "p_pass_all": p_all,
        "median_days_to_pass": (days[len(days) // 2] if days else None),
        "median_stagnation_days": stagn[len(stagn) // 2],
        "p_breach_by_rule": {k: v / n_paths for k, v in sorted(breaches.items())},
        "expected_first_payout": first_payout,
        "ev_per_fee": p_all * first_payout - fee,
        "fee": fee,
    }

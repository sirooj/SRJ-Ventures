"""Typed loader + validation for prop-firm rulebooks.

Schema: ``docs/propfirm_rules/schema.md``. ``load_rules(path)`` returns frozen
dataclasses; any structural problem raises ``RuleError`` naming file + field.

Loss semantics (D-017): a daily-loss floor is ``reference − pct of base`` where
``reference`` ∈ initial / reset_balance / reset_max_balance_equity and the
allowance base (``pct_of``) ∈ initial / reference. A trailing max-loss floor
rises with ``trail_reference`` and optionally locks at ``initial``. The pure
helpers ``daily_floor`` / ``max_floor`` pin this so the simulator (B2) can't
reinterpret it; the running-maximum ratchet is the caller's job.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

PCT_OF = {"initial", "reference"}
REFERENCE = {"initial", "reset_balance", "reset_max_balance_equity"}
MEASURED_ON = {"equity", "balance"}
MAX_TYPES = {"static", "eod_trailing", "intraday_trailing"}
TRAIL_REFERENCE = {"highest_reset_balance", "highest_equity"}
LOCK_AT = {"initial"}
MODELED_KEYS = {"daily_loss", "max_loss", "consistency", "news",
                "min_hold_seconds", "max_requests_per_day", "weekend_holding",
                "payout", "fees"}

TOP_FIELDS = {"firm", "program", "verify_before_purchase", "phases", "daily_loss",
              "max_loss", "consistency", "news", "trading_limits", "payout",
              "fees", "banned_behaviors", "sources", "modeled_in_sim", "notes"}
PHASE_FIELDS = {"profit_target_pct", "min_trading_days", "min_profitable_days",
                "time_limit_days", "target_requires_flat"}
DAILY_FIELDS = {"pct", "pct_of", "reference", "measured_on", "reset_tz", "reset_time"}
MAX_FIELDS = {"pct", "pct_of", "type", "trail_reference", "lock_at"}
CONSISTENCY_FIELDS = {"best_day_max_pct_of_positive_days"}
NEWS_FIELDS = {"evaluation_restricted", "funded_window_min"}
LIMITS_FIELDS = {"weekend_holding", "max_requests_per_day", "min_hold_seconds"}
PAYOUT_FIELDS = {"split_pct", "split_max_pct", "first_after_days", "cycle_days"}
FEES_FIELDS = {"fee_by_size", "fee_refund"}
SOURCE_FIELDS = {"url", "accessed"}

_TZ_RE = re.compile(r"^UTC([+-]\d{1,2})?$")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


@dataclass(frozen=True)
class Phase:
    profit_target_pct: float
    min_trading_days: int = 0
    min_profitable_days: int = 0
    time_limit_days: int | None = None
    target_requires_flat: bool = False


@dataclass(frozen=True)
class DailyLoss:
    pct: float
    pct_of: str
    reference: str
    measured_on: str
    reset_tz: str
    reset_time: str


@dataclass(frozen=True)
class MaxLoss:
    pct: float
    pct_of: str
    type: str
    trail_reference: str | None = None
    lock_at: str | None = None


@dataclass(frozen=True)
class Consistency:
    best_day_max_pct_of_positive_days: float | None = None


@dataclass(frozen=True)
class News:
    evaluation_restricted: bool = False
    funded_window_min: int = 0


@dataclass(frozen=True)
class TradingLimits:
    weekend_holding: bool | None = None
    max_requests_per_day: int | None = None
    min_hold_seconds: int | None = None


@dataclass(frozen=True)
class Payout:
    split_pct: float | None = None
    split_max_pct: float | None = None
    first_after_days: int | None = None
    cycle_days: int | None = None


@dataclass(frozen=True)
class Fees:
    fee_by_size: dict | None = None
    fee_refund: bool | None = None


@dataclass(frozen=True)
class Source:
    url: str
    accessed: str


@dataclass(frozen=True)
class FirmRules:
    firm: str
    program: str
    verify_before_purchase: bool
    phases: tuple[Phase, ...]
    daily_loss: DailyLoss
    max_loss: MaxLoss
    consistency: Consistency
    news: News
    trading_limits: TradingLimits
    payout: Payout
    fees: Fees
    banned_behaviors: tuple[str, ...] | None
    sources: tuple[Source, ...]
    modeled_in_sim: dict[str, bool]
    notes: tuple[str, ...]


class RuleError(ValueError):
    """Validation failure naming the file and field."""


def _check_keys(mapping: dict, allowed: set[str], where: str) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        raise RuleError(f"{where}: unknown keys {sorted(unknown)}")


def _req(mapping: dict, key: str, where: str):
    if not isinstance(mapping, dict) or key not in mapping:
        raise RuleError(f"{where}: missing required field '{key}'")
    return mapping[key]


def _pct(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuleError(f"{where}: percentage must be a number, got {value!r}")
    if not 0 < value <= 100:
        raise RuleError(f"{where}: percentage out of (0, 100]: {value!r}")
    return float(value)


def _tz(value, where: str) -> str:
    if not isinstance(value, str):
        raise RuleError(f"{where}: reset_tz must be a string, got {value!r}")
    if _TZ_RE.match(value) or value == "UTC":
        return value
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError:
        raise RuleError(f"{where}: unknown timezone {value!r}") from None
    return value


def daily_floor(rules: FirmRules, initial: float, reference_value: float) -> float:
    """Breach floor for the daily-loss rule (pure; D-017).

    ``reference_value`` is the rule's reference level (reset balance, or the
    max of balance/equity where applicable); the allowance is ``pct`` of
    ``initial`` or of the reference, per ``pct_of``.
    """
    base = initial if rules.daily_loss.pct_of == "initial" else reference_value
    return reference_value - rules.daily_loss.pct / 100 * base


def max_floor(rules: FirmRules, initial: float, trail_value: float) -> float:
    """Breach floor for the max-loss rule (pure; D-017).

    ``trail_value`` is the running maximum of ``trail_reference`` — the caller
    keeps the ratchet (it never falls). For ``static`` the trail is ignored.
    With ``lock_at == "initial"`` the floor never rises above ``initial``.
    """
    m = rules.max_loss
    ref = initial if m.type == "static" else trail_value
    base = initial if m.pct_of == "initial" else trail_value
    floor = ref - m.pct / 100 * base
    if m.lock_at == "initial":
        floor = min(floor, initial)
    return floor


def load_rules(path: str | Path) -> FirmRules:
    """Load and validate one rulebook YAML. Raises ``RuleError`` on problems."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise RuleError(f"{path}: top level must be a mapping")
    w = str(path)
    _check_keys(raw, TOP_FIELDS, w)

    firm = _req(raw, "firm", w)
    program = _req(raw, "program", w)
    if not firm or not program:
        raise RuleError(f"{w}: 'firm' and 'program' must be non-empty")
    if "verify_before_purchase" not in raw or not isinstance(
            raw["verify_before_purchase"], bool):
        raise RuleError(f"{w}: 'verify_before_purchase' bool flag is required")

    phases = []
    for i, p in enumerate(_req(raw, "phases", w)):
        pw = f"{w}.phases[{i}]"
        if not isinstance(p, dict):
            raise RuleError(f"{pw}: must be a mapping")
        _check_keys(p, PHASE_FIELDS, pw)
        for k in ("min_trading_days", "min_profitable_days"):
            if k in p and (not isinstance(p[k], int) or p[k] < 0):
                raise RuleError(f"{pw}.{k}: must be an int >= 0")
        tl = p.get("time_limit_days")
        if tl is not None and (not isinstance(tl, int) or tl <= 0):
            raise RuleError(f"{pw}.time_limit_days: positive int or null")
        phases.append(Phase(
            profit_target_pct=_pct(_req(p, "profit_target_pct", pw), pw),
            min_trading_days=p.get("min_trading_days", 0),
            min_profitable_days=p.get("min_profitable_days", 0),
            time_limit_days=tl,
            target_requires_flat=bool(p.get("target_requires_flat", False)),
        ))
    if not phases:
        raise RuleError(f"{w}: at least one phase is required")

    d = _req(raw, "daily_loss", w)
    dw = f"{w}.daily_loss"
    _check_keys(d, DAILY_FIELDS, dw)
    pct_of = _req(d, "pct_of", dw)
    reference = _req(d, "reference", dw)
    if pct_of not in PCT_OF:
        raise RuleError(f"{dw}.pct_of: unknown {pct_of!r}")
    if reference not in REFERENCE:
        raise RuleError(f"{dw}.reference: unknown {reference!r}")
    daily = DailyLoss(
        pct=_pct(_req(d, "pct", dw), dw),
        pct_of=pct_of, reference=reference,
        measured_on=_req(d, "measured_on", dw),
        reset_tz=_tz(_req(d, "reset_tz", dw), dw),
        reset_time=_req(d, "reset_time", dw),
    )
    if daily.measured_on not in MEASURED_ON:
        raise RuleError(f"{dw}.measured_on: unknown {daily.measured_on!r}")
    if not _TIME_RE.match(daily.reset_time):
        raise RuleError(f"{dw}.reset_time: want HH:MM, got {daily.reset_time!r}")

    m = _req(raw, "max_loss", w)
    mw = f"{w}.max_loss"
    _check_keys(m, MAX_FIELDS, mw)
    m_pct_of = m.get("pct_of", "initial")
    if m_pct_of not in PCT_OF:
        raise RuleError(f"{mw}.pct_of: unknown {m_pct_of!r}")
    trail_reference = m.get("trail_reference")
    if trail_reference is not None and trail_reference not in TRAIL_REFERENCE:
        raise RuleError(f"{mw}.trail_reference: unknown {trail_reference!r}")
    lock_at = m.get("lock_at")
    if lock_at is not None and lock_at not in LOCK_AT:
        raise RuleError(f"{mw}.lock_at: unknown {lock_at!r}")
    maxloss = MaxLoss(
        pct=_pct(_req(m, "pct", mw), mw),
        pct_of=m_pct_of,
        type=_req(m, "type", mw),
        trail_reference=trail_reference,
        lock_at=lock_at,
    )
    if maxloss.type not in MAX_TYPES:
        raise RuleError(f"{mw}.type: unknown {maxloss.type!r}")

    c = raw.get("consistency", {})
    _check_keys(c, CONSISTENCY_FIELDS, f"{w}.consistency")
    bdp = c.get("best_day_max_pct_of_positive_days")
    consistency = Consistency(
        best_day_max_pct_of_positive_days=None if bdp is None else _pct(
            bdp, f"{w}.consistency"))

    n = raw.get("news", {})
    _check_keys(n, NEWS_FIELDS, f"{w}.news")
    fwm = n.get("funded_window_min", 0)
    if isinstance(fwm, bool) or not isinstance(fwm, int) or fwm < 0:
        raise RuleError(f"{w}.news.funded_window_min: int >= 0 required")
    news = News(bool(n.get("evaluation_restricted", False)), fwm)

    t = raw.get("trading_limits", {})
    _check_keys(t, LIMITS_FIELDS, f"{w}.trading_limits")
    for k in ("weekend_holding",):
        if t.get(k) is not None and not isinstance(t[k], bool):
            raise RuleError(f"{w}.trading_limits.{k}: bool or null required")
    for k in ("max_requests_per_day", "min_hold_seconds"):
        v = t.get(k)
        if v is not None and (isinstance(v, bool) or not isinstance(v, int)
                              or v <= 0):
            raise RuleError(f"{w}.trading_limits.{k}: int > 0 or null required")
    limits = TradingLimits(t.get("weekend_holding"), t.get("max_requests_per_day"),
                           t.get("min_hold_seconds"))

    p = raw.get("payout", {})
    _check_keys(p, PAYOUT_FIELDS, f"{w}.payout")
    payout = Payout(p.get("split_pct"), p.get("split_max_pct"),
                    p.get("first_after_days"), p.get("cycle_days"))
    for name in ("split_pct", "split_max_pct"):
        v = getattr(payout, name)
        if v is not None:
            _pct(v, f"{w}.payout.{name}")

    f = raw.get("fees", {})
    _check_keys(f, FEES_FIELDS, f"{w}.fees")
    fees = Fees(f.get("fee_by_size"), f.get("fee_refund"))

    banned = raw.get("banned_behaviors")
    sources = _req(raw, "sources", w)
    if not sources:
        raise RuleError(f"{w}: at least one source is required")
    srcs = []
    for i, s in enumerate(sources):
        _check_keys(s, SOURCE_FIELDS, f"{w}.sources[{i}]")
        url = _req(s, "url", f"{w}.sources[{i}]")
        if not str(url).startswith("http"):
            raise RuleError(f"{w}.sources[{i}].url: want http(s), got {url!r}")
        srcs.append(Source(url, str(s.get("accessed", ""))))

    modeled = raw.get("modeled_in_sim", {})
    unknown = set(modeled) - MODELED_KEYS
    if unknown:
        raise RuleError(f"{w}.modeled_in_sim: unknown keys {sorted(unknown)}")
    if any(not isinstance(v, bool) for v in modeled.values()):
        raise RuleError(f"{w}.modeled_in_sim: all values must be bool")
    # Missing keys default to false: never reported as passed (D-017).
    modeled_full = {k: bool(modeled.get(k, False)) for k in MODELED_KEYS}

    return FirmRules(
        firm=str(firm), program=str(program),
        verify_before_purchase=bool(raw["verify_before_purchase"]),
        phases=tuple(phases), daily_loss=daily, max_loss=maxloss,
        consistency=consistency, news=news, trading_limits=limits,
        payout=payout, fees=fees,
        banned_behaviors=None if banned is None else tuple(banned),
        sources=tuple(srcs), modeled_in_sim=modeled_full,
        notes=tuple(raw.get("notes", [])),
    )

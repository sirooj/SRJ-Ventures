"""Typed loader + validation for prop-firm rulebooks.

Schema: ``docs/propfirm_rules/schema.md``. ``load_rules(path)`` returns frozen
dataclasses; any structural problem raises ``ValueError`` naming file + field.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

DAILY_BASIS = {"initial", "prior_day_balance", "prior_day_max_balance_equity"}
MEASURED_ON = {"equity", "balance"}
MAX_TYPES = {"static", "eod_trailing", "intraday_trailing"}
MODELED_KEYS = {"daily_loss", "max_loss", "consistency", "news",
                "min_hold_seconds", "max_requests_per_day", "weekend_holding",
                "payout", "fees"}
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
    basis: str
    measured_on: str
    reset_tz: str
    reset_time: str


@dataclass(frozen=True)
class MaxLoss:
    pct: float
    type: str
    trail_basis: str | None = None
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


def load_rules(path: str | Path) -> FirmRules:
    """Load and validate one rulebook YAML. Raises ``RuleError`` on problems."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise RuleError(f"{path}: top level must be a mapping")
    w = str(path)

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
    daily = DailyLoss(
        pct=_pct(_req(d, "pct", f"{w}.daily_loss"), f"{w}.daily_loss"),
        basis=_req(d, "basis", f"{w}.daily_loss"),
        measured_on=_req(d, "measured_on", f"{w}.daily_loss"),
        reset_tz=_tz(_req(d, "reset_tz", f"{w}.daily_loss"), f"{w}.daily_loss"),
        reset_time=_req(d, "reset_time", f"{w}.daily_loss"),
    )
    if daily.basis not in DAILY_BASIS:
        raise RuleError(f"{w}.daily_loss.basis: unknown {daily.basis!r}")
    if daily.measured_on not in MEASURED_ON:
        raise RuleError(f"{w}.daily_loss.measured_on: unknown {daily.measured_on!r}")
    if not _TIME_RE.match(daily.reset_time):
        raise RuleError(f"{w}.daily_loss.reset_time: want HH:MM, "
                        f"got {daily.reset_time!r}")

    m = _req(raw, "max_loss", w)
    maxloss = MaxLoss(
        pct=_pct(_req(m, "pct", f"{w}.max_loss"), f"{w}.max_loss"),
        type=_req(m, "type", f"{w}.max_loss"),
        trail_basis=m.get("trail_basis"),
        lock_at=m.get("lock_at"),
    )
    if maxloss.type not in MAX_TYPES:
        raise RuleError(f"{w}.max_loss.type: unknown {maxloss.type!r}")

    c = raw.get("consistency", {})
    bdp = c.get("best_day_max_pct_of_positive_days")
    consistency = Consistency(
        best_day_max_pct_of_positive_days=None if bdp is None else _pct(
            bdp, f"{w}.consistency"))

    n = raw.get("news", {})
    news = News(bool(n.get("evaluation_restricted", False)),
                int(n.get("funded_window_min", 0)))

    t = raw.get("trading_limits", {})
    limits = TradingLimits(t.get("weekend_holding"), t.get("max_requests_per_day"),
                           t.get("min_hold_seconds"))

    p = raw.get("payout", {})
    payout = Payout(p.get("split_pct"), p.get("split_max_pct"),
                    p.get("first_after_days"), p.get("cycle_days"))
    for name in ("split_pct", "split_max_pct"):
        v = getattr(payout, name)
        if v is not None:
            _pct(v, f"{w}.payout.{name}")

    f = raw.get("fees", {})
    fees = Fees(f.get("fee_by_size"), f.get("fee_refund"))

    banned = raw.get("banned_behaviors")
    sources = _req(raw, "sources", w)
    if not sources:
        raise RuleError(f"{w}: at least one source is required")
    srcs = []
    for i, s in enumerate(sources):
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

    return FirmRules(
        firm=str(firm), program=str(program),
        verify_before_purchase=bool(raw["verify_before_purchase"]),
        phases=tuple(phases), daily_loss=daily, max_loss=maxloss,
        consistency=consistency, news=news, trading_limits=limits,
        payout=payout, fees=fees,
        banned_behaviors=None if banned is None else tuple(banned),
        sources=tuple(srcs), modeled_in_sim=dict(modeled),
        notes=tuple(raw.get("notes", [])),
    )

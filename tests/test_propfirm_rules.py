"""Tests for the prop-firm rules loader: 3 valid rulebooks + invalid files."""
from pathlib import Path

import pytest
import yaml

from core.data.paths import repo_file
from core.propfirm.rules import RuleError, daily_floor, load_rules, max_floor

RULES = Path(repo_file("docs", "propfirm_rules"))


def test_all_rulebooks_load():
    r2 = load_rules(RULES / "ftmo_2step_standard.yaml")
    assert (r2.firm, r2.program) == ("FTMO", "2-Step Standard")
    assert [p.profit_target_pct for p in r2.phases] == [10.0, 5.0]
    assert r2.daily_loss.pct == 5.0 and r2.daily_loss.measured_on == "equity"
    assert r2.max_loss.type == "static"
    assert r2.consistency.best_day_max_pct_of_positive_days is None
    assert r2.modeled_in_sim["max_requests_per_day"] is False
    assert r2.verify_before_purchase is True

    r1 = load_rules(RULES / "ftmo_1step.yaml")
    assert r1.max_loss.type == "eod_trailing"
    assert r1.consistency.best_day_max_pct_of_positive_days == 50.0
    assert r1.phases[0].target_requires_flat is True

    r5 = load_rules(RULES / "the5ers_high_stakes.yaml")
    assert r5.daily_loss.reset_tz == "UTC+3"
    assert r5.payout.cycle_days == 14
    assert r5.news.evaluation_restricted is True


def _bad(tmp_path, mutate):
    src = yaml.safe_load((RULES / "ftmo_2step_standard.yaml").read_text())
    mutate(src)
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.safe_dump(src))
    return f


def test_bad_enum_rejected(tmp_path):
    f = _bad(tmp_path, lambda s: s["daily_loss"].__setitem__("reference", "vibes"))
    with pytest.raises(RuleError, match="reference"):
        load_rules(f)


def test_bad_pct_rejected(tmp_path):
    f = _bad(tmp_path, lambda s: s["max_loss"].__setitem__("pct", 101))
    with pytest.raises(RuleError, match="percentage"):
        load_rules(f)


def test_missing_identity_rejected(tmp_path):
    f = _bad(tmp_path, lambda s: s.pop("firm"))
    with pytest.raises(RuleError, match="firm"):
        load_rules(f)


def test_unknown_modeled_key_rejected(tmp_path):
    f = _bad(tmp_path, lambda s: s["modeled_in_sim"].__setitem__("astrology", True))
    with pytest.raises(RuleError, match="modeled_in_sim"):
        load_rules(f)


def test_bad_tz_and_time_rejected(tmp_path):
    f = _bad(tmp_path, lambda s: s["daily_loss"].__setitem__("reset_tz", "Mars/Olympus"))
    with pytest.raises(RuleError, match="timezone"):
        load_rules(f)
    f = _bad(tmp_path, lambda s: s["daily_loss"].__setitem__("reset_time", "25:00"))
    with pytest.raises(RuleError, match="HH:MM"):
        load_rules(f)


def test_floors_planner_table():
    """D-017 semantics pinned: initial = 100,000."""
    r2 = load_rules(RULES / "ftmo_2step_standard.yaml")
    assert daily_floor(r2, 100_000, 103_000) == 98_000
    assert max_floor(r2, 100_000, 999_999) == 90_000  # static ignores trail

    r5 = load_rules(RULES / "the5ers_high_stakes.yaml")
    assert daily_floor(r5, 100_000, 103_000) == 97_850

    r1 = load_rules(RULES / "ftmo_1step.yaml")
    assert max_floor(r1, 100_000, 104_000) == 94_000
    # Ratchet never falls: caller keeps the running max, floor stays put.
    trail = max(104_000, 99_000)
    assert max_floor(r1, 100_000, trail) == 94_000


def test_modeled_defaults_to_false(tmp_path):
    """Absent modeled_in_sim keys must read as unmodeled, never passed."""
    f = _bad(tmp_path, lambda s: s["modeled_in_sim"].pop("news"))
    rules = load_rules(f)
    assert rules.modeled_in_sim["news"] is False
    assert rules.modeled_in_sim["daily_loss"] is True


def test_typo_keys_rejected(tmp_path):
    f = _bad(tmp_path, lambda s: s.__setitem__("trading_limit", {}))
    with pytest.raises(RuleError, match="unknown keys"):
        load_rules(f)
    f = _bad(tmp_path,
             lambda s: s["trading_limits"].__setitem__("min_hold_secs", 60))
    with pytest.raises(RuleError, match="unknown keys"):
        load_rules(f)


def test_trading_limits_types_rejected(tmp_path):
    f = _bad(tmp_path,
             lambda s: s["trading_limits"].__setitem__("max_requests_per_day", -5))
    with pytest.raises(RuleError, match="int > 0"):
        load_rules(f)

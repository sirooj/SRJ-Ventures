"""Tests for session VWAP, bands, anchored VWAP — incl. no-lookahead + DST."""
from datetime import datetime, timezone

import polars as pl
import pytest

from core.indicators.vwap import anchored_vwap, session_id, session_vwap


def _bars(n=4):
    base = datetime(2023, 6, 1, 12, tzinfo=timezone.utc)
    return pl.DataFrame(
        {
            "ts": [base.replace(minute=m) for m in range(n)],
            "open": [10.0] * n,
            "high": [11.0, 13.0, 12.0, 14.0][:n],
            "low": [9.0] * n,
            "close": [10.0, 12.0, 11.0, 13.0][:n],
            "tick_count": [1, 1, 1, 1][:n],
            "session": ["a"] * n,
        }
    )


def test_session_vwap_hand_calc():
    # typical = (H+L+C)/3 → [10, 34/3]
    out = session_vwap(_bars(2))
    assert out["vwap"][0] == pytest.approx(10.0)
    assert out["vwap"][1] == pytest.approx((10.0 + 34 / 3) / 2)
    # variance around running vwap at bar 2:
    v = (10.0 + 34 / 3) / 2
    var = ((10.0 - v) ** 2 + (34 / 3 - v) ** 2) / 2
    assert out["ub1"][1] == pytest.approx(v + var**0.5)
    assert out["lb1"][1] == pytest.approx(v - var**0.5)
    assert out["ub3"][1] == pytest.approx(v + 3 * var**0.5)
    # first bar: zero variance → bands equal vwap
    assert out["ub1"][0] == pytest.approx(10.0)


def test_session_vwap_resets_per_session():
    df = _bars(4).with_columns(
        pl.Series("session", ["a", "a", "b", "b"]))
    out = session_vwap(df)
    assert out["vwap"][2] == pytest.approx((12.0 + 9.0 + 11.0) / 3)  # fresh session


def test_anchored_vwap():
    out = anchored_vwap(_bars(4), datetime(2023, 6, 1, 12, 2, tzinfo=timezone.utc),
                        price_col="close", weight_col="tick_count")
    assert out[0] is None and out[1] is None
    assert out[2] == pytest.approx(11.0)
    assert out[3] == pytest.approx(12.0)


def test_no_lookahead_prefix_stability():
    """Recomputing on truncated data must equal the prefix of the full result."""
    full = session_vwap(_bars(4))
    trunc = session_vwap(_bars(4).head(2))
    for col in ("vwap", "ub1", "ub2", "ub3", "lb1", "lb2", "lb3"):
        assert full[col][:2].to_list() == pytest.approx(trunc[col].to_list())


def test_session_id_dst_transition():
    # US DST starts 2023-03-12; 13:30Z = 09:30 EDT (was EST the Friday before).
    fri = pl.Series([datetime(2023, 3, 10, 14, 30, tzinfo=timezone.utc)])
    mon = pl.Series([datetime(2023, 3, 13, 13, 30, tzinfo=timezone.utc)])
    assert session_id(fri, "America/New_York", "09:30", "16:00")[0] == "2023-03-10"
    assert session_id(mon, "America/New_York", "09:30", "16:00")[0] == "2023-03-13"

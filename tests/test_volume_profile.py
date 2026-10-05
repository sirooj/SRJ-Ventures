"""Tests for fixed profiles, value area, HVN/LVN, naked POCs."""
from datetime import datetime, timezone

import numpy as np
import polars as pl
import pytest

from core.indicators.volume_profile import (
    composite_profile,
    fixed_profile,
    session_profiles,
    track_naked_pocs,
)


def test_poc_and_value_area_70():
    prices = np.array([10.1] * 5 + [11.1] * 10 + [12.1] * 3)
    p = fixed_profile(prices, np.ones(len(prices)), bin_size=1.0)
    assert p.poc == pytest.approx(11.0)
    assert p.total_volume == 18
    # 70% of 18 = 12.6 → POC(10) + richer neighbour(5) = 15 → VA [10, 11]
    assert (p.val, p.vah) == (pytest.approx(10.0), pytest.approx(11.0))
    assert p.hvn == [pytest.approx(11.0)]
    assert p.lvn == []


def test_hvn_lvn_extrema():
    # bins 10..14 with volumes [1,5,2,8,3]
    prices = np.array([10.5, 11.5, 12.5, 13.5, 14.5])
    p = fixed_profile(prices, np.array([1.0, 5.0, 2.0, 8.0, 3.0]), bin_size=1.0)
    assert p.poc == pytest.approx(13.0)
    assert p.hvn == [pytest.approx(11.0), pytest.approx(13.0)]
    assert p.lvn == [pytest.approx(12.0)]


def test_empty_profile():
    p = fixed_profile(np.array([]), np.array([]), bin_size=1.0)
    assert p.total_volume == 0 and np.isnan(p.poc)


def test_session_and_composite():
    df = pl.DataFrame({
        "close": [10.1, 10.2, 11.1, 11.2],
        "tick_count": [5, 5, 5, 5],
        "session": ["d1", "d1", "d2", "d2"],
    })
    profs = session_profiles(df, "session", bin_size=1.0)
    assert set(profs) == {"d1", "d2"}
    assert profs["d1"].poc == pytest.approx(10.0)
    comp = composite_profile(df["close"].to_numpy(),
                             df["tick_count"].to_numpy(), bin_size=1.0)
    assert comp.total_volume == 20


def test_naked_poc_tracking():
    t0 = datetime(2023, 6, 1, tzinfo=timezone.utc)
    t1 = datetime(2023, 6, 2, tzinfo=timezone.utc)
    t2 = datetime(2023, 6, 3, tzinfo=timezone.utc)
    bars = pl.DataFrame({
        "ts": [t1, t2],
        "high": [99.0, 101.0],
        "low": [98.0, 99.5],
    }, schema={"ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
               "high": pl.Float64, "low": pl.Float64})
    out = track_naked_pocs([(t0, 100.0), (t0, 90.0)], bars)
    assert out[0]["naked"] is False   # 100 traded through on t2
    assert out[1]["naked"] is True    # 90 never touched

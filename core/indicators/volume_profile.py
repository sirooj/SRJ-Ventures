"""Fixed-price volume profiles: POC, 70% value area, HVN/LVN, naked POCs.

Profiles aggregate ``volumes`` (tick counts or bar volumes) into fixed price
bins of ``bin_size`` (per instrument, from ``config/instruments.yaml``).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl


@dataclass(frozen=True)
class Profile:
    bin_low: np.ndarray      # lower edge of each occupied bin (ascending)
    volume: np.ndarray       # volume per bin
    poc: float               # price (bin low) of the point of control
    vah: float               # value-area high (bin low)
    val: float               # value-area low (bin low)
    hvn: list[float]         # high-volume nodes (strict local maxima)
    lvn: list[float]         # low-volume nodes (strict local minima)
    total_volume: float
    value_area_pct: float = 0.70


def fixed_profile(
    prices: np.ndarray, volumes: np.ndarray, bin_size: float,
    value_area_pct: float = 0.70,
) -> Profile:
    """Build a fixed-bin profile. Pure function of the given prices/volumes."""
    prices = np.asarray(prices, dtype=float)
    volumes = np.asarray(volumes, dtype=float)
    if len(prices) == 0:
        empty = np.array([], dtype=float)
        return Profile(empty, empty, float("nan"), float("nan"), float("nan"),
                        [], [], 0.0, value_area_pct)
    idx = np.floor(prices / bin_size).astype(np.int64)
    lo, inv = np.unique(idx, return_inverse=True)
    vol = np.zeros(len(lo))
    np.add.at(vol, inv, volumes)
    order = np.argsort(lo)
    lo, vol = lo[order], vol[order]
    bins = lo * bin_size

    poc_pos = int(np.argmax(vol))
    total = float(vol.sum())

    # Value area: expand from POC to the higher-volume neighbour until >= 70%.
    top, bot = poc_pos, poc_pos
    va_vol = vol[poc_pos]
    while va_vol < value_area_pct * total:
        up = vol[top + 1] if top + 1 < len(vol) else -1.0
        dn = vol[bot - 1] if bot - 1 >= 0 else -1.0
        if up < 0 and dn < 0:
            break
        if up >= dn:
            top += 1
            va_vol += vol[top]
        else:
            bot -= 1
            va_vol += vol[bot]

    # Strict local extrema (edges compare against their single neighbour).
    hvn, lvn = [], []
    for i in range(len(vol)):
        left = vol[i - 1] if i > 0 else -1.0
        right = vol[i + 1] if i + 1 < len(vol) else -1.0
        if vol[i] > left and vol[i] > right:
            hvn.append(float(bins[i]))
        if vol[i] < left and vol[i] < right:
            lvn.append(float(bins[i]))

    return Profile(
        bin_low=bins, volume=vol,
        poc=float(bins[poc_pos]), vah=float(bins[top]), val=float(bins[bot]),
        hvn=hvn, lvn=lvn, total_volume=total, value_area_pct=value_area_pct,
    )


def composite_profile(
    prices: np.ndarray, volumes: np.ndarray, bin_size: float,
    value_area_pct: float = 0.70,
) -> Profile:
    """Multi-session composite = one fixed profile over concatenated data."""
    return fixed_profile(prices, volumes, bin_size, value_area_pct)


def session_profiles(
    df: pl.DataFrame,
    session_col: str,
    price_col: str = "close",
    volume_col: str = "tick_count",
    bin_size: float = 1.0,
) -> dict[str, Profile]:
    """Per-session profiles keyed by session label."""
    out: dict[str, Profile] = {}
    for sess, part in df.group_by(session_col, maintain_order=True):
        out[str(sess[0])] = fixed_profile(
            part[price_col].to_numpy(), part[volume_col].to_numpy(), bin_size)
    return out


def track_naked_pocs(
    poc_events: list[tuple[object, float]], bars: pl.DataFrame
) -> list[dict]:
    """Flag POCs never traded through after their session ended.

    ``poc_events``: ``(session_end_ts, poc_price)``. A POC is *touched* when a
    later bar has ``low <= poc <= high``; otherwise it stays *naked*.
    """
    b = bars.sort("ts")
    out = []
    for end_ts, poc in poc_events:
        later = b.filter(pl.col("ts") > end_ts)
        touched = bool(
            len(later)
            and ((later["low"] <= poc) & (later["high"] >= poc)).any()
        )
        out.append({"poc": poc, "session_end": str(end_ts), "naked": not touched})
    return out

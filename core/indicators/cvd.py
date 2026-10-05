"""Tick-rule Cumulative Volume Delta (CVD).

Sign comes from the tick rule on the **bid** (+1 up / −1 down / carry forward
on unchanged ticks — see ``core.data.bars.add_tick_rule``). Default weight is
unit (±1 per tick); pass ``weight_col`` (e.g. ``bid_vol``) to weight by size.

Variants: full-history cumulative, per-session reset, and rolling tick-count
windows. All causal (cumsum / trailing rolling sums only).
"""
from __future__ import annotations

import polars as pl

from core.data.bars import add_tick_rule


def _contrib(df: pl.DataFrame, weight_col: str | None) -> pl.Expr:
    if weight_col is None:
        return pl.col("delta_tick_carry").cast(pl.Float64)
    return (pl.col("delta_tick_carry").cast(pl.Float64)
            * pl.col(weight_col).cast(pl.Float64))


def cvd_from_ticks(
    ticks: pl.DataFrame,
    session_col: str | None = None,
    weight_col: str | None = None,
    roll_windows: tuple[int, ...] = (100, 1000),
) -> pl.DataFrame:
    """Append ``cvd`` (+ ``cvd_roll_<N>``) to tick data, in tick order."""
    df = ticks.sort("ts")
    if "delta_tick_carry" not in df.columns:
        df = add_tick_rule(df)
    contrib = _contrib(df, weight_col)
    if session_col is None:
        df = df.with_columns(contrib.cum_sum().alias("cvd"))
    else:
        df = df.with_columns(contrib.cum_sum().over(session_col).alias("cvd"))
    for n in roll_windows:
        df = df.with_columns(
            contrib.rolling_sum(window_size=n, min_samples=1).alias(f"cvd_roll_{n}")
        )
    return df


def cvd_from_bars(
    bars_1m: pl.DataFrame,
    session_col: str | None = None,
    roll_windows: tuple[int, ...] = (30, 120),
) -> pl.DataFrame:
    """CVD from summed per-bar ``delta_tick_carry`` (approximation of tick CVD)."""
    df = bars_1m.sort("ts")
    contrib = pl.col("delta_tick_carry").cast(pl.Float64)
    if session_col is None:
        df = df.with_columns(contrib.cum_sum().alias("cvd"))
    else:
        df = df.with_columns(contrib.cum_sum().over(session_col).alias("cvd"))
    for n in roll_windows:
        df = df.with_columns(
            contrib.rolling_sum(window_size=n, min_samples=1).alias(f"cvd_roll_{n}")
        )
    return df

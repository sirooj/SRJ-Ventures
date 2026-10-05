"""Bid-side 1m bars from ticks + resampling to 5m/15m/1h.

Bar columns (all prices from the **bid**):
``ts`` (bar open, UTC ms) | ``open/high/low/close`` | ``tick_count`` |
``bid_vol_sum`` | ``ask_vol_sum`` | ``spread_mean`` | ``spread_max`` |
``delta_tick`` | ``delta_tick_carry``.

Tick-rule delta: +1 if the bid rose vs the previous tick, −1 if it fell,
0 if unchanged. ``delta_tick_carry`` inherits the last non-zero sign
(computed at tick level, then summed per bar).

Usage::

    python -m core.data.bars --symbol EURUSD --year 2023
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

import numpy as np
import polars as pl

from .paths import bars_path, data_root, ticks_month_path

BAR_SCHEMA = {
    "ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "tick_count": pl.UInt32,
    "bid_vol_sum": pl.Float64,
    "ask_vol_sum": pl.Float64,
    "spread_mean": pl.Float64,
    "spread_max": pl.Float64,
    "delta_tick": pl.Int32,
    "delta_tick_carry": pl.Int32,
}


def add_tick_rule(ticks: pl.DataFrame, price_col: str = "bid") -> pl.DataFrame:
    """Append ``delta_tick`` (+1/−1/0) and ``delta_tick_carry`` columns.

    Pure tick-level function; the carry is a vectorised forward-fill of the
    last non-zero sign (no Python loop, no lookahead — uses only past ticks).
    """
    bid = ticks[price_col].to_numpy()
    d = np.sign(np.diff(bid, prepend=bid[:1])).astype(np.int32)
    n = len(d)
    if n == 0:
        return ticks.with_columns(
            pl.lit(0, dtype=pl.Int32).alias("delta_tick"),
            pl.lit(0, dtype=pl.Int32).alias("delta_tick_carry"),
        )
    last_nz = np.maximum.accumulate(np.where(d != 0, np.arange(n), 0))
    carry = d[last_nz]
    return ticks.with_columns(
        pl.Series("delta_tick", d, dtype=pl.Int32),
        pl.Series("delta_tick_carry", carry, dtype=pl.Int32),
    )


def ticks_to_1m(ticks: pl.DataFrame) -> pl.DataFrame:
    """Aggregate sorted ticks into 1-minute bid-side bars."""
    if len(ticks) == 0:
        return pl.DataFrame(schema=BAR_SCHEMA)
    ticks = ticks.sort("ts")
    if "delta_tick" not in ticks.columns:
        ticks = add_tick_rule(ticks)
    return (
        ticks.group_by_dynamic("ts", every="1m")
        .agg(
            pl.col("bid").first().alias("open"),
            pl.col("bid").max().alias("high"),
            pl.col("bid").min().alias("low"),
            pl.col("bid").last().alias("close"),
            pl.len().cast(pl.UInt32).alias("tick_count"),
            pl.col("bid_vol").sum().alias("bid_vol_sum"),
            pl.col("ask_vol").sum().alias("ask_vol_sum"),
            pl.col("spread").mean().alias("spread_mean"),
            pl.col("spread").max().alias("spread_max"),
            pl.col("delta_tick").sum().alias("delta_tick"),
            pl.col("delta_tick_carry").sum().alias("delta_tick_carry"),
        )
        .sort("ts")
    )


RESAMPLE_EVERY = {"5m": "5m", "15m": "15m", "1h": "1h"}


def resample_bars(bars_1m: pl.DataFrame, tf: str) -> pl.DataFrame:
    """Resample 1m bars to 5m / 15m / 1h (sums stay sums, spreads re-aggregate)."""
    if tf not in RESAMPLE_EVERY:
        raise ValueError(f"tf must be one of {sorted(RESAMPLE_EVERY)}, got {tf!r}")
    if len(bars_1m) == 0:
        return pl.DataFrame(schema=BAR_SCHEMA)
    return (
        bars_1m.sort("ts")
        .group_by_dynamic("ts", every=RESAMPLE_EVERY[tf])
        .agg(
            pl.col("open").first().alias("open"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
            pl.col("tick_count").sum().alias("tick_count"),
            pl.col("bid_vol_sum").sum().alias("bid_vol_sum"),
            pl.col("ask_vol_sum").sum().alias("ask_vol_sum"),
            pl.col("spread_mean").mean().alias("spread_mean"),
            pl.col("spread_max").max().alias("spread_max"),
            pl.col("delta_tick").sum().alias("delta_tick"),
            pl.col("delta_tick_carry").sum().alias("delta_tick_carry"),
        )
        .sort("ts")
    )


def build_symbol_year(symbol: str, year: int, months: list[int] | None = None) -> dict:
    """Build 1m bars (+5m/15m/1h) for every available tick month of a symbol-year."""
    months = months or list(range(1, 13))
    out: dict = {}
    for m in months:
        src = ticks_month_path(symbol, year, m)
        if not src.exists():
            continue
        bars_1m = ticks_to_1m(pl.read_parquet(src))
        for tf, bars in [("1m", bars_1m)] + [
            (tf, resample_bars(bars_1m, tf)) for tf in ("5m", "15m", "1h")
        ]:
            dst = bars_path(symbol, tf, year, m)
            dst.parent.mkdir(parents=True, exist_ok=True)
            bars.write_parquet(dst, compression="zstd", statistics=True)
            out[f"{tf}/{m:02d}"] = (len(bars), str(dst))
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Build bid-side bars from tick parquet")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--months", default=None, help="e.g. 1,2,3 (default: all)")
    args = ap.parse_args(argv)
    months = [int(x) for x in args.months.split(",")] if args.months else None
    for k, v in build_symbol_year(args.symbol, args.year, months).items():
        print(k, v)


if __name__ == "__main__":
    main()

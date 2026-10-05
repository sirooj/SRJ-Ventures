"""Session VWAP with ±1/2/3σ bands (tick-count-weighted, on bid) + anchored VWAP.

All computations are causal: each bar's VWAP uses only that bar and earlier
bars of the same session (enforced by ``tests/test_vwap.py``).
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import polars as pl


def typical_price() -> pl.Expr:
    """Bid typical price (H+L+C)/3."""
    return (pl.col("high") + pl.col("low") + pl.col("close")) / 3.0


def session_id(
    ts: pl.Series, tz_name: str, sess_open: str, sess_close: str
) -> pl.Series:
    """Label each UTC timestamp with its trading-session date (local calendar).

    Overnight sessions (close <= open) attribute post-midnight bars to the
    previous day. DST is handled by ``zoneinfo`` — no manual offsets.
    """
    tz = ZoneInfo(tz_name)
    oh, om = map(int, sess_open.split(":"))
    ch, cm = map(int, sess_close.split(":"))
    overnight = (ch, cm) <= (oh, om)
    labels = []
    for t in ts.to_list():
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        local = t.astimezone(tz)
        d = local.date()
        if overnight and (local.hour, local.minute) < (ch, cm):
            d = d.fromordinal(d.toordinal() - 1)
        labels.append(str(d))
    return pl.Series("session", labels)


def session_vwap(
    bars: pl.DataFrame,
    session_col: str = "session",
    price_col: str | None = None,
    weight_col: str = "tick_count",
) -> pl.DataFrame:
    """Append ``vwap`` and ``ub1..3``/``lb1..3`` bands per session.

    Typical price defaults to (H+L+C)/3; weight defaults to ``tick_count``.
    Band variance is the causal population variance E[t²] − E[t]², i.e. the
    mean squared deviation from the *running* VWAP.
    """
    df = bars.sort("ts").with_columns(
        typical_price().alias("_t") if price_col is None
        else pl.col(price_col).alias("_t")
    )
    w = pl.col(weight_col).cast(pl.Float64)
    df = df.with_columns(
        (w.cum_sum().over(session_col)).alias("_cumw"),
        ((pl.col("_t") * w).cum_sum().over(session_col)).alias("_cumpv"),
    )
    df = df.with_columns((pl.col("_cumpv") / pl.col("_cumw")).alias("vwap"))
    # Population variance around the running VWAP: E[t²] − E[t]² (causal).
    df = df.with_columns(
        (((pl.col("_t") ** 2 * w).cum_sum().over(session_col) / pl.col("_cumw"))
         - pl.col("vwap") ** 2)
        .clip(0.0, None)
        .alias("_var")
    )
    df = df.with_columns(pl.col("_var").sqrt().alias("_sd"))
    for k in (1, 2, 3):
        df = df.with_columns(
            (pl.col("vwap") + k * pl.col("_sd")).alias(f"ub{k}"),
            (pl.col("vwap") - k * pl.col("_sd")).alias(f"lb{k}"),
        )
    return df.drop(["_t", "_cumw", "_cumpv", "_var", "_sd"])


def anchored_vwap(
    bars: pl.DataFrame,
    anchor_ts: datetime,
    price_col: str = "close",
    weight_col: str = "tick_count",
) -> pl.Series:
    """VWAP anchored at ``anchor_ts`` — cumulative from the anchor, null before."""
    df = bars.sort("ts")
    mask = df["ts"] >= anchor_ts
    t = df[price_col].cast(pl.Float64)
    w = df[weight_col].cast(pl.Float64)
    cumw = (w * mask.cast(pl.Float64)).cum_sum()
    cumpv = (t * w * mask.cast(pl.Float64)).cum_sum()
    vwap = cumpv / cumw
    return (
        pl.Series("anchored_vwap", vwap.to_list())
        .zip_with(mask, pl.Series([None] * len(df), dtype=pl.Float64))
        .alias("anchored_vwap")
    )

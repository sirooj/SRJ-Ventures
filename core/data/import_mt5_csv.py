"""Import sirooj's existing Dukascopy-derived CSV archives into tick parquet.

Background: sirooj's custom chart history lives in ``D:\\download`` as
dukascopy-node pulls converted for MT5. Two formats exist:

- ``dukascopy-node-utc``: ``timestamp,askPrice,bidPrice`` with UTC timestamps
  (``YYYY.MM.DD HH:mm:ss.SSS``) — directly reusable.
- ``mt5-server``: MT5 import/export layout ``Date,Time,Bid,Ask,...`` (comma or
  tab separated) in **MT5 server time** (UTC+2 winter / UTC+3 summer, US DST
  bounds). Converted back to UTC with the inverse rule — see ``server_to_utc``.

Output matches the standard monthly tick layout
(``ticks/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet``) with
``bid_vol``/``ask_vol`` set to 0 (MT5 exports carry no quote volumes;
``tick_count`` remains the volume proxy).

Usage::

    python -m core.data.import_mt5_csv --symbol EURUSD --format mt5-server \
        D:\\download\\eurusd-topup.csv
    python -m core.data.import_mt5_csv --symbol EURUSD --format dukascopy-node-utc \
        D:\\download\\aug03-eurusd-utc.csv
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl

from .paths import ticks_month_path

TICK_SCHEMA = {
    "ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
    "bid": pl.Float64,
    "ask": pl.Float64,
    "bid_vol": pl.Float32,
    "ask_vol": pl.Float32,
    "spread": pl.Float64,
}


# --------------------------------------------------------------------------
# MT5 server time <-> UTC (inverse of Convert-DukascopyToMT5.ps1)
# --------------------------------------------------------------------------
def _nth_sunday(year: int, month: int, n: int) -> int:
    """Day-of-month of the n-th Sunday."""
    first = datetime(year, month, 1)
    first_sunday = 1 + (6 - first.weekday()) % 7
    return first_sunday + 7 * (n - 1)


def us_dst_start(year: int) -> datetime:
    """Second Sunday of March (naive UTC): server switches +2 → +3.

    Naive on purpose — compared against naive MT5-server stamps; the real
    switch falls in the Sunday weekly close, which holds no ticks.
    """
    return datetime(year, 3, _nth_sunday(year, 3, 2))


def us_dst_end(year: int) -> datetime:
    """First Sunday of November (naive UTC): server switches +3 → +2."""
    return datetime(year, 11, _nth_sunday(year, 11, 1))


def server_offset_hours(server_naive: datetime) -> int:
    """MT5 server offset from UTC for a naive server-time stamp."""
    # DST window expressed in server-time terms (+3 applied to the UTC bounds).
    start = us_dst_start(server_naive.year) + timedelta(hours=3)
    end = us_dst_end(server_naive.year) + timedelta(hours=3)
    return 3 if start <= server_naive < end else 2


def server_to_utc(server_naive: datetime) -> datetime:
    """Naive MT5-server timestamp → aware UTC (inverts the ps1 shift rule)."""
    return (server_naive - timedelta(hours=server_offset_hours(server_naive))).replace(
        tzinfo=timezone.utc
    )


# --------------------------------------------------------------------------
# Parsers
# --------------------------------------------------------------------------
def _parse_mt5_dt(date_s: str, time_s: str) -> datetime:
    for fmt in ("%Y.%m.%d %H:%M:%S.%f", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(f"{date_s} {time_s}", fmt)
        except ValueError:
            continue
    raise ValueError(f"unparseable MT5 datetime: {date_s} {time_s}")


def read_dukascopy_node_utc(path: Path) -> pl.DataFrame:
    """Read ``timestamp,askPrice,bidPrice`` (UTC) into tick schema."""
    df = pl.read_csv(
        path, has_header=True,
        schema_overrides={"timestamp": pl.String, "askPrice": pl.Float64, "bidPrice": pl.Float64},
    )
    ts = (
        df["timestamp"]
        .str.strptime(pl.Datetime(time_unit="ms"), "%Y.%m.%d %H:%M:%S.%3f")
        .dt.replace_time_zone("UTC")
    )
    return pl.DataFrame(
        {
            "ts": ts,
            "bid": df["bidPrice"],
            "ask": df["askPrice"],
            "spread": df["askPrice"] - df["bidPrice"],
        },
        schema={k: v for k, v in TICK_SCHEMA.items() if k != "bid_vol"
                and k != "ask_vol"},
    ).with_columns(
        pl.lit(0.0, dtype=pl.Float32).alias("bid_vol"),
        pl.lit(0.0, dtype=pl.Float32).alias("ask_vol"),
    ).select(["ts", "bid", "ask", "bid_vol", "ask_vol", "spread"]).sort("ts")


def read_mt5_server(path: Path) -> pl.DataFrame:
    """Read MT5 ``Date,Time,Bid,Ask,...`` (comma or tab) in server time → UTC.

    Fully vectorised: naive server stamps are parsed with ``strptime`` and the
    +2/+3 offset is applied per row via the US-DST bounds of that row's year.
    (Transitions fall inside the Sunday weekly close, which holds no ticks,
    so boundary imprecision cannot corrupt data.)
    """
    head = path.open("r", encoding="utf-8").readline()
    sep = "\t" if "\t" in head else ","
    df = pl.read_csv(path, has_header=True, separator=sep, infer_schema_length=10000)
    cols = {c.lower().strip("<>"): c for c in df.columns}
    date_c, time_c, bid_c, ask_c = cols["date"], cols["time"], cols["bid"], cols["ask"]
    naive = (
        (pl.col(date_c).cast(pl.String) + " " + pl.col(time_c).cast(pl.String))
        .str.strptime(pl.Datetime(time_unit="ms"), "%Y.%m.%d %H:%M:%S.%3f", strict=False)
    )
    naive2 = (
        (pl.col(date_c).cast(pl.String) + " " + pl.col(time_c).cast(pl.String))
        .str.strptime(pl.Datetime(time_unit="ms"), "%Y.%m.%d %H:%M:%S", strict=False)
    )
    df = df.with_columns(pl.coalesce(naive, naive2).alias("_naive"))
    cond = pl.lit(False)
    for yr in df["_naive"].dt.year().unique().to_list():
        start = us_dst_start(yr) + timedelta(hours=3)  # bounds in server terms
        end = us_dst_end(yr) + timedelta(hours=3)
        cond = cond | ((pl.col("_naive").dt.year() == yr)
                       & (pl.col("_naive") >= start) & (pl.col("_naive") < end))
    df = df.with_columns(
        pl.when(cond).then(3).otherwise(2).alias("_off"),
        pl.col(bid_c).cast(pl.Float64).alias("_bid"),
        pl.col(ask_c).cast(pl.Float64).alias("_ask"),
    )
    ts = (pl.col("_naive") - pl.duration(hours=pl.col("_off"))).dt.replace_time_zone("UTC")
    return df.select(
        ts.alias("ts"),
        pl.col("_bid").alias("bid"),
        pl.col("_ask").alias("ask"),
        (pl.col("_ask") - pl.col("_bid")).alias("spread"),
    ).with_columns(
        pl.lit(0.0, dtype=pl.Float32).alias("bid_vol"),
        pl.lit(0.0, dtype=pl.Float32).alias("ask_vol"),
    ).select(["ts", "bid", "ask", "bid_vol", "ask_vol", "spread"]).sort("ts")


def write_monthly(df: pl.DataFrame, symbol: str) -> dict:
    """Merge a tick frame into monthly parquet parts (union + dedup on ts).

    Parts are merged, never clobbered: existing rows win on ``ts`` conflicts
    (first write wins — the RAW MT5 exports were imported before patch files).
    Returns month → row count after merge.
    """
    if len(df) == 0:
        return {}
    df = df.with_columns(
        pl.col("ts").dt.year().alias("y"), pl.col("ts").dt.month().alias("m")
    )
    counts: dict = {}
    for (y, m), part in df.group_by(["y", "m"]):
        out = ticks_month_path(symbol, y, m)
        out.parent.mkdir(parents=True, exist_ok=True)
        part = part.drop(["y", "m"])
        if out.exists():
            part = pl.concat([pl.read_parquet(out), part]).unique(
                subset=["ts"], keep="first").sort("ts")
        part.write_parquet(out, compression="zstd", statistics=True)
        counts[f"{y}-{m:02d}"] = len(part)
    return counts


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Import existing CSV tick archives")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--format", choices=["dukascopy-node-utc", "mt5-server"],
                    required=True)
    args = ap.parse_args(argv)
    reader = read_dukascopy_node_utc if args.format == "dukascopy-node-utc" else read_mt5_server
    for f in args.files:
        df = reader(Path(f))
        counts = write_monthly(df, args.symbol)
        print(f, len(df), counts)


if __name__ == "__main__":
    main()

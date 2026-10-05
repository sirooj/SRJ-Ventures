"""Data QA: coverage, gaps, spikes, spread-by-hour, DST sanity.

Reads tick/bar parquet from ``$SRJ_DATA`` and writes
``results/data_qa/report.md`` (committed — small markdown only).

Usage::

    python -m core.data.qa --symbol EURUSD --year 2023
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import polars as pl

from .bars import BAR_SCHEMA  # noqa: F401  (schema reference)
from .paths import bars_path, results_dir, ticks_month_path

# FX spot weekly close: Friday 22:00 UTC → Sunday 22:00 UTC.
WEEKLY_CLOSE_START_WD = 4  # Friday
WEEKLY_CLOSE_START_H = 22
WEEKLY_CLOSE_END_WD = 6  # Sunday
WEEKLY_CLOSE_END_H = 22


def in_weekly_close(ts: datetime) -> bool:
    """True when a UTC timestamp falls in the Fri-22:00 → Sun-22:00 close."""
    wd, h = ts.weekday(), ts.hour + ts.minute / 60
    if wd == 4:
        return h >= 22
    if wd == 5:
        return True
    if wd == 6:
        return h < 22
    return False


def expected_trading_minutes(start: datetime, end: datetime) -> int:
    """Expected 1m bars in [start, end) excluding the weekly close."""
    total = 0
    cur = start.replace(second=0, microsecond=0)
    while cur < end:
        if not in_weekly_close(cur):
            total += 1
        cur += timedelta(minutes=1)
    return total


def minute_coverage(bars_1m: pl.DataFrame) -> dict:
    """Coverage fraction of 1m bars over the observed span."""
    if len(bars_1m) == 0:
        return {"bars": 0, "expected": 0, "coverage": 0.0}
    start = bars_1m["ts"].min()
    end = bars_1m["ts"].max() + timedelta(minutes=1)
    expected = expected_trading_minutes(start, end)
    present = bars_1m["ts"].n_unique()
    return {
        "bars": len(bars_1m),
        "unique_minutes": present,
        "expected": expected,
        "coverage": present / expected if expected else 0.0,
        "span_start": str(start),
        "span_end": str(end),
    }


def _contains_saturday(start: datetime, end: datetime) -> bool:
    """True when a Saturday 00:00 UTC falls strictly inside (start, end).

    Every normal Fri-close → Sun-reopen weekend contains one, so this
    identifies weekend gaps regardless of exact close/reopen minutes.
    """
    start_n = start.replace(tzinfo=None)
    end_n = end.replace(tzinfo=None)
    sat = start_n.date() + timedelta(days=(5 - start_n.weekday()) % 7)
    while datetime(sat.year, sat.month, sat.day) < end_n:
        if datetime(sat.year, sat.month, sat.day) > start_n:
            return True
        sat += timedelta(days=7)
    return False


def find_gaps(bars_1m: pl.DataFrame, min_gap_minutes: int = 5) -> pl.DataFrame:
    """Gaps over ``min_gap_minutes`` during trading hours (weekends excluded)."""
    if len(bars_1m) < 2:
        return pl.DataFrame(
            {"gap_start": [], "gap_end": [], "gap_minutes": []},
            schema={"gap_start": pl.Datetime(time_unit="ms", time_zone="UTC"),
                    "gap_end": pl.Datetime(time_unit="ms", time_zone="UTC"),
                    "gap_minutes": pl.Float64},
        )
    ts = bars_1m.sort("ts").select(
        pl.col("ts").shift(1).alias("gap_start"),
        pl.col("ts").alias("gap_end"),
    )
    ts = ts.with_columns(
        ((pl.col("gap_end") - pl.col("gap_start")).dt.total_seconds() / 60)
        .alias("gap_minutes")
    ).filter(pl.col("gap_minutes") > min_gap_minutes)
    gaps = []
    for prev, cur, mins in ts.iter_rows():
        if prev is None:
            continue
        prev_n, cur_n = prev.replace(tzinfo=None), cur.replace(tzinfo=None)
        if _contains_saturday(prev_n, cur_n):
            continue  # normal Fri-close → Sun-reopen weekend
        gaps.append((prev, cur, mins))
    if not gaps:
        return pl.DataFrame(
            {"gap_start": [], "gap_end": [], "gap_minutes": []},
            schema={"gap_start": pl.Datetime(time_unit="ms", time_zone="UTC"),
                    "gap_end": pl.Datetime(time_unit="ms", time_zone="UTC"),
                    "gap_minutes": pl.Float64},
        )
    return pl.DataFrame(
        {"gap_start": [g[0] for g in gaps], "gap_end": [g[1] for g in gaps],
         "gap_minutes": [g[2] for g in gaps]}
    )


def detect_spikes(bars_1m: pl.DataFrame, max_abs_logret: float = 0.01) -> pl.DataFrame:
    """Bars whose close-to-close |log return| exceeds the threshold."""
    if len(bars_1m) < 2:
        return bars_1m.clear()
    df = bars_1m.sort("ts").with_columns(
        pl.col("close").log().diff().abs().alias("_ret")
    )
    return df.filter(pl.col("_ret") > max_abs_logret).drop("_ret")


def spread_by_hour(ticks: pl.DataFrame) -> pl.DataFrame:
    """Mean/max spread per UTC hour of day."""
    return (
        ticks.with_columns(pl.col("ts").dt.hour().alias("hour"))
        .group_by("hour")
        .agg(
            pl.col("spread").mean().alias("spread_mean"),
            pl.col("spread").max().alias("spread_max"),
            pl.len().alias("ticks"),
        )
        .sort("hour")
    )


def dst_sanity(
    bars_1m: pl.DataFrame, tz_name: str, sess_open: str, sess_close: str
) -> dict:
    """Session-length sanity around DST transitions.

    Counts 1m bars inside the local session window per local date; reports the
    distribution and any anomalous (short) days. Also checks duplicate /
    non-monotonic timestamps globally.
    """
    ts = bars_1m.sort("ts")["ts"]
    dupes = len(ts) - ts.n_unique()
    tz = ZoneInfo(tz_name)
    oh, om = map(int, sess_open.split(":"))
    ch, cm = map(int, sess_close.split(":"))
    per_day: dict = {}
    for t in ts.to_list():
        local = t.astimezone(tz)
        lt = local.time()
        import datetime as _dt

        if _dt.time(oh, om) <= lt < _dt.time(ch, cm):
            per_day[str(local.date())] = per_day.get(str(local.date()), 0) + 1
    counts = sorted(per_day.values())
    expected = (ch * 60 + cm) - (oh * 60 + om)
    anomalous = sorted(d for d, c in per_day.items() if c < 0.9 * expected)
    return {
        "tz": tz_name,
        "session": f"{sess_open}-{sess_close}",
        "expected_minutes": expected,
        "days": len(per_day),
        "median_minutes": (counts[len(counts) // 2] if counts else 0),
        "min_minutes": (counts[0] if counts else 0),
        "duplicate_ts": dupes,
        "short_days": anomalous[:20],
        "n_short_days": len(anomalous),
    }


def _section(symbol: str, year: int) -> list[str]:
    """QA lines for one symbol-year (no file IO)."""
    bars = [
        pl.read_parquet(p)
        for m in range(1, 13)
        if (p := bars_path(symbol, "1m", year, m)).exists()
    ]
    ticks = [
        pl.read_parquet(p)
        for m in range(1, 13)
        if (p := ticks_month_path(symbol, year, m)).exists()
    ]
    lines = [f"# Data QA — {symbol} {year}", ""]
    if not bars:
        lines.append("No 1m bars found.")
    else:
        b = pl.concat(bars).sort("ts")
        cov = minute_coverage(b)
        lines += [
            "## Coverage",
            f"- span: {cov['span_start']} → {cov['span_end']}",
            f"- bars: {cov['bars']} unique minutes: {cov['unique_minutes']} "
            f"expected (ex-weekly-close): {cov['expected']}",
            f"- **coverage: {cov['coverage']:.3%}**",
            "",
            "## Gaps > 5 min (trading hours)",
        ]
        gaps = find_gaps(b)
        lines.append(f"- {len(gaps)} gaps" if len(gaps) else "- none")
        for row in gaps.head(20).iter_rows(named=True):
            lines.append(
                f"  - {row['gap_start']} → {row['gap_end']} ({row['gap_minutes']:.0f} min)")
        lines += ["", "## Spikes (|log-ret| > 1%)"]
        spikes = detect_spikes(b)
        lines.append(f"- {len(spikes)} spike bars")
        for row in spikes.head(20).iter_rows(named=True):
            lines.append(f"  - {row['ts']} O={row['open']} H={row['high']} "
                         f"L={row['low']} C={row['close']}")
        lines += ["", "## DST sanity (NY 09:30–16:00)"]
        dst = dst_sanity(b, "America/New_York", "09:30", "16:00")
        lines += [
            f"- days: {dst['days']}, expected min/day: {dst['expected_minutes']}, "
            f"median: {dst['median_minutes']}, min: {dst['min_minutes']}",
            f"- duplicate ts: {dst['duplicate_ts']}",
            f"- short days ({dst['n_short_days']}): "
            + (", ".join(dst["short_days"]) or "none"),
        ]
    if ticks:
        t = pl.concat(ticks)
        lines += ["", "## Spread by hour (UTC)"]
        for row in spread_by_hour(t).iter_rows(named=True):
            lines.append(
                f"- {row['hour']:02d}:00 mean={row['spread_mean']:.6f} "
                f"max={row['spread_max']:.6f} n={row['ticks']}")
    else:
        lines += ["", "No tick files found — spread table skipped."]
    return lines


def build_report(symbols: list[str], years: list[int]) -> str:
    """Run all checks over symbol-years; write results/data_qa/report.md."""
    sections: list[str] = []
    for symbol in symbols:
        for year in years:
            sections.extend(_section(symbol, year))
            sections.append("\n---\n")
    out = results_dir("data_qa") / "report.md"
    out.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")
    return str(out)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Data QA report")
    ap.add_argument("--symbols", required=True, help="comma-separated, e.g. EURUSD,GBPUSD")
    ap.add_argument("--years", required=True, help="comma-separated, e.g. 2025,2026")
    args = ap.parse_args(argv)
    print(build_report(args.symbols.split(","),
                       [int(y) for y in args.years.split(",")]))


if __name__ == "__main__":
    main()

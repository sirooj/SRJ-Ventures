"""Plot one NY session: price + VWAP bands + volume profile + CVD.

Reads 1m bars from ``$SRJ_DATA`` and writes a small PNG to
``results/indicators_demo/<symbol>_<date>.png`` (committed).

Usage::

    python research/make_indicators_demo.py --symbol USATECHIDXUSD --date 2026-10-02
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402

from core.data.bars import bars_path  # noqa: E402
from core.data.paths import results_dir  # noqa: E402
from core.indicators.cvd import cvd_from_bars  # noqa: E402
from core.indicators.volume_profile import fixed_profile  # noqa: E402
from core.indicators.vwap import session_vwap  # noqa: E402

NY = ZoneInfo("America/New_York")


def load_session(symbol: str, date: str) -> pl.DataFrame:
    """1m bars of one NY 09:30–16:00 session (regular hours only)."""
    import datetime as _dt

    day = datetime.strptime(date, "%Y-%m-%d").date()
    lo_utc = _dt.datetime.combine(day, _dt.time(9, 30), tzinfo=NY).astimezone(
        _dt.timezone.utc)
    hi_utc = _dt.datetime.combine(day, _dt.time(16, 0), tzinfo=NY).astimezone(
        _dt.timezone.utc)
    src = bars_path(symbol, "1m", lo_utc.year, lo_utc.month)
    bars = pl.read_parquet(src)
    sess = bars.filter(
        (pl.col("ts") >= lo_utc) & (pl.col("ts") < hi_utc)
    ).sort("ts")
    return sess.with_columns(pl.lit(date).alias("session"))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Plot one NY indicator session")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--date", required=True, help="NY calendar date YYYY-MM-DD")
    ap.add_argument("--bin-size", type=float, default=None,
                    help="volume-profile bin (default: instruments.yaml vp_bin)")
    args = ap.parse_args(argv)

    if args.bin_size is None:
        import yaml

        cfg = yaml.safe_load(
            Path(__file__).resolve().parents[1].joinpath(
                "config", "instruments.yaml").open())
        args.bin_size = float(cfg["instruments"][args.symbol]["vp_bin"])

    bars = load_session(args.symbol, args.date)
    if len(bars) == 0:
        raise SystemExit(f"no 1m bars for {args.symbol} on {args.date}")
    bars = session_vwap(bars)
    bars = cvd_from_bars(bars)
    prof = fixed_profile(bars["close"].to_numpy(),
                         bars["tick_count"].to_numpy(), args.bin_size)

    fig = plt.figure(figsize=(10, 8))
    gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1.4], hspace=0.45)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)  # price + CVD share the bar axis…
    ax2 = fig.add_subplot(gs[2])              # …but the profile keeps its own
    ax = [ax0, ax1, ax2]
    xs = range(len(bars))
    ax[0].plot(xs, bars["close"].to_list(), lw=0.9, label="bid close")
    ax[0].plot(xs, bars["vwap"].to_list(), lw=0.9, label="VWAP")
    for k, style in ((1, ":"), (2, "--"), (3, "-.")):
        ax[0].plot(xs, bars[f"ub{k}"].to_list(), lw=0.7, ls=style)
        ax[0].plot(xs, bars[f"lb{k}"].to_list(), lw=0.7, ls=style)
    ax[0].set_title(f"{args.symbol} {args.date} NY session — close, VWAP ±1/2/3σ")
    ax[0].legend(loc="upper left", fontsize=8)

    ax[1].plot(xs, bars["cvd"].to_list(), lw=0.9)
    ax[1].set_title("CVD (tick-rule, 1m sums)")

    ax[2].barh(prof.bin_low, prof.volume, height=args.bin_size * 0.9)
    for level, style, tag in ((prof.poc, "-", "POC"),
                              (prof.vah, "--", "VAH"), (prof.val, "--", "VAL")):
        ax[2].axhline(level, ls=style, lw=0.9)
        ax[2].text(0.99, level, tag, transform=ax[2].get_yaxis_transform(),
                   ha="right", va="bottom", fontsize=8)
    ax[2].set_title(f"Volume profile (bin {args.bin_size:g})")

    fig.tight_layout()
    out = results_dir("indicators_demo") / f"{args.symbol}_{args.date}.png"
    fig.savefig(out, dpi=90)
    print(f"wrote {out} ({len(bars)} bars, POC {prof.poc})")


if __name__ == "__main__":
    main()

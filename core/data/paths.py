"""Filesystem layout helpers.

All data paths derive from the ``SRJ_DATA`` env var (never hardcoded),
defaulting to ``D:\\SRJ Venture\\data``. The repo itself only holds code,
specs, and small results; ticks/bars/raw live on D:.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATA_ROOT = Path(r"D:\SRJ Venture\data")


def data_root() -> Path:
    """Data root from ``SRJ_DATA`` (User env var, persisted per AGENTS.md)."""
    return Path(os.environ.get("SRJ_DATA", str(DEFAULT_DATA_ROOT)))


def raw_bi5_path(symbol: str, year: int, month0: int, day: int, hour: int) -> Path:
    """Raw Dukascopy file layout: dukascopy/raw/<SYM>/<YYYY>/<MM0>/<DD>/<HH>h_ticks.bi5."""
    return (
        data_root() / "dukascopy" / "raw" / symbol / f"{year:04d}"
        / f"{month0:02d}" / f"{day:02d}" / f"{hour:02d}h_ticks.bi5"
    )


def ticks_month_path(symbol: str, year: int, month: int) -> Path:
    """Monthly tick parquet: ticks/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet."""
    return (
        data_root() / "ticks" / f"symbol={symbol}" / f"year={year:04d}"
        / f"month={month:02d}" / "part.parquet"
    )


def bars_path(symbol: str, tf: str, year: int, month: int | None = None) -> Path:
    """Bar parquet layout (monthly parts).

    bars/symbol=<SYM>/tf=<TF>/year=<YYYY>[/month=<MM>]/part.parquet
    """
    p = data_root() / "bars" / f"symbol={symbol}" / f"tf={tf}" / f"year={year:04d}"
    if month is not None:
        p = p / f"month={month:02d}"
    return p / "part.parquet"


def results_dir(*parts: str) -> Path:
    """Committed small-output dir: <repo>/results/<parts...> (created on demand)."""
    p = REPO_ROOT / "results" / Path(*parts) if parts else REPO_ROOT / "results"
    p.mkdir(parents=True, exist_ok=True)
    return p


def repo_file(*parts: str) -> Path:
    """Path to a file inside the repo (e.g. config/instruments.yaml)."""
    return REPO_ROOT.joinpath(*parts)

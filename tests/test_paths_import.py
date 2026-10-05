"""Tests for SRJ_DATA-driven path layout + MT5 CSV importer."""
from datetime import datetime
from pathlib import Path

from core.data import import_mt5_csv as imp
from core.data import paths


def test_layout_uses_srj_data(monkeypatch, tmp_path):
    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    p = paths.raw_bi5_path("EURUSD", 2023, 0, 2, 3)
    assert p == tmp_path / "dukascopy" / "raw" / "EURUSD" / "2023" / "00" / "02" / "03h_ticks.bi5"
    assert paths.ticks_month_path("EURUSD", 2023, 1).name == "part.parquet"
    assert "symbol=EURUSD" in str(paths.ticks_month_path("EURUSD", 2023, 1))
    assert "tf=5m" in str(paths.bars_path("EURUSD", "5m", 2023, 1))


def test_server_tz_rule():
    assert imp.server_offset_hours(datetime(2026, 1, 15, 12, 0)) == 2
    assert imp.server_offset_hours(datetime(2026, 7, 15, 12, 0)) == 3
    assert imp.server_offset_hours(datetime(2025, 12, 1, 0, 0)) == 2
    assert imp.us_dst_start(2026) == datetime(2026, 3, 8)
    assert imp.us_dst_end(2026) == datetime(2026, 11, 1)
    utc = imp.server_to_utc(datetime(2026, 1, 15, 12, 0))
    assert utc.hour == 10 and utc.utcoffset().total_seconds() == 0


def test_read_mt5_server_csv(tmp_path: Path):
    f = tmp_path / "tiny.csv"
    f.write_text("Date,Time,Bid,Ask,Last,Volume\n"
                 "2026.01.05,00:00:05.041,1.15940,1.15970,0.00000,0\n")
    df = imp.read_mt5_server(f)
    assert len(df) == 1 and df["bid"][0] == 1.15940
    # 2026-01-05 is winter (+2) → 00:00 server = 22:00 UTC previous day
    assert (df["ts"][0].hour, df["ts"][0].day) == (22, 4)


def test_read_dukascopy_node_utc(tmp_path: Path):
    f = tmp_path / "tiny.csv"
    f.write_text("timestamp,askPrice,bidPrice\n2026.08.02 21:00:11.358,1.1552,1.15446\n")
    df = imp.read_dukascopy_node_utc(f)
    assert len(df) == 1 and df["bid"][0] == 1.15446
    assert (df["ts"][0].hour, df["ts"][0].day) == (21, 2)

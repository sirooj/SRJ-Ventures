"""Tests for the Dukascopy URL builder / .bi5 parser (no network)."""
import lzma
import struct
from datetime import datetime, timezone

import polars as pl

from core.data.dukascopy import build_url, hour_range, month0, parse_bi5


def test_month0_zero_based():
    assert month0(datetime(2023, 1, 1)) == 0
    assert month0(datetime(2023, 12, 31)) == 11


def test_build_url_zero_based_month():
    u = build_url("EURUSD", datetime(2023, 1, 2, 3, tzinfo=timezone.utc))
    assert u == ("https://datafeed.dukascopy.com/datafeed/"
                 "EURUSD/2023/00/02/03h_ticks.bi5")
    u = build_url("USA500IDXUSD", datetime(2023, 12, 31, 23, tzinfo=timezone.utc))
    assert "/USA500IDXUSD/2023/11/31/23h_ticks.bi5" in u


def _payload(recs):
    return lzma.compress(b"".join(struct.pack(">IIIff", *r) for r in recs))


def test_parse_bi5_two_ticks():
    recs = [
        (0, 115970, 115940, 1.0, 2.0),      # t=00:00:00.000
        (60000, 115966, 115940, 1.5, 2.5),  # t=00:01:00.000
    ]
    hour = datetime(2025, 12, 1, tzinfo=timezone.utc)
    df = parse_bi5(_payload(recs), hour, point=100_000)
    assert len(df) == 2
    assert df["bid"].to_list() == [1.15940, 1.15940]
    assert df["ask"].to_list() == [1.15970, 1.15966]
    assert df["ts"][0] == datetime(2025, 12, 1, tzinfo=timezone.utc)
    assert df["ts"][1] == datetime(2025, 12, 1, 0, 1, tzinfo=timezone.utc)
    assert df["spread"].to_list()[0] == pl.Series([1.15970 - 1.15940]).to_list()[0]
    assert df["bid_vol"].to_list() == [2.0, 2.5]


def test_parse_bi5_empty_and_garbage():
    hour = datetime(2023, 1, 1, tzinfo=timezone.utc)
    for payload in (b"", lzma.compress(b""), b"not-lzma-at-all"):
        df = parse_bi5(payload, hour, point=100_000)
        assert len(df) == 0
        assert df.columns == ["ts", "bid", "ask", "bid_vol", "ask_vol", "spread"]


def test_hour_range_half_open_and_aligned():
    start = datetime(2023, 1, 1, 0, 30, tzinfo=timezone.utc)
    end = datetime(2023, 1, 1, 3, tzinfo=timezone.utc)
    hours = list(hour_range(start, end))
    assert [h.hour for h in hours] == [0, 1, 2]  # floor-aligned, end-exclusive


def test_convert_merges_and_feed_wins(monkeypatch, tmp_path):
    """convert_month_to_parquet unions with an imported part; feed wins on ts."""
    import lzma as _lzma
    import struct as _struct

    from core.data import dukascopy as dk
    from core.data.paths import raw_bi5_path, ticks_month_path

    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    raw = _lzma.compress(_struct.pack(">IIIff", 0, 112001, 112000, 1.0, 1.0))
    rp = raw_bi5_path("EURUSD", 2026, 8, 28, 0)  # MM0=8 → September
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_bytes(raw)
    # Pre-existing "imported" part with a conflicting ts (bid differs).
    old = pl.DataFrame(
        {
            "ts": [datetime(2026, 9, 28, tzinfo=timezone.utc)],
            "bid": [9.999],
            "ask": [10.0],
            "bid_vol": [0.0],
            "ask_vol": [0.0],
            "spread": [0.001],
        },
        schema={
            "ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
            "bid": pl.Float64, "ask": pl.Float64,
            "bid_vol": pl.Float32, "ask_vol": pl.Float32, "spread": pl.Float64,
        },
    )
    out = ticks_month_path("EURUSD", 2026, 9)
    out.parent.mkdir(parents=True, exist_ok=True)
    old.write_parquet(out)
    assert dk.convert_month_to_parquet("EURUSD", 2026, 9, 100_000) == out
    got = pl.read_parquet(out)
    assert len(got) == 1 and got["bid"][0] == 1.12  # feed value wins

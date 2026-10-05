"""Issue #2 (A.1) tests: empty-hour markers, partial-hour exclusion, --no-convert."""

from datetime import datetime, timedelta, timezone

import httpx

from core.data import dukascopy as dk
from core.data.dukascopy import (
    _fetch_and_store,
    download_range,
    fresh_hours,
    hour_range,
)
from core.data.paths import raw_empty_path


def _404_client(calls: list):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_empty_marker_written_and_respected(monkeypatch, tmp_path):
    """404 → 0-byte .empty marker; second call skips without fetching."""
    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    dt = datetime(2026, 8, 2, 21, tzinfo=timezone.utc)  # Sunday evening
    calls: list = []
    client = _404_client(calls)
    assert _fetch_and_store(client, "EURUSD", dt) == "empty"
    marker = raw_empty_path("EURUSD", 2026, 7, 2, 21)
    assert marker.exists() and marker.stat().st_size == 0
    assert _fetch_and_store(client, "EURUSD", dt) == "exists"
    assert len(calls) == 1  # no second request


def test_fresh_hours_drops_current_and_future():
    now = datetime(2026, 10, 5, 12, 30, tzinfo=timezone.utc)
    hours = list(hour_range(now - timedelta(hours=3), now + timedelta(hours=2)))
    fresh = fresh_hours(hours, now)
    # Kept: hours ending at/before 11:30 → starts ≤ 10:00. Dropped: 11:00..13:00.
    assert [h.hour for h in fresh] == [9, 10]
    assert all(h + timedelta(hours=1) <= now - timedelta(hours=1) for h in fresh)


def test_download_range_skips_partial_hours_no_network(monkeypatch, tmp_path):
    """A fully-future range fetches nothing and counts everything as skipped."""
    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    now = datetime.now(timezone.utc)
    start = (now + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    stats = download_range(["EURUSD"], start, start + timedelta(hours=3),
                           max_workers=1, now=now)
    assert stats == {"stored": 0, "exists": 0, "empty": 0, "failed": 0, "skipped": 3}


def test_main_no_convert_skips_conversion(monkeypatch, tmp_path):
    """--no-convert downloads raws but never calls convert_month_to_parquet."""
    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    converted: list = []
    monkeypatch.setattr(dk, "download_range",
                        lambda *a, **k: {"stored": 0, "exists": 0, "empty": 0,
                                         "failed": 0, "skipped": 0})
    monkeypatch.setattr(dk, "convert_month_to_parquet",
                        lambda *a: converted.append(a))
    dk.main(["download", "--symbols", "EURUSD",
             "--start", "2026-01-01", "--end", "2026-01-02", "--no-convert"])
    assert converted == []

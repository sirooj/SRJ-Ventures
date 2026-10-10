"""Issue #2 (A.1) tests: empty-hour markers, partial-hour exclusion, --no-convert."""

from datetime import datetime, timedelta, timezone

import httpx
import pytest

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


def test_healthy_first_prefers_serving_edge(monkeypatch):
    """TCP-alive 503 edges must sort behind edges that serve (200/404)."""
    import httpx as _httpx

    calls = {"n": 0}

    def fake_probe_get(url, **kwargs):
        # _healthy_first probes IPs in list order: first gets 503, rest 404.
        calls["n"] += 1
        if calls["n"] == 1:
            return _httpx.Response(503)
        return _httpx.Response(404)

    monkeypatch.setattr(dk.httpx, "get", fake_probe_get)
    ranked = dk._healthy_first(["10.0.0.9", "10.0.0.1", "10.0.0.2"])
    assert ranked[0] in ("10.0.0.1", "10.0.0.2")  # 503 edge sinks
    assert ranked[-1] == "10.0.0.9"


def _flaky_client(statuses: list[int], calls: list, body: bytes = b"data"):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(statuses[min(len(calls) - 1, len(statuses) - 1)],
                              content=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


class _FakeTime:
    def __init__(self):
        self.sleeps: list = []

    def sleep(self, s):
        self.sleeps.append(s)


def test_fetch_hour_retries_then_succeeds(monkeypatch):
    """Transient 503s are retried; success on the 3rd attempt returns content."""
    calls: list = []
    client = _flaky_client([503, 503, 200], calls)
    fake = _FakeTime()
    monkeypatch.setattr(dk, "time", fake)
    out = dk.fetch_hour(client, "EURUSD",
                        datetime(2023, 3, 15, 3, tzinfo=timezone.utc))
    assert out == b"data" and len(calls) == 3 and fake.sleeps == [1, 2]


def test_fetch_hour_fail_fast_retries_2(monkeypatch):
    """retries=2 → 2 attempts, backoff sleeps [1, 2], then raises for the CSV."""
    calls: list = []
    client = _flaky_client([503], calls)
    fake = _FakeTime()
    monkeypatch.setattr(dk, "time", fake)
    with pytest.raises(httpx.HTTPStatusError):
        dk.fetch_hour(client, "EURUSD",
                      datetime(2023, 3, 15, 3, tzinfo=timezone.utc), retries=2)
    assert len(calls) == 2 and fake.sleeps == [1, 2]


def test_download_range_threads_retries(monkeypatch, tmp_path):
    """download_range forwards retries to every _fetch_and_store call."""
    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    seen: list = []

    def fake_store(client, sym, dt, retries=5):
        seen.append(retries)
        return "exists"

    monkeypatch.setattr(dk, "_fetch_and_store", fake_store)
    stats = download_range(["EURUSD"], datetime(2026, 1, 1, tzinfo=timezone.utc),
                           datetime(2026, 1, 1, 2, tzinfo=timezone.utc),
                           max_workers=1, retries=2,
                           now=datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert seen == [2, 2] and stats["exists"] == 2


def test_main_retries_flag_default_and_override(monkeypatch, tmp_path):
    """--retries defaults to 5 (unchanged behaviour) and threads through."""
    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    got: dict = {}

    def fake_range(*a, **k):
        got.clear()
        got.update(k)
        return {"stored": 0, "exists": 0, "empty": 0, "failed": 0, "skipped": 0}

    monkeypatch.setattr(dk, "download_range", fake_range)
    base = ["download", "--symbols", "EURUSD",
            "--start", "2026-01-01", "--end", "2026-01-02", "--no-convert"]
    dk.main(base)
    assert got["retries"] == 5
    dk.main(base + ["--retries", "2"])
    assert got["retries"] == 2

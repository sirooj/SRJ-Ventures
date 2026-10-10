"""Dukascopy tick downloader + monthly parquet conversion.

Feed layout (hour in UTC, ``MM0`` is the **zero-based** month, January = ``00``)::

    https://datafeed.dukascopy.com/datafeed/{SYMBOL}/{YYYY}/{MM0}/{DD}/{HH}h_ticks.bi5

File format: LZMA-compressed; records are 20 bytes big-endian ``>IIIff``:
ms offset from the hour start, ask (int), bid (int), ask volume (float),
bid volume (float). An empty file / HTTP 404 means no ticks (weekend/holiday).

Int prices are divided by a per-instrument ``point`` value from
``config/instruments.yaml`` — verified empirically, never assumed.

Downloader behaviour: resume-safe (skips existing files), retries with
exponential backoff (--retries, default 5; lower = fail fast to the failures
CSV for a later pass when the feed 503s), polite concurrency
(<= 6 parallel requests), failed hours logged to a CSV under
``$SRJ_DATA/dukascopy/``.

Usage::

    python -m core.data.dukascopy download --symbols EURUSD,GBPUSD \
        --start 2023-01-01 --end 2023-02-01
    python -m core.data.dukascopy convert --symbol EURUSD --year 2023 --month 1
"""
from __future__ import annotations

import argparse
import csv
import lzma
import socket
import struct
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import polars as pl
import yaml
from tqdm import tqdm

from .paths import (
    data_root,
    raw_bi5_path,
    raw_empty_path,
    repo_file,
    ticks_month_path,
)

FEED = "https://datafeed.dukascopy.com/datafeed"
FEED_HOST = "datafeed.dukascopy.com"
REC = struct.Struct(">IIIff")  # ms_offset, ask_int, bid_int, ask_vol, bid_vol
MAX_WORKERS = 6


# --------------------------------------------------------------------------
# DNS-poisoning workaround (documented, opt-in)
# --------------------------------------------------------------------------
def doh_ips(host: str, timeout: float = 15.0) -> list[str]:
    """Resolve A records via DNS-over-HTTPS (Google, then Cloudflare).

    Needed on networks whose DNS hijacks the feed host (e.g. Telkomsel
    `internetbaik` returns a block-server IP for datafeed.dukascopy.com).
    """
    endpoints = [
        ("https://dns.google/resolve", {"name": host, "type": "A"}),
        ("https://cloudflare-dns.com/dns-query", {"name": host, "type": "A"}),
    ]
    for url, params in endpoints:
        try:
            r = httpx.get(url, params=params,
                          headers={"Accept": "application/dns-json"},
                          timeout=timeout)
            r.raise_for_status()
            ips = [a["data"] for a in r.json().get("Answer", [])
                   if a.get("type") == 1]
            if ips:
                return _healthy_first(ips)
        except httpx.HTTPError:
            continue
    return []


def _healthy_first(ips: list[str], timeout: float = 8.0) -> list[str]:
    """Rank edges by a real HTTPS probe (TCP alone can't see 503s).

    Probes a Saturday hour (expect 404 = edge serves correctly) through each IP
    with SNI/TLS intact. Healthy edges come first ordered by latency; refused
    edges go last. A TCP-only check passes dead edges that answer handshakes
    but 503 every request — this cost us a ~6h near-zero run on 2026-10-06.
    """
    probe_dt = datetime(2023, 1, 7, 12, tzinfo=timezone.utc)  # Saturday
    scored: list[tuple[tuple[int, float], str]] = []
    for ip in ips:
        uninstall = install_resolve_override(FEED_HOST, [ip])
        try:
            t = time.time()
            r = httpx.get(build_url("EURUSD", probe_dt), timeout=timeout,
                          headers={"User-Agent": "SRJ-Ventures-research/0.1"})
            ok = r.status_code in (200, 404)
            scored.append(((0 if ok else 1, time.time() - t), ip))
        except httpx.HTTPError:
            scored.append(((1, float("inf")), ip))
        finally:
            uninstall()
    return [ip for _, ip in sorted(scored)]


_real_getaddrinfo = socket.getaddrinfo


def install_resolve_override(host: str, ips: list[str]):
    """Pin ``host`` to ``ips`` for this process (round-robin over calls).

    Only the lookup is overridden — TLS SNI still uses the real hostname, so
    certificate verification stays fully enabled. Returns an uninstall fn.
    """
    if not ips:
        raise ValueError("no IPs to pin")
    state = {"i": 0}

    def hooked(h, port, *args, **kwargs):
        if h == host:
            ip = ips[state["i"] % len(ips)]
            state["i"] += 1
            return _real_getaddrinfo(ip, port, *args, **kwargs)
        return _real_getaddrinfo(h, port, *args, **kwargs)

    socket.getaddrinfo = hooked  # type: ignore[method-assign]
    return lambda: setattr(socket, "getaddrinfo", _real_getaddrinfo)

TICK_SCHEMA = {
    "ts": pl.Datetime(time_unit="ms", time_zone="UTC"),
    "bid": pl.Float64,
    "ask": pl.Float64,
    "bid_vol": pl.Float32,
    "ask_vol": pl.Float32,
    "spread": pl.Float64,
}


# --------------------------------------------------------------------------
# Pure helpers (unit-tested, no network)
# --------------------------------------------------------------------------
def month0(dt: datetime) -> int:
    """Zero-based month for the Dukascopy URL (January == 0)."""
    return dt.month - 1


def build_url(symbol: str, dt_utc: datetime) -> str:
    """Hour file URL. ``dt_utc`` must be hour-aligned (UTC)."""
    return (
        f"{FEED}/{symbol}/{dt_utc.year:04d}/{month0(dt_utc):02d}/"
        f"{dt_utc.day:02d}/{dt_utc.hour:02d}h_ticks.bi5"
    )


def hour_range(start: datetime, end: datetime):
    """Yield hour-aligned UTC datetimes in [start, end)."""
    cur = start.replace(minute=0, second=0, microsecond=0)
    while cur < end:
        yield cur
        cur += timedelta(hours=1)


def parse_bi5(payload: bytes, hour_start: datetime, point: float) -> pl.DataFrame:
    """Decompress + decode one hour file into a tick DataFrame.

    Columns: ``ts`` (UTC, ms), ``bid``, ``ask``, ``bid_vol``, ``ask_vol``,
    ``spread``. Empty payload → empty frame with the same schema.
    """
    if not payload:
        return pl.DataFrame(schema=TICK_SCHEMA)
    try:
        raw = lzma.decompress(payload)
    except lzma.LZMAError:
        return pl.DataFrame(schema=TICK_SCHEMA)
    if not raw:
        return pl.DataFrame(schema=TICK_SCHEMA)

    n = len(raw) // REC.size
    ms, ask_i, bid_i, ask_v, bid_v = [], [], [], [], []
    for off, a, b, av, bv in REC.iter_unpack(raw[: n * REC.size]):
        ms.append(off)
        ask_i.append(a)
        bid_i.append(b)
        ask_v.append(av)
        bid_v.append(bv)

    base_ms = int(hour_start.timestamp() * 1000)
    bid = [x / point for x in bid_i]
    ask = [x / point for x in ask_i]
    return pl.DataFrame(
        {
            "ts": [base_ms + m for m in ms],
            "bid": bid,
            "ask": ask,
            "bid_vol": bid_v,
            "ask_vol": ask_v,
            "spread": [a - b for a, b in zip(ask, bid)],
        },
        schema=TICK_SCHEMA,
    )


# --------------------------------------------------------------------------
# Network
# --------------------------------------------------------------------------
def fetch_hour(
    client: httpx.Client, symbol: str, dt_utc: datetime, retries: int = 5
) -> bytes | None:
    """Fetch one hour file. Returns ``None`` when there are no ticks (404).

    Raises the last exception after ``retries`` failed attempts (5xx/timeouts).
    """
    url = build_url(symbol, dt_utc)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = client.get(url, timeout=30.0)
            if r.status_code == 404:
                return None  # weekend / holiday — not a failure
            r.raise_for_status()
            return r.content
        except httpx.HTTPStatusError as e:
            last = e
            if e.response.status_code == 404:
                return None
        except (httpx.TransportError, httpx.TimeoutException) as e:
            last = e
        time.sleep(2**attempt)
    assert last is not None
    raise last


def _fetch_and_store(client: httpx.Client, symbol: str, dt: datetime,
                     retries: int = 5) -> str:
    """Fetch one hour and store the raw .bi5 (or an .empty marker).

    Returns: stored / exists / empty / failed is counted by the caller.
    A 0-byte ``<HH>h_ticks.empty`` marker records feed-confirmed empty hours
    (404 or empty body) so resumes skip weekends/holidays without re-requests.
    """
    path = raw_bi5_path(symbol, dt.year, month0(dt), dt.day, dt.hour)
    if path.exists() or raw_empty_path(symbol, dt.year, month0(dt), dt.day, dt.hour).exists():
        return "exists"
    payload = fetch_hour(client, symbol, dt, retries)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not payload:  # None (404) or empty body — nothing to store
        raw_empty_path(symbol, dt.year, month0(dt), dt.day, dt.hour).write_bytes(b"")
        return "empty"
    # Atomic write: a kill mid-download must never leave a truncated .bi5
    # that resume would mistake for a complete (quiet) hour.
    tmp = path.with_suffix(".part")
    tmp.write_bytes(payload)
    tmp.replace(path)
    return "stored"


def fresh_hours(hours: list[datetime], now: datetime) -> list[datetime]:
    """Drop hours that may still be partial: end later than ``now − 1h``.

    The current hour (and any future hour) is excluded so resumes never freeze
    a partial file as complete. Pure function of (hours, now) — tested.
    """
    cutoff = now - timedelta(hours=1)
    return [dt for dt in hours if dt + timedelta(hours=1) <= cutoff]


def download_range(
    symbols: list[str],
    start: datetime,
    end: datetime,
    max_workers: int = MAX_WORKERS,
    retries: int = 5,
    now: datetime | None = None,
) -> dict:
    """Download every hour in [start, end) for each symbol.

    Resume-safe: existing files *and* `.empty` markers are skipped; hours that
    may still be partial (ending after ``now − 1h``) are excluded and counted
    as ``skipped``. ``retries`` bounds the attempts per hour before it is
    logged to the failures CSV for a later pass — pass a low value to fail
    fast when the feed 503s. Returns a stats dict and writes failed hours
    (exceptions after retries) to a CSV under ``$SRJ_DATA``.
    """
    hours = fresh_hours(list(hour_range(start, end)),
                        now or datetime.now(timezone.utc))
    skipped = (len(list(hour_range(start, end))) - len(hours)) * len(symbols)
    stats = {"stored": 0, "exists": 0, "empty": 0, "failed": 0, "skipped": skipped}
    failures: list[tuple[str, str, str]] = []
    total = len(hours) * len(symbols)

    with httpx.Client(headers={"User-Agent": "SRJ-Ventures-research/0.1"}) as client:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futs = {
                pool.submit(_fetch_and_store, client, sym, dt, retries): (sym, dt)
                for sym in symbols
                for dt in hours
            }
            for fut in tqdm(as_completed(futs), total=total, desc="dukascopy"):
                sym, dt = futs[fut]
                try:
                    stats[fut.result()] += 1
                except Exception as e:  # noqa: BLE001 — logged to CSV
                    stats["failed"] += 1
                    failures.append((sym, dt.isoformat(), repr(e)))

    if failures:
        log = data_root() / "dukascopy" / (
            f"failures_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        )
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("w", newline="") as f:
            csv.writer(f).writerow(["symbol", "hour_utc", "error"])
            csv.writer(f).writerows(failures)
        print(f"failed hours logged to {log}")
    return stats


# --------------------------------------------------------------------------
# Conversion raw .bi5 -> monthly ticks parquet
# --------------------------------------------------------------------------
def load_instruments() -> dict:
    """Load ``config/instruments.yaml`` (dukascopy symbols + point values)."""
    with repo_file("config", "instruments.yaml").open() as f:
        return yaml.safe_load(f)


def convert_month_to_parquet(
    symbol: str, year: int, month: int, point: float
) -> Path | None:
    """Concatenate all raw hours of a month into one sorted parquet file.

    Layout: ``ticks/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet``.
    Merges with an existing part (e.g. from ``import_mt5_csv``): on ``ts``
    conflicts the **fresh feed download wins** (authoritative precision +
    volumes). Returns the path, or ``None`` when the month holds no ticks.
    """
    raw_dir = data_root() / "dukascopy" / "raw" / symbol / f"{year:04d}"
    files = sorted(raw_dir.rglob("*.bi5"))
    # Keep only the requested 1-based month: dir name is zero-based MM0.
    files = [p for p in files if int(p.parent.parent.name) == month - 1]
    if not files:
        return None

    frames: list[pl.DataFrame] = []
    for p in files:
        # .../<MM0>/<DD>/<HH>h_ticks.bi5
        hh = int(p.name[:2])
        dd = int(p.parent.name)
        hour_start = datetime(year, month, dd, hh, tzinfo=timezone.utc)
        df = parse_bi5(p.read_bytes(), hour_start, point)
        if len(df):
            frames.append(df)
    if not frames:
        return None

    out = ticks_month_path(symbol, year, month)
    out.parent.mkdir(parents=True, exist_ok=True)
    fresh = pl.concat(frames).sort("ts")
    if out.exists():
        fresh = pl.concat([pl.read_parquet(out), fresh]).unique(
            subset=["ts"], keep="last").sort("ts")
    fresh.write_parquet(out, compression="zstd", statistics=True)
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _parse_day(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Dukascopy tick downloader")
    sub = ap.add_subparsers(dest="cmd", required=True)

    dl = sub.add_parser("download", help="download hours + convert touched months")
    dl.add_argument("--symbols", required=True, help="comma-separated feed symbols")
    dl.add_argument("--start", required=True, help="YYYY-MM-DD (UTC, inclusive)")
    dl.add_argument("--end", required=True, help="YYYY-MM-DD (UTC, inclusive)")
    dl.add_argument("--workers", type=int, default=MAX_WORKERS)
    dl.add_argument("--retries", type=int, default=5,
                    help="attempts per hour before logging it to the failures "
                         "CSV for a later pass (lower = fail fast when the "
                         "feed 503s; default: 5)")
    dl.add_argument("--point", type=float, default=None,
                    help="override point value for all symbols (probing)")
    dl.add_argument("--resolve", default=None, metavar="IP|auto",
                    help="pin feed host to IP, or 'auto' to resolve via DoH "
                         "(for DNS-hijacking ISPs; keeps TLS verification on)")
    dl.add_argument("--no-convert", action="store_true",
                    help="only download raws; skip monthly parquet conversion "
                         "(for unverified point values)")
    dl.add_argument("--convert-symbols", default=None, metavar="SYM,...",
                    help="convert only these symbols (default: all downloaded)")

    cv = sub.add_parser("convert", help="convert one raw month to parquet")
    cv.add_argument("--symbol", required=True)
    cv.add_argument("--year", type=int, required=True)
    cv.add_argument("--month", type=int, required=True)
    cv.add_argument("--point", type=float, default=None)

    args = ap.parse_args(argv)
    cfg = load_instruments()["instruments"]

    if args.cmd == "download":
        symbols = [s.strip() for s in args.symbols.split(",")]
        start = _parse_day(args.start)
        end = _parse_day(args.end) + timedelta(days=1)  # inclusive end day
        uninstall = None
        if args.resolve:
            ips = doh_ips(FEED_HOST) if args.resolve == "auto" else [args.resolve]
            if not ips:
                raise SystemExit("DoH resolution failed — pass --resolve <IP> explicitly")
            uninstall = install_resolve_override(FEED_HOST, ips)
            print(f"pinned {FEED_HOST} -> {ips}")
        try:
            stats = download_range(symbols, start, end, args.workers,
                                   retries=args.retries)
        finally:
            if uninstall:
                uninstall()
        print(stats)
        if args.no_convert:
            return
        convert_set = set(symbols)
        if args.convert_symbols:
            convert_set &= {s.strip() for s in args.convert_symbols.split(",")}
        # Convert every touched month.
        cur = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
        while cur < end:
            for sym in symbols:
                if sym not in convert_set:
                    continue
                feed_sym = cfg[sym]["dukascopy_symbol"]
                point = args.point or cfg[sym]["point"]
                if point is None:
                    print(f"skip convert {sym} {cur:%Y-%m}: point unverified")
                    continue
                out = convert_month_to_parquet(feed_sym, cur.year, cur.month, point)
                print(f"{sym} {cur:%Y-%m}: {out}")
            cur = (cur + timedelta(days=32)).replace(day=1)
    else:
        point = args.point or cfg[args.symbol]["point"]
        if point is None:
            raise SystemExit(f"no verified point for {args.symbol} (see instruments.yaml)")
        print(convert_month_to_parquet(args.symbol, args.year, args.month, point))


if __name__ == "__main__":
    main()

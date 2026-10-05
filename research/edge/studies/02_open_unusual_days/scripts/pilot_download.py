"""Study 02 pilot: download RTH-covering hours (13-20 UTC) on weekdays, via repo code.

Usage: python pilot_download.py SYM1,SYM2 START END WORKERS
Resume-safe (repo _fetch_and_store skips existing files).
Logs to $SRJ_DATA/logs/download_<start>_<end>.log.
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

import httpx

from core.data.dukascopy import _fetch_and_store
from core.data.paths import data_root

HOURS_UTC = range(13, 21)  # 13:00..20:59 UTC covers 09:30-16:00 ET in EDT and EST


def hours(start, end):
    d = start
    while d <= end:
        if d.weekday() < 5:
            for h in HOURS_UTC:
                yield datetime(d.year, d.month, d.day, h, tzinfo=timezone.utc)
        d += timedelta(days=1)


def main():
    syms = sys.argv[1].split(",")
    start = datetime.strptime(sys.argv[2], "%Y-%m-%d")
    end = datetime.strptime(sys.argv[3], "%Y-%m-%d")
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    logdir = data_root() / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    log = open(logdir / f"download_{sys.argv[2]}_{sys.argv[3]}.log", "a")
    jobs = [(s, h) for s in syms for h in hours(start, end)]
    stats = {"stored": 0, "exists": 0, "empty": 0, "failed": 0}
    t0 = time.time()
    with httpx.Client(headers={"User-Agent": "SRJ-Ventures-research/0.1"}) as client:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_fetch_and_store, client, s, h): (s, h) for s, h in jobs}
            for i, f in enumerate(as_completed(futs), 1):
                s, h = futs[f]
                try:
                    stats[f.result()] += 1
                except Exception as e:  # noqa: BLE001
                    stats["failed"] += 1
                    log.write(f"FAIL {s} {h:%Y-%m-%dT%H} {type(e).__name__}: {e}\n")
                if i % 200 == 0 or i == len(jobs):
                    log.write(f"{i}/{len(jobs)} {stats} {time.time() - t0:.0f}s\n")
                    log.flush()
    print(f"jobs={len(jobs)} {stats} elapsed={time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

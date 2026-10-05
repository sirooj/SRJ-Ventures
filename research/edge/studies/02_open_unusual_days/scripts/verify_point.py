"""Verify index point value tick-exact: repo parse_bi5(point=1000) vs dukascopy-node CSV.

Usage: python verify_point.py SYMBOL NODE_CSV [POINT]
Compares every tick in the raw .bi5 hours present for the CSV's first day (UTC).
"""
import csv
import sys
from datetime import datetime, timezone

from core.data.dukascopy import month0, parse_bi5
from core.data.paths import raw_bi5_path


def main():
    sym, path = sys.argv[1], sys.argv[2]
    point = float(sys.argv[3]) if len(sys.argv) > 3 else 1000.0
    ref = {}
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            ref.setdefault(int(row[0]), []).append((float(row[1]), float(row[2])))
    day = datetime.fromtimestamp(min(ref) / 1000, tz=timezone.utc).date()
    n = match = miss = 0
    worst = 0.0
    for h in range(24):
        hs = datetime(day.year, day.month, day.day, h, tzinfo=timezone.utc)
        p = raw_bi5_path(sym, hs.year, month0(hs), hs.day, h)
        if not p.exists():
            continue
        df = parse_bi5(p.read_bytes(), hs, point)
        for ts, ask, bid in zip(df["ts"].to_list(), df["ask"].to_list(), df["bid"].to_list()):
            ts_ms = ts if isinstance(ts, int) else int(ts.timestamp() * 1000)
            n += 1
            cands = ref.get(ts_ms)
            if not cands:
                miss += 1
                continue
            d = min(max(abs(ask - a), abs(bid - b)) for a, b in cands)
            worst = max(worst, d)
            if d < 1e-6:
                match += 1
    print(f"{sym} point={point} day={day} ticks={n} exact={match} ts_missing={miss} "
          f"worst_abs_diff={worst:.6f} -> {'VERIFIED' if n and match == n else 'NOT VERIFIED'}")


if __name__ == "__main__":
    main()

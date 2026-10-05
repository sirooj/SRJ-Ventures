"""Diagnose ts_missing in verify_point: per-hour counts, repo .bi5 vs dukascopy-node CSV."""
import collections
import csv
import sys
from datetime import datetime, timezone

from core.data.dukascopy import month0, parse_bi5
from core.data.paths import raw_bi5_path


def main():
    sym, path = sys.argv[1], sys.argv[2]
    ref_h = collections.Counter()
    ref_ts = set()
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            t = int(row[0])
            ref_ts.add(t)
            ref_h[datetime.fromtimestamp(t / 1000, tz=timezone.utc).hour] += 1
    day = datetime.fromtimestamp(min(ref_ts) / 1000, tz=timezone.utc).date()
    for h in range(24):
        hs = datetime(day.year, day.month, day.day, h, tzinfo=timezone.utc)
        p = raw_bi5_path(sym, hs.year, month0(hs), hs.day, h)
        if not p.exists():
            continue
        df = parse_bi5(p.read_bytes(), hs, 1000.0)
        ts = [t if isinstance(t, int) else int(t.timestamp() * 1000) for t in df["ts"].to_list()]
        miss = sum(1 for t in ts if t not in ref_ts)
        print(f"h{h:02d} bi5={len(ts)} node={ref_h.get(h, 0)} missing_in_node={miss} "
              f"bi5_first={ts[0] if ts else None} bi5_last={ts[-1] if ts else None}")
    print("node hours:", sorted(ref_h.items()))
    print("node max ts:", max(ref_ts), datetime.fromtimestamp(max(ref_ts) / 1000, tz=timezone.utc))


if __name__ == "__main__":
    main()

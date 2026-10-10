"""Study 02: raw .bi5 -> monthly tick parquet -> bid bars (1m/5m/15m/1h), via repo core/data.

Usage: python build_bars.py SYM[,SYM] START_YYYY-MM END_YYYY-MM

Resume-safe. A month is re-converted only when a raw .bi5 is newer than its tick
parquet; `convert_month_to_parquet` de-duplicates on ``ts``. The index point value
is asserted to be the E-011-verified 1000. The yaml's ``point_verified`` flag is
shared infrastructure and is deliberately not edited here.
"""
import sys
import time

from core.data.bars import build_symbol_year
from core.data.dukascopy import convert_month_to_parquet, load_instruments
from core.data.paths import data_root, ticks_month_path

E011_POINT = 1000  # tick-exact vs dukascopy-node for USA500IDXUSD and USATECHIDXUSD (E-011)


def months(a: str, b: str):
    y, m = map(int, a.split("-"))
    yb, mb = map(int, b.split("-"))
    while (y, m) <= (yb, mb):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def newest_raw_mtime(sym: str, y: int, m: int) -> float:
    d = data_root() / "dukascopy" / "raw" / sym / f"{y:04d}" / f"{m - 1:02d}"
    files = list(d.rglob("*.bi5")) if d.exists() else []
    return max((p.stat().st_mtime for p in files), default=0.0)


def main():
    syms = sys.argv[1].split(",")
    inst = load_instruments()["instruments"]
    for sym in syms:
        point = inst[sym]["point"]
        if point != E011_POINT:
            raise SystemExit(f"{sym}: point {point} != E-011 verified {E011_POINT}; stop.")
        for y, m in months(sys.argv[2], sys.argv[3]):
            t0 = time.time()
            dst = ticks_month_path(sym, y, m)
            raw_t = newest_raw_mtime(sym, y, m)
            if raw_t == 0.0:
                print(f"{sym} {y}-{m:02d}: no raw files, skip")
                continue
            if not dst.exists() or raw_t > dst.stat().st_mtime:
                convert_month_to_parquet(sym, y, m, point)
            res = build_symbol_year(sym, y, [m])
            n1 = res.get(f"1m/{m:02d}", (0,))[0]
            print(f"{sym} {y}-{m:02d}: 1m bars={n1} ({time.time() - t0:.1f}s)", flush=True)


if __name__ == "__main__":
    main()

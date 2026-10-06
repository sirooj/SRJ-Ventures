"""Study 02 step 1: does the volume-structure conditioning separate the open's direction?

Implements CARD.md (locked, E-010): features F1-F7 at T in {09:45, 10:05} ET, forward
returns +15/+30/+60 min in ATR14 units, per-bucket n / mean / day-level t / hit rate.

Usage:
  python step1.py --sample SMOKE   # warm-up only (Dec 2022): pipeline check, neither IS nor OOS
  python step1.py --sample IS      # writes IS tables + F3 tercile cuts (IS only)
  python step1.py --sample OOS     # needs the IS outputs; writes OOS tables + kill check

OOS discipline: the IS run never builds a feature for any day after 2025-06-30.

Codification choices (the card is silent; fixed before any IS/OOS data was seen):
- Profiles are built from RTH bid ticks (one tick = one unit), bins of `vp_bin`. The value
  area spans [VAL bin low, VAH bin low + vp_bin); POC = the POC bin's midpoint.
- Bars: 1m bid bars; "bars closed by T" = bars opening before T. close_T = close of the
  09:44 / 10:04 bar. The forward close is the last bar opening at or before T+h-1 min.
- Prior session = the last full NYSE day. It must have >= 95% RTH minute coverage, or the
  day is dropped. ATR14 and RVOL lookbacks use full days with >= 95% coverage only.
- Naked POCs: POCs of the last 5 full sessions not touched by any later RTH session range
  (the overnight session is not in the data, so "naked" means naked in RTH).
- F3: a zero sign(close_T - open) is excluded. F5: a day with both divergences is excluded.
- F6: "first goes below the open" = the first 0.05-ATR excursion from the open is
  downward. The test/tag is judged on the low made before the first 0.05-ATR excursion
  above the open. A day matching two types goes to `unclassified`.
- F7: acceptance = two consecutive 5m closes inside value, the second ending <= 11:00.
  Outcome = the opposite edge is touched after acceptance. The base rate =
  inside-value opens touching the same edge from 09:30, matched by VA-width
  distance decile
  (acceptance close vs open). The base sample has more time to touch, so the comparison is
  conservative for the rule.
- NYSE holidays, half-days and FOMC dates are hard-coded below (verify before step 2).
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from core.data.dukascopy import load_instruments
from core.data.paths import bars_path, data_root, ticks_month_path
from core.indicators.cvd import cvd_from_bars
from core.indicators.volume_profile import fixed_profile
from core.indicators.vwap import session_vwap

NY = "America/New_York"
SYMS = {"NAS100": "USATECHIDXUSD", "US500": "USA500IDXUSD"}
WARMUP_START = date(2022, 11, 15)
SAMPLES = {
    "SMOKE": (date(2022, 12, 1), date(2022, 12, 31)),
    "IS": (date(2023, 1, 1), date(2025, 6, 30)),
    "OOS": (date(2025, 7, 1), date(2026, 9, 30)),
}
T_LIST = {"09:45": 585, "10:05": 605}
HORIZONS = (15, 30, 60)
RTH_OPEN, RTH_CLOSE, SCALP_END, ACCEPT_END = 570, 960, 690, 660

HOLIDAYS = {date.fromisoformat(s) for s in """
2022-11-24 2022-12-26
2023-01-02 2023-01-16 2023-02-20 2023-04-07 2023-05-29 2023-06-19 2023-07-04 2023-09-04
2023-11-23 2023-12-25
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02
2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04
2025-09-01 2025-11-27 2025-12-25
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07
""".split()}
HALF_DAYS = {date.fromisoformat(s) for s in """
2022-11-25 2023-07-03 2023-11-24 2024-07-03 2024-11-29 2024-12-24 2025-07-03 2025-11-28
2025-12-24
""".split()}
FOMC = {date.fromisoformat(s) for s in """
2022-12-14 2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01
2023-12-13 2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07
2024-12-18 2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29
2025-12-10 2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29 2026-09-16
""".split()}

F2_EDGES = (-1.0, -0.25, 0.25, 1.0)
F2_LABELS = ("<-1", "-1..-0.25", "-0.25..0.25", "0.25..1", ">1")


# ---------------------------------------------------------------- calendar / loading
def full_days(start: date, end: date) -> list[date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5 and d not in HOLIDAYS and d not in HALF_DAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


def months(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def _ny_cols(df: pl.DataFrame) -> pl.DataFrame:
    ny = pl.col("ts").dt.convert_time_zone(NY)
    return df.with_columns(
        ny.dt.date().alias("d"),
        (ny.dt.hour().cast(pl.Int32) * 60 + ny.dt.minute().cast(pl.Int32)).alias("mod"))


def _rth(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter((pl.col("mod") >= RTH_OPEN) & (pl.col("mod") < RTH_CLOSE))


def load_rth_bars(sym: str, end: date) -> pl.DataFrame:
    frames = [pl.read_parquet(p) for y, m in months(WARMUP_START, end)
              if (p := bars_path(sym, "1m", y, m)).exists()]
    df = _rth(_ny_cols(pl.concat(frames).unique("ts", keep="last").sort("ts")))
    df = df.filter(pl.col("d") <= end).with_columns(pl.col("d").cast(pl.Utf8).alias("session"))
    df = session_vwap(df, session_col="session")
    return cvd_from_bars(df, session_col="session")


def daily_profiles(sym: str, end: date, vp_bin: float) -> dict[date, dict]:
    out: dict[date, dict] = {}
    for y, m in months(WARMUP_START, end):
        p = ticks_month_path(sym, y, m)
        if not p.exists():
            continue
        t = _rth(_ny_cols(pl.read_parquet(p, columns=["ts", "bid"]))).filter(pl.col("d") <= end)
        for (d,), part in t.group_by("d"):
            bid = part["bid"].to_numpy()
            pr = fixed_profile(bid, np.ones(len(bid)), vp_bin)
            out[d] = {"poc": pr.poc + vp_bin / 2, "va_low": pr.val, "va_high": pr.vah + vp_bin,
                      "hi": float(bid.max()), "lo": float(bid.min())}
    return out


# ---------------------------------------------------------------- features
def bucket_f2(x: float) -> str:
    for edge, lab in zip(F2_EDGES, F2_LABELS):
        if x < edge:
            return lab
    return F2_LABELS[-1]


def f5_divergence(high: np.ndarray, low: np.ndarray, cvd: np.ndarray) -> str:
    def div(price: np.ndarray, sign: int) -> bool:
        best, idx = -math.inf, []
        for i, p in enumerate(price * sign):
            if p > best:
                best = p
                idx.append(i)
        if len(idx) < 2 or idx[-1] - idx[-2] < 3:
            return False
        i, j = idx[-1], idx[-2]
        return bool(cvd[i] < cvd[j]) if sign > 0 else bool(cvd[i] > cvd[j])

    bear, bull = div(high, 1), div(low, -1)
    if bear and bull:
        return "both"
    return "bear_at_high" if bear else ("bull_at_low" if bull else "none")


def _first(mask: np.ndarray):
    w = np.flatnonzero(mask)
    return int(w[0]) if len(w) else None


def f6_opening_type(o, high, low, c, atr, refs_dn, refs_up) -> str:
    hi, lo = float(high.max()), float(low.min())
    rng = hi - lo
    if rng <= 0:
        return "unclassified"
    top, bot = c >= lo + 2 * rng / 3, c <= lo + rng / 3
    mid = not top and not bot
    e05, e10, e15, tag = 0.05 * atr, 0.10 * atr, 0.15 * atr, 0.03 * atr
    dn_i, up_i = _first(low <= o - e05), _first(high >= o + e05)
    down_first = dn_i is not None and (up_i is None or dn_i < up_i)
    up_first = up_i is not None and (dn_i is None or up_i < dn_i)
    lo_test = float(low[:up_i].min()) if up_i else lo   # low made before any up-excursion
    hi_test = float(high[:dn_i].max()) if dn_i else hi
    tag_dn = any(lo_test - tag <= r <= o for r in refs_dn)
    tag_up = any(o <= r <= hi_test + tag for r in refs_up)
    m = []
    if lo >= o - e05 and top and c >= o + e15:
        m.append("OD_up")
    if hi <= o + e05 and bot and c <= o - e15:
        m.append("OD_dn")
    if down_first and tag_dn and top and c > o:
        m.append("OTD_up")
    if up_first and tag_up and bot and c < o:
        m.append("OTD_dn")
    if down_first and lo_test <= o - e10 and not tag_dn and top and c > o:
        m.append("ORR_up")
    if up_first and hi_test >= o + e10 and not tag_up and bot and c < o:
        m.append("ORR_dn")
    if hi >= o + e05 and lo <= o - e05 and mid:
        m.append("OA")
    return m[0] if len(m) == 1 else "unclassified"


def f7_setup(b: dict, prof: dict) -> dict | None:
    """80% rule for one day. Returns None unless the open is outside value."""
    o, vl, vh = b["open"][0], prof["va_low"], prof["va_high"]
    side = "from_above" if o > vh else ("from_below" if o < vl else None)
    if side is None:
        return None
    mod, close = b["mod"], b["close"]
    blk = (mod - RTH_OPEN) // 5
    starts, acc_end, acc_close, prev_in = [], None, None, False
    for k in range((ACCEPT_END - RTH_OPEN) // 5):  # 5m blocks ending <= 11:00
        sel = np.flatnonzero(blk == k)
        if not len(sel):
            prev_in = False
            continue
        cl = close[sel[-1]]
        inside = vl <= cl <= vh
        if inside and prev_in:
            acc_end, acc_close = RTH_OPEN + 5 * (k + 1), cl
            break
        prev_in = inside
        starts.append(k)
    if acc_end is None:
        return {"side": side, "accepted": False}
    after = mod >= acc_end
    w = vh - vl
    if side == "from_above":
        dist = (acc_close - vl) / w
        hit = lambda lim: bool(np.any(b["low"][after & (mod < lim)] <= vl))  # noqa: E731
    else:
        dist = (vh - acc_close) / w
        hit = lambda lim: bool(np.any(b["high"][after & (mod < lim)] >= vh))  # noqa: E731
    return {"side": side, "accepted": True, "decile": min(int(max(dist, 0) * 10), 9),
            "hit_1130": hit(SCALP_END), "hit_1600": hit(RTH_CLOSE)}


def f7_base(b: dict, prof: dict) -> dict | None:
    o, vl, vh = b["open"][0], prof["va_low"], prof["va_high"]
    if not (vl <= o <= vh) or vh <= vl:
        return None
    w, mod = vh - vl, b["mod"]
    out = {}
    for side, dist, touch in (("from_above", (o - vl) / w, b["low"] <= vl),
                              ("from_below", (vh - o) / w, b["high"] >= vh)):
        out[side] = {"decile": min(int(dist * 10), 9),
                     "hit_1130": bool(np.any(touch & (mod < SCALP_END))),
                     "hit_1600": bool(np.any(touch))}
    return out


# ---------------------------------------------------------------- per-symbol day table
def build_days(name: str, sym: str, start: date, end: date, vp_bin: float):
    bars = load_rth_bars(sym, end)
    prof = daily_profiles(sym, end, vp_bin)
    cols = ["mod", "open", "high", "low", "close", "tick_count", "vwap", "cvd"]
    byday = {d: {c: part[c].to_numpy() for c in cols}
             for (d,), part in bars.group_by("d", maintain_order=True)}
    cal = full_days(WARMUP_START, end)
    cov_rth = {d: len(v["mod"]) / (RTH_CLOSE - RTH_OPEN) for d, v in byday.items()}
    cov_open = {d: int(np.sum(v["mod"] < SCALP_END)) / (SCALP_END - RTH_OPEN)
                for d, v in byday.items()}
    good_rth = [d for d in cal if cov_rth.get(d, 0) >= 0.95 and d in prof]
    good_open = [d for d in cal if cov_open.get(d, 0) >= 0.95]
    tc = {(d, tn): float(byday[d]["tick_count"][byday[d]["mod"] < tm].sum())
          for d in good_open for tn, tm in T_LIST.items()}

    rows, f7_rows, drops = [], [], {"coverage": 0, "prior_incomplete": 0, "warmup": 0}
    for i, d in enumerate(cal):
        if not (start <= d <= end):
            continue
        if cov_open.get(d, 0) < 0.95:
            drops["coverage"] += 1
            continue
        prior = cal[i - 1] if i > 0 else None
        if prior is None or prior not in good_rth:
            drops["prior_incomplete"] += 1
            continue
        atr_days = [x for x in good_rth if x < d][-14:]
        rvol_days = [x for x in good_open if x < d][-20:]
        if len(atr_days) < 14 or len(rvol_days) < 20:
            drops["warmup"] += 1
            continue
        atr = float(np.mean([prof[x]["hi"] - prof[x]["lo"] for x in atr_days]))
        p = prof[prior]
        w = p["va_high"] - p["va_low"]
        later = [x for x in prof if x < d]
        naked = []
        for s in [x for x in good_rth if x < d][-5:]:
            poc = prof[s]["poc"]
            if not any(prof[x]["lo"] <= poc <= prof[x]["hi"] for x in later if x > s):
                naked.append(poc)
        b = byday[d]
        o = float(b["open"][0])
        if b["mod"][0] != RTH_OPEN or w <= 0:
            drops["coverage"] += 1
            continue
        f1 = "above_VAH" if o > p["va_high"] else ("below_VAL" if o < p["va_low"] else "inside")
        f2 = bucket_f2((o - p["poc"]) / w)
        refs_dn = [p["va_low"], p["poc"], p["lo"], *naked]
        refs_up = [p["va_high"], p["poc"], p["hi"], *naked]
        for tn, tm in T_LIST.items():
            sel = b["mod"] < tm
            if sel.sum() < 5 or b["mod"][sel][-1] < tm - 3:
                continue
            hi_, lo_, cl_ = b["high"][sel], b["low"][sel], b["close"][sel]
            c = float(cl_[-1])
            last5 = cl_[-5:] - b["vwap"][sel][-5:]
            f4 = "all_above" if (last5 > 0).all() else ("all_below" if (last5 < 0).all()
                                                        else "mixed")
            row = {"symbol": name, "d": d, "T": tn, "fomc": d in FOMC, "atr14": atr,
                   "open": o, "close_T": c, "F1": f1, "F2": f2,
                   "rvol": tc[(d, tn)] / np.mean([tc[(x, tn)] for x in rvol_days]),
                   "dir": int(np.sign(c - o)), "F4": f4,
                   "F5": f5_divergence(hi_, lo_, b["cvd"][sel]),
                   "F6": f6_opening_type(o, hi_, lo_, c, atr, refs_dn, refs_up)}
            for h in HORIZONS:
                fsel = b["mod"] <= tm + h - 1
                fm = b["mod"][fsel][-1]
                fwd = float(b["close"][fsel][-1]) - c if fm >= tm + h - 6 else math.nan
                row[f"r{h}_pts"], row[f"r{h}"] = fwd, fwd / atr
            rows.append(row)
        st, base = f7_setup(b, p), f7_base(b, p)
        if st and st["accepted"]:
            f7_rows.append({"symbol": name, "d": d, "kind": "setup", **st})
        if base:
            for side, v in base.items():
                f7_rows.append({"symbol": name, "d": d, "kind": "base", "side": side, **v})
    return pl.DataFrame(rows), pl.DataFrame(f7_rows), drops


# ---------------------------------------------------------------- statistics
def bucket_stats(x: np.ndarray, pts: np.ndarray) -> dict:
    x, pts = x[~np.isnan(x)], pts[~np.isnan(pts)]
    n = len(x)
    sd = float(np.std(x, ddof=1)) if n > 1 else math.nan
    t = float(np.mean(x) / (sd / math.sqrt(n))) if n > 1 and sd > 0 else math.nan
    return {"n": n, "mean_atr": float(np.mean(x)) if n else math.nan, "t": t,
            "hit": float(np.mean(x > 0)) if n else math.nan,
            "mean_pts": float(np.mean(pts)) if n else math.nan}


def grid_table(days: pl.DataFrame, cuts: dict) -> pl.DataFrame:
    rows = []
    for (name, tn), part in days.group_by(["symbol", "T"], maintain_order=True):
        c1, c2 = cuts[name][tn]
        part = part.with_columns(
            pl.when(pl.col("rvol") < c1).then(pl.lit("lo"))
            .when(pl.col("rvol") < c2).then(pl.lit("mid")).otherwise(pl.lit("hi"))
            .alias("_terc"))
        part = part.with_columns(
            pl.when(pl.col("dir") == 0).then(pl.lit("excluded"))
            .otherwise(pl.col("_terc") + pl.when(pl.col("dir") > 0).then(pl.lit("_up"))
                       .otherwise(pl.lit("_dn"))).alias("F3"))
        for feat in ("F1", "F2", "F3", "F4", "F5", "F6"):
            for (bk,), g in part.group_by(feat, maintain_order=True):
                if bk in ("excluded", "both"):
                    continue
                for h in HORIZONS:
                    s = bucket_stats(g[f"r{h}"].to_numpy(), g[f"r{h}_pts"].to_numpy())
                    rows.append({"symbol": name, "T": tn, "horizon": h, "feature": feat,
                                 "bucket": bk, **s})
    return pl.DataFrame(rows).sort(["symbol", "feature", "bucket", "T", "horizon"])


def f7_table(f7: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for name in f7["symbol"].unique().sort().to_list():
        for side in ("from_above", "from_below"):
            setup = f7.filter((pl.col("symbol") == name) & (pl.col("kind") == "setup")
                              & (pl.col("side") == side))
            base = f7.filter((pl.col("symbol") == name) & (pl.col("kind") == "base")
                             & (pl.col("side") == side))
            for hz in ("hit_1130", "hit_1600"):
                rate = {k: v for k, v in base.group_by("decile").agg(pl.col(hz).mean()).rows()}
                p = np.array([rate.get(k, math.nan) for k in setup["decile"].to_list()])
                hits = setup[hz].to_numpy().astype(float)
                ok = ~np.isnan(p)
                n, exp_ = int(ok.sum()), float(p[ok].sum())
                var = float((p[ok] * (1 - p[ok])).sum())
                z = (hits[ok].sum() - exp_) / math.sqrt(var) if var > 0 else math.nan
                rows.append({"symbol": name, "side": side, "outcome": hz, "n_setups": n,
                             "hit_rate": hits[ok].mean() if n else math.nan,
                             "base_rate": exp_ / n if n else math.nan,
                             "diff_pp": 100 * (hits[ok].mean() - exp_ / n) if n else math.nan,
                             "z": z, "n_base": len(base)})
    return pl.DataFrame(rows)


def kill_check(is_t: pl.DataFrame, oos_t: pl.DataFrame) -> pl.DataFrame:
    key = ["symbol", "T", "horizon", "feature", "bucket"]
    j = is_t.join(oos_t, on=key, how="left", suffix="_oos")
    look = {tuple(r[k] for k in key): r for r in oos_t.iter_rows(named=True)}
    other = {"NAS100": "US500", "US500": "NAS100"}
    adj = {15: (30,), 30: (15, 60), 60: (30,)}
    out = []
    for r in j.iter_rows(named=True):
        sgn = np.sign(r["mean_atr"]) if r["mean_atr"] == r["mean_atr"] else 0
        c1 = r["n"] >= 40 and (r["n_oos"] or 0) >= 40
        to = r["t_oos"]
        c3 = bool(to is not None and to == to and np.sign(to) == sgn and abs(to) >= 1.5)
        alts = [look.get((other[r["symbol"]], r["T"], r["horizon"], r["feature"], r["bucket"]))]
        alts += [look.get((r["symbol"], r["T"], h, r["feature"], r["bucket"]))
                 for h in adj[r["horizon"]]]
        c4 = any(a and a["t"] == a["t"] and np.sign(a["t"]) == sgn and abs(a["t"]) >= 1.0
                 for a in alts)
        c5 = abs(r["mean_atr"]) >= 0.05 if r["mean_atr"] == r["mean_atr"] else False
        out.append({**r, "c1_n": c1, "c2_is_t": abs(r["t"]) >= 2.0 if r["t"] == r["t"] else False,
                    "c3_oos_t": c3, "c4_robust": c4, "c5_size": c5,
                    "survives": all((c1, abs(r["t"]) >= 2.0 if r["t"] == r["t"] else False,
                                     c3, c4, c5))})
    return pl.DataFrame(out)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", choices=list(SAMPLES), required=True)
    ap.add_argument("--symbols", default="NAS100,US500")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    start, end = SAMPLES[a.sample]
    out = Path(a.out or data_root().parent / "results" / "study02")
    out.mkdir(parents=True, exist_ok=True)
    inst = load_instruments()["instruments"]
    days_all, f7_all = [], []
    for name in a.symbols.split(","):
        sym = SYMS[name]
        days, f7, drops = build_days(name, sym, start, end, float(inst[sym]["vp_bin"]))
        print(f"{name} {a.sample}: days={days['d'].n_unique() if len(days) else 0} "
              f"drops={drops}", flush=True)
        days_all.append(days)
        f7_all.append(f7)
    days_all = [x for x in days_all if len(x)]
    if not days_all:
        raise SystemExit("no usable days: check coverage / data")
    days, f7 = pl.concat(days_all), pl.concat([x for x in f7_all if len(x)], how="diagonal")
    days.write_parquet(out / f"days_{a.sample}.parquet")
    f7.write_parquet(out / f"f7_days_{a.sample}.parquet")

    cuts_path = out / ("cuts_SMOKE.json" if a.sample == "SMOKE" else "cuts_IS.json")
    if a.sample in ("IS", "SMOKE"):
        cuts = {n: {tn: [float(q) for q in np.quantile(
                    days.filter((pl.col("symbol") == n) & (pl.col("T") == tn))["rvol"]
                    .to_numpy(), [1 / 3, 2 / 3])] for tn in T_LIST}
                for n in days["symbol"].unique().to_list()}
        cuts_path.write_text(json.dumps(cuts, indent=1))
    else:
        if not cuts_path.exists():
            raise SystemExit("OOS needs cuts_IS.json from the IS run first.")
        cuts = json.loads(cuts_path.read_text())

    tab, f7t = grid_table(days, cuts), f7_table(f7)
    tab.write_csv(out / f"step1_{a.sample}.csv")
    f7t.write_csv(out / f"step1_f7_{a.sample}.csv")
    print(f"grid rows={len(tab)} (F1-F6) + F7 rows={len(f7t)}")
    print("F6 counts:", days.group_by(["symbol", "T", "F6"]).len().sort("len").tail(8).rows())
    if a.sample == "OOS":
        kc = kill_check(pl.read_csv(out / "step1_IS.csv"), tab)
        kc.write_csv(out / "step1_kill.csv")
        print("survivors (F1-F6):", kc.filter(pl.col("survives")).height)
        print(kc.filter(pl.col("survives")).select(
            ["symbol", "T", "horizon", "feature", "bucket", "n", "mean_atr", "t", "n_oos",
             "mean_atr_oos", "t_oos"]))
        is7 = pl.read_csv(out / "step1_f7_IS.csv")
        j7 = is7.join(f7t, on=["symbol", "side", "outcome"], suffix="_oos")
        j7 = j7.with_columns(((pl.col("diff_pp") >= 10) & (pl.col("z") >= 2)
                              & (pl.col("diff_pp_oos") >= 10) & (pl.col("z_oos") >= 1.5))
                             .alias("survives"))
        j7.write_csv(out / "step1_f7_kill.csv")
        print("F7:", j7.select(["symbol", "side", "outcome", "n_setups", "diff_pp", "z",
                                "n_setups_oos", "diff_pp_oos", "z_oos", "survives"]))
    else:
        cand = tab.filter((pl.col("n") >= 40) & (pl.col("t").abs() >= 2.0)
                          & (pl.col("mean_atr").abs() >= 0.05))
        print(f"{a.sample} candidates (n>=40, |t|>=2, |mean|>=0.05): {cand.height}")
        print(cand.select(["symbol", "T", "horizon", "feature", "bucket", "n", "mean_atr", "t"]))
        print(f7t)


if __name__ == "__main__":
    main()

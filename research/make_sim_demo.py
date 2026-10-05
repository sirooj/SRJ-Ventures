"""Prop-firm sim demo: dummy random-entry strategy on EURUSD 2026-03 1m bars.

Generates seeded random trades (fixed fractional risk), runs our simulator +
Monte Carlo, then cross-checks P(pass) through the LuxAlgo oracle
(`npx @luxalgo/prop-firm-sim-cli`, FTMO 100k 2-step) on the same R-multiples.
Writes small JSON/MD to ``results/sim_demo/`` (committed).

Usage:: ``python research/make_sim_demo.py``
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import polars as pl  # noqa: E402

from core.data.paths import repo_file, results_dir  # noqa: E402
from core.propfirm.rules import load_rules  # noqa: E402
from core.propfirm.sim import monte_carlo, run_attempt  # noqa: E402

INITIAL = 100_000.0
RISK_USD = 500.0  # 0.5% of initial per trade
SEED = 42
N_TRADES = 40


def build_trades(bars: pl.DataFrame, seed: int = SEED) -> list[dict]:
    """Random entries: SL 20–60 pips, TP at 1.5–2.5R, 24h timeout, costs = spread."""
    rng = random.Random(seed)
    ts = bars["ts"].to_list()
    closes = bars["close"].to_list()
    spread = bars["spread_mean"].to_list()
    n = len(ts)
    trades = []
    step = max(1, n // N_TRADES)
    for i in range(0, n - 500, step):
        side = rng.choice([1, -1])
        entry = closes[i]
        sl_d = rng.uniform(0.0020, 0.0060)
        tp_d = sl_d * rng.uniform(1.5, 2.5)
        sl = entry - side * sl_d
        tp = entry + side * tp_d
        size = RISK_USD / sl_d  # $500 risk per trade (multiplier 1 = USD)
        exit_ts, exit_px = ts[min(i + 1440, n - 1)], closes[min(i + 1440, n - 1)]
        for j in range(i + 1, min(i + 1441, n)):
            bar_h = bars["high"][j]
            bar_l = bars["low"][j]
            hit_tp = (bar_h >= tp) if side > 0 else (bar_l <= tp)
            hit_sl = (bar_l <= sl) if side > 0 else (bar_h >= sl)
            if hit_tp or hit_sl:
                exit_ts = ts[j]
                exit_px = tp if hit_tp and not hit_sl else sl
                if hit_tp and hit_sl:  # same-bar ambiguity: conservative = SL
                    exit_px = sl
                break
        trades.append({"entry_ts": ts[i], "exit_ts": exit_ts, "symbol": "EURUSD",
                       "side": side, "size": size, "entry_price": entry,
                       "exit_price": exit_px, "multiplier": 1.0,
                       "costs": spread[i] * size})
    return trades


def main() -> None:
    from core.data.paths import bars_path

    bars = pl.read_parquet(bars_path("EURUSD", "1m", 2026, 3)).sort("ts")
    rules = load_rules(repo_file("docs", "propfirm_rules", "ftmo_2step_standard.yaml"))
    trades = build_trades(bars)
    r = run_attempt(trades, bars, rules, INITIAL, phase=0)
    mc = monte_carlo(trades, bars, rules, INITIAL, fee=540.0, seed=SEED, n_paths=50)

    # LuxAlgo cross-check on identical R-multiples.
    rmults = [((t["side"] * (t["exit_price"] - t["entry_price"]) * t["size"]
                - t["costs"]) / RISK_USD) for t in trades]
    out = results_dir("sim_demo")
    (out / "r_multiples.txt").write_text(
        "\n".join(f"{x:.4f}" for x in rmults), encoding="utf-8")
    days = len({t["exit_ts"].date() for t in trades})
    lux = subprocess.run(
        "npx --yes @luxalgo/prop-firm-sim-cli simulate "
        "--firm ftmo --challenge ftmo-normal-challenge-2-steps-100k "
        f"--r-series-file \"{out / 'r_multiples.txt'}\" "
        "--risk 0.5% --risk-mode percent-of-initial "
        f"--trades-per-day {len(trades) / max(days, 1):.2f} "
        "--paths 10000 --seed 42",
        capture_output=True, text=True, timeout=600, shell=True)
    (out / "luxalgo.txt").write_text(lux.stdout + "\n--- STDERR ---\n" + lux.stderr,
                                    encoding="utf-8")
    (out / "ours.json").write_text(json.dumps(
        {"single_attempt": r.__dict__, "monte_carlo": mc,
         "n_trades": len(trades), "note": "dummy random entries, March 2026"},
        indent=2, default=str), encoding="utf-8")

    p_ours = mc["p_pass_all"]
    p_lux = None
    for line in lux.stdout.splitlines():
        if "Pass probability per attempt" in line:
            p_lux = line.strip()
    (out / "compare.md").write_text(
        "# Sim cross-check (FTMO 100k 2-step, dummy strategy)\n\n"
        f"- ours P(pass all): {p_ours:.3f} (50 seeded paths, adverse-extreme marking)\n"
        f"- LuxAlgo: {p_lux}\n\n"
        "Expectation: where trades carry no adverse excursion the two agree within MC\n"
        "noise; where they differ ours must be lower (LuxAlgo observes equity at trade\n"
        "close only — see its rule-semantics doc; our open questions in the PR).\n"
        "Semantic deltas vs our YAMLs: (1) LuxAlgo allows allowance-as-%-of-anchor\n"
        "(`limitBasis: anchor`) — our schema covers it via `pct_of: reference`, FTMO uses\n"
        "`initial` on both; (2) their `basis` lacks our max(balance,equity) conservative\n"
        "superset for The5ers; (3) they model consistency dilution + risk-free min-day\n"
        "grind, ours fails hard (stricter); (4) failure attribution identical\n"
        "(higher floor wins).\n", encoding="utf-8")
    print(f"trades={len(trades)} p_ours={p_ours:.3f} lux={p_lux}")


if __name__ == "__main__":
    main()

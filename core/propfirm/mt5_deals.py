"""MT5 deal-tape → simulator trade-list converter.

Input: deal dicts as exported by the terminal / ``read_tester_report`` detail
rows: ``time`` (aware datetime), ``symbol``, ``side`` (+1 buy / −1 sell),
``volume``, ``price``. Netting is FIFO per symbol: closes match the earliest
open entries (partial closes split lots); a flip closes the remainder and
opens the opposite side. Costs default to 0 — pass explicit per-trade costs
(spread/commission) where known.

Output: trade dicts for ``core.propfirm.sim.run_attempt`` (entry/exit ts,
symbol, side, size, entry/exit price, costs, multiplier). **No EA source or
parameters touch this module.**
"""
from __future__ import annotations


def deals_to_trades(deals: list[dict], multiplier: float = 1.0,
                    costs_per_unit: float = 0.0) -> list[dict]:
    """Net a chronologically ordered deal tape into round-trip trades."""
    booked: list[dict] = []   # open entries: {ts, symbol, side, vol, price}
    trades: list[dict] = []
    for d in sorted(deals, key=lambda x: x["time"]):
        side, vol = d["side"], float(d["volume"])
        while vol > 0:
            match = next((b for b in booked
                          if b["symbol"] == d["symbol"] and b["side"] == -side), None)
            if match is None:  # opening deal
                booked.append({"ts": d["time"], "symbol": d["symbol"],
                               "side": side, "vol": vol, "price": d["price"]})
                vol = 0
            else:
                lot = min(vol, match["vol"])
                entry_side = match["side"]
                trades.append({
                    "entry_ts": match["ts"], "exit_ts": d["time"],
                    "symbol": d["symbol"], "side": entry_side, "size": lot,
                    "entry_price": match["price"], "exit_price": d["price"],
                    "multiplier": multiplier,
                    "costs": costs_per_unit * lot * 2,
                })
                match["vol"] -= lot
                vol -= lot
                if match["vol"] <= 0:
                    booked.remove(match)
    return trades

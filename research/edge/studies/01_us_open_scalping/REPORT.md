# Edge research log: US index open scalping

**Track:** a new edge, separate from Flow Nexus. Researcher: 3 SRJ Venture Bot. Orchestrator: sirooj.
**Data:** Dukascopy 1-minute bid and ask bars, Oct 2025 – Sep 2026 (256 full NY sessions).
- Parameters are chosen on Oct 2025 – May 2026 (in-sample).
- They are then tested unchanged on Jun – Sep 2026 (out-of-sample).

## Step 1: cost vs movement
This compares the median 15-minute high–low range with the median spread plus commission.

| Session (ET) | NAS100 | US500 | USDJPY | EURUSD / GBPUSD (partial data) |
|---|---|---|---|---|
| NY open 09:30–11:30 | 68× | 26× | 12× | 9.5× |
| NY mid 11:30–15:00 | 40× | 17× | 7× | 5–6× |
| London 03:00–08:00 | 27× | 8× | 8× | 7× |
| Asia / off-hours | 22× | 6× | 7× | 3–4× |

The best window of the day is 09:30–09:45 ET on NAS100, at about 100×.

## Step 2: does the opening move carry direction?
All tests take one trade per day.
- Entries are blocked between 09:55 and 10:05 (10:00 ET news releases).
- Every trade has a visible stop and holds at least 3 minutes before any take-profit.
- Each strategy is flat by 15:55.
- Stress slippage per side: NAS100 1.0 point, US500 0.25 point.

### A. Opening-range breakout (48 configurations)
Grid: opening range 5, 15 or 30 minutes; stop at the opposite side or the midpoint; take-profit 1R, 1.5R, 2R or none (time exit).

| | NAS100 | US500 |
|---|---|---|
| In-sample configs with positive mean R | 15% | 2% |
| Out-of-sample configs with positive mean R | 2% | 46% (noise) |
| In-sample winners still positive out-of-sample | 0 of 7 | 0 of 1 |
| Best in-sample config, full-year mean R | −0.006 | 0.001 |
| With zero slippage: out-of-sample configs positive | 2% | 52% |
| FTMO 2-step, rolling start every day | 0 passes | 0 passes |

### B. Fading the first break back to the opening-range midpoint (18 configurations)
- With a 5-minute range, the fade loses clearly in-sample (t from −2.0 to −2.7). That means early breaks continue a little, but not by enough to pay for a breakout trade.
- With 15- and 30-minute ranges, the fade is flat: mean R stays within about ±0.1, and no configuration reaches |t| > 1.1 in both periods.

### C. Intraday momentum (Gao et al.)
The signal is the sign of the move from the prior close to 10:00. The trade runs from 15:30 to 15:59.

| | In-sample | Out-of-sample |
|---|---|---|
| NAS100 | −1.3 pts/day, t = −0.3 | +13.8 pts/day, t = 1.8 |
| US500 | −0.9 pts/day, t = −1.0 | +0.8 pts/day, t = 0.6 |

Round-trip cost is about 3 points on NAS100 and about 1 point on US500. The sign flips between periods, so this isn't a usable edge.

## Verdict
The open moves a lot, but on these tests that movement doesn't predict direction.
- With about 250 trades, the standard error is about 0.06R. Any edge larger than about 0.13R per trade is ruled out.
- An edge small enough to hide in that noise wouldn't pass a challenge at one trade per day anyway.

## Caveats
- Only 12 months of data.
- Only unconditioned rules were tested: no filters on gap size, range width versus ATR, relative volume, or news days.
- Dukascopy spreads are tighter than FTMO and The5ers spreads, but the result is null even with zero slippage.

## Files on the bot's VM
Scripts are in `/workspace/research/`: `cost_map.py`, `orb.py`, `diag.py`. Outputs are in `out/`.

## Backup note (2026-10-06)
The VM files listed above were lost when session 1 hit its usage limit and were never pushed. The numbers in this report are the only surviving record. Re-derive them if they are ever needed (E-006).

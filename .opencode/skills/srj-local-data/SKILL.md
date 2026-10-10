---
name: srj-local-data
description: Downloading, verifying, converting and preparing Dukascopy data on sirooj's machine. CODER only. Use before any study or backtest that needs ticks or bars, in either track.
---

# SRJ local data (D-006, D-011, D-014, D-023, E-011, E-014)

All market data lives under `SRJ_DATA` (`D:\SRJ Venture\data`). Both tracks use the same dataset; never keep a second copy.

1. **Check before downloading.** List what `SRJ_DATA` already has for the symbol and date range. That includes #2's full-history download and sirooj's existing archives. Download only the gaps.
2. **Pilot first** (AGENTS §4). Start with one month per new symbol. Report the time taken and the disk used per symbol-year, then scale up.
3. **Download** with `core/data/dukascopy.py`, or the study's own downloader if the card names one.
   - Use the same resolution #2 uses (DoH via `--resolve auto` or the pinned IP), with TLS intact.
   - Write `.bi5` files atomically. Never cache the current UTC hour (D-014).
   - Run long downloads in the background, with a progress log on D:.
   - Dukascopy throttles, so keep the worker count modest. Finish with a 1-worker fill pass for missed hours.
4. **Verify** index point values tick-exact before converting.
   - Already verified (E-011): `USA500IDXUSD` and `USATECHIDXUSD` use `point=1000`.
   - dukascopy-node can drop hours silently. It is not a completeness reference.
5. **Convert, build bars, run QA** with `core/data/bars.py` and `core/data/qa.py`. Use the bid side for price and volume, and UTC timestamps.
6. **Report** in the CODER report: symbols, date range, disk used, gaps or missing hours, and the QA verdict.
7. **Rules:**
   - Scripts read `SRJ_DATA` from the environment. No hardcoded paths, and no leftover VM paths from older studies.
   - Never commit data.
   - Never feed the edge track's forward holdout (2026-10-01 onward, E-013) into a study run unless the planner says so.

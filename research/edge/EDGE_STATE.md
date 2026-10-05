# SRJ Edge Research: STATE (session pointer)

> **Read this first in every edge-research session.** This track is separate from the Flow Nexus track (`docs/STATE.md`). Don't mix them.
> **Owner:** the RESEARCHER updates this file in every backup relay, and the CODER commits it verbatim.

_Last updated: 2026-10-06 (researcher session 2, PromptQL project "4 SRJ Venture", bot `7b7cb100-a425-4362-aed4-732283e70666`), backup 02a_

---

## 1. How to resume

**sirooj pastes only this:**
```
@<bot name> Resume SRJ Edge Research. Read research/edge/EDGE_STATE.md (+ research/edge/DECISIONS_EDGE.md, AGENTS.md §5, .opencode/skills/) in sirooj/SRJ-Ventures, then continue from "Next actions". Latest CODER message: <newest CODER message only, if any>
```

**RESEARCHER on start:** follow the skill `srj-session-start`.

## 2. Track in one paragraph

The goal is a **new** intraday CFD edge for prop-firm challenges, separate from the Flow Nexus port.
- **Constraints:** the project's hard constraints apply in full (`srj-hard-constraints`, E-002).
- **Lens:** volume-first is mandatory (D-005, E-004). Every study leads with a bid-tick volume read: Volume Profile, VWAP, tick-rule CVD, or tick-count relative volume.
- **Style:** scalping is preferred. ≤1H is the chart-timeframe ceiling, not a cap on trade duration (E-003).
- **Evidence:** Dukascopy data the researcher downloads into its own cloud VM (E-009).
- **Scoring:** prop-firm challenge rules, not Sharpe (D-004).

## 3. Roles

| Role | Who | Does |
|---|---|---|
| RESEARCHER | PromptQL bot | Designs and runs studies in its own VM; writes backup relays |
| CODER | OpenCode on sirooj's machine | Commits relays verbatim; opens and merges backup PRs (E-005) |
| OPERATOR | sirooj | Manually orchestrates between the two; domain answers; final say |

GitHub is connected in PromptQL project "4 SRJ Venture" through sirooj's account. The researcher uses it **read-only**. Writes go through the CODER.

## 4. Study log

| # | Study | Status | Result | Report |
|---|---|---|---|---|
| 01 | US index open scalping on NAS100/US500: ORB, ORB fade, Gao intraday momentum | done 2026-10-05 | **Null.** No edge larger than about 0.13R per trade; 0 FTMO passes (E-008) | `studies/01_us_open_scalping/REPORT.md` |
| 02 | NY open on unusual days, read through volume structure | **in progress**: card locked (E-010); index points verified (E-011); full data download running on the researcher's VM | — | `studies/02_open_unusual_days/CARD.md` |

**Lost:** session 1's scripts (`cost_map.py`, `orb.py`, `diag.py`) and its draft state and decision files lived only on that bot's VM. They were never pushed. E-006 exists to stop this from happening again.

## 5. Next actions

1. **CODER:** commit backup 02a and report the PR number and merge SHA.
2. **RESEARCHER:**
   - Finish the download: NAS100 + US500, 13–20 UTC weekday hours, 2022-11-15 → 2026-09-30, via `studies/02_open_unusual_days/scripts/pilot_download.py`. Re-run once to fill failed hours (resume-safe).
   - Convert to parquet and build 1m bid bars with the repo's `core/data` code.
   - Write `scripts/step1.py` (features F1–F7 from CARD.md, using `core/indicators`). Run IS first, write the IS tables, then run OOS.
   - Back up step-1 results and scripts as backup 02b before step 2.
3. **If the researcher's VM is lost:** the scripts in this backup re-create the data in about 2.5 h (4 workers). Nothing else is needed.
4. **OPERATOR (optional, Flow Nexus track):** E-011's point evidence could let `config/instruments.yaml` mark both indices `point_verified: true`. That file is shared infrastructure, so it changes only through the planner/CODER track, not through an edge backup.

## 6. Study 02 design

Locked in `studies/02_open_unusual_days/CARD.md` (E-010). It supersedes the draft that was here in backup 01. Changes from the draft, all made before any data was seen:
- Decision times fixed at 09:45 and 10:05 ET; forward horizons +15/+30/+60 min, measured in ATR14 units.
- Exact feature buckets, codified Dalton opening-type thresholds, and the 80% rule's base-rate comparison.
- Grid fixed at 344 tests, with a 5-part kill criterion (including cross-index or adjacent-horizon robustness and a minimum mean of 0.05 ATR14).

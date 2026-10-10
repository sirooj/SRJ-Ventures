# SRJ Edge Research: STATE (session pointer)

> **Read this first in every edge-research session.** This track is separate from the Flow Nexus track (`docs/STATE.md`). Don't mix them.
> **Owner:** the PLANNER updates this file and delivers it in a relay; the CODER commits it verbatim (E-014).

_Last updated: 2026-10-10 (planner workflow session, PromptQL project "6 SRJ Venture", bot `15269cb1-95b2-4c4f-b429-fcc7ea935588`), relay WORKFLOW 02 (E-016)_

---

## 1. How to resume

**sirooj pastes only this:**
```
@<bot name> Resume SRJ Edge Research. Read research/edge/EDGE_STATE.md (+ research/edge/DECISIONS_EDGE.md, AGENTS.md §5, .opencode/skills/) in sirooj/SRJ-Ventures, then continue from "Next actions". Latest CODER message: <newest CODER message only, if any>
```

- **PLANNER on start:** follow `srj-session-start` and `srj-credit-budget`.
- **CODER on start:** read `AGENTS.md`, then this file, then the open `ready-for-code` Issues labelled `research`.

## 2. Track in one paragraph

The goal is a **new** intraday CFD edge for prop-firm challenges, separate from the Flow Nexus port.
- **Constraints:** the project's hard constraints apply in full (`srj-hard-constraints`, E-002).
- **Lens:** volume-first is mandatory (D-005, E-004). Every study leads with a bid-tick volume read: Volume Profile, VWAP, tick-rule CVD, or tick-count relative volume.
- **Style:** scalping is preferred. ≤1H is the chart-timeframe ceiling, not a cap on trade duration (E-003).
- **Evidence:** Dukascopy data the CODER downloads and prepares in `SRJ_DATA` on sirooj's machine (E-014). There is no cloud VM.
- **Scoring:** prop-firm challenge rules, not Sharpe (D-004).

## 3. Roles (D-023, E-014)

| Role | Who | Does |
|---|---|---|
| PLANNER | PromptQL bot | Designs studies (cards, addenda, kill criteria), writes relays, reviews CODER reports, records verdicts. Never runs a VM. |
| CODER | OpenCode on sirooj's machine | Downloads and prepares data, writes and runs study scripts, writes the results files and the CODER report. Merges `research/edge/**` PRs once checks pass (E-005, E-014). |
| OPERATOR | sirooj | "go" or redirect; carries relays and reports; domain answers; final say |

GitHub is connected in PromptQL projects "4 SRJ Venture" to "6 SRJ Venture" through sirooj's account. The planner uses it **read-only**. Writes go through the CODER.

## 4. Study log

| # | Study | Status | Result | Report |
|---|---|---|---|---|
| 01 | US index open scalping on NAS100/US500: ORB, ORB fade, Gao intraday momentum | done 2026-10-05 | **Null.** No edge larger than about 0.13R per trade; 0 FTMO passes (E-008) | `studies/01_us_open_scalping/REPORT.md` |
| 02 | NY open on unusual days, read through volume structure | **step 1 done** 2026-10-06 and backed up (PR #15, `c7ed9b8`): card locked (E-010), points verified (E-011), codification fixed (E-012); step 2 not started | **F1–F6 null** (0/336 survive). **F7 80% rule, open above prior value: survives** on NAS100 and US500 at both 11:30 and 16:00. Open below value: fails (E-013) | `studies/02_open_unusual_days/CARD.md`, `studies/02_open_unusual_days/STEP1_RESULTS.md` |

**Lost (VM era):**
- Session 1's scripts (`cost_map.py`, `orb.py`, `diag.py`) and its draft state and decision files lived only on that bot's VM. They were never pushed.
- Session 2's first drafts of `build_bars.py` and `step1.py` were lost the same way. Session 3 re-wrote them and pushed them in backup 02b.

E-006 was written to stop this. Since E-014, all compute runs on sirooj's machine, so there is no VM to lose.

## 5. Next actions

1. **CODER:** commit relay WORKFLOW 01, file Issues B1–B3 from it, and report.
2. **CODER (study 02 prep, no fitting; can start now):**
   - **B1:** rebuild the study-02 data in `SRJ_DATA` and reproduce step 1 locally. Results must match `c7ed9b8`.
   - **B2:** verify the NYSE holidays, half-days and FOMC dates hard-coded in `scripts/step1.py`.
   - **B3:** build the US high-impact news calendar for the ±5 min blackout.
3. **OPERATOR:** say "go step 2" or redirect. Proposed step-2 scope: **F7 from above value only** (E-013).
4. **PLANNER, after "go" and the B1–B3 reports:**
   - If B2 found a wrong date, first record the re-run's difference in an E-entry.
   - Before anyone touches step-2 data, write the step-2 addendum to CARD.md:
     - entry at acceptance,
     - visible SL,
     - targets (VAL / partial),
     - every configuration counted,
     - fit on IS only.
   - Relay it; the CODER runs it.
5. **Forward holdout:** OOS 2025-07-01 → 2026-09-30 has been used once, to select F7. Data from 2026-10-01 onward is the fresh forward holdout (E-013). No study run touches it until the planner says so.
6. **OPERATOR (optional, Flow Nexus track):** E-011's point evidence could let `config/instruments.yaml` mark both indices `point_verified: true`. That file is shared infrastructure, so it changes only through the Flow Nexus track (D-020), not through an edge PR.
7. **CODER (W4, relay WORKFLOW 02):** back-fill `research/edge/TRIALS.csv` from studies 01 and 02 (E-016). From now on, every study PR appends its own rows, and every CODER report states the study's cumulative trial count.
8. **PLANNER, each session:** once the Idea Funnel has run, read `research/funnel/queue.md` and promote, park or reject (`srj-idea-funnel`). A promoted candidate becomes a new study only through a locked `CARD.md`.

## 6. Study 02 design

Locked in `studies/02_open_unusual_days/CARD.md` (E-010). It supersedes the draft that was here in backup 01. Changes from the draft, all made before any data was seen:
- Decision times fixed at 09:45 and 10:05 ET; forward horizons +15/+30/+60 min, measured in ATR14 units.
- Exact feature buckets, codified Dalton opening-type thresholds, and the 80% rule's base-rate comparison.
- Grid fixed at 344 tests, with a 5-part kill criterion (including cross-index or adjacent-horizon robustness and a minimum mean of 0.05 ATR14).

Step-1 codification choices the card left open are in E-012 and the `scripts/step1.py` docstring. Results are in `STEP1_RESULTS.md`; the verdict is E-013.

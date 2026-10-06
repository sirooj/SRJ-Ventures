# SRJ Edge Research: STATE (session pointer)

> **Read this first in every edge-research session.** This track is separate from the Flow Nexus track (`docs/STATE.md`). Don't mix them.
> **Owner:** the RESEARCHER updates this file in every backup relay, and the CODER commits it verbatim.

_Last updated: 2026-10-06 (researcher session 3, PromptQL project "5 SRJ Venture", bot `96b32602-0da2-4e37-8a0d-9f411f3773c5`), backup 02b_

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

GitHub is connected in PromptQL projects "4 SRJ Venture" and "5 SRJ Venture" through sirooj's account. The researcher uses it **read-only**. Writes go through the CODER.

## 4. Study log

| # | Study | Status | Result | Report |
|---|---|---|---|---|
| 01 | US index open scalping on NAS100/US500: ORB, ORB fade, Gao intraday momentum | done 2026-10-05 | **Null.** No edge larger than about 0.13R per trade; 0 FTMO passes (E-008) | `studies/01_us_open_scalping/REPORT.md` |
| 02 | NY open on unusual days, read through volume structure | **step 1 done** 2026-10-06: card locked (E-010), points verified (E-011), codification fixed (E-012); step 2 not started | **F1–F6 null** (0/336 survive). **F7 80% rule, open above prior value: survives** on NAS100 and US500 at both 11:30 and 16:00. Open below value: fails (E-013) | `studies/02_open_unusual_days/CARD.md`, `studies/02_open_unusual_days/STEP1_RESULTS.md` |

**Lost:** session 1's scripts (`cost_map.py`, `orb.py`, `diag.py`) and its draft state and decision files lived only on that bot's VM. They were never pushed. Session 2's first drafts of `build_bars.py` and `step1.py` were lost the same way; session 3 re-wrote them, and they are pushed in backup 02b. E-006 exists to stop this from happening again.

## 5. Next actions

1. **CODER:** commit backup 02b and report the PR number and merge SHA.
2. **OPERATOR:** say "go step 2" or redirect. Proposed step-2 scope: **F7 from above value only** (E-013).
3. **RESEARCHER, before fitting anything in step 2:**
   - Verify the NYSE holidays, half-days and FOMC dates hard-coded in `scripts/step1.py` against an official source. If any date is wrong, re-run step 1 and record the difference in a new E-entry.
   - Build a US high-impact news calendar for the ±5 min blackout (the card's step-1 approximation is not enough for step 2).
   - Write a step-2 addendum to CARD.md before touching data: entry at acceptance, visible SL, targets (VAL / partial), every configuration counted. Fit on IS only.
   - OOS 2025-07-01 → 2026-09-30 has now been used once, to select F7. Reserve data from 2026-10-01 onwards as a fresh forward holdout (E-013).
4. **If the researcher's VM is lost:** re-create everything from the pushed scripts. Provision ≥15 GB disk. Run `pilot_download.py USATECHIDXUSD,USA500IDXUSD 2022-11-15 2026-09-30 4`, which takes about 2.5 h because Dukascopy throttles; then run one 1-worker fill per symbol. Then run `build_bars.py <SYM> 2022-11 2026-09` per symbol, then `step1.py --sample IS`, then `--sample OOS`.
5. **OPERATOR (optional, Flow Nexus track):** E-011's point evidence could let `config/instruments.yaml` mark both indices `point_verified: true`. That file is shared infrastructure, so it changes only through the planner/CODER track, not through an edge backup.

## 6. Study 02 design

Locked in `studies/02_open_unusual_days/CARD.md` (E-010). It supersedes the draft that was here in backup 01. Changes from the draft, all made before any data was seen:
- Decision times fixed at 09:45 and 10:05 ET; forward horizons +15/+30/+60 min, measured in ATR14 units.
- Exact feature buckets, codified Dalton opening-type thresholds, and the 80% rule's base-rate comparison.
- Grid fixed at 344 tests, with a 5-part kill criterion (including cross-index or adjacent-horizon robustness and a minimum mean of 0.05 ATR14).

Step-1 codification choices the card left open are in E-012 and the `scripts/step1.py` docstring. Results are in `STEP1_RESULTS.md`; the verdict is E-013.

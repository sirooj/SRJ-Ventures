# SRJ Edge Research: STATE (session pointer)

> **Read this first in every edge-research session.** This track is separate from the Flow Nexus track (`docs/STATE.md`). Don't mix them.
> **Owner:** the RESEARCHER updates this file in every backup relay, and the CODER commits it verbatim.

_Last updated: 2026-10-06 (researcher session 2, PromptQL project "4 SRJ Venture", bot `7b7cb100-a425-4362-aed4-732283e70666`)_

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
| 02 | Unusual-day filter for the NY open, volume-first (see §6) | designed, not started | — | — |

**Lost:** session 1's scripts (`cost_map.py`, `orb.py`, `diag.py`) and its draft state and decision files lived only on that bot's VM. They were never pushed. E-006 exists to stop this from happening again.

## 5. Next actions

1. **CODER:** commit backup 01 and report the PR number and merge SHA.
2. **OPERATOR:** confirm or veto E-005 (the CODER merges backup PRs itself). Then tell the researcher "go 02".
3. **RESEARCHER:** run study 02 per §6:
   - Card first.
   - Pilot one month of data.
   - Step 1: does the conditioning separate direction?
   - Push the card, scripts and step-1 results in backup 02 before going further.

## 6. Study 02 design (draft; locked in CARD.md before any results are seen)

- **Question:** the NY open moves a lot but has no unconditional direction (study 01). On *unusual* days, read through volume structure, does the open's direction become predictable?
- **Universe:** NAS100 (`USATECHIDXUSD`) and US500 (`USA500IDXUSD`).
  - Window: 09:30–11:30 ET.
  - No entries 09:55–10:05 ET, or within ±5 min of high-impact news.
- **Data:** Dukascopy bid ticks, 2023-01-01 → 2026-09-30.
  - In-sample (IS): 2023-01 → 2025-06.
  - Out-of-sample (OOS): 2025-07 → 2026-09.
  - Index point values must be verified tick-exact before conversion. Pilot one month first.
- **Causal day features, measured at 09:30 + N minutes:**
  - **Open vs the prior regular session's (09:30–16:00 ET) volume profile:** inside value, above VAH, or below VAL. Distance to the prior POC and to naked POCs.
  - **Gap** relative to the prior POC.
  - **Relative volume (RVOL):** tick count in the first N minutes ÷ the mean for the same window over the last 20 days.
  - **VWAP acceptance:** consecutive closes on one side of the session VWAP. Position relative to the σ bands.
  - **CVD divergence** at the opening-range extremes (used for divergence only, D-006).
  - **Context only:** opening-range width ÷ 14-day ATR.
- **Discretionary read, codified:** classify each open as open-drive, open-test-drive, open-rejection-reverse, open-auction, or unclassified (Dalton opening types). Also test the "80% rule": an open outside value that is accepted back inside tends to travel to the other side of value. Ambiguous cases go to `unclassified` and are never forced into a type.
- **Step 1:** forward returns at +15, +30 and +60 min by feature bucket and opening type, with counts and t-stats, IS vs OOS.
  - **Kill criterion:** no bucket shows |t| ≥ 2 in IS together with the same sign and |t| ≥ 1.5 in OOS, with at least 40 days per bucket.
- **Step 2 (only if step 1 survives):** scalp entries that obey the hard constraints, then costs (real spread, commission and stress slippage, and also zero slippage), then FTMO and The5ers challenge simulation from rolling start dates.

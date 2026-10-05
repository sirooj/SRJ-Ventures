---
name: srj-edge-study
description: How to design, run and report an SRJ edge-research study. Primarily for the RESEARCHER; the CODER can also use it to re-run a study. Use when proposing a new edge, running a backtest study, or writing up a result.
---

# SRJ edge study

## 1. Card first, before any code
Write `research/edge/studies/<NN>_<slug>/CARD.md`, following `.github/ISSUE_TEMPLATE/strategy.md`, plus:
- **Volume read (required, E-004):** which bid-tick volume structure drives the idea. Options: prior or composite VP (POC, VAH/VAL, HVN/LVN, naked POC), session or anchored VWAP with σ bands, tick-rule CVD divergence, tick-count relative volume. Non-volume filters are context only, each with one line on why.
- **Who is on the other side**, why the edge might persist, and why it might have decayed.
- **Constraint check:** run `srj-hard-constraints` and list anything borderline.
- **Locked before results:** the in-sample/out-of-sample dates, the configuration grid, and the kill criteria.

Read the study log and decisions first, so you don't retest a dead idea (for example E-008).

## 2. Data
- **Reuse repo code:** `core/data/dukascopy.py` (download and convert), `core/data/bars.py`, `core/indicators/*`. If something is missing, add it to `core/` with a test and push it in the backup. No throwaway loaders.
- **Pilot first** (AGENTS §4): one month. Measure disk use and time, then scale up.
- The RESEARCHER downloads into its own VM (E-009). Run long downloads in the background and log progress to a file.

## 3. Method
1. **Step 1: does the conditioning separate direction?** Compute forward returns by feature bucket, with counts and t-stats, in-sample vs out-of-sample. If the kill criteria fire, stop and report.
2. **Step 2: rules.** Entries, SL and TP that obey the hard constraints. Then costs: real spread, commission and stress slippage, plus a zero-slippage run. Output a trade list.
3. **Step 3: challenge simulation.** Run the trade list against each firm's YAML from rolling start dates. Report P(pass), days to pass, and P(breach) by rule. Use `core/propfirm` once the simulator is merged. Until then, state the approximation you used.

Throughout:
- Choose parameters on in-sample data only. Keep grids small, and report how many configurations were tried.
- Discretionary reads (opening types, acceptance vs rejection) must be codified as causal rules. Unclear days go to `unclassified`, never forced into a type.

## 4. Report
Write `research/edge/studies/<NN>_<slug>/REPORT.md`:
- the question, data and method
- tables comparing in-sample and out-of-sample
- a verdict (edge, null, or inconclusive), with the effect size the data rules out
- caveats and the next step

Never tune until something passes.

Then:
- update EDGE_STATE §4 and §5,
- append an E-entry with the verdict,
- run `srj-research-backup`.

## 5. Session budget
- One good pass with visible progress beats many slow passes.
- Before any job longer than 5 min, write into EDGE_STATE or a relay what is running and where its outputs land.
- If the session might end, back up partial work now. Partial and pushed beats complete and lost.

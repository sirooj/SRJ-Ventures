---
name: srj-edge-study
description: How to design, run and report an SRJ edge-research study. The PLANNER designs and rules; the CODER runs everything on sirooj's machine. Use when proposing a new edge, running a study or backtest, or writing up a result.
---

# SRJ edge study (E-014)

## 0. Who does what
| Step | PLANNER | CODER |
|---|---|---|
| Card + kill criteria | writes and locks it | commits it verbatim |
| Data | specifies symbols, dates, IS/OOS | downloads and prepares it (`srj-local-data`) |
| Scripts | specifies method and codification | writes, tests and runs them |
| Results | reviews the CODER report | writes `STEP<n>_RESULTS.md` / `REPORT.md` with numbers and a proposed verdict |
| Verdict | records the E-entry, updates EDGE_STATE | — |

## 1. Card first, before any code (PLANNER)
Write `research/edge/studies/<NN>_<slug>/CARD.md`, following `.github/ISSUE_TEMPLATE/strategy.md`, plus:
- **Volume read (required, E-004):** which bid-tick volume structure drives the idea. Options:
  - prior or composite VP (POC, VAH/VAL, HVN/LVN, naked POC),
  - session or anchored VWAP with σ bands,
  - tick-rule CVD divergence,
  - tick-count relative volume.

  Non-volume filters are context only, each with one line on why.
- **Who is on the other side**, why the edge might persist, and why it might have decayed.
- **Constraint check:** run `srj-hard-constraints` and list anything borderline.
- **Locked before results:**
  - the in-sample/out-of-sample dates,
  - the configuration grid and the kill criteria,
  - every codification choice the CODER will need, so the CODER never picks one after seeing data. Anything left open, the CODER asks about with `question`.

Read the study log and decisions first, so you don't retest a dead idea (for example E-008).

## 2. Data (CODER, local)
- Follow `srj-local-data`: check `SRJ_DATA` first, download only the gaps, pilot first.
- **Reuse repo code:** `core/data/dukascopy.py`, `core/data/bars.py`, `core/indicators/*`. If something is missing, add it to `core/` with a test; that PR follows D-020. No throwaway loaders.
- Never feed the forward holdout (currently 2026-10-01 onward, E-013) into a study run.

## 3. Method (CODER runs, PLANNER rules)
1. **Step 1: does the conditioning separate direction?** Compute forward returns by feature bucket, with counts and t-stats, in-sample vs out-of-sample. If the kill criteria fire, stop and report.
2. **Step 2: rules.**
   - Entries, SL and TP that obey the hard constraints.
   - Then costs: real spread, commission and stress slippage, plus a zero-slippage run.
   - Output a trade list.
3. **Step 3: challenge simulation.**
   - Run the trade list against each firm's YAML from rolling start dates.
   - Report P(pass), days to pass, and P(breach) by rule.
   - Use `core/propfirm` once the simulator is merged. Until then, state the approximation used.

Throughout:
- **Pre-registration:** commit the IS script and IS results before running OOS. The OOS run uses that committed script unchanged. Disclose any later change in the report, with its diff.
- Choose parameters on in-sample data only. Keep grids small, and report how many configurations were tried.
- Discretionary reads (opening types, acceptance vs rejection) must be codified as causal rules. Unclear days go to `unclassified`, never forced into a type.

## 4. Report
The CODER writes `research/edge/studies/<NN>_<slug>/REPORT.md` (or `STEP<n>_RESULTS.md`), with:
- the question, data and method,
- tables comparing in-sample and out-of-sample,
- a proposed verdict (edge, null, or inconclusive), with the effect size the data rules out,
- caveats and the next step.

The CODER also puts the key numbers in the PR's CODER report (`srj-relay`). Never tune until something passes.

The PLANNER then:
- reviews the report,
- appends the verdict E-entry,
- updates EDGE_STATE §4 and §5,
- delivers all of it in the next relay.

## 5. Budget
- **CODER:**
  - One good pass with visible progress beats many slow passes.
  - Before any job longer than 5 min, note in the Issue what is running and where its outputs land.
  - Push partial work early. Partial and pushed beats complete and lost.
- **PLANNER:** review from the report. Open raw result files only for a specific missing number (`srj-credit-budget`).

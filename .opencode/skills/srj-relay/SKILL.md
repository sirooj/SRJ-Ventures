---
name: srj-relay
description: How the PLANNER writes a relay and how the CODER executes it and reports back, on either track. Replaces srj-research-backup. Use whenever work crosses between PromptQL and sirooj's machine.
---

# SRJ relay (D-015, D-020, D-023, D-024, E-005, E-014)

## PLANNER: writing a relay
Before any build relay, list the 1–3 consequential choices for the OPERATOR and get answers first.

Title: `RELAY: <FLOW|EDGE|WORKFLOW> <NN>, <slug>`. Contents, in order:
1. **Branch** name.
2. **Files** the planner authored, for example pointers, decision logs, skills and cards:
   - `## File n: <path>`: the file in full, in a fenced block. Use four-backtick fences when the file contains triple backticks.
   - `## Append to: <path>`: the exact lines to add at the end, for append-only files (decision logs, CSV ledgers). Never edit old entries.
   - `## Edit: <path>`: exact `Replace:` / `With:` blocks or an exact insertion point, for a file the planner doesn't hold in full.
   - `## Delete: <path>`.
3. **Tasks**, each a ready-to-file Issue with:
   - title and labels,
   - goal and inputs,
   - **`OSS check:`** for any task that builds a component: the `docs/TOOLING.md` rows considered and the verdict (D-024),
   - spec and steps, with tolerances or kill criteria fixed before any run,
   - acceptance checks,
   - what to report.
   The spec says *what* to do and *how to judge it*. The CODER picks implementation details within the hard constraints.
4. **Checks**, the **commit message**, and the **merge basis**: a D-020 approval line, or E-005 / E-014 / D-024.

Always include:
- the updated track pointer (status, next actions, last-updated line),
- any new D-/E-entries.

Store the relay as an artifact and tell sirooj to paste it whole.

## CODER: executing a relay
1. `git fetch && git switch main && git pull && git switch -c <branch>`.
2. Write the planner's files **verbatim**, and apply its appends and edits exactly.
   - If one fails a check, make the minimal fix and list the exact diff in the PR body.
   - A D-020 approval covers verbatim content only. If you changed anything, wait for re-approval.
3. File the tasks as Issues verbatim (D-015).
4. Do the tasks. Data and compute run locally (`srj-local-data`, `srj-edge-study`).
5. Checks:
   - `git status` shows only the expected paths.
   - No data and no secrets.
   - `uv run pytest` and `uv run ruff check .` pass.
6. Open the PR, merge it on its stated basis, and reply with the CODER report.

## Escalation (D-024)
- **Failed twice:** if the same task fails twice, stop. Comment both attempts on the Issue (what you did, the error, what you tried), add `question`, and move to the next unblocked Issue.
- **Too good:** if a result shows a win rate above 75%, a profit factor above 3, or a max drawdown under 1R over at least 30 trades, run the leak checklist before reporting:
  - timestamps are causal and no future bars enter features;
  - session boundaries and DST are right;
  - fills happen at the next tick, not on the signal bar;
  - the spread is applied;
  - IS and OOS don't overlap, and the forward holdout is untouched.

  Say in the report that it ran and what it found.
- **Execution-critical:** code that touches order placement, position sizing, SL/TP placement or moves, risk limits, or prop-firm rule enforcement gets the label `execution-critical`. Keep each such diff at 300 lines or less; split it if larger. The planner reviews the diff line by line, not just the report.

## CODER report (Evidence order)
This becomes the next session's "Latest CODER message". By default it is the only thing the planner reads, so keep it under ~40 lines, in this order:
1. **Where:** PR number, merge SHA (or "awaiting approval"), Issue numbers.
2. **Checks:** pytest count, ruff, git-status scope.
3. **Results:** the key numbers in one small table (IS vs OOS, counts, t/z, P(pass), …). Numbers come from our code, never estimated.
4. **Counter-evidence:** what failed, weak splits, configurations that didn't hold, data gaps that could flatter the result.
5. **Trials:** the configurations evaluated in this report, and the study's cumulative count from `research/edge/TRIALS.csv`.
6. **Leak check:** "not triggered", or what it found.
7. **Data:** symbols, date range, disk used, gaps or missing hours.
8. **Flags:** deviations, incidents, open questions, and the rework count (how many times this task came back).
9. **Proposed verdict:** your opinion, labelled, last.
10. **Pointer:** the path of the full results file in the repo.

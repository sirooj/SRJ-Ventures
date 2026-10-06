---
name: srj-relay
description: How the PLANNER writes a relay and how the CODER executes it and reports back, on either track. Replaces srj-research-backup. Use whenever work crosses between PromptQL and sirooj's machine.
---

# SRJ relay (D-015, D-020, D-023, E-005, E-014)

## PLANNER: writing a relay
Title: `RELAY: <FLOW|EDGE|WORKFLOW> <NN>, <slug>`. Contents, in order:
1. **Branch** name.
2. **Files** the planner authored, for example pointers, decision logs, skills and cards.
   - Each file in full, as `## File n: <path>` followed by a fenced block. Use four-backtick fences when the file contains triple backticks.
   - Deletions as `## Delete: <path>`.
   - Decision logs are append-only: never edit old entries.
3. **Tasks**, each a ready-to-file Issue with:
   - title and labels,
   - goal and inputs,
   - spec and steps,
   - acceptance checks,
   - what to report.
   The spec says *what* to do and *how to judge it*. The CODER picks implementation details within the hard constraints.
4. **Checks**, the **commit message**, and the **merge basis**: a D-020 approval line, or E-005 / E-014.

Always include:
- the updated track pointer (status, next actions, last-updated line),
- any new D-/E-entries.

Store the relay as an artifact and tell sirooj to paste it whole.

## CODER: executing a relay
1. `git fetch && git switch main && git pull && git switch -c <branch>`.
2. Write the planner's files **verbatim**.
   - If one fails a check, make the minimal fix and list the exact diff in the PR body.
   - A D-020 approval covers verbatim content only. If you changed anything, wait for re-approval.
3. File the tasks as Issues verbatim (D-015).
4. Do the tasks. Data and compute run locally (`srj-local-data`, `srj-edge-study`).
5. Checks:
   - `git status` shows only the expected paths.
   - No data and no secrets.
   - `uv run pytest` and `uv run ruff check .` pass.
6. Open the PR, merge it on its stated basis, and reply with the CODER report.

## CODER report
This becomes the next session's "Latest CODER message". By default it is the only thing the planner reads, so keep it under ~40 lines:
- **Where:** PR number, merge SHA (or "awaiting approval"), Issue numbers.
- **Checks:** pytest count, ruff, git-status scope.
- **Results:**
  - the key numbers in one small table (IS vs OOS, counts, t/z, P(pass), …),
  - your proposed verdict.
- **Data:** symbols, date range, disk used, gaps or missing hours.
- **Flags:** deviations, incidents, open questions.
- **Pointer:** the path of the full results file in the repo.

---
name: srj-research-backup
description: Back up edge research to GitHub through the CODER. The RESEARCHER uses it to write a backup relay after every study and at session end; the CODER uses it to execute one.
---

# SRJ research backup relay (E-005, E-006)

## RESEARCHER: writing the relay
Write one relay titled `RELAY: BACKUP <NN>, <slug>` containing:
1. **Branch:** `edge-backup-<NN>-<slug>`.
2. **Files:** every file in full, as `## File n: <path>` followed by a fenced block. Use four-backtick fences when the file contains triple backticks. Give whole files, not diffs.
3. **Always included:**
   - the updated `research/edge/EDGE_STATE.md` (§4 study log, §5 next actions, the last-updated line),
   - the full `research/edge/DECISIONS_EDGE.md` with the new E-entries appended (append-only; never edit old entries).
4. **Scripts** from the VM that produced the results, not only summaries. Run them through ruff in the VM first. No data, and no file over 1 MB.
5. **Checks and commit message**, so the CODER can run and copy them.

Store the relay as an artifact and tell sirooj to paste it whole. Also store a hidden VM backup copy of the files, for example `edge_backup_<NN>.tar.gz`.

## CODER: executing the relay
1. Create the branch: `git fetch && git switch main && git pull && git switch -c <branch>`.
2. Write each file **verbatim**. Don't reformat or "fix" anything. If something looks wrong, commit it as-is and flag it in the PR body.
3. Run the checks:
   - `git status` shows only the paths in the relay.
   - No data and no secrets.
   - `uv run pytest` and `uv run ruff check .` pass.
4. Commit with the given message and push. Open a PR titled `[RESEARCH] Edge backup <NN>: <slug>`, labelled `research`, with the file list and any flags in the body.
5. **Merge (E-005):** if the PR touches only `research/edge/**` and `.opencode/skills/**`, merge it once the checks pass; sirooj's paste is the operator approval. Any other path follows D-020.
6. **Reply** with: PR number, merge SHA, check results, and any flags. That reply is the "Latest CODER message" in the next resume line.

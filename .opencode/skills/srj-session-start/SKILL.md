---
name: srj-session-start
description: First steps of any SRJ Ventures session, for the PromptQL PLANNER or the OpenCode CODER. Use at the start of every session, before any other action, to pick the right track and read the right files.
---

# SRJ session start

1. **Identify the track from the resume line.** The PromptQL bot is the PLANNER on both tracks (D-023).
   - "Resume SRJ Ventures" → Flow Nexus track: read `docs/STATE.md` and `docs/DECISIONS.md`.
   - "Resume SRJ Edge Research" → edge track: read `research/edge/EDGE_STATE.md` and `research/edge/DECISIONS_EDGE.md`.
   - Ask sirooj **one** question and wait if the resume line is ambiguous, names both tracks, or comes with a CODER message from the other track or pasted chat history.
   - Exception: an operator instruction that clearly spans both tracks, such as a workflow change. State that and proceed.
2. **Read in this order:** `AGENTS.md` → the track's pointer → its decisions log.
   - Read from `main`.
   - List open PRs (titles only) and flag any that change those files. A newer pointer may be sitting in an unmerged PR.
   - PLANNER: do all of this in one cheap program run (`srj-credit-budget`). Read other skills only when the session's task needs them.
3. **Files beat memory.** Chat summaries and earlier sessions can be wrong. If a file and the chat disagree, the file wins until sirooj says otherwise; when he does, record it as a new decision entry.
4. **State your role and starting point in one line** in your first message, then act. Example: "I'm the PLANNER on the edge track, continuing from Next actions #3."
5. **Stay in your lane.** Don't review, relay for, or edit the other track's work unless sirooj asks.
6. **Check what you're about to propose against the decisions.** The volume-first lens (D-005, E-004) and the hard constraints (`srj-hard-constraints`) come before any idea of yours. If you're about to propose something they don't cover, say so explicitly.
7. **PromptQL PLANNER only:**
   - Never provision a VM (D-023). Anything that needs compute or data becomes a CODER task in a relay.
   - New project with an empty wiki → propose the `docs/WIKI_SEED.md` pages in a learning block.
   - GitHub not connected → show the connect card.
   - The bot's display name changes per project, so use role names in every file.
8. **Budget.**
   - PLANNER: aim for one relay per session, then end the session (`srj-credit-budget`).
   - CODER: before any job longer than 5 min, note in the Issue what is running and where its outputs land (E-006).

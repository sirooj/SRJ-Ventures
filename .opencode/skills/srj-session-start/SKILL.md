---
name: srj-session-start
description: First steps of any SRJ Ventures session, for the PromptQL bot or OpenCode. Use at the start of every session, before any other action, to pick the right track and read the right files.
---

# SRJ session start

1. **Identify the track from the resume line.**
   - "Resume SRJ Ventures" → Flow Nexus track: read `docs/STATE.md`; the PromptQL bot's role is PLANNER.
   - "Resume SRJ Edge Research" → edge track: read `research/edge/EDGE_STATE.md`; the PromptQL bot's role is RESEARCHER.
   - Ambiguous, both tracks, or pasted chat history → ask sirooj **one** question and wait. Do not act first.
2. **Read in this order:** `AGENTS.md` → the track's pointer → the track's decisions log → the skills this session will use. Read from `main`. Also list open PRs that change those files. A newer pointer may be sitting in an unmerged PR; if so, say so rather than assume either version.
3. **Files beat memory.** Chat summaries and earlier sessions can be wrong. If a file and the chat disagree, the file wins until sirooj says otherwise; when he does, record it as a new decision entry.
4. **State your role and starting point in one line** in your first message, then act. Example: "I'm the RESEARCHER on the edge track, continuing from Next actions #3."
5. **Stay in your lane.** Don't review, relay for, or edit the other track's work unless sirooj asks.
6. **Check what you're about to propose against the decisions.** The volume-first lens (D-005, E-004) and the hard constraints (`srj-hard-constraints`) come before any idea of yours. If you're about to propose something they don't cover, say so explicitly.
7. **PromptQL bot only:**
   - New project with an empty wiki → propose the `docs/WIKI_SEED.md` pages in a learning block.
   - GitHub not connected → show the connect card.
   - The bot's display name changes per project, so use role names in every file.
8. **Budget.** Assume the session can end at any moment. Before any job longer than 5 min, write the plan into the pointer or a relay first (E-006).

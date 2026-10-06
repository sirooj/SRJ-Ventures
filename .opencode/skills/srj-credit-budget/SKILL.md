---
name: srj-credit-budget
description: PromptQL credit rules for the PLANNER. Use at the start of every planner session, and before any action that runs code, reads many files, or would need compute.
---

# SRJ credit budget (D-023)

sirooj's PromptQL credit is spent three ways:
- by cloud VMs, which drain it fastest,
- by programs the planner runs,
- by the planner's model turns.

The planner directs; sirooj's machine does the work.

## Never
- **Never provision a VM.** A task becomes a CODER task in a relay if it needs any of these:
  - a shell,
  - data or a download,
  - a study or backtest,
  - more than a few seconds of compute.
- Never download Dukascopy (or any market) data into PromptQL.
- Never run studies, grids, simulations or backtests in the program runtime.
- Don't read raw result files (CSV grids, trade lists, logs). If the CODER report is missing a number, ask for that number in the next relay.

## Allowed (cheap)
- The program runtime, for two things only:
  - small GitHub reads through `__github`: pointers, decisions logs, skills, PR bodies, and small diffs,
  - assembling relays from those files.
- Reading and proposing to the PromptQL wiki.

## Session shape
1. **Start:** in one program run, read `AGENTS.md`, the track pointer, its decisions log, and the open PR/issue titles.
2. **Work:** batch everything into **one relay** where possible: tasks, file updates, reviews, and the pointer update.
3. **Review:** work from the CODER report in the PR body (`srj-relay`). Open a diff only when the report flags something.
4. **End:** once the relay is delivered, close the interaction. Don't hold a session open, poll, or schedule check-ins.
5. **Big tasks:** if a planner task looks expensive (a huge diff, many files), say so and offer the cheap version first.

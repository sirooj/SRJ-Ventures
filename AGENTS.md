# AGENTS.md — SRJ Ventures relay protocol + working conventions

**Session start: read `docs/STATE.md`, then `docs/DECISIONS.md`.**

This repo is the **only channel** between the cloud orchestrator
(the PromptQL planner bot — its display name can change per PromptQL project)
and the local CODER agent running on sirooj's
Windows machine. The orchestrator cannot see this machine. Everything flows
through **GitHub Issues, PRs, and committed files**.

## 0. Roles (D-019, D-020)
- **PLANNER** (PromptQL bot): research, specs, reviews, decisions. Owns `docs/STATE.md` and D-entries.
- **CODER** (OpenCode, this terminal): implement → test → execute → report. Never guess; ask with the `question` label. Merge only when a `Planner review (relayed): APPROVED` comment exists for the current head SHA.
- **OPERATOR** (sirooj): domain answers, access, fee tables, VPN/machine, final say.
- Before building a new component, check `docs/DECISIONS.md` D-022 for OSS to reuse.

## 1. Relay protocol

- Issues labelled **`ready-for-code`** are tasks from the orchestrator. Only work
  on those (or explicit `research`/`data` requests).
- To pick one up:
  1. Comment `picked up` on the Issue.
  2. Swap the label `ready-for-code` → `in-progress`.
  3. Create a branch `issue-<n>-<slug>` and do the work there.
- **Definition of done** (all required before review):
  - code and tests pass: `uv run pytest` (and `uv run ruff check .`)
  - outputs are written to `results/<id>/` (small files only, < 1 MB each)
  - a PR is opened with `Closes #<n>`, a summary of metrics, assumptions, and
    open questions, with label **`needs-review`**
- If the trading logic is ambiguous, **don't guess**. Comment on the Issue and
  add the label **`question`**.
- Labels in use: `ready-for-code`, `in-progress`, `needs-review`, `question`,
  `research`, `data`.

## 2. Machine conventions (Windows, D: drive — C: is nearly full)

- Repo lives at `D:\SRJ Venture\SRJ-Ventures` (quote the path — it has a space).
- Everything lives on D:, including data, venvs, caches, Python installs:
  - `SRJ_ROOT = D:\SRJ Venture`
  - `SRJ_DATA = D:\SRJ Venture\data`
  - `UV_CACHE_DIR = D:\SRJ Venture\.cache\uv`
  - `UV_PYTHON_INSTALL_DIR = D:\SRJ Venture\.python`
  - `PIP_CACHE_DIR = D:\SRJ Venture\.cache\pip`
- Code reads data paths from the `SRJ_DATA` env var (see `core/data/paths.py`).
  **Never hardcode paths.**

## 3. Data conventions

- **Bid-side by default** for price and volume analysis on CFDs (sirooj's
  convention). Keep the ask side only for spread and cost modelling.
- All timestamps in **UTC** internally. Sessions are defined with `zoneinfo`
  (`America/New_York`, `Europe/London`) so DST is handled correctly.
- **No lookahead.** Indicators may use only data available at the bar close.
  Every indicator ships with a unit test that enforces this (recompute on a
  truncated series must equal the prefix of the full-series result).
- **Never commit data**: ticks, parquet, bars, `.bi5` (see `.gitignore`).
  Commit only code, specs, and small results (JSON/MD/CSV summaries < 1 MB).
  **Never commit secrets.**

## 4. Pilot-first rule

New symbols / longer history: download a small pilot first, report disk usage
per symbol-year, then scale. Don't re-download what already exists — check
`SRJ_DATA` and sirooj's existing archives first.

## 5. Tracks, session start, skills (E-001, E-007)

This repo runs **two independent tracks**. A session works on exactly one of them.

| Track | Pointer (read first) | Decisions | PromptQL bot's role |
|---|---|---|---|
| Flow Nexus port + infrastructure (Phase 0–1) | `docs/STATE.md` | `docs/DECISIONS.md` (D-xxx) | PLANNER |
| Edge research (new edges, separate from Flow Nexus) | `research/edge/EDGE_STATE.md` | `research/edge/DECISIONS_EDGE.md` (E-xxx) | RESEARCHER |

- **RESEARCHER** (PromptQL bot, edge track): designs and runs studies in its own cloud VM, on Dukascopy data it downloads itself. It never needs the D: drive. Its GitHub writes go through the CODER as backup relays.
- The resume line names the track. If it doesn't, ask the operator one question before doing anything.
- Never act on the other track (reviews, relays, STATE edits) unless the operator asks.
- PromptQL bot display names change per project ("3 SRJ Venture Bot", "4 SRJ Venture Bot", …). Refer to roles, not names.

Skills live in `.opencode/skills/<name>/SKILL.md`. Any agent can also read them directly as files.

| Skill | Use when |
|---|---|
| `srj-session-start` | First thing in any session, in either role |
| `srj-hard-constraints` | Before proposing, coding, testing or approving any strategy, and before any commit |
| `srj-edge-study` | Designing, running or reporting an edge study |
| `srj-research-backup` | After every study and at session end, when writing or executing a backup relay |

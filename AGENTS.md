# AGENTS.md — SRJ Ventures relay protocol + working conventions

**Session start: follow the skill `srj-session-start`.** It tells you which track pointer (`docs/STATE.md` or `research/edge/EDGE_STATE.md`) and decisions log to read.

This repo is the **only channel** between the cloud PLANNER (the PromptQL bot — its display name changes per PromptQL project)
and the local CODER agent running on sirooj's Windows machine. The planner cannot see this machine. Everything flows
through **GitHub Issues, PRs, and committed files**.

## 0. Roles (D-019, D-023)

The PLANNER directs, the CODER builds and computes, and the OPERATOR approves. **All data and all compute live on sirooj's machine.** The planner never runs a cloud VM, so that PromptQL credit lasts (D-023).

- **PLANNER** (PromptQL bot): director of both tracks.
  - Plans and writes specs, study cards and relays; reviews PR reports; decides.
  - Owns the track pointers (`docs/STATE.md`, `research/edge/EDGE_STATE.md`) and the D-/E-entries.
  - Does not download data, run studies or backtests, or provision a VM. Follows `srj-credit-budget`.
  - Reviews the Idea Funnel queue (`research/funnel/queue.md`) once per session and promotes, parks or rejects candidates (`srj-idea-funnel`).
- **CODER** (OpenCode, this terminal): builder and executor.
  - Implements, downloads and prepares data in `SRJ_DATA`, runs tests, studies and backtests, and reports.
  - Runs the Idea Funnel and web research locally (`srj-idea-funnel`, `srj-research-web`).
  - Never guesses; asks with the `question` label.
  - Reports evidence first and proposes a verdict last; the planner records the decision.
- **OPERATOR** (sirooj): "go" or redirect, domain answers, access, fee tables, VPN/machine, and the final say.
  - Carries planner relays to the CODER and the CODER's newest report back, until the PromptQL GitHub App can write to the repo (D-015).
- **Reuse before build (D-022, D-024):** before building a new component, check `docs/TOOLING.md`. Every relay task that builds something carries an `OSS check:` line. A tool is adopted only after it reproduces a known in-house result.

## 1. Relay protocol (both tracks; skill `srj-relay`)

1. The PLANNER writes a relay titled `RELAY: <FLOW|EDGE|WORKFLOW> <NN>, <slug>`. sirooj pastes it to the CODER whole.
2. The CODER commits the relay's files verbatim and files its tasks as Issues verbatim (D-015). Labels: `ready-for-code`, plus `research`/`data` where the relay gives them. Only work on those, or on explicit operator requests.
3. To pick an Issue up:
   1. Comment `picked up` on the Issue.
   2. Swap the label `ready-for-code` → `in-progress`.
   3. Create a branch `issue-<n>-<slug>` and do the work there.
4. **Definition of done** (all required before review):
   - Code and tests pass: `uv run pytest` and `uv run ruff check .`.
   - Outputs are written to `results/<id>/` or the study's `results/` folder (small files only, < 1 MB each).
   - A PR is opened with:
     - `Closes #<n>`,
     - the label **`needs-review`** (edge track: **`research`**),
     - a **CODER report** in the PR body, in Evidence order (`srj-relay`). The report is what the planner reviews.
5. If the trading logic is ambiguous, **don't guess**. Comment on the Issue and add the label **`question`**. If the same task fails twice, escalate the same way (`srj-relay`).
6. **Merges:**
   - **Default (D-020):** merge only when a `Planner review (relayed): APPROVED` comment exists for the PR's current head SHA.
   - **Planner relay committed verbatim**, touching only `research/edge/**` and `.opencode/skills/**`: the CODER merges once checks pass. sirooj's paste is the approval (E-005).
   - **CODER-produced edge work**, touching only `research/edge/**`: the CODER merges once checks pass. The planner reviews the report at its next session and corrects anything through a new E-entry (E-014).
   - **Idea Funnel runs**, touching only `research/funnel/**`: the CODER merges once the validator and checks pass (D-024).
   - **`execution-critical`** PRs (order placement, sizing, SL/TP, risk limits, prop-firm rule enforcement): D-020, plus a line-by-line planner review of the diff.
7. Labels in use: `ready-for-code`, `in-progress`, `needs-review`, `question`,
  `research`, `data`, `execution-critical`.

## 2. Machine conventions (Windows, D: drive — C: is nearly full)

- Repo lives at `D:\SRJ Venture\SRJ-Ventures` (quote the path — it has a space).
- Everything lives on D:, including data, venvs, caches, Python installs, and browser binaries for web research:
  - `SRJ_ROOT = D:\SRJ Venture`
  - `SRJ_DATA = D:\SRJ Venture\data`
  - `UV_CACHE_DIR = D:\SRJ Venture\.cache\uv`
  - `UV_PYTHON_INSTALL_DIR = D:\SRJ Venture\.python`
  - `PIP_CACHE_DIR = D:\SRJ Venture\.cache\pip`
- Code reads data paths from the `SRJ_DATA` env var (see `core/data/paths.py`).
  **Never hardcode paths.**
- Secrets live in `D:\SRJ Venture\.secrets\`, outside the repo. Private, uncommitted material (MQL5 inventory, saved web sources) lives in `D:\SRJ Venture\private\`.

## 3. Data conventions

- Both tracks share one dataset under `SRJ_DATA`. The CODER downloads and prepares it (skill `srj-local-data`).
- **Bid-side by default** for price and volume analysis on CFDs (sirooj's
  convention). Keep the ask side only for spread and cost modelling.
- All timestamps in **UTC** internally. Sessions are defined with `zoneinfo`
  (`America/New_York`, `Europe/London`) so DST is handled correctly.
- **No lookahead.** Indicators may use only data available at the bar close.
  Every indicator ships with a unit test that enforces this (recompute on a
  truncated series must equal the prefix of the full-series result).
- **Never commit data**: ticks, parquet, bars, `.bi5` (see `.gitignore`).
  Commit only code, specs, and small results (JSON/MD/CSV summaries < 1 MB).
  **Never commit secrets** or copyrighted source text.

## 4. Pilot-first rule

New symbols / longer history: download a small pilot first, report disk usage
per symbol-year, then scale. Don't re-download what already exists — check
`SRJ_DATA` and sirooj's existing archives first.

## 5. Tracks, session start, skills (E-001, E-007, D-023, D-024)

This repo runs **two independent tracks**. A session works on exactly one of them. The PromptQL bot is the PLANNER on both.

| Track | Resume line | Pointer (read first) | Decisions |
|---|---|---|---|
| Flow Nexus port + infrastructure (Phase 0–1) | "Resume SRJ Ventures" | `docs/STATE.md` | `docs/DECISIONS.md` (D-xxx) |
| Edge research (new edges, separate from Flow Nexus) | "Resume SRJ Edge Research" | `research/edge/EDGE_STATE.md` | `research/edge/DECISIONS_EDGE.md` (E-xxx) |

- The resume line names the track. Ask the operator one question before doing anything if:
  - the resume line doesn't name a track, or
  - the CODER message belongs to the other track.
- Exception: an operator instruction that clearly spans both tracks, such as a workflow change. Say so and proceed.
- Never act on the other track (reviews, relays, pointer edits) unless the operator asks.
- PromptQL bot display names change per project ("5 SRJ Venture Bot", "6 SRJ Venture Bot", …). Refer to roles, not names.
- The Idea Funnel (`research/funnel/`) is not a track. Its candidates enter the edge track only when the planner promotes one to a locked card (E-016).

Skills live in `.opencode/skills/<name>/SKILL.md`. Any agent can also read them directly as files.

| Skill | Who | Use when |
|---|---|---|
| `srj-session-start` | both | First thing in any session |
| `srj-credit-budget` | PLANNER | Every planner session. Also before running code, reading many files, or anything that needs compute |
| `srj-hard-constraints` | both | Before proposing, coding, testing or approving any strategy, and before any commit |
| `srj-relay` | both | Writing, executing or reporting on a relay (replaces `srj-research-backup`) |
| `srj-local-data` | CODER | Before any download, conversion or bar build |
| `srj-edge-study` | both | Designing (PLANNER) or running (CODER) an edge study |
| `srj-research-web` | CODER | Any web research: finding, fetching and saving sources |
| `srj-idea-funnel` | CODER runs, PLANNER reviews | "run funnel", a scheduled funnel run, or the planner's queue review |

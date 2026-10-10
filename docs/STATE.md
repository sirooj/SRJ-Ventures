# SRJ Ventures: STATE (session pointer)

> **Read this first in every new session**, whether you are the PromptQL planner or the OpenCode coder. It is the single source of truth for "where are we". History lives in git, decisions live in `docs/DECISIONS.md`, and the long-term domain context lives in `docs/WIKI_SEED.md` and the PromptQL wiki.
> **Owner of this file:** the PLANNER updates it at the end of every session and delivers it in a relay. The CODER may fix numbers or facts and must note that in the PR.

_Last updated: 2026-10-10 (planner session, PromptQL project "7", bot e4d720de-937a-43f3-954e-ee6933bf5f17): D-025 (relay WORKFLOW 03), W1–W4 filed as #20–#23_

---

## 1. How to resume (no copy-paste)

**sirooj, starting a new PromptQL session:** paste only this:
```
@<bot name> Resume SRJ Ventures. Read https://github.com/sirooj/SRJ-Ventures/blob/main/docs/STATE.md (+ DECISIONS.md, WIKI_SEED.md), then continue from "Next actions". Latest CODER message: <paste only the newest CODER message, if any>
```

**PLANNER (a new PromptQL bot) on start:** follow `srj-session-start` and `srj-credit-budget`. In short:
1. Read the `SRJ Ventures` wiki page. If it doesn't exist (new project), seed it from `docs/WIKI_SEED.md` with a learning block.
2. In one program run, fetch from GitHub (`__github` integration):
   - `docs/STATE.md` and `docs/DECISIONS.md`,
   - the titles of open issues and open PRs,
   - `research/funnel/queue.md`, once the funnel has run.
   Never provision a VM (D-023).
3. Continue from §5 "Next actions". Never re-decide anything listed in DECISIONS.md without a new D-entry.
4. At session end:
   - update this file (status, issue table, next actions),
   - append any D-entries,
   - deliver both in one relay (`srj-relay`).

**CODER (a new OpenCode session) on start:**
1. Read `AGENTS.md`, then this file, then `docs/DECISIONS.md`.
2. Run `gh issue list --label ready-for-code` and `gh pr list`.
3. Pick up the lowest-numbered `ready-for-code` issue that isn't blocked (see the dependencies in §4).

---

## 2. Project in one paragraph

An agentic research → code → test loop that produces intraday CFD strategies (≤1H, mostly ≤15m) built to **pass prop-firm challenges**. A challenge is a capped-fee option on funded capital. The bias is volume-first: Volume Profile, VWAP, and CVD on Dukascopy bid ticks; other edges are allowed. Every strategy is scored by a **challenge simulator** (P(pass), days-to-pass, EV per fee), not by Sharpe. New ideas arrive through the CODER's **Idea Funnel**, and the planner promotes the best to locked study cards (D-024).

## 3. Roles & bridge (D-019, D-023, D-024)

| Role | Who | Where |
|---|---|---|
| PLANNER (director: plans, specs, reviews, decides) | PromptQL bot | cloud; can't see D: drive; never runs a VM |
| CODER (builder: code, all data download and compute, web research, Idea Funnel, reports) | OpenCode, in sirooj's Windows terminal | `D:\SRJ Venture` (repo + data, `SRJ_DATA`) |
| OPERATOR (approvals, domain answers, final say) | sirooj | carries relays and CODER reports between the two |
| Bridge | GitHub relay on `sirooj/SRJ-Ventures` | Issues (`ready-for-code`) → `issue-<n>-<slug>` branch → PR `Closes #n` + `needs-review` + CODER report → planner review → merge |

Labels: `ready-for-code`, `in-progress`, `needs-review`, `question`, `research`, `data`, `execution-critical`.
**Known blocker:** the PromptQL GitHub App isn't installed on the repo, so planner writes return 403. Until it is fixed, the planner drafts and the CODER files verbatim (D-015).

## 4. Status board

**Phase 0 · Foundation:** ✅ merged (PR #1, 2026-10-05). Default branch = `main`.

**Phase 1 · Data + evaluator:** 🔄 in progress.

| # | Title | Depends on | Status |
|---|---|---|---|
| #2 | [DATA] Full-history pilot + index point verification | — | downloading (single run, pinned 16.62.244.190, atomic .bi5 writes); then convert FX → verify indices → bars → PR. Also feeds the edge track (E-015). |
| #3 | [PROPFIRM] Rules schema + loader + 3 YAMLs | — | ✅ PR #8 merged |
| #4 | [PROPFIRM] Challenge simulator v0 + MC + demo | #3 | PR #11 `needs-review` |
| #5 | [RESEARCH] Read-only MQL5 inventory | — | PR #10 `needs-review`; baseline = SRJ Flow Nexus EA (D-021) |
| #6 | [CODE] Phase 0 follow-ups | #2 | queued (`ready-for-code`) |
| #9 | [TOOLS] mcp-mt5 for headless Strategy Tester runs + deals export | #5 inventory | PR #12 `needs-review` (D-022) |

**Workflow v2 · Reuse + funnel (D-024, D-025):** filed (PR #24, 03d6d61).

| # | Title | Depends on | Status |
|---|---|---|---|
| W1 (#20) | [TOOLS][FUNNEL] Idea Funnel scaffold + validator | W2 for rungs 2–3 | ready-for-code |
| W2 (#21) | [TOOLS] research-web ladder: install + smoke test | — | ready-for-code |
| W3 (#22) | [TOOLS][BACKTEST] Engine spike: vectorbt + NautilusTrader vs study 01 | NAS100 bars for study 01's IS window (#17 / #2) | ready-for-code |
| W4 (#23) | [RESEARCH][EDGE] Back-fill `TRIALS.csv` | — | ready-for-code |
| W5 (#<new>) | [TOOLS][FUNNEL] Vault inbox + Telegram exporter | #20 | ready-for-code |

## 5. Next actions

1. **CODER:**
   - Commit relay WORKFLOW 02 (and WORKFLOW 01, if it is still uncommitted), file W1–W4, and report.
   - Create the label `execution-critical`.
   - Keep #2 running.
   - Add a CODER report in Evidence order (`srj-relay`) to the bodies of PRs #10, #11 and #12 if they don't have one.
   - Write `docs/RUNBOOK.md`, now including the research-web setup and the funnel command.
   - Order: W2 → W1 → W3 (once its data exists). Start #6 once #2 lands.
2. **sirooj:**
   - Optional: get a DeepAPI key (deepapi.co) and save it under `D:\SRJ Venture\.secrets\`. The weekly cap is $3 (D-024). Without a key, the funnel uses curated sources only.
   - Veto or edit SOURCES.md entries (the planner curates it, D-025). Capture Discord, Telegram and EA material into the vault inbox. When W5 starts, create a Telegram API id at my.telegram.org, save it under `.secrets\`, and list the channels to allow-list.
   - Answer any still-open #5 items: the timeframes/sessions of Flow Nexus, and whether there is any MT5 statement or tester report.
   - Fill the FTMO/The5ers fee tables when convenient.
3. **PLANNER:**
   1. Review PRs #11, #10 and #12 from their CODER reports.
   2. Review the W1–W3 reports and update the verdicts in `docs/TOOLING.md`.
   3. Each session, once the funnel has run: read `research/funnel/queue.md` and promote, park or reject (`srj-idea-funnel`).
   4. Pick the port scope.
   5. Draft strategy cards 1–8 as `research/cards/*.md`.
   6. Each session: review SOURCES.md 'Discovered' entries and the vault-derived candidates.

## 6. Hard constraints (from DECISIONS)

- Storage only on `D:\SRJ Venture`. **No data in git.** No MQL5 source or exact params while the repo is public.
- Strategies: hold ≥2–3 min; ≤2,000 server requests/day (SL moves only at bar close); ±5 min news blackout; visible SL on every order; flat before Friday close; best-day cap; your own code only.
- All prop-firm rules are `verify_before_purchase`.

## 7. Pointers

- Blueprint v0.2: `docs/architecture.md`
- Reuse registry: `docs/TOOLING.md` (D-022, D-024)
- Idea Funnel: `research/funnel/` (`srj-idea-funnel`); trial ledger: `research/edge/TRIALS.csv` (E-016)
- Prop-firm shortlist: FTMO + The5ers primary; E8 Markets + Blue Guardian secondary (D-009)
- Workflow: the planner directs and the CODER computes; no cloud VM (D-023); reuse before build, funnel and research-web (D-024). Skills: `.opencode/skills/` (AGENTS §5).
- PromptQL bots:
  - session 1 = "1 SRJ Ventures Bot" (previous project)
  - session 2 = `https://prompt.ql.app/project/p-133b1b19-6e80/promptql-playground/thread/9d8237ea-fdb3-4d6f-b8bb-dc1c0b32311b`
  - session 3 (workflow revision) = `https://prompt.ql.app/project/p-bfb8eb54-4272/promptql-playground/thread/faa09a35-8233-42b5-8b5a-ff8ad462e3ee`
  - workflow v2 = `https://prompt.ql.app/project/p-bfb8eb54-4272/promptql-playground/thread/15269cb1-95b2-4c4f-b429-fcc7ea935588`
  - workflow v3 = https://prompt.ql.app/project/p-78aa168c-b098/promptql-playground/thread/e4d720de-937a-43f3-954e-ee6933bf5f17

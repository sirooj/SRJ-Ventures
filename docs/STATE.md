# SRJ Ventures: STATE (session pointer)

> **Read this first in every new session**, whether you are the PromptQL planner or the OpenCode coder. It is the single source of truth for "where are we". History lives in git, decisions live in `docs/DECISIONS.md`, and the long-term domain context lives in `docs/WIKI_SEED.md` and the PromptQL wiki.
> **Owner of this file:** the PLANNER updates it at the end of every session, via a PR or a CODER relay. The CODER may fix numbers or facts and must note that in the PR.

_Last updated: 2026-10-05 (planner session 2, bot `9d8237ea-fdb3-4d6f-b8bb-dc1c0b32311b`)_

---

## 1. How to resume (no copy-paste)

**sirooj, starting a new PromptQL session:** paste only this:
```
@<bot name> Resume SRJ Ventures. Read https://github.com/sirooj/SRJ-Ventures/blob/main/docs/STATE.md (+ DECISIONS.md, WIKI_SEED.md), then continue from "Next actions". Latest CODER message: <paste only the newest CODER message, if any>
```

**PLANNER (a new PromptQL bot) on start:**
1. Read the `SRJ Ventures` wiki page. If it doesn't exist (new project), seed it from `docs/WIKI_SEED.md` with a learning block.
2. Fetch `docs/STATE.md`, `docs/DECISIONS.md`, open issues, and open PRs from GitHub (`__github` integration).
3. Continue from §5 "Next actions". Never re-decide anything listed in DECISIONS.md without a new D-entry.
4. At session end: update this file (status, issue table, next actions), append any D-entries, and deliver the result as a PR or a CODER relay.

**CODER (a new OpenCode session) on start:**
1. Read `AGENTS.md`, then this file, then `docs/DECISIONS.md`.
2. Run `gh issue list --label ready-for-code` and `gh pr list`.
3. Pick up the lowest-numbered `ready-for-code` issue that isn't blocked (see the dependencies in §4).

---

## 2. Project in one paragraph

An agentic research → code → test loop that produces intraday CFD strategies (≤1H, mostly ≤15m) built to **pass prop-firm challenges**. A challenge is a capped-fee option on funded capital. The bias is volume-first: Volume Profile, VWAP, and CVD on Dukascopy bid ticks; other edges are allowed. Every strategy is scored by a **challenge simulator** (P(pass), days-to-pass, EV per fee), not by Sharpe.

## 3. Roles & bridge

| Role | Who | Where |
|---|---|---|
| PLANNER (orchestrator + researcher + reviewer) | PromptQL bot | cloud; can't see D: drive |
| CODER | OpenCode, in sirooj's Windows terminal | `D:\SRJ Venture` (repo + data, `SRJ_DATA`) |
| Bridge | GitHub relay on `sirooj/SRJ-Ventures` | Issues (`ready-for-code`) → `issue-<n>-<slug>` branch → PR `Closes #n` + `needs-review` → planner review → merge |

Labels: `ready-for-code`, `in-progress`, `needs-review`, `question`, `research`, `data`.
**Known blocker:** the PromptQL GitHub App isn't installed on the repo, so planner writes return 403. Until it is fixed, the planner drafts and the CODER files verbatim (D-015).

## 4. Status board

**Phase 0 · Foundation:** ✅ merged (PR #1). Default branch = `main`.

**Phase 1 · Data + evaluator:** 🔄 in progress.

| # | Title | Depends on | Status |
|---|---|---|---|
| #2 | [DATA] Full-history pilot + index point verification | — | downloading (single run, pinned edge, atomic writes, ~0.3–0.5 files/s, multi-day); then convert FX → verify indices → bars → PR |
| #3 | [PROPFIRM] Rules schema + loader + 3 YAMLs | — | ✅ merged (PR #8) |
| #4 | [PROPFIRM] Challenge simulator v0 + MC + demo | #3 | PR #11 needs-review (demo: ours P(pass) 0.70 vs LuxAlgo 1.00, 50 paths; 4 semantics deltas in compare.md) |
| #5 | [RESEARCH] Read-only MQL5 inventory | — | PR #10 needs-review; 3 open questions for sirooj in the PR |
| #6 | [CODE] Phase 0 follow-ups | #2 | queued |
| #9 | [TOOLS] mcp-mt5 + deals → trades converter | #5 | PR #12 needs-review (includes docs/RUNBOOK.md). BLOCKED: tester pass needs ≥5 GB free on C: (now 0.2 GB) |

Known tool quirk: mcp-mt5 compile fails on paths containing spaces; use space-free paths.

## 5. Next actions

1. **PLANNER:** review PR #10, #11, #12. Check the #11 0.70-vs-1.00 gap is explained by intra-trade excursion and not by a rule bug; run LuxAlgo with more paths. Then pick the Flow Nexus port scope and draft strategy cards 1–8 in `research/cards/*.md`.
2. **sirooj:** answer the 3 #5 follow-ups in PR #10: revision baseline, session details, broker statement. Decide on C: space: relocate or prune `opencode.db` (33.6 GB) and the MT5 logs (~1.5 GB/day). Fill the FTMO/The5ers fee tables when convenient.
3. **CODER:** keep #2 running. Address the review comments on #10, #11 and #12. Run the Flow Nexus tester pass once C: has ≥5 GB free.

## 6. Hard constraints (from DECISIONS)

- Storage only on `D:\SRJ Venture`. **No data in git.** No MQL5 source or exact params while the repo is public.
- Strategies: hold ≥2–3 min; ≤2,000 server requests/day (SL moves only at bar close); ±5 min news blackout; visible SL on every order; flat before Friday close; best-day cap; your own code only.
- All prop-firm rules are `verify_before_purchase`.

## 7. Pointers

- Blueprint v0.2: `docs/architecture.md`
- Prop-firm shortlist: FTMO + The5ers primary; E8 Markets + Blue Guardian secondary (D-009)
- PromptQL bots: session 1 = "1 SRJ Ventures Bot" (previous project); session 2 = `https://prompt.ql.app/project/p-133b1b19-6e80/promptql-playground/thread/9d8237ea-fdb3-4d6f-b8bb-dc1c0b32311b`

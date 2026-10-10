---
name: srj-idea-funnel
description: The CODER's Idea Funnel. Scans sources for intraday CFD strategy ideas, dedupes them, drafts card candidates with an Evidence Packet, and validates them. It never touches market data, backtests or optimises. Use when sirooj says "run funnel" or a scheduled run starts. The PLANNER uses it to review queue.md.
---

# SRJ Idea Funnel (D-024, E-016)

Adapted from the Daily Strategy Funnel template. Its Phase 2 (automatic backtest and optimise) is **removed on purpose**. Studies run only from a PLANNER-locked card (E-010), and an unattended run must never touch the forward holdout (E-013).

## Read first, in this order
1. `AGENTS.md`
2. `.opencode/skills/srj-hard-constraints/SKILL.md`
3. `research/edge/EDGE_STATE.md` (study log, Dead Ideas) and `research/edge/DECISIONS_EDGE.md`
4. `research/funnel/SOURCES.md`
5. `research/funnel/index.csv` and `research/funnel/rejected/index.csv`
6. `.opencode/skills/srj-research-web/SKILL.md`

Never edit: the decision logs, the STATE pointers, any locked `CARD.md`, `docs/propfirm_rules/*.yaml`, `config/instruments.yaml`, or the skills.

## Run size
- **Floor:** 3 queued candidates. **Ceiling:** 15 evaluated ideas. Stop at whichever comes first.
- **Shortfall:** if the ceiling is hit below the floor, log `shortfall` with the reason. Never pad the queue.
- **Lookback:** 30 days for forums, social and news. No limit for papers and classic sources; dedup prevents repeats.

## Per idea
1. **Screen** against the hard-reject list. On a hit, write a row to `rejected/index.csv` and move on.
2. **Dedup:**
   - `hash` = the first 6 hex of SHA-256 of `normalise(hypothesis) | instrument | timeframe`, where normalise means lowercase and collapsed whitespace.
   - An exact hash match against candidates or rejects → hard reject `duplicate`.
   - The same family as a study or a Dead Idea (for example the E-008 ORB family) on the same instrument and timeframe → hard reject `dead_idea`. Related but different → queue with `related_to`.
3. **Due diligence** (`srj-research-web`, source scepticism). Read the full source, not the headline.
4. **Write** the candidate folder (below).
5. **Validate.** Any miss → redraft, at most 2 retries → otherwise reject with the name of the failed check.

### Hard reject
- Hold under 3 minutes; HFT, arbitrage, latency exploitation, copy trading.
- No stop loss; martingale, grid, or averaging down.
- Needs weekend holding, more than 2,000 server requests per day, or non-CFD instruments.
- No codifiable entry and exit rule; an incoherent hypothesis.
- `duplicate` or `dead_idea`.

### Soft warning (queue with the flag)
- `out_of_universe`: outside the pilot set (EURUSD, GBPUSD, USDJPY, US500 = `USA500IDXUSD`, NAS100 = `USATECHIDXUSD`) but portable.
- `volume_port`: needs exchange volume, footprint or L2, but ports to bid-tick count or tick-rule CVD.
- `volume_read: missing`: states no volume read (E-004). The PLANNER usually rejects these.
- `session`: outside the London and New York sessions.
- `regime`: regime-dependent.
- `related_to: <id>`.

## Candidate folder
`research/funnel/candidates/<YYYY-MM-DD>_<SYM>_<TF>_<slug>_<hash>/`
- `review.md`:
  - frontmatter: `id, hash, status: QUEUED, family, instrument, timeframe, session, volume_read, flags, related_to, sources, created`;
  - body: a one-line claim, then the disclaimer "Unverified external claim. Not tested on SRJ data."
- `evidence.md`, the Evidence Packet, in this order:
  1. Claim (one line).
  2. Source record: URL, author, date, rung, private file name.
  3. Raw evidence as the source states it, labelled with its sample type (IS / OOS / live / unstated / screenshot).
  4. Counter-evidence: failure cases, contradicting sources, conditions where it shouldn't work. If none: "searched <where>, none found".
  5. Mechanism, and who is on the other side.
  6. Builder's note: opinion, labelled, last. No verdict words.
- `card_draft.md`: `.github/ISSUE_TEMPLATE/strategy.md` filled in as far as the source allows, plus the volume read, the `srj-hard-constraints` checklist, and open codification questions. No grid and no kill criteria: the PLANNER writes those.
- `source.md`: URL, author, retrieval date, a summary of 3–5 sentences, and at most one quote of ≤15 words cited as `NN-slug.md:START-END`.

No code, no numbers of our own, no market data.

## Validator (a script, built in task W1)
**Static:** the four files exist; the required headings and frontmatter keys exist; `hash` is unique across candidates and rejects.

**Dynamic:**
1. The quote in `source.md` appears verbatim in the private source file at the cited lines.
2. The URL returned HTTP 200 at retrieval.
3. `card_draft.md` has a non-empty volume read (or the `volume_read: missing` flag) and a filled constraint checklist.
4. `evidence.md` has a counter-evidence entry.
5. No verdict words ("works", "profitable", "proven", "edge confirmed", …) outside quotes.
6. No numbers presented as SRJ results.

## Files updated every run
- `index.csv`: `id, hash, created, instrument, timeframe, family, flags, related_to, status, source_url`.
- `rejected/index.csv`: `date, idea, hash, rule, reason, source_url`.
- `queue.md`:
  - pending candidates, newest first (id, claim, flags, link);
  - then a **Reject sample**: 3 random rejects since the last run, each with its rule and reason.
- `runs.log`: `<YYYY-MM-DD HH:MM> | funnel | scanned=N queued=N rejected=N redrafts=N deepapi_usd=X.XX | notes`.
- `SOURCES.md`: append new sources under "Discovered (unreviewed)".

## Commit and merge
- Branch `funnel-<YYYY-MM-DD>`, touching only `research/funnel/**`.
- The CODER merges once the validator, `uv run pytest` and `uv run ruff check .` pass (D-024).
- Put the run's `runs.log` line in the PR body.

## PLANNER review (once per session, cheap)
Read `research/funnel/queue.md` only.
- For each candidate, decide **promote**, **park** or **reject**.
- Check the reject sample for wrong kills.
- **Promote:** the next relay sets `status: PROMOTED` and carries a new locked `CARD.md` (`srj-edge-study`).
- **Park / reject:** the next relay sets the status and the reason.

Only a promoted card ever touches data.

## Scheduled runs
- Manual ("run funnel"), or nightly through Windows Task Scheduler using OpenCode's non-interactive mode. The exact command lives in `docs/RUNBOOK.md`.
- Never use a PromptQL scheduled trigger: it spends credit.

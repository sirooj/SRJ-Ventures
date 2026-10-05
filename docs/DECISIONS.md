# SRJ Ventures: Decisions Log

Append-only. Each entry records the date, the decision, and the reason. Never edit old entries; supersede them with a new one ("Supersedes D-00x").

| ID | Date | Decision | Why |
|---|---|---|---|
| D-001 | 2026-10-05 | Roles: PromptQL bot = orchestrator + researcher (PLANNER); OpenCode in sirooj's terminal = CODER. | The cloud bot can't read the local repo or data; OpenCode can. |
| D-002 | 2026-10-05 | The bridge is the GitHub relay on `sirooj/SRJ-Ventures` (issues → branch → PR → review). No SCAS tunnel. | SCAS doesn't support Windows; the relay also leaves an audit trail. |
| D-003 | 2026-10-05 | Goal: use the convex payout of prop-firm capital. Strategies are intraday, ≤1H (mostly ≤15m), high win rate but tail-checked. | Pass challenges quickly. The capped fee is the downside. |
| D-004 | 2026-10-05 | Fitness function = prop-firm challenge simulator (P(pass), days-to-pass, EV per fee, P(breach) by rule), not Sharpe. | A challenge is a bounded option; negative-skew systems breach drawdown rules. |
| D-005 | 2026-10-05 | Volume-first bias (Volume Profile, VWAP, CVD); other edges (statistical, time-of-day, OFI, oscillators) allowed. | sirooj's existing edge and preference. |
| D-006 | 2026-10-05 | CFD only for now. Data = Dukascopy free ticks. Volume analysis on the **bid** side; VP = tick count per bin; CVD = tick-rule proxy used for divergence only. L2/L3 not pursued. | No capital for futures data; there is no free L2/L3; CFD books are broker-internal. |
| D-007 | 2026-10-05 | Validate the volume proxy instead of buying data: Dukascopy POC/VA vs futures profiles; tick-rule CVD vs true CVD on free crypto aggTrades. | Cheap evidence that the CFD volume edge is real. |
| D-008 | 2026-10-05 | Pilot instruments: EURUSD, GBPUSD, USDJPY, USA500IDXUSD, USATECHIDXUSD, 2023→today. Other majors + US30/DAX/FTSE later. | Lowest spread and commission. |
| D-009 | 2026-10-05 | Prop firms: FTMO + The5ers primary; E8 Markets + Blue Guardian secondary. Excluded: FundedNext (EA only <$50K), Alpha Capital (no full automation), FundingPips (payout-denial complaints). | Reputation plus clearest EA rules. All rules marked verify-before-purchase. |
| D-010 | 2026-10-05 | First rule file: FTMO 2-Step Standard, then FTMO 1-Step and The5ers High Stakes. The simulator marks open trades at the worst price each minute (equity-based daily loss). | The most automation-friendly program; FTMO daily loss is measured on equity. |
| D-011 | 2026-10-05 | All storage on `D:\SRJ Venture` (repo, data, Python, uv/pip caches). Data never goes in git; paths via `SRJ_DATA`. | C: drive is full. |
| D-012 | 2026-10-05 | Repo is public, so no MQL5 source or exact parameters are committed. Detailed legacy inventory lives in `D:\SRJ Venture\private\`. | Protect sirooj's edge. |
| D-013 | 2026-10-05 | PR #1 (Phase 0) approved. Follow-ups go in #6 and run after #2. | Clean work; follow-ups are non-blocking. |
| D-014 | 2026-10-05 | Accepted the CODER review of the Phase 1 drafts: `--no-convert` flag; never cache the current UTC hour; A.5 reworded to verify-after; B split into B1 (rules) + B2 (sim); `max_requests_per_day` documented but unmodeled in sim v0. | Prevents converting indices before verification and stale-skip bugs; keeps PRs reviewable. |
| D-015 | 2026-10-05 | Until the PromptQL GitHub App can write to the repo, the CODER files planner-authored issues verbatim via `gh` in the agreed order and reports the numbers back. | The planner gets 403 on writes; this keeps numbering deterministic. |
| D-016 | 2026-10-05 | Session continuity: `docs/STATE.md` is the pointer every new session reads first; this log holds decisions. The planner updates STATE.md at the end of each session. | No more pasting chat history between sessions. |
| D-017 | 2026-10-05 | Rulebook semantics: daily loss = `reference` (initial / reset_balance / reset_max_balance_equity) minus `pct` of (`initial` or `reference`); trailing max loss uses a `trail_reference` enum and a `lock_at` enum; floors are pinned by `daily_floor`/`max_floor` helpers with tests. Unverified rules default to the stricter reading (equity, unmodeled = false); unknown keys are rejected. | FTMO's floor is reset balance − 5% of initial; a single `basis` field conflated the two, and a lenient sim overstates P(pass). |
| D-018 | 2026-10-05 | While the PromptQL GitHub App can't write: the CODER posts planner reviews verbatim as PR comments prefixed "Planner review (relayed):"; sirooj performs merges after planner approval. | Keeps the audit trail on GitHub and the CODER never self-merges. |

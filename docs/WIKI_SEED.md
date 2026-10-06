# SRJ Ventures: Wiki Seed (portable long-term context)

> **Purpose:** if a new PromptQL project, or any other AI tool, starts with an empty wiki, it creates these pages from this file. Every entry here is durable context, not status. Status lives in `STATE.md` and `research/edge/EDGE_STATE.md`.
> **Format:** each `##` heading is one wiki page title, with its aliases in brackets.

## SRJ Ventures  [aliases: SRJ, SRJ Venture]
sirooj's quantitative automated-trading project: an agentic research → code → test loop producing intraday CFD strategies (≤1H chart timeframe, mostly ≤15m) optimized to pass prop-firm challenges.
- **Repo:** `github.com/sirooj/SRJ-Ventures` (public).
- **Local root:** `D:\SRJ Venture`. All data and caches are on D:, because C: is full.
- **Two tracks**, one per session; the resume line names it:
  - the Flow Nexus port + infrastructure: pointer `docs/STATE.md`, decisions D-xxx in `docs/DECISIONS.md`,
  - edge research: pointer `research/edge/EDGE_STATE.md`, decisions E-xxx.
- **PromptQL projects** are numbered ("4 SRJ Venture", "5 SRJ Venture", "6 SRJ Venture", …). The bot's display name changes with them, so files refer to roles, not bot names.

## SRJ Planner–Coder Relay  [aliases: GitHub relay, relay protocol, PLANNER, CODER, OPERATOR]
- **Roles (D-023):**
  - **PLANNER:** the PromptQL bot, director of both tracks. Plans, writes specs, cards and relays, reviews, decides.
  - **CODER:** OpenCode in sirooj's Windows terminal. Builds, downloads and prepares all data, runs every study and backtest, reports.
  - **OPERATOR:** sirooj. Approvals, domain answers, final say.
- All data and compute live on sirooj's machine. The planner never runs a cloud VM (see SRJ Credit Budget).
- **Flow:**
  1. The planner writes a relay, and sirooj pastes it to the CODER. The planner can't write to GitHub itself: its writes return 403 until the PromptQL GitHub App gets write access.
  2. The CODER commits the relay's files verbatim and files its tasks as Issues labelled `ready-for-code`.
  3. The CODER comments "picked up", adds `in-progress`, and works on branch `issue-<n>-<slug>`.
  4. The CODER opens a PR (`Closes #n`, `needs-review`) with a compact CODER report. sirooj pastes the newest report into the next planner session.
  5. Merging needs a relayed planner approval for the head SHA (D-020). Edge-only PRs follow E-005 / E-014.
- SCAS is not used because it doesn't support Windows.

## SRJ Credit Budget  [aliases: credit budget, no-VM rule]
- sirooj's PromptQL credit is limited, and cloud VMs drained it fastest. Since 2026-10-06 the planner never provisions a VM (D-023).
- The planner uses the program runtime only for small GitHub reads and for assembling relays. No downloads, studies or backtests run in PromptQL.
- The planner reviews work from the CODER report in the PR body, not from raw result files, and aims for one relay per session.
- Skill: `srj-credit-budget`.

## SRJ Skills  [aliases: skills, .opencode/skills]
Shared working rules for both agents, kept in `.opencode/skills/<name>/SKILL.md`. A rule changes by editing its skill, together with a decision entry (E-007).
- `srj-session-start`: first steps of every session — pick the track, read the pointer and the decisions log.
- `srj-credit-budget`: the planner's cost rules — no VM, cheap reads, one relay per session.
- `srj-hard-constraints`: the non-negotiable strategy, data and repo rules.
- `srj-relay`: writing, executing and reporting on a relay. It replaced `srj-research-backup`.
- `srj-local-data`: the CODER's Dukascopy download, verification, conversion and bar building on D:.
- `srj-edge-study`: the card-first study method — the planner designs and rules, the CODER runs.

## SRJ Edge Research  [aliases: edge track, edge research]
- A separate track for new intraday CFD edges, independent of the Flow Nexus port. Pointer: `research/edge/EDGE_STATE.md`. Decisions: `research/edge/DECISIONS_EDGE.md` (E-xxx).
- Volume-first is mandatory (E-004). Every study leads with a bid-tick volume read: VP, VWAP, tick-rule CVD, or tick-count RVOL.
- **Card first:**
  - IS/OOS dates, grid and kill criteria are locked before any data is seen.
  - IS work is committed before OOS runs.
  - A null result is a result.
- **Dead idea:** unconditioned US-index open scalping (ORB, ORB fade, Gao intraday momentum) has no edge. Don't retest it (E-008).

## Prop-Firm Challenge Simulator  [aliases: challenge sim, propfirm sim]
- The project's fitness function. It scores strategies by:
  - P(pass),
  - median days to pass,
  - P(breach) by rule,
  - EV per fee = P(pass)·E[first payout] − fee.
- It replays trades on 1m bid bars, marking open trades at the adverse extreme each minute: longs at the bid low, shorts at the bid high + max spread.
- It evaluates each rule in that firm's reset timezone, using a block bootstrap over daily trade sequences.
- Rules it can't model are reported as `unmodeled`: request counts, news windows, device/IP.
- Rulebooks live in `docs/propfirm_rules/*.yaml`.

## Dukascopy Tick Data  [aliases: Dukascopy, bi5]
- Free quote ticks (bid/ask + quoted size), not trades, so there is no aggressor side.
- Volume conventions:
  - Volume analysis uses the **bid side**.
  - Volume Profile = tick count per bin.
  - VWAP = tick-weighted bid.
  - CVD = tick-rule proxy, used for divergence only.
- Point values:
  - FX 1e5; JPY pairs 1e3.
  - Indices must be verified tick-exact before conversion. `USA500IDXUSD` and `USATECHIDXUSD` use `point=1000`, verified (E-011).
  - dukascopy-node can silently drop hours, so it is not a completeness reference.
- Sirooj's local ISP hijacks feed DNS, so the downloader uses DoH (`--resolve auto`) with TLS intact.
- Dukascopy throttles downloads. The CODER downloads the data once into `SRJ_DATA`, and both tracks share it.
- MT5-imported months have zero quote volumes.

## SRJ Target Prop Firms  [aliases: prop firms, FTMO, The5ers]
- Primary: FTMO, then The5ers. Secondary: E8 Markets, Blue Guardian.
- Excluded:
  - FundedNext: EAs only on accounts under $50K.
  - Alpha Capital: trade-management EAs only.
  - FundingPips: payout-denial complaints.
- Key FTMO detail: the 5% daily loss is measured on equity from the 00:00 Europe/Prague balance.
- Strategy hard limits:
  - hold time of at least 2–3 min
  - ≤2,000 server requests per day
  - ±5 min news blackout
  - visible SL on every order
  - flat before the weekend
  - best-day cap
  - own code only, one device/IP per account

## SRJ Legacy MQL5 Projects  [aliases: SRJ_FlowLogic, SRJ_Indicators, SRJ Flow Nexus EA]
- `D:\SRJ_FlowLogic_MT5_Port (9)\SRJ_FlowLogic_Project`: market-structure logic (Bias, Orderblock, Imbalance, Fractals).
- `D:\SRJ_Indicators\`: tick-based volume profile, plus `SRJ_TickCore.mqh`.
- **Port baseline: the SRJ Flow Nexus EA** (D-021).
  - It orchestrates the SRJ POI Marker, SRJ Flow Logic and SRJ CQD indicators.
  - It targets EURUSD/GBPUSD/USDJPY and is not production-ready.
- Confidential: never commit the source or exact parameters while the repo is public.

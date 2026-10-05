# SRJ Ventures: Wiki Seed (portable long-term context)

> **Purpose:** if a new PromptQL project, or any other AI tool, starts with an empty wiki, it creates these pages from this file. Every entry here is durable context, not status. Status lives in `STATE.md`.
> **Format:** each `##` heading is one wiki page title, with its aliases in brackets.

## SRJ Ventures  [aliases: SRJ, SRJ Venture]
sirooj's quantitative automated-trading project: an agentic research → code → test loop producing intraday CFD strategies (≤1H, mostly ≤15m) optimized to pass prop-firm challenges. Repo: `github.com/sirooj/SRJ-Ventures` (public). Local root: `D:\SRJ Venture` (all data and caches on D:; C: is full). Session pointer: `docs/STATE.md`. Decisions: `docs/DECISIONS.md`.

## SRJ Planner–Coder Relay  [aliases: GitHub relay, relay protocol, PLANNER, CODER]
- The PromptQL bot is the PLANNER (orchestrates, researches, reviews). OpenCode in sirooj's Windows terminal is the CODER.
- They communicate only through GitHub Issues and PRs on SRJ-Ventures:
  1. The planner files an issue with the `ready-for-code` label.
  2. The coder comments "picked up", adds `in-progress`, and works on branch `issue-<n>-<slug>`.
  3. The coder opens a PR with `Closes #n` and the `needs-review` label.
  4. The planner reviews and merges.
- Anything the planner needs from sirooj's machine (files, numbers, re-runs) must be requested through an issue.
- SCAS is not used because it doesn't support Windows.

## Prop-Firm Challenge Simulator  [aliases: challenge sim, propfirm sim]
- The project's fitness function. It scores strategies by P(pass), median days to pass, P(breach) by rule, and EV per fee = P(pass)·E[first payout] − fee.
- It replays trades on 1m bid bars, marking open trades at the adverse extreme each minute (longs at bid low; shorts at bid high + max spread).
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
- Point values: FX 1e5, JPY pairs 1e3. Indices must be verified tick-exact via dukascopy-node before conversion.
- Sirooj's local ISP hijacks feed DNS, so the downloader uses DoH (`--resolve auto`) with TLS intact.
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

## SRJ Legacy MQL5 Projects  [aliases: SRJ_FlowLogic, SRJ_Indicators]
- `D:\SRJ_FlowLogic_MT5_Port (9)\SRJ_FlowLogic_Project`: market-structure logic (Bias, Orderblock, Imbalance, Fractals).
- `D:\SRJ_Indicators\`: tick-based volume profile, plus `SRJ_TickCore.mqh`.
- Confidential: never commit the source or exact parameters while the repo is public.

---
name: srj-hard-constraints
description: Checklist of the non-negotiable SRJ Ventures strategy, data and repo rules. Use before proposing, coding, backtesting or approving any strategy, and before any commit.
---

# SRJ hard constraints

**Sources of truth:** `docs/DECISIONS.md`, `research/edge/DECISIONS_EDGE.md`, `docs/WIKI_SEED.md` and `docs/propfirm_rules/*.yaml`. If this checklist disagrees with them, they win; fix this file through a decision entry.

## Strategy: check every setup and every test
- [ ] **Instruments:** CFDs only (D-006). Pilot set: EURUSD, GBPUSD, USDJPY, US500 (`USA500IDXUSD`), NAS100 (`USATECHIDXUSD`) (D-008).
- [ ] **Timeframe:** chart timeframe ≤1H, mostly ≤15m (D-003). ≤1H is not a cap on trade duration (E-003). Scalping is preferred.
- [ ] **Sessions:** London and New York only (E-002).
- [ ] **Lens:** volume-first. The setup states its bid-tick volume read (D-005, E-004).
- [ ] **Hold time:** at least 3 min before any exit other than the stop loss.
- [ ] **Stop loss:** a visible SL on every order, from the moment of entry.
- [ ] **Server requests:** ≤2,000 per day. SL/TP moves happen only at bar close.
- [ ] **News:** ±5 min blackout around high-impact releases. On index opens, no entries 09:55–10:05 ET.
- [ ] **Weekends:** flat before Friday close; no weekend holding.
- [ ] **Best day:** respect the best-day / consistency cap in the target firm's YAML.
- [ ] **Behaviour:** own code only; one device/IP per account; nothing that looks like arbitrage, latency exploitation, HFT or copy trading.
- [ ] **Firms:**
  - Primary: FTMO, The5ers.
  - Secondary: E8 Markets, Blue Guardian.
  - Excluded: FundedNext, Alpha Capital, FundingPips (D-009).
- [ ] **Fitness:** challenge simulation — P(pass), days to pass, EV per fee, P(breach) by rule — not Sharpe (D-004).
  - FTMO daily loss is measured on equity against the 00:00 Europe/Prague balance.
  - Where a rule is unverified, use the stricter reading (D-010, D-017).
- [ ] **Verification:** every firm rule is `verify_before_purchase`.

## Data and research
- Use the **bid** side for price and volume. Use the ask side only for spread and cost (D-006).
- Indicator definitions (D-006):
  - Volume Profile = tick count per price bin.
  - VWAP = tick-weighted bid.
  - CVD = tick-rule proxy, used for divergence only.
- Dukascopy ticks are quotes, not trades. Treat tick count as a volume proxy and keep D-007 (validate the proxy) in mind.
- Timestamps are UTC internally; sessions use `zoneinfo`. No lookahead: features use only data available at bar close.
- Verify index point values tick-exact before converting.
- **Costs:** real ask−bid spread + commission + stress slippage. Always also report the result at zero slippage.
- **Honesty:** split in-sample and out-of-sample by date before looking. Report how many configurations were tried. A null result is a result.

## Repo
- Never commit data (ticks, parquet, bars, `.bi5`) or secrets. Committed results must be under 1 MB.
- The repo is public, so no MQL5 source and no exact legacy parameters (D-012).
- Local storage on D: only (D-011). Paths come from `SRJ_DATA`; never hardcode them.
- New Python must pass `uv run ruff check .`, and `uv run pytest` must stay green.

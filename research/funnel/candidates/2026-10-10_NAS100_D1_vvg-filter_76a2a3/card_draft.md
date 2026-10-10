## Strategy: VVG-DAY-FILTER-NQ (draft — PLANNER writes grid + kill criteria)

## Hypothesis
Premarket gap, first-30-minute range and first-bar participation identify unusual days whose intraday behaviour differs enough to deserve their own study.

## Universe & sessions
- Symbols: NAS100 (`USATECHIDXUSD`)
- Sessions (with timezones): New York 09:30–16:00 America/New_York (classifier inputs use premarket + first 30 minutes)
- Excluded periods (news, rollover, holidays): ±5 min news blackout; flat before Friday close

## Setup & triggers
- Indicators / levels used (with parameters): absolute overnight gap, absolute first-30-minute return, first-bar tick count vs 20-day baseline
- volume_read: first-bar tick-count vs 20-day rolling baseline
- Entry: to be codified (classifier first; any directional rule comes from the planner-locked card)
- Stop / target: to be codified (visible stop on every order, hold at least 3 minutes)
- Filters / no-trade conditions: classifier inactive on most days (about 4% flagged in the source)

## Risk & costs
- Risk per trade (% of equity): to be set by planner
- Spread/commission/slippage assumptions: Dukascopy bid/ask spread + commission
- Prop-firm program + relevant rules (drawdown type, daily loss, consistency): FTMO 2-Step Standard

## Success criteria
- Min trades, target expectancy, max drawdown, time in trial: to be set by planner (no grid and no kill criteria here)

## Definition of done for CODER
- [ ] Backtest over agreed history with costs
- [ ] Metrics + assumptions + open questions in PR (`Closes #<n>`, `needs-review`)

## srj-hard-constraints checklist
- [x] hold at least 3 minutes
- [x] at most 2,000 server requests per day (stop moves at bar close only)
- [x] ±5 min news blackout
- [x] visible stop on every order
- [x] flat before Friday close
- [x] own code only (source read as spec, nothing vendored)

## Open codification questions
- Exact premarket window for the gap and the first-bar definition on our 1m bars?
- Baseline length for first-bar participation (20-day vs adaptive)?
- Classifier as day filter for study-02-style rules vs standalone rule?

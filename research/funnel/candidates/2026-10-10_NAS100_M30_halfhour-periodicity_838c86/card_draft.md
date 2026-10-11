## Strategy: HALF-HOUR-PERIODICITY-NQ-30m (draft — PLANNER writes grid + kill criteria)

## Hypothesis
Index returns repeat at daily-clock half-hours because institutional flow repeats; a tick-count elevation confirms the rhythm is active today.

## Universe & sessions
- Symbols: NAS100 (`USATECHIDXUSD`)
- Sessions (with timezones): London 08:00–16:30 Europe/London, New York 09:30–16:00 America/New_York
- Excluded periods (news, rollover, holidays): ±5 min news blackout; flat before Friday close

## Setup & triggers
- Indicators / levels used (with parameters): half-hour returns, 20-day median same-half-hour tick count
- volume_read: tick-count relative volume (same half-hour vs 20-day median)
- Entry: to be codified (direction of prior same-half-hour return, gated by tick-count elevation)
- Stop / target: to be codified (visible stop on every order, hold at least 3 minutes)
- Filters / no-trade conditions: to be codified

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
- Which lookback for the same-half-hour direction (1 day vs multi-day average)?
- Tick-count elevation threshold and baseline window?
- Single half-hour hold vs timed exit?

## Strategy: HMM-MOMENTUM-ES-15m (draft — PLANNER writes grid + kill criteria)

## Hypothesis
Latent momentum states estimated without filter lag capture intraday persistence better than moving-average triggers.

## Universe & sessions
- Symbols: US500 (`USA500IDXUSD`)
- Sessions (with timezones): New York 09:30–16:00 America/New_York
- Excluded periods (news, rollover, holidays): ±5 min news blackout; flat before Friday close

## Setup & triggers
- Indicators / levels used (with parameters): HMM momentum state (2–3 states), volatility ratio, time-of-day season index
- volume_read: missing (returns-only model; no volume input — planner usually rejects these)
- Entry: to be codified (position follows the inferred state, lagged one bar)
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
- Bar length for state estimation (source aggregates ticks; port proposes M15)?
- Number of states and estimation method (Baum-Welch vs simplified)?
- Can a tick-count volume read be added without breaking the model?

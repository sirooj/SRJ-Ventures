## Claim
Trade US500 intraday momentum states from a Hidden Markov Model with volatility-ratio and time-of-day side information.

## Source record
- URL: https://arxiv.org/abs/2006.08307
- Author: Christensen, Godsill, Turner (2020)
- Date: 2020-06-15
- Rung: 1 (trafilatura via ar5iv full text)
- Private file: 01-hmm-momentum.md

## Raw evidence
As stated by the source (sample: ES tick data 2011, 258 days; OOS simulation with the signal lagged one period): a Hidden Markov Model of latent momentum states with volatility-ratio and seasonality side information reports the momentum effect as intact pre- and post-cost; IOHMM variants beat the plain HMM baseline by more than 10% on Sharpe ratio in their simulation.

## Counter-evidence
Single year (2011), single instrument (ES), in-sample-heavy Bayesian fitting with acknowledged convergence and prior-sensitivity caveats. No volume input anywhere in the model, so the mandatory volume-first lens is unmet. The side-information predictors (volatility ratio, seasonality) are time-of-day context, not a volume read. Searched the conclusions for out-of-sample breadth: none beyond the 2011 simulation is reported.

## Mechanism
Momentum states persist long enough that a lag-free state estimate can ride them; volatility-ratio and time-of-day inputs condition the transition odds. The other side: participants trading against stale filter-based signals.

## Builder's note
Opinion, labelled: codifiable as a state machine on our bars, but the missing volume read and the single-year fit make this the weakest of the three queued ideas; it needs a volume read added at card stage or a planner rejection. No verdict.

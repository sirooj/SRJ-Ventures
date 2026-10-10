# Idea Funnel queue

## Pending candidates (newest first)

- **2026-10-10_NAS100_M30_halfhour-periodicity_838c86** (tick-count volume read; NAS100 M30)
  - Claim: Trade NAS100 in the direction of yesterday same half-hour return, filtered by same-half-hour tick-count elevation.
  - Flags: none
  - Link: candidates/2026-10-10_NAS100_M30_halfhour-periodicity_838c86/review.md

- **2026-10-10_NAS100_D1_vvg-filter_76a2a3** (tick-count volume read; NAS100 D1)
  - Claim: Use the VVG premarket classifier to select unusual NAS100 days for intraday study.
  - Flags: related_to: study-02
  - Link: candidates/2026-10-10_NAS100_D1_vvg-filter_76a2a3/review.md

- **2026-10-10_US500_M15_hmm-momentum_c3e355** (volume_read: missing; US500 M15)
  - Claim: Trade US500 intraday momentum states from a Hidden Markov Model with volatility-ratio and time-of-day side information.
  - Flags: volume_read: missing
  - Link: candidates/2026-10-10_US500_M15_hmm-momentum_c3e355/review.md

## Reject sample (3 seeded-random rejects since last run)

- Risk-averse VWAP execution with volume uncertainty (Busseti 2015). [d30ef0]
  - Rule: no-codifiable-rule. Execution benchmark, no directional rule.

- Guaranteed VWAP pricing under permanent impact (Gueant 2013). [d6cf05]
  - Rule: no-codifiable-rule. Execution pricing, no directional rule.

- Overnight anomaly: hold US indices close-to-open for the overnight drift. [0c6112]
  - Rule: no-edge-on-universe. US-indices overnight/intraday divergence stopped in 2008 (Knuteson 2020 §II); absent on our pilot universe.

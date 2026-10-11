# Idea Funnel queue

## Pending candidates

None. Run 1 (2026-10-10) queued 3; all decided in WORKFLOW 04 (2 parked, 1 rejected).

## Parked (revisit on new evidence)

- **2026-10-10_NAS100_M30_halfhour-periodicity_838c86**
  - Claim: Trade NAS100 in the direction of yesterday same half-hour return, filtered by same-half-hour tick-count elevation.
  - Revisit if: a source shows index-level same-half-hour continuation, or a version where the tick-count surge itself carries direction.
  - Link: candidates/2026-10-10_NAS100_M30_halfhour-periodicity_838c86/review.md
- **2026-10-10_NAS100_D1_vvg-filter_76a2a3** (tagged for study 02)
  - Claim: Use the VVG premarket classifier to select unusual NAS100 days for intraday study.
  - Revisit after study 02 step 2 as an alternative unusual-day definition.
  - Link: candidates/2026-10-10_NAS100_D1_vvg-filter_76a2a3/review.md

## Rejected this round

- **2026-10-10_US500_M15_hmm-momentum_c3e355**: rule volume-first (E-004), single-year evidence.
  - Link: candidates/2026-10-10_US500_M15_hmm-momentum_c3e355/review.md

## Reject sample (3 seeded-random rejects from run 1)

- Risk-averse VWAP execution with volume uncertainty (Busseti 2015). [d30ef0]
  - Rule: no-codifiable-rule. Execution benchmark, no directional rule.
- Guaranteed VWAP pricing under permanent impact (Gueant 2013). [d6cf05]
  - Rule: no-codifiable-rule. Execution pricing, no directional rule.
- Overnight anomaly: hold US indices close-to-open for the overnight drift. [0c6112]
  - Rule: no-edge-on-universe. US-indices overnight/intraday divergence stopped in 2008 (Knuteson 2020 Sec. II); absent on our pilot universe.

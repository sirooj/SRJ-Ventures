## Claim
Trade NAS100 in the direction of yesterday same half-hour return, filtered by same-half-hour tick-count elevation.

## Source record
- URL: https://arxiv.org/abs/1005.3535
- Author: Heston, Korajczyk, Sadka (2010)
- Date: 2010-05-19
- Rung: 1 (trafilatura via ar5iv full text)
- Private file: 01-heston-halfhour.md

## Raw evidence
As stated by the source (sample: IS 2001–2005 NYSE stocks, OOS robustness incl. 2008 period): return continuation peaks at horizons that are exact multiples of one trading day; the daily decile spread earns about 2–3 basis points per half-hour with t-statistics near 10; volume shows similar periodic patterns.

## Counter-evidence
The test is cross-sectional long-short across NYSE stocks, not a single index; a single-index port is untested. Reported 2–3 basis points per half-hour must clear our spread plus commission on NAS100 CFDs. Effect measured 2001–2005; the paper's own 2008 check shrinks it. Searched the paper full text for volume-read detail: volume periodicity is shown, no tradable volume trigger is specified.

## Mechanism
Institutional fund flows and VWAP-style execution algorithms repeat on a daily clock, creating predictable volume and order-imbalance rhythm at the same half-hour. A same-half-hour tick-count elevation shows the rhythm is active today. The other side: liquidity providers absorbing the repeated flow.

## Builder's note
Opinion, labelled: the daily-clock mechanism is plausible and the volume filter is native to our data; the cross-section-to-single-index port is the weak point and needs an explicit robustness demand in the card. No verdict.

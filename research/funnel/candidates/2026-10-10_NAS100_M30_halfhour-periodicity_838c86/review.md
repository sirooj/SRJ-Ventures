---
id: 2026-10-10_NAS100_M30_halfhour-periodicity_838c86
hash: 838c86
status: PARKED
family: halfhour-periodicity
instrument: NAS100
timeframe: M30
session: London, New York
volume_read: tick-count relative volume (same half-hour vs 20-day median)
flags: ""
related_to: ""
sources: https://arxiv.org/abs/1005.3535
created: 2026-10-10
---
Trade NAS100 in the direction of yesterday same half-hour return, filtered by same-half-hour tick-count elevation.
Unverified external claim. Not tested on SRJ data.

Planner verdict (WORKFLOW 04, PARK): Heston, Korajczyk and Sadka is a cross-sectional long-short result on NYSE stocks; the index-level time-series version is a separate claim nobody has tested. The signal is a return and the volume read only gates it, while E-004 needs the volume read to lead. Revisit if a source shows index-level same-half-hour continuation, or a version where the tick-count surge itself carries direction.

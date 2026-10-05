# Study 02: NY open on unusual days, read through volume structure

**Track:** SRJ Edge Research (E-001). **Researcher:** PromptQL bot. **Orchestrator:** sirooj.
**Status:** card LOCKED 2026-10-06, before any study-02 data was looked at. If anything below changes after results are seen, the change gets a new E-entry and the report states it.
**Template:** `.github/ISSUE_TEMPLATE/strategy.md` plus the `srj-edge-study` additions.

## Hypothesis
Study 01 found that the NY cash open moves a lot but, unconditionally, its direction can't be predicted (E-008). The claim here is narrower: on **unusual days**, read through the **prior session's volume structure**, the open's direction becomes predictable for 15–60 minutes.

**Who is on the other side:**
- Overnight inventory that is wrong-footed when the open lands outside yesterday's value.
- Late responsive traders fading a drive that has initiative behind it.
- Breakout traders caught when acceptance fails.

**Why it could persist:** this is the core of Market Profile / auction market theory. Fading or following depends on context, so it resists simple crowding.

**Why it may have decayed:** these ideas are widely published (Dalton, the "80% rule"). That is why sirooj wants a discretionary-style read, and why the out-of-sample test decides.

## Volume read (required, E-004)
Everything is on Dukascopy **bid** ticks; tick count is the volume proxy (D-006).

- **Prior RTH volume profile.** The prior full session, 09:30–16:00 ET.
  - Tick count per bin, with `vp_bin` from `config/instruments.yaml` (NAS100 5.0, US500 1.0).
  - POC, plus a 70% value area (VAH/VAL) grown outward from the POC by the larger adjacent bin.
  - Naked POCs from the last 5 sessions.
- **Relative volume (RVOL).** Tick count from 09:30 to T ÷ the mean of the same window over the prior 20 sessions.
- **Session VWAP**, anchored at 09:30: tick-weighted bid with σ bands (`core/indicators/vwap.py`).
- **Tick-rule CVD**, anchored at 09:30, used for divergence only (`core/indicators/cvd.py`).

**Context only (not volume):** ATR14 is the mean of the prior 14 RTH sessions' high−low. It is used only to normalise returns and drive thresholds, so that NAS100 and US500 are comparable across years.

## Universe, sessions, data
- **Symbols:** NAS100 `USATECHIDXUSD`, US500 `USA500IDXUSD`.
- **Window:** NY session, signals between 09:30 and 11:30 ET.
- **Decision times:** T ∈ {09:45, 10:05} ET.
  - Nothing is evaluated 09:55–10:05; 10:05 is the first bar after the blackout.
- **News:**
  - The 08:30 releases fall before the open.
  - The 10:00 releases are covered by the 09:55–10:05 blackout.
  - FOMC days are flagged and reported separately, because 14:00 falls outside every horizon from T. Step 2 needs a full high-impact calendar.
- **Data:** Dukascopy bid ticks, using only the hours that cover 09:30–16:00 ET (13:00–21:00 UTC), from 2022-11-15 (for the warm-up lookbacks) to 2026-09-30.
  - **In-sample (IS):** 2023-01-01 → 2025-06-30.
  - **Out-of-sample (OOS):** 2025-07-01 → 2026-09-30.
  - The OOS period is not examined until the IS tables are written.
- **Days:**
  - NYSE full trading days only.
  - Half-days are excluded both as signal days and as prior-profile days; "prior" means the last full session.
  - A day is dropped if its minute coverage from 09:30 to 11:30 is below 95%.
- **Point value:** index `point=1000` is provisional (`point_verified: false`). The pilot verifies it tick-exact against `dukascopy-node` before any conversion; if that fails, the study stops.

## Features at decision time T (all causal: only bars closed by T)
| ID | Feature | Buckets (locked) |
|---|---|---|
| F1 | Open (first bid at or after 09:30:00) vs prior value area | above VAH / inside / below VAL |
| F2 | Gap = (open − prior POC) ÷ prior VA width | < −1, −1…−0.25, −0.25…0.25, 0.25…1, > 1 |
| F3 | RVOL(09:30→T) tercile (cut points fixed on IS only) × sign(close_T − open) | 3 × 2 = 6 |
| F4 | VWAP acceptance: the last 5 one-minute closes before T | all above / all below / mixed |
| F5 | CVD divergence at the opening-range (OR = 09:30→T) extreme | bearish at high / bullish at low / none |
| F6 | Opening type (codified Dalton, below) | OD↑, OD↓, OTD↑, OTD↓, ORR↑, ORR↓, OA, unclassified |

**F5 definition.** The OR makes a new high whose session CVD is *lower* than the CVD at the previous OR high, and that previous high was set at least 3 bars earlier. That is a bearish divergence; bullish is the mirror image.

**F6 opening types, codified.** All distances are in ATR14 units. "Top third" and "bottom third" refer to the OR from 09:30 to T.
- **Open-Drive (OD↑):**
  - The low from 09:30 to T is ≥ open − 0.05.
  - close_T is in the top third.
  - close_T ≥ open + 0.15.
  - OD↓ is the mirror image.
- **Open-Test-Drive (OTD↑):**
  - Price first goes ≥ 0.05 below the open and tags a prior reference (VAL, POC, prior low or a naked POC) within 0.03.
  - It then reverses so that close_T is in the top third and above the open.
  - OTD↓ is the mirror image.
- **Open-Rejection-Reverse (ORR↑):**
  - Price first goes ≥ 0.10 below the open **without** tagging a reference.
  - It then reverses through the open so that close_T is in the top third.
  - ORR↓ is the mirror image.
- **Open-Auction (OA):**
  - Price trades ≥ 0.05 on both sides of the open.
  - close_T is in the middle third.
- **Unclassified:** anything else, or any day matching two types. Days are never forced into a type.

**F7, the "80% rule".**
- **Setup:** the open is outside prior value, and price is then *accepted* back inside. Acceptance means two consecutive 5-minute closes inside value, completed by 11:00 ET.
- **Outcome:** price touches the opposite VA edge by 11:30 (the scalp window) and by 16:00.
- **Comparison:** the hit rate against a base rate. The base rate is the touch rate of that same edge for inside-value opens at the same distance, in VA-width deciles.

## Step 1 (this card): does the conditioning separate direction?
- **Measure:** the forward return from the bid close of the bar at T to T + {15, 30, 60} min, in ATR14 units (points are also reported).
- **Report per bucket:**
  - n (days)
  - mean return
  - day-level t-stat
  - hit rate
  - IS and OOS side by side, per symbol
- **Grid:**
  - F1–F6: 28 buckets × 2 decision times × 3 horizons × 2 symbols = **336 tests**.
  - F7: 2 sides × 2 outcome horizons × 2 symbols = **8 tests**.
  - Total **344**. All 344 are reported, not just the winners.
- **Expected false survivors under the null:**
  - About 344 × 0.046 × 0.067 ≈ **1**, using IS |t| ≥ 2, then the same sign in OOS with |t| ≥ 1.5.
  - So that rule alone is not enough.

**Kill criterion (locked).** Step 1 fails unless at least one bucket meets all of the following:
1. n ≥ 40 days in IS **and** in OOS.
2. |t| ≥ 2.0 in IS.
3. The same sign and |t| ≥ 1.5 in OOS.
4. Robustness: the same sign and |t| ≥ 1.0 in OOS **either** on the other index **or** at an adjacent horizon.
5. The IS mean is ≥ 0.05 ATR14, which is roughly the round-trip cost plus stress slippage.

For F7, the hit rate must exceed its base rate by ≥ 10 percentage points, with binomial z ≥ 2 in IS and z ≥ 1.5 in OOS.

If nothing survives, the verdict is null and is reported with the effect size the data rules out.

## Step 2 (only if step 1 survives)
- Codify scalp entries for the surviving buckets, obeying `srj-hard-constraints`:
  - visible SL at entry
  - hold ≥ 3 min
  - SL/TP moves only at bar close
  - flat by 15:55
  - no entries 09:55–10:05 or within ±5 min of high-impact news
- Costs: the real ask−bid spread plus commission, plus stress slippage (NAS100 1.0 pt and US500 0.25 pt per side), plus a separate zero-slippage run.
- Parameters are fitted on IS only. Every configuration tried is counted.

## Step 3
Simulate the trade list against FTMO 2-step and The5ers High Stakes (`docs/propfirm_rules/*.yaml`) from rolling start dates. Use `core/propfirm` once it is merged; until then, state the approximation used.

## Constraint check (`srj-hard-constraints`)
- **Pass:** CFDs, NY session, chart timeframe ≤ 15m, volume-first, visible SL, hold ≥ 3 min, bar-close SL moves, 09:55–10:05 blackout, flat intraday.
- **Borderline:**
  - The news calendar is approximated in step 1 (see "News" above).
  - The best-day cap can only be checked in step 3.

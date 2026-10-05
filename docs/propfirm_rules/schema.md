# Prop-firm rules schema

Typed rulebooks live in this directory (`<firm>_<program>.yaml`) and are loaded
by `core/propfirm/rules.py`. Every value is transcribed from official pages and
flagged **`verify_before_purchase: true`** — re-check against the live pages
before buying any challenge.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `firm`, `program` | string | Identity, e.g. `FTMO`, `2-Step Standard`. |
| `verify_before_purchase` | bool | Must be present. `true` = values below are unverified transcriptions. |
| `phases[]` | list | One entry per challenge phase (see below). |
| `daily_loss` | object | `{pct, pct_of, reference, measured_on, reset_tz, reset_time}`. `pct_of` ∈ `initial` / `reference` (what the allowance is a percentage of); `reference` ∈ `initial` / `reset_balance` / `reset_max_balance_equity` (the level the allowance is subtracted from). `measured_on` ∈ `equity` / `balance`. Unverified rules use the stricter reading. |
| `max_loss` | object | `{pct, pct_of, type, trail_reference, lock_at}`. `type` ∈ `static` / `eod_trailing` / `intraday_trailing`. `trail_reference` ∈ null / `highest_reset_balance` / `highest_equity`. `lock_at` ∈ null / `initial` (floor stops rising at breakeven). |
| `consistency` | object | `{best_day_max_pct_of_positive_days}` — null when the program has no best-day rule. |
| `news` | object | `{evaluation_restricted, funded_window_min}` — whether high-impact-news blackouts apply in evaluation, and the funded window in minutes (±). |
| `trading_limits` | object | `{weekend_holding, max_requests_per_day, min_hold_seconds}` — each nullable when the rulebook is silent. |
| `payout` | object | `{split_pct, split_max_pct, first_after_days, cycle_days}` — `split_pct` is the headline figure, `split_max_pct` the ceiling when advertised as "up to". Nulls where unstated. |
| `fees` | object | `{fee_by_size, fee_refund}` — `fee_by_size` is null until sirooj fills it. |
| `banned_behaviors` | list\|null | Strategies explicitly banned (HFT, hedging, …). |
| `sources[]` | list | `{url, accessed}` — one entry per official page used. |
| `modeled_in_sim` | map | Per-rule flag consumed by the challenge simulator (B2): rule name → bool. `false` means the sim **reports the rule as `unmodeled`, never as passed**. Known keys: `daily_loss`, `max_loss`, `consistency`, `news`, `min_hold_seconds`, `max_requests_per_day`, `weekend_holding`, `payout`, `fees`. |
| `notes[]` | list | Free-text flags (ambiguities, cross-page contradictions, what to verify). |

## Phase entry

`{profit_target_pct, min_trading_days, min_profitable_days, time_limit_days, target_requires_flat}`.
`time_limit_days: null` = no time limit. Percentages are plain numbers (10 = 10%).

## Timezones

`reset_tz` accepts an IANA name (`Europe/Prague`) or a fixed offset (`UTC`, `UTC+3`,
`UTC-5`). `reset_time` is `HH:MM` in that zone.

## Validation (`core/propfirm/rules.py`)

`load_rules(path)` returns frozen dataclasses and raises `ValueError` naming the
file and field on: missing/extra-typed fields, **unknown keys at the top level
or inside any group** (typos become defaults otherwise), unknown enum values,
percentages outside (0, 100], negative day counts, malformed `reset_time`,
unresolvable `reset_tz`, bad `news.funded_window_min` / `trading_limits` types,
empty `sources`, unknown `modeled_in_sim` keys, or a missing
`verify_before_purchase` flag. Absent `modeled_in_sim` keys default to `false`.

Floors are pinned by `daily_floor(rules, initial, reference_value)` and
`max_floor(rules, initial, trail_value)` — pure functions; the running-maximum
ratchet is the simulator's job.

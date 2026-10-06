# Study 02, step 1 results

Run 2026-10-06 by the RESEARCHER (session 3) on Dukascopy bid ticks, 13–20 UTC weekday hours,
2022-11-15 → 2026-09-30. NAS100 8096/8096 hours; US500 8093/8096 (3 hours missing after two
fill runs, because of feed throttling; affected days fall to the coverage rule). Card: `CARD.md`
(E-010). Codification: E-012. Verdict: E-013.

## Samples

| symbol | sample | days | dropped: coverage | dropped: prior incomplete |
|---|---|---|---|---|
| NAS100 | IS 2023-01-01 → 2025-06-30 | 615 | 3 | 1 |
| US500 | IS | 612 | 3 | 4 |
| NAS100 | OOS 2025-07-01 → 2026-09-30 | 307 | 5 | 0 |
| US500 | OOS | 310 | 2 | 0 |

The IS tables were written and hashed before OOS ran; the hashes were re-checked after OOS:

```
f08be7d14c0d1272ba8998dc61170205ea69ba8f078420be81d4043170dc6dc2  /workspace/results/study02/cuts_IS.json
01483063312c0ef6e31d3d2c8cc400e344a6dc94004e5b4bb08bbf88a30af3ff  /workspace/results/study02/days_IS.parquet
6943a39aca87d7adcd146043611146b205a5ba60c37b18066c56d6c119a7cabe  /workspace/results/study02/f7_days_IS.parquet
2f77c2ff743432639d5e1e06ec556848b9c1a0e8d559deea9d61ad085451eaf2  /workspace/results/study02/step1_IS.csv
26068b6bfe2daec80325b5a0cc17c236ac66d0daf8368503fdef4aa993502ecf  /workspace/results/study02/step1_f7_IS.csv
f08be7d14c0d1272ba8998dc61170205ea69ba8f078420be81d4043170dc6dc2  /workspace/results/study02/cuts_IS.json
```

## Verdict

- **F1–F6 (336 tests): null.** 273 buckets had n ≥ 40 in IS; 16 reached
  |t| ≥ 2 in IS; 1 of those kept the same sign with |t| ≥ 1.5 in OOS; survivors:
  0. The largest IS |mean| among n ≥ 40 buckets was 0.093 ATR14. Among the
  IS-significant buckets, OOS rules out an effect in the IS direction larger than
  0.436 ATR14 (upper 95% bound, worst case).
- **F7 (8 tests): opening above the prior value area survives** on both indices at both outcome
  horizons (diff ≥ 10 pp and z ≥ 2 IS; diff ≥ 10 pp and z ≥ 1.5 OOS). Opening below fails: the
  OOS sign is negative on both indices.
- The 4 surviving F7 tests are strongly correlated (the same days and two closely related
  indices; 11:30 is nested in 16:00). Treat them as **one** finding, not four.
- A higher touch rate is not yet a tradable edge. Step 2 must show it after costs, with a
  visible SL and the hold and blackout rules.

## F7: the 80% rule

| symbol | side | outcome | n_setups | hit_rate | base_rate | diff_pp | z | n_setups_oos | hit_rate_oos | base_rate_oos | diff_pp_oos | z_oos | survives |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NAS100 | from_above | hit_1130 | 69 | 0.49 | 0.35 | 14.68 | 2.73 | 47 | 0.57 | 0.46 | 11.31 | 1.76 | True |
| NAS100 | from_above | hit_1600 | 69 | 0.67 | 0.45 | 21.66 | 3.75 | 47 | 0.7 | 0.56 | 13.75 | 2.1 | True |
| NAS100 | from_below | hit_1130 | 70 | 0.47 | 0.5 | -2.48 | -0.44 | 38 | 0.39 | 0.51 | -11.32 | -1.5 | False |
| NAS100 | from_below | hit_1600 | 70 | 0.66 | 0.6 | 5.58 | 1.0 | 38 | 0.58 | 0.62 | -4.01 | -0.53 | False |
| US500 | from_above | hit_1130 | 67 | 0.45 | 0.3 | 15.27 | 3.12 | 45 | 0.56 | 0.38 | 17.7 | 2.58 | True |
| US500 | from_above | hit_1600 | 67 | 0.66 | 0.4 | 25.92 | 5.01 | 45 | 0.73 | 0.49 | 23.84 | 3.34 | True |
| US500 | from_below | hit_1130 | 55 | 0.27 | 0.38 | -10.86 | -1.76 | 202 | 0.22 | 0.42 | -19.92 | -1.85 | False |
| US500 | from_below | hit_1600 | 55 | 0.56 | 0.53 | 3.3 | 0.52 | 202 | 0.39 | 0.58 | -18.81 | -1.65 | False |

`hit_rate`: share of accepted setups that touch the opposite value-area edge after acceptance.
`base_rate`: touch rate of the same edge from 09:30 on inside-value opens, matched by distance
decile (conservative for the rule).

## F1–F6 buckets that passed IS |t| ≥ 2

| symbol | T | horizon | feature | bucket | n | mean_atr | t | n_oos | mean_atr_oos | t_oos | c3_oos_t | c4_robust | c5_size |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NAS100 | 10:05 | 30 | F2 | -1..-0.25 | 119 | 0.039 | 2.05 | 46 | -0.064 | -1.539 | False | False | False |
| NAS100 | 10:05 | 30 | F4 | all_above | 256 | 0.035 | 2.572 | 131 | 0.019 | 1.017 | False | False | False |
| NAS100 | 10:05 | 60 | F4 | all_above | 256 | 0.041 | 2.106 | 131 | -0.002 | -0.071 | False | True | False |
| NAS100 | 10:05 | 15 | F6 | OA | 108 | 0.035 | 2.429 | 55 | 0.013 | 0.562 | False | True | False |
| NAS100 | 09:45 | 30 | F6 | ORR_dn | 22 | 0.157 | 2.77 | 10 | 0.113 | 0.937 | False | True | True |
| NAS100 | 09:45 | 60 | F6 | ORR_dn | 22 | 0.167 | 2.132 | 10 | 0.182 | 1.404 | False | False | True |
| NAS100 | 09:45 | 15 | F6 | OTD_dn | 18 | 0.066 | 2.236 | 14 | 0.123 | 2.342 | True | False | True |
| NAS100 | 09:45 | 60 | F6 | OTD_dn | 18 | 0.13 | 2.172 | 14 | 0.079 | 0.523 | False | False | True |
| NAS100 | 10:05 | 60 | F6 | OTD_dn | 24 | 0.115 | 2.019 | 16 | -0.081 | -0.932 | False | False | True |
| US500 | 10:05 | 15 | F2 | -0.25..0.25 | 104 | 0.033 | 2.21 | 50 | 0.021 | 0.962 | False | False | False |
| US500 | 09:45 | 30 | F5 | bear_at_high | 24 | -0.206 | -3.291 | 16 | 0.112 | 1.35 | False | False | True |
| US500 | 09:45 | 15 | F6 | OTD_dn | 21 | 0.055 | 2.23 | 16 | -0.005 | -0.086 | False | True | True |
| US500 | 09:45 | 30 | F6 | OTD_dn | 21 | 0.079 | 2.014 | 16 | -0.064 | -0.708 | False | False | True |
| US500 | 09:45 | 60 | F6 | OTD_dn | 21 | 0.098 | 2.575 | 16 | -0.026 | -0.191 | False | False | True |
| US500 | 10:05 | 30 | F6 | OTD_up | 29 | 0.094 | 2.914 | 13 | 0.002 | 0.03 | False | True | True |
| US500 | 10:05 | 60 | F6 | OTD_up | 29 | 0.095 | 2.507 | 13 | 0.001 | 0.014 | False | True | True |

All 336 rows are in `results/step1_grid.csv`, and all 8 F7 rows in `results/step1_f7.csv`
(rounded to 3 dp; the full-precision tables are regenerated by `step1.py`).

## Known limitations

- F6 leaves about 46% of days `unclassified`. It was not re-codified after IS was seen (E-012).
- The NYSE holiday, half-day and FOMC dates are hard-coded and not yet verified.
- The news filter is the card's step-1 approximation.

## Reproduce

```
export SRJ_DATA=<data dir>
S=research/edge/studies/02_open_unusual_days/scripts
uv run python $S/pilot_download.py USATECHIDXUSD,USA500IDXUSD 2022-11-15 2026-09-30 4
uv run python $S/pilot_download.py USA500IDXUSD 2022-11-15 2026-09-30 1   # fill
uv run python $S/build_bars.py USATECHIDXUSD 2022-11 2026-09
uv run python $S/build_bars.py USA500IDXUSD 2022-11 2026-09
uv run python $S/step1.py --sample IS
uv run python $S/step1.py --sample OOS
```

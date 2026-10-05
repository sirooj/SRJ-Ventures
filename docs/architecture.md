# Architecture — Phase 0 data + indicators

## Pipeline

```
Dukascopy feed (.bi5, hourly, UTC)          sirooj's CSV archives (D:\download)
        │                                              │
        ▼                                              ▼
core/data/dukascopy.py                core/data/import_mt5_csv.py
  download (resume-safe, ≤6 conn.,          (converts existing 2025-12→2026-09
   retries + backoff, failures CSV)         FX archives into the same layout)
        │                                              │
        └──────────────┬───────────────────────────────┘
                       ▼
ticks/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
  ts (UTC ms) | bid | ask | bid_vol | ask_vol | spread
                       │
                       ▼
core/data/bars.py → 1m bid-side bars (+ tick_count, vols, spread stats,
                      delta_tick, delta_tick_carry) → resample 5m/15m/1h
                       │
                       ▼
core/data/qa.py → results/data_qa/report.md
  (coverage, gaps > 5 min in session, spikes, spread by hour, DST checks)
                       │
                       ▼
core/indicators/ (all causal, no-lookahead tested)
  vwap.py            session VWAP ±1/2/3σ (tick-count-weighted, bid) + anchored
  volume_profile.py  per-session + composite POC / VAH-VAL 70% / HVN-LVN / naked POC
  cvd.py             tick-rule CVD, session reset + rolling variants
                       │
                       ▼
research/cards/ + strategies/ + core/backtest/ + core/propfirm/  (Phase ≥ 1)
```

## Key decisions

- **Bid-side primary.** OHLC, volume proxy (`tick_count`), VWAP, profiles, and
  CVD all derive from the bid. Ask exists only via `spread` / cost modelling.
- **UTC everywhere internally.** Session logic uses `zoneinfo` so DST needs no
  manual offsets. QA explicitly checks DST transitions.
- **Ticks are the grain.** Bars are derived and resampled, never edited in place;
  `delta_tick_carry` is computed at tick level, then summed per bar.
- **Point values are data, not assumptions.** `.bi5` int prices are divided by a
  per-instrument `point` from `config/instruments.yaml`, verified empirically.
- **Small repo, big data.** The repo holds code/specs/small results; all ticks
  and bars live under `$SRJ_DATA` on D: (see `core/data/paths.py`).

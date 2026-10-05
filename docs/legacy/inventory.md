# Legacy MQL5 inventory — PUBLIC summary

> Confidentiality (D-012, D-021): the repo is public, so this page holds module
> names + one-line purposes only — no source, no parameter values. The full
> inventory lives off-repo at `D:\SRJ Venture\private\legacy_inventory.md`.

Baseline (per sirooj): **SRJ Flow Nexus EA** (`Experts/SRJ_FlowNexus_EA.mq5`,
"Phase 2 EA - Orchestrator and Trade Execution", v1.00) — places orders, not
production-ready. Instruments EURUSD/GBPUSD/USDJPY (GC/NQ later).

## Dependency graph

```
SRJ_FlowNexus_EA (orders: YES — sole order sender)
 ├─ iCustom → SRJ_POI_Marker      (POI detection + retest tracking)
 ├─ iCustom → SRJ_CQD_TickBased_MT5 (cumulative delta census w/ carry)
 ├─ iCustom → SRJ_FlowLogic       (market-structure engine, HTF lookback)
 └─ Include/SRJ/*.mqh (15 libs): Types, State, BiasEngine, HTFEngine,
    OrderblockMgr, ImbalanceMgr, Fractals, Sessions, Draw, Text, Panels,
    Alerts, SeedFormat, TickCore, HandFixture
Tick tooling (no orders): SRJ_TickPumper_EA, SRJ_BarsFromTicks,
SRJ_RatesRebuild, SRJ_TickBridge, SRJ_TickAudit, SRJ_TickFlagAudit,
SRJ_TickPurge, SRJ_CVD_TickBased_MT5, SRJ_CVD_TickBidAsk_MT5
```

## EA input names (no values)

`InpPoiMarkerName, InpCqdName, InpFlowLogicName, InpRiskPercent, InpMagicBase,`
`InpMode, InpAlertPopup/Push/HeadsUp/StandDown, InpPoi_UseSeed, InpPoi_BinPips,`
`InpPoi_WeightMode, InpCqd_NoReset, InpCqd_MaxCarryBars, InpCqd_MaxBackfillDays,`
`InpFL_HtfLookbackBars, InpMinBarsRequired, InpMinRewardRisk, InpDebugLog,`
`InpSelL1–L3, InpAdoptExt1`

## Order-placement surface (structural, derived from source)

- Entry: elected setup → per-bar memo → fire path (POI retest + CQD census +
  flow/HTF confluence + min reward:risk + demo-guard).
- Exits: origin/anchor-line break on body close; TP-touch legs; HTF-flip leg
  currently experiment-disabled.
- Protection: SL/TP + trailing/breakeven; news/day/week-flat (Fri 17:00 ET).
- Sessions/timeframes (derived): M5 execution chart; M15/H1/H4 structure;
  US-Eastern marks (16:55 ET daily close, Friday 17:00 ET flat); news blackout;
  server/GMT clock reconciliation.

## Track record: what exists (existence only)

- Strategy Tester caches: **yes** (`Tester/cache/SRJ_FlowNexus_EA.EURUSD.M5.*`,
  Jun→Sep 2026) plus daily tester logs.
- Broker statement: **not found** in the terminal folders.

## Python mapping (existing modules)

POI POC/VA → `core/indicators/volume_profile.py`; CQD carry →
`core/indicators/cvd.py`; ET sessions → `vwap.session_id`; tick-rule →
`core/data/bars.py`. FlowLogic/HTF/order-block/imbalance/bias have no Python
equivalent yet (Phase 2+).

## Open questions for sirooj (`question`)

1. Exact live sessions/timeframes beyond derived M5 + ET marks.
2. Any broker statement outside the terminal folders?
3. Which Flow Nexus revision (many `.preB*` variants) is the port baseline?

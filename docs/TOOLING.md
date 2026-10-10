# TOOLING — reuse-before-build registry (D-022, D-024)

> Check this file before building any component. Every relay task that builds something carries an `OSS check:` line naming the rows it considered. A tool becomes **adopted** only after the CODER shows it reproduces a known in-house result (the adoption gate, below). Stars and licenses were checked on 2026-10-10; re-check before adopting.

Verdicts: **adopted** · **spike** (under test against the gate) · **oracle** (cross-check only) · **reference** (read, don't run) · **earmarked** (later phase) · **optional** (allowed, not required) · **rejected**.

## Licenses
- MIT, BSD, Apache-2.0, Unlicense: use freely; keep the notice if vendored.
- LGPL-3.0: use as a library; don't copy its source into the repo.
- GPL, AGPL: run locally as a separate tool only. Never vendor or import its code into `core/`.
- Commons Clause (vectorbt): internal research is fine; we never sell or host it.

## Simulation, backtest, execution
| Component | Today | Option | License | Verdict | Notes |
|---|---|---|---|---|---|
| Challenge simulator | in-house `core/propfirm/` | LuxAlgo `prop-firm-sim` | MIT | oracle (D-022) | OSS doesn't mark equity at the minute-level adverse extreme |
| Backtest: screening | study scripts | `polakowo/vectorbt` (9.3k★) | Apache-2.0 + Commons Clause | spike (W3) | vectorised, numpy-based |
| Backtest: quote-tick validation | none | `nautechsystems/nautilus_trader` (29.8k★) | LGPL-3.0 | spike (W3) | quote-tick native, realistic fills; for survivors only |
| Backtest: other | — | `kernc/backtesting.py` | AGPL-3.0 | rejected | bar-only, AGPL |
| Backtest: other | — | `mementum/backtrader` | GPL-3.0 | rejected | no push since 2024-08 |
| Backtest: other | — | `nkaz001/hftbacktest` | MIT | rejected | HFT-oriented; our constraints forbid HFT |
| MT5 tester automation | — | `PHUICMT/mcp-mt5` | MIT | adopted (D-022) | #9 / PR #12 |
| Live risk guard | — | `2023ai/ftmo-risk-control` | MIT | earmarked, Phase 5 (D-022) | `execution-critical` |
| Parameter search | locked grids | `optuna/optuna` | MIT | rejected for now | later only inside a locked IS grid, every trial in `TRIALS.csv`, by a new E-entry |
| Overfitting stats | none | `esvhd/pypbo` | AGPL-3.0 | reference | PBO/CSCV, deflated Sharpe; run locally once `TRIALS.csv` has data |
| Tear-sheets | matplotlib | `ranaroussi/quantstats` | Apache-2.0 | optional | supplement only; fitness stays the challenge sim |
| Financial ML | — | `hudson-and-thames/mlfinlab` | commercial | rejected | no longer open source; last push 2023 |

## Data
| Component | Today | Option | License | Verdict | Notes |
|---|---|---|---|---|---|
| Dukascopy download | `core/data/dukascopy.py` | `Leo4815162342/dukascopy-node` (923★) | MIT | oracle / fallback | cross-check for #2; don't replace working code |
| Dukascopy download | — | `giuse88/duka` | MIT | rejected | stale since 2019 |
| Tick and bar storage | polars + parquet | `pola-rs/polars` | MIT | adopted | — |
| Ad-hoc queries | — | `duckdb/duckdb` | MIT | optional | SQL over the parquet lake, no new build |
| Data validation | `core/data/qa.py` | `pandera-dev/pandera` | MIT | optional | polars schemas for ticks and bars |
| Trial tracking | `research/edge/TRIALS.csv` | `mlflow/mlflow` | Apache-2.0 | rejected for now | revisit if the CSV gets unwieldy |

## Research and web (skill `srj-research-web`)
| Component | Today | Option | License | Verdict | Notes |
|---|---|---|---|---|---|
| Papers | — | `lukasschwab/arxiv.py` | MIT | adopted, pending W2 | rung 0 |
| Reddit | — | `praw-dev/praw` | BSD-2 | optional, pending W2 | needs free Reddit app keys |
| YouTube | — | `jdepoix/youtube-transcript-api` + `yt-dlp/yt-dlp` | MIT / Unlicense | adopted, pending W2 | rung 0 |
| GitHub | `gh` CLI | — | MIT | adopted | rung 0 |
| Static article text | — | `adbar/trafilatura` (6.9k★) | Apache-2.0 | adopted, pending W2 | rung 1 |
| JS-rendered pages | — | `unclecode/crawl4ai` (85k★) | Apache-2.0 | adopted, pending W2 | rung 2 |
| Browser interaction | — | `browser-use/browser-use` (117k★) | MIT | adopted, pending W2 | rung 3, last resort |
| Web search | — | DeepAPI `/v1/search/web` | paid SaaS | adopted, capped at $3/week (D-024) | key kept outside the repo |
| Web search (self-hosted) | — | `searxng/searxng` | AGPL-3.0 | rejected for now | needs Docker; revisit if DeepAPI is dropped |
| Hosted scrapers | — | `mendableai/firecrawl`, `jina-ai/reader` | AGPL / hosted | rejected | hosted dependency |
| Agent-skill patterns | — | `davidondrej/skills` | no repo license found | reference | SRJ skills are written fresh, informed by it |

## Adoption gate (D-024)
1. Pick a known in-house result: a merged study result, a report table, or a test fixture.
2. Fix the tolerances in the task **before** running.
3. The CODER runs the tool against it and reports the comparison in the CODER report.
4. Inside tolerance → the PLANNER sets the verdict to **adopted** here in the next relay. Outside → **rejected** or a second spike, with the reason.

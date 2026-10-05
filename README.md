# SRJ Ventures

Quant research loop for **intraday CFD strategies designed to pass prop-firm
challenges**. The orchestrator (cloud PromptQL bot) plans research; the local
CODER agent implements it. The only channel between them is this repo
(see [AGENTS.md](AGENTS.md)).

## Layout

```
SRJ-Ventures/
├─ AGENTS.md               # relay protocol + conventions (read first)
├─ config/instruments.yaml # symbol universe, Dukascopy symbols, point values, sessions
├─ core/
│  ├─ data/      # Dukascopy loader, bars, QA  (paths via $SRJ_DATA)
│  ├─ indicators/# vwap, volume_profile, cvd
│  ├─ backtest/  # (Phase ≥1)
│  └─ propfirm/  # (Phase ≥1)
├─ strategies/   # (Phase 1+ — Phase 0 ports nothing)
├─ research/cards/
├─ docs/ (architecture, propfirm_rules/)
├─ results/<id>/ # small committed outputs (< 1 MB)
└─ tests/
```

Data lives **outside** the repo at `$SRJ_DATA` (`D:\SRJ Venture\data`):

```
data/
├─ dukascopy/raw/<SYM>/<YYYY>/<MM0>/<DD>/<HH>h_ticks.bi5
├─ ticks/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
└─ bars/symbol=<SYM>/tf=<1m|5m|15m|1h>/year=<YYYY>/part.parquet
```

## Setup (Windows, everything on D:)

```powershell
# 1. Persist env (then restart the shell)
[Environment]::SetEnvironmentVariable('SRJ_ROOT', 'D:\SRJ Venture', 'User')
[Environment]::SetEnvironmentVariable('SRJ_DATA', 'D:\SRJ Venture\data', 'User')
[Environment]::SetEnvironmentVariable('UV_CACHE_DIR', 'D:\SRJ Venture\.cache\uv', 'User')
[Environment]::SetEnvironmentVariable('UV_PYTHON_INSTALL_DIR', 'D:\SRJ Venture\.python', 'User')
[Environment]::SetEnvironmentVariable('PIP_CACHE_DIR', 'D:\SRJ Venture\.cache\pip', 'User')

# 2. Python 3.12 via uv (installs under D:\SRJ Venture\.python, not C:)
uv python install 3.12
uv sync

# 3. Checks
uv run pytest
uv run ruff check .
```

`gh` auth (needed to pick up Issues / open PRs): `gh auth login`.

## Workflows

```powershell
# Download Dukascopy ticks (pilot: 5 symbols, 2023-01-01 → today)
uv run python -m core.data.dukascopy download --symbols EURUSD,GBPUSD,USDJPY,USA500IDXUSD,USATECHIDXUSD `
  --start 2023-01-01 --end 2026-10-05

# If your ISP hijacks DNS (e.g. Telkomsel `internetbaik` blocks
# datafeed.dukascopy.com), resolve via DoH — TLS verification stays on:
uv run python -m core.data.dukascopy download --resolve auto --symbols EURUSD `
  --start 2023-01-01 --end 2023-02-01

# Monthly parquet conversion is part of download; or re-run it standalone:
uv run python -m core.data.dukascopy convert --symbol EURUSD --year 2023 --month 1

# 1m bars + resample
uv run python -m core.data.bars --symbol EURUSD --year 2023

# Data QA report → results/data_qa/report.md
uv run python -m core.data.qa --symbols EURUSD,GBPUSD,USDJPY,USA500IDXUSD,USATECHIDXUSD --years 2026
```

## Conventions (summary)

Bid-side data · UTC internally, `zoneinfo` sessions · no lookahead (tested) ·
never commit data or secrets. Full version in [AGENTS.md](AGENTS.md).

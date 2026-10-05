# SRJ Ventures operator RUNBOOK (for sirooj)

Plain commands only. Run these in Windows PowerShell. Anything not listed
here: ask the CODER before running it.

## 1. Safe vs unsafe

SAFE (read-only, run anytime):
`gh pr list`, `gh issue list --label ready-for-code`,
`uv run pytest` (inside `D:\SRJ Venture\SRJ-Ventures`),
checking the files below.

UNSAFE (never run without asking):
- deleting anything under `D:\SRJ Venture\data\`
- `Stop-Process` on `uv`/`python` — killing only the parent orphans workers
  (Oct 2026: two downloads raced for 20 min this way)
- anything that writes to `C:` (it's nearly full)
- merging a PR the planner hasn't approved

## 2. Check the tick download

```powershell
Get-Content 'D:\SRJ Venture\data\dukascopy\logs\pilot_20261005.log' | Select-Object -Last 2
(Get-ChildItem 'D:\SRJ Venture\data\dukascopy\raw' -Recurse -Filter '*.bi5' | Measure-Object).Count
(Get-ChildItem 'D:\SRJ Venture\data\dukascopy\raw' -Recurse -Filter '*.empty' | Measure-Object).Count
Get-Content 'D:\SRJ Venture\data\dukascopy\failures_*.csv'  # only exists if hours failed
Get-PSDrive D  # FreeGB column: pilot needs ~10 GB total
```

Healthy = counts grow over hours, one `uv` + two `python` processes at most
(`Get-Process uv,python`). Weekend hours land as 0-byte `.empty` markers —
that is normal, not an error.

## 3. Stop and restart a download cleanly

```powershell
Get-Process -Name 'uv','python' | Stop-Process -Force  # whole tree, not one PID
```

Then tell the CODER to relaunch it. Restarts are safe: finished hours are
skipped, `.empty` markers skip weekends, and `.bi5` files are written
atomically (a kill can't corrupt them).

## 4. VPN and the feed

Without VPN, the ISP hijacks the feed's DNS and downloads fail TLS checks.
Two rules: turn VPN **on** for any Dukascopy download; the downloader's
`--resolve auto` (DoH) is the default either way and keeps TLS verification on.

## 5. Start a new PromptQL session (one line)

```
Resume SRJ Ventures. Read https://github.com/sirooj/SRJ-Ventures/blob/main/docs/STATE.md (+ DECISIONS.md, WIKI_SEED.md), then continue from "Next actions".
```

## 6. GitHub 403 from the planner / C: full

- Planner 403 on write: nothing to fix on your side unless you want to
  install the PromptQL GitHub App (then tell the planner). The CODER relays
  everything meanwhile.
- C: nearly full blocks MT5 tester runs (5 GB gate): check with
  `Get-PSDrive C`; biggest eaters so far were the agent session store
  (`C:\Users\winar\.local\share\opencode\opencode.db`) and MT5
  `MQL5/logs` + `Tester/logs`. Don't delete blindly — ask first.

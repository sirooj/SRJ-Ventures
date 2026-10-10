# SRJ Ventures RUNBOOK (CODER machine)

Environment: Windows, everything on D: (C: is nearly full). PowerShell.

> MERGE NOTE (W1, #20): `docs/RUNBOOK.md` §2 (research-web setup + env vars)
> lives in PR #28 (W2). Rebase onto `main` after #28 merges and combine the
> files; this file carries the funnel section only.

## 1. Environment variables

Same block as PR #28 §1 (`SRJ_DATA`, `UV_*`, `PLAYWRIGHT_BROWSERS_PATH`,
`CRAWL4_AI_BASE_DIRECTORY` — all on D:). Secrets in
`D:\SRJ Venture\.secrets\`, never logged.

## 3. Idea Funnel runs (W1, #20)

Skill: `.opencode/skills/srj-idea-funnel/SKILL.md`. Manual: `run funnel`.
Validator: `uv run python -m core.funnel.validate <candidate_dir>`.

Nightly Task Scheduler command (OpenCode non-interactive mode — verified
`opencode run [message..]` exists). DISABLED until the planner has reviewed
the first queue (`research/funnel/queue.md`):

```powershell
$act = New-ScheduledTaskAction -Execute 'opencode' `
  -Argument 'run "run funnel"' `
  -WorkingDirectory 'D:\SRJ Venture\SRJ-Ventures'
$tr = New-ScheduledTaskTrigger -Daily -At 02:00
Register-ScheduledTask -TaskName 'SRJ-Funnel-Nightly' -Action $act -Trigger $tr
Disable-ScheduledTask -TaskName 'SRJ-Funnel-Nightly'
```

First run (2026-10-10, by hand, rungs 0–1, no DeepAPI key):
`2026-10-10 20:59 | funnel | scanned=15 queued=3 rejected=12 redrafts=0 deepapi_usd=0.00`.
Queued: halfhour-periodicity (NAS100 M30), vvg-filter (NAS100 D1,
`related_to: study-02`), hmm-momentum (US500 M15, `volume_read: missing`).

## 4. Vault + Telegram export (W5, #26 — to be filled by W5)

_TBD in W5._

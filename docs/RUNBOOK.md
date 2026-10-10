# SRJ Ventures RUNBOOK (CODER machine)

Environment: Windows, everything on D: (C: is nearly full). PowerShell.

## 1. Environment variables

Set these before any work (add to the PowerShell profile for persistence):

```powershell
$env:SRJ_ROOT = 'D:\SRJ Venture'
$env:SRJ_DATA = 'D:\SRJ Venture\data'
$env:UV_CACHE_DIR = 'D:\SRJ Venture\.cache\uv'
$env:UV_PYTHON_INSTALL_DIR = 'D:\SRJ Venture\.python'
$env:PIP_CACHE_DIR = 'D:\SRJ Venture\.cache\pip'
$env:PLAYWRIGHT_BROWSERS_PATH = 'D:\SRJ Venture\.cache\ms-playwright'
$env:CRAWL4_AI_BASE_DIRECTORY = 'D:\SRJ Venture\.cache\crawl4ai'
```

Secrets live in `D:\SRJ Venture\.secrets\` (outside git, never logged):
no DeepAPI key yet (`deepapi_unavailable`); Reddit app keys optional (rung 0);
Telegram API id for W5 (`telegram.env`).

## 2. Research-web ladder (W2, #21)

Skill: `.opencode/skills/srj-research-web/SKILL.md`.

```powershell
uv sync --group research          # optional ladder; core pytest never needs it
uv run playwright install chromium  # browsers land in $env:PLAYWRIGHT_BROWSERS_PATH
```

Smoke test (2026-10-10, all caches on D:, all saves under
`D:\SRJ Venture\private\funnel\sources\`):

| Rung | Tool (version) | Result | Time | Note |
|---|---|---|---|---|
| 0 | arxiv 4.0.1 | OK | 2.6s | q-fin.TR paper metadata + abstract, 2,104 chars |
| 0 | yt-dlp 2026.8.19 + youtube-transcript-api 1.2.4 | OK | 9.4s + 4.2s | ytsearch found video, transcript 24,063 chars |
| 1 | trafilatura 2.3.1 | OK (with one stated failure) | 1.9s | arXiv abs page 3,344 chars; SSRN abstract page returned 0 chars (bot-block suspected), recorded as URL-specific failure |
| 2 | crawl4ai 0.9.4 | OK | 8.9s | tradingstats.net rendered to 13,400 chars |
| 3 | browser-use 0.13.11 | OK (partial) | 5.4s | opened arxiv.org, extracted title via `navigate_to` + `get_current_page_title`; the Agent/LLM layer is untested (no LLM key) |
| — | praw 7.8.2 | installed, not smoke-tested | — | needs free Reddit app keys in `.secrets\` |
| search | DeepAPI `/v1/search/web` | `deepapi_unavailable` | — | no key in `.secrets\`; $3/week cap (D-024) applies once set |

Disk used: `ms-playwright` ~740 MB (chromium + headless shell + ffmpeg);
`crawl4ai` cache ~17 KB; saved smoke sources ~48 KB; 158 packages in the
`research` group (note: resolver moved anyio 4.15.1 → 4.12.1;
`uv run pytest` still 41 passed).

## 3. Idea Funnel runs (W1, #20 — to be filled by W1)

Nightly Task Scheduler command (OpenCode non-interactive mode), disabled until
the planner has reviewed the first queue: _TBD in W1_.

## 4. Vault + Telegram export (W5, #26 — to be filled by W5)

_TBD in W5._

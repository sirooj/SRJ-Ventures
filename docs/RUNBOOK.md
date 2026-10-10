# SRJ Ventures RUNBOOK (CODER machine)

Environment: Windows, everything on D: (C: is nearly full). PowerShell.

> MERGE NOTE (W5, #26): `docs/RUNBOOK.md` §§1–2 live in PR #28 (W2) and §3 in
> PR #30 (W1). Rebase onto `main` after they merge and combine; this file
> carries §4 only.

## 4. Vault + Telegram export (W5, #26)

Skill note: the funnel reads `D:\SRJ Venture\private\vault\inbox\**` as rung
`vault` (see `research/funnel/SOURCES.md` § Vault inbox).

- Vault root (outside git): `D:\SRJ Venture\private\vault\` with
  `inbox\web|x|youtube|discord|telegram|ea_code`, `papers\`,
  `telegram_allowlist.txt`. Guard: `uv run python tools/tg_export.py check`
  fails if any vault path is git-tracked (third-party EA code is spec-only).
- Exporter: `uv run python tools/tg_export.py export` (Telethon on sirooj's
  own account, read-only: history reads only, never posts/joins; sleeps on
  FLOOD_WAIT; incremental per-channel cursor in `.tg_state.json`).
- Setup (sirooj, when W5 starts): create a Telegram API id at
  my.telegram.org, save `api_id`/`api_hash` in
  `D:\SRJ Venture\.secrets\telegram.env` (`KEY=VALUE` lines), and list the
  joined channels to allow-list in
  `D:\SRJ Venture\private\vault\telegram_allowlist.txt` (one per line).
- Discord: manual capture only (no user-token automation; bot token only
  where the server admin invited the bot). Out of scope for automation (D-025).

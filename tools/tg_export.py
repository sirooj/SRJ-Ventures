"""Telegram exporter → Obsidian vault inbox (issue #26, W5; D-025).

Read-only export of allow-listed channels sirooj has joined, using his own
account (Telethon). One markdown note per day per channel with front-matter.
Incremental via a per-channel last-message-id cursor. Sleeps on FLOOD_WAIT.
Never posts, never joins. Discord automation is out of scope (D-025).

Usage:
  uv run python tools/tg_export.py check    # fail if any vault path is git-tracked
  uv run python tools/tg_export.py export   # needs .secrets\\telegram.env + allowlist
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import timezone
from pathlib import Path

SRJ_ROOT = Path(os.environ.get("SRJ_ROOT", r"D:\SRJ Venture"))
VAULT = SRJ_ROOT / "private" / "vault"
INBOX_TG = VAULT / "inbox" / "telegram"
ALLOWLIST = VAULT / "telegram_allowlist.txt"
STATE = VAULT / ".tg_state.json"
SECRETS_ENV = SRJ_ROOT / ".secrets" / "telegram.env"

REQUIRED_FRONTMATTER = ["source", "url", "author", "date", "tier",
                        "captured_by", "licence"]


# --------------------------------------------------------------------------
# Pure helpers (unit-tested, no network)
# --------------------------------------------------------------------------
def load_dotenv(path: Path) -> dict:
    """Parse KEY=VALUE lines (ignores blanks and # comments)."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("\"'")
    return out


def load_allowlist(path: Path) -> list[str]:
    """Channel usernames/ids, one per line; # comments and blanks skipped."""
    if not path.is_file():
        return []
    return [line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")]


def load_state(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def day_note_path(channel: str, day: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in channel)
    return INBOX_TG / safe / f"{day}.md"


def render_note(channel: str, day: str, url: str,
                messages: list[dict]) -> str:
    """One note per day per channel, with the funnel front-matter (W5)."""
    head = ["---", "source: telegram", f"url: {url}", f"author: {channel}",
            f"date: {day}", "tier: C", "captured_by: tg_export",
            "licence: unknown", "---", ""]
    body = [f"# {channel} — {day}", ""]
    for m in messages:
        body += [f"## {m['ts']}", "", m["text"], ""]
    return "\n".join(head + body)


def parse_frontmatter(note: str) -> dict:
    """Inverse of render_note header (for tests and the funnel)."""
    if not note.startswith("---\n"):
        return {}
    raw, _, _ = note[4:].partition("\n---\n")
    out: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def check_vault_not_tracked(repo_root: Path, vault: Path,
                            runner=None) -> list[str]:
    """Fail (non-empty list) if any vault path is tracked by git.

    The vault must live outside the repo work tree and never appear in
    `git ls-files`. Third-party EA/indicator code is spec-only: this check
    keeps it out of git.
    """
    violations: list[str] = []
    try:
        vault.resolve().relative_to(repo_root.resolve())
        violations.append(f"vault inside repo work tree: {vault}")
    except ValueError:
        pass
    run = runner or (lambda *a, **k: subprocess.run(*a, **k))
    try:
        r = run(["git", "-C", str(repo_root), "ls-files"],
                capture_output=True, text=True, timeout=60)
        tracked = r.stdout.splitlines() if r.returncode == 0 else []
    except Exception as e:  # noqa: BLE001 — git missing counts as uncheckable
        return [f"git ls-files failed: {e!r}"]
    vp = str(vault.resolve())
    for t in tracked:
        if t == "private/vault" or t.startswith("private/vault/") or vp in t:
            violations.append(f"tracked by git: {t}")
    return violations


# --------------------------------------------------------------------------
# Export (needs telethon + .secrets\\telegram.env; lazy import so tests
# and core checks never require the research group)
# --------------------------------------------------------------------------
def _flood_seconds(e: Exception) -> int | None:
    try:
        from telethon.errors import FloodWaitError
        if isinstance(e, FloodWaitError):
            return int(e.seconds)
    except ImportError:
        pass
    return None


async def _fetch_new(client, channel: str, last_id: int) -> list:
    """Read-only history fetch with FLOOD_WAIT sleep. Never posts/joins."""
    while True:
        try:
            return [m async for m in
                    client.iter_messages(channel, min_id=last_id)]
        except Exception as e:  # noqa: BLE001 — FloodWait handled, else raise
            secs = _flood_seconds(e)
            if secs is None:
                raise
            time.sleep(secs + 1)


def export_channel(client, channel: str, last_id: int) -> tuple[int, int]:
    """Export messages newer than last_id. Returns (notes_written, new_last_id)."""
    msgs = asyncio.run(_fetch_new(client, channel, last_id))
    if not msgs:
        return 0, last_id
    by_day: dict[str, list[dict]] = {}
    top = last_id
    for m in msgs:
        top = max(top, m.id)
        ts = m.date.astimezone(timezone.utc)
        day = ts.strftime("%Y-%m-%d")
        text = (m.text or "").strip()
        if text:
            by_day.setdefault(day, []).append(
                {"ts": ts.strftime("%Y-%m-%d %H:%M"), "text": text})
    n = 0
    for day, items in sorted(by_day.items()):
        p = day_note_path(channel, day)
        if p.is_file():  # append new blocks to the existing note for that day
            old = p.read_text(encoding="utf-8")
            if parse_frontmatter(old).get("date") != day:
                raise ValueError(f"front-matter date mismatch in {p}")
            extra = "\n".join(
                f"## {it['ts']}\n\n{it['text']}\n" for it in items)
            if extra.strip() and extra.strip() not in old:
                p.write_text(old + "\n" + extra, encoding="utf-8")
                n += 1
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://t.me/{channel.lstrip('@')}"
        p.write_text(render_note(channel, day, url, items), encoding="utf-8")
        n += 1
    return n, top


def cmd_export() -> int:
    if not SECRETS_ENV.is_file():
        print(f"missing {SECRETS_ENV} (api_id/api_hash); nothing to do")
        return 2
    cfg = load_dotenv(SECRETS_ENV)
    channels = load_allowlist(ALLOWLIST)
    if not channels:
        print(f"allowlist {ALLOWLIST} is empty; nothing to do")
        return 2
    try:
        from telethon import TelegramClient
    except ImportError:
        print("telethon not installed (uv sync --group research); nothing to do")
        return 2
    session = cfg.get("session_path",
                      str(SRJ_ROOT / "private" / "tg_session"))
    state = load_state(STATE)
    total = 0
    with TelegramClient(session, int(cfg["api_id"]),
                        cfg["api_hash"]) as client:
        for ch in channels:
            n, top = export_channel(client, ch, int(state.get(ch, 0)))
            state[ch] = top
            total += n
            print(f"{ch}: {n} notes, cursor {top}")
    save_state(STATE, state)
    print(f"wrote {total} notes")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Telegram → vault exporter (W5).")
    ap.add_argument("cmd", choices=["check", "export"])
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        bad = check_vault_not_tracked(Path(args.repo_root).resolve(), VAULT)
        if bad:
            print("\n".join(f"FAIL vault-guard: {b}" for b in bad))
            return 1
        print("PASS vault-guard")
        return 0
    return cmd_export()


if __name__ == "__main__":
    sys.exit(main())

"""Issue #26 (W5) tests: vault exporter — front-matter, allow-list,
incremental cursor, FLOOD_WAIT sleep, read-only, vault guard. No network."""
from datetime import datetime, timezone
from types import SimpleNamespace

import tools.tg_export as tg


def _msg(i, day, hour, text):
    return SimpleNamespace(id=i,
                           date=datetime(2026, 10, day, hour, tzinfo=timezone.utc),
                           text=text)


class _FakeClient:
    def __init__(self, messages, fail_first=None):
        self._messages = messages
        self.calls = []
        self._fail_first = fail_first

    async def iter_messages(self, channel, min_id=0):
        self.calls.append(("iter_messages", channel, min_id))
        if self._fail_first:
            exc = self._fail_first
            self._fail_first = None
            raise exc
        for m in self._messages:
            if m.id > min_id:
                yield m


def test_frontmatter_roundtrip():
    note = tg.render_note("chan", "2026-10-09", "https://t.me/chan",
                          [{"ts": "2026-10-09 10:00", "text": "hello"}])
    fm = tg.parse_frontmatter(note)
    assert all(fm.get(k) for k in tg.REQUIRED_FRONTMATTER)
    assert fm["source"] == "telegram" and fm["captured_by"] == "tg_export"


def test_allowlist_filter(tmp_path):
    p = tmp_path / "allow.txt"
    p.write_text("# comment\n\n  chan_one  \n@chan_two\n", encoding="utf-8")
    assert tg.load_allowlist(p) == ["chan_one", "@chan_two"]
    assert tg.load_allowlist(tmp_path / "missing.txt") == []


def test_incremental_cursor(tmp_path, monkeypatch):
    monkeypatch.setattr(tg, "INBOX_TG", tmp_path / "inbox")
    client = _FakeClient([_msg(1, 9, 10, "first"), _msg(2, 9, 12, "second"),
                          _msg(3, 10, 9, "third")])
    n, top = tg.export_channel(client, "chan", 0)
    assert (n, top) == (2, 3)  # two day-notes, cursor at 3
    assert (tmp_path / "inbox" / "chan" / "2026-10-09.md").is_file()
    n2, top2 = tg.export_channel(client, "chan", top)
    assert (n2, top2) == (0, 3)
    assert client.calls[-1][2] == 3  # second run passed min_id=3


def test_flood_wait_sleeps(monkeypatch, tmp_path):
    monkeypatch.setattr(tg, "INBOX_TG", tmp_path / "inbox")

    class _FakeTime:
        def __init__(self):
            self.sleeps = []

        def sleep(self, s):
            self.sleeps.append(s)

    fake = _FakeTime()
    monkeypatch.setattr(tg, "time", fake)
    monkeypatch.setattr(tg, "_flood_seconds", lambda e: 7)
    client = _FakeClient([_msg(5, 9, 10, "after flood")],
                         fail_first=RuntimeError("flood"))
    n, top = tg.export_channel(client, "chan", 0)
    assert (n, top) == (1, 5) and fake.sleeps == [8]


def test_read_only_client(tmp_path, monkeypatch):
    monkeypatch.setattr(tg, "INBOX_TG", tmp_path / "inbox")
    client = _FakeClient([_msg(1, 9, 10, "hi")])
    tg.export_channel(client, "chan", 0)
    assert {c[0] for c in client.calls} == {"iter_messages"}


def test_vault_guard_inside_repo(tmp_path):
    bad = tg.check_vault_not_tracked(tmp_path, tmp_path / "private" / "vault",
                                     runner=lambda *a, **k: SimpleNamespace(
                                         stdout="", returncode=0))
    assert any("inside repo" in b for b in bad)


def test_vault_guard_tracked_path(tmp_path):
    def runner(*a, **k):
        return SimpleNamespace(stdout="tools/tg_export.py\nprivate/vault/x.md\n",
                               returncode=0)

    bad = tg.check_vault_not_tracked(tmp_path / "repo", tmp_path / "vault",
                                     runner=runner)
    assert bad == ["tracked by git: private/vault/x.md"]


def test_vault_guard_clean(tmp_path):
    def runner(*a, **k):
        return SimpleNamespace(stdout="tools/x.py\n", returncode=0)

    assert tg.check_vault_not_tracked(tmp_path / "repo", tmp_path / "vault",
                                      runner=runner) == []


def test_export_channel_no_running_loop(tmp_path, monkeypatch):
    """export_channel works under plain pytest (asyncio.run inside)."""
    monkeypatch.setattr(tg, "INBOX_TG", tmp_path / "inbox")
    n, _ = tg.export_channel(_FakeClient([_msg(1, 9, 10, "x")]), "c", 0)
    assert n == 1

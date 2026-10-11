"""Issue #20 (W1) tests: funnel validator — one valid fixture passes,
one broken fixture per check fails with that check's name. All text invented.
"""
from types import SimpleNamespace

import pytest

from core.funnel import candidate_hash
from core.funnel.validate import REVIEW_KEYS, validate

CLAIM = "Breakfast-range expansion with a tick-count filter on EURUSD."
QUOTE = "morning range breaks tend to extend past noon"
PRIVATE_NAME = "invented-breakfast.md"


def _frontmatter(hash6):
    lines = ["---"]
    vals = {"id": "2026-10-10_EURUSD_M15_breakfast_aaaaaa", "hash": hash6,
            "status": "QUEUED", "family": "range-expansion",
            "instrument": "EURUSD", "timeframe": "M15",
            "session": "London", "volume_read": "tick-count relative volume",
            "flags": "", "related_to": "",
            "sources": "https://example.com/invented-breakfast",
            "created": "2026-10-10"}
    for k in REVIEW_KEYS:
        lines.append(f"{k}: {vals[k]}")
    return "\n".join(lines) + "\n---\n"


def _review(hash6):
    return (_frontmatter(hash6)
            + f"{CLAIM}\nUnverified external claim. Not tested on SRJ data.\n")


def _evidence():
    return ("## Claim\n" + CLAIM + "\n"
            "## Source record\nInvented blog, 2026-01-01, rung 1, "
            + PRIVATE_NAME + "\n"
            "## Raw evidence\nAs stated by the source (sample: unstated): a "
            "morning range break often extends into the midday period.\n"
            "## Counter-evidence\nRange days often fade the break; "
            "trend days often extend. No single direction dominates all "
            "sessions, so a filter is needed.\n"
            "## Mechanism\nA cluster of stop orders rests beyond the early "
            "extreme; a tick-count rise shows fresh interest.\n"
            "## Builder's note\nPlausible enough to codify; needs a real "
            "test before any verdict.\n")


def _card():
    return ("# Card draft (invented)\n\nvolume_read: tick-count relative volume\n\n"
            "Entry: to be codified. Exit: to be codified.\n\n"
            "## srj-hard-constraints checklist\n- [x] hold at least 3 minutes\n"
            "- [x] visible stop on every order\n- [ ] news blackout codified\n")


def _source():
    return ("URL: https://example.com/invented-breakfast\nAuthor: Invented Author\n"
            "Retrieved: 2026-10-10\n\nSummary: An invented post describes a "
            "morning range idea on a major pair. It gives no sample or costs. "
            "It stays a lead until tested.\n\n"
            f"> {QUOTE}\n{PRIVATE_NAME}:2-2\n")


def _private_text():
    return ("header line\n" + QUOTE + "\nthird line\n")


def _ok_http(url, **kwargs):
    return SimpleNamespace(status_code=200)


@pytest.fixture()
def setup(tmp_path, monkeypatch):
    """A fully valid candidate + funnel root + private root."""
    monkeypatch.setenv("SRJ_DATA", str(tmp_path))
    funnel = tmp_path / "funnel"
    (funnel / "candidates").mkdir(parents=True)
    (funnel / "rejected").mkdir()
    (funnel / "index.csv").write_text(
        "id,hash,created,instrument,timeframe,family,flags,"
        "related_to,status,source_url\n")
    (funnel / "rejected" / "index.csv").write_text(
        "date,idea,hash,rule,reason,source_url\n")
    h = candidate_hash(CLAIM, "EURUSD", "M15")
    cand = funnel / "candidates" / f"2026-10-10_EURUSD_M15_breakfast_{h}"
    cand.mkdir()
    (cand / "review.md").write_text(_review(h))
    (cand / "evidence.md").write_text(_evidence())
    (cand / "card_draft.md").write_text(_card())
    (cand / "source.md").write_text(_source())
    priv = tmp_path / "private"
    priv.mkdir()
    (priv / PRIVATE_NAME).write_text(_private_text())
    return cand, funnel, priv


def _run(cand, funnel, priv, http_get=_ok_http):
    return validate(cand, funnel, priv, http_get=http_get)


def test_valid_fixture_passes(setup):
    assert _run(*setup) == []


def test_four_files_exist(setup):
    cand, funnel, priv = setup
    (cand / "card_draft.md").unlink()
    fails = _run(cand, funnel, priv)
    assert fails == ["FAIL four-files-exist: missing ['card_draft.md']"]


def test_review_frontmatter(setup):
    cand, funnel, priv = setup
    text = (cand / "review.md").read_text()
    (cand / "review.md").write_text(text.replace("session: London\n", ""))
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL review-frontmatter") for f in fails)
    assert not any("hash-valid" in f or "hash-unique" in f for f in fails)


def test_evidence_headings(setup):
    cand, funnel, priv = setup
    text = (cand / "evidence.md").read_text()
    text = text.replace("## Mechanism", "## TMP").replace(
        "## Builder's note", "## Mechanism").replace("## TMP", "## Builder's note")
    (cand / "evidence.md").write_text(text)
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL evidence-headings") for f in fails)


def test_card_draft_requirements(setup):
    cand, funnel, priv = setup
    text = (cand / "card_draft.md").read_text()
    (cand / "card_draft.md").write_text(
        "\n".join(line for line in text.splitlines()
                   if not line.strip().startswith("- [")))
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL card-draft-requirements") for f in fails)
    assert not any(f.startswith("FAIL volume-read") for f in fails)


def test_source_md_requirements(setup):
    cand, funnel, priv = setup
    text = (cand / "source.md").read_text()
    (cand / "source.md").write_text(
        text.replace(f"{PRIVATE_NAME}:2-2", ""))
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL source-md-requirements") for f in fails)
    assert not any(f.startswith("FAIL quote-verbatim") for f in fails)


def test_hash_valid(setup):
    cand, funnel, priv = setup
    text = (cand / "review.md").read_text()
    h = candidate_hash(CLAIM, "EURUSD", "M15")
    (cand / "review.md").write_text(text.replace(f"hash: {h}", "hash: deadbe"))
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL hash-valid") for f in fails)


def test_hash_unique(setup):
    cand, funnel, priv = setup
    import shutil
    dup = cand.parent / (cand.name + "_dup")
    shutil.copytree(cand, dup)
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL hash-unique") for f in fails)


def test_quote_verbatim(setup):
    cand, funnel, priv = setup
    (priv / PRIVATE_NAME).write_text("totally different content\n")
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL quote-verbatim") for f in fails)


def test_url_200(setup):
    cand, funnel, priv = setup
    fails = _run(cand, funnel, priv,
                 http_get=lambda url, **k: SimpleNamespace(status_code=404))
    assert any(f.startswith("FAIL url-200") for f in fails)


def test_volume_read(setup):
    cand, funnel, priv = setup
    (cand / "card_draft.md").write_text(
        "# Card draft (invented)\n\nNo read stated here.\n\n- [x] item\n")
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL volume-read") for f in fails)


def test_counter_evidence(setup):
    cand, funnel, priv = setup
    text = (cand / "evidence.md").read_text()
    import re
    text = re.sub(r"## Counter-evidence\n(.*?)(?=\n## |\Z)",
                  "## Counter-evidence\n", text, flags=re.DOTALL)
    (cand / "evidence.md").write_text(text)
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL counter-evidence") for f in fails)


def test_no_verdict_words(setup):
    cand, funnel, priv = setup
    (cand / "evidence.md").write_text(
        (cand / "evidence.md").read_text() + "This approach works well.\n")
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL no-verdict-words") for f in fails)


def test_no_own_numbers(setup):
    cand, funnel, priv = setup
    (cand / "evidence.md").write_text(
        (cand / "evidence.md").read_text().replace(
            "## Mechanism\n",
            "## Mechanism\nOur backtest shows mean 0.4R per trade.\n"))
    fails = _run(cand, funnel, priv)
    assert any(f.startswith("FAIL no-own-numbers") for f in fails)

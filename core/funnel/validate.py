"""Idea Funnel candidate validator (skill `srj-idea-funnel`, issue #20).

Usage: uv run python -m core.funnel.validate <candidate_dir>
       [--funnel-root research/funnel] [--private-root <vault-adjacent sources dir>]

Exit 0 when every check passes; otherwise prints `FAIL <check-name>` lines
(one per failed check) and exits 1. Each test fixture breaks exactly one
check, so check names are stable API (see tests/test_funnel_validate.py).
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path

import httpx
import yaml

from . import candidate_hash

REVIEW_KEYS = ["id", "hash", "status", "family", "instrument", "timeframe",
               "session", "volume_read", "flags", "related_to", "sources",
               "created"]
EVIDENCE_HEADINGS = ["## Claim", "## Source record", "## Raw evidence",
                     "## Counter-evidence", "## Mechanism",
                     "## Builder's note"]
DISCLAIMER = "Unverified external claim. Not tested on SRJ data."
VERDICT_WORDS = ["works", "profitable", "proven", "edge confirmed",
                 "guaranteed", "holy grail"]
# Performance-metric phrasing outside quotes (review body, Mechanism, note).
RESULT_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(R\b|%|percent|trades|win\s*rate|profit\s*factor|sharpe)\b",
    re.IGNORECASE)
QUOTE_CITE_RE = re.compile(r"(\S+\.md):(\d+)-(\d+)")
CITATION_LINE_RE = re.compile(r"^>\s*(.+)$", re.MULTILINE)


def _fail(fails: list, name: str, detail: str = ""):
    fails.append(f"FAIL {name}" + (f": {detail}" if detail else ""))


def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def _body(text: str) -> str:
    m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return text[m.end():] if m else text


def _unquoted(text: str) -> str:
    """Drop blockquote lines (quoted source text is exempt from checks)."""
    return "\n".join(line for line in text.splitlines()
                      if not line.lstrip().startswith(">"))


def validate(cand: Path, funnel_root: Path, private_root: Path,
             http_get=None) -> list[str]:
    """Run every static + dynamic check. Returns the FAIL lines (empty = pass)."""
    fails: list[str] = []
    files = {n: cand / n for n in
             ("review.md", "evidence.md", "card_draft.md", "source.md")}

    # -- S1: the four files exist --
    missing = [n for n, p in files.items() if not p.is_file()]
    if missing:
        _fail(fails, "four-files-exist", f"missing {missing}")
        return fails  # nothing else can run
    review, evidence, card, source = (p.read_text(encoding="utf-8")
                                     for p in files.values())

    # -- S2: review frontmatter keys + disclaimer --
    fm = _frontmatter(review)
    if not fm:
        _fail(fails, "review-frontmatter", "no YAML frontmatter block")
    else:
        absent = [k for k in REVIEW_KEYS if k not in fm]
        if absent:
            _fail(fails, "review-frontmatter", f"missing keys {absent}")
        if fm.get("status") != "QUEUED":
            _fail(fails, "review-frontmatter",
                  f"status must be QUEUED, got {fm.get('status')!r}")
    if DISCLAIMER not in review:
        _fail(fails, "review-frontmatter", "disclaimer line missing")
    claim = ""
    for line in _body(review).splitlines():
        if line.strip():
            claim = line.strip()
            break

    # -- S3: evidence headings in order --
    idx = [evidence.find(h) for h in EVIDENCE_HEADINGS]
    if any(i < 0 for i in idx) or idx != sorted(idx):
        _fail(fails, "evidence-headings",
              "need the six ## headings in skill order")

    # -- S4: card draft volume read + constraint checklist --
    if "volume" not in card.lower():
        _fail(fails, "card-draft-requirements", "no volume read")
    elif ("volume_read: missing" not in card
          and not re.search(r"volume_read:\s*\S+", card)):
        _fail(fails, "card-draft-requirements", "volume read not stated")
    if not re.search(r"^\s*-\s*\[[ xX]\]", card, re.MULTILINE):
        _fail(fails, "card-draft-requirements",
              "constraint checklist has no items")

    # -- S5: source.md record + quoted citation --
    if "http" not in source:
        _fail(fails, "source-md-requirements", "no URL")
    quotes = CITATION_LINE_RE.findall(source)
    cite = QUOTE_CITE_RE.search(source)
    if len(quotes) > 1:
        _fail(fails, "source-md-requirements", "more than one quote")
    if not cite:
        _fail(fails, "source-md-requirements",
              "no NN-slug.md:START-END citation")
    elif quotes and len(quotes[0].split()) > 15:
        _fail(fails, "source-md-requirements",
              f"quote is {len(quotes[0].split())} words (>15)")

    # -- S6: hash recomputes from claim + instrument + timeframe --
    if fm and claim:
        want = candidate_hash(claim, str(fm.get("instrument", "")),
                              str(fm.get("timeframe", "")))
        if fm.get("hash") != want:
            _fail(fails, "hash-valid",
                  f"frontmatter {fm.get('hash')!r} != recomputed {want!r}")

    # -- S7: hash unique across candidates and rejects --
    if fm and fm.get("hash"):
        seen = _known_hashes(funnel_root)
        if seen.count(str(fm["hash"])) > 1:
            _fail(fails, "hash-unique", f"hash {fm['hash']!r} seen twice")

    # -- D1: quote verbatim in the private source file at cited lines --
    if cite and quotes:
        fname, a, b = cite.group(1), int(cite.group(2)), int(cite.group(3))
        cands = sorted(private_root.rglob(fname))
        if not cands:
            _fail(fails, "quote-verbatim", f"{fname} not saved privately")
        else:
            lines = cands[0].read_text(encoding="utf-8").splitlines()
            span = "\n".join(lines[a - 1:b])
            if quotes[0] not in span:
                _fail(fails, "quote-verbatim",
                      "quote not found verbatim at cited lines")

    # -- D2: URL returned HTTP 200 --
    urls = re.findall(r"https?://\S+", source)
    if urls:
        get = http_get or httpx.get
        try:
            r = get(urls[0], timeout=20.0,
                    headers={"User-Agent": "SRJ-Ventures-funnel/0.1"})
            if r.status_code != 200:
                _fail(fails, "url-200", f"HTTP {r.status_code}")
        except Exception as e:  # noqa: BLE001 — any fetch failure fails the check
            _fail(fails, "url-200", repr(e)[:120])

    # -- D3: volume read already covered in S4 (non-empty or missing-flag);
    #        re-assert here so the dynamic name exists independently --
    if "volume" not in card.lower():
        _fail(fails, "volume-read", "no volume read in card draft")

    # -- D4: counter-evidence entry --
    m = re.search(r"## Counter-evidence\n(.*?)(?=\n## |\Z)", evidence, re.DOTALL)
    counter = m.group(1).strip() if m else ""
    if len(counter) < 10 or ("none found" in counter.lower()
                             and "searched" not in counter.lower()):
        _fail(fails, "counter-evidence",
              "empty, or 'none found' without searched-<where>")

    # -- D5: no verdict words outside quotes --
    blob = _unquoted(review + "\n" + evidence + "\n" + card).lower()
    hits = sorted({w for w in VERDICT_WORDS if w in blob})
    if hits:
        _fail(fails, "no-verdict-words", f"found {hits}")

    # -- D6: no numbers presented as SRJ results --
    for label, section in (("review-body", _body(review)),
                           ("mechanism/note", _tail_sections(evidence))):
        if RESULT_RE.search(_unquoted(section)):
            _fail(fails, "no-own-numbers", f"metric phrasing in {label}")
            break

    return fails


def _tail_sections(evidence: str) -> str:
    """Mechanism + Builder's note sections (own-numbers check zone)."""
    m = re.search(r"## Mechanism\n(.*)", evidence, re.DOTALL)
    return m.group(1) if m else ""


def _known_hashes(funnel_root: Path) -> list[str]:
    """Hashes from index.csv, rejected/index.csv, and candidate frontmatter."""
    out: list[str] = []
    for csv_path, col in ((funnel_root / "index.csv", "hash"),
                          (funnel_root / "rejected" / "index.csv", "hash")):
        if csv_path.is_file():
            with csv_path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get(col):
                        out.append(row[col])
    cand_root = funnel_root / "candidates"
    if cand_root.is_dir():
        for review in sorted(cand_root.glob("*/review.md")):
            try:
                fm = _frontmatter(review.read_text(encoding="utf-8"))
                if fm.get("hash"):
                    out.append(str(fm["hash"]))
            except Exception:  # noqa: BLE001 — a broken candidate fails S2 anyway
                continue
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate one funnel candidate.")
    ap.add_argument("candidate_dir")
    ap.add_argument("--funnel-root", default="research/funnel")
    ap.add_argument("--private-root", default=os.path.join(
        os.environ.get("SRJ_ROOT", r"D:\SRJ Venture"),
        "private", "funnel", "sources"))
    args = ap.parse_args(argv)
    fails = validate(Path(args.candidate_dir), Path(args.funnel_root),
                     Path(args.private_root))
    if fails:
        print("\n".join(fails))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

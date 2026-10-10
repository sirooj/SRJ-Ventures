"""Idea Funnel helpers (skill `srj-idea-funnel`, issue #20).

Hash: first 6 hex of SHA-256 of `normalise(hypothesis) | instrument | timeframe`,
where normalise = lowercase + collapsed whitespace.
"""
from __future__ import annotations

import hashlib
import re

_WS = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Lowercase + collapsed whitespace."""
    return _WS.sub(" ", text.strip().lower())


def candidate_hash(hypothesis: str, instrument: str, timeframe: str) -> str:
    """6-hex dedup hash for a candidate."""
    key = f"{normalise(hypothesis)}|{instrument}|{timeframe}"
    return hashlib.sha256(key.encode()).hexdigest()[:6]

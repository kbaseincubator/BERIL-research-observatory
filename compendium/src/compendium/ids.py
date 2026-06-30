"""Deterministic text normalization + content-addressed hashing.

Pure functions of content: ``normalize`` (NFKC label/statement normalization) and ``content_hash``
(stable member-set hashing used for page reuse). Order-independent and stable across re-extraction.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def normalize(text: str) -> str:
    """Deterministic label/statement normalization: NFKC, lowercase, strip punctuation, collapse ws."""
    if text is None:
        return ""
    t = unicodedata.normalize("NFKC", str(text)).lower()
    t = _PUNCT.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    return t


def _h(text: str, n: int = 12) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=max(4, n // 2)).hexdigest()[:n]


def content_hash(*parts: str, n: int = 16) -> str:
    return _h("".join(p or "" for p in parts), n=n)

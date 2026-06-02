"""Content-addressed identity + canonical serialization.

Identity rules (design spec §7):
  - Node id  = ``n:`` + blake2b(normalized_label + "|" + type)        -> stable forever; CURIE is an alias.
  - Assertion id = ``a:`` + blake2b(s|p|o)  (relation) or blake2b(normalized statement) (finding/claim).
These are pure functions of content, so they are stable across re-extraction and order-independent —
which is what makes corrections re-bind and the build idempotent.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Iterable, Optional

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


def node_id(label: str, type_: str) -> str:
    return "n:" + _h(normalize(label) + "|" + (type_ or "").strip())


def assertion_id(*, s: Optional[str] = None, p: Optional[str] = None, o: Optional[str] = None,
                 statement: Optional[str] = None, project: Optional[str] = None) -> str:
    """Relation assertions hash (s|p|o); statement assertions hash the normalized statement.

    ``project`` is folded in only for statement assertions (a finding is project-local), so the same
    relation extracted in two projects collapses to one assertion id while two projects' prose findings
    stay distinct.
    """
    if statement is not None:
        basis = "stmt|" + (project or "") + "|" + normalize(statement)
    else:
        basis = "rel|" + "|".join([s or "", p or "", o or ""])
    return "a:" + _h(basis)


def content_hash(*parts: str, n: int = 16) -> str:
    return _h("".join(p or "" for p in parts), n=n)


def canonical_triples(graph) -> list[tuple[str, str, str]]:
    """Stable, sorted (s, p, o) triples for hashing / idempotency checks."""
    triples = {(e.s, e.p, e.o) for e in graph.edges}
    return sorted(triples)


def graph_hash(graph) -> str:
    """Order-independent hash of the canonical graph (nodes + edges + tiers)."""
    node_part = sorted(f"{n.id}{n.type}{n.curie or ''}{n.tier}" for n in graph.nodes)
    edge_part = sorted(f"{e.s}{e.p}{e.o}{e.polarity or ''}{e.tier}" for e in graph.edges)
    return content_hash("".join(node_part), "".join(edge_part), n=32)


def section_fact_hash(facts: Iterable[str]) -> str:
    """Stable hash of a page-section's facts (sorted) — drives section-level re-narration."""
    return content_hash("".join(sorted(facts)), n=16)

"""beril science — pure, model-free calibrated-trust computation.

Ported from the beril-pi-agent reference (lib/science.ts, lib/claim-state.ts).

Trust is expressed as WORDS, never a verbalized number, so a claim cannot sound
more certain than its evidence supports. The author WRITES a confidence word; this
module computes the evidence side and flags the gap:

- ``groundedness_for_evidence`` — counts the DISTINCT independent re-runnable
  sources behind a claim (``well-grounded``/``single-source``/``ungrounded``),
  deduped at the notebook level so two cells of the same notebook are one source.
- ``tier_mismatch`` — flags where a *written* ``high``/``medium`` confidence
  outruns its groundedness.

The claims ledger (``claims_cmd``) reads the written confidence word and computes
groundedness + tier_mismatch from the evidence. Every function is pure and
deterministic (no I/O, no model; tolerant of empty or malformed input — never
throws).
"""

from __future__ import annotations

import re

#: Confidence tiers, strongest first.
CONFIDENCE_TIERS = ("high", "medium", "low")
#: Groundedness tiers, strongest first.
GROUNDEDNESS_TIERS = ("well-grounded", "single-source", "ungrounded")
#: Per-claim status enum (a separate axis from the project lifecycle states).
CLAIM_STATUSES = (
    "open",
    "supported",
    "refuted",
    "needs-replication",
    "blocked",
    "needs-evidence",
)
#: Evidence pointer kinds; only ``query``/``notebook`` are re-runnable results.
EVIDENCE_KINDS = ("query", "notebook", "figure", "paper", "web", "docs")


def is_result(pointer: dict) -> bool:
    """A re-runnable data/code result (vs literature, which alone stays ``low``).

    Tolerant of malformed (non-dict) elements — returns False rather than raising.
    """
    return isinstance(pointer, dict) and pointer.get("kind") in ("query", "notebook")


def groundedness_for_evidence(supports: list[dict]) -> str:
    """Map supporting evidence to a groundedness tier (pure, deterministic).

    Counts the DISTINCT independent re-runnable sources: only query/notebook
    locators count, keyed at the SOURCE level — the ``#cell-N`` anchor is dropped,
    so two cells of the same notebook are ONE source (they share a kernel/data
    load and are not independent corroboration), while distinct notebooks/queries
    each count once. >=2 distinct -> ``well-grounded``; exactly 1 ->
    ``single-source``; 0 -> ``ungrounded``. Tolerates ``[]`` / missing locators.
    """
    locators: set[str] = set()
    for p in supports or []:
        if not is_result(p):
            continue
        # Drop the `#cell-N` (or any `#…`) anchor so same-notebook cells collapse
        # to one source; query locators have no anchor and pass through unchanged.
        normalized = re.sub(r"\s+", "", str(p.get("locator") or ""))
        key = normalized.split("#", 1)[0].lower()
        if key:
            locators.add(key)
    if len(locators) >= 2:
        return "well-grounded"
    if len(locators) == 1:
        return "single-source"
    return "ungrounded"


def tier_mismatch(confidence: str, groundedness: str) -> bool:
    """True when a written ``high``/``medium`` confidence outruns its evidence.

    Pure — derived from the artifacts, never a model-supplied field.
    """
    return confidence in ("high", "medium") and groundedness != "well-grounded"


def confidence_from(text: str) -> str | None:
    """First recognized confidence word (high|medium|low) in a string, else None.

    The canonical word ladder is ``atlas/methods/evidence-grading.md`` (high/medium/
    low, graded by independent evidence streams); this matches it. Groundedness is a
    SEPARATE computed axis — see :func:`groundedness_for_evidence` / :func:`tier_mismatch`.
    """
    m = re.search(r"\b(high|medium|low)\b", text, re.IGNORECASE)
    return m.group(1).lower() if m else None


_STATUS_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in CLAIM_STATUSES) + r")\b", re.IGNORECASE
)


def status_from(text: str) -> str | None:
    """First recognized claim status token in a string (by position), else None.

    Position-based like :func:`confidence_from`, so a written value followed by a
    comment listing the other options resolves to the written value, not the
    first enum member that happens to appear.
    """
    m = _STATUS_RE.search(text)
    return m.group(1).lower() if m else None


def claim_id(text: str) -> str:
    """Stable slug for a claim: lowercased, non-alnum -> '-', trimmed THEN
    truncated to 56 chars (matches the reference order; no re-trim after slice)."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    slug = re.sub(r"^-+|-+$", "", slug)
    slug = slug[:56]
    return slug or "claim"

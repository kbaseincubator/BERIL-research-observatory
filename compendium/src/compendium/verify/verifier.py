"""Deterministic auto-verification: assign entity/assertion tiers.

No tier here claims a *relation* is true -- grounding is purely about whether referenced
entities carry CURIEs and whether the cited evidence span is locatable in the source text.
``conflict`` tiers are assigned later during the cross-project build.
"""

from __future__ import annotations

import pathlib

from ..models import (
    TIER_ASSERTED,
    TIER_GROUNDED,
    Assertion,
    Entity,
    ProjectKG,
)


def _entity_grounded(entity: Entity) -> bool:
    return bool(entity.curie)


def _read_text(project_dir: pathlib.Path, rel: str) -> str | None:
    """Return the text of ``project_dir/<rel>`` or None if it cannot be read."""
    try:
        return (project_dir / rel).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None


def _entities_grounded(a: Assertion, entities: dict[str, Entity]) -> bool:
    """True iff the assertion references >=1 entity and every referenced entity is grounded."""
    referenced = [nid for nid in (a.s, a.o) if nid is not None]
    referenced.extend(a.entities)
    if not referenced:
        return False
    return all(nid in entities and _entity_grounded(entities[nid]) for nid in referenced)


def _span_ok(a: Assertion, project_dir: pathlib.Path) -> bool:
    """Locate the evidence span's quote in the cited file.

    No evidence or no span -> False. Span present but empty quote -> True. Otherwise the
    quote must be a substring of the cited file's text (missing file -> False).
    """
    if a.evidence is None or a.evidence.span is None:
        return False
    span = a.evidence.span
    if not span.quote:
        return True
    text = _read_text(project_dir, span.file)
    if text is None:
        return False
    return span.quote in text


def verify(pkg: ProjectKG, project_dir: pathlib.Path) -> ProjectKG:
    """Assign entity and assertion tiers in-place (mutates and returns ``pkg``)."""
    for entity in pkg.entities:
        entity.tier = TIER_GROUNDED if _entity_grounded(entity) else TIER_ASSERTED

    entities = {e.node: e for e in pkg.entities}
    for a in pkg.assertions:
        grounded = _entities_grounded(a, entities) and _span_ok(a, project_dir)
        a.tier = TIER_GROUNDED if grounded else TIER_ASSERTED

    return pkg

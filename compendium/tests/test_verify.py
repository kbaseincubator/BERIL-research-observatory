"""Tests for deterministic auto-verification (compendium.verify.verifier)."""

from __future__ import annotations

import pathlib

from compendium.models import (
    TIER_ASSERTED,
    TIER_GROUNDED,
    Assertion,
    Entity,
    Evidence,
    ProjectKG,
    ProjectMeta,
    Span,
)
from compendium.verify import verify

FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "proj_demo"
QUOTE = "grows robustly on quinate as a sole carbon source"


def _entity(node: str, *, curie: str | None) -> Entity:
    return Entity(node=node, type="Organism", label=node, curie=curie)


def _pkg(entities: list[Entity], assertion: Assertion) -> ProjectKG:
    return ProjectKG(
        project=ProjectMeta(id="proj_demo", title="Demo"),
        entities=entities,
        assertions=[assertion],
    )


def test_entity_tier_from_curie() -> None:
    pkg = ProjectKG(
        project=ProjectMeta(id="p", title="p"),
        entities=[_entity("n:a", curie="NCBITaxon:1"), _entity("n:b", curie=None)],
    )
    out = verify(pkg, FIXTURE_DIR)
    by_node = {e.node: e for e in out.entities}
    assert by_node["n:a"].tier == TIER_GROUNDED
    assert by_node["n:b"].tier == TIER_ASSERTED


def test_relation_grounded() -> None:
    span = Span(file="REPORT.md", quote=QUOTE)
    a = Assertion(id="a:1", kind="relation", s="n:org", p="grows_on", o="n:quin",
                  evidence=Evidence(span=span))
    pkg = _pkg(
        [_entity("n:org", curie="NCBITaxon:1"), _entity("n:quin", curie="CHEBI:1")],
        a,
    )
    out = verify(pkg, FIXTURE_DIR)
    assert out.assertions[0].tier == TIER_GROUNDED


def test_relation_one_entity_ungrounded() -> None:
    span = Span(file="REPORT.md", quote=QUOTE)
    a = Assertion(id="a:1", kind="relation", s="n:org", p="grows_on", o="n:quin",
                  evidence=Evidence(span=span))
    pkg = _pkg(
        [_entity("n:org", curie="NCBITaxon:1"), _entity("n:quin", curie=None)],
        a,
    )
    out = verify(pkg, FIXTURE_DIR)
    assert out.assertions[0].tier == TIER_ASSERTED


def test_relation_quote_not_in_file() -> None:
    span = Span(file="REPORT.md", quote="this string is absent from the report")
    a = Assertion(id="a:1", kind="relation", s="n:org", p="grows_on", o="n:quin",
                  evidence=Evidence(span=span))
    pkg = _pkg(
        [_entity("n:org", curie="NCBITaxon:1"), _entity("n:quin", curie="CHEBI:1")],
        a,
    )
    out = verify(pkg, FIXTURE_DIR)
    assert out.assertions[0].tier == TIER_ASSERTED


def test_finding_no_entities() -> None:
    span = Span(file="REPORT.md", quote=QUOTE)
    a = Assertion(id="a:1", kind="finding", statement="some finding",
                  evidence=Evidence(span=span))
    pkg = _pkg([], a)
    out = verify(pkg, FIXTURE_DIR)
    assert out.assertions[0].tier == TIER_ASSERTED


def test_missing_cited_file_is_asserted() -> None:
    span = Span(file="NOPE.md", quote=QUOTE)
    a = Assertion(id="a:1", kind="relation", s="n:org", p="grows_on", o="n:quin",
                  evidence=Evidence(span=span))
    pkg = _pkg(
        [_entity("n:org", curie="NCBITaxon:1"), _entity("n:quin", curie="CHEBI:1")],
        a,
    )
    out = verify(pkg, FIXTURE_DIR)
    assert out.assertions[0].tier == TIER_ASSERTED


def test_empty_quote_with_span_is_grounded() -> None:
    span = Span(file="REPORT.md", quote="")
    a = Assertion(id="a:1", kind="relation", s="n:org", p="grows_on", o="n:quin",
                  evidence=Evidence(span=span))
    pkg = _pkg(
        [_entity("n:org", curie="NCBITaxon:1"), _entity("n:quin", curie="CHEBI:1")],
        a,
    )
    out = verify(pkg, FIXTURE_DIR)
    assert out.assertions[0].tier == TIER_GROUNDED

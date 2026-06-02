"""Tests for the deterministic grounder."""

from __future__ import annotations

from compendium import ids
from compendium.ground import ground, regex_curie
from compendium.models import Entity, ProjectKG, ProjectMeta


def _entity(label: str, type_: str, curie: str | None = None) -> Entity:
    return Entity(node=ids.node_id(label, type_), type=type_, label=label, curie=curie)


def _pkg(*entities: Entity) -> ProjectKG:
    return ProjectKG(project=ProjectMeta(id="p1", title="P1"), entities=list(entities))


def test_regex_curie_patterns():
    assert regex_curie("K00845") == "KEGG:K00845"
    assert regex_curie("COG0791") == "COG:COG0791"
    assert regex_curie("PF13455") == "Pfam:PF13455"
    assert regex_curie("PMID:12345") == "PMID:12345"
    assert regex_curie("10.1234/abc") == "DOI:10.1234/abc"
    assert regex_curie("Foo barbar") is None


def test_ground_known_organism():
    e = _entity("Acinetobacter baylyi ADP1", "Organism")
    pkg = ground(_pkg(e))
    out = pkg.entities[0]
    assert out.curie == "NCBITaxon:62977"
    assert out.label == "Acinetobacter baylyi ADP1"


def test_ground_organism_alias_canonicalizes_label():
    e = _entity("ADP1", "Organism")
    pkg = ground(_pkg(e))
    assert pkg.entities[0].curie == "NCBITaxon:62977"
    assert pkg.entities[0].label == "Acinetobacter baylyi ADP1"


def test_ground_unknown_organism_stays_none():
    e = _entity("Foo barbar", "Organism")
    pkg = ground(_pkg(e))
    assert pkg.entities[0].curie is None


def test_ground_regex_entities():
    ko = _entity("K00845", "KO")
    cog = _entity("COG0791", "OrthologGroup")
    gene = _entity("PF13455", "Gene")
    pkg = ground(_pkg(ko, cog, gene))
    assert pkg.entities[0].curie == "KEGG:K00845"
    assert pkg.entities[1].curie == "COG:COG0791"
    assert pkg.entities[2].curie == "Pfam:PF13455"


def test_ground_preserves_existing_curie_and_node_ids():
    pre = _entity("K00845", "KO", curie="custom:x")
    node = pre.node
    pkg = ground(_pkg(pre))
    assert pkg.entities[0].curie == "custom:x"
    assert pkg.entities[0].node == node


def test_ground_mutates_and_returns_same_object():
    pkg = _pkg(_entity("K00845", "KO"))
    assert ground(pkg) is pkg

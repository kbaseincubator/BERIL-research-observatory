"""Build tests: cross-project canonicalization via shared CURIE + synthesis nodes/edges."""

from compendium import ids
from compendium.build import build
from compendium.models import (
    TIER_GROUNDED,
    Assertion,
    Entity,
    ProjectKG,
    ProjectMeta,
)

CURIE = "NCBITaxon:62977"


def _make_pkg(project_id: str, organism_label: str, finding_text: str) -> ProjectKG:
    node = ids.node_id(organism_label, "Organism")
    org = Entity(
        node=node,
        type="Organism",
        label=organism_label,
        curie=CURIE,
        tier=TIER_GROUNDED,
    )
    finding = Assertion(
        id=ids.assertion_id(statement=finding_text, project=project_id),
        kind="finding",
        statement=finding_text,
        entities=[node],
        tier=TIER_GROUNDED,
    )
    return ProjectKG(
        project=ProjectMeta(id=project_id, title=project_id),
        entities=[org],
        assertions=[finding],
    )


def test_shared_curie_collapses_to_one_organism_with_both_findings():
    pkg_a = _make_pkg("proj_a", "ADP1", "ADP1 grows on benzoate")
    pkg_b = _make_pkg("proj_b", "Acinetobacter baylyi ADP1", "ADP1 lacks gene X")

    graph = build([pkg_a, pkg_b])

    organisms = [n for n in graph.nodes if n.type == "Organism"]
    assert len(organisms) == 1
    org = organisms[0]
    assert org.curie == CURIE
    assert org.provenance == ["proj_a", "proj_b"]

    findings = [n for n in graph.nodes if n.type == "Finding"]
    assert len(findings) == 2

    about_edges = [e for e in graph.edges if e.p == "about"]
    assert len(about_edges) == 2
    # every about edge points at the single canonical organism
    assert all(e.o == org.id for e in about_edges)
    assert {e.s for e in about_edges} == {f.id for f in findings}

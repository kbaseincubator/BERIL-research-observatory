"""Deterministic quality-assessment tests for the KG and rendered wiki."""

from __future__ import annotations

import pathlib

from compendium.models import Edge, Graph, Node
from compendium.quality import assess_kg, assess_wiki
from compendium.quality.wiki_quality import safe


def _small_graph() -> Graph:
    """2 nodes (one grounded biology node), 1 edge — fully wired, no dangling."""
    return Graph(
        nodes=[
            Node(
                id="n:org",
                type="Organism",  # biology type, grounded
                label="Acinetobacter baylyi ADP1",
                curie="NCBITaxon:62977",
                provenance=["proj_a"],
            ),
            Node(
                id="n:topic",
                type="Topic",  # synthesis type, not biology -> excluded from grounding
                label="Carbon metabolism",
                provenance=["proj_a"],
            ),
        ],
        edges=[
            Edge(s="n:org", p="about", o="n:topic", provenance=["proj_a"]),
        ],
    )


def test_assess_kg_core_metrics_exact():
    g = _small_graph()
    m = assess_kg(g)

    assert m["n_nodes"] == 2
    assert m["n_edges"] == 1
    assert m["dangling_edges"] == 0
    # 1 biology node (Organism), grounded -> grounding_rate exactly 1.0
    assert m["grounding_rate"] == 1.0
    assert 0.0 <= m["provenance_completeness"] <= 1.0
    assert m["provenance_completeness"] == 1.0
    # both nodes are edge endpoints
    assert m["orphan_nodes"] == 0
    assert m["nodes_by_type"] == {"Organism": 1, "Topic": 1}
    assert m["edges_by_predicate"] == {"about": 1}


def test_assess_kg_dangling_and_orphans_and_grounding_fraction():
    g = Graph(
        nodes=[
            Node(id="n:a", type="Gene", label="catA", curie="KO:K00001"),  # grounded
            Node(id="n:b", type="Gene", label="catB"),  # ungrounded biology node
            Node(id="n:iso", type="Topic", label="lonely"),  # orphan, non-biology
        ],
        edges=[
            Edge(s="n:a", p="related_to", o="n:missing"),  # dangling (o not a node)
        ],
    )
    m = assess_kg(g)
    assert m["dangling_edges"] == 1
    # 2 biology (Gene) nodes, 1 grounded -> 0.5
    assert m["grounding_rate"] == 0.5
    # n:b and n:iso are not endpoints; n:a is. -> 2 orphans
    assert m["orphan_nodes"] == 2


def test_assess_kg_empty_graph_is_zeroed():
    m = assess_kg(Graph())
    assert m["grounding_rate"] == 0.0
    assert m["provenance_completeness"] == 0.0
    assert m["cross_project_edges"] == 0


def test_assess_kg_cross_project_edges():
    g = Graph(
        nodes=[
            Node(id="n:a", type="Gene", label="g1", provenance=["proj_a", "proj_b"]),
            Node(id="n:b", type="Gene", label="g2", provenance=["proj_a"]),
        ],
        edges=[Edge(s="n:a", p="related_to", o="n:b", provenance=["proj_a"])],
    )
    # endpoint n:a contributed by 2 projects -> edge is cross-project
    assert assess_kg(g)["cross_project_edges"] == 1


def test_assess_wiki_coverage_and_links_exact(tmp_path: pathlib.Path):
    g = _small_graph()
    wiki = tmp_path / "wiki"
    wiki.mkdir()

    org_stem = safe("n:org")
    topic_stem = safe("n:topic")
    assert org_stem == "n_org"

    # one matching page for the Organism node, with a valid internal link to topic
    # and one broken internal link.
    (wiki / f"{topic_stem}.html").write_text("<html><body>topic</body></html>", encoding="utf-8")
    (wiki / f"{org_stem}.html").write_text(
        "<html><body>"
        f'<a href="{topic_stem}.html">topic</a>'
        '<a href="missing.html">broken</a>'
        '<a href="https://example.com">external</a>'
        '<a href="#frag">anchor</a>'
        "</body></html>",
        encoding="utf-8",
    )

    m = assess_wiki(tmp_path, g)
    assert m["page_count"] == 2
    # both graph nodes have pages -> coverage 1.0
    assert m["coverage"] == 1.0
    # only "missing.html" is a broken internal link (external + anchor ignored)
    assert m["broken_internal_links"] == 1
    assert m["orphan_pages"] == 0
    assert m["pages_by_type"] == {"Organism": 1, "Topic": 1}


def test_assess_wiki_orphan_and_partial_coverage(tmp_path: pathlib.Path):
    g = _small_graph()
    wiki = tmp_path / "wiki"
    wiki.mkdir()

    # cover only one of two nodes, plus one orphan page with no node.
    (wiki / f"{safe('n:org')}.html").write_text("<html></html>", encoding="utf-8")
    (wiki / "ghost.html").write_text("<html></html>", encoding="utf-8")

    m = assess_wiki(tmp_path, g)
    assert m["coverage"] == 0.5
    assert m["orphan_pages"] == 1
    assert m["broken_internal_links"] == 0

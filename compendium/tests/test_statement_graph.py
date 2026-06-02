"""Tests for transitional statement-card graph assembly."""

from __future__ import annotations

import json
from pathlib import Path

from compendium.build.statement_graph import build_statement_graph, export_statement_graph_artifacts
from compendium.models import (
    AboutRefs,
    EvidenceAnchor,
    ExtractionManifest,
    StatementCard,
    StatementLinks,
)


def _manifest() -> ExtractionManifest:
    return ExtractionManifest(
        agent_type="llm_extractor",
        skill="kg-ingest-project",
        model="test-model",
        prompt_hash="prompt:abc",
        context_pack_hash="context:def",
        repo_commit="abc123",
        timestamp="2026-06-02T00:00:00Z",
    )


def _evidence(
    *,
    project: str = "adp1_deletion_phenotypes",
    exact: str = "Carbon sources define a three-tier essentiality landscape",
) -> EvidenceAnchor:
    return EvidenceAnchor(
        source_project=project,
        source_doc="REPORT.md",
        source_section="Key Findings",
        exact=exact,
        prefix="The deletion screen showed that ",
        suffix=" across tested conditions.",
        notebook="analysis.ipynb",
        figure="fig1.png",
    )


def _card(
    card_id: str,
    *,
    statement: str,
    entities: list[str] | None = None,
    topics: list[str] | None = None,
    links: StatementLinks | None = None,
    qualifiers: dict[str, str] | None = None,
    evidence: EvidenceAnchor | None = None,
) -> StatementCard:
    return StatementCard(
        id=card_id,
        kind="finding",
        statement=statement,
        scope="project_local",
        tier="grounded",
        confidence="high",
        about=AboutRefs(
            entities=entities or ["entity:adp1"],
            topics=topics or ["topic:carbon-source-essentiality"],
        ),
        links=links or StatementLinks(),
        qualifiers=qualifiers or {"organism": "entity:adp1", "method": "RB-TnSeq"},
        evidence=evidence or _evidence(),
        extraction=_manifest(),
    )


def test_statement_cards_are_first_class_nodes() -> None:
    card = _card(
        "stmt:carbon",
        statement="Carbon sources define a three-tier essentiality landscape in ADP1.",
    )

    graph = build_statement_graph([card])

    node = _node_by_id(graph, "stmt:carbon")
    assert node["type"] == "statement_card"
    assert node["label"] == card.statement
    assert node["attrs"]["kind"] == "finding"
    assert node["attrs"]["statement"] == card.statement


def test_scientific_provenance_and_navigation_edge_classes() -> None:
    card = _card(
        "stmt:carbon",
        statement="Carbon sources define a three-tier essentiality landscape in ADP1.",
        links=StatementLinks(supports=["stmt:growth"], motivates=["stmt:opportunity"]),
    )

    graph = build_statement_graph([card])
    edges = graph["edges"]

    assert _edge(edges, "stmt:carbon", "about_entity", "entity:adp1")[
        "edge_class"
    ] == "navigation_edge"
    assert _edge(
        edges,
        "stmt:carbon",
        "member_of_topic",
        "topic:carbon-source-essentiality",
    )["edge_class"] == "navigation_edge"
    assert _edge(edges, "stmt:carbon", "supports", "stmt:growth")[
        "edge_class"
    ] == "scientific_edge"
    assert _edge(edges, "stmt:carbon", "motivates", "stmt:opportunity")[
        "edge_class"
    ] == "scientific_edge"
    assert any(
        e["s"] == "stmt:carbon"
        and e["p"] == "has_evidence"
        and e["edge_class"] == "provenance_edge"
        for e in edges
    )
    assert any(e["p"] == "uses_notebook" and e["edge_class"] == "provenance_edge" for e in edges)
    assert any(e["p"] == "cites" and e["edge_class"] == "provenance_edge" for e in edges)


def test_statement_graph_output_is_deterministic() -> None:
    first = _card(
        "stmt:a",
        statement="ADP1 growth varies by carbon source.",
        entities=["entity:z", "entity:a"],
        topics=["topic:z", "topic:a"],
        links=StatementLinks(supports=["stmt:c", "stmt:b"]),
    )
    second = _card(
        "stmt:b",
        statement="Quinate growth motivates a follow-up assay.",
        evidence=_evidence(project="acinetobacter_adp1_explorer", exact="Quinate growth was observed"),
    )

    graph_a = build_statement_graph([first, second])
    graph_b = build_statement_graph([second, first])

    assert json.dumps(graph_a, sort_keys=True) == json.dumps(graph_b, sort_keys=True)


def test_statement_graph_has_no_dangling_edge_endpoints() -> None:
    card = _card(
        "stmt:carbon",
        statement="Carbon sources define a three-tier essentiality landscape in ADP1.",
        links=StatementLinks(
            supports=["stmt:missing-support"],
            requires_validation=["stmt:missing-review-target"],
        ),
    )

    graph = build_statement_graph([card])
    node_ids = {node["id"] for node in graph["nodes"]}

    for edge in graph["edges"]:
        assert edge["s"] in node_ids
        assert edge["o"] in node_ids

    assert _node_by_id(graph, "stmt:missing-support")["type"] == "statement_reference"
    assert _node_by_id(graph, "stmt:missing-review-target")["type"] == "statement_reference"


def test_entity_ids_are_canonicalized_with_aliases_preserved() -> None:
    card = _card(
        "stmt:carbon",
        statement="ADP1 growth varies by carbon source.",
        entities=["ADP1", "entity:ADP1", "entity:adp1"],
        qualifiers={"organism": "entity:ADP1", "method": "RB-TnSeq"},
    )

    graph = build_statement_graph([card])

    assert _node_by_id(graph, "stmt:carbon")["attrs"]["about"]["entities"] == ["entity:adp1"]
    assert _node_by_id(graph, "stmt:carbon")["attrs"]["qualifiers"]["organism"] == "entity:adp1"
    assert _edge(graph["edges"], "stmt:carbon", "about_entity", "entity:adp1")

    entity = _node_by_id(graph, "entity:adp1")
    assert entity["type"] == "entity"
    assert entity["label"] == "ADP1"
    assert entity["attrs"]["canonical_id"] == "entity:adp1"
    assert entity["attrs"]["aliases"] == ["ADP1", "entity:ADP1", "entity:adp1"]
    assert entity["attrs"]["original_ids"] == ["ADP1", "entity:ADP1", "entity:adp1"]


def test_curie_like_entity_qualifiers_materialize_entity_nodes() -> None:
    card = _card(
        "stmt:carbon",
        statement="ADP1 growth varies by carbon source.",
        entities=["entity:adp1"],
        qualifiers={"organism": "NCBITaxon:62977", "method": "RB-TnSeq"},
    )

    graph = build_statement_graph([card])

    statement = _node_by_id(graph, "stmt:carbon")
    assert statement["attrs"]["qualifier_entities"] == ["entity:ncbitaxon:62977"]
    assert statement["attrs"]["qualifiers"]["organism"] == "entity:ncbitaxon:62977"
    assert statement["attrs"]["original_qualifiers"]["organism"] == "NCBITaxon:62977"

    entity = _node_by_id(graph, "entity:ncbitaxon:62977")
    assert entity["label"] == "NCBITaxon:62977"
    assert entity["attrs"]["aliases"] == ["NCBITaxon:62977"]
    assert entity["attrs"]["curies"] == ["NCBITaxon:62977"]
    assert _edge(graph["edges"], "stmt:carbon", "about_entity", "entity:ncbitaxon:62977")


def test_explicit_contradictions_materialize_conflict_review_structure() -> None:
    source = _card(
        "stmt:a",
        statement="ADP1 grows on quinate.",
        links=StatementLinks(contradicts=["stmt:b"]),
    )
    target = _card("stmt:b", statement="ADP1 does not grow on quinate.")

    graph = build_statement_graph([target, source])

    contradicts = _edge(graph["edges"], "stmt:a", "contradicts", "stmt:b")
    conflict_id = contradicts["attrs"]["conflict_id"]
    conflict = _node_by_id(graph, conflict_id)
    assert conflict["type"] == "conflict"
    assert conflict["attrs"]["kind"] == "explicit_contradiction"
    assert conflict["attrs"]["statement_ids"] == ["stmt:a", "stmt:b"]
    assert conflict["attrs"]["contradiction_links"] == [
        {
            "source_project": "adp1_deletion_phenotypes",
            "source_statement_id": "stmt:a",
            "target_statement_id": "stmt:b",
        }
    ]

    for statement_id in ("stmt:a", "stmt:b"):
        review_edge = _edge(graph["edges"], statement_id, "needs_review", conflict_id)
        assert review_edge["edge_class"] == "review_edge"
        assert review_edge["attrs"]["review_reason"] == "explicit_contradiction"


def test_statement_graph_artifacts_are_byte_stable_across_card_shuffles(tmp_path: Path) -> None:
    first = _card(
        "stmt:a",
        statement="ADP1 growth varies by carbon source.",
        entities=["entity:Z", "A"],
        topics=["topic:z", "topic:a"],
        links=StatementLinks(supports=["stmt:c", "stmt:b"], contradicts=["stmt:b"]),
        qualifiers={"organism": "NCBITaxon:62977", "method": "RB-TnSeq"},
    )
    second = _card(
        "stmt:b",
        statement="Quinate growth motivates a follow-up assay.",
        evidence=_evidence(project="acinetobacter_adp1_explorer", exact="Quinate growth was observed"),
    )

    graph_a = build_statement_graph([first, second])
    graph_b = build_statement_graph([second, first])
    graph_b["nodes"] = list(reversed(graph_b["nodes"]))
    graph_b["edges"] = list(reversed(graph_b["edges"]))

    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    export_statement_graph_artifacts(graph_a, out_a)
    export_statement_graph_artifacts(graph_b, out_b)

    for filename in ("graph.json", "nodes.tsv", "edges.tsv"):
        assert (out_a / filename).read_bytes() == (out_b / filename).read_bytes()


def test_statement_graph_artifacts_export_first_class_statement_nodes(tmp_path: Path) -> None:
    card = _card(
        "stmt:carbon",
        statement="Carbon sources define a three-tier essentiality landscape in ADP1.",
    )

    export_statement_graph_artifacts(build_statement_graph([card]), tmp_path)

    graph = json.loads((tmp_path / "graph.json").read_text(encoding="utf-8"))
    node = _node_by_id(graph, "stmt:carbon")
    assert node["type"] == "statement_card"
    assert node["label"] == card.statement

    nodes_tsv = (tmp_path / "nodes.tsv").read_text(encoding="utf-8")
    assert nodes_tsv.startswith("id\ttype\tlabel\tattrs\n")
    assert f"stmt:carbon\tstatement_card\t{card.statement}\t" in nodes_tsv


def _node_by_id(graph: dict, node_id: str) -> dict:
    return next(node for node in graph["nodes"] if node["id"] == node_id)


def _edge(edges: list[dict], source: str, predicate: str, target: str) -> dict:
    return next(edge for edge in edges if edge["s"] == source and edge["p"] == predicate and edge["o"] == target)

"""Essential tests for ContextDelivery models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from observatory_context.models import ContextItem, GraphResult, MemoryStore, RelationEdge, Scope, Tier


def test_enum_values_match_cli_contract() -> None:
    assert Tier.L0 == "L0"
    assert Scope.graph == "graph"
    assert MemoryStore.journal == "journal"


def test_context_item_defaults_are_independent() -> None:
    left = ContextItem(uri="u1", title="A", kind="note", tier=Tier.L0, content="")
    right = ContextItem(uri="u2", title="B", kind="note", tier=Tier.L0, content="")

    left.project_ids.append("p1")
    left.tags.append("tag1")

    assert right.project_ids == []
    assert right.tags == []
    assert right.source_type == "resource"


def test_context_item_rejects_invalid_source_type() -> None:
    with pytest.raises(ValidationError):
        ContextItem(
            uri="u",
            title="Bad",
            kind="note",
            tier=Tier.L0,
            content="",
            source_type="invalid",  # type: ignore[arg-type]
        )


def test_relation_edge_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        RelationEdge(
            subject_uri="viking://a",
            predicate="links_to",
            object_uri="viking://b",
            evidence="ref",
            confidence="unknown",  # type: ignore[arg-type]
        )


def test_graph_result_wraps_root_connected_and_relations() -> None:
    root = ContextItem(uri="viking://root", title="Root", kind="entity", tier=Tier.L2, content="")
    child = ContextItem(uri="viking://child", title="Child", kind="entity", tier=Tier.L2, content="")
    edge = RelationEdge(
        subject_uri=root.uri,
        predicate="links_to",
        object_uri=child.uri,
        evidence="ref",
        confidence="moderate",
    )

    result = GraphResult(root=root, connected=[child], relations=[edge])

    assert result.root.uri == root.uri
    assert [item.uri for item in result.connected] == [child.uri]
    assert [relation.object_uri for relation in result.relations] == [child.uri]

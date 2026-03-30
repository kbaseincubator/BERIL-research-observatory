"""Essential tests for knowledge-layer URI builders."""

from __future__ import annotations

import pytest

from observatory_context.uris import (
    build_entity_relations_uri,
    build_entity_uri,
    build_hypothesis_uri,
    build_knowledge_graph_uri,
    build_memory_uri,
    build_timeline_uri,
)


def test_knowledge_graph_root_uri() -> None:
    assert build_knowledge_graph_uri() == "viking://resources/observatory/knowledge-graph"


def test_entity_and_relations_uris_share_expected_layout() -> None:
    entity_uri = build_entity_uri("organism", "escherichia-coli")

    assert entity_uri == "viking://resources/observatory/knowledge-graph/entities/organisms/escherichia-coli"
    assert build_entity_relations_uri("organism", "escherichia-coli") == f"{entity_uri}/relations"


def test_hypothesis_and_timeline_uris_use_graph_namespace() -> None:
    assert build_hypothesis_uri("hyp_core_genome_fitness") == (
        "viking://resources/observatory/knowledge-graph/hypotheses/hyp_core_genome_fitness"
    )
    assert build_timeline_uri() == "viking://resources/observatory/knowledge-graph/timeline"


def test_memory_uri_uses_store_directory_and_optional_slug() -> None:
    assert build_memory_uri("journal") == "viking://resources/observatory/memories/research-journal"
    assert build_memory_uri("conversations", "session-42") == (
        "viking://resources/observatory/memories/conversations/session-42"
    )


def test_uri_builders_reject_unknown_types() -> None:
    with pytest.raises(KeyError):
        build_entity_uri("unknown", "foo")
    with pytest.raises(KeyError):
        build_memory_uri("unknown")

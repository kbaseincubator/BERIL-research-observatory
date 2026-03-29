"""Tests for knowledge-graph and memory URI builders."""

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


def test_build_knowledge_graph_uri():
    assert build_knowledge_graph_uri() == "viking://resources/observatory/knowledge-graph"


def test_build_entity_uri_organism():
    uri = build_entity_uri("organism", "escherichia-coli")
    assert uri == "viking://resources/observatory/knowledge-graph/entities/organisms/escherichia-coli"


def test_build_entity_uri_gene():
    uri = build_entity_uri("gene", "recA")
    assert uri == "viking://resources/observatory/knowledge-graph/entities/genes/recA"


def test_build_entity_uri_pathway():
    uri = build_entity_uri("pathway", "glycolysis")
    assert uri == "viking://resources/observatory/knowledge-graph/entities/pathways/glycolysis"


def test_build_entity_uri_method():
    uri = build_entity_uri("method", "rnaseq")
    assert uri == "viking://resources/observatory/knowledge-graph/entities/methods/rnaseq"


def test_build_entity_uri_concept():
    uri = build_entity_uri("concept", "fitness")
    assert uri == "viking://resources/observatory/knowledge-graph/entities/concepts/fitness"


def test_build_entity_uri_unknown_type_raises():
    with pytest.raises(KeyError):
        build_entity_uri("unknown", "foo")


def test_build_entity_relations_uri():
    uri = build_entity_relations_uri("organism", "escherichia-coli")
    assert uri == "viking://resources/observatory/knowledge-graph/entities/organisms/escherichia-coli/relations"


def test_build_hypothesis_uri():
    uri = build_hypothesis_uri("hyp_core_genome_fitness")
    assert uri == "viking://resources/observatory/knowledge-graph/hypotheses/hyp_core_genome_fitness"


def test_build_timeline_uri():
    assert build_timeline_uri() == "viking://resources/observatory/knowledge-graph/timeline"


def test_build_memory_uri_journal_no_slug():
    uri = build_memory_uri("journal")
    assert uri == "viking://resources/observatory/memories/research-journal"


def test_build_memory_uri_journal_with_slug():
    uri = build_memory_uri("journal", "2026-03-28_phage-fitness-refined")
    assert uri == "viking://resources/observatory/memories/research-journal/2026-03-28_phage-fitness-refined"


def test_build_memory_uri_patterns():
    uri = build_memory_uri("patterns")
    assert uri == "viking://resources/observatory/memories/patterns"


def test_build_memory_uri_conversations_with_slug():
    uri = build_memory_uri("conversations", "session-42")
    assert uri == "viking://resources/observatory/memories/conversations/session-42"


def test_build_memory_uri_unknown_store_raises():
    with pytest.raises(KeyError):
        build_memory_uri("unknown")

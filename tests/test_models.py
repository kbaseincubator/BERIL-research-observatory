"""Tests for ContextDelivery data models and enums."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from observatory_context.models import (
    ContextItem,
    GraphResult,
    MemoryStore,
    RelationEdge,
    Scope,
    SearchResults,
    Tier,
)


# --- Enum values ---


class TestTierEnum:
    def test_values(self) -> None:
        assert Tier.L0 == "L0"
        assert Tier.L1 == "L1"
        assert Tier.L2 == "L2"

    def test_is_str(self) -> None:
        assert isinstance(Tier.L0, str)


class TestScopeEnum:
    def test_values(self) -> None:
        assert Scope.all == "all"
        assert Scope.resources == "resources"
        assert Scope.memory == "memory"
        assert Scope.graph == "graph"


class TestMemoryStoreEnum:
    def test_values(self) -> None:
        assert MemoryStore.journal == "journal"
        assert MemoryStore.patterns == "patterns"
        assert MemoryStore.conversations == "conversations"


# --- ContextItem ---


class TestContextItem:
    def test_required_fields(self) -> None:
        item = ContextItem(
            uri="viking://projects/p1",
            title="Project One",
            kind="project",
            tier=Tier.L1,
            content="Some content",
        )
        assert item.uri == "viking://projects/p1"
        assert item.title == "Project One"
        assert item.kind == "project"
        assert item.tier == Tier.L1
        assert item.content == "Some content"

    def test_defaults(self) -> None:
        item = ContextItem(
            uri="viking://x",
            title="X",
            kind="note",
            tier=Tier.L0,
            content="",
        )
        assert item.project_ids == []
        assert item.tags == []
        assert item.source_type == "resource"
        assert item.metadata == {}

    def test_mutable_defaults_are_independent(self) -> None:
        a = ContextItem(uri="u1", title="A", kind="note", tier=Tier.L0, content="")
        b = ContextItem(uri="u2", title="B", kind="note", tier=Tier.L0, content="")
        a.project_ids.append("p1")
        assert b.project_ids == []

    def test_memory_source_type(self) -> None:
        item = ContextItem(
            uri="viking://memory/j/1",
            title="Journal Entry",
            kind="journal",
            tier=Tier.L0,
            content="Today I...",
            source_type="memory",
        )
        assert item.source_type == "memory"

    def test_invalid_source_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ContextItem(
                uri="viking://x",
                title="X",
                kind="note",
                tier=Tier.L0,
                content="",
                source_type="invalid",  # type: ignore[arg-type]
            )


# --- SearchResults ---


class TestSearchResults:
    def test_construction(self) -> None:
        item = ContextItem(
            uri="viking://x", title="X", kind="note", tier=Tier.L1, content="body"
        )
        results = SearchResults(query="test query", items=[item], total_count=1)
        assert results.query == "test query"
        assert len(results.items) == 1
        assert results.total_count == 1

    def test_empty_items(self) -> None:
        results = SearchResults(query="nothing", items=[], total_count=0)
        assert results.items == []


# --- RelationEdge ---


class TestRelationEdge:
    def test_construction(self) -> None:
        edge = RelationEdge(
            subject_uri="viking://a",
            predicate="depends_on",
            object_uri="viking://b",
            evidence="citation",
            confidence="high",
        )
        assert edge.subject_uri == "viking://a"
        assert edge.predicate == "depends_on"
        assert edge.object_uri == "viking://b"
        assert edge.evidence == "citation"
        assert edge.confidence == "high"

    def test_valid_confidence_values(self) -> None:
        for conf in ("high", "moderate", "low"):
            edge = RelationEdge(
                subject_uri="s",
                predicate="p",
                object_uri="o",
                evidence="e",
                confidence=conf,  # type: ignore[arg-type]
            )
            assert edge.confidence == conf

    def test_invalid_confidence_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RelationEdge(
                subject_uri="s",
                predicate="p",
                object_uri="o",
                evidence="e",
                confidence="unknown",  # type: ignore[arg-type]
            )


# --- GraphResult ---


class TestGraphResult:
    def _make_item(self, uri: str, title: str = "T") -> ContextItem:
        return ContextItem(uri=uri, title=title, kind="note", tier=Tier.L2, content="")

    def test_construction(self) -> None:
        root = self._make_item("viking://root")
        connected = [self._make_item("viking://a"), self._make_item("viking://b")]
        edge = RelationEdge(
            subject_uri="viking://root",
            predicate="links_to",
            object_uri="viking://a",
            evidence="ref",
            confidence="moderate",
        )
        result = GraphResult(root=root, connected=connected, relations=[edge])
        assert result.root.uri == "viking://root"
        assert len(result.connected) == 2
        assert len(result.relations) == 1

    def test_empty_connected_and_relations(self) -> None:
        root = self._make_item("viking://root")
        result = GraphResult(root=root, connected=[], relations=[])
        assert result.connected == []
        assert result.relations == []

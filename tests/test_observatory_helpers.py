"""Unit tests for helper functions targeted by the simplification refactor."""

from __future__ import annotations

import pytest

from observatory_context._text import compact_text, split_frontmatter
from observatory_context.retrieval.knowledge_index import KnowledgeEntity, KnowledgeIndex


# --- compact_text ---


class TestCompactText:
    def test_none_returns_none(self) -> None:
        assert compact_text(None) is None

    def test_empty_returns_none(self) -> None:
        assert compact_text("") is None

    def test_short_text_passes_through(self) -> None:
        assert compact_text("hello world") == "hello world"

    def test_whitespace_normalized(self) -> None:
        assert compact_text("hello   \n\t  world") == "hello world"

    def test_long_text_truncated_at_240(self) -> None:
        long_text = "a " * 200
        result = compact_text(long_text)
        assert result is not None
        assert len(result) == 240

    def test_custom_limit(self) -> None:
        result = compact_text("hello world foo bar", limit=11)
        assert result == "hello world"


# --- split_frontmatter ---


class TestSplitFrontmatter:
    def test_valid_frontmatter_parsed(self) -> None:
        content = "---\ntitle: Hello\nkind: note\n---\n\nBody text here."
        metadata, body = split_frontmatter(content, {})
        assert metadata["title"] == "Hello"
        assert metadata["kind"] == "note"
        assert body == "Body text here."

    def test_no_frontmatter_returns_content_as_body(self) -> None:
        content = "Just plain text without frontmatter."
        metadata, body = split_frontmatter(content, {"fallback": True})
        assert metadata == {"fallback": True}
        assert body == "Just plain text without frontmatter."

    def test_opening_delimiter_without_closing_does_not_crash(self) -> None:
        content = "---\ntitle: Hello\nNo closing delimiter here."
        metadata, body = split_frontmatter(content, {})
        # Should return content as-is since no closing ---
        assert body == content.strip()

    def test_fallback_metadata_preserved_and_merged(self) -> None:
        content = "---\ntitle: From FM\n---\n\nBody."
        metadata, body = split_frontmatter(content, {"existing": "value"})
        assert metadata["existing"] == "value"
        assert metadata["title"] == "From FM"


# --- _compute_enables (manifest version, dict-of-dicts) ---


class TestComputeEnablesManifest:
    def test_populates_enables_from_depends_on(self) -> None:
        from observatory_context.ingest.manifest import _compute_enables

        entries = {
            "alpha": {"id": "alpha", "depends_on": ["beta"]},
            "beta": {"id": "beta", "depends_on": []},
            "gamma": {"id": "gamma", "depends_on": ["beta"]},
        }
        _compute_enables(entries)

        assert entries["beta"]["enables"] == ["alpha", "gamma"]
        assert entries["alpha"]["enables"] == []
        assert entries["gamma"]["enables"] == []

    def test_missing_dependency_is_silently_skipped(self) -> None:
        from observatory_context.ingest.manifest import _compute_enables

        entries = {
            "alpha": {"id": "alpha", "depends_on": ["nonexistent"]},
        }
        _compute_enables(entries)
        assert entries["alpha"]["enables"] == []


# --- _compute_enables (exports version, list-of-dicts) ---


class TestComputeEnablesExports:
    def test_populates_enables_from_depends_on(self) -> None:
        from observatory_context.materialize.exports import _compute_enables

        projects = [
            {"id": "alpha", "depends_on": ["beta"], "enables": []},
            {"id": "beta", "depends_on": [], "enables": []},
            {"id": "gamma", "depends_on": ["beta"], "enables": []},
        ]
        _compute_enables(projects)

        assert projects[1]["enables"] == ["alpha", "gamma"]
        assert projects[0]["enables"] == []


# --- parse_live_resource ---


class TestParseLiveResource:
    def test_parses_valid_frontmatter(self) -> None:
        from observatory_context.notes.store import parse_live_resource

        content = "---\nid: note-1\nkind: note\ntitle: Test\n---\n\nBody text."
        result = parse_live_resource("viking://test", content)

        assert result["id"] == "note-1"
        assert result["kind"] == "note"
        assert result["title"] == "Test"
        assert result["body"] == "Body text."

    def test_uses_fallback_metadata(self) -> None:
        from observatory_context.notes.store import parse_live_resource

        content = "No frontmatter here."
        result = parse_live_resource(
            "viking://test",
            content,
            fallback_metadata={"id": "fb-1", "kind": "note", "title": "Fallback"},
        )

        assert result["id"] == "fb-1"
        assert result["kind"] == "note"


# --- KnowledgeIndex init ---


class TestKnowledgeIndexInit:
    @pytest.fixture
    def sample_index(self) -> KnowledgeIndex:
        entities = {
            "org_a": KnowledgeEntity(
                id="org_a", name="Org A", kind="organism",
                projects=frozenset(["proj1", "proj2"]),
            ),
            "gene_b": KnowledgeEntity(
                id="gene_b", name="Gene B", kind="gene",
                projects=frozenset(["proj1"]),
            ),
            "conc_c": KnowledgeEntity(
                id="conc_c", name="Concept C", kind="concept",
                projects=frozenset(["proj2"]),
            ),
        }
        return KnowledgeIndex(entities=entities, relations=[])

    def test_entities_by_kind(self, sample_index: KnowledgeIndex) -> None:
        organisms = sample_index.list_entities(kind="organism")
        assert len(organisms) == 1
        assert organisms[0].id == "org_a"

        genes = sample_index.list_entities(kind="gene")
        assert len(genes) == 1

    def test_project_to_entities(self, sample_index: KnowledgeIndex) -> None:
        entities = sample_index.entities_for_project("proj1")
        assert entities == {"org_a", "gene_b"}

        entities = sample_index.entities_for_project("proj2")
        assert entities == {"org_a", "conc_c"}

    def test_entity_to_projects(self, sample_index: KnowledgeIndex) -> None:
        projects = sample_index.projects_for_entity("org_a")
        assert projects == {"proj1", "proj2"}

        projects = sample_index.projects_for_entity("gene_b")
        assert projects == {"proj1"}

    def test_unknown_entity_returns_empty(self, sample_index: KnowledgeIndex) -> None:
        assert sample_index.projects_for_entity("nonexistent") == set()
        assert sample_index.entities_for_project("nonexistent") == set()

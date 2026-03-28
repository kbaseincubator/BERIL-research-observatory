"""Unit tests for helper functions targeted by the simplification refactor."""

from __future__ import annotations

from observatory_context._text import compact_text, split_frontmatter


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


class TestComputeEnables:
    def test_populates_enables_from_depends_on(self) -> None:
        from observatory_context._graph import compute_enables

        projects = [
            {"id": "alpha", "depends_on": ["beta"]},
            {"id": "beta", "depends_on": []},
            {"id": "gamma", "depends_on": ["beta"]},
        ]
        compute_enables(projects)

        assert projects[1]["enables"] == ["alpha", "gamma"]
        assert projects[0]["enables"] == []
        assert projects[2]["enables"] == []

    def test_missing_dependency_is_silently_skipped(self) -> None:
        from observatory_context._graph import compute_enables

        projects = [{"id": "alpha", "depends_on": ["nonexistent"]}]
        compute_enables(projects)
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



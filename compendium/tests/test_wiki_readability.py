"""Smoke tests for the committed human-facing wiki."""

from __future__ import annotations

from pathlib import Path

WIKI = Path(__file__).resolve().parents[1] / "wiki"
FORBIDDEN_GRAPH_TERMS = ("curie", "biolink", "edge_class", "node_id")


def _markdown_pages() -> list[Path]:
    if not WIKI.exists():
        return []
    return sorted(path for path in WIKI.rglob("*.md") if ".manifests" not in path.parts)


def test_committed_wiki_pages_have_sources() -> None:
    pages = _markdown_pages()
    assert pages
    for page in pages:
        text = page.read_text(encoding="utf-8")
        assert "## Sources" in text or page.name == "index.md"


def test_committed_wiki_pages_do_not_expose_graph_jargon() -> None:
    for page in _markdown_pages():
        text = page.read_text(encoding="utf-8").lower()
        assert not any(term in text for term in FORBIDDEN_GRAPH_TERMS), page


def test_topic_pages_have_introductions_and_connections() -> None:
    topic_dir = WIKI / "topics"
    topic_pages = sorted(topic_dir.glob("*.md")) if topic_dir.exists() else []
    assert topic_pages
    for page in topic_pages:
        text = page.read_text(encoding="utf-8")
        assert "## Overview" in text
        assert "## Connections" in text or "## Adjacent topics" in text
        before_sources = text.split("## Sources", 1)[0]
        assert before_sources.count("[") >= 2

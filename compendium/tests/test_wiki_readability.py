"""Smoke tests for the committed human-facing wiki."""

from __future__ import annotations

import re
from pathlib import Path

WIKI = Path(__file__).resolve().parents[1] / "wiki"
FORBIDDEN_GRAPH_TERMS = ("curie", "biolink", "edge_class", "node_id")


def _markdown_pages() -> list[Path]:
    if not WIKI.exists():
        return []
    return sorted(path for path in WIKI.rglob("*.md") if ".manifests" not in path.parts)


def test_committed_wiki_pages_have_provenance() -> None:
    pages = _markdown_pages()
    assert pages
    for page in pages:
        # Home is an intro map; project pages are stubs (Key findings, no citations).
        if page.name == "index.md" or page.parent.name == "projects":
            continue
        text = page.read_text(encoding="utf-8")
        assert "## Sources" in text or "## References" in text, page


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
        body = re.split(r"## (?:Sources|References)", text, maxsplit=1)[0]
        assert body.count("[") >= 2

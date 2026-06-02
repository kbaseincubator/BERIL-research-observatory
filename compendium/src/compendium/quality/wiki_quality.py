"""Deterministic quality metrics for the rendered wiki site.

No LLM, no network — pure functions over a site directory and the canonical
:class:`compendium.models.Graph`. HTML is parsed with stdlib only.
"""

from __future__ import annotations

import pathlib
from html.parser import HTMLParser
from urllib.parse import urldefrag, urlparse

from ..models import Graph


def safe(node_id: str) -> str:
    """Filesystem-safe page stem for a node id (``':'`` and ``'/'`` -> ``'_'``)."""
    return node_id.replace(":", "_").replace("/", "_")


class _HrefParser(HTMLParser):
    """Collect ``href`` targets from ``<a>`` tags."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


def _extract_hrefs(html: str) -> list[str]:
    parser = _HrefParser()
    parser.feed(html)
    return parser.hrefs


def _is_internal(href: str) -> bool:
    """True for same-site relative links (skip external/anchor/special schemes)."""
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        return False
    target = urldefrag(href)[0]
    return bool(target)


def assess_wiki(site_dir: pathlib.Path, graph: Graph) -> dict:
    """Compute coverage / link-integrity metrics for a rendered wiki.

    Parameters
    ----------
    site_dir
        Root of the rendered site (pages live under ``wiki/<safe(id)>.html``).
    graph
        The canonical graph the wiki was rendered from.

    Returns
    -------
    dict
        Metrics keyed by name (see module/design spec).
    """
    site_dir = pathlib.Path(site_dir)
    wiki_dir = site_dir / "wiki"

    html_files = sorted(wiki_dir.glob("*.html")) if wiki_dir.is_dir() else []
    page_stems = {p.stem for p in html_files}

    # coverage: fraction of graph nodes that have a wiki page.
    node_stems = {safe(n.id) for n in graph.nodes}
    covered = sum(1 for stem in node_stems if stem in page_stems)
    coverage = covered / len(node_stems) if node_stems else 0.0

    # pages_by_type: count pages by the type of the node they represent.
    stem_to_type = {safe(n.id): n.type for n in graph.nodes}
    stem_to_tier = {safe(n.id): n.tier for n in graph.nodes}
    pages_by_type: dict[str, int] = {}
    pages_by_tier: dict[str, int] = {}
    for stem in page_stems:
        node_type = stem_to_type.get(stem, "Unknown")
        pages_by_type[node_type] = pages_by_type.get(node_type, 0) + 1
        node_tier = stem_to_tier.get(stem, "Unknown")
        pages_by_tier[node_tier] = pages_by_tier.get(node_tier, 0) + 1

    # orphan_pages: rendered html files with no corresponding graph node.
    orphan_pages = sum(1 for stem in page_stems if stem not in node_stems)

    # broken_internal_links: internal hrefs whose target file is missing under site_dir.
    broken_internal_links = 0
    pages_with_provenance = 0
    for page in html_files:
        html = page.read_text(encoding="utf-8")
        if "Provenance" in html and "projects:" in html:
            pages_with_provenance += 1
        for href in _extract_hrefs(html):
            if not _is_internal(href):
                continue
            target = urldefrag(href)[0]
            resolved = (page.parent / target).resolve()
            if not resolved.exists():
                broken_internal_links += 1

    return {
        "page_count": len(html_files),
        "pages_by_type": pages_by_type,
        "pages_by_tier": pages_by_tier,
        "coverage": coverage,
        "broken_internal_links": broken_internal_links,
        "orphan_pages": orphan_pages,
        "provenance_section_rate": pages_with_provenance / len(html_files) if html_files else 0.0,
    }

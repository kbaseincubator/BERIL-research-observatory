"""Deterministic Cosma export: the reader graph (home/topic/project/data/author).

Sibling of ``render/markdown.py``. ``render-markdown`` publishes the human-readable wiki;
``export-cosma`` turns the same authored pages into a Cosma project (records + config) that
``cosma modelize`` renders into a single self-contained ``cosmoscope.html`` — an interactive
graph beside the readable wiki. No LLM, no network; same inputs ⇒ byte-identical output.

Each published wiki page becomes one Cosma record. Project pages are real wiki pages now, so
project nodes come straight from those records; the cross-page links the pages carry (navigation,
inline-citation references, and project mentions) are rewritten from ``[label](rel.md)`` into
``[[Target Title|label]]`` wikilinks, which Cosma reads as graph edges.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import posixpath
import re

import yaml

from compendium.models import PagePlan
from compendium.pages.artifact import wiki_page_path

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+?\.md)(#[^)]*)?\)")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class CosmaRecord:
    """One Cosma record (graph node): a Markdown file with frontmatter + wikilinked body."""

    filename: str
    title: str
    type: str
    body: str

    def to_markdown(self) -> str:
        front = f"---\ntitle: {self.title}\ntype: {self.type}\n---\n\n"
        return front + self.body.rstrip() + "\n"


def build_cosma_records(
    page_plans: list[PagePlan],
    *,
    page_markdown: dict[str, str],
) -> list[CosmaRecord]:
    """Build the sorted Cosma records (one per published page) for the reader graph.

    Cosma derives a node id from each record's title, so two pages whose titles slugify to the same
    id (e.g. the ``Functional Dark Matter`` topic and the project of the same name) would collide and
    one node would be dropped. Project records that collide are suffixed with `` (project)`` — and
    the disambiguated title is used everywhere, so inbound wikilinks still resolve.
    """
    present = [plan for plan in page_plans if plan.id in page_markdown]
    page_path = {plan.id: wiki_page_path(plan).as_posix() for plan in present}
    natural_title = {plan.id: (_h1(page_markdown[plan.id]) or plan.title) for plan in present}

    slug_counts = Counter(_title_slug(title) for title in natural_title.values())
    title = {}
    for plan in present:
        value = natural_title[plan.id]
        if plan.type == "project" and slug_counts[_title_slug(value)] > 1:
            value = f"{value} (project)"
        title[plan.id] = value

    title_by_path = {page_path[plan.id]: title[plan.id] for plan in present}
    records = []
    for plan in present:
        body = _H1_RE.sub("", page_markdown[plan.id], count=1).lstrip()
        body = _rewrite_links(body, page_path[plan.id], title_by_path)
        records.append(
            CosmaRecord(filename=_flat(page_path[plan.id]), title=title[plan.id], type=plan.type, body=body)
        )
    return sorted(records, key=lambda record: record.filename)


def write_cosma_project(
    page_plans: list[PagePlan],
    *,
    wiki_dir: str | Path,
    out_dir: str | Path,
    title: str = "Compendium",
    description: str = "",
) -> list[Path]:
    """Read the authored wiki and write a Cosma project (``src/*.md`` + ``config.yml``).

    Reads each planned page's published Markdown from ``wiki_dir``, builds the Cosma records,
    and writes them under ``out_dir/src`` with a generated ``out_dir/config.yml``. Stale
    ``src/*.md`` are removed first so regeneration is clean. ``cosma modelize`` (run separately)
    turns this into the cosmoscope.
    """
    wiki_path = Path(wiki_dir)
    page_markdown = {
        plan.id: (wiki_path / wiki_page_path(plan)).read_text(encoding="utf-8")
        for plan in page_plans
        if (wiki_path / wiki_page_path(plan)).is_file()
    }
    records = build_cosma_records(page_plans, page_markdown=page_markdown)

    out_path = Path(out_dir)
    src_dir = out_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    for stale in src_dir.glob("*.md"):
        stale.unlink()

    written: list[Path] = []
    for record in records:
        record_path = src_dir / record.filename
        record_path.write_text(record.to_markdown(), encoding="utf-8")
        written.append(record_path)

    config_path = out_path / "config.yml"
    config_path.write_text(
        yaml.safe_dump(cosma_config(title=title, description=description), sort_keys=False),
        encoding="utf-8",
    )
    written.append(config_path)
    return written


def cosma_config(*, title: str, description: str = "") -> dict:
    """Return the generated Cosma ``config.yml`` content (light theme, typed record colors)."""
    description = description or f"Reader graph for {title}: topics, projects, shared data, authors."
    return {
        "select_origin": "directory",
        "files_origin": "./src",
        "export_target": "./",
        "history": False,
        "focus_max": 1,
        "record_types": {
            "home": {"fill": "#b478ff", "stroke": "#b478ff"},
            "topic": {"fill": "#5b8cff", "stroke": "#5b8cff"},
            "project": {"fill": "#8a94a6", "stroke": "#8a94a6"},
            "data": {"fill": "#37b98b", "stroke": "#37b98b"},
            "author": {"fill": "#e0883b", "stroke": "#e0883b"},
        },
        "link_types": {"undefined": {"stroke": "simple", "color": "#96a5be"}},
        "graph_background_color": "#ffffff",
        "graph_highlight_color": "#ff6a6a",
        "graph_text_size": 11,
        "node_size_method": "degree",
        "generate_id": "always",
        "title": title,
        "description": description,
        "lang": "en",
    }


def _rewrite_links(body: str, page_path: str, title_by_path: dict[str, str]) -> str:
    page_dir = posixpath.dirname(page_path)

    def repl(match: re.Match) -> str:
        label, target = match.group(1), match.group(2)
        resolved = posixpath.normpath(posixpath.join(page_dir, target))
        title = title_by_path.get(resolved)
        # A link to another wiki page becomes a graph edge; an external link (e.g. the source
        # REPORT.md outside the wiki tree) is left as a plain Markdown link, not flattened to text.
        return f"[[{title}|{label}]]" if title else match.group(0)

    return _LINK_RE.sub(repl, body)


def _flat(path: str) -> str:
    return path[:-3].replace("/", "_") + ".md" if path.endswith(".md") else path.replace("/", "_")


def _h1(markdown: str) -> str | None:
    match = _H1_RE.search(markdown)
    return match.group(1).strip() if match else None


def _title_slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

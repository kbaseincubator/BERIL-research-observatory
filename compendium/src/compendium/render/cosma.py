"""Deterministic Cosma export: the reader graph (topic/project/data/author) as Cosma records.

Sibling of ``render/markdown.py``. ``render-markdown`` publishes the human-readable wiki;
``export-cosma`` turns the same inputs into a Cosma project (records + config) that
``cosma modelize`` renders into a single self-contained ``cosmoscope.html`` — an interactive
graph beside the readable wiki. No LLM, no network; same inputs ⇒ byte-identical output.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import posixpath
import re

import yaml

from compendium.models import PagePlan, StatementCard
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
    cards: list[StatementCard],
    registry,
    authors: dict,
    collections: dict,
    page_markdown: dict[str, str],
) -> list[CosmaRecord]:
    """Build the sorted Cosma records for the reader graph.

    Page records reuse the authored wiki prose (``page_markdown`` keyed by page id), converting
    ``[label](rel.md)`` cross-links into ``[[Target Title|label]]`` wikilinks. ``registry``,
    ``cards``, ``authors`` and ``collections`` add project-stub nodes wired to their pages.
    """
    page_path = {plan.id: wiki_page_path(plan).as_posix() for plan in page_plans}
    title_by_id = {
        plan.id: _h1(page_markdown[plan.id]) or plan.title
        for plan in page_plans
        if plan.id in page_markdown
    }
    title_by_path = {page_path[pid]: title for pid, title in title_by_id.items()}

    records: list[CosmaRecord] = []
    for plan in page_plans:
        if plan.id not in page_markdown:
            continue
        records.append(
            _page_record(plan, page_markdown[plan.id], page_path[plan.id], title_by_path)
        )

    page_titles = dict(title_by_id)
    project_links = _project_links(cards, registry, authors, collections, set(page_titles))
    for project_id, target_ids in project_links.items():
        records.append(_project_record(project_id, target_ids, page_titles))

    return sorted(records, key=lambda r: r.filename)


def write_cosma_project(
    page_plans: list[PagePlan],
    *,
    cards: list[StatementCard],
    registry,
    authors: dict,
    collections: dict,
    wiki_dir: str | Path,
    out_dir: str | Path,
    title: str = "Compendium",
    description: str = "",
) -> list[Path]:
    """Read the authored wiki and write a Cosma project (``src/*.md`` + ``config.yml``).

    Reads each planned page's published Markdown from ``wiki_dir``, builds the Cosma records
    (page nodes + project stubs), and writes them under ``out_dir/src`` with a generated
    ``out_dir/config.yml``. Stale ``src/*.md`` are removed first so regeneration is clean.
    Returns the paths written. ``cosma modelize`` (run separately) turns this into the cosmoscope.
    """
    wiki_path = Path(wiki_dir)
    page_markdown = {
        plan.id: (wiki_path / wiki_page_path(plan)).read_text(encoding="utf-8")
        for plan in page_plans
        if (wiki_path / wiki_page_path(plan)).is_file()
    }
    records = build_cosma_records(
        page_plans,
        cards=cards,
        registry=registry,
        authors=authors,
        collections=collections,
        page_markdown=page_markdown,
    )

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


def _project_links(
    cards: list[StatementCard],
    registry,
    authors: dict,
    collections: dict,
    page_ids: set[str],
) -> dict[str, set[str]]:
    """Map each project (present among the cards) to the page ids it belongs to.

    Mirrors the planner's joins: project→topic from canonical card topics, project→author from
    the ORCID author index, project→data from the shared-collection index. Only targets that are
    real pages (have markdown) are kept, so the wikilinks always resolve.
    """
    links: dict[str, set[str]] = {card.evidence[0].source_project: set() for card in cards}

    for card in cards:
        project = card.evidence[0].source_project
        for topic in card.topics:
            key = registry.topic_key(topic) if registry is not None else topic
            if key in page_ids:
                links[project].add(key)

    for record in authors.values():
        author_page = f"author:{_slug(record.orcid or record.name)}"
        if author_page in page_ids:
            for project in record.projects:
                if project in links:
                    links[project].add(author_page)

    for record in collections.values():
        data_page = f"data:{record.id}"
        if data_page in page_ids:
            for project in record.projects:
                if project in links:
                    links[project].add(data_page)

    return dict(sorted(links.items()))


def _project_record(project_id: str, target_ids: set[str], page_titles: dict[str, str]) -> CosmaRecord:
    title = _titleize(project_id)
    related = sorted((page_titles[pid] for pid in target_ids), key=str.casefold)
    bullets = "\n".join(f"- [[{name}]]" for name in related)
    body = f"Project node for **{title}**, linked to its topics, authors, and shared data.\n"
    if bullets:
        body += f"\n## Related\n\n{bullets}\n"
    return CosmaRecord(filename=f"project_{project_id}.md", title=title, type="project", body=body)


def _page_record(
    plan: PagePlan, markdown: str, path: str, title_by_path: dict[str, str]
) -> CosmaRecord:
    title = _h1(markdown) or plan.title
    body = _H1_RE.sub("", markdown, count=1).lstrip()
    body = _rewrite_links(body, path, title_by_path)
    return CosmaRecord(filename=_flat(path), title=title, type=plan.type, body=body)


def _rewrite_links(body: str, page_path: str, title_by_path: dict[str, str]) -> str:
    page_dir = posixpath.dirname(page_path)

    def repl(match: re.Match) -> str:
        label, target = match.group(1), match.group(2)
        resolved = posixpath.normpath(posixpath.join(page_dir, target))
        title = title_by_path.get(resolved)
        return f"[[{title}|{label}]]" if title else label

    return _LINK_RE.sub(repl, body)


def _flat(path: str) -> str:
    return path[:-3].replace("/", "_") + ".md" if path.endswith(".md") else path.replace("/", "_")


def _h1(markdown: str) -> str | None:
    match = _H1_RE.search(markdown)
    return match.group(1).strip() if match else None


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"


def _titleize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()

"""Page context and authored Markdown artifacts for kg-synthesize-page."""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
import posixpath
import re
from typing import Any

from compendium import ids
from compendium.models import PagePlan, StatementCard
from compendium.pages.citations import (
    clean_project_lead,
    link_project_mentions,
    normalize_page_links,
    render_inline_citations,
)
from compendium.pages.project_page import build_project_page
from compendium.pages.reflow import reflow_paragraphs

_PAGE_DIRS = {"topic": "topics", "data": "data", "author": "authors", "project": "projects"}


def page_artifact_path(plan: PagePlan) -> Path:
    """Return the stable manifest/context path for a generated page artifact."""
    if plan.id == "home" or plan.type == "home":
        return Path("home.md")
    stem = _slug(plan.id.split(":", 1)[1] if ":" in plan.id else plan.id)
    directory = _PAGE_DIRS.get(plan.type, f"{_slug(plan.type)}s")
    return Path(directory) / f"{stem}.md"


def wiki_page_path(plan: PagePlan) -> Path:
    """Return the published wiki path for a page plan."""
    if plan.id == "home" or plan.type == "home":
        return Path("index.md")
    return page_artifact_path(plan)


def page_manifest_path(plan: PagePlan) -> Path:
    """Return the manifest path inside the human-facing wiki directory."""
    return Path(".manifests") / page_artifact_path(plan).with_suffix(".manifest.json")


def build_page_context(
    plan: PagePlan,
    cards: list[StatementCard],
    *,
    page_plans: list[PagePlan],
    registry=None,
    source_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the deterministic bounded context an LLM should use for one page."""
    card_by_id = {card.id: card for card in cards}
    page_paths = {item.id: wiki_page_path(item).as_posix() for item in page_plans}
    member_cards = [
        card_by_id[statement_id]
        for statement_id in plan.member_statement_ids
        if statement_id in card_by_id
    ]
    statements = [_statement_context(card, source_root) for card in member_cards]
    return {
        "page": {
            **plan.to_dict(),
            "wiki_path": wiki_page_path(plan).as_posix(),
            "manifest_path": page_manifest_path(plan).as_posix(),
        },
        "statements": statements,
        "projects": _projects(statements),
        "topics": _topics(member_cards, registry),
        "entities": _entities(member_cards, registry),
        "authors": [],
        "data_collections": [],
        "adjacent_pages": _page_refs(plan.outgoing_links, page_paths),
        "allowed_citations": _allowed_citations(member_cards),
        "narrative": _narrative(plan, registry),
        "instructions": {
            "audience": "scientist-engineer new to this specific niche",
            "style": "human-readable Obsidian-style synthesis page",
            "body_rule": "synthesize across statements; do not emit statement-by-statement summaries",
            "citations": (
                "Place each allowed [stmt:id; project] citation inline, right after the clause it "
                "supports. Do not write a Sources or References section — it is generated for you."
            ),
        },
    }


def write_page_context(
    plan: PagePlan,
    cards: list[StatementCard],
    out_dir: Path,
    *,
    page_plans: list[PagePlan],
    statement_graph: dict[str, list[dict[str, Any]]] | None = None,
    source_root: str | Path | None = None,
) -> tuple[Path, Path]:
    """Write one page context JSON and prompt Markdown for LLM synthesis."""
    context = build_page_context(
        plan,
        cards,
        page_plans=page_plans,
        source_root=source_root,
    )
    context_path = Path(out_dir) / page_artifact_path(plan).with_suffix(".context.json")
    prompt_path = Path(out_dir) / page_artifact_path(plan).with_suffix(".prompt.md")
    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(
        json.dumps(context, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prompt_path.write_text(_prompt(context), encoding="utf-8")
    return context_path, prompt_path


def write_page_artifact(
    plan: PagePlan,
    cards: list[StatementCard],
    out_dir: Path,
    *,
    markdown: str,
    model: str,
    prompt_hash: str,
    page_plans: list[PagePlan] | None = None,
    repo_commit: str = "",
    timestamp: str = "",
) -> tuple[Path, Path]:
    """Publish an authored Markdown page (with provenance transforms) plus its manifest.

    For non-project pages the authored draft carries inline ``[stmt:id; project]`` tokens and
    ```project``` mentions; these are rewritten into numbered references and project links here.
    For project pages the draft is just the short lead, and the structured stub is assembled
    deterministically around it.
    """
    card_by_id = {card.id: card for card in cards}
    member_ids = [sid for sid in plan.member_statement_ids if sid in card_by_id]
    page_path = wiki_page_path(plan).as_posix()
    known_projects = {card.evidence[0].source_project for card in cards}

    if plan.type == "project":
        published, cited_statement_ids = _project_markdown(
            plan,
            cards,
            member_ids,
            lead=markdown,
            page_plans=page_plans or [],
            page_path=page_path,
            known_projects=known_projects,
        )
    else:
        known_paths = {wiki_page_path(item).as_posix() for item in (page_plans or [])}
        body = normalize_page_links(markdown, page_path=page_path, known_paths=known_paths)
        body = link_project_mentions(body, known_projects, page_path=page_path)
        published, cited_statement_ids = render_inline_citations(
            body, card_by_id, page_path=page_path, member_ids=set(member_ids)
        )

    manifest = _manifest(
        plan,
        cited_statement_ids,
        model=model,
        prompt_hash=prompt_hash,
        repo_commit=repo_commit,
        timestamp=timestamp,
    )
    markdown_path = Path(out_dir) / wiki_page_path(plan)
    manifest_path = Path(out_dir) / page_manifest_path(plan)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(reflow_paragraphs(published), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return markdown_path, manifest_path


def _project_markdown(
    plan: PagePlan,
    cards: list[StatementCard],
    member_ids: list[str],
    *,
    lead: str,
    page_plans: list[PagePlan],
    page_path: str,
    known_projects: set[str],
) -> tuple[str, list[str]]:
    """Assemble a project page (deterministic stub + injected lead)."""
    card_by_id = {card.id: card for card in cards}
    findings = [(card_by_id[sid].text, card_by_id[sid].confidence) for sid in member_ids]

    plan_by_id = {item.id: item for item in page_plans}
    page_dir = posixpath.dirname(page_path) or "."
    grouped: dict[str, list[tuple[str, str]]] = {"topic": [], "data": [], "author": []}
    for target_id in plan.outgoing_links:
        target = plan_by_id.get(target_id)
        if target is None or target.type not in grouped:
            continue
        rel = posixpath.relpath(wiki_page_path(target).as_posix(), page_dir)
        grouped[target.type].append((target.title, rel))
    for items in grouped.values():
        items.sort()

    project_id = plan.id.split(":", 1)[1] if ":" in plan.id else plan.id
    clean_lead = link_project_mentions(clean_project_lead(lead), known_projects, page_path=page_path)
    markdown = build_project_page(
        title=plan.title,
        lead=clean_lead,
        findings=findings,
        topics=grouped["topic"],
        data=grouped["data"],
        authors=grouped["author"],
        report_link=_report_relpath(project_id),
    )
    return markdown, list(member_ids)


def _report_relpath(project_id: str) -> str:
    """Relative link from a ``projects/<slug>.md`` page to the source ``REPORT.md``.

    The published wiki lives at ``compendium/wiki/`` while the source corpus lives at
    ``<root>/projects/`` (one level above ``compendium``), so a depth-1 project page reaches
    its report via three parent hops.
    """
    return f"../../../projects/{project_id}/REPORT.md"


def _statement_context(
    card: StatementCard,
    source_root: str | Path | None,
) -> dict[str, Any]:
    evidence = card.evidence[0]
    return {
        "id": card.id,
        "kind": card.kind,
        "confidence": card.confidence,
        "text": card.text,
        "topics": list(card.topics),
        "entities": list(card.entities),
        "links": card.links.to_dict(),
        "evidence": [anchor.to_dict() for anchor in card.evidence],
        "source_excerpt": _source_excerpt(evidence.to_dict(), source_root),
    }


def _source_excerpt(
    evidence: dict[str, Any],
    source_root: str | Path | None,
    *,
    radius: int = 600,
) -> str:
    if source_root is None:
        return ""
    source_path = Path(source_root) / evidence["source_project"] / evidence["source_doc"]
    if not source_path.is_file():
        return ""
    text = source_path.read_text(encoding="utf-8", errors="replace")
    quote = evidence["quote"]
    index = text.find(quote)
    if index < 0:
        return quote
    start = max(0, index - radius)
    end = min(len(text), index + len(quote) + radius)
    return text[start:end].strip()


def _page_refs(page_ids: Iterable[str], page_paths: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"id": page_id, "title": _title(page_id), "path": page_paths[page_id]}
        for page_id in sorted(set(page_ids))
        if page_id in page_paths
    ]


def _prompt(context: dict[str, Any]) -> str:
    page = context["page"]
    if page["type"] == "project":
        return "\n".join(
            [
                f"# Write Project Lead: {page['title']}",
                "",
                "Use the adjacent `.context.json` as the only allowed scientific context.",
                "",
                "Write ONLY a 2-3 sentence plain-language lead: what this project set out to do and",
                "its single most important result. Do not add headings, a findings list, or links —",
                "the key-findings list, navigation links, and report link are generated for you.",
                "",
            ]
        )
    return "\n".join(
        [
            f"# Write Wiki Page: {page['title']}",
            "",
            "Use the adjacent `.context.json` as the only allowed scientific context.",
            "",
            "Requirements:",
            "- Write synthesized prose, not a statement-by-statement summary.",
            "- Follow `narrative.section_plan` unless it would create an empty section.",
            "- Include Markdown links to related wiki pages using `adjacent_pages` paths.",
            "- Cite only ids in `allowed_citations`, placing each `[stmt:id; project]` inline right",
            "  after the clause it supports.",
            "- Use source excerpts from `projects/` to improve readability and scientific framing.",
            "- Do not write a Sources or References section — it is generated from your inline citations.",
            "",
            "Suggested shape:",
            "- `# <page title>`",
            "- `## Overview`",
            "- narrative sections from `narrative.section_plan`, with inline citations",
            "",
        ]
    )


def _manifest(
    plan: PagePlan,
    cited_statement_ids: list[str],
    *,
    model: str,
    prompt_hash: str,
    repo_commit: str,
    timestamp: str,
) -> dict[str, Any]:
    plan_payload = json.dumps(plan.to_dict(), sort_keys=True, separators=(",", ":"))
    return {
        "skill": "kg-synthesize-page",
        "model": model,
        "prompt_hash": prompt_hash,
        "page_id": plan.id,
        "page_type": plan.type,
        "page_plan_hash": "hash:" + ids.content_hash(plan_payload, n=16),
        "member_hash": plan.member_hash,
        "section_hashes": {
            section.id: section.member_hash
            for section in sorted(plan.sections, key=lambda item: item.id)
        },
        "cited_statement_ids": cited_statement_ids,
        "repo_commit": repo_commit,
        "timestamp": timestamp,
    }


def _title(page_id: str) -> str:
    value = page_id.split(":", 1)[1] if ":" in page_id else page_id
    return value.replace("_", " ").replace("-", " ").title()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"


def _projects(statements: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            evidence["source_project"]
            for statement in statements
            for evidence in statement["evidence"]
        }
    )


def _topics(cards: list[StatementCard], registry) -> list[dict[str, str]]:
    topic_ids = sorted({topic for card in cards for topic in card.topics})
    return [_registry_record(topic_id, registry, "topics") for topic_id in topic_ids]


def _entities(cards: list[StatementCard], registry) -> list[dict[str, str]]:
    entity_ids = sorted({entity for card in cards for entity in card.entities})
    return [_registry_record(entity_id, registry, "entities") for entity_id in entity_ids]


def _registry_record(raw_id: str, registry, collection: str) -> dict[str, str]:
    key = raw_id
    if registry is not None:
        key = registry.topic_key(raw_id) if collection == "topics" else registry.entity_key(raw_id)
    record = getattr(registry, collection, {}).get(key, {}) if registry is not None else {}
    return {
        "id": key,
        "label": record.get("label", _title(key)),
        "definition": record.get("definition", ""),
        "kind": record.get("kind", ""),
        "url": record.get("url", ""),
    }


def _allowed_citations(cards: list[StatementCard]) -> list[dict[str, str]]:
    return [
        {"statement_id": card.id, "source_project": card.evidence[0].source_project}
        for card in sorted(cards, key=lambda item: item.id)
    ]


def _narrative(plan: PagePlan, registry) -> dict[str, Any]:
    return {
        "lead": _lead(plan, registry),
        "section_plan": [
            {"id": section.id, "heading": section.heading}
            for section in plan.sections
        ],
    }


def _lead(plan: PagePlan, registry) -> str:
    if plan.type == "topic" and registry is not None:
        record = registry.topics.get(registry.topic_key(plan.id), {})
        if record.get("definition"):
            return record["definition"]
    if plan.type == "data":
        return "Explain what this shared data collection is and why it connects these projects."
    if plan.type == "project":
        return "In 2-3 sentences, say what this project set out to do and its most important result."
    if plan.type == "author":
        return "Summarize this contributor's project and topic footprint using only the page context."
    if plan.type == "home":
        return "Introduce the synthesis wiki as a map of cross-project topics, shared data, and authors."
    return "Introduce the page subject and explain why it matters in this synthesis wiki."

"""Page context and authored Markdown artifacts for kg-synthesize-page."""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
import re
from typing import Any

from compendium import ids
from compendium.models import PagePlan, StatementCard

_PAGE_DIRS = {
    "topic": "topics",
    "claim": "claims",
    "conflict": "conflicts",
    "opportunity": "opportunities",
    "direction": "directions",
    "hypothesis": "hypotheses",
    "project": "projects",
    "entity": "entities",
}
_CITATION_RE = re.compile(r"\[(stmt:[^;\]\s]+);[^\]]+\]")


def page_artifact_path(plan: PagePlan) -> Path:
    """Return the authored Markdown path for a generated page artifact."""
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


def build_page_context(
    plan: PagePlan,
    cards: list[StatementCard],
    *,
    page_plans: list[PagePlan],
    statement_graph: dict[str, list[dict[str, Any]]] | None = None,
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
    return {
        "page": {
            **plan.to_dict(),
            "artifact_path": page_artifact_path(plan).as_posix(),
            "wiki_path": wiki_page_path(plan).as_posix(),
        },
        "link_map": _link_map(plan, page_paths),
        "sections": [
            {
                **section.to_dict(),
                "statements": [
                    _statement_context(card_by_id[statement_id], source_root)
                    for statement_id in section.member_statement_ids
                    if statement_id in card_by_id
                ],
            }
            for section in plan.sections
        ],
        "member_statements": [
            _statement_context(card, source_root) for card in member_cards
        ],
        "local_graph": _local_graph_context(plan, statement_graph),
        "all_page_paths": page_paths,
        "instructions": {
            "prose": (
                "Write the full page body as human-readable academic prose. Use the "
                "statement cards, local graph, link map, and project evidence excerpts as "
                "context; do not use template prose or list-only summaries."
            ),
            "citations": (
                "Every factual paragraph must cite statement ids and source projects in "
                "the form [stmt:id; source_project]. Only cite member statements."
            ),
            "links": (
                "Use Markdown links from link_map for related pages. Keep structured "
                "evidence/source material after the prose, not as the page lead."
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
        statement_graph=statement_graph,
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
    repo_commit: str = "",
    timestamp: str = "",
) -> tuple[Path, Path]:
    """Write an LLM-authored Markdown page plus its synthesis manifest."""
    card_by_id = {card.id: card for card in cards}
    member_ids = [sid for sid in plan.member_statement_ids if sid in card_by_id]
    cited_statement_ids = _validate_authored_markdown(markdown, set(member_ids))
    manifest = _manifest(
        plan,
        cited_statement_ids,
        model=model,
        prompt_hash=prompt_hash,
        repo_commit=repo_commit,
        timestamp=timestamp,
    )
    markdown_path = Path(out_dir) / page_artifact_path(plan)
    manifest_path = markdown_path.with_suffix(".manifest.json")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return markdown_path, manifest_path


def _statement_context(
    card: StatementCard,
    source_root: str | Path | None,
) -> dict[str, Any]:
    evidence = card.evidence
    return {
        "id": card.id,
        "kind": card.kind,
        "scope": card.scope,
        "tier": card.tier,
        "confidence": card.confidence,
        "statement": card.statement,
        "about": card.about.to_dict(),
        "links": card.links.to_dict(),
        "qualifiers": dict(sorted(card.qualifiers.items())),
        "evidence": evidence.to_dict(),
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
    exact = evidence["exact"]
    index = text.find(exact)
    if index < 0:
        return exact
    start = max(0, index - radius)
    end = min(len(text), index + len(exact) + radius)
    return text[start:end].strip()


def _link_map(plan: PagePlan, page_paths: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    return {
        "outgoing": _page_refs(plan.outgoing_links, page_paths),
        "backlinks": _page_refs(plan.backlinks, page_paths),
    }


def _page_refs(page_ids: Iterable[str], page_paths: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"id": page_id, "title": _title(page_id), "path": page_paths[page_id]}
        for page_id in sorted(set(page_ids))
        if page_id in page_paths
    ]


def _local_graph_context(
    plan: PagePlan,
    statement_graph: dict[str, list[dict[str, Any]]] | None,
) -> dict[str, Any]:
    if statement_graph is None:
        return {"nodes": [], "edges": []}
    local_ids = {plan.id, *plan.member_statement_ids}
    edges = [
        edge
        for edge in sorted(statement_graph.get("edges", []), key=_edge_sort_key)
        if {
            str(edge.get("s", "")),
            str(edge.get("o", "")),
            *(str(statement_id) for statement_id in edge.get("statement_ids", [])),
        }
        & local_ids
    ]
    node_ids = {
        str(edge.get("s", "")) for edge in edges
    } | {str(edge.get("o", "")) for edge in edges}
    nodes = [
        node
        for node in sorted(statement_graph.get("nodes", []), key=lambda item: str(item.get("id", "")))
        if str(node.get("id", "")) in node_ids
    ]
    return {"nodes": nodes, "edges": edges}


def _prompt(context: dict[str, Any]) -> str:
    page = context["page"]
    return "\n".join(
        [
            f"# Write Wiki Page: {page['title']}",
            "",
            "Use the adjacent `.context.json` as the only allowed scientific context.",
            "",
            "Requirements:",
            "- Write a full prose-rich academic wiki page, not a template and not a link list.",
            "- Include Markdown links to related wiki pages using `link_map` paths.",
            "- Cite every factual paragraph as `[stmt:id; source_project]`.",
            "- Only cite statement ids present in `member_statements`.",
            "- Use source excerpts from `projects/` to improve readability and scientific framing.",
            "- Keep structured evidence/source details after the prose.",
            "",
            "Suggested shape:",
            "- `# <page title>`",
            "- `## Introduction`",
            "- `## Synthesis`",
            "- caveats/conflicts if relevant",
            "- future steps/opportunities if relevant",
            "- `## Source Statements`",
            "- navigation links/backlinks as support material",
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


def _validate_authored_markdown(markdown: str, allowed_statement_ids: set[str]) -> list[str]:
    cited_statement_ids = sorted(set(_CITATION_RE.findall(markdown)))
    unknown_statement_ids = sorted(set(cited_statement_ids) - allowed_statement_ids)
    if unknown_statement_ids:
        raise ValueError(
            "authored page cites statements outside page membership: "
            + ", ".join(unknown_statement_ids)
        )
    if allowed_statement_ids and not cited_statement_ids:
        raise ValueError("authored page must cite at least one member statement")
    return cited_statement_ids


def _title(page_id: str) -> str:
    value = page_id.split(":", 1)[1] if ":" in page_id else page_id
    return value.replace("_", " ").replace("-", " ").title()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"


def _edge_sort_key(edge: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(edge.get("edge_class", "")),
        str(edge.get("p", "")),
        str(edge.get("s", "")),
        str(edge.get("o", "")),
        str(edge.get("id", "")),
    )

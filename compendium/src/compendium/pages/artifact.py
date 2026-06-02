"""Deterministic page artifacts for the kg-synthesize-page workflow."""

from __future__ import annotations

import json
import re
from pathlib import Path
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


def page_artifact_path(plan: PagePlan) -> Path:
    """Return the relative markdown path for a generated page artifact."""
    if plan.id == "home" or plan.type == "home":
        return Path("home.md")
    stem = _slug(plan.id.split(":", 1)[1] if ":" in plan.id else plan.id)
    directory = _PAGE_DIRS.get(plan.type, f"{_slug(plan.type)}s")
    return Path(directory) / f"{stem}.md"


def build_page_artifact(
    plan: PagePlan,
    cards: list[StatementCard],
    *,
    model: str = "deterministic-section-list",
    prompt_hash: str = "prompt:deterministic-section-list",
    repo_commit: str = "",
    timestamp: str = "",
) -> dict[str, Any]:
    """Build deterministic markdown and manifest for a fixed page plan.

    The markdown is intentionally prose-light. It is the stable fallback and
    cache substrate that the LLM page-synthesis skill can replace section by
    section when member hashes change.
    """
    card_by_id = {card.id: card for card in cards}
    member_cards = [card_by_id[sid] for sid in plan.member_statement_ids if sid in card_by_id]
    cited_statement_ids = sorted({card.id for card in member_cards})
    manifest = _manifest(
        plan,
        cited_statement_ids,
        model=model,
        prompt_hash=prompt_hash,
        repo_commit=repo_commit,
        timestamp=timestamp,
    )
    return {
        "path": page_artifact_path(plan).as_posix(),
        "markdown": _markdown(plan, card_by_id, manifest),
        "manifest": manifest,
    }


def write_page_artifact(
    plan: PagePlan,
    cards: list[StatementCard],
    out_dir: Path,
    **kwargs: Any,
) -> tuple[Path, Path]:
    """Write markdown plus ``.manifest.json`` for a generated page artifact."""
    artifact = build_page_artifact(plan, cards, **kwargs)
    markdown_path = Path(out_dir) / artifact["path"]
    manifest_path = markdown_path.with_suffix(".manifest.json")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(artifact["markdown"], encoding="utf-8")
    manifest_path.write_text(
        json.dumps(artifact["manifest"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return markdown_path, manifest_path


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
            section.id: section.member_hash for section in sorted(plan.sections, key=lambda item: item.id)
        },
        "cited_statement_ids": cited_statement_ids,
        "repo_commit": repo_commit,
        "timestamp": timestamp,
    }


def _markdown(
    plan: PagePlan,
    card_by_id: dict[str, StatementCard],
    manifest: dict[str, Any],
) -> str:
    lines = [
        "---",
        f"page_id: {json.dumps(plan.id)}",
        f"page_type: {json.dumps(plan.type)}",
        f"member_hash: {json.dumps(plan.member_hash)}",
        f"manifest: {json.dumps(page_artifact_path(plan).with_suffix('.manifest.json').as_posix())}",
        "---",
        "",
        f"# {plan.title}",
        "",
    ]

    for section in plan.sections:
        lines.extend([f"## {section.heading}", ""])
        section_cards = [
            card_by_id[sid]
            for sid in section.member_statement_ids
            if sid in card_by_id
        ]
        if not section_cards:
            lines.extend(["No statements selected for this section.", ""])
            continue
        for card in section_cards:
            lines.append(
                "- "
                f"{card.statement} "
                f"[{card.id}; {card.evidence.source_project}]"
            )
        lines.append("")

    lines.extend(
        [
            "## Source Statements",
            "",
        ]
    )
    for statement_id in manifest["cited_statement_ids"]:
        card = card_by_id[statement_id]
        lines.append(
            "- "
            f"`{card.id}` {card.kind}/{card.tier}/{card.confidence}: "
            f"{card.evidence.source_project}/{card.evidence.source_doc}"
        )
    lines.append("")
    return "\n".join(lines)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"

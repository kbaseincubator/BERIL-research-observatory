"""Deterministic page artifacts for the kg-synthesize-page workflow."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from compendium import ids
from compendium.models import PagePlan, StatementCard
from compendium.render.markdown import render_markdown_page

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
    page_plans: list[PagePlan] | None = None,
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
        "markdown": _markdown(plan, cards, page_plans, manifest),
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
    cards: list[StatementCard],
    page_plans: list[PagePlan] | None,
    manifest: dict[str, Any],
) -> str:
    markdown = render_markdown_page(plan, cards, page_plans=page_plans)
    manifest_line = (
        f"manifest: "
        f"{json.dumps(page_artifact_path(plan).with_suffix('.manifest.json').as_posix())}"
    )
    return markdown.replace(
        f"member_hash: {plan.member_hash}\n",
        f"member_hash: {plan.member_hash}\n{manifest_line}\n",
        1,
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"

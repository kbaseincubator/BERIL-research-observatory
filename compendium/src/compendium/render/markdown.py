"""Markdown wiki publisher for LLM-authored synthesis pages."""

from __future__ import annotations

from pathlib import Path

from compendium.models import PagePlan
from compendium.pages.artifact import page_manifest_path, wiki_page_path


def render_markdown_wiki(
    page_plans: list[PagePlan],
    wiki_dir: str | Path,
) -> list[Path]:
    """Validate LLM-authored Markdown wiki pages and their manifests.

    Scientific prose must already exist in ``wiki_dir``; this function does not synthesize prose
    or copy from a second tree. It rejects stale pages/manifests and requires every planned page
    to have both a published Markdown file and a manifest. No ``graph.md`` build artifact is
    emitted.
    """
    wiki_path = Path(wiki_dir)
    wiki_path.mkdir(parents=True, exist_ok=True)

    page_paths = _page_paths(page_plans)
    _reject_stale_artifacts(wiki_path, page_plans, page_paths)
    written: list[Path] = []
    for plan in sorted(page_plans, key=_plan_sort_key):
        page = wiki_path / page_paths[plan.id]
        if not page.is_file():
            raise ValueError(f"missing wiki page for {plan.id}: {page}")
        manifest = wiki_path / page_manifest_path(plan)
        if not manifest.is_file():
            raise ValueError(f"missing page manifest for {plan.id}: {manifest}")
        written.append(page)
    return written


def _reject_stale_artifacts(
    wiki_path: Path,
    page_plans: list[PagePlan],
    page_paths: dict[str, Path],
) -> None:
    expected_pages = set(page_paths.values())
    stale_pages = sorted(
        path.relative_to(wiki_path)
        for path in wiki_path.rglob("*.md")
        if path.relative_to(wiki_path) not in expected_pages
    )
    if stale_pages:
        raise ValueError(
            "stale wiki markdown pages: "
            + ", ".join(path.as_posix() for path in stale_pages)
        )

    manifest_root = wiki_path / ".manifests"
    if not manifest_root.exists():
        return
    expected_manifests = {
        page_manifest_path(plan)
        for plan in page_plans
    }
    stale_manifests = sorted(
        path.relative_to(wiki_path)
        for path in manifest_root.rglob("*.manifest.json")
        if path.relative_to(wiki_path) not in expected_manifests
    )
    if stale_manifests:
        raise ValueError(
            "stale wiki manifests: "
            + ", ".join(path.as_posix() for path in stale_manifests)
        )


def _page_paths(page_plans: list[PagePlan]) -> dict[str, Path]:
    return {
        plan.id: wiki_page_path(plan)
        for plan in sorted(page_plans, key=_plan_sort_key)
    }


def _plan_sort_key(plan: PagePlan) -> tuple[int, str]:
    return (0 if plan.id == "home" else 1, plan.id)

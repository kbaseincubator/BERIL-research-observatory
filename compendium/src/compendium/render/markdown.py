"""Markdown wiki publisher for LLM-authored synthesis pages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from compendium.models import PagePlan
from compendium.pages.artifact import page_manifest_path, wiki_page_path


def render_markdown_wiki(
    page_plans: list[PagePlan],
    wiki_dir: str | Path,
    *,
    statement_graph: dict[str, list[dict[str, Any]]] | None = None,
) -> list[Path]:
    """Validate authored Markdown wiki pages and refresh deterministic graph page.

    Scientific prose must already exist in ``wiki_dir``. This function does not
    synthesize prose and does not copy pages from a second Markdown tree.
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

    graph_path = wiki_path / "graph.md"
    graph_path.write_text(
        _render_graph(page_plans, page_paths, statement_graph),
        encoding="utf-8",
    )
    written.append(graph_path)
    return written


def _reject_stale_artifacts(
    wiki_path: Path,
    page_plans: list[PagePlan],
    page_paths: dict[str, Path],
) -> None:
    expected_pages = {Path("graph.md"), *page_paths.values()}
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


def _render_graph(
    page_plans: list[PagePlan],
    page_paths: dict[str, Path],
    statement_graph: dict[str, list[dict[str, Any]]] | None,
) -> str:
    graph = statement_graph or {"nodes": [], "edges": []}
    lines = [
        "# Graph",
        "",
        f"- Nodes: {len(graph.get('nodes', []))}",
        f"- Edges: {len(graph.get('edges', []))}",
        "",
        "## Pages",
        "",
    ]
    for plan in sorted(page_plans, key=_plan_sort_key):
        lines.append(
            f"- {_link(plan.title, page_paths[plan.id], Path('graph.md'))} "
            f"`{plan.type}` `{plan.id}`"
        )
    lines.extend(["", "## Edge Classes", ""])
    counts: dict[str, int] = {}
    for edge in graph.get("edges", []):
        edge_class = str(edge.get("edge_class", "unknown"))
        counts[edge_class] = counts.get(edge_class, 0) + 1
    if counts:
        for edge_class in sorted(counts):
            lines.append(f"- `{edge_class}`: {counts[edge_class]}")
    else:
        lines.append("No graph edges.")
    lines.append("")
    return "\n".join(lines)


def _page_paths(page_plans: list[PagePlan]) -> dict[str, Path]:
    return {
        plan.id: wiki_page_path(plan)
        for plan in sorted(page_plans, key=_plan_sort_key)
    }


def _link(label: str, target_path: Path, current_path: Path) -> str:
    href = _relative_path(current_path, target_path)
    return f"[{label}]({href})"


def _relative_path(current_path: Path, target_path: Path) -> str:
    current_parent = current_path.parent
    if str(current_parent) == ".":
        return target_path.as_posix()
    return Path(*([".."] * len(current_parent.parts)), target_path).as_posix()


def _plan_sort_key(plan: PagePlan) -> tuple[int, str]:
    return (0 if plan.id == "home" else 1, plan.id)

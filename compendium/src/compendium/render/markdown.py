"""Markdown wiki publisher for LLM-authored synthesis pages."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from compendium.models import PagePlan
from compendium.pages.artifact import page_artifact_path, wiki_page_path


def render_markdown_wiki(
    page_plans: list[PagePlan],
    authored_pages_dir: str | Path,
    out_dir: str | Path,
    *,
    statement_graph: dict[str, list[dict[str, Any]]] | None = None,
) -> list[Path]:
    """Publish an authored Markdown wiki with deterministic links and graph page.

    Scientific prose must already exist in ``authored_pages_dir``. This function
    does not synthesize prose; it only copies page artifacts into the canonical
    wiki folder and writes deterministic navigation support files.
    """
    authored_path = Path(authored_pages_dir)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    page_paths = _page_paths(page_plans)
    written: list[Path] = []
    for plan in sorted(page_plans, key=_plan_sort_key):
        source = authored_path / page_artifact_path(plan)
        if not source.is_file():
            raise ValueError(f"missing authored page for {plan.id}: {source}")
        manifest = source.with_suffix(".manifest.json")
        if not manifest.is_file():
            raise ValueError(f"missing page manifest for {plan.id}: {manifest}")
        target = out_path / page_paths[plan.id]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        written.append(target)

    graph_path = out_path / "graph.md"
    graph_path.write_text(
        _render_graph(page_plans, page_paths, statement_graph),
        encoding="utf-8",
    )
    written.append(graph_path)
    return written


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

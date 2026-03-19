"""Deterministic L0/L1/L2 rendering helpers."""

from __future__ import annotations

from enum import StrEnum


class RenderLevel(StrEnum):
    """Supported deterministic detail levels."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


def render_resource(resource: dict, level: RenderLevel) -> str:
    """Render a resource deterministically from structured fields."""
    kind = resource.get("kind", "resource")
    title = resource.get("title") or resource.get("id", "untitled")

    if level == RenderLevel.L0:
        tags = ", ".join(resource.get("tags", []))
        return "\n".join(
            [
                f"# {title}",
                f"- kind: {kind}",
                f"- project_ids: {', '.join(resource.get('project_ids', [])) or 'none'}",
                f"- tags: {tags or 'none'}",
            ]
        )

    if level == RenderLevel.L1:
        lines = [
            f"# {title}",
            f"Kind: {kind}",
        ]
        if summary := resource.get("summary"):
            lines.append("")
            lines.append(summary)
        if question := resource.get("research_question"):
            lines.append("")
            lines.append(f"Research question: {question}")
        if links := resource.get("links"):
            lines.append("")
            lines.append(f"Links: {', '.join(links)}")
        return "\n".join(lines)

    lines = [f"# {title}", "", "```yaml", _dump_yamlish(resource), "```"]
    return "\n".join(lines)


def _dump_yamlish(data: dict) -> str:
    parts: list[str] = []
    for key, value in data.items():
        parts.append(f"{key}: {value!r}")
    return "\n".join(parts)


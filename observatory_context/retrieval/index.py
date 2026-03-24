"""Manifest-backed resource indexing for Phase 2 retrieval."""

from __future__ import annotations

from pathlib import Path

from observatory_context._text import compact_text
from observatory_context.ingest import build_resource_manifest
from observatory_context.service.models import ContextResource


def build_authored_resource_index(repo_root: Path) -> dict[str, ContextResource]:
    """Build a deterministic in-memory index for authored resources."""
    resources: dict[str, ContextResource] = {}
    for item in build_resource_manifest(repo_root):
        source_path = Path(item.source_path)
        metadata = dict(item.metadata)
        content: str | None = None
        if item.kind != "figure" and source_path.suffix.lower() in {".md", ".yaml", ".yml", ".txt"}:
            content = source_path.read_text(encoding="utf-8")
        if item.kind == "project":
            summary = metadata.get("research_question")
        elif item.kind == "figure":
            summary = metadata.get("caption")
        else:
            summary = compact_text(content)
        resource = ContextResource(
            id=str(metadata.get("id") or source_path.stem),
            uri=item.uri,
            kind=item.kind,
            title=str(metadata.get("title") or source_path.name),
            project_ids=list(metadata.get("project_ids") or item.project_ids),
            tags=list(metadata.get("tags") or []),
            source_refs=list(metadata.get("source_refs") or [str(source_path.relative_to(repo_root))]),
            links=list(metadata.get("links") or []),
            summary=summary,
            research_question=metadata.get("research_question"),
            body=content,
            metadata=metadata,
        )
        resources[resource.uri] = resource
    return resources

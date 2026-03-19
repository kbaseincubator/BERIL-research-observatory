"""Metadata- and link-driven related-resource helpers."""

from __future__ import annotations

from observatory_context.service.models import ContextResource


def rank_related_resources(
    source: ContextResource,
    candidates: list[ContextResource],
    mode: str = "default",
    limit: int = 10,
) -> list[ContextResource]:
    """Return related resources without graph traversal."""
    scored: list[tuple[int, ContextResource]] = []
    source_link_set = set(source.links)
    source_project_ids = set(source.project_ids)
    source_tags = set(source.tags)
    source_refs = set(source.source_refs)

    for candidate in candidates:
        if candidate.uri == source.uri:
            continue
        score = 0
        if mode in {"default", "project"} and source_project_ids & set(candidate.project_ids):
            score += 5
        if mode in {"default", "tags"}:
            score += 3 * len(source_tags & set(candidate.tags))
        if mode in {"default", "sources"}:
            score += 4 * len(source_refs & set(candidate.source_refs))
        if mode in {"default", "links"}:
            if candidate.uri in source_link_set:
                score += 8
            if source.uri in set(candidate.links):
                score += 6
        if score > 0:
            scored.append((score, candidate))

    scored.sort(key=lambda item: (-item[0], item[1].kind != "project_document", item[1].title.lower()))
    return [resource for _, resource in scored[:limit]]

"""Metadata- and link-driven related-resource helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from observatory_context.service.models import ContextResource

if TYPE_CHECKING:
    from observatory_context.retrieval.knowledge_index import KnowledgeIndex


def rank_related_resources(
    source: ContextResource,
    candidates: list[ContextResource],
    mode: str = "default",
    limit: int = 10,
    knowledge_index: KnowledgeIndex | None = None,
) -> list[ContextResource]:
    """Return related resources, optionally enhanced by knowledge graph."""
    scored: list[tuple[int, ContextResource]] = []
    source_link_set = set(source.links)
    source_project_ids = set(source.project_ids)
    source_tags = set(source.tags)
    source_refs = set(source.source_refs)

    graph_related_project_ids: set[str] = set()
    neighbor_entity_ids: set[str] = set()
    if knowledge_index is not None and mode in {"default", "graph"}:
        for project_id in source_project_ids:
            for entity_id in knowledge_index.entities_for_project(project_id):
                for neighbor_id in knowledge_index.entity_neighbors(entity_id):
                    neighbor_entity_ids.add(neighbor_id)
                    graph_related_project_ids |= knowledge_index.projects_for_entity(
                        neighbor_id
                    )
        graph_related_project_ids -= source_project_ids

    for candidate in candidates:
        if candidate.uri == source.uri:
            continue
        score = 0
        candidate_project_ids = set(candidate.project_ids)
        if mode in {"default", "project"} and source_project_ids & candidate_project_ids:
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
        if knowledge_index is not None and mode in {"default", "graph"}:
            if candidate_project_ids & graph_related_project_ids:
                score += 4
            if candidate.kind == "knowledge_document":
                candidate_id_lower = candidate.id.lower()
                for neighbor_id in neighbor_entity_ids:
                    if neighbor_id.lower() in candidate_id_lower:
                        score += 6
                        break
        if score > 0:
            scored.append((score, candidate))

    scored.sort(key=lambda item: (-item[0], item[1].kind != "project_document", item[1].title.lower()))
    return [resource for _, resource in scored[:limit]]

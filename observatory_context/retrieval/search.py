"""Lexical and metadata-driven retrieval helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from observatory_context.service.models import ContextResource

if TYPE_CHECKING:
    from observatory_context.retrieval.knowledge_index import KnowledgeIndex


def lexical_search(
    resources: list[ContextResource],
    query: str,
    knowledge_index: KnowledgeIndex | None = None,
) -> list[ContextResource]:
    """Rank resources with a simple lexical/path/metadata scorer."""
    scored: list[tuple[int, ContextResource]] = []
    query_lower = query.strip().lower()
    query_tokens = [token for token in query_lower.replace("/", " ").replace("_", " ").split() if token]

    boosted_project_ids: set[str] = set()
    entity_names: set[str] = set()
    if knowledge_index is not None:
        matched_entities = knowledge_index.match_query(query)
        for entity in matched_entities:
            boosted_project_ids |= knowledge_index.projects_for_entity(entity.id)
            entity_names.add(entity.name.lower())
            entity_names.add(entity.id.lower())

    for resource in resources:
        score = _score_resource(resource, query_lower, query_tokens)
        if knowledge_index is not None and score > 0:
            if set(resource.project_ids) & boosted_project_ids:
                score += 6
            combined = f"{resource.title} {resource.body or ''}".lower()
            for name in entity_names:
                if name in combined:
                    score += 4
                    break
        if score > 0:
            scored.append((score, resource))
    scored.sort(key=lambda item: (-item[0], item[1].kind != "project", item[1].title.lower(), item[1].uri))
    return [resource for _, resource in scored]


def _score_resource(resource: ContextResource, query_lower: str, query_tokens: list[str]) -> int:
    haystacks = [
        resource.id.lower(),
        resource.title.lower(),
        resource.uri.lower(),
        " ".join(resource.project_ids).lower(),
        " ".join(resource.tags).lower(),
        " ".join(resource.source_refs).lower(),
        " ".join(resource.links).lower(),
        (resource.summary or "").lower(),
        (resource.research_question or "").lower(),
        (resource.body or "").lower(),
    ]
    combined = " ".join(haystacks)
    if query_lower not in combined and query_tokens and not all(token in combined for token in query_tokens):
        return 0
    score = 0
    for haystack in haystacks:
        if not haystack:
            continue
        if query_lower == haystack:
            score += 12
        elif query_lower in haystack:
            score += 8
        for token in query_tokens:
            if token in haystack:
                score += 2
    return score

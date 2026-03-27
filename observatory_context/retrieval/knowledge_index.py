"""Lightweight read-only index over knowledge/ YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True, slots=True)
class KnowledgeEntity:
    """An entity from the knowledge graph (organism, gene, pathway, method, concept)."""

    id: str
    name: str
    kind: str
    projects: frozenset[str] = frozenset()
    aliases: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class KnowledgeRelation:
    """An evidence-backed edge between two entities."""

    subject: str
    predicate: str
    object: str
    evidence_project: str = ""
    confidence: str = ""


class KnowledgeIndex:
    """In-memory index built from knowledge/*.yaml files."""

    def __init__(
        self,
        entities: dict[str, KnowledgeEntity],
        relations: list[KnowledgeRelation],
    ) -> None:
        self._entities = entities
        self._relations = relations

        self._entities_by_kind: dict[str, list[KnowledgeEntity]] = {}
        self._project_to_entities: dict[str, set[str]] = {}
        self._entity_to_projects: dict[str, set[str]] = {}
        self._relations_by_entity: dict[str, list[KnowledgeRelation]] = {}
        for entity in entities.values():
            self._entities_by_kind.setdefault(entity.kind, []).append(entity)
            self._entity_to_projects[entity.id] = set(entity.projects)
            for project_id in entity.projects:
                self._project_to_entities.setdefault(project_id, set()).add(entity.id)
        for rel in relations:
            self._relations_by_entity.setdefault(rel.subject, []).append(rel)
            if rel.object != rel.subject:
                self._relations_by_entity.setdefault(rel.object, []).append(rel)

    def get_entity(self, entity_id: str) -> KnowledgeEntity | None:
        return self._entities.get(entity_id)

    def list_entities(self, kind: str | None = None) -> list[KnowledgeEntity]:
        if kind is not None:
            return list(self._entities_by_kind.get(kind, []))
        return list(self._entities.values())

    def entity_connections(self, entity_id: str) -> list[KnowledgeRelation]:
        return list(self._relations_by_entity.get(entity_id, []))

    def projects_for_entity(self, entity_id: str) -> set[str]:
        return set(self._entity_to_projects.get(entity_id, set()))

    def entities_for_project(self, project_id: str) -> set[str]:
        return set(self._project_to_entities.get(project_id, set()))

    def match_query(self, query: str) -> list[KnowledgeEntity]:
        query_lower = query.strip().lower()
        if not query_lower:
            return []
        matches: list[tuple[int, KnowledgeEntity]] = []
        for entity in self._entities.values():
            score = 0
            if query_lower == entity.id.lower():
                score += 10
            elif query_lower in entity.id.lower():
                score += 4
            if query_lower == entity.name.lower():
                score += 10
            elif query_lower in entity.name.lower():
                score += 6
            for alias in entity.aliases:
                if query_lower == alias.lower():
                    score += 8
                elif query_lower in alias.lower():
                    score += 3
            if score > 0:
                matches.append((score, entity))
        matches.sort(key=lambda item: (-item[0], item[1].id))
        return [entity for _, entity in matches]

    def entity_neighbors(self, entity_id: str) -> set[str]:
        neighbors: set[str] = set()
        for rel in self._relations_by_entity.get(entity_id, []):
            other = rel.object if rel.subject == entity_id else rel.subject
            neighbors.add(other)
        return neighbors


def _load_yaml_list(path: Path, root_key: str) -> list[dict]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    values = data.get(root_key, [])
    return [v for v in values if isinstance(v, dict)]


_ENTITY_FILES: list[tuple[str, str, str]] = [
    ("organisms", "organisms.yaml", "organism"),
    ("genes", "genes.yaml", "gene"),
    ("pathways", "pathways.yaml", "pathway"),
    ("methods", "methods.yaml", "method"),
    ("concepts", "concepts.yaml", "concept"),
]


def _extract_aliases(row: dict) -> frozenset[str]:
    aliases: set[str] = set()
    for key in ("strain", "abbreviation", "alt_name"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            aliases.add(val.strip())
    alt_names = row.get("aliases") or row.get("alt_names")
    if isinstance(alt_names, list):
        for name in alt_names:
            if isinstance(name, str) and name.strip():
                aliases.add(name.strip())
    return frozenset(aliases)


def build_knowledge_index(repo_root: Path) -> KnowledgeIndex:
    """Build an in-memory index from knowledge/*.yaml files."""
    knowledge_dir = repo_root / "knowledge"
    entities: dict[str, KnowledgeEntity] = {}

    for root_key, filename, kind in _ENTITY_FILES:
        rows = _load_yaml_list(knowledge_dir / "entities" / filename, root_key)
        for row in rows:
            entity_id = str(row.get("id", ""))
            if not entity_id:
                continue
            projects = frozenset(
                str(p) for p in (row.get("projects") or []) if str(p).strip()
            )
            entities[entity_id] = KnowledgeEntity(
                id=entity_id,
                name=str(row.get("name", "")),
                kind=kind,
                projects=projects,
                aliases=_extract_aliases(row),
            )

    raw_relations = _load_yaml_list(knowledge_dir / "relations.yaml", "relations")
    relations: list[KnowledgeRelation] = []
    for rel in raw_relations:
        relations.append(
            KnowledgeRelation(
                subject=str(rel.get("subject", "")),
                predicate=str(rel.get("predicate", "")),
                object=str(rel.get("object", "")),
                evidence_project=str(rel.get("evidence_project", "")),
                confidence=str(rel.get("confidence", "")),
            )
        )

    return KnowledgeIndex(entities=entities, relations=relations)

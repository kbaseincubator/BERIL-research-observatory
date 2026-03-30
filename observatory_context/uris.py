"""Deterministic URI helpers for observatory resources."""

from __future__ import annotations

from pathlib import PurePosixPath


_ROOT = "viking://resources/observatory"


def _normalize_segment(value: str) -> str:
    return PurePosixPath(value.replace("\\", "/")).as_posix().strip("/")


def build_project_resource_uri(project_id: str, section: str, relative_path: str) -> str:
    path = PurePosixPath(
        "projects",
        project_id,
        _normalize_segment(section),
        _normalize_segment(relative_path),
    )
    return f"{_ROOT}/{path.as_posix()}"


def build_observatory_root_uri() -> str:
    return _ROOT


def build_project_workspace_uri(project_id: str) -> str:
    path = PurePosixPath("projects", _normalize_segment(project_id))
    return f"{_ROOT}/{path.as_posix()}"


def build_figure_resource_uri(project_id: str, figure_id: str) -> str:
    path = PurePosixPath("projects", project_id, "authored", "figures", _normalize_segment(figure_id))
    return f"{_ROOT}/{path.as_posix()}"


def build_project_live_note_uri(project_id: str, resource_id: str, date: str) -> str:
    path = PurePosixPath(
        "projects",
        _normalize_segment(project_id),
        "notes",
        _normalize_segment(date),
        _normalize_segment(resource_id),
    )
    return f"{_ROOT}/{path.as_posix()}"


def build_shared_live_note_uri(resource_id: str, date: str) -> str:
    path = PurePosixPath("notes", _normalize_segment(date), _normalize_segment(resource_id))
    return f"{_ROOT}/{path.as_posix()}"


def build_project_notes_root_uri(project_id: str) -> str:
    path = PurePosixPath("projects", _normalize_segment(project_id), "notes")
    return f"{_ROOT}/{path.as_posix()}"


def build_shared_notes_root_uri() -> str:
    path = PurePosixPath("notes")
    return f"{_ROOT}/{path.as_posix()}"


_ENTITY_TYPE_PLURALS = {
    "organism": "organisms",
    "gene": "genes",
    "pathway": "pathways",
    "method": "methods",
    "concept": "concepts",
}

_MEMORY_STORE_DIRS = {
    "journal": "research-journal",
    "patterns": "patterns",
    "conversations": "conversations",
}


def build_knowledge_graph_uri() -> str:
    path = PurePosixPath("knowledge-graph")
    return f"{_ROOT}/{path.as_posix()}"


def build_entity_uri(entity_type: str, entity_id: str) -> str:
    plural = _ENTITY_TYPE_PLURALS[entity_type]
    path = PurePosixPath(
        "knowledge-graph",
        "entities",
        _normalize_segment(plural),
        _normalize_segment(entity_id),
    )
    return f"{_ROOT}/{path.as_posix()}"


def build_entity_relations_uri(entity_type: str, entity_id: str) -> str:
    return f"{build_entity_uri(entity_type, entity_id)}/relations"


def build_hypothesis_uri(hypothesis_id: str) -> str:
    path = PurePosixPath("knowledge-graph", "hypotheses", _normalize_segment(hypothesis_id))
    return f"{_ROOT}/{path.as_posix()}"


def build_timeline_uri() -> str:
    path = PurePosixPath("knowledge-graph", "timeline")
    return f"{_ROOT}/{path.as_posix()}"


def build_memory_uri(store: str, slug: str | None = None) -> str:
    store_dir = _MEMORY_STORE_DIRS[store]
    if slug is None:
        path = PurePosixPath("memories", _normalize_segment(store_dir))
    else:
        path = PurePosixPath("memories", _normalize_segment(store_dir), _normalize_segment(slug))
    return f"{_ROOT}/{path.as_posix()}"

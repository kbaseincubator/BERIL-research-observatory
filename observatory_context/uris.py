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


def build_project_workspace_uri(project_id: str) -> str:
    path = PurePosixPath("projects", _normalize_segment(project_id))
    return f"{_ROOT}/{path.as_posix()}"


def build_figure_resource_uri(project_id: str, figure_id: str) -> str:
    path = PurePosixPath("projects", project_id, "authored", "figures", _normalize_segment(figure_id))
    return f"{_ROOT}/{path.as_posix()}"


def build_knowledge_resource_uri(relative_path: str) -> str:
    path = PurePosixPath("overlays", "raw-knowledge", _normalize_segment(relative_path))
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

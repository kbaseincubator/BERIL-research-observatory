"""Build resource manifests from the repository."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from scripts.build_registry import parse_figures_from_report, parse_project

from observatory_context.uris import (
    build_figure_resource_uri,
    build_knowledge_resource_uri,
    build_project_resource_uri,
)

_KNOWLEDGE_ROOT_KEYS = {
    "entities/organisms.yaml": "organisms",
    "entities/genes.yaml": "genes",
    "entities/pathways.yaml": "pathways",
    "entities/methods.yaml": "methods",
    "entities/concepts.yaml": "concepts",
    "relations.yaml": "relations",
    "hypotheses.yaml": "hypotheses",
    "timeline.yaml": "events",
}


@dataclass(slots=True)
class ResourceManifestItem:
    """Deterministic logical resource for ingest."""

    uri: str
    kind: str
    source_path: str
    project_ids: list[str]
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


def build_resource_manifest(
    repo_root: Path,
    project_ids: set[str] | None = None,
) -> list[ResourceManifestItem]:
    """Build the Phase 1 resource manifest from repository content."""
    manifest: list[ResourceManifestItem] = []
    registry = _load_yaml(repo_root / "docs" / "project_registry.yaml")
    figure_catalog = _load_yaml(repo_root / "docs" / "figure_catalog.yaml")
    project_entries: dict[str, dict] = {}
    registry_projects = {
        project["id"]: dict(project)
        for project in registry.get("projects", [])
        if isinstance(project, dict) and project.get("id")
    }
    figure_catalog_entries = {
        (
            str(figure.get("project_id") or figure.get("project") or ""),
            Path(str(figure.get("figure_file") or figure.get("file") or "")).name,
        ): dict(figure)
        for figure in figure_catalog.get("figures", [])
        if isinstance(figure, dict)
    }
    selected_project_ids = set(project_ids or [])
    discovered_project_ids = [
        path.name
        for path in sorted((repo_root / "projects").iterdir())
        if path.is_dir() and (path / "README.md").exists()
        and (not selected_project_ids or path.name in selected_project_ids)
    ]

    for project_id in discovered_project_ids:
        project_dir = repo_root / "projects" / project_id
        project = parse_project(project_dir)
        legacy_project = registry_projects.get(project_id, {})
        if project is None:
            project = legacy_project
        else:
            project = _merge_project_entry(project, legacy_project)
        if not project:
            continue
        project_entries[project_id] = project
    _compute_enables(project_entries)

    for project_id, project in project_entries.items():
        for name in ("README.md", "REPORT.md", "provenance.yaml"):
            source_path = repo_root / "projects" / project_id / name
            if not source_path.exists():
                continue
            manifest.append(
                ResourceManifestItem(
                    uri=build_project_resource_uri(project_id, "authored", name),
                    kind="project" if name == "README.md" else "project_document",
                    source_path=str(source_path),
                    project_ids=[project_id],
                    metadata={
                        "id": project_id,
                        "kind": "project" if name == "README.md" else "project_document",
                        "title": project.get("title", project_id),
                        "tags": project.get("tags", []),
                        "research_question": project.get("research_question"),
                        "source_refs": [str(source_path.relative_to(repo_root))],
                        "project_ids": [project_id],
                        "export_project": project if name == "README.md" else None,
                    },
                )
            )

    for project_id in discovered_project_ids:
        project_dir = repo_root / "projects" / project_id
        report_path = project_dir / "REPORT.md"
        provenance_path = project_dir / "provenance.yaml"
        report_content = report_path.read_text(encoding="utf-8") if report_path.exists() else None
        provenance = _load_yaml(provenance_path) if provenance_path.exists() else None
        seen_figure_uris: set[str] = set()
        figures = parse_figures_from_report(
            project_id,
            report_content,
            project_dir / "figures",
            provenance if isinstance(provenance, dict) else None,
        )
        for figure in figures:
            figure_file = figure.get("file")
            legacy_figure = figure_catalog_entries.get((project_id, Path(str(figure_file or "")).name), {})
            figure_id = str(legacy_figure.get("id") or f"{project_id}__{Path(str(figure_file or 'figure')).stem}")
            source_path = repo_root / str(figure.get("path"))
            if not figure_file or not source_path.exists():
                continue
            figure_uri = build_figure_resource_uri(project_id, figure_id)
            if figure_uri in seen_figure_uris:
                continue
            seen_figure_uris.add(figure_uri)
            export_figure = {
                "project": project_id,
                "file": figure_file,
                "path": figure.get("path"),
                "caption": figure.get("caption") if figure.get("caption") is not None else legacy_figure.get("caption"),
                "notebook": figure.get("notebook") if figure.get("notebook") is not None else legacy_figure.get("notebook"),
                "tags": list(figure.get("tags") or legacy_figure.get("tags") or []),
            }
            manifest.append(
                ResourceManifestItem(
                    uri=figure_uri,
                    kind="figure",
                    source_path=str(source_path),
                    project_ids=[project_id],
                    metadata={
                        "id": figure_id,
                        "kind": "figure",
                        "title": figure.get("caption") or figure_id,
                        "tags": list(figure.get("tags") or []),
                        "caption": figure.get("caption"),
                        "source_refs": [str(source_path.relative_to(repo_root))],
                        "project_ids": [project_id],
                        "export_figure": export_figure,
                    },
                )
            )

    if selected_project_ids:
        return manifest

    for relative_path in _knowledge_paths(repo_root / "knowledge"):
        source_path = repo_root / "knowledge" / relative_path
        relative_posix = relative_path.as_posix()
        manifest.append(
            ResourceManifestItem(
                uri=build_knowledge_resource_uri(relative_posix),
                kind="knowledge_document",
                source_path=str(source_path),
                project_ids=[],
                metadata={
                    "id": relative_path.stem,
                    "kind": "knowledge_document",
                    "title": relative_path.name,
                    "tags": ["raw-knowledge"],
                    "source_refs": [f"knowledge/{relative_posix}"],
                    "overlay_family": "raw-knowledge",
                    "overlay_relative_path": relative_posix,
                    "overlay_root_key": _knowledge_root_keys(relative_path),
                },
            )
        )

    return manifest


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _knowledge_paths(knowledge_root: Path) -> list[Path]:
    paths = []
    for path in sorted(knowledge_root.rglob("*.yaml")):
        if path.name == "research_graph.yaml":
            continue
        paths.append(path.relative_to(knowledge_root))
    return paths


def _knowledge_root_keys(relative_path: Path) -> str:
    relative_posix = relative_path.as_posix()
    try:
        return _KNOWLEDGE_ROOT_KEYS[relative_posix]
    except KeyError as exc:
        raise ValueError(f"Unsupported knowledge overlay path: {relative_posix}") from exc


def _compute_enables(project_entries: dict[str, dict]) -> None:
    for project in project_entries.values():
        project["depends_on"] = sorted(project.get("depends_on") or [])
        project["enables"] = []
    for project in project_entries.values():
        for dependency in project.get("depends_on") or []:
            dependency_id = str(dependency)
            if dependency_id in project_entries:
                project_entries[dependency_id]["enables"].append(project["id"])
    for project in project_entries.values():
        project["enables"] = sorted(project.get("enables") or [])


def _merge_project_entry(parsed: dict, legacy: dict) -> dict:
    merged = dict(legacy)
    merged.update(parsed)
    for key in ("research_question", "title", "status", "date_completed"):
        if parsed.get(key) in (None, "", "unknown") and legacy.get(key) not in (None, ""):
            merged[key] = legacy[key]
    for key in (
        "key_findings",
        "tags",
        "organisms",
        "databases_used",
        "key_data_artifacts",
        "references",
        "depends_on",
    ):
        if not parsed.get(key) and legacy.get(key):
            merged[key] = legacy[key]
    return merged

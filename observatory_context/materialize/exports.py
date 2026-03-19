"""Deterministic export builders for OpenViking-backed resources."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from observatory_context.service import ObservatoryContextService


class ExportMaterializationError(ValueError):
    """Raised when export-critical metadata is missing from a resource."""


def collect_project_ids(repo_root: Path) -> list[str]:
    """Discover project IDs from the Git-authored project workspace layout."""
    projects_root = Path(repo_root) / "projects"
    project_ids = [
        path.name
        for path in sorted(projects_root.iterdir())
        if path.is_dir() and (path / "README.md").exists()
    ]
    return project_ids


def build_project_registry_export(
    service: ObservatoryContextService,
    project_ids: list[str],
    generated_at: str,
) -> dict[str, object]:
    """Build `project_registry.yaml` from project resources."""
    projects: list[dict[str, object]] = []
    for project_id in sorted(set(project_ids)):
        workspace = service.get_project_workspace(project_id)
        export_project = workspace.project_resource.metadata.get("export_project")
        if not isinstance(export_project, dict):
            raise ExportMaterializationError(
                f"Resource {workspace.project_resource.uri} is missing export_project metadata"
            )
        project = deepcopy(export_project)
        project["depends_on"] = sorted(project.get("depends_on") or [])
        project["enables"] = []
        projects.append(project)

    _compute_enables(projects)
    return {
        "version": 1,
        "generated_at": generated_at,
        "project_count": len(projects),
        "projects": projects,
    }


def build_figure_catalog_export(
    service: ObservatoryContextService,
    project_ids: list[str],
    generated_at: str,
) -> dict[str, object]:
    """Build `figure_catalog.yaml` from figure resources."""
    figures: list[dict[str, object]] = []
    for project_id in sorted(set(project_ids)):
        for resource in service.list_project_resources(project_id, kind="figure"):
            export_figure = resource.metadata.get("export_figure")
            if not isinstance(export_figure, dict):
                raise ExportMaterializationError(
                    f"Resource {resource.uri} is missing export_figure metadata"
                )
            figures.append(deepcopy(export_figure))
    figures.sort(key=lambda figure: (str(figure["project"]), str(figure["file"]), str(figure["path"])))
    return {
        "version": 1,
        "generated_at": generated_at,
        "figure_count": len(figures),
        "figures": figures,
    }


def _compute_enables(projects: list[dict[str, object]]) -> None:
    id_to_project = {str(project["id"]): project for project in projects}
    for project in projects:
        for dependency in project.get("depends_on") or []:
            dependency_id = str(dependency)
            if dependency_id in id_to_project:
                enables = id_to_project[dependency_id].setdefault("enables", [])
                if project["id"] not in enables:
                    enables.append(project["id"])
    for project in projects:
        project["enables"] = sorted(project.get("enables") or [])

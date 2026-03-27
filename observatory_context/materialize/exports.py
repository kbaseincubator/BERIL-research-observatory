"""Deterministic export builders for OpenViking-backed resources."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from observatory_context._discovery import discover_project_ids
from observatory_context._graph import compute_enables
from observatory_context.service import ObservatoryContextService


class ExportMaterializationError(ValueError):
    """Raised when export-critical metadata is missing from a resource."""


def collect_project_ids(repo_root: Path) -> list[str]:
    """Discover project IDs from the Git-authored project workspace layout."""
    return discover_project_ids(repo_root)


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

    compute_enables(projects)
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



"""Build resource manifests from the repository."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from observatory_context.uris import (
    build_figure_resource_uri,
    build_knowledge_resource_uri,
    build_project_resource_uri,
)


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


def build_resource_manifest(repo_root: Path) -> list[ResourceManifestItem]:
    """Build the Phase 1 resource manifest from repository content."""
    manifest: list[ResourceManifestItem] = []

    registry = _load_yaml(repo_root / "docs" / "project_registry.yaml")
    figure_catalog = _load_yaml(repo_root / "docs" / "figure_catalog.yaml")

    project_index = {
        project["id"]: project
        for project in registry.get("projects", [])
        if isinstance(project, dict) and project.get("id")
    }

    for project_id, project in project_index.items():
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
                    },
                )
            )

    for figure in figure_catalog.get("figures", []):
        if not isinstance(figure, dict):
            continue
        project_id = figure.get("project_id") or figure.get("project")
        figure_file = figure.get("figure_file")
        figure_id = figure.get("id") or Path(figure_file or "figure").stem
        if not project_id or not figure_file:
            continue
        source_path = repo_root / "projects" / project_id / figure_file
        if not source_path.exists():
            continue
        manifest.append(
            ResourceManifestItem(
                uri=build_figure_resource_uri(project_id, figure_id),
                kind="figure",
                source_path=str(source_path),
                project_ids=[project_id],
                metadata={
                    "id": figure_id,
                    "kind": "figure",
                    "title": figure.get("caption") or figure_id,
                    "tags": figure.get("tags", []),
                    "caption": figure.get("caption"),
                    "source_refs": [str(source_path.relative_to(repo_root))],
                },
            )
        )

    for relative_path in _knowledge_paths(repo_root / "knowledge"):
        source_path = repo_root / "knowledge" / relative_path
        manifest.append(
            ResourceManifestItem(
                uri=build_knowledge_resource_uri(relative_path.as_posix()),
                kind="knowledge_document",
                source_path=str(source_path),
                project_ids=[],
                metadata={
                    "id": relative_path.stem,
                    "kind": "knowledge_document",
                    "title": relative_path.name,
                    "tags": ["raw-knowledge"],
                    "source_refs": [f"knowledge/{relative_path.as_posix()}"],
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


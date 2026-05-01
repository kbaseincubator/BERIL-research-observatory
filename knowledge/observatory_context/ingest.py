from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import PROJECT_INDEX_TARGET_URI, PROJECTS_TARGET_URI, ContextConfig
from .manifest import (
    build_manifest,
    changed_targets,
    load_manifest,
    removed_targets,
    save_manifest,
)
from .selection import (
    docs_target_uri,
    iter_project_dirs,
    project_target_uri,
    select_central_docs,
    select_project_files,
)
from .staging import stage_doc, stage_project, stage_project_index


MANIFEST_FILENAME = "context_manifest.json"


def ingest_all(config: ContextConfig, client: Any) -> None:
    project_dirs = iter_project_dirs(config.projects_dir)
    project_index = stage_project_index(project_dirs, config.staging_dir)
    _add_resource(client, project_index, PROJECT_INDEX_TARGET_URI, "BERIL project index")

    for project_dir in project_dirs:
        _ingest_project_dir(config, client, project_dir)

    for doc_path in select_central_docs(config.repo_root):
        _ingest_doc(config, client, doc_path)

    client.wait_processed()
    save_manifest(_manifest_path(config), _current_manifest(config))


def ingest_changed(config: ContextConfig, client: Any) -> None:
    old_manifest = load_manifest(_manifest_path(config))
    new_manifest = _current_manifest(config)
    targets = changed_targets(old_manifest, new_manifest)
    removed = removed_targets(old_manifest, new_manifest)
    project_dirs = {path.name: path for path in iter_project_dirs(config.projects_dir)}
    docs = {docs_target_uri(path): path for path in select_central_docs(config.repo_root)}
    project_targets_changed = False

    for target_uri in targets:
        if target_uri.startswith(PROJECTS_TARGET_URI):
            project_id = target_uri.removeprefix(PROJECTS_TARGET_URI).strip("/")
            if project_id in project_dirs:
                project_targets_changed = True
                _ingest_project_dir(config, client, project_dirs[project_id])
        elif target_uri in docs:
            _ingest_doc(config, client, docs[target_uri])

    for target_uri in removed:
        _remove_resource(client, target_uri)
        if target_uri.startswith(PROJECTS_TARGET_URI):
            project_targets_changed = True

    if project_targets_changed:
        project_index = stage_project_index(list(project_dirs.values()), config.staging_dir)
        _add_resource(client, project_index, PROJECT_INDEX_TARGET_URI, "BERIL project index")

    if targets or removed:
        client.wait_processed()
    save_manifest(_manifest_path(config), new_manifest)


def ingest_project(config: ContextConfig, client: Any, project_id: str) -> None:
    project_dir = resolve_project_dir(config, project_id)
    _ingest_project_dir(config, client, project_dir)
    project_index = stage_project_index(iter_project_dirs(config.projects_dir), config.staging_dir)
    _add_resource(client, project_index, PROJECT_INDEX_TARGET_URI, "BERIL project index")
    client.wait_processed()
    save_manifest(_manifest_path(config), _current_manifest(config))


def resolve_project_dir(config: ContextConfig, project_id: str) -> Path:
    if project_id in {"", ".", ".."} or "/" in project_id or "\\" in project_id:
        raise ValueError(f"Project ID must be a simple directory name: {project_id!r}")
    project_dir = config.projects_dir / project_id
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Project does not exist: {project_id}")
    return project_dir


def ingest_docs(config: ContextConfig, client: Any) -> None:
    for doc_path in select_central_docs(config.repo_root):
        _ingest_doc(config, client, doc_path)
    client.wait_processed()
    save_manifest(_manifest_path(config), _current_manifest(config))


def _current_manifest(config: ContextConfig) -> dict[str, dict[str, str]]:
    target_sources: dict[str, list[Path]] = {}
    for project_dir in iter_project_dirs(config.projects_dir):
        target_sources[project_target_uri(project_dir.name)] = select_project_files(project_dir)
    for doc_path in select_central_docs(config.repo_root):
        target_sources[docs_target_uri(doc_path)] = [doc_path]
    return build_manifest(target_sources, config.repo_root)


def _ingest_project_dir(config: ContextConfig, client: Any, project_dir: Path) -> None:
    staged = stage_project(project_dir, config.staging_dir)
    _add_resource(client, staged, project_target_uri(project_dir.name), f"BERIL project {project_dir.name}")


def _ingest_doc(config: ContextConfig, client: Any, doc_path: Path) -> None:
    staged = stage_doc(doc_path, config.staging_dir)
    _add_resource(client, staged, docs_target_uri(doc_path), f"BERIL doc {doc_path.name}")


def _add_resource(client: Any, path: Path, target_uri: str, reason: str) -> None:
    client.add_resource(path=str(path), to=target_uri, reason=reason, wait=False)


def _remove_resource(client: Any, target_uri: str) -> None:
    client.rm(target_uri, recursive=True)


def _manifest_path(config: ContextConfig) -> Path:
    return config.state_dir / MANIFEST_FILENAME

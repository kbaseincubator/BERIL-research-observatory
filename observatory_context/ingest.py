from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from openviking_cli.exceptions import (
    DeadlineExceededError,
    EmbeddingFailedError,
    InternalError,
    ProcessingError,
    ResourceExhaustedError,
    UnavailableError,
    VLMFailedError,
)

TRANSIENT_OV_ERRORS: tuple[type[Exception], ...] = (
    DeadlineExceededError,
    EmbeddingFailedError,
    InternalError,
    ProcessingError,
    ResourceExhaustedError,
    UnavailableError,
    VLMFailedError,
)

from .config import DOCS_TARGET_URI, PROJECTS_TARGET_URI, ContextConfig
from .manifest import (
    Manifest,
    build_manifest,
    changed_targets,
    load_manifest,
    removed_targets,
    save_manifest,
)
from .progress import IngestObserver, NullObserver
from .relations import apply_project_relations
from .selection import (
    docs_target_uri,
    iter_project_dirs,
    project_target_uri,
    select_central_docs,
    select_project_files,
)
from .staging import stage_doc, stage_project


MANIFEST_FILENAME = "context_manifest.json"

# OpenViking's temp tier (`viking://temp/default/<MMDDHHMM>_<hash>`) collides
# under sustained back-to-back `add_resource` pressure, surfacing as
# "Directory not found" / corrupt-zip errors mid-finalize. Drain the queue
# every N projects so the server can flush temp before more pile up. The
# manifest is also checkpointed at each drain — only after `wait_processed`
# confirms the queue is idle, so a manifest entry means "fully processed by
# OV", not just "synchronously finalized".
#
# Default is 1 (slow-and-steady) to minimize CBORG/VLM rate-limit pressure;
# bump via OV_INGEST_DRAIN_EVERY when the backend is healthy and you want
# more throughput.
DRAIN_EVERY = max(1, int(os.environ.get("OV_INGEST_DRAIN_EVERY", "1")))

# Transient temp-tier errors usually clear after a brief settle. Retry the
# same upload a few times with linear backoff before giving up.
ADD_RESOURCE_RETRIES = 3
ADD_RESOURCE_BACKOFF_SECONDS = 5.0


def ingest_all(
    config: ContextConfig,
    client: Any,
    *,
    observer: IngestObserver | None = None,
    limit: int | None = None,
) -> None:
    obs = observer or NullObserver()
    project_dirs = iter_project_dirs(config.projects_dir)
    selected = project_dirs[:limit] if limit else project_dirs
    docs = [] if limit else select_central_docs(config.repo_root)
    obs.start(total=len(selected) + len(docs))

    new_manifest = _current_manifest(config)

    pending_checkpoint: set[str] = set()
    for index, project_dir in enumerate(selected, start=1):
        target_uri = project_target_uri(project_dir.name)
        _ingest_project_dir(config, client, project_dir)
        obs.advance(project_dir.name)
        pending_checkpoint.add(target_uri)
        if index % DRAIN_EVERY == 0 and index < len(selected):
            obs.wait_processed(client)
            _checkpoint_manifest(config, new_manifest, pending_checkpoint)
            pending_checkpoint.clear()

    for doc_path in docs:
        _ingest_doc(config, client, doc_path)
        obs.advance(f"docs/{doc_path.name}")

    if limit:
        ingested = {project_target_uri(p.name) for p in selected}
        manifest_to_save = _partial_manifest(
            load_manifest(_manifest_path(config)), new_manifest, ingested
        )
    else:
        _remove_stale(client, config, new_manifest)
        manifest_to_save = new_manifest
    obs.wait_processed(client)
    save_manifest(_manifest_path(config), manifest_to_save)
    obs.done()


def ingest_changed(
    config: ContextConfig,
    client: Any,
    *,
    observer: IngestObserver | None = None,
    limit: int | None = None,
) -> None:
    obs = observer or NullObserver()
    old_manifest = load_manifest(_manifest_path(config))
    new_manifest = _current_manifest(config)
    targets = changed_targets(old_manifest, new_manifest)
    removed = removed_targets(old_manifest, new_manifest)
    project_dirs = {path.name: path for path in iter_project_dirs(config.projects_dir)}
    docs = {docs_target_uri(path): path for path in select_central_docs(config.repo_root)}

    if limit:
        # Limit caps project ingests; skip docs and removals so a partial run
        # never persists half-finished reconciliation.
        targets = [t for t in targets if t.startswith(PROJECTS_TARGET_URI)][:limit]
        removed = []
        docs = {}

    ingested_uris: set[str] = set()
    obs.start(total=max(len(targets) + len(removed), 1))

    project_index = 0
    pending_checkpoint: set[str] = set()
    for target_uri in targets:
        if target_uri.startswith(PROJECTS_TARGET_URI):
            project_id = target_uri.removeprefix(PROJECTS_TARGET_URI).strip("/")
            if project_id in project_dirs:
                _ingest_project_dir(config, client, project_dirs[project_id])
                ingested_uris.add(target_uri)
                obs.advance(project_id)
                pending_checkpoint.add(target_uri)
                project_index += 1
                if project_index % DRAIN_EVERY == 0:
                    obs.wait_processed(client)
                    _checkpoint_manifest(config, new_manifest, pending_checkpoint)
                    pending_checkpoint.clear()
        elif target_uri in docs:
            _ingest_doc(config, client, docs[target_uri])
            ingested_uris.add(target_uri)
            obs.advance(f"docs/{docs[target_uri].name}")

    for target_uri in removed:
        _remove_resource(client, target_uri)
        ingested_uris.add(target_uri)
        obs.advance(f"removed: {target_uri}")

    if targets or removed:
        obs.wait_processed(client)
    if limit:
        manifest_to_save = _partial_manifest(old_manifest, new_manifest, ingested_uris)
    else:
        manifest_to_save = new_manifest
    save_manifest(_manifest_path(config), manifest_to_save)
    obs.done()


def ingest_project(
    config: ContextConfig,
    client: Any,
    project_id: str,
    *,
    observer: IngestObserver | None = None,
) -> None:
    ingest_projects(config, client, [project_id], observer=observer)


def ingest_projects(
    config: ContextConfig,
    client: Any,
    project_ids: list[str],
    *,
    observer: IngestObserver | None = None,
) -> None:
    obs = observer or NullObserver()
    project_dirs = [resolve_project_dir(config, project_id) for project_id in project_ids]
    obs.start(total=len(project_dirs))
    for project_dir in project_dirs:
        _ingest_project_dir(config, client, project_dir)
        obs.advance(project_dir.name)

    new_manifest = _current_manifest(config)
    _remove_stale(client, config, new_manifest)
    obs.wait_processed(client)
    save_manifest(_manifest_path(config), new_manifest)
    obs.done()


def resolve_project_dir(config: ContextConfig, project_id: str) -> Path:
    if project_id in {"", ".", ".."} or "/" in project_id or "\\" in project_id:
        raise ValueError(f"Project ID must be a simple directory name: {project_id!r}")
    project_dir = config.projects_dir / project_id
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Project does not exist: {project_id}")
    return project_dir


def ingest_docs(
    config: ContextConfig,
    client: Any,
    *,
    observer: IngestObserver | None = None,
) -> None:
    obs = observer or NullObserver()
    docs = select_central_docs(config.repo_root)
    obs.start(total=max(len(docs), 1))
    for doc_path in docs:
        _ingest_doc(config, client, doc_path)
        obs.advance(f"docs/{doc_path.name}")

    new_manifest = _current_manifest(config)
    _remove_stale(client, config, new_manifest, prefix=DOCS_TARGET_URI)
    obs.wait_processed(client)
    save_manifest(_manifest_path(config), new_manifest)
    obs.done()


def _remove_stale(
    client: Any,
    config: ContextConfig,
    new_manifest: dict[str, dict[str, str]],
    *,
    prefix: str | None = None,
) -> None:
    old_manifest = load_manifest(_manifest_path(config))
    for target_uri in removed_targets(old_manifest, new_manifest):
        if prefix is None or target_uri.startswith(prefix):
            _remove_resource(client, target_uri)


def _partial_manifest(old: Manifest, new: Manifest, touched: set[str]) -> Manifest:
    merged = dict(old)
    for uri in touched:
        if uri in new:
            merged[uri] = new[uri]
        else:
            merged.pop(uri, None)
    return merged


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
    apply_project_relations(client, project_dir, config.projects_dir)


def _ingest_doc(config: ContextConfig, client: Any, doc_path: Path) -> None:
    staged = stage_doc(doc_path, config.staging_dir)
    _add_resource(client, staged, docs_target_uri(doc_path), f"BERIL doc {doc_path.name}")


def _add_resource(client: Any, path: Path, target_uri: str, reason: str) -> None:
    for attempt in range(1, ADD_RESOURCE_RETRIES + 1):
        try:
            client.add_resource(path=str(path), to=target_uri, reason=reason, wait=False)
            return
        except TRANSIENT_OV_ERRORS:
            if attempt == ADD_RESOURCE_RETRIES:
                raise
            time.sleep(ADD_RESOURCE_BACKOFF_SECONDS * attempt)


def _checkpoint_manifest(
    config: ContextConfig, new_manifest: Manifest, touched: set[str]
) -> None:
    if not touched:
        return
    current = load_manifest(_manifest_path(config))
    save_manifest(_manifest_path(config), _partial_manifest(current, new_manifest, touched))


def _remove_resource(client: Any, target_uri: str) -> None:
    client.rm(target_uri, recursive=True)


def _manifest_path(config: ContextConfig) -> Path:
    return config.state_dir / MANIFEST_FILENAME

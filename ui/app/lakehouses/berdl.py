"""BERDL MinIO-backed lakehouse source.

Reads the ``projects/`` tree from the public tenant prefix
(``tenant-general-warehouse/microbialdiscoveryforge/projects/`` by default) on
the BERDL MinIO endpoint and stages it locally so the existing
``RepositoryParser`` can walk it without modification.

Scope (PR 2): only ``projects/`` comes from MinIO. The parser also needs
``docs/``, ``atlas/``, ``ui/config/``, and ``.claude/skills/`` — those continue
to be read from the local ``repo_dir`` on disk. Sync materializes those as
symlinks into the cache root so the parser sees a unified tree:

    <cache>/
        projects/      ← downloaded fresh from MinIO each sync
        docs/          ← symlink → <repo_dir>/docs
        atlas/         ← symlink → <repo_dir>/atlas
        ui/            ← symlink → <repo_dir>/ui
        .claude/       ← symlink → <repo_dir>/.claude

Auth: a single service-account access/secret key pair, injected via env
(``BERIL_BERDL_MINIO_ACCESS_KEY`` / ``BERIL_BERDL_MINIO_SECRET_KEY``). The
public archive is readable by this account; per-user credentials are out of
scope for this PR and will arrive with the chat / agent-SDK work.

Connectivity: BERIL on ``beril.kbase.us`` has direct access to
``minio.berdl.kbase.us``. For off-cluster dev (e.g. docker-compose on a
laptop), point ``berdl_https_proxy`` at the local pproxy bridge —
``aioboto3`` will route MinIO traffic through it and leave other outbound
calls alone.

TODO: ``is_available()`` should HEAD the MinIO endpoint so /health can report
a meaningful reachability state. Currently returns True like the legacy
adapter; revisit when /health gains real probes.
"""

import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import aioboto3
from aiobotocore.config import AioConfig

from app.config import Settings
from app.dataloader import RepositoryParser
from app.lakehouses.base import SyncResult

logger = logging.getLogger(__name__)

# Subdirectories the parser reads from repo_dir but the BERDL archive doesn't
# carry. Symlinked into the staged tree on each sync so the parser sees a
# unified root. When any of these gain a separate source, drop it from this
# list and add a real fetch.
_LOCAL_SUBDIRS = ("docs", "atlas", "ui", ".claude")


class BERDLLakehouse:
    name = "berdl"

    def __init__(self, settings: Settings) -> None:
        if not settings.berdl_minio_access_key or not settings.berdl_minio_secret_key:
            raise ValueError(
                "BERDL lakehouse requires berdl_minio_access_key and "
                "berdl_minio_secret_key. Set BERIL_BERDL_MINIO_ACCESS_KEY and "
                "BERIL_BERDL_MINIO_SECRET_KEY in the environment."
            )
        self._settings = settings
        self._session = aioboto3.Session()

    async def sync(self) -> SyncResult:
        s = self._settings
        cache_root = Path(s.lakehouse_cache_dir)

        # Download into an ephemeral staging dir so an interrupted sync never
        # leaves the live cache half-updated.
        staging_root = cache_root / f".staging-{uuid.uuid4().hex[:8]}"
        staging_projects = staging_root / "projects"
        staging_projects.mkdir(parents=True, exist_ok=True)

        try:
            await self._download_prefix(
                bucket=s.berdl_minio_bucket,
                prefix=s.berdl_projects_prefix,
                dest=staging_projects,
            )

            # Atomic swap: rename staged projects/ over the live one. shutil.move
            # is used (not os.replace) because the destination may be a directory
            # that needs full removal first — see _atomic_swap.
            live_projects = cache_root / "projects"
            self._atomic_swap(staging_projects, live_projects)
        finally:
            # Clean up the staging skeleton regardless of outcome.
            if staging_root.exists():
                shutil.rmtree(staging_root, ignore_errors=True)

        # Re-create symlinks for the parser's other walk targets. Done after
        # the swap so a partial sync can't leave dangling links pointing into
        # a deleted staging dir.
        self._link_local_subdirs(cache_root, s.repo_dir)

        # Parse the unified tree.
        parser = RepositoryParser(repo_path=cache_root)
        repo_data = parser.parse_all()
        logger.info(
            "BERDL sync complete. Last updated: %s", repo_data.last_updated,
        )

        return SyncResult(
            repo_data=repo_data,
            projects_dir=cache_root / "projects",
            source_name=self.name,
            last_updated=repo_data.last_updated,
        )

    async def is_available(self) -> bool:
        """TODO: actually probe the MinIO endpoint (HEAD on the bucket).
        Currently mirrors the legacy adapter and always returns True; the
        sync() failure path is the real signal."""
        return True

    # ------------------------------------------------------------------
    # S3 helpers
    # ------------------------------------------------------------------

    async def _download_prefix(self, *, bucket: str, prefix: str, dest: Path) -> None:
        """List every object under ``prefix`` and download in parallel into
        ``dest``. Preserves the relative path from ``prefix``."""
        s = self._settings
        config = AioConfig(proxies={"https": s.berdl_https_proxy}) if s.berdl_https_proxy else None

        async with self._session.client(
            "s3",
            endpoint_url=s.berdl_minio_endpoint,
            aws_access_key_id=s.berdl_minio_access_key,
            aws_secret_access_key=s.berdl_minio_secret_key,
            config=config,
        ) as client:
            keys = await self._list_keys(client, bucket=bucket, prefix=prefix)
            logger.info("BERDL: downloading %d objects from %s/%s", len(keys), bucket, prefix)
            # Bound parallelism — MinIO will happily serve, but FDs and memory
            # aren't free. 16 in flight is a small load on the server and a
            # safe ceiling on a service host.
            sem = asyncio.Semaphore(16)
            await asyncio.gather(*(
                self._download_one(client, sem, bucket=bucket, key=key, prefix=prefix, dest=dest)
                for key in keys
            ))

    async def _list_keys(self, client: Any, *, bucket: str, prefix: str) -> list[str]:
        """Paginated list — list_objects_v2 caps at 1000 per page."""
        keys: list[str] = []
        paginator = client.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []) or []:
                # Skip "directory marker" zero-byte objects MinIO sometimes emits.
                if obj["Key"].endswith("/"):
                    continue
                keys.append(obj["Key"])
        return keys

    async def _download_one(
        self,
        client: Any,
        sem: asyncio.Semaphore,
        *,
        bucket: str,
        key: str,
        prefix: str,
        dest: Path,
    ) -> None:
        async with sem:
            # Relative path inside the staged projects/ tree.
            relative = key[len(prefix):] if key.startswith(prefix) else key
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            # download_file streams to disk — avoids loading large blobs in RAM.
            await client.download_file(bucket, key, str(target))

    # ------------------------------------------------------------------
    # Local filesystem helpers
    # ------------------------------------------------------------------

    def _atomic_swap(self, src: Path, dest: Path) -> None:
        """Replace ``dest`` (directory) with ``src`` (directory) atomically.

        ``os.replace`` on a directory only succeeds if the destination is also
        a directory and is empty on some filesystems. To stay portable we move
        the existing destination aside, rename src into place, then delete the
        old one. Not strictly atomic across the two renames, but the window is
        small and the parser is only invoked after this completes.
        """
        if dest.exists():
            attic = dest.with_name(dest.name + f".old-{uuid.uuid4().hex[:8]}")
            os.replace(dest, attic)
            try:
                os.replace(src, dest)
            except Exception:
                # Restore the previous state on failure so we don't end up
                # with no projects/ at all.
                os.replace(attic, dest)
                raise
            shutil.rmtree(attic, ignore_errors=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(src, dest)

    def _link_local_subdirs(self, cache_root: Path, repo_dir: Path) -> None:
        """Symlink the subdirectories the parser reads from local disk into
        the cache root so a single RepositoryParser(repo_path=cache_root) sees
        a complete tree."""
        cache_root.mkdir(parents=True, exist_ok=True)
        for name in _LOCAL_SUBDIRS:
            link = cache_root / name
            target = repo_dir / name
            if link.is_symlink() or link.exists():
                # Re-link in case repo_dir has shifted (rare, but cheap to handle).
                if link.is_symlink() or link.is_file():
                    link.unlink()
                else:
                    # An actual directory at this path would shadow the link
                    # silently — refuse rather than overwrite real data.
                    raise RuntimeError(
                        f"Refusing to overwrite real directory at {link}; "
                        "expected a symlink or absent path."
                    )
            link.symlink_to(target, target_is_directory=True)

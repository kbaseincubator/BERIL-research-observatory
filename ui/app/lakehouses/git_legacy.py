"""Git-backed lakehouse source (legacy).

Wraps the existing ``ensure_repo_cloned`` + ``pull_latest`` + ``load_repository_data``
flow under the ``LakehouseSource`` interface so call sites stop branching on
``settings.data_repo_url``. Behavior is preserved exactly:

- If ``data_repo_url`` is set, shallow-clone (or pull) into ``data_repo_path``
  and load ``data_cache/data.pkl.gz`` from there. On any failure, fall back to
  parsing ``repo_dir`` directly — matches the existing logic in
  ``initialize_data``.
- If ``force_local_data`` is set, skip the git flow entirely.
- Otherwise, parse ``repo_dir`` directly.

This adapter exists so a future MinIO-backed source can slot in without
touching the parser or routes. Once the new source is the default, this
adapter can be removed alongside the ``data_repo_*`` settings.
"""

import logging
from pathlib import Path

from app.config import Settings
from app.dataloader import load_repository_data
from app.git_data_sync import ensure_repo_cloned, pull_latest
from app.lakehouses.base import SyncResult

logger = logging.getLogger(__name__)


class GitLegacyLakehouse:
    name = "git"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # Track whether we've already cloned this process — controls
        # clone-vs-pull on subsequent sync() calls (the webhook path).
        self._cloned = False

    async def sync(self) -> SyncResult:
        s = self._settings

        if s.force_local_data:
            logger.info("force_local_data set — parsing local repository directly")
            return self._parse_local()

        if s.data_repo_url:
            try:
                if self._cloned:
                    logger.info("Pulling latest changes for branch %s", s.data_repo_branch)
                    await pull_latest(s.data_repo_path, s.data_repo_branch)
                else:
                    logger.info("Syncing data from git repository: %s", s.data_repo_url)
                    await ensure_repo_cloned(
                        s.data_repo_url, s.data_repo_branch, s.data_repo_path
                    )
                    self._cloned = True

                data_file = s.data_repo_path / "data_cache" / "data.pkl.gz"
                repo_data = load_repository_data(data_file)
                logger.info(
                    "Repository data loaded from git. Last updated: %s",
                    repo_data.last_updated,
                )
                return SyncResult(
                    repo_data=repo_data,
                    projects_dir=s.data_repo_path / "projects",
                    source_name=self.name,
                    last_updated=repo_data.last_updated,
                )
            except Exception as e:
                logger.error("Failed to load from git repo: %s", e)
                logger.info("Falling back to local parsing")
                return self._parse_local()

        logger.info("No git repo configured, parsing local files")
        return self._parse_local()

    def _parse_local(self) -> SyncResult:
        """Parse ``repo_dir`` in place — used for the no-git-configured and
        fallback paths. Matches the original ``load_repository_data(None)`` call."""
        repo_data = load_repository_data(None)
        return SyncResult(
            repo_data=repo_data,
            projects_dir=self._settings.repo_dir / "projects",
            source_name=self.name,
            last_updated=repo_data.last_updated,
        )

    async def is_available(self) -> bool:
        """Always True — the git flow falls back to local parsing on any failure,
        so there is no useful "unavailable" state to surface."""
        return True

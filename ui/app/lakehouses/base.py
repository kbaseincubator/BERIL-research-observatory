"""Lakehouse source protocol.

A ``LakehouseSource`` knows how to materialize the project tree and parse it
into a ``RepositoryData`` object. Implementations are picked at startup from
``settings.lakehouse_source`` and called from both the app's startup hook and
the data-update webhook.

The protocol is intentionally small. Implementations own their own retries,
fallbacks, and atomicity — callers just await ``sync()`` and react to the
result.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from app.models import RepositoryData


@dataclass
class SyncResult:
    """Outcome of a successful sync.

    - ``repo_data`` is the parsed catalog the app serves.
    - ``projects_dir`` is the filesystem root containing ``<slug>/`` subtrees;
      callers (the importer, the static mount) read from this path.
    - ``source_name`` identifies which lakehouse produced this result, for
      logging and the webhook response payload.
    - ``last_updated`` echoes ``repo_data.last_updated`` for convenience — the
      webhook response wants it without unpacking the larger object.
    """
    repo_data: RepositoryData
    projects_dir: Path
    source_name: str
    last_updated: datetime | None


class LakehouseSource(Protocol):
    name: str

    async def sync(self) -> SyncResult:
        """Fetch the latest project tree and return the parsed result.

        Implementations should be idempotent — the webhook calls this on every
        notification, and startup calls it once.
        """
        ...

    async def is_available(self) -> bool:
        """Quick reachability check used by the health endpoint."""
        ...

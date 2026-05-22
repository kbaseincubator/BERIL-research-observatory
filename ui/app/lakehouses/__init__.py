"""Lakehouse source registry.

A *lakehouse source* materializes the project tree (READMEs, notebooks, data,
figures) onto local disk and parses it into a ``RepositoryData`` object. The
abstraction exists so the runtime can swap between the legacy git-clone flow
and future MinIO-backed flows without touching the parser or the route layer.

Exactly one source is active at a time, chosen by ``BERIL_LAKEHOUSE_SOURCE``.
The default is ``"git"`` — the legacy behavior — so deployments that don't opt
in to the new abstraction keep working unchanged.
"""

from app.config import Settings
from app.lakehouses.base import LakehouseSource, SyncResult
from app.lakehouses.berdl import BERDLLakehouse
from app.lakehouses.git_legacy import GitLegacyLakehouse


def get_lakehouse_source(settings: Settings) -> LakehouseSource:
    """Build the active lakehouse source from settings."""
    name = settings.lakehouse_source
    if name == "git":
        return GitLegacyLakehouse(settings)
    if name == "berdl":
        return BERDLLakehouse(settings)
    # Fail loud on unknown names rather than silently falling back — a typo
    # here would otherwise quietly downgrade prod to a different data flow.
    raise ValueError(f"Unknown lakehouse source: {name!r}")


__all__ = [
    "LakehouseSource",
    "SyncResult",
    "get_lakehouse_source",
]

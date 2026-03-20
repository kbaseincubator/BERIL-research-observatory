"""Runtime helpers for live and offline OpenViking workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from observatory_context.client import OpenVikingObservatoryClient
from observatory_context.config import ObservatoryContextSettings
from observatory_context.service import ObservatoryContextService


def build_client(
    settings: ObservatoryContextSettings | None = None,
) -> OpenVikingObservatoryClient:
    """Construct the OpenViking client wrapper."""
    return OpenVikingObservatoryClient(settings or ObservatoryContextSettings())


def build_service(
    repo_root: Path,
    offline: bool = False,
    require_live: bool = False,
    client: Any | None = None,
) -> ObservatoryContextService:
    """Build a service in offline or live-backed mode."""
    if offline:
        return ObservatoryContextService(repo_root=repo_root, client=None)

    resolved_client = client or build_client()
    if require_live and not resolved_client.health():
        raise RuntimeError("OpenViking server is not reachable")
    return ObservatoryContextService(repo_root=repo_root, client=resolved_client)

from __future__ import annotations

import socket
from typing import Any
from urllib.parse import urlparse

from .config import ContextConfig


LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
PROBE_TIMEOUT_SECONDS = 1.0
LOCAL_START_HINT = (
    "OpenViking does not appear to be running at {url}.\n"
    "Start it in another terminal:\n"
    "  uv run --group knowledge openviking-server --config knowledge/openviking/ov.conf"
)
REMOTE_HINT = (
    "Cannot reach OpenViking at {url}.\n"
    "Verify OPENVIKING_URL is correct and the server is reachable."
)


def create_client(config: ContextConfig) -> Any:
    import openviking as ov

    _ensure_reachable(config.openviking_url)
    client = ov.SyncHTTPClient(
        url=config.openviking_url,
        api_key=config.openviking_api_key,
    )
    client.initialize()
    return client


def server_reachable(config: ContextConfig) -> bool:
    """Probe the configured OpenViking server without raising.

    Used by the query CLI to decide between online queries and the local
    fallback. Ingest still uses ``create_client``/``_ensure_reachable`` so its
    write path fails cleanly when the server is down.
    """
    return _probe(config.openviking_url)


def _probe(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname
    if host is None:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=PROBE_TIMEOUT_SECONDS):
            return True
    except OSError:
        return False


def _ensure_reachable(url: str) -> None:
    if urlparse(url).hostname is None:
        raise SystemExit(f"Invalid OPENVIKING_URL: {url!r}")
    if _probe(url):
        return
    host = urlparse(url).hostname
    template = LOCAL_START_HINT if host in LOCAL_HOSTS else REMOTE_HINT
    raise SystemExit(template.format(url=url))

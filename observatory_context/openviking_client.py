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


def _ensure_reachable(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if host is None:
        raise SystemExit(f"Invalid OPENVIKING_URL: {url!r}")
    try:
        with socket.create_connection((host, port), timeout=PROBE_TIMEOUT_SECONDS):
            return
    except OSError:
        template = LOCAL_START_HINT if host in LOCAL_HOSTS else REMOTE_HINT
        raise SystemExit(template.format(url=url))

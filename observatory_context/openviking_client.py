from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

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


# --- Health / auth diagnostics --------------------------------------------
#
# Two tiers, so a failing query can be pinned on the server vs. the client:
#   1. Reachability — GET {url}/health (public, no auth). Tells "is the server
#      up and is the URL/proxy right".
#   2. Auth — an authenticated OV call with OPENVIKING_API_KEY. Tells "is my
#      key valid" (distinguished from the server being down).

DIAGNOSE_TIMEOUT_SECONDS = 5.0

_SETUP_HINT = (
    "No API key configured. Get one with the setup helper:\n"
    "  uv run knowledge/scripts/setup_remote_ov.py --cookie '<beril_session>'\n"
    "See docs/remote-openviking-setup.md."
)
_REGEN_HINT = (
    "Your API key was rejected — it is invalid or expired. Mint a fresh one:\n"
    "  uv run knowledge/scripts/setup_remote_ov.py --cookie '<beril_session>' --regenerate"
)

# OV SDK exceptions that unambiguously mean "the key is bad", matched by class
# name so we don't hard-depend on the SDK's import path here.
_AUTH_EXCEPTION_NAMES = frozenset(
    {"UnauthenticatedError", "PermissionDeniedError", "SessionExpiredError"}
)
_AUTH_MESSAGE_MARKERS = (
    "unauthenticated",
    "unauthorized",
    "permission denied",
    "invalid api key",
    "invalid key",
    "401",
    "403",
)

_VERDICT_LABELS = {
    "ok": "OK",
    "unreachable": "UNREACHABLE",
    "unhealthy": "UNHEALTHY",
    "no_key": "NO API KEY",
    "auth_failed": "AUTH FAILED",
    "error": "ERROR",
}


@dataclass(frozen=True)
class Diagnosis:
    """Structured result of :func:`diagnose`.

    ``verdict`` is one of ``ok``, ``unreachable``, ``unhealthy``, ``no_key``,
    ``auth_failed``, ``error``. ``remedy`` is a human-readable next step (empty
    when ``ok``); ``server`` is the parsed ``/health`` body when reachable.
    """

    verdict: str
    url: str
    reachable: bool
    detail: str
    remedy: str = ""
    server: dict | None = None

    @property
    def ok(self) -> bool:
        return self.verdict == "ok"


def _health_url(url: str) -> str:
    return f"{url.rstrip('/')}/health"


def _http_health(url: str, timeout: float) -> dict | None:
    """GET ``{url}/health`` (no auth). Body dict on 200, ``{}`` if non-JSON,
    ``None`` if the server can't be reached or answers non-200."""
    try:
        response = httpx.get(_health_url(url), timeout=timeout)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _requires_key(health: dict) -> bool:
    """Whether the server enforces client auth, per its ``/health`` report."""
    mode = str(health.get("auth_mode") or "").lower()
    return mode not in ("", "none", "disabled", "off")


def _is_auth_error(exc: BaseException) -> bool:
    if type(exc).__name__ in _AUTH_EXCEPTION_NAMES:
        return True
    text = str(exc).lower()
    return any(marker in text for marker in _AUTH_MESSAGE_MARKERS)


def _probe_auth(config: ContextConfig, timeout: float) -> tuple[str, str]:
    """Attempt one authenticated OV call. Returns ``(status, detail)`` where
    status is ``ok`` (key works), ``auth_failed`` (key rejected), or ``error``
    (reachable but the call failed for another reason)."""
    client = None
    try:
        client = create_client(config)
        client.get_status()
        return "ok", ""
    except SystemExit as exc:  # _ensure_reachable hint — treat as transport
        return "error", str(exc)
    except Exception as exc:
        return ("auth_failed" if _is_auth_error(exc) else "error"), str(exc)
    finally:
        close = getattr(client, "close", None)
        if close:
            try:
                close()
            except Exception:
                pass


def diagnose(config: ContextConfig, *, timeout: float = DIAGNOSE_TIMEOUT_SECONDS) -> Diagnosis:
    """Classify OpenViking availability into a reachability + auth verdict."""
    url = config.openviking_url
    health = _http_health(url, timeout)
    if health is None:
        host = urlparse(url).hostname
        remedy = (LOCAL_START_HINT if host in LOCAL_HOSTS else REMOTE_HINT).format(url=url)
        return Diagnosis(
            "unreachable", url, False,
            detail=f"OpenViking is not reachable at {url}.",
            remedy=remedy,
        )
    if health.get("healthy") is False or health.get("status") == "error":
        return Diagnosis(
            "unhealthy", url, True, server=health,
            detail=f"OpenViking at {url} is reachable but reports unhealthy.",
            remedy="Server-side issue — check the OpenViking deployment/logs.",
        )
    if not _requires_key(health):
        return Diagnosis(
            "ok", url, True, server=health,
            detail=f"OpenViking at {url} is reachable (no client auth required).",
        )
    if not config.openviking_api_key:
        return Diagnosis(
            "no_key", url, True, server=health,
            detail=f"OpenViking at {url} requires an API key, but OPENVIKING_API_KEY is not set.",
            remedy=_SETUP_HINT,
        )
    status, note = _probe_auth(config, timeout)
    if status == "ok":
        return Diagnosis(
            "ok", url, True, server=health,
            detail=f"OpenViking at {url} is reachable and your API key is valid.",
        )
    if status == "auth_failed":
        return Diagnosis(
            "auth_failed", url, True, server=health,
            detail=f"OpenViking at {url} is reachable, but your API key was rejected.",
            remedy=_REGEN_HINT,
        )
    return Diagnosis(
        "error", url, True, server=health,
        detail=f"OpenViking at {url} is reachable, but an authenticated call failed ({note}).",
        remedy="Unexpected error — retry, or check the OpenViking server logs.",
    )


def format_diagnosis(diag: Diagnosis) -> str:
    """Render a :class:`Diagnosis` as a short human-readable block."""
    label = _VERDICT_LABELS.get(diag.verdict, diag.verdict)
    lines = [f"OpenViking: {label}  ({diag.url})", diag.detail]
    if diag.server:
        meta = ", ".join(
            part
            for part in (
                f"version {diag.server['version']}" if diag.server.get("version") else "",
                f"auth_mode {diag.server['auth_mode']}" if diag.server.get("auth_mode") else "",
            )
            if part
        )
        if meta:
            lines.append(f"  server: {meta}")
    if diag.remedy:
        lines.extend(["", diag.remedy])
    return "\n".join(lines)

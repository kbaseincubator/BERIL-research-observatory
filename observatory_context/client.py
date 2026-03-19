"""Thin wrapper around the OpenViking HTTP client."""

from __future__ import annotations

from typing import Any

from observatory_context.config import ObservatoryContextSettings


class OpenVikingObservatoryClient:
    """Lazy OpenViking client wrapper used by repo scripts."""

    def __init__(self, settings: ObservatoryContextSettings) -> None:
        self.settings = settings
        self._client: Any | None = None

    def initialize(self) -> None:
        if self._client is not None:
            return
        try:
            import openviking
        except ImportError as exc:
            raise RuntimeError(
                "openviking is not installed. Run `uv sync` or `uv run --with openviking ...`."
            ) from exc

        self._client = openviking.SyncHTTPClient(
            url=self.settings.openviking_url,
            api_key=self.settings.openviking_api_key,
            agent_id=self.settings.openviking_agent_id,
        )
        self._client.initialize()

    @property
    def client(self) -> Any:
        if self._client is None:
            self.initialize()
        assert self._client is not None
        return self._client

    def add_resource(self, path: str, uri: str, reason: str, wait: bool = True) -> dict[str, Any]:
        return self.client.add_resource(path=path, to=uri, reason=reason, wait=wait)

    def list_resources(self, uri: str, recursive: bool = False) -> list[dict[str, Any]]:
        return self.client.ls(uri, recursive=recursive)

    def search(self, query: str, target_uri: str | None = None) -> list[dict[str, Any]]:
        if target_uri:
            return self.client.find(query, target_uri=target_uri)
        return self.client.find(query)


"""Thin wrapper around the OpenViking HTTP client."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import yaml

from observatory_context.config import ObservatoryContextSettings
from observatory_context.ingest.manifest import ResourceManifestItem


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

    def wait_until_processed(self, timeout: float | None = None) -> dict[str, Any]:
        return self.client.wait_processed(timeout=timeout)

    def list_resources(self, uri: str, recursive: bool = False) -> list[dict[str, Any]]:
        return self.client.ls(uri, recursive=recursive)

    def search(self, query: str, target_uri: str | None = None) -> list[dict[str, Any]]:
        if target_uri:
            return self.client.find(query, target_uri=target_uri)
        return self.client.find(query)

    def read_resource(self, uri: str) -> str:
        return self.client.read(uri)

    def stat_resource(self, uri: str) -> dict[str, Any]:
        return self.client.stat(uri)

    def resource_exists(self, uri: str) -> bool:
        try:
            self.stat_resource(uri)
        except Exception as exc:
            if exc.__class__.__name__ == "NotFoundError":
                return False
            raise
        return True

    def make_directory(self, uri: str) -> None:
        self.client.mkdir(uri)

    def health(self) -> bool:
        return bool(self.client.health())

    def get_status(self) -> dict[str, Any]:
        return dict(self.client.get_status())

    def link_resources(self, from_uri: str, uris: list[str], reason: str = "") -> None:
        self.client.link(from_uri, uris=uris, reason=reason)

    def relations(self, uri: str) -> list[dict[str, Any]]:
        return self.client.relations(uri)

    def add_text_resource(
        self,
        uri: str,
        content: str,
        metadata: dict[str, Any],
        reason: str,
        wait: bool = True,
    ) -> dict[str, Any]:
        with NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write("---\n")
            handle.write(yaml.safe_dump(metadata, sort_keys=True))
            handle.write("---\n\n")
            handle.write(content)
        try:
            return self.add_resource(path=str(temp_path), uri=uri, reason=reason, wait=wait)
        finally:
            temp_path.unlink(missing_ok=True)

    def add_manifest_resource(self, item: ResourceManifestItem, wait: bool = True) -> dict[str, Any]:
        source_path = Path(item.source_path)
        if item.kind == "figure":
            caption = item.metadata.get("caption") or item.metadata.get("title") or source_path.name
            content = f"Figure resource for {caption}\nSource artifact: {source_path}\n"
        else:
            content = source_path.read_text(encoding="utf-8")
        return self.add_text_resource(
            uri=item.uri,
            content=content,
            metadata=item.metadata,
            reason=f"Ingest {item.kind} from BERIL observatory manifest",
            wait=wait,
        )

"""Deterministic overlay builders for tracked knowledge YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from observatory_context.service import ObservatoryContextService


class OverlayMaterializationError(ValueError):
    """Raised when overlay-critical metadata is missing from a resource."""


@dataclass(frozen=True, slots=True)
class OverlayDocument:
    """Deterministic representation of one materialized overlay file."""

    uri: str
    relative_path: str
    payload: dict[str, Any]


def build_raw_knowledge_overlays(service: ObservatoryContextService) -> list[OverlayDocument]:
    """Build deterministic overlay payloads from tracked raw knowledge resources."""
    resources = [
        resource
        for resource in service.all_resources().values()
        if resource.kind == "knowledge_document" and "raw-knowledge" in resource.tags
    ]
    resources.sort(key=lambda resource: resource.uri)

    overlays: list[OverlayDocument] = []
    for resource in resources:
        relative_path = resource.metadata.get("overlay_relative_path")
        if not isinstance(relative_path, str) or not relative_path:
            raise OverlayMaterializationError(f"Resource {resource.uri} is missing overlay_relative_path metadata")
        root_key = resource.metadata.get("overlay_root_key")
        if not isinstance(root_key, str) or not root_key:
            raise OverlayMaterializationError(f"Resource {resource.uri} is missing overlay_root_key metadata")
        payload = _load_overlay_payload(resource.uri, resource.body, root_key)
        overlays.append(OverlayDocument(uri=resource.uri, relative_path=relative_path, payload=payload))

    overlays.sort(key=lambda overlay: overlay.relative_path)
    return overlays


def _load_overlay_payload(uri: str, body: str | None, root_key: str) -> dict[str, Any]:
    if body is None:
        raise OverlayMaterializationError(f"Resource {uri} is missing YAML body content")
    payload = yaml.safe_load(body)
    if not isinstance(payload, dict):
        raise OverlayMaterializationError(f"Resource {uri} did not parse as a YAML mapping")
    if root_key not in payload:
        raise OverlayMaterializationError(f"Resource {uri} is missing required root key '{root_key}'")
    return payload

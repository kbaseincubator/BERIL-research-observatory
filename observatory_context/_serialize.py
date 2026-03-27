"""Shared YAML serialization for deterministic exports and overlays."""

from __future__ import annotations

from scripts.build_registry import yaml_dump


def dump_yaml(payload: dict[str, object]) -> str:
    """Serialize a payload using the repository YAML format."""
    return yaml_dump(payload)

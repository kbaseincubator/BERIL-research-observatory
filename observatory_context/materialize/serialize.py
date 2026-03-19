"""YAML serialization helpers for deterministic Phase 3 exports."""

from __future__ import annotations

from pathlib import Path

from scripts.build_registry import yaml_dump


def dump_yaml_export(payload: dict[str, object]) -> str:
    """Serialize an export payload using the repository YAML format."""
    return yaml_dump(payload)


def write_yaml_export(path: Path, payload: dict[str, object]) -> None:
    """Write a serialized export payload to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_yaml_export(payload), encoding="utf-8")

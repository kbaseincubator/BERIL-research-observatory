"""Serialization helpers for deterministic overlay materialization."""

from __future__ import annotations

from pathlib import Path

from scripts.build_registry import yaml_dump

from observatory_context.overlays.materialize import OverlayDocument


def dump_overlay_yaml(payload: dict[str, object]) -> str:
    """Serialize an overlay payload using the repository YAML format."""
    return yaml_dump(payload)


def write_overlay_documents(output_dir: Path, overlays: list[OverlayDocument]) -> None:
    """Write overlay payloads into a deterministic output directory."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    for overlay in overlays:
        output_path = root / overlay.relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dump_overlay_yaml(overlay.payload), encoding="utf-8")

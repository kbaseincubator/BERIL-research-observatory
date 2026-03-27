"""Deterministic Phase 4 overlay materialization helpers."""

from observatory_context.overlays.materialize import (
    OverlayDocument,
    OverlayMaterializationError,
    build_raw_knowledge_overlays,
)
from observatory_context.overlays.serialize import dump_overlay_yaml, write_overlay_documents

__all__ = [
    "OverlayDocument",
    "OverlayMaterializationError",
    "build_raw_knowledge_overlays",
    "dump_overlay_yaml",
    "write_overlay_documents",
]

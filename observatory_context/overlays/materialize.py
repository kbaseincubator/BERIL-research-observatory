"""Deterministic overlay builders for tracked knowledge YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class OverlayMaterializationError(ValueError):
    """Raised when overlay-critical metadata is missing from a resource."""


@dataclass(frozen=True, slots=True)
class OverlayDocument:
    """Deterministic representation of one materialized overlay file."""

    uri: str
    relative_path: str
    payload: dict[str, Any]

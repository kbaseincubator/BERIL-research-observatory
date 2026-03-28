"""Shared YAML serialization for deterministic exports and overlays."""

from __future__ import annotations

import yaml


def dump_yaml(payload: dict[str, object]) -> str:
    """Serialize a payload using the repository YAML format."""
    return yaml.dump(
        payload,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )

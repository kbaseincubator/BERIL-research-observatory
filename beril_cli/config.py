"""User configuration for BERIL CLI (~/.config/beril/config.toml)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "beril"
CONFIG_PATH = CONFIG_DIR / "config.toml"


def load() -> dict[str, Any]:
    """Load user config. Returns empty dict if file doesn't exist."""
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def _toml_escape(val: str) -> str:
    """Escape a string for use inside a TOML double-quoted value."""
    return val.replace("\\", "\\\\").replace('"', '\\"')


def save(cfg: dict[str, Any]) -> None:
    """Write config to disk. Only supports the expected two-section shape."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    if "user" in cfg:
        lines.append("[user]")
        for key in ("name", "affiliation", "orcid"):
            val = cfg["user"].get(key, "")
            if val:
                lines.append(f'{key} = "{_toml_escape(val)}"')
        lines.append("")

    if "defaults" in cfg:
        lines.append("[defaults]")
        for key in ("agent",):
            val = cfg["defaults"].get(key, "")
            if val:
                lines.append(f'{key} = "{_toml_escape(val)}"')
        lines.append("")

    CONFIG_PATH.write_text("\n".join(lines) + "\n")


def get_default_agent() -> str:
    """Return the user's default agent, or 'claude' as fallback."""
    cfg = load()
    return cfg.get("defaults", {}).get("agent", "claude")

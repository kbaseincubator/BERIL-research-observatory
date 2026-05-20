"""beril user — show user identity from ~/.config/beril/config.toml."""

from __future__ import annotations

import argparse
import json
import sys

from beril_cli import config

_FIELDS = ("name", "affiliation", "orcid")
_LABELS = {"name": "Name", "affiliation": "Affiliation", "orcid": "ORCID"}


def run_user(args: argparse.Namespace) -> int:
    """Print user identity. Exit 0 if all fields present, 1 otherwise."""
    cfg = config.load()
    user = cfg.get("user", {}) if isinstance(cfg, dict) else {}
    values = {f: (user.get(f, "") or "").strip() for f in _FIELDS}
    missing = [f for f in _FIELDS if not values[f]]

    if args.json:
        json.dump(values, sys.stdout)
        sys.stdout.write("\n")
        if missing:
            print(
                "Missing field(s): " + ", ".join(missing) + ". Run `beril setup` to fill them in.",
                file=sys.stderr,
            )
        return 0 if not missing else 1

    if not any(values.values()):
        print("No user config found.", file=sys.stderr)
        print(
            "Run `beril setup` to configure your name, affiliation, and ORCID.",
            file=sys.stderr,
        )
        return 1

    width = max(len(_LABELS[f]) for f in _FIELDS) + 1
    for f in _FIELDS:
        label = (_LABELS[f] + ":").ljust(width + 1)
        print(f"{label} {values[f] or '(missing)'}")

    if missing:
        print(
            "\nMissing field(s): " + ", ".join(missing) + ". Run `beril setup` to fill them in.",
            file=sys.stderr,
        )
        return 1

    return 0

"""Load and apply curator corrections to per-project KGs.

Corrections are content-addressed against assertion/node ids, so they re-bind after re-extraction
and apply deterministically (sorted by correction id). See design spec §8.
"""

from __future__ import annotations

import json
import pathlib

import yaml

from .models import Correction, ProjectKG


def load_corrections(path: pathlib.Path) -> list[Correction]:
    """Read every ``*.yaml``/``*.json`` in *path*; each file is a list of correction dicts.

    Missing directory yields ``[]``. Results are sorted by correction id.
    """
    path = pathlib.Path(path)
    if not path.is_dir():
        return []
    corrections: list[Correction] = []
    for fp in sorted(path.iterdir()):
        if fp.suffix not in (".yaml", ".yml", ".json"):
            continue
        text = fp.read_text(encoding="utf-8")
        data = json.loads(text) if fp.suffix == ".json" else yaml.safe_load(text)
        for item in data or []:
            corrections.append(Correction.from_dict(item))
    corrections.sort(key=lambda c: c.id)
    return corrections


def apply_corrections(
    pkgs: list[ProjectKG], corrections: list[Correction]
) -> tuple[list[ProjectKG], list[tuple[str, str]]]:
    """Apply *corrections* to *pkgs* in id order.

    Returns the (mutated) packages and the list of force-merge node-id pairs.

    Kinds:
      - ``retract``: drop assertions whose id is in ``targets``.
      - ``fix-value``: set value fields on assertions whose id is in ``targets``.
      - ``reground``: set ``entity.curie = value['curie']`` for entities whose node is in ``targets``.
      - ``demote`` / ``promote``: set ``tier`` (from ``value['tier']``) on matching assertions.
      - ``force-merge``: collect ``(targets[0], targets[1])``.
    """
    force_merge_pairs: list[tuple[str, str]] = []
    for c in sorted(corrections, key=lambda x: x.id):
        targets = set(c.targets)
        if c.kind == "retract":
            for pkg in pkgs:
                pkg.assertions = [a for a in pkg.assertions if a.id not in targets]
        elif c.kind == "fix-value":
            for pkg in pkgs:
                for a in pkg.assertions:
                    if a.id in targets:
                        for k, v in c.value.items():
                            setattr(a, k, v)
        elif c.kind == "reground":
            curie = c.value.get("curie")
            for pkg in pkgs:
                for e in pkg.entities:
                    if e.node in targets:
                        e.curie = curie
        elif c.kind in ("demote", "promote"):
            tier = c.value.get("tier")
            if tier is not None:
                for pkg in pkgs:
                    for a in pkg.assertions:
                        if a.id in targets:
                            a.tier = tier
        elif c.kind == "force-merge":
            if len(c.targets) >= 2:
                force_merge_pairs.append((c.targets[0], c.targets[1]))
    return pkgs, force_merge_pairs

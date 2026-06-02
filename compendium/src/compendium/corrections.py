"""Load and apply curator corrections to per-project KGs.

Corrections are content-addressed against assertion/node ids, so they re-bind after re-extraction
and apply deterministically (sorted by correction id). See design spec §8.
"""

from __future__ import annotations

import copy
import json
import pathlib

import yaml

from .models import (
    Assertion,
    Correction,
    ProjectKG,
    TIER_ASSERTED,
    TIER_CONFLICT,
    TIER_GROUNDED,
    TIER_RETRACTED,
)


_KIND_ALIASES = {
    "fix-statement": "fix-value",
    "fix-qualifier": "fix-value",
    "reground-entity": "reground",
}


def _normalized_kind(kind: str) -> str:
    return _KIND_ALIASES.get(kind, kind)


def _record_retraction(pkg: ProjectKG, correction: Correction, assertion: Assertion) -> None:
    metadata = pkg.project.extraction.setdefault("corrections", [])
    metadata.append(
        {
            "id": correction.id,
            "kind": correction.kind,
            "normalized_kind": "retract",
            "target": getattr(assertion, "id", ""),
            "assertion": assertion.to_dict(),
        }
    )


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
        The retracted assertion is preserved in ``project.extraction["corrections"]`` with
        ``tier="retracted"`` for provenance.
      - ``fix-value`` / ``fix-statement`` / ``fix-qualifier``: set value fields on assertions
        whose id is in ``targets``.
      - ``reground`` / ``reground-entity``: set ``entity.curie = value['curie']`` for entities
        whose node is in ``targets``.
      - ``demote`` / ``promote`` / ``mark-conflict`` / ``resolve-conflict``: set ``tier`` on
        matching assertions.
      - ``force-merge``: collect ``(targets[0], targets[1])``.
      - ``force-split``: accepted as an explicit no-op; graph assembly has no anti-merge hook.
    """
    force_merge_pairs: list[tuple[str, str]] = []
    for c in sorted(corrections, key=lambda x: x.id):
        kind = _normalized_kind(c.kind)
        targets = set(c.targets)
        if kind == "retract":
            for pkg in pkgs:
                kept = []
                for a in pkg.assertions:
                    if a.id in targets:
                        retracted = copy.deepcopy(a)
                        retracted.tier = TIER_RETRACTED
                        _record_retraction(pkg, c, retracted)
                    else:
                        kept.append(a)
                pkg.assertions = kept
        elif kind == "fix-value":
            for pkg in pkgs:
                for a in pkg.assertions:
                    if a.id in targets:
                        for k, v in c.value.items():
                            setattr(a, k, v)
        elif kind == "reground":
            curie = c.value.get("curie")
            for pkg in pkgs:
                for e in pkg.entities:
                    if e.node in targets:
                        e.curie = curie
        elif kind in ("demote", "promote", "mark-conflict", "resolve-conflict"):
            tier = c.value.get("tier")
            if tier is None:
                tier = {
                    "demote": TIER_ASSERTED,
                    "promote": TIER_GROUNDED,
                    "mark-conflict": TIER_CONFLICT,
                    "resolve-conflict": TIER_GROUNDED,
                }[kind]
            if tier is not None:
                for pkg in pkgs:
                    for a in pkg.assertions:
                        if a.id in targets:
                            a.tier = tier
        elif kind == "force-merge":
            if len(c.targets) >= 2:
                force_merge_pairs.append((c.targets[0], c.targets[1]))
        elif kind == "force-split":
            continue
    return pkgs, force_merge_pairs

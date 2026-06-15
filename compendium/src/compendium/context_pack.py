"""Deterministic context pack builder for KG ingestion skills.

Context packs are script-level artifacts: they are pure functions of a project
directory and contain no LLM/model output.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from compendium.audit import audit_project
from compendium.models import (
    CONFIDENCE_LEVELS,
    PAGE_TYPES,
    SCIENTIFIC_EDGE_KINDS,
    STATEMENT_KINDS,
    STATEMENT_SCOPES,
    STATEMENT_TIERS,
)
from compendium.people import parse_authors

_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_NOTEBOOK_RE = re.compile(r"\b[\w./-]+\.ipynb\b")
_FIGURE_RE = re.compile(r"\bfigures/[\w./-]+\.(?:png|jpg|jpeg|svg|pdf)\b", re.IGNORECASE)

def build_context_pack(project_dir: Path) -> dict[str, Any]:
    """Build a deterministic, serializable context pack for ``project_dir``.

    Parameters
    ----------
    project_dir
        Path to a BERIL project directory.

    Returns
    -------
    dict
        JSON-serializable context pack with ``context_pack_hash`` populated.
    """
    project_dir = Path(project_dir)
    audit = audit_project(project_dir)
    source_files = audit["source_files"]
    source_anchors = audit["source_anchors"]

    pack: dict[str, Any] = {
        "context_pack_version": 2,
        "project": {
            "id": audit["id"],
            "title": _resolve_title(project_dir, audit["id"]),
            "status": _project_status(project_dir),
            "authors": _project_authors(project_dir),
            "metadata_source": audit["metadata_source"],
            "coverage": audit["coverage"],
        },
        "source_files": source_files,
        "source_sections": audit["source_sections"],
        "source_anchors": source_anchors,
        "candidate_terms": _candidate_terms(source_anchors),
        "asset_hints": _asset_hints(project_dir, source_files),
        "related_project_hints": [],
        "prior_statement_cards": [],
        "extraction_instructions": _extraction_instructions(),
        "allowed_vocabularies": _allowed_vocabularies(),
    }
    pack["context_pack_hash"] = _context_pack_hash(pack)
    return pack


def _load_beril(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "beril.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _first_h1(project_dir: Path, name: str) -> str | None:
    path = project_dir / name
    if not path.is_file():
        return None
    match = _H1_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def _resolve_title(project_dir: Path, project_id: str) -> str:
    beril = _load_beril(project_dir)
    title = beril.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return _first_h1(project_dir, "REPORT.md") or _first_h1(project_dir, "README.md") or project_id


def _project_status(project_dir: Path) -> str | None:
    status = _load_beril(project_dir).get("status")
    return status if isinstance(status, str) else None


def _project_authors(project_dir: Path) -> list[dict[str, Any]]:
    path = project_dir / "README.md"
    if not path.is_file():
        return []
    return [
        {"name": a.name, "orcid": a.orcid, "affiliation": a.affiliation}
        for a in parse_authors(path.read_text(encoding="utf-8"))
    ]


def _candidate_terms(source_anchors: list[dict[str, Any]]) -> dict[str, list[str]]:
    terms: dict[str, set[str]] = {}
    for anchor in source_anchors:
        terms.setdefault(anchor["kind"], set()).add(anchor["exact"])
    return {kind: sorted(values) for kind, values in sorted(terms.items())}


def context_pack_bytes(pack: dict[str, Any]) -> bytes:
    """Return canonical JSON bytes for deterministic file output/tests."""
    return json.dumps(
        pack,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _asset_hints(project_dir: Path, source_files: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    notebooks: set[str] = set()
    figures: set[str] = set()
    for source_file in source_files:
        if not source_file["path"].endswith(".md"):
            continue
        text = (project_dir / source_file["path"]).read_text(encoding="utf-8")
        notebooks.update(_NOTEBOOK_RE.findall(text))
        figures.update(_FIGURE_RE.findall(text))
    return {
        "notebooks": [{"path": path} for path in sorted(notebooks)],
        "figures": [{"path": path} for path in sorted(figures)],
    }


def _extraction_instructions() -> dict[str, Any]:
    return {
        "purpose": "Extract statement cards with exact evidence anchors from this deterministic context pack.",
        "requirements": [
            "Use only source text and hints present in this context pack.",
            "Every non-retracted statement card must include an evidence anchor.",
            "Use allowed vocabularies exactly as provided.",
            "Do not invent source documents, datasets, entities, relation types, or measurements.",
        ],
    }


def _allowed_vocabularies() -> dict[str, list[str]]:
    return {
        "statement_kinds": list(STATEMENT_KINDS),
        "statement_scopes": list(STATEMENT_SCOPES),
        "statement_tiers": list(STATEMENT_TIERS),
        "confidence": list(CONFIDENCE_LEVELS),
        "scientific_links": list(SCIENTIFIC_EDGE_KINDS),
        "page_types": list(PAGE_TYPES),
    }


def _context_pack_hash(pack: dict[str, Any]) -> str:
    without_hash = {key: value for key, value in pack.items() if key != "context_pack_hash"}
    return _sha256_bytes(context_pack_bytes(without_hash))


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()

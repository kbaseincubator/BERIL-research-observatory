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

from compendium.audit import audit_project
from compendium.extract.structural import extract_project
from compendium.models import (
    ASSERTION_KINDS,
    BIOLOGY_TYPES,
    CONFIDENCE_LEVELS,
    EDGE_CLASSES,
    PAGE_TYPES,
    SCIENTIFIC_EDGE_KINDS,
    STATEMENT_KINDS,
    STATEMENT_SCOPES,
    STATEMENT_TIERS,
    SYNTHESIS_TYPES,
)

_SOURCE_FILES = ("REPORT.md", "RESEARCH_PLAN.md", "REVIEW.md", "README.md", "beril.yaml")
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)
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
    kg = extract_project(project_dir, audit=audit)
    source_files = _source_files(project_dir)
    source_sections = _source_sections(project_dir, source_files)

    pack: dict[str, Any] = {
        "context_pack_version": 1,
        "project": {
            "id": kg.project.id,
            "title": kg.project.title,
            "status": kg.project.status,
            "authors": kg.project.authors,
            "metadata_source": audit["metadata_source"],
            "stage1_coverage": kg.project.stage1_coverage,
        },
        "source_files": source_files,
        "source_sections": source_sections,
        "deterministic_entities": _entities(kg),
        "deterministic_mentions": _mentions(kg),
        "evidence_anchors": _evidence_anchors(kg),
        "dataset_hints": _dataset_hints(kg),
        "asset_hints": _asset_hints(project_dir, source_files),
        "related_project_hints": [],
        "prior_statement_cards": [],
        "openviking_context_refs": [],
        "extraction_instructions": _extraction_instructions(),
        "allowed_vocabularies": _allowed_vocabularies(),
    }
    pack["context_pack_hash"] = _context_pack_hash(pack)
    return pack


def context_pack_bytes(pack: dict[str, Any]) -> bytes:
    """Return canonical JSON bytes for deterministic file output/tests."""
    return json.dumps(
        pack,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _source_files(project_dir: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for name in _SOURCE_FILES:
        path = project_dir / name
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({
            "path": name,
            "sha256": _sha256_bytes(data),
            "size_bytes": len(data),
        })
    return files


def _source_sections(project_dir: Path, source_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for source_file in source_files:
        path = source_file["path"]
        if not path.endswith(".md"):
            continue
        text = (project_dir / path).read_text(encoding="utf-8")
        sections.extend(_markdown_sections(path, text))
    return sorted(sections, key=lambda s: (s["source_doc"], s["start_line"], s["id"]))


def _markdown_sections(source_doc: str, text: str) -> list[dict[str, Any]]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        exact = text.strip()
        if not exact:
            return []
        return [_section_dict(source_doc, None, 1, 1, 0, len(text), exact)]

    line_starts = _line_starts(text)
    sections: list[dict[str, Any]] = []
    for i, match in enumerate(matches):
        level = len(match.group(1))
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        exact = text[match.start():body_end].strip()
        if not exact:
            continue
        heading = match.group(2).strip()
        sections.append(_section_dict(
            source_doc,
            heading,
            level,
            _line_at(line_starts, match.start()),
            match.start(),
            body_end,
            exact,
        ))
    return sections


def _section_dict(
    source_doc: str,
    heading: str | None,
    level: int,
    start_line: int,
    start_char: int,
    end_char: int,
    exact: str,
) -> dict[str, Any]:
    return {
        "id": _stable_id("section", source_doc, heading or "", str(start_char), exact),
        "source_doc": source_doc,
        "heading": heading,
        "level": level,
        "start_line": start_line,
        "char": [start_char, end_char],
        "text_hash": _sha256_text(exact),
        "text": exact,
    }


def _entities(kg: Any) -> list[dict[str, Any]]:
    return sorted(
        (entity.to_dict() for entity in kg.entities),
        key=lambda entity: (entity["type"], entity["label"], entity["node"]),
    )


def _mentions(kg: Any) -> list[dict[str, Any]]:
    return sorted(
        (mention.to_dict() for mention in kg.mentions),
        key=lambda mention: (mention["span"]["file"] if mention.get("span") else "", mention["id"]),
    )


def _evidence_anchors(kg: Any) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for assertion in kg.assertions:
        if assertion.evidence is None or assertion.evidence.span is None:
            continue
        span = assertion.evidence.span
        anchors.append({
            "id": _stable_id("anchor", assertion.id, span.file, span.quote),
            "source_project": kg.project.id,
            "source_doc": span.file,
            "source_section": span.heading,
            "assertion_id": assertion.id,
            "assertion_kind": assertion.kind,
            "exact": span.quote,
            "prefix": "",
            "suffix": "",
            "char": list(span.char),
            "notebook": assertion.evidence.notebook,
            "figure": assertion.evidence.figure,
            "p_value": assertion.evidence.p_value,
        })
    return sorted(anchors, key=lambda anchor: (anchor["source_doc"], anchor["char"], anchor["id"]))


def _dataset_hints(kg: Any) -> list[dict[str, Any]]:
    mentions_by_label: dict[str, list[dict[str, Any]]] = {}
    for mention in kg.mentions:
        if mention.type != "Dataset":
            continue
        mentions_by_label.setdefault(mention.label, []).append(mention.to_dict())

    hints: list[dict[str, Any]] = []
    for entity in kg.entities:
        if entity.type != "Dataset":
            continue
        hints.append({
            "node": entity.node,
            "label": entity.label,
            "curie": entity.curie,
            "mentions": sorted(mentions_by_label.get(entity.label, []), key=lambda m: m["id"]),
        })
    return sorted(hints, key=lambda hint: (hint["label"], hint["node"]))


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
        "legacy_assertion_kinds": list(ASSERTION_KINDS),
        "statement_scopes": list(STATEMENT_SCOPES),
        "statement_tiers": list(STATEMENT_TIERS),
        "confidence": list(CONFIDENCE_LEVELS),
        "entity_types": sorted(set(BIOLOGY_TYPES + SYNTHESIS_TYPES)),
        "edge_classes": list(EDGE_CLASSES),
        "scientific_links": list(SCIENTIFIC_EDGE_KINDS),
        "page_types": list(PAGE_TYPES),
    }


def _context_pack_hash(pack: dict[str, Any]) -> str:
    without_hash = {key: value for key, value in pack.items() if key != "context_pack_hash"}
    return _sha256_bytes(context_pack_bytes(without_hash))


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _stable_id(prefix: str, *parts: str) -> str:
    basis = "\x1f".join(parts)
    return f"{prefix}:{hashlib.blake2b(basis.encode('utf-8'), digest_size=8).hexdigest()}"


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for match in re.finditer("\n", text):
        starts.append(match.end())
    return starts


def _line_at(line_starts: list[int], char: int) -> int:
    line = 1
    for i, start in enumerate(line_starts, start=1):
        if start > char:
            break
        line = i
    return line

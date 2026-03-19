#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""
Validate semantic knowledge graph YAML files for shape and cross-file integrity.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
SKIP_PROJECTS = {"hackathon_demo"}

ENTITY_SPECS = {
    "organisms": ("entities/organisms.yaml", "organisms"),
    "genes": ("entities/genes.yaml", "genes"),
    "pathways": ("entities/pathways.yaml", "pathways"),
    "methods": ("entities/methods.yaml", "methods"),
    "concepts": ("entities/concepts.yaml", "concepts"),
}


def _load_yaml_dict(path: Path) -> tuple[dict, list[str]]:
    if not path.exists():
        return {}, [f"missing file: {path.relative_to(REPO_ROOT)}"]
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return {}, [f"invalid YAML in {path.relative_to(REPO_ROOT)}: {exc}"]
    if not isinstance(payload, dict):
        return {}, [f"{path.relative_to(REPO_ROOT)}: top-level content must be a mapping"]
    return payload, []


def _load_root_list(path: Path, root_key: str) -> tuple[list[dict], list[str]]:
    payload, errors = _load_yaml_dict(path)
    if errors:
        return [], errors
    rows = payload.get(root_key)
    if not isinstance(rows, list):
        return [], [f"{path.relative_to(REPO_ROOT)}: expected top-level '{root_key}' list"]
    return [row for row in rows if isinstance(row, dict)], []


def _known_project_ids() -> set[str]:
    return {
        project_dir.name
        for project_dir in PROJECTS_DIR.iterdir()
        if project_dir.is_dir()
        and project_dir.name not in SKIP_PROJECTS
        and (project_dir / "README.md").exists()
    }


def _check_duplicate_ids(rows: list[dict], label: str) -> tuple[set[str], list[str]]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        row_id = str(row.get("id", "")).strip()
        if not row_id:
            continue
        if row_id in seen:
            duplicates.add(row_id)
        seen.add(row_id)
    errors = [f"duplicate {label} ID: {row_id}" for row_id in sorted(duplicates)]
    return seen, errors


def validate_knowledge_graph() -> list[str]:
    errors: list[str] = []
    known_projects = _known_project_ids()

    entity_ids: set[str] = set()
    for label, (rel_path, root_key) in ENTITY_SPECS.items():
        rows, row_errors = _load_root_list(KNOWLEDGE_DIR / rel_path, root_key)
        errors.extend(row_errors)
        ids, dup_errors = _check_duplicate_ids(rows, label[:-1] if label.endswith("s") else label)
        entity_ids.update(ids)
        errors.extend(dup_errors)

        for row in rows:
            for project_id in row.get("projects", []) or []:
                project_text = str(project_id).strip()
                if project_text and project_text not in known_projects:
                    errors.append(
                        f"{rel_path}: entity '{row.get('id', '<missing-id>')}' references unknown project '{project_text}'"
                    )

    relations, relation_errors = _load_root_list(KNOWLEDGE_DIR / "relations.yaml", "relations")
    errors.extend(relation_errors)
    for relation in relations:
        subject = str(relation.get("subject", "")).strip()
        obj = str(relation.get("object", "")).strip()
        evidence_project = str(relation.get("evidence_project", "")).strip()

        if subject and subject not in entity_ids:
            errors.append(f"relations.yaml: relation references unknown subject '{subject}'")
        if obj and obj not in entity_ids:
            errors.append(f"relations.yaml: relation references unknown object '{obj}'")
        if evidence_project and evidence_project not in known_projects:
            errors.append(
                f"relations.yaml: relation references unknown evidence_project '{evidence_project}'"
            )

    hypotheses, hypothesis_errors = _load_root_list(KNOWLEDGE_DIR / "hypotheses.yaml", "hypotheses")
    errors.extend(hypothesis_errors)
    _, dup_errors = _check_duplicate_ids(hypotheses, "hypothesis")
    errors.extend(dup_errors)
    for hypothesis in hypotheses:
        hyp_id = str(hypothesis.get("id", "<missing-id>")).strip() or "<missing-id>"
        origin_project = str(hypothesis.get("origin_project", "")).strip()
        if origin_project and origin_project not in known_projects:
            errors.append(
                f"hypotheses.yaml: hypothesis '{hyp_id}' references unknown origin_project '{origin_project}'"
            )
        for entity_id in hypothesis.get("entities", []) or []:
            entity_text = str(entity_id).strip()
            if entity_text and entity_text not in entity_ids:
                errors.append(
                    f"hypotheses.yaml: hypothesis '{hyp_id}' references unknown entity '{entity_text}'"
                )

    events, event_errors = _load_root_list(KNOWLEDGE_DIR / "timeline.yaml", "events")
    errors.extend(event_errors)
    for event in events:
        event_ref = str(event.get("ref", "")).strip() or str(event.get("date", "")).strip() or "<missing-ref>"
        project = str(event.get("project", "")).strip()
        if project and project not in known_projects:
            errors.append(
                f"timeline.yaml: event '{event_ref}' references unknown project '{project}'"
            )
        for project_id in event.get("projects", []) or []:
            project_text = str(project_id).strip()
            if project_text and project_text not in known_projects:
                errors.append(
                    f"timeline.yaml: event '{event_ref}' references unknown project '{project_text}'"
                )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate semantic knowledge graph YAML files.")
    parser.parse_args([] if argv is None else argv)

    errors = validate_knowledge_graph()
    if errors:
        print("FAIL: knowledge graph validation errors detected.\n")
        for error in errors:
            print(f"- {error}")
        print(f"\nErrors: {len(errors)}")
        return 1

    print("PASS: knowledge graph YAML files are internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

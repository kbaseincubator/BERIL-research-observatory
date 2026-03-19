#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jsonschema>=4.23",
#   "pyyaml>=6.0",
# ]
# ///
"""
Validate provenance.yaml files against schema and repository integrity checks.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
SCHEMA_PATH = REPO_ROOT / "knowledge" / "schema" / "provenance.schema.json"
SKIP_PROJECTS = {"hackathon_demo"}


def _load_build_registry_module():
    module_path = REPO_ROOT / "scripts" / "build_registry.py"
    spec = importlib.util.spec_from_file_location("build_registry", module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Failed to load build_registry module from {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _normalize_doi(doi: str) -> str:
    doi = doi.strip()
    doi = re.sub(r"^https?://doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi


def _normalize_pmid(pmid: str) -> str:
    return re.sub(r"\D+", "", pmid.strip())


def _validate_project_provenance(
    project_dir: Path,
    data: dict,
    validator: Draft202012Validator,
    known_collections: set[str],
    all_project_ids: set[str],
) -> list[str]:
    project_id = project_dir.name
    errors: list[str] = []

    # JSON Schema validation
    for err in validator.iter_errors(data):
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{project_id}: schema error at {path}: {err.message}")

    refs = data.get("references", []) or []
    ref_ids = []
    for ref in refs:
        rid = str(ref.get("id", "")).strip()
        if rid:
            ref_ids.append(rid)
        doi = ref.get("doi")
        pmid = ref.get("pmid")
        url = ref.get("url")
        if doi:
            norm = _normalize_doi(str(doi))
            if not norm:
                errors.append(f"{project_id}: reference '{rid}' has empty DOI after normalization")
        if pmid:
            norm = _normalize_pmid(str(pmid))
            if not norm:
                errors.append(f"{project_id}: reference '{rid}' has invalid PMID")
        if not (doi or pmid or url):
            errors.append(f"{project_id}: reference '{rid}' must include at least one of DOI, PMID, or URL")
    if len(ref_ids) != len(set(ref_ids)):
        errors.append(f"{project_id}: duplicate reference IDs found in references")
    ref_id_set = set(ref_ids)

    # Data sources
    for ds in data.get("data_sources", []) or []:
        coll = ds.get("collection")
        if coll and coll not in known_collections:
            errors.append(f"{project_id}: unknown collection ID '{coll}' in data_sources")
        ref = ds.get("reference")
        if ref and ref not in ref_id_set:
            errors.append(f"{project_id}: data_sources reference '{ref}' not found in references")

    # Cross-project dependencies
    for dep in data.get("cross_project_deps", []) or []:
        dep_project = dep.get("project")
        if dep_project and dep_project not in all_project_ids:
            errors.append(
                f"{project_id}: cross_project_deps project '{dep_project}' does not exist"
            )

    # Findings
    findings = data.get("findings", []) or []
    finding_ids = [str(f.get("id", "")).strip() for f in findings if str(f.get("id", "")).strip()]
    if len(finding_ids) != len(set(finding_ids)):
        errors.append(f"{project_id}: duplicate finding IDs found in findings")

    for finding in findings:
        fid = finding.get("id", "<missing-id>")
        nb = finding.get("notebook")
        if nb and not (project_dir / "notebooks" / nb).exists():
            errors.append(f"{project_id}: finding '{fid}' notebook not found: notebooks/{nb}")
        for fig in finding.get("figures", []) or []:
            if not (project_dir / "figures" / fig).exists():
                errors.append(f"{project_id}: finding '{fid}' figure not found: figures/{fig}")
        for df in finding.get("data_files", []) or []:
            if not (project_dir / df).exists():
                errors.append(f"{project_id}: finding '{fid}' data_file not found: {df}")
        for ref in finding.get("references", []) or []:
            if ref not in ref_id_set:
                errors.append(
                    f"{project_id}: finding '{fid}' references unknown reference ID '{ref}'"
                )

    # Generated data
    for gd in data.get("generated_data", []) or []:
        file = gd.get("file")
        if file and not (project_dir / file).exists():
            errors.append(f"{project_id}: generated_data file not found: {file}")
        nb = gd.get("source_notebook")
        if nb and not (project_dir / "notebooks" / nb).exists():
            errors.append(
                f"{project_id}: generated_data source_notebook not found: notebooks/{nb}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate project provenance.yaml files.")
    parser.add_argument(
        "--project",
        help="Validate a single project by ID. Defaults to all projects with provenance.yaml.",
    )
    args = parser.parse_args()

    if not SCHEMA_PATH.exists():
        print(f"FAIL: schema file not found: {SCHEMA_PATH.relative_to(REPO_ROOT)}")
        return 1

    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    build_registry = _load_build_registry_module()
    known_collections = set(build_registry.KNOWN_COLLECTIONS)

    all_project_dirs = [
        d
        for d in sorted(PROJECTS_DIR.iterdir())
        if d.is_dir() and d.name not in SKIP_PROJECTS and (d / "README.md").exists()
    ]
    all_project_ids = {d.name for d in all_project_dirs}

    if args.project:
        project_dir = PROJECTS_DIR / args.project
        if not project_dir.is_dir():
            print(f"FAIL: project not found: {args.project}")
            return 1
        project_dirs = [project_dir]
    else:
        project_dirs = [d for d in all_project_dirs if (d / "provenance.yaml").exists()]

    if not project_dirs:
        print("PASS: no provenance.yaml files found (nothing to validate).")
        return 0

    all_errors: list[str] = []
    validated = 0
    for project_dir in project_dirs:
        prov_path = project_dir / "provenance.yaml"
        if not prov_path.exists():
            if args.project:
                print(f"FAIL: provenance file not found for {project_dir.name}")
                return 1
            continue
        try:
            data = yaml.safe_load(prov_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            all_errors.append(f"{project_dir.name}: invalid YAML: {e}")
            continue
        if not isinstance(data, dict):
            all_errors.append(f"{project_dir.name}: provenance top-level must be a mapping")
            continue

        errs = _validate_project_provenance(
            project_dir=project_dir,
            data=data,
            validator=validator,
            known_collections=known_collections,
            all_project_ids=all_project_ids,
        )
        all_errors.extend(errs)
        validated += 1

    if all_errors:
        print("FAIL: provenance validation errors detected.\n")
        for err in all_errors:
            print(f"- {err}")
        print(f"\nValidated files: {validated}, errors: {len(all_errors)}")
        return 1

    print(f"PASS: validated {validated} provenance.yaml file(s) with no errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

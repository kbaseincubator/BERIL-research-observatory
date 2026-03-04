#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""
Validate that committed registry artifacts match the current project sources.

This script regenerates registry structures in-memory using scripts/build_registry.py
and compares them to the committed docs artifacts (ignoring generated timestamps).
It fails with exit code 1 when artifacts are stale.
"""

from __future__ import annotations

import copy
import difflib
import importlib.util
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
OUTPUT_REGISTRY = DOCS_DIR / "project_registry.yaml"
OUTPUT_FIGURES = DOCS_DIR / "figure_catalog.yaml"
OUTPUT_FINDINGS = DOCS_DIR / "findings_digest.md"
OUTPUT_GRAPH_COVERAGE = DOCS_DIR / "knowledge_graph_coverage.md"


def _load_build_registry_module():
    module_path = REPO_ROOT / "scripts" / "build_registry.py"
    spec = importlib.util.spec_from_file_location("build_registry", module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Failed to load module spec from {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _normalize_registry_payload(data: dict) -> dict:
    payload = copy.deepcopy(data)
    payload.pop("generated_at", None)
    return payload


def _normalize_figure_payload(data: dict) -> dict:
    payload = copy.deepcopy(data)
    payload.pop("generated_at", None)
    return payload


def _normalize_findings_digest(text: str) -> str:
    lines = text.splitlines()
    if len(lines) >= 2 and lines[1].startswith("**Last updated**:"):
        # Keep project/finding counts but ignore date.
        suffix = lines[1].split("|", 1)[1].strip() if "|" in lines[1] else ""
        lines[1] = f"**Last updated**: <normalized>{' | ' + suffix if suffix else ''}"
    return "\n".join(lines).strip()


def _normalize_graph_coverage(text: str) -> str:
    lines = text.splitlines()
    if len(lines) >= 2 and lines[1].startswith("**Last updated**:"):
        suffix = lines[1].split("|", 1)[1].strip() if "|" in lines[1] else ""
        lines[1] = f"**Last updated**: <normalized>{' | ' + suffix if suffix else ''}"
    return "\n".join(lines).strip()


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    missing = [
        p
        for p in (
            OUTPUT_REGISTRY,
            OUTPUT_FIGURES,
            OUTPUT_FINDINGS,
            OUTPUT_GRAPH_COVERAGE,
        )
        if not p.exists()
    ]
    if missing:
        print("FAIL: missing registry artifacts:")
        for p in missing:
            print(f"  - {p.relative_to(REPO_ROOT)}")
        print("\nRun: uv run scripts/build_registry.py")
        return 1

    build_registry = _load_build_registry_module()

    all_project_dirs = sorted(
        d
        for d in build_registry.PROJECTS_DIR.iterdir()
        if d.is_dir()
        and d.name not in build_registry.SKIP_PROJECTS
        and (d / "README.md").exists()
    )

    all_projects = []
    for project_dir in all_project_dirs:
        entry = build_registry.parse_project(project_dir)
        if entry:
            all_projects.append(entry)
    build_registry.compute_enables(all_projects)

    provenance_cache: dict[str, dict | None] = {}
    report_cache: dict[str, str | None] = {}
    for project_dir in all_project_dirs:
        pid = project_dir.name
        prov_path = project_dir / "provenance.yaml"
        report_path = project_dir / "REPORT.md"
        try:
            provenance_cache[pid] = (
                yaml.safe_load(prov_path.read_text(encoding="utf-8"))
                if prov_path.exists()
                else None
            )
        except (yaml.YAMLError, OSError):
            provenance_cache[pid] = None
        report_cache[pid] = (
            report_path.read_text(encoding="utf-8") if report_path.exists() else None
        )

    expected_registry = build_registry.generate_registry(all_projects)
    expected_figure_catalog = build_registry.generate_figure_catalog(
        all_project_dirs, provenance_cache, report_cache
    )
    expected_findings = build_registry.generate_findings_digest(
        all_project_dirs, all_projects, provenance_cache, report_cache
    )
    expected_graph_coverage = build_registry.generate_knowledge_graph_coverage(all_projects)

    actual_registry = _load_yaml(OUTPUT_REGISTRY)
    actual_figure_catalog = _load_yaml(OUTPUT_FIGURES)
    actual_findings = OUTPUT_FINDINGS.read_text(encoding="utf-8")
    actual_graph_coverage = OUTPUT_GRAPH_COVERAGE.read_text(encoding="utf-8")

    issues: list[str] = []

    if _normalize_registry_payload(actual_registry) != _normalize_registry_payload(expected_registry):
        act_ids = {p["id"] for p in actual_registry.get("projects", [])}
        exp_ids = {p["id"] for p in expected_registry.get("projects", [])}
        missing_ids = sorted(exp_ids - act_ids)
        extra_ids = sorted(act_ids - exp_ids)
        issues.append(
            "project_registry.yaml is stale "
            f"(actual projects={len(act_ids)}, expected={len(exp_ids)}, "
            f"missing={len(missing_ids)}, extra={len(extra_ids)})"
        )
        if missing_ids:
            issues.append(f"  missing project IDs: {', '.join(missing_ids[:10])}")
        if extra_ids:
            issues.append(f"  extra project IDs: {', '.join(extra_ids[:10])}")

    if _normalize_figure_payload(actual_figure_catalog) != _normalize_figure_payload(expected_figure_catalog):
        issues.append(
            "figure_catalog.yaml is stale "
            f"(actual figure_count={actual_figure_catalog.get('figure_count')}, "
            f"expected={expected_figure_catalog.get('figure_count')})"
        )

    norm_actual_findings = _normalize_findings_digest(actual_findings)
    norm_expected_findings = _normalize_findings_digest(expected_findings)
    if norm_actual_findings != norm_expected_findings:
        issues.append("findings_digest.md is stale")
        diff = difflib.unified_diff(
            norm_actual_findings.splitlines(),
            norm_expected_findings.splitlines(),
            fromfile="actual/findings_digest.md",
            tofile="expected/findings_digest.md",
            n=3,
        )
        preview = list(diff)[:40]
        if preview:
            issues.append("  diff preview:")
            issues.extend(f"    {line}" for line in preview)

    norm_actual_graph = _normalize_graph_coverage(actual_graph_coverage)
    norm_expected_graph = _normalize_graph_coverage(expected_graph_coverage)
    if norm_actual_graph != norm_expected_graph:
        issues.append("knowledge_graph_coverage.md is stale")

    if issues:
        print("FAIL: knowledge registry artifacts are out of date.\n")
        for item in issues:
            print(item)
        print("\nRun: uv run scripts/build_registry.py")
        return 1

    print("PASS: knowledge registry artifacts are fresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

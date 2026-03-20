"""Capture Phase 0 baseline snapshots for the OpenViking migration."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml

from observatory_context.baseline import capture_baseline_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "migration_baseline" / "2026-03-19"
VALIDATORS = {
    "validate_provenance": ["uv", "run", "scripts/validate_provenance.py"],
    "validate_knowledge_graph": ["uv", "run", "scripts/validate_knowledge_graph.py"],
    "validate_registry_freshness": ["uv", "run", "scripts/validate_registry_freshness.py"],
}
QUERY_COMMANDS = {
    "metal stress": ["uv", "run", "scripts/query_knowledge_unified.py", "search", "metal stress"],
    "essential genes": ["uv", "run", "scripts/query_knowledge_unified.py", "search", "essential genes"],
    "org_adp1": ["uv", "run", "scripts/query_knowledge_unified.py", "search", "org_adp1"],
    "landscape": ["uv", "run", "scripts/query_knowledge_unified.py", "landscape"],
    "gaps": ["uv", "run", "scripts/query_knowledge_unified.py", "gaps"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture baseline fixtures for the OpenViking migration.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for baseline snapshot files.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    validator_results = {name: _run(command).returncode == 0 for name, command in VALIDATORS.items()}
    query_outputs = {name: _run(command).stdout.strip() for name, command in QUERY_COMMANDS.items()}

    snapshot = capture_baseline_snapshot(REPO_ROOT, query_outputs, validator_results)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "baseline_snapshot.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (args.output_dir / "baseline_snapshot.yaml").write_text(
        yaml.safe_dump(snapshot, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Wrote baseline snapshot to {args.output_dir}")
    return 0


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())


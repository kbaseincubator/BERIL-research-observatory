from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "knowledge" / "scripts" / "ingest_context.py"


def test_empty_project_is_rejected_not_silent_success():
    """`--project ""` must be rejected, not reported as a successful no-op.

    The validator runs before any server contact, so this needs no server.
    """
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--project", ""],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "Ingest finished" not in combined
    assert "Project ID must be a simple directory name" in proc.stderr
    assert "Traceback" not in proc.stderr

"""Tests for BERDL local environment setup conventions."""

from __future__ import annotations

import tomllib
from pathlib import Path

from scripts import detect_berdl_environment


def test_detect_environment_uses_repo_venv(monkeypatch, tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".env").write_text('KBASE_AUTH_TOKEN="token"\n', encoding="utf-8")

    monkeypatch.setattr(detect_berdl_environment, "__file__", str(scripts_dir / "detect_berdl_environment.py"))
    monkeypatch.setattr(detect_berdl_environment, "test_connectivity", lambda *args, **kwargs: False)
    monkeypatch.setattr(detect_berdl_environment, "check_port_listening", lambda port: True)

    result = detect_berdl_environment.detect_environment()

    assert result["checks"]["venv"] is True
    assert result["ready"] is True


def test_pyproject_defines_berdl_and_ingest_extras() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    optional = payload["project"]["optional-dependencies"]

    assert "berdl" in optional
    assert "ingest" in optional

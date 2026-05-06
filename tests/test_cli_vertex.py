"""Tests for Vertex integration in beril CLI (config, setup, start)."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from beril_cli import config


@pytest.fixture()
def tmp_config(tmp_path, monkeypatch):
    """Point config at a temporary directory."""
    cfg_dir = tmp_path / ".config" / "beril"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_PATH", cfg_dir / "config.toml")
    return cfg_dir / "config.toml"


# ── config.py ──────────────────────────────────────────


def test_save_and_load_vertex_config(tmp_config):
    """Round-trip: save vertex config then load it back."""
    cfg = {
        "defaults": {"agent": "claude"},
        "vertex": {
            "enabled": True,
            "project_id": "my-project",
            "region": "global",
            "credentials_file": "/tmp/creds.json",
        },
    }
    config.save(cfg)
    loaded = config.load()
    assert loaded["vertex"]["enabled"] is True
    assert loaded["vertex"]["project_id"] == "my-project"
    assert loaded["vertex"]["region"] == "global"
    assert loaded["vertex"]["credentials_file"] == "/tmp/creds.json"


def test_save_without_vertex(tmp_config):
    """Config without vertex section doesn't create one."""
    cfg = {"defaults": {"agent": "claude"}}
    config.save(cfg)
    loaded = config.load()
    assert "vertex" not in loaded


def test_get_vertex_config_empty(tmp_config):
    """get_vertex_config returns empty dict when not configured."""
    config.save({"defaults": {"agent": "claude"}})
    assert config.get_vertex_config() == {}


def test_get_vertex_config_returns_section(tmp_config):
    """get_vertex_config returns the vertex section."""
    cfg = {
        "defaults": {"agent": "claude"},
        "vertex": {
            "enabled": True,
            "project_id": "test-proj",
            "region": "global",
            "credentials_file": "/tmp/c.json",
        },
    }
    config.save(cfg)
    v = config.get_vertex_config()
    assert v["enabled"] is True
    assert v["project_id"] == "test-proj"


def test_vertex_disabled_saved_correctly(tmp_config):
    """enabled=false is persisted and loaded correctly."""
    cfg = {
        "defaults": {"agent": "claude"},
        "vertex": {"enabled": False},
    }
    config.save(cfg)
    loaded = config.load()
    assert loaded["vertex"]["enabled"] is False


# ── start.py env injection ─────────────────────────────


def test_start_injects_vertex_env(tmp_path, tmp_config, monkeypatch):
    """run_start sets Vertex env vars when enabled and creds exist."""
    from beril_cli import start

    # Create fake credentials file
    creds_file = tmp_path / "creds.json"
    creds_file.write_text("{}")

    # Save config with vertex enabled
    config.save({
        "defaults": {"agent": "claude"},
        "vertex": {
            "enabled": True,
            "project_id": "test-proj",
            "region": "global",
            "credentials_file": str(creds_file),
        },
    })

    # Create fake repo root with PROJECT.md
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "PROJECT.md").write_text("marker")
    (repo / ".env").write_text("KBASE_AUTH_TOKEN=fake\n")
    monkeypatch.chdir(repo)

    # Capture the execvp call instead of actually exec-ing
    captured = {}

    def fake_execvp(binary, args):
        captured["binary"] = binary
        captured["args"] = args
        captured["env"] = {
            k: os.environ[k]
            for k in (
                "CLAUDE_CODE_USE_VERTEX",
                "CLOUD_ML_REGION",
                "ANTHROPIC_VERTEX_PROJECT_ID",
                "GOOGLE_APPLICATION_CREDENTIALS",
            )
            if k in os.environ
        }

    monkeypatch.setattr(os, "execvp", fake_execvp)
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")

    start.run_start(agent="claude", extra_args=["/berdl_start"])

    assert captured["env"]["CLAUDE_CODE_USE_VERTEX"] == "1"
    assert captured["env"]["CLOUD_ML_REGION"] == "global"
    assert captured["env"]["ANTHROPIC_VERTEX_PROJECT_ID"] == "test-proj"
    assert captured["env"]["GOOGLE_APPLICATION_CREDENTIALS"] == str(creds_file)


def test_start_skips_vertex_when_disabled(tmp_path, tmp_config, monkeypatch):
    """run_start does NOT set Vertex env vars when vertex is not configured."""
    from beril_cli import start

    config.save({"defaults": {"agent": "claude"}})

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "PROJECT.md").write_text("marker")
    (repo / ".env").write_text("KBASE_AUTH_TOKEN=fake\n")
    monkeypatch.chdir(repo)

    # Clean env
    for key in ("CLAUDE_CODE_USE_VERTEX", "ANTHROPIC_VERTEX_PROJECT_ID"):
        monkeypatch.delenv(key, raising=False)

    captured = {}

    def fake_execvp(binary, args):
        captured["env_vertex"] = os.environ.get("CLAUDE_CODE_USE_VERTEX")

    monkeypatch.setattr(os, "execvp", fake_execvp)
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")

    start.run_start(agent="claude", extra_args=["/berdl_start"])

    assert captured["env_vertex"] is None


def test_start_warns_missing_creds(tmp_path, tmp_config, monkeypatch, capsys):
    """run_start warns when vertex enabled but creds file is missing."""
    from beril_cli import start

    config.save({
        "defaults": {"agent": "claude"},
        "vertex": {
            "enabled": True,
            "project_id": "test-proj",
            "region": "global",
            "credentials_file": "/nonexistent/creds.json",
        },
    })

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "PROJECT.md").write_text("marker")
    (repo / ".env").write_text("KBASE_AUTH_TOKEN=fake\n")
    monkeypatch.chdir(repo)

    captured = {}

    def fake_execvp(binary, args):
        captured["called"] = True

    monkeypatch.setattr(os, "execvp", fake_execvp)
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.delenv("CLAUDE_CODE_USE_VERTEX", raising=False)

    start.run_start(agent="claude", extra_args=["/berdl_start"])

    stderr = capsys.readouterr().err
    assert "credentials file not found" in stderr
    assert os.environ.get("CLAUDE_CODE_USE_VERTEX") is None

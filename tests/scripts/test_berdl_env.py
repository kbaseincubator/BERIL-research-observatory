"""Tests for scripts/berdl_env.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "berdl_env.py"


def test_script_exists():
    assert SCRIPT.exists(), "scripts/berdl_env.py must exist"


def test_check_returns_zero_when_on_cluster_ready(monkeypatch):
    """When detection reports on-cluster ready, --check exits 0."""
    fake_result = {
        "location": "on-cluster",
        "ready": True,
        "checks": {"spark_direct": True, "kbase_token_env": True},
        "next_steps": ["✅ On BERDL cluster"],
    }
    with patch("scripts.berdl_env.detect_environment", return_value=fake_result):
        from scripts.berdl_env import check_cli
        rc = check_cli()
        assert rc == 0


def test_check_returns_zero_when_off_cluster_ready(monkeypatch):
    """When detection reports off-cluster fully ready, --check exits 0."""
    fake_result = {
        "location": "off-cluster",
        "ready": True,
        "checks": {
            "spark_direct": False,
            "kbase_token_env_file": True,
            "venv_berdl": True,
            "ssh_tunnel_1337": True,
            "ssh_tunnel_1338": True,
            "pproxy_8123": True,
        },
        "next_steps": ["✅ Off-cluster fully configured"],
    }
    with patch("scripts.berdl_env.detect_environment", return_value=fake_result):
        from scripts.berdl_env import check_cli
        rc = check_cli()
        assert rc == 0


def test_check_starts_pproxy_when_only_pproxy_missing(monkeypatch):
    """If tunnels are up but pproxy is down, helper starts pproxy and re-checks."""
    not_ready = {
        "location": "off-cluster",
        "ready": False,
        "checks": {
            "kbase_token_env_file": True,
            "venv_berdl": True,
            "ssh_tunnel_1337": True,
            "ssh_tunnel_1338": True,
            "pproxy_8123": False,
        },
        "next_steps": ["❌ pproxy not running on port 8123."],
    }
    ready_after = dict(not_ready, ready=True, checks=dict(not_ready["checks"], pproxy_8123=True))
    with patch("scripts.berdl_env.detect_environment", side_effect=[not_ready, ready_after]) as detect, \
         patch("scripts.berdl_env.start_pproxy", return_value=True) as starter:
        from scripts.berdl_env import check_cli
        rc = check_cli()
        assert rc == 0
        starter.assert_called_once()
        assert detect.call_count == 2


def test_check_returns_nonzero_when_tunnels_missing(monkeypatch, capsys):
    """If SSH tunnels are missing, --check exits 1 and prints SSH commands."""
    fake_result = {
        "location": "off-cluster",
        "ready": False,
        "checks": {
            "kbase_token_env_file": True,
            "venv_berdl": True,
            "ssh_tunnel_1337": False,
            "ssh_tunnel_1338": False,
            "pproxy_8123": False,
        },
        "next_steps": ["❌ SSH tunnel(s) on port(s) 1337, 1338 not running."],
    }
    with patch("scripts.berdl_env.detect_environment", return_value=fake_result):
        from scripts.berdl_env import check_cli
        rc = check_cli()
        assert rc == 1
        captured = capsys.readouterr()
        assert "SSH tunnel" in captured.out or "SSH tunnel" in captured.err


def test_json_mode_emits_parseable_json(monkeypatch, capsys):
    fake_result = {
        "location": "on-cluster",
        "ready": True,
        "checks": {"spark_direct": True},
        "next_steps": [],
    }
    with patch("scripts.berdl_env.detect_environment", return_value=fake_result):
        from scripts.berdl_env import json_cli
        rc = json_cli()
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["location"] == "on-cluster"
        assert parsed["ready"] is True


def test_require_environment_raises_when_not_ready(monkeypatch):
    """Python API raises BerdlEnvironmentError when detection says not ready."""
    fake_result = {
        "location": "off-cluster",
        "ready": False,
        "checks": {},
        "next_steps": ["❌ Something missing"],
    }
    with patch("scripts.berdl_env.detect_environment", return_value=fake_result), \
         patch("scripts.berdl_env.start_pproxy", return_value=False):
        from scripts.berdl_env import require_environment, BerdlEnvironmentError
        with pytest.raises(BerdlEnvironmentError) as excinfo:
            require_environment()
        assert "Something missing" in str(excinfo.value) or excinfo.value.next_steps


def test_require_environment_returns_env_when_ready(monkeypatch):
    fake_result = {
        "location": "on-cluster",
        "ready": True,
        "checks": {"spark_direct": True},
        "next_steps": [],
    }
    with patch("scripts.berdl_env.detect_environment", return_value=fake_result):
        from scripts.berdl_env import require_environment
        env = require_environment()
        assert env.location == "on-cluster"
        assert env.checks["spark_direct"] is True

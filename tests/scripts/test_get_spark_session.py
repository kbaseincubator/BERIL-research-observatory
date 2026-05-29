"""Tests for scripts/get_spark_session.py auto-spawn behavior."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch


def test_ensure_hub_is_public():
    """ensure_hub must be importable as a public name."""
    from scripts.get_spark_session import ensure_hub
    assert callable(ensure_hub)


def test_ensure_hub_alias_preserved():
    """The original _ensure_hub name should still resolve to the same function."""
    from scripts.get_spark_session import ensure_hub, _ensure_hub
    assert ensure_hub is _ensure_hub


def test_ensure_hub_skipped_when_env_var_set(monkeypatch):
    """BERDL_NO_AUTO_SPAWN=1 short-circuits ensure_hub before any subprocess call."""
    from scripts import get_spark_session

    monkeypatch.setenv("BERDL_NO_AUTO_SPAWN", "1")
    with patch("scripts.get_spark_session.subprocess.run") as run:
        get_spark_session.ensure_hub()
        run.assert_not_called()


def test_ensure_hub_runs_when_env_var_unset(monkeypatch):
    """Without the env var, ensure_hub at least invokes berdl-remote status."""
    from scripts import get_spark_session

    monkeypatch.delenv("BERDL_NO_AUTO_SPAWN", raising=False)
    fake_status = MagicMock(returncode=0, stdout="Kernel available\n", stderr="")
    with patch("scripts.get_spark_session.subprocess.run", return_value=fake_status) as run, \
         patch("scripts.get_spark_session.Path") as path_cls:
        # Pretend the berdl-remote config exists so we skip the login branch.
        path_cls.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
        get_spark_session.ensure_hub()
        assert run.called

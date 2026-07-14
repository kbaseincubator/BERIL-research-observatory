from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "knowledge" / "scripts" / "setup_remote_ov.py"


def _load():
    spec = importlib.util.spec_from_file_location("setup_remote_ov", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = _load()


def test_render_env_replaces_in_place_and_preserves_others():
    existing = "KBASE_AUTH_TOKEN=abc\n# note\nOPENVIKING_URL=http://old\nX=1\n"
    out = setup.render_env(
        existing, {"OPENVIKING_URL": "https://new/ov", "OPENVIKING_API_KEY": "K"}
    )
    assert "KBASE_AUTH_TOKEN=abc" in out
    assert "# note" in out
    assert "X=1" in out
    assert out.count("OPENVIKING_URL=") == 1
    assert "OPENVIKING_URL=https://new/ov" in out
    assert "OPENVIKING_API_KEY=K" in out


def test_render_env_empty_file_appends_both():
    out = setup.render_env("", {"OPENVIKING_URL": "https://new/ov", "OPENVIKING_API_KEY": "K"})
    assert out == "OPENVIKING_URL=https://new/ov\nOPENVIKING_API_KEY=K\n"


def test_resolve_cookie_strips_prefix(monkeypatch):
    monkeypatch.delenv("BERIL_SESSION", raising=False)
    assert setup._resolve_cookie("beril_session=eyJabc") == "eyJabc"
    assert setup._resolve_cookie("  raw-value  ") == "raw-value"


def test_resolve_cookie_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("BERIL_SESSION", "from-env")
    assert setup._resolve_cookie(None) == "from-env"


def test_resolve_cookie_missing_raises(monkeypatch):
    monkeypatch.delenv("BERIL_SESSION", raising=False)
    monkeypatch.setattr(setup.sys.stdin, "isatty", lambda: False)
    with pytest.raises(SystemExit):
        setup._resolve_cookie(None)


def test_guard_401_is_clear(monkeypatch):
    class _Resp:
        status_code = 401
        is_success = False

    with pytest.raises(SystemExit) as excinfo:
        setup._guard(_Resp(), action="fetch credentials")
    assert "401" in str(excinfo.value)

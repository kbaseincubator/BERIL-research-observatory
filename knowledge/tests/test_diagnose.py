from __future__ import annotations

from pathlib import Path

from observatory_context import openviking_client as oc
from observatory_context.config import ContextConfig


def _cfg(url: str = "https://x/ov", key: str | None = None) -> ContextConfig:
    return ContextConfig(repo_root=Path("."), openviking_url=url, openviking_api_key=key)


# --- verdict mapping (tiers stubbed) ---------------------------------------


def test_diagnose_unreachable(monkeypatch):
    monkeypatch.setattr(oc, "_http_health", lambda url, timeout: None)
    diag = oc.diagnose(_cfg())
    assert diag.verdict == "unreachable"
    assert not diag.reachable and not diag.ok
    assert diag.remedy


def test_diagnose_unhealthy(monkeypatch):
    monkeypatch.setattr(oc, "_http_health", lambda url, timeout: {"healthy": False})
    diag = oc.diagnose(_cfg())
    assert diag.verdict == "unhealthy"
    assert diag.reachable


def test_diagnose_no_key(monkeypatch):
    monkeypatch.setattr(
        oc, "_http_health", lambda url, timeout: {"healthy": True, "auth_mode": "api_key"}
    )
    diag = oc.diagnose(_cfg(key=None))
    assert diag.verdict == "no_key"
    assert "setup_remote_ov" in diag.remedy


def test_diagnose_ok_when_no_auth_required(monkeypatch):
    monkeypatch.setattr(
        oc, "_http_health", lambda url, timeout: {"healthy": True, "auth_mode": "none"}
    )
    diag = oc.diagnose(_cfg(key=None))
    assert diag.verdict == "ok" and diag.ok


def test_diagnose_ok_when_key_valid(monkeypatch):
    monkeypatch.setattr(
        oc, "_http_health", lambda url, timeout: {"healthy": True, "auth_mode": "api_key"}
    )
    monkeypatch.setattr(oc, "_probe_auth", lambda config, timeout: ("ok", ""))
    diag = oc.diagnose(_cfg(key="k"))
    assert diag.verdict == "ok"


def test_diagnose_auth_failed(monkeypatch):
    monkeypatch.setattr(
        oc, "_http_health", lambda url, timeout: {"healthy": True, "auth_mode": "api_key"}
    )
    monkeypatch.setattr(oc, "_probe_auth", lambda config, timeout: ("auth_failed", "401"))
    diag = oc.diagnose(_cfg(key="bad"))
    assert diag.verdict == "auth_failed"
    assert "--regenerate" in diag.remedy


def test_diagnose_probe_error(monkeypatch):
    monkeypatch.setattr(
        oc, "_http_health", lambda url, timeout: {"healthy": True, "auth_mode": "api_key"}
    )
    monkeypatch.setattr(oc, "_probe_auth", lambda config, timeout: ("error", "boom"))
    diag = oc.diagnose(_cfg(key="k"))
    assert diag.verdict == "error"


# --- helpers ----------------------------------------------------------------


def test_http_health_parses_json_body(monkeypatch):
    class _Resp:
        status_code = 200

        def json(self):
            return {"healthy": True, "version": "0.3.24"}

    monkeypatch.setattr(oc.httpx, "get", lambda url, timeout: _Resp())
    body = oc._http_health("https://x/ov", 1.0)
    assert body["version"] == "0.3.24"


def test_http_health_non_200_is_none(monkeypatch):
    class _Resp:
        status_code = 503

        def json(self):
            return {}

    monkeypatch.setattr(oc.httpx, "get", lambda url, timeout: _Resp())
    assert oc._http_health("https://x/ov", 1.0) is None


def test_http_health_transport_error_is_none(monkeypatch):
    def _boom(url, timeout):
        raise oc.httpx.ConnectError("nope")

    monkeypatch.setattr(oc.httpx, "get", _boom)
    assert oc._http_health("https://x/ov", 1.0) is None


def test_is_auth_error_by_class_name_and_message():
    class UnauthenticatedError(Exception):
        pass

    assert oc._is_auth_error(UnauthenticatedError("no"))
    assert oc._is_auth_error(RuntimeError("HTTP 401 unauthorized"))
    assert not oc._is_auth_error(RuntimeError("deadline exceeded"))


def test_requires_key_by_auth_mode():
    assert oc._requires_key({"auth_mode": "api_key"})
    assert not oc._requires_key({"auth_mode": "none"})
    assert not oc._requires_key({})


def test_format_diagnosis_shows_remedy_and_server_meta():
    diag = oc.Diagnosis(
        "no_key",
        "https://x/ov",
        True,
        detail="needs a key",
        remedy="do X",
        server={"version": "0.3.24", "auth_mode": "api_key"},
    )
    text = oc.format_diagnosis(diag)
    assert "NO API KEY" in text
    assert "do X" in text
    assert "version 0.3.24" in text

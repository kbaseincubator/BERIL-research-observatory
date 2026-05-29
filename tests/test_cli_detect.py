"""Tests for `beril_cli.detect` — auto-detection of user identity."""

from __future__ import annotations

import pytest

from beril_cli import detect


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Strip detection-relevant env vars unless a test sets them explicitly."""
    for var in ("ORCID", "KBASE_AUTH_TOKEN", "KBASE_AUTH_URL"):
        monkeypatch.delenv(var, raising=False)


def _stub_http(monkeypatch, responses: dict[str, dict | None]):
    """Replace `_http_get_json` with a dict-driven stub. Unmatched URLs return None."""
    def fake_get(url: str, headers=None):
        return responses.get(url)
    monkeypatch.setattr(detect, "_http_get_json", fake_get)


# ── ORCID extraction ──────────────────────────────────────


def test_normalize_orcid_bare_id():
    assert detect._normalize_orcid("0000-0001-2345-6789") == "0000-0001-2345-6789"


def test_normalize_orcid_url_form():
    assert detect._normalize_orcid("https://orcid.org/0000-0001-2345-6789") == "0000-0001-2345-6789"


def test_normalize_orcid_x_checksum():
    assert detect._normalize_orcid("0000-0002-1825-009X") == "0000-0002-1825-009X"


def test_normalize_orcid_garbage_returns_empty():
    assert detect._normalize_orcid("not an orcid") == ""


def test_normalize_orcid_empty():
    assert detect._normalize_orcid("") == ""


# ── detect_orcid: env var path ───────────────────────────


def test_detect_orcid_from_env(monkeypatch):
    monkeypatch.setenv("ORCID", "0000-0001-2345-6789")
    assert detect.detect_orcid() == "0000-0001-2345-6789"


def test_detect_orcid_env_url_form(monkeypatch):
    monkeypatch.setenv("ORCID", "https://orcid.org/0000-0001-2345-6789")
    assert detect.detect_orcid() == "0000-0001-2345-6789"


# ── detect_orcid: KBase fallback ─────────────────────────


def test_detect_orcid_falls_back_to_kbase(monkeypatch):
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setenv("KBASE_AUTH_URL", "https://example.test/auth/")
    _stub_http(monkeypatch, {
        "https://example.test/auth/api/V2/me": {
            "display": "Alice",
            "idents": [
                {"provider": "Google", "provusername": "alice@example.com"},
                {"provider": "OrcID", "provusername": "0000-0001-2345-6789"},
            ],
        },
    })
    assert detect.detect_orcid() == "0000-0001-2345-6789"


def test_detect_orcid_no_orcid_anywhere(monkeypatch):
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setenv("KBASE_AUTH_URL", "https://example.test/auth")
    _stub_http(monkeypatch, {
        "https://example.test/auth/api/V2/me": {
            "display": "Alice",
            "idents": [{"provider": "Google", "provusername": "alice@example.com"}],
        },
    })
    assert detect.detect_orcid() == ""


def test_detect_orcid_no_env_no_token(monkeypatch):
    assert detect.detect_orcid() == ""


# ── detect_name_from_orcid ───────────────────────────────


def test_detect_name_prefers_credit_name(monkeypatch):
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/person": {
            "name": {
                "given-names": {"value": "Alice"},
                "family-name": {"value": "Smith"},
                "credit-name": {"value": "Alice M. Smith"},
            },
        },
    })
    assert detect.detect_name_from_orcid("0000-0001-2345-6789") == "Alice M. Smith"


def test_detect_name_falls_back_to_given_family(monkeypatch):
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/person": {
            "name": {
                "given-names": {"value": "Alice"},
                "family-name": {"value": "Smith"},
                "credit-name": None,
            },
        },
    })
    assert detect.detect_name_from_orcid("0000-0001-2345-6789") == "Alice Smith"


def test_detect_name_private_record_returns_empty(monkeypatch):
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/person": {"name": None},
    })
    assert detect.detect_name_from_orcid("0000-0001-2345-6789") == ""


def test_detect_name_empty_orcid():
    assert detect.detect_name_from_orcid("") == ""


# ── detect_affiliation_from_orcid ────────────────────────


def _emp(org_name: str, end_date=None, display_index="0") -> dict:
    return {
        "summaries": [{
            "employment-summary": {
                "organization": {"name": org_name},
                "end-date": end_date,
                "display-index": display_index,
            },
        }],
    }


def test_detect_affiliation_single_active(monkeypatch):
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/employments": {
            "affiliation-group": [_emp("Acme Lab")],
        },
    })
    assert detect.detect_affiliation_from_orcid("0000-0001-2345-6789") == "Acme Lab"


def test_detect_affiliation_skips_ended(monkeypatch):
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/employments": {
            "affiliation-group": [
                _emp("Old Place", end_date={"year": {"value": "2020"}}),
                _emp("Current Lab"),
            ],
        },
    })
    assert detect.detect_affiliation_from_orcid("0000-0001-2345-6789") == "Current Lab"


def test_detect_affiliation_picks_highest_display_index(monkeypatch):
    """ORCID renders highest display-index at the top — that's the preferred entry."""
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/employments": {
            "affiliation-group": [
                _emp("Secondary Lab", display_index="0"),
                _emp("Preferred Lab", display_index="2"),
            ],
        },
    })
    assert detect.detect_affiliation_from_orcid("0000-0001-2345-6789") == "Preferred Lab"


def test_detect_affiliation_no_active_employments(monkeypatch):
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/employments": {
            "affiliation-group": [_emp("Old", end_date={"year": {"value": "2018"}})],
        },
    })
    assert detect.detect_affiliation_from_orcid("0000-0001-2345-6789") == ""


def test_detect_affiliation_http_failure(monkeypatch):
    _stub_http(monkeypatch, {})  # all requests miss → None
    assert detect.detect_affiliation_from_orcid("0000-0001-2345-6789") == ""


def test_detect_affiliation_empty_orcid():
    assert detect.detect_affiliation_from_orcid("") == ""


# ── detect_user_identity (composite) ─────────────────────


def test_detect_user_identity_full(monkeypatch):
    monkeypatch.setenv("ORCID", "0000-0001-2345-6789")
    _stub_http(monkeypatch, {
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/person": {
            "name": {"credit-name": {"value": "Alice M. Smith"}},
        },
        "https://pub.orcid.org/v3.0/0000-0001-2345-6789/employments": {
            "affiliation-group": [_emp("Acme Lab")],
        },
    })
    assert detect.detect_user_identity() == {
        "name": "Alice M. Smith",
        "affiliation": "Acme Lab",
        "orcid": "0000-0001-2345-6789",
    }


def test_detect_user_identity_orcid_only(monkeypatch):
    """ORCID present but record entirely private."""
    monkeypatch.setenv("ORCID", "0000-0001-2345-6789")
    _stub_http(monkeypatch, {})  # no responses → all fail
    out = detect.detect_user_identity()
    assert out["orcid"] == "0000-0001-2345-6789"
    assert out["name"] == ""
    assert out["affiliation"] == ""


def test_detect_user_identity_kbase_name_fallback(monkeypatch):
    """No ORCID env, no ORCID linked, but KBase has a display name."""
    monkeypatch.setenv("KBASE_AUTH_TOKEN", "tok")
    monkeypatch.setenv("KBASE_AUTH_URL", "https://example.test/auth")
    _stub_http(monkeypatch, {
        "https://example.test/auth/api/V2/me": {
            "display": "Alice Smith",
            "idents": [{"provider": "Google", "provusername": "alice@example.com"}],
        },
    })
    out = detect.detect_user_identity()
    assert out == {"name": "Alice Smith", "affiliation": "", "orcid": ""}


def test_detect_user_identity_nothing_available():
    assert detect.detect_user_identity() == {"name": "", "affiliation": "", "orcid": ""}

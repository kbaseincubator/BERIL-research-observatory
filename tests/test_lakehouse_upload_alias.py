"""The mc-alias precondition check in tools/lakehouse_upload.py.

The failure branch is the only thing a blocked user sees, and it used to name
three different variable schemes in one line (MINIO_*, then AWS_*), none of which
a current BERDL pod sets. See #366.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `import tools.lakehouse_upload` from the repo-root tests/ directory.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import lakehouse_upload  # noqa: E402


def test_a_configured_alias_passes(monkeypatch):
    monkeypatch.setattr(lakehouse_upload, "_mc", lambda *a, **k: (0, "berdl-minio", ""))

    assert lakehouse_upload._check_mc_alias() is True


def test_a_missing_alias_fails_and_names_the_s3_variables(monkeypatch, capsys):
    monkeypatch.setattr(lakehouse_upload, "MC_ALIAS", "test-alias")
    monkeypatch.setattr(
        lakehouse_upload, "_mc", lambda *a, **k: (1, "", "alias not found")
    )

    assert lakehouse_upload._check_mc_alias() is False

    err = capsys.readouterr().err
    assert "not configured" in err
    # The remedy has to be runnable. configure_mc.sh resolves the credentials,
    # and the manual form must name the variables a pod actually sets.
    assert "scripts/configure_mc.sh" in err
    assert "mc alias set test-alias" in err
    for name in ("S3_ENDPOINT_URL", "S3_ACCESS_KEY", "S3_SECRET_KEY"):
        assert name in err
    # The schemes it used to name, neither of which exists on a current pod.
    assert "MINIO_ENDPOINT_URL" not in err
    assert "AWS_ACCESS_KEY_ID" not in err

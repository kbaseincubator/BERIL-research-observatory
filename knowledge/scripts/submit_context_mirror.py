#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openviking",
#     "httpx",
#     "pyyaml",
#     "rich",
# ]
# ///
"""Best-effort mirror of a just-archived project into the BERIL context service.

`tools/lakehouse_upload.py` calls this **after** a successful lakehouse upload so
the knowledge layer sees the completed project. It is deliberately a separate
`uv run --script` process rather than an in-process import: the upload tool runs
under whatever interpreter the caller has active (which may lack `openviking`),
whereas this script's PEP-723 header pins its own environment. That keeps all the
knowledge-layer machinery in the `knowledge` module and out of the upload tool.

Three gates must pass before the mirror runs — all required:

  1. the BERIL webapp is available,
  2. the user is logged in with a valid credential, and
  3. the context service is reachable and accepts that credential.

(1)+(2) are proved together by an authenticated health call against BERIL;
(3) by the context client's own reachability + auth diagnosis (against the
credential the importer will actually use). If any gate fails we skip — never
fail — because the lakehouse archive, not the context index, is the source of
truth for "submitted".

Output: a single line of JSON on stdout (always)::

    {"status": "ok"|"skipped"|"failed", "reason": "..."}

Exit code is always 0 — this is advisory. The caller reads `status`/`reason` and
surfaces a WARN on anything other than "ok"; it never treats a non-"ok" mirror
as a submission failure.

Usage:
    submit_context_mirror.py <project_id>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from beril_cli import auth_store
from beril_cli.ov_client import OvLinkError, ov_health
from observatory_context.config import ContextConfig
from observatory_context.ingest import ingest_project
from observatory_context.openviking_client import create_client, diagnose


def _emit(status: str, reason: str) -> int:
    """Print the single-line JSON verdict. Always exit 0 (advisory)."""
    print(json.dumps({"status": status, "reason": reason}))
    return 0


def _preflight() -> tuple[bool, str]:
    """Check the three gates. Return (ok, reason)."""
    # Gates 1+2: authenticated health call against BERIL. A 200 proves the
    # webapp is up and the stored token still authenticates.
    record = auth_store.load()
    if record is None:
        return False, (
            "not logged in to BERIL (no ~/.beril/auth.json); "
            "run `beril login` to enable the context-service submission"
        )
    try:
        ov_health(record.base_url, record.token)
    except OvLinkError as exc:
        return False, f"BERIL context service health check failed: {exc}"

    # Gate 3: reachability + client-auth against the context service the way the
    # importer will reach it (ContextConfig resolves the cached credential).
    diag = diagnose(ContextConfig.from_env())
    if not diag.ok:
        return False, f"context service not ready ({diag.verdict}): {diag.detail}"
    return True, "context service available"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id", help="Project directory name under projects/")
    args = parser.parse_args()

    try:
        ok, reason = _preflight()
    except Exception as exc:  # unexpected client/transport error
        return _emit("skipped", f"context-service preflight error: {exc}")
    if not ok:
        return _emit("skipped", reason)

    config = ContextConfig.from_env()
    try:
        client = create_client(config)
    except Exception as exc:
        # create_client raises SystemExit on an unreachable server; the
        # preflight should have caught that, but guard against the race.
        return _emit("skipped", f"context service became unreachable: {exc}")

    try:
        ingest_project(config, client, args.project_id)
    except Exception as exc:
        return _emit("failed", f"context-service submission failed: {exc}")
    finally:
        close = getattr(client, "close", None)
        if close:
            try:
                close()
            except Exception:
                pass

    return _emit("ok", f"submitted {args.project_id} to context service")


if __name__ == "__main__":
    raise SystemExit(main())

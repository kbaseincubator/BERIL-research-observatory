"""The durable query registry — an append-only per-project journal.

``projects/<id>/journal.jsonl`` holds one JSON object per line,
``{ts, session_id, kind, locator, payload}``. It exists so that a ``query:``
evidence pointer in ``REPORT.md`` can resolve against something *observed while
the analysis ran* rather than reconstructed at synthesis time. Without it, a
well-formed ``q:`` pointer could never resolve and so could never contribute to
``computed.resolved_artifact_support``.

Append-only JSONL with one ``O_APPEND`` write per record: appending needs no
read-modify-write, so two concurrent tool calls cannot corrupt the file. Same
discipline, for the same reason, as ``.claude/hooks/plan-gate.py::_record``.

Capture is **agent-invoked** (``beril capture-event``, called by the
``berdl-query`` and ``synthesize`` skills) and therefore best-effort — the same
reliability tier as ``WORKLOG.md``, not the passive tier of ``runtime.json``.
BERDL queries run inside notebook cells against a Spark session, so they are
never a distinct tool call that a ``PostToolUse`` hook could observe. See
``docs/provenance-and-trust.md``.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

JOURNAL_FILE = "journal.jsonl"

#: The ``q:<id>`` locator grammar, shared by the writer here and by
#: ``claims_cmd.resolve_evidence_pointer``. Deliberately one definition: a
#: second copy is how a locator becomes writable but unresolvable.
QUERY_LOCATOR = re.compile(r"q:[A-Za-z0-9][A-Za-z0-9._-]*$")


def append_event(
    project_dir: Path,
    kind: str,
    locator: str,
    payload: str = "",
    session_id: str | None = None,
) -> None:
    """Append one event to the project's journal.

    Parameters
    ----------
    project_dir
        Path to the project directory (the journal lives directly inside it).
    kind
        Event kind; ``query`` is the only kind with a consumer today.
    locator
        The evidence locator exactly as it will be written in ``REPORT.md``
        (for a query, ``q:<id>``).
    payload
        Free text describing the event — for a query, the SQL that ran.
    session_id
        Omitted from the record when unknown, never fabricated.
    """
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **({"session_id": session_id} if session_id else {}),
        "kind": kind,
        "locator": locator,
        "payload": payload,
    }
    with open(Path(project_dir) / JOURNAL_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def find_query(project_dir: Path, locator: str) -> dict | None:
    """Return the most recent ``kind == "query"`` record for ``locator``.

    Lines that are not JSON objects, and records carrying no non-empty string
    ``ts``, are skipped rather than trusted: a truncated or hand-edited journal
    must not resolve a pointer to a timestamp that isn't there.

    Reads with ``errors="replace"`` so that undecodable bytes degrade a single
    line to unparseable rather than raising out of the resolver. ``claims
    build`` reads this file; a journal corrupted by a partial write must leave a
    query unresolved, not abort the whole projection.

    Returns ``None`` when the journal is absent, unreadable, or holds no record
    for this locator — all three are the same fact to a reader, that the query
    was never captured.
    """
    found = None
    try:
        with open(
            Path(project_dir) / JOURNAL_FILE, encoding="utf-8", errors="replace"
        ) as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                ts = record.get("ts") if isinstance(record, dict) else None
                if (
                    isinstance(ts, str)
                    and ts.strip()
                    and record.get("kind") == "query"
                    and record.get("locator") == locator
                ):
                    found = record
    except OSError:
        return None
    return found

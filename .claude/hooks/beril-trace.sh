#!/usr/bin/env bash
# PostToolUse hook → append a secret-redacted provenance row to the active
# project's TRACE.jsonl. Strictly best-effort: it must NEVER block the turn, so
# it always exits 0 regardless of what happens. The hook payload (JSON) arrives
# on stdin and is passed straight through to the CLI verb.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)"
if [ -n "$root" ]; then
  py="$root/.venv/bin/python"
  [ -x "$py" ] || py="python3"
  cd "$root" 2>/dev/null && "$py" -m beril_cli.cli trace-append >/dev/null 2>&1
fi
exit 0

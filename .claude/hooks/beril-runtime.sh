#!/usr/bin/env bash
# SessionStart hook → write/merge the active project's runtime.json.
# Strictly best-effort: it must NEVER block the session, so it always exits 0.
# The hook payload (JSON) arrives on stdin and is passed through to the CLI verb.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)"
if [ -n "$root" ]; then
  py="$root/.venv/bin/python"
  [ -x "$py" ] || py="python3"
  cd "$root" 2>/dev/null && "$py" -m beril_cli.cli runtime-snapshot >/dev/null 2>&1
fi
exit 0

#!/bin/sh
# beril-research-state.sh — SessionStart hook (best-effort, always exit 0).
#
# Reinjects the beril cross-session orientation (world-model "where am I /
# what's next") as SessionStart additionalContext. The `beril whereami
# --reinject` command resolves the active project itself (by mtime) and renders
# a guard-wrapped orientation block.
#
# Strictly advisory: any failure (missing beril, no project, bad output) is
# swallowed and the hook exits 0 so a session never breaks. It never mutates
# world-model content and never gates a lifecycle transition.

# Drain stdin (the hook JSON payload); its contents are not needed.
cat >/dev/null 2>&1 || true

# Resolve a Python interpreter for both the CLI fallback and JSON encoding.
PY=""
if command -v python3 >/dev/null 2>&1; then
	PY="python3"
elif command -v python >/dev/null 2>&1; then
	PY="python"
fi

# Resolve the beril command: prefer the installed entry point, else the module.
run_whereami() {
	if command -v beril >/dev/null 2>&1; then
		beril whereami --reinject 2>/dev/null
	elif [ -n "$PY" ]; then
		"$PY" -m beril_cli.cli whereami --reinject 2>/dev/null
	else
		return 1
	fi
}

emit() {
	# $1 = orientation text. Emit SessionStart additionalContext as JSON,
	# JSON-encoding the text via Python so embedded quotes/newlines are safe.
	# The text is passed through an env var (not stdin) so it does not collide
	# with the heredoc that feeds the Python program on stdin.
	[ -n "$PY" ] || return 1
	BERIL_ORIENTATION="$1" "$PY" - <<'PY' 2>/dev/null
import json, os
text = os.environ.get("BERIL_ORIENTATION", "")
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": text,
    }
}))
PY
}

# Best-effort: capture orientation; emit only on non-empty success.
orientation=$(run_whereami) || exit 0
if [ -n "$orientation" ]; then
	emit "$orientation" || true
fi

exit 0

---
description: Show the recent event-level trace (TRACE.jsonl) for a project — read-only.
argument-hint: "[project_id] [count]"
allowed-tools: Read, Bash
---

# Trace (`/trace`)

Show the recent tool-event trace for a project. **Read-only** — this never writes or modifies anything.

Arguments: `$ARGUMENTS`

## Steps

1. Resolve the project id from the first argument, or from the current working directory if inside `projects/{id}/`. The optional second argument is how many recent events to show (default 30).
2. If `projects/{project_id}/TRACE.jsonl` does not exist, tell the user there is no trace yet (it is appended by the `PostToolUse` hook as tools run inside that project) and stop.
3. Show the last N rows, e.g. `tail -n {count} projects/{project_id}/TRACE.jsonl`, and summarize them: for each event, the timestamp, the tool, and a short description of the (already secret-redacted) input. Highlight notable events (notebook edits, queries, submissions).

Note that the trace is append-only, **secret-redacted at write time**, and **non-authoritative** — an inspectable record of what ran, not a trust signal. Do not edit `TRACE.jsonl` or any other file. Treat the file as already redacted; do not attempt to un-redact or fetch secrets.

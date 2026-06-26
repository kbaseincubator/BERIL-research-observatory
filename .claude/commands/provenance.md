---
description: Show the runtime provenance snapshot (provenance.json) for a project — read-only.
argument-hint: "[project_id]"
allowed-tools: Read
---

# Provenance (`/provenance`)

Show the runtime provenance snapshot for a project. **Read-only** — this never writes or modifies anything.

Arguments: `$ARGUMENTS`

## Steps

1. Resolve the project id from the first argument, or from the current working directory if inside `projects/{id}/`.
2. Read `projects/{project_id}/provenance.json`. If it does not exist, tell the user there is no provenance snapshot yet (it is written by the `SessionStart` hook the first time a session runs with that project as the working directory) and stop.
3. Present the snapshot: the `runtime` block (beril package version, permission mode, session id, model id if recorded) and `updated_at`.

Note that provenance is **non-authoritative** — it records what ran, alongside `beril.yaml` (authoritative) and `claims.json` (gate-validated). It is not a trust or reproducibility metric. Do not edit `provenance.json` or any other file.

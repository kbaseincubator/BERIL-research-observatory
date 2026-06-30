---
description: Show the runtime-provenance snapshot (runtime.json) for a project — read-only.
argument-hint: "[project_id]"
allowed-tools: Read
---

# Runtime provenance (`/runtime`)

Show the runtime-provenance snapshot for a project — *how a session ran*. **Read-only** — this never writes or modifies anything.

Arguments: `$ARGUMENTS`

## Steps

1. Resolve the project id from the first argument, or from the current working directory if inside `projects/{id}/`.
2. Read `projects/{project_id}/runtime.json`. If it does not exist, tell the user there is no runtime snapshot yet (it is written by the `SessionStart` hook the first time a session runs with that project as the working directory) and stop.
3. Present the snapshot (shaped loosely to W3C PROV): the `agent` block (beril version, model id if recorded), the `activity` block (session id, permission mode), and `updated_at`.

This is **runtime / execution** provenance (who/what/when ran) — distinct from *source / lineage* provenance (a project's `data/PROVENANCE.md` and the Atlas's source frontmatter). It is **non-authoritative** — it records what ran, alongside `beril.yaml` (authoritative) and `claims.json`. It is not a trust or reproducibility metric. Do not edit `runtime.json` or any other file.

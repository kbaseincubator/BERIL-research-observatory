---
description: Show the runtime-provenance session history (runtime.json) for a project — read-only.
argument-hint: "[project_id]"
allowed-tools: Read
---

# Runtime provenance (`/runtime`)

Show the runtime-provenance history for a project — *how observed sessions ran*. **Read-only** — this never writes or modifies anything.

Arguments: `$ARGUMENTS`

## Steps

1. Resolve the project id from the first argument, or from the current working directory if inside `projects/{id}/`.
2. Read `projects/{project_id}/runtime.json`. If it does not exist, tell the user there is no runtime history yet and stop.
3. Present each `sessions[]` record separately: session id/observation time, `agent` (beril version, model, effort), `activity` (source, permission mode), `code` (git sha, dirty), `tenant`, `actor` (user, ORCID), `cost` (session-to-date USD, when observed, and `counted_usd` — the portion already attributed to a closed stage), and `documented_datasets_snapshot` (REPORT hash, observation time, and author-documented collections/tables). Any field may be absent.
4. If `beril.yaml` has an `agent_cost` block, show the per-stage ledger and the total (the sum of the `usd` column). Say plainly that it is a **floor**: only Claude Code sessions are observed, so work done by a human or by another agent is not counted. A stage with `sessions_observed: 0` and no `usd` was **unobserved** — do not report it as costing nothing. `last_status` in `runtime.json` is the stage currently being watched, not a lifecycle assertion; `beril.yaml.status` remains authoritative.

This is **runtime / execution** provenance (who/what/when was observed) — distinct from *source / lineage* provenance. The documented dataset snapshot does not prove which queries executed. It is non-authoritative and excluded from OpenViking scientific recall. Do not edit `runtime.json` or any other file.

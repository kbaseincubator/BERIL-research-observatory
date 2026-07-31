# `claims.json` schema

`projects/<id>/claims.json` is a generated, per-project projection of the
author-written `## Claims` section in `REPORT.md`. Version `2.0` is the stable
contract for downstream consumers such as planning-workflow and OpenViking.
It is not a second cross-project claims database.

## Top-level contract (schema `2.0`)

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Exactly `"2.0"`. |
| `project` | string | Project directory id. |
| `updated_at` | ISO-8601 string | Projection generation time. |
| `report_hash` | string | `sha256:<hex>` of the exact `REPORT.md` projected. |
| `claims` | array | Claim records. This is the canonical collection key. |
| `summary` | object | Stable tally described below. |

Each claim has `claim_id`, `claim`, `author_assertions`, `computed`, `supports`,
and `refutes`. `reviewer_notes` may also be present. `author_assertions.status`
and `author_assertions.confidence` are read from `REPORT.md`; `supported` and
`refuted` therefore mean "the report author marked this status," not "BERIL
independently proved this verdict."

Status values are `open`, `supported`, `refuted`, `needs-replication`, `blocked`,
and `needs-evidence`. Confidence values are `high`, `medium`, and `low`.

## Evidence and resolution

Evidence kinds are `query`, `notebook`, `figure`, `paper`, `web`, and `docs`.
Every pointer preserves `kind`, `locator`, and `exact`; it may have an explicit
`stream`. Its generated `resolution.status` is one of:

- `resolved`: a local re-runnable artifact and optional cell were found.
- `unresolved`: a well-formed pointer could not be resolved.
- `invalid`: the locator was malformed or unsafe.
- `not-checked`: the pointer kind is preserved but is not a local computed
  artifact checked by this projection.

Notebook paths are relative to the project directory and must remain inside it,
including after symlink resolution. `#cell-N` is the one-based ordinal in the
notebook's `cells` array. Absolute paths, traversal outside the project, malformed
anchors, missing notebooks, and missing cells never contribute support.

Query locators use `q:<id>` and resolve against the durable query registry,
`projects/<id>/journal.jsonl`, written by `beril capture-event` while the query runs.
A registered locator resolves to `{status: resolved, query_id, recorded_at}` — the
timestamp of the most recent matching record — and contributes support exactly as a
resolved notebook pointer does. A well-formed locator that was never registered is
preserved as `unresolved` with reason `query-not-recorded`, and contributes nothing;
an absent journal and a journal without that id are the same fact. Capture is
agent-invoked and best-effort, so an unresolved query pointer means the query was not
registered, not that it did not run.

`computed.resolved_artifact_support` is `none`, `single-stream`, or
`multiple-streams`. It is deliberately not called scientific groundedness.
Only resolved notebook/query pointers count. Multiple artifacts without stream
metadata share the conservative `default` stream. Authors may declare a stream
with `[stream: <id>]`, but this groups artifacts only; it does not independently
verify scientific independence. `computed.confidence_mismatch` is advisory and
true when written `high`/`medium` confidence lacks multiple explicit resolved
streams.

## Summary contract

`summary` contains:

- `total`
- `author_status`: a count for every status enum value
- `resolved_artifact_support`: counts for `multiple-streams`, `single-stream`,
  and `none`
- `confidence_mismatch`
- `evidence_resolution`: counts for `resolved`, `unresolved`, `invalid`, and
  `not-checked`

Planning-workflow should use `summary.total` and `summary.author_status` for an
accurate tally, while labeling the statuses as author assertions.

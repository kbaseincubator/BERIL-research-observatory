# OpenViking Phase 2 Implementation

This document describes the Phase 2 slice of the OpenViking migration: read
parity plus the first shared live-context write paths.

It builds on the baseline and resource-model decisions in
[`docs/viking_sql_migration.md`](viking_sql_migration.md).

## Scope Implemented

The repository now includes a root-level Observatory Context Service under
[`observatory_context/service/`](../observatory_context/service) with these
public methods:

- `search_context(query, kind?, project?, tags?, detail_level?)`
- `get_resource(id_or_uri, detail_level?)`
- `get_project_workspace(project_id, detail_level?)`
- `list_project_resources(project_id, kind?, path?)`
- `related_resources(id_or_uri, mode?, limit?)`
- `add_note(project_id?, title, body, tags?, links?)`
- `add_observation(project_id?, source_ref?, body, tags?, links?)`

Supporting modules live under:

- [`observatory_context/retrieval/`](../observatory_context/retrieval)
- [`observatory_context/notes/`](../observatory_context/notes)

## Read Path Behavior

### Authored resources

Authored research artifacts still come from Git through the existing Phase 1
manifest builder:

- project `README.md`
- project `REPORT.md`
- project `provenance.yaml`
- figures listed in `docs/figure_catalog.yaml`
- raw `knowledge/*.yaml` documents

The service indexes those manifest items locally and keeps Git authoritative for
their authored content.

### Deterministic detail levels

`get_resource(...)` and `search_context(...)` continue to use deterministic
`L0`, `L1`, and `L2` rendering through
[`observatory_context/render.py`](../observatory_context/render.py).

No model-generated summary is required for parity-critical responses.

### Workspace boundary

`get_project_workspace(project_id, ...)` and
`list_project_resources(project_id, ...)` treat
`viking://resources/observatory/projects/{project_id}` as the default retrieval
boundary.

The workspace includes:

- authored project resources from the manifest
- live notes and observations under `projects/{project_id}/notes/...`

### Search fallback

`search_context(...)` tries the OpenViking search path first when a client is
available. If semantic retrieval is unavailable or produces no resolvable local
result, the service falls back to lexical/path/metadata search over:

- IDs
- titles
- URIs
- source refs
- tags
- research-question text
- stored body text

This is the first fix for discoverability gaps like `org_adp1`.

### Related resources

`related_resources(...)` is intentionally not a graph traversal API.

It ranks resources by:

- same-project membership
- shared tags
- shared source refs
- explicit resource links

Optional overlay links may enrich this later, but Phase 2 stays metadata- and
link-driven.

## Live Context Writes

Notes and observations are now written as OpenViking live-context resources with
YAML front matter plus markdown body.

Default URI layout:

```text
viking://resources/observatory/projects/{project_id}/notes/{date}/{resource_id}
viking://resources/observatory/notes/{date}/{resource_id}
```

The write path is append-only by URI. Git-authored artifacts are not mutated by
these writes.

Each live resource stores:

- `id`
- `kind`
- `title`
- `project_ids`
- `source_refs`
- `tags`
- `links`
- `created_at`
- `updated_at`
- `author_or_actor`
- `provenance`

## Thin Client Extensions

[`observatory_context/client.py`](../observatory_context/client.py) remains a
thin wrapper. Phase 2 only added the primitives needed for the service:

- `read_resource`
- `stat_resource`
- `make_directory`
- `link_resources`
- `relations`
- `add_text_resource`

## Tests Added

Phase 2 coverage currently includes:

- resource fetch with deterministic `L1` and `L2`
- project workspace listing
- project resource filtering
- lexical fallback when semantic retrieval is unavailable
- metadata/link-driven related-resource ranking
- note and observation writes becoming visible to later reads

See [`scripts/tests/test_viking_phase2.py`](../scripts/tests/test_viking_phase2.py).

## Still Deferred

Phase 2 does **not** implement:

- deterministic export materialization back into Git
- overlay reconstruction beyond raw document ingest
- SQLite
- tenancy or memory design
- UI integration

Those moved into Phase 3 and later work.

For the landed export slice, see
[`docs/openviking_phase3.md`](openviking_phase3.md).
For the next implementation slice, see
[`docs/openviking_phase4_plan.md`](openviking_phase4_plan.md).

# OpenViking Phase 0/1 Implementation

This document describes what is now implemented in the repository for the
OpenViking migration baseline and the document-first ingest slice.

It complements, but does not replace, the higher-level migration plan in
[`docs/viking_sql_migration.md`](viking_sql_migration.md).

## Scope Implemented

The current implementation covers:

- **Phase 0** baseline capture for the existing Git-native knowledge layer
- **Phase 1** document-first ingest scaffolding for OpenViking
- deterministic local render generation and parity checks
- repo-managed local setup and resource-model documentation

It does **not** yet cover:

- the Observatory Context Service read/write API
- note or observation writes into OpenViking
- export materialization back into Git
- structured overlay reconstruction
- UI integration

## New Files And Entry Points

### Root package

The new root Python package is
[`observatory_context/`](../observatory_context).

Key modules:

- `baseline.py`: captures deterministic baseline counts and query fixtures
- `client.py`: thin lazy wrapper around the OpenViking HTTP client
- `config.py`: `BERIL_*` environment-based settings
- `uris.py`: deterministic URI mapping helpers
- `render.py`: deterministic L0/L1/L2 renderers
- `parity.py`: local parity issue reporting
- `ingest/manifest.py`: document-first manifest builder

### Scripts

- [`scripts/viking_capture_baseline.py`](../scripts/viking_capture_baseline.py)
- [`scripts/viking_ingest.py`](../scripts/viking_ingest.py)
- [`scripts/viking_materialize_renders.py`](../scripts/viking_materialize_renders.py)
- [`scripts/viking_validate_parity.py`](../scripts/viking_validate_parity.py)

### Supporting docs and config

- [`config/openviking/ov.conf.example`](../config/openviking/ov.conf.example)
- [`docs/openviking_setup.md`](openviking_setup.md)
- [`docs/openviking_resource_model.md`](openviking_resource_model.md)
- [`docs/migration_baseline/2026-03-19/baseline_snapshot.yaml`](migration_baseline/2026-03-19/baseline_snapshot.yaml)

## Phase 0: Baseline Capture

`scripts/viking_capture_baseline.py` records the pre-migration repository state
into `docs/migration_baseline/2026-03-19/`.

The snapshot currently records:

- core artifact counts:
  - 46 projects
  - 383 figures
  - 20 organisms
  - 15 genes
  - 10 pathways
  - 14 methods
  - 21 concepts
  - 32 relations
  - 20 hypotheses
  - 43 timeline events
- validator results for:
  - `validate_provenance`
  - `validate_knowledge_graph`
  - `validate_registry_freshness`
- representative query outputs for:
  - `metal stress`
  - `essential genes`
  - `org_adp1`
  - `landscape`
  - `gaps`

The snapshot is intentionally local and deterministic. It is the parity target
for the current Phase 1 implementation, not yet a production monitoring system.

## Phase 1: Document-First Ingest

The current ingest path is manifest-driven.

`scripts/viking_ingest.py` builds a logical resource manifest from:

- project `README.md`
- project `REPORT.md`
- project `provenance.yaml`
- project figure files referenced by `docs/figure_catalog.yaml`
- YAML files under `knowledge/`, imported only as raw retrievable documents

The current ingest model keeps the migration document-first:

- project README becomes `kind=project`
- project report and provenance become `kind=project_document`
- figures become `kind=figure`
- `knowledge/*.yaml` becomes `kind=knowledge_document`

No structured overlay rebuild happens yet.

## Deterministic URI And Render Rules

The Phase 1 code enforces stable URIs:

- project resources:
  `viking://resources/observatory/projects/{project_id}/authored/{relative_path}`
- figures:
  `viking://resources/observatory/projects/{project_id}/authored/figures/{figure_id}`
- raw knowledge imports:
  `viking://resources/observatory/overlays/raw-knowledge/{relative_path}`

`scripts/viking_materialize_renders.py` writes deterministic L0/L1/L2 markdown
files under `.cache/openviking/renders/` using the manifest metadata. These are
local artifacts for inspection and parity work; they are not yet materialized
back into tracked Git exports.

## Current Parity Story

`scripts/viking_validate_parity.py` currently checks:

- current artifact counts against the captured baseline snapshot
- duplicate logical URIs in the generated manifest
- missing project workspaces relative to `docs/project_registry.yaml`

At this stage parity is still **repository-local**:

- it proves the manifest and baseline capture behave deterministically
- it does not yet prove full round-trip parity against a populated live
  OpenViking server

That stronger parity check belongs in the next implementation slices.

## Local Workflow

Typical local flow:

```bash
uv sync --extra dev
cp config/openviking/ov.conf.example config/openviking/ov.conf
export OPENVIKING_CONFIG_FILE="$PWD/config/openviking/ov.conf"

uv run scripts/viking_capture_baseline.py
uv run scripts/viking_ingest.py --dry-run --limit 5
uv run scripts/viking_materialize_renders.py
uv run scripts/viking_validate_parity.py
```

Only run `scripts/viking_ingest.py` without `--dry-run` when the OpenViking
server is actually running and you want to upload resources.

## Limits Of The Current Implementation

The current implementation is intentionally conservative.

- It does not mutate existing registry or graph outputs.
- It does not create a second source of truth.
- It does not define the Phase 2 API contract beyond the migration plan.
- It does not yet persist OpenViking notes, observations, or shared-context
  writes.
- It does not assume a specific production OpenViking deployment topology
  beyond one shared HTTP server.

## Recommended Next Reading

- [`docs/openviking_setup.md`](openviking_setup.md)
- [`docs/openviking_resource_model.md`](openviking_resource_model.md)
- [`docs/openviking_next_phases.md`](openviking_next_phases.md)

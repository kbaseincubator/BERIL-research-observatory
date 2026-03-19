# OpenViking Phase 3 Implementation

This document describes the landed Phase 3 slice of the OpenViking migration:
deterministic export materialization from OpenViking-backed authored resources
into Git review artifacts.

It builds on the service and live-context write path in
[`docs/openviking_phase2.md`](openviking_phase2.md).

## Scope Implemented

Phase 3 adds a dedicated materialization layer under
[`observatory_context/materialize/`](../observatory_context/materialize) and two
entry-point scripts:

- [`scripts/viking_materialize_exports.py`](../scripts/viking_materialize_exports.py)
- [`scripts/viking_validate_exports.py`](../scripts/viking_validate_exports.py)

The exported Git review artifacts are:

- `docs/project_registry.yaml`
- `docs/figure_catalog.yaml`

## Materialization Rules

- Git remains authoritative for authored research assets.
- OpenViking-backed authored resources remain the source for export
  materialization.
- Generated YAML remains single-writer and deterministic.
- Live notes and observations written in Phase 2 are not exported in this slice.

## Export Inputs

The Phase 1/2 manifest now carries export-critical metadata on authored
resources:

- project `README.md` resources include `export_project`
- figure resources include `export_figure`

Those metadata payloads are derived from the existing repository parsers so the
Phase 3 export path preserves current registry contracts while keeping the Phase
2 service API unchanged.

## Commands

Materialize directly into tracked docs:

```bash
uv run scripts/viking_materialize_exports.py
```

Materialize into another directory for review or CI:

```bash
uv run scripts/viking_materialize_exports.py --output-dir /tmp/openviking-exports
```

Validate generated exports against tracked outputs:

```bash
uv run scripts/viking_validate_exports.py --generated-dir /tmp/openviking-exports
```

## Tests Added

Phase 3 coverage now includes:

- project registry export from project resources
- figure catalog export from figure resources
- deterministic ordering
- missing export metadata failures
- parity validation against tracked YAML outputs

See [`scripts/tests/test_viking_phase3.py`](../scripts/tests/test_viking_phase3.py).

## Still Deferred

Phase 3 still does not implement:

- overlay reconstruction/materialization
- SQLite or reporting storage
- tenancy or memory design
- UI integration

Those remain the next implementation slice.

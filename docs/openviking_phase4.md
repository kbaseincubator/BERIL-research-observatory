# OpenViking Phase 4 Implementation Brief

This document defines the intended implementation slice for Phase 4.

Phase 3 established deterministic export materialization for:

- `docs/project_registry.yaml`
- `docs/figure_catalog.yaml`

The next slice should add deterministic overlay materialization for the current
knowledge layer without expanding the migration scope.

## Objective

Reconstruct the current `knowledge/*.yaml` family as optional,
OpenViking-backed overlay resources while preserving the existing
source-of-truth boundaries:

- Git remains authoritative for authored project assets and tracked knowledge
  files
- OpenViking remains the shared context layer
- overlay outputs remain deterministic and generated

## Implementation Boundary

Phase 4 should implement only:

- a narrow overlay materialization layer for the current tracked knowledge YAML
  files
- deterministic serialization for overlay outputs
- parity validation against tracked `knowledge/*.yaml` files
- targeted Phase 4 tests and script entry points

Phase 4 should not implement:

- SQLite
- tenancy
- memory design
- UI integration
- generic graph traversal APIs
- export of Phase 2 live notes or observations into authored Git files

## Recommended Modules

- `observatory_context/overlays/`
- `scripts/viking_materialize_overlays.py`
- `scripts/viking_validate_overlays.py`
- `scripts/tests/test_viking_phase4.py`

## References

- [`docs/openviking_phase3.md`](openviking_phase3.md)
- [`docs/openviking_phase4_plan.md`](openviking_phase4_plan.md)
- [`docs/plans/2026-03-19-openviking-phase4.md`](plans/2026-03-19-openviking-phase4.md)
- [`docs/openviking_resource_model.md`](openviking_resource_model.md)
- [`docs/viking_sql_migration.md`](viking_sql_migration.md)

# OpenViking Phase 3 Plan

This document narrows the next implementation slice after Phase 2.

For the executable step-by-step implementation plan, see
[`docs/plans/2026-03-19-openviking-phase3.md`](plans/2026-03-19-openviking-phase3.md).

The Phase 2 service now provides stable reads plus live note and observation
writes. The next step should stay focused on deterministic export
materialization only.

## Phase 3 Goal

Rebuild selected Git review artifacts from OpenViking resources without
changing the source-of-truth boundaries:

- Git remains authoritative for authored research assets
- OpenViking remains authoritative for live notes, observations, and shared
  context
- generated Git exports remain materialized outputs, not hand-edited files

## Required Outcomes

- deterministic export path for `docs/project_registry.yaml`
- deterministic export path for `docs/figure_catalog.yaml`
- parity checks against the current tracked outputs
- validator compatibility with existing repository workflows

## Recommended Repository Shape

Add a dedicated materialization layer instead of embedding export logic into the
service:

- `observatory_context/materialize/`
- `scripts/viking_materialize_exports.py`
- `scripts/viking_validate_exports.py`

## Suggested Implementation Order

1. Define the internal export schema derived from OpenViking resources.
2. Rebuild `project_registry.yaml` deterministically from project resources.
3. Rebuild `figure_catalog.yaml` deterministically from figure resources.
4. Compare generated exports against the current tracked files.
5. Keep existing validators green before redirecting any older builder path.

## Guardrails

- Do not add overlay reconstruction in this slice.
- Do not add SQLite in this slice.
- Do not wire the service directly into the UI as part of Phase 3.
- Do not introduce dual-write behavior for generated Git files.

## Minimum Verification

- targeted Phase 3 tests
- parity comparison for both exported YAML files
- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`

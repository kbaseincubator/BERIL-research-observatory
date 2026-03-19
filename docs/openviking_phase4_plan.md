# OpenViking Phase 4 Plan

This document narrows the next implementation slice after Phase 3.

For the executable step-by-step implementation plan, see
[`docs/plans/2026-03-19-openviking-phase4.md`](plans/2026-03-19-openviking-phase4.md).

The Phase 3 export path now rebuilds deterministic Git review artifacts from
OpenViking-backed authored resources. The next slice should stay focused on
structured overlay resources only.

## Phase 4 Goal

Add the first deterministic overlay family on top of the existing context layer
without changing the Phase 2/3 source-of-truth boundaries.

## Required Outcomes

- reconstruct the current Layer 3 knowledge files as optional OpenViking-backed
  overlay resources
- keep overlays derived and deterministic
- expose overlays through repository-validation-compatible materialization
  commands only where needed
- preserve the existing service contract unless a Phase 4 read path requires a
  small, explicit extension

## Guardrails

- Do not add SQLite in this slice.
- Do not add tenancy or memory design in this slice.
- Do not wire the service into `ui/` in this slice.
- Do not export live notes or observations into authored Git files.
- Do not introduce graph-depth traversal as a generic API.

## Candidate Scope

The preferred Phase 4 slice is:

- add one overlay namespace under `overlays/`
- materialize the current raw knowledge family as deterministic overlay
  resources
- validate parity against the tracked `knowledge/*.yaml` documents

Anything beyond that should be deferred to a later phase.

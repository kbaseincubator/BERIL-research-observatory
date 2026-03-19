# OpenViking Next Phases Guide

This document turns the migration plan into concrete implementation guidance for
Phases 2 through 4.

The intended reading order is:

1. [docs/viking_sql_migration.md](viking_sql_migration.md)
2. [docs/openviking_phase0_phase1.md](openviking_phase0_phase1.md)
3. this guide

## Current Starting Point

The repository now has:

- a captured baseline snapshot
- a deterministic manifest builder
- deterministic URI and render helpers
- a thin OpenViking HTTP client wrapper
- local parity checks against the captured baseline

The next phases should build on that foundation rather than bypass it.

## Phase 2: Read Parity And Shared Context

### Goal

Add an Observatory Context Service that exposes stable read APIs and the first
live-context write APIs on top of OpenViking.

### Required outcomes

- `search_context(...)` returns project-scoped and cross-project results
- `get_resource(...)` returns deterministic L0/L1/L2 detail
- `get_project_workspace(...)` returns the default retrieval unit for a project
- `list_project_resources(...)` exposes the workspace contents cleanly
- `related_resources(...)` works without requiring graph traversal
- `add_note(...)` and `add_observation(...)` write live context into OpenViking
- lexical/path/metadata fallback works when embeddings are unavailable

### Recommended repository shape

Keep the Context Service as a new standalone service layer under the root
package first.

Recommended additions:

- `observatory_context/service/`
- `observatory_context/retrieval/`
- `observatory_context/notes/`
- `scripts/viking_smoke_test.py`

Do **not** wire this directly into `ui/app` as the first step. Keep the service
contract stable first, then let the UI or MCP layer call into it.

### Suggested implementation order

1. Add typed request/response models for the read APIs.
2. Implement `get_resource` and `get_project_workspace` first.
3. Implement `list_project_resources`.
4. Add `search_context` with explicit project, kind, and tag filtering.
5. Add `related_resources` using:
   - same-project membership
   - shared tags
   - source references
   - explicit links
   - optional overlay links when present
6. Add `add_note` and `add_observation`.
7. Add failure-mode handling for semantic-search unavailability.

### Important design rules

- `detail_level` must keep using deterministic L0/L1/L2 rendering.
- Project workspaces remain the primary retrieval boundary.
- `related_resources` should stay metadata- and link-driven.
- Notes and observations should be append-only or revisioned.
- Do not introduce a universal graph traversal API.

### Minimum test coverage

- read-path tests for every public method
- one integration test against a real local OpenViking server
- regression test for `org_adp1`-like discoverability gaps
- fallback test where semantic retrieval is disabled and lexical retrieval still
  works
- multi-client note visibility test

### Exit checklist

- representative prompt retrieval is materially better than current
  `query_knowledge.py`
- a note written by one client is visible to another without a Git commit
- L0/L1/L2 behavior is consistent for resource fetches
- failures in ingest/search/write paths are observable and surfaced clearly

## Phase 3: Materialize Deterministic Exports

### Goal

Rebuild selected Git review artifacts from OpenViking rather than from the
current direct registry builder path.

### Required outcomes

- deterministic exports for at least:
  - `docs/project_registry.yaml`
  - `docs/figure_catalog.yaml`
- validator compatibility with current repo workflows
- explicit single-writer materialization path

### Recommended repository shape

Add a dedicated materialization layer rather than embedding export logic into
the service methods.

Recommended additions:

- `observatory_context/materialize/`
- `scripts/viking_materialize_exports.py`
- `scripts/viking_validate_exports.py`

### Suggested implementation order

1. Define an internal export schema derived from OpenViking resources.
2. Rebuild `project_registry.yaml` deterministically from project resources.
3. Rebuild `figure_catalog.yaml` deterministically from figure resources.
4. Compare generated exports against the current Git-native outputs.
5. Only after parity is stable, decide whether to retire or redirect parts of
   `scripts/build_registry.py`.

### Important design rules

- Generated exports remain read-only in Git after cutover.
- Export jobs must be deterministic and stable under re-run.
- There must be one materializer for generated Git outputs.
- No undocumented identifier drift is acceptable.

### Minimum test coverage

- golden-file style comparison for exported YAML structure
- parity tests against the current tracked outputs
- failure tests for missing resource metadata required by export
- validator tests proving the existing freshness and provenance workflows still
  pass

### Exit checklist

- exported artifacts remain repo-compatible
- existing validators pass on exported content
- no project or figure ID drift is introduced

## Phase 4: Reintroduce Structured Overlays Selectively

### Goal

Bring back only the structured overlay families that clearly improve retrieval
or workflow quality.

### Required outcomes

- explicit justification for each overlay family
- overlay storage under `overlays/{overlay_name}/...`
- optional use, not global requirement

### Suggested implementation order

1. Start with one overlay family only.
2. Prefer the overlay with the clearest retrieval payoff.
3. Validate that the overlay improves a concrete workflow.
4. Only then consider a second overlay family.

Practical candidate families:

- entity and relation overlays for cross-project biological concepts
- timeline overlays for observatory history browsing
- hypothesis overlays for active reasoning and review workflows

### Important design rules

- Overlays are secondary views, not the core ingest model.
- A project must still migrate cleanly without any overlay.
- Overlay exports to Git should exist only if the repo still benefits from
  reviewable files.
- Overlay presence should enrich `related_resources`, not redefine the base API.

### Minimum test coverage

- overlay generation from existing raw resources
- retrieval tests showing overlay-assisted improvement
- tests proving base retrieval still works when overlays are absent

### Exit checklist

- each overlay family has an explicit use case
- each overlay demonstrably improves retrieval or workflow quality
- overlays remain optional

## Cross-Phase Guardrails

These rules should stay fixed through the remaining migration work.

- Git stays authoritative for authored research artifacts.
- OpenViking owns live notes, observations, and shared working context.
- Generated Git outputs are materialized, not hand-edited.
- The migration stays resource-first, not graph-first.
- SQLite remains deferred unless a concrete analytics or reporting bottleneck
  appears.
- Multi-tenant account design and memory design remain deferred unless they
  become unavoidable for the accepted context layer.

## Suggested Commands For The Next Work Slices

Before Phase 2 implementation:

```bash
uv run scripts/viking_capture_baseline.py
uv run scripts/viking_validate_parity.py
```

During Phase 2 work:

```bash
uv run --with pytest pytest scripts/tests/test_viking_phase1.py -q
uv run scripts/validate_provenance.py
uv run scripts/validate_knowledge_graph.py
uv run scripts/validate_registry_freshness.py
```

Before claiming any later phase complete:

- run the relevant new tests for that phase
- run the three existing validators
- verify the baseline/parity expectations still hold unless intentionally
  superseded by a newer accepted snapshot

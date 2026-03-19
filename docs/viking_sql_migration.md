# Migration Plan: Current Knowledge Layer -> OpenViking

**Updated:** 2026-03-19

## Context

The observatory already has a working 3-layer knowledge system:

1. **Layer 1**: per-project `provenance.yaml`
2. **Layer 2**: derived registry artifacts in `docs/`
3. **Layer 3**: semantic graph files in `knowledge/`

This is not a greenfield migration. The current repository is the migration
input contract.

### Current baseline

As of 2026-03-19, the live repository contains:

| Artifact | Count |
|---|---:|
| Valid `provenance.yaml` files | 46 |
| Projects in `docs/project_registry.yaml` | 46 |
| Figures in `docs/figure_catalog.yaml` | 383 |
| Organisms | 20 |
| Genes | 15 |
| Pathways | 10 |
| Methods | 14 |
| Concepts | 21 |
| Relations | 32 |
| Hypotheses | 20 |
| Timeline events | 43 |

The current deterministic toolchain already works:

- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`
- `uv run scripts/query_knowledge.py ...`

## Decision

The end state remains **OpenViking as the active serving store** for observatory
knowledge, behind a thin observatory MCP layer.

The migration should be simplified relative to the earlier draft:

- **Keep scope to observatory knowledge only** in v1
- **Use a single shared OpenViking HTTP server**
- **Defer SQLite** until it is proven necessary as a derived read model
- **Defer user memory, agent memory, session memory, and multi-tenant admin
  flows** until after observatory migration parity is stable
- **Preserve the current YAML/Markdown schemas and IDs** as the interoperability
  contract

This means the migration is from:

`Git-native authoritative artifacts`

to:

`Git-compatible authoritative contract + OpenViking serving layer`

not from:

`old file system`

to:

`brand-new schema and storage model`

## Branch Strategy

This migration should be based on the current provenance/knowledge-layer work,
not on today's `main`.

### Required base

- `feature/structured-provenance` already contains the provenance schema,
  registry builder, query tooling, and `knowledge/` graph artifacts that are
  being migrated
- Current `main` does **not** contain that layer, so it is not a valid base for
  a migration of the current system

### Working rule

- If `feature/structured-provenance` merges first, create the migration branch
  from the updated `main`
- If work starts before that merge, stack the migration branch on top of
  `feature/structured-provenance`
- Do **not** start the migration from current `main`

## Target Architecture

```
┌────────────────────────────────────────────────────┐
│  Claude Code / humans / UI / future automations   │
│                     ↕                              │
├────────────────────────────────────────────────────┤
│        Observatory MCP Layer (thin wrapper)       │
│  • read/search tools for observatory knowledge    │
│  • write tools only after parity is proven        │
│  • audit metadata for mutations                   │
│                     ↕                              │
├────────────────────────────────────────────────────┤
│     OpenViking HTTP Server (single shared)        │
│  • AGFS-backed storage                            │
│  • hierarchical L0/L1/L2 retrieval                │
│  • semantic search over observatory resources     │
└────────────────────────────────────────────────────┘
                      ↑
                      │ import/export
                      ↓
┌────────────────────────────────────────────────────┐
│                Git Repository                      │
│  reports, provenance YAML, registry artifacts,    │
│  knowledge graph YAML, notebooks, figures, code   │
└────────────────────────────────────────────────────┘
```

### Source-of-truth boundaries

| Category | v1 role | Storage |
|---|---|---|
| Notebooks, figures, reports, code | Remain in Git | Repository files |
| Provenance schema and graph schema | Canonical contract | Repository files |
| Observatory serving store | OpenViking | `viking://resources/observatory/` |
| Export/rollback format | Repository-compatible YAML/Markdown | Generated from OpenViking before cutover is considered complete |

### Explicitly out of scope for v1

- SQLite sidecar
- Multi-tenant account design
- User preferences/session memory
- Agent skills memory
- Contradiction review queues
- UI migration off file parsing

## OpenViking Mapping

Use a single observatory namespace and preserve current identifiers wherever
they already exist.

```
viking://resources/observatory/
├── projects/{project_id}/
│   ├── overview
│   ├── provenance
│   └── figures/{figure_id}
├── findings/{finding_id}
├── entities/{type}/{entity_id}
├── relations/{relation_id}
├── hypotheses/{hypothesis_id}
└── timeline/{event_id}
```

### Mapping rules

| Current artifact | Viking target | ID rule |
|---|---|---|
| `projects/{id}/provenance.yaml` | `projects/{id}/provenance` | Preserve project ID |
| `docs/project_registry.yaml` entry | `projects/{id}/overview` | Preserve project ID |
| Provenance findings | `findings/{finding_id}` | Preserve finding ID from provenance when present |
| `knowledge/entities/*.yaml` entries | `entities/{type}/{id}` | Preserve entity ID |
| `knowledge/relations.yaml` entries | `relations/{id}` | Preserve relation ID if present; otherwise derive deterministically and document the rule |
| `knowledge/hypotheses.yaml` entries | `hypotheses/{id}` | Preserve existing hypothesis ID |
| `knowledge/timeline.yaml` entries | `timeline/{id}` | Preserve event ID if present; otherwise derive deterministically and document the rule |
| `docs/figure_catalog.yaml` entries | `projects/{project_id}/figures/{figure_id}` | Preserve figure filename when already unique, otherwise derive a stable figure ID |

### Content levels

OpenViking resources should be populated from existing artifacts, not from a
new bespoke schema:

- **L0**: short deterministic summary from structured fields
- **L1**: concise overview assembled from current project/graph metadata
- **L2**: full provenance/report/graph content or a lossless structured render

Do not treat the embedding model choice as an architecture decision. Keep it as
deployment configuration in the OpenViking server config.

## Migration Phases

## Phase 0: Baseline And Contract Freeze

Before any OpenViking import work:

1. Base the work on `feature/structured-provenance` or on `main` after merge
2. Rebuild and validate the current knowledge layer
3. Capture the live baseline counts listed above
4. Capture representative query outputs from the current CLI:
   - `metal stress`
   - `essential genes`
   - `org_adp1`
   - `landscape`
   - `gaps`

### Exit criteria

- Provenance validation passes
- Knowledge graph validation passes
- Registry freshness validation passes
- Baseline counts are recorded in the migration notes

## Phase 1: OpenViking Bootstrap And Import

Stand up the smallest viable deployment:

1. One shared `openviking-server` in HTTP mode
2. One observatory-specific config
3. One import/export utility for observatory knowledge

Import only observatory knowledge artifacts:

- project overviews
- provenance
- findings
- figures
- entities
- relations
- hypotheses
- timeline events

### Requirements

- Preserve current IDs whenever possible
- Generate deterministic IDs only where the repo does not already provide one
- Record the normalization rules used by the importer
- Implement export back to repository-compatible YAML/Markdown before moving to
  write cutover

### Exit criteria

- OpenViking import completes for all current artifacts
- Imported counts match the baseline
- Export path exists and reproduces repo-compatible artifacts

## Phase 2: Read Parity And MCP Integration

Add a thin observatory MCP layer on top of OpenViking.

### Initial MCP tools

- `search_knowledge(query, scope?, detail_level?)`
- `get_project(id, detail_level?)`
- `get_entity(id, detail_level?)`
- `get_hypothesis(id, detail_level?)`
- `browse_knowledge(path)`
- `related_to(entity_id, depth?)`

### Deliberate non-goals in this phase

- No `query_structured(sql)`
- No SQLite rebuild loop
- No session or user memory tools

For deterministic rollups such as landscape summaries and gap analysis, keep
using existing repository logic until there is demonstrated parity or a clear
reason to move them.

### Exit criteria

- Representative search results are materially equivalent to current CLI
- Project/entity/hypothesis detail retrieval works at L0/L1/L2
- Observability is in place for import and query failures

## Phase 3: Write Cutover

Only after read parity and export round-trip are proven:

### MCP write tools

- `add_finding(...)`
- `add_entity(...)`
- `add_relation(...)`
- `update_hypothesis(...)`
- `add_provenance(...)`

### Write rules

- Every write must keep ID stability
- Every write must remain exportable to repo-compatible artifacts
- Every write must record minimal audit metadata:
  - actor
  - timestamp
  - tool
  - target resource

### Exit criteria

- New or updated knowledge written through MCP exports cleanly
- Exported artifacts pass the same repo validators as the current system

## Optional Later Phases

These are intentionally deferred:

### SQLite sidecar

Only add SQLite if one of these becomes a real bottleneck:

- deterministic reporting latency
- ad hoc tabular joins across imported records
- full-text search behavior that OpenViking alone does not satisfy

If added later:

- treat SQLite as **derived and read-only**
- use SQLite WAL for concurrent readers with a single rebuilder/writer
- use FTS5 for text indexing
- do not make SQLite a co-equal source of truth

### Memory and tenancy

Only design user memory, agent memory, session memory, or multi-tenant account
separation after the observatory knowledge migration is stable and accepted.

## Acceptance Checks

The migration is not complete until these checks pass.

### Baseline validation

- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`

### Import parity

- project count matches `46`
- figure count matches `383`
- entity/relation/hypothesis/timeline counts match the baseline

### Query parity

- `search_knowledge("metal stress")` returns the same leading project class as
  the current CLI
- `search_knowledge("essential genes")` returns the same leading project class
  as the current CLI
- `related_to("org_adp1")` preserves the same connection story as the current
  graph files

### Export round-trip

- exported artifacts remain repository-compatible
- repo validators pass on exported content
- no undocumented ID drift

### Concurrency topology

- multiple clients successfully use one shared OpenViking HTTP server
- no design depends on multiple OpenViking processes sharing one data directory

## Why This Version Is Simpler

Compared with the earlier draft, this version removes several sources of
unnecessary complexity from v1:

- no SQLite sidecar
- no custom session-memory architecture
- no multi-tenant setup work
- no UI migration in the first phase
- no requirement to redesign the current provenance/graph contract
- no branch-from-current-main path that ignores the actual migration inputs

## External References

These inform the simplifications above and should be re-checked during
implementation:

- OpenViking official repository and examples:
  https://github.com/volcengine/OpenViking
- SQLite WAL:
  https://sqlite.org/wal.html
- SQLite FTS5:
  https://sqlite.org/fts5.html

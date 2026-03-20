# Migration Plan: Knowledge Layer -> OpenViking Context Layer

**Updated:** 2026-03-19

## Context

The observatory already has a working 3-layer knowledge system:

1. **Layer 1**: per-project `provenance.yaml`
2. **Layer 2**: derived registry artifacts in `docs/`
3. **Layer 3**: semantic graph files in `knowledge/`

This migration is not justified by "the current system is broken." The current
system already validates, serves deterministic queries, and works well with
Claude Code's filesystem tools.

The reason to introduce OpenViking is different:

- provide a **shared live context layer** for agents and humans without routing
  every context update through Git commits and merges
- improve **retrieval quality** across heterogeneous project artifacts,
  summaries, notes, and cross-project references
- keep **structured exports** where they are useful, without forcing the full
  observatory into one rigid graph model

This is therefore **not** a graph migration. It is a context-layer migration.

### Current baseline

As of 2026-03-19, the live repository contains:

| Artifact | Count |
|---|---:|
| Valid `provenance.yaml` files | 46 |
| Projects in `docs/project_registry.yaml` | 46 |
| Figures in `docs/figure_catalog.yaml` | 361 |
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

The target state is:

`Git-authored research assets + OpenViking live context layer + generated structured projections`

not:

`Git contract + graph-shaped OpenViking serving store`

Key design decisions:

- **Use OpenViking as the active shared context and retrieval layer**
- **Keep Git authoritative for authored research artifacts**
- **Make the current registry and graph outputs projections, not the core model**
- **Use documents/resources as the default data model**
- **Treat typed entities/relations/hypotheses/timeline as optional overlays**
- **Defer SQLite** until derived analytics or reporting make it necessary
- **Defer multi-tenant account design, session memory, and user memory** until
  the context-layer migration is stable

## Branch Strategy

This migration should still be based on the current provenance/knowledge-layer
work, not on today's `main`.

### Required base

- `feature/structured-provenance` already contains the provenance schema,
  registry builder, query tooling, and `knowledge/` artifacts that form the
  migration baseline
- Current `main` does **not** contain that layer, so it is not a valid base for
  this work

### Working rule

- If `feature/structured-provenance` merges first, create the migration branch
  from the updated `main`
- If work starts before that merge, stack the migration branch on top of
  `feature/structured-provenance`
- Do **not** start the migration from current `main`

## Target Architecture

```
┌───────────────────────────────────────────────────────┐
│ Claude Code / humans / UI / future automations       │
│                         ↕                             │
├───────────────────────────────────────────────────────┤
│         Observatory Context Service (MCP/API)        │
│  • browse/search/get tools                           │
│  • note/observation write tools                      │
│  • deterministic export/materialization jobs         │
│  • lexical fallback when embeddings are unavailable  │
│                         ↕                             │
├───────────────────────────────────────────────────────┤
│       OpenViking HTTP Server (single shared)         │
│  • document/resource-oriented storage                │
│  • hierarchical L0/L1/L2 retrieval                   │
│  • semantic + metadata retrieval over live context   │
│  • revisioned or append-only writes for live notes   │
└───────────────────────────────────────────────────────┘
                ↑                         ↓
         Git ingest for authored      Materialize
           research assets         deterministic exports
                ↑                         ↓
┌───────────────────────────────────────────────────────┐
│                   Git Repository                      │
│ reports, notebooks, code, figures, datasets,         │
│ selected reviewable YAML/Markdown projections         │
└───────────────────────────────────────────────────────┘
```

## Source-of-Truth Boundaries

Ownership is defined by **resource class**, not by system-wide slogan.

| Resource class | Authoritative location | Notes |
|---|---|---|
| Reports, notebooks, code, figures, datasets | Git | Human-authored, reviewable research artifacts |
| Live notes, observations, context summaries, soft links, working metadata | OpenViking | Shared context plane for agents and humans |
| Registry summaries and optional structured overlays | Generated from OpenViking into Git | Read-only generated outputs after cutover |

### Critical consistency rule

No logical record may be edited in both places.

- Git-authored assets are ingested into OpenViking
- OpenViking live-context writes are exported only through a materializer
- Generated repo artifacts are **not** hand-edited after cutover

This avoids the dual-write ambiguity in the previous plan.

## OpenViking Resource Model

Do **not** map the observatory into one flat global graph as the primary model.
Use a resource-centric hierarchy with minimal common metadata.

### Required metadata for every resource

- `id`
- `kind`
- `project_ids`
- `source_refs`
- `tags`
- `created_at`
- `updated_at`
- `author_or_actor`
- `provenance`
- `links`

### Recommended namespace

```
viking://resources/observatory/
├── projects/{project_id}/
│   ├── authored/          # ingested report, README, figure refs, manifests
│   ├── summaries/         # deterministic L0/L1/L2 renders
│   ├── notes/             # live notes, observations, interim context
│   └── exports/           # materialized per-project structured views
├── shared/
│   ├── digests/
│   ├── collections/
│   └── indexes/
├── notes/{date}/
└── overlays/{overlay_name}/
```

### Resource semantics

- `projects/{project_id}/...` is the default retrieval unit
- cross-project relationships are represented first as soft links, shared tags,
  citations, and source references
- graph-like overlays live under `overlays/` and are optional derived views
- no project is blocked from migration because it does not fit a global entity
  schema

## L0/L1/L2 Content Rules

L0/L1/L2 generation must be deterministic for parity-critical resources.

### Project resources

- **L0**: project ID, title, status, top tags, main question
- **L1**: concise project summary with key findings, main artifacts, and linked
  projects
- **L2**: full ingested report/provenance/export content

### Figure resources

- **L0**: figure file, project, short caption
- **L1**: caption + nearby context + tags
- **L2**: full figure metadata and source reference

### Note/observation resources

- **L0**: explicit title or first sentence + project
- **L1**: body summary assembled from stored metadata
- **L2**: full note content and references

### Overlay resources

- **L0**: ID + type + deterministic one-line summary
- **L1**: concise structured render from the source fields
- **L2**: full serialized overlay payload

Do **not** rely on model-generated summaries for acceptance-critical parity.
Model-generated enrichment may exist only as a convenience layer and must be
marked as derived.

## Observatory Context Service

The MCP layer is not a thin wrapper. It is a domain service with explicit
contracts.

### Initial read tools

- `search_context(query, kind?, project?, tags?, detail_level?)`
- `get_resource(id_or_uri, detail_level?)`
- `get_project_workspace(project_id, detail_level?)`
- `list_project_resources(project_id, kind?, path?)`
- `related_resources(id_or_uri, mode?, limit?)`

### Initial write tools

- `add_note(project_id?, title, body, tags?, links?)`
- `add_observation(project_id?, source_ref?, body, tags?, links?)`

### Tool behavior rules

- `detail_level` maps to deterministic L0/L1/L2 content
- `related_resources` uses soft links, shared metadata, citations, same-project
  membership, and overlay links when they exist
- do **not** ship depth-based graph traversal as a required primitive
- lexical/metadata retrieval remains available when embedding search is down

## Structured Overlays

The current Layer 3 graph becomes an **optional overlay family**, not the core
schema for the entire observatory.

### Overlay policy

- keep entity/relation/hypothesis/timeline overlays only where they materially
  improve a project family or workflow
- allow multiple overlay families over time instead of one universal graph
- store overlays under `overlays/{overlay_name}/...`
- treat overlays as generated or curated resources in OpenViking first, then
  export to Git only if reviewable files are still useful

### Default assumption

If a project does not benefit from a typed overlay, it still migrates cleanly as
documents, summaries, notes, and soft-linked resources.

## Migration Phases

## Phase 0: Baseline, Reframe, And Contract Freeze

Before any import work:

1. Base the work on `feature/structured-provenance` or on `main` after merge
2. Rebuild and validate the current knowledge layer
3. Capture the live baseline counts listed above
4. Capture representative query outputs from the current CLI:
   - `metal stress`
   - `essential genes`
   - `org_adp1`
   - `landscape`
   - `gaps`
5. Freeze the new ownership boundaries:
   - Git-authored assets
   - OpenViking live-context resources
   - generated export paths

### Exit criteria

- Provenance validation passes
- Knowledge graph validation passes
- Registry freshness validation passes
- Baseline counts are recorded
- Resource-class ownership rules are documented and accepted

## Phase 1: Bootstrap The Document-First Context Layer

Stand up the smallest viable deployment:

1. One shared `openviking-server` in HTTP mode
2. One observatory-specific config
3. One Git-ingest pipeline for authored assets
4. One deterministic L0/L1/L2 renderer

Initial ingest includes:

- project READMEs and reports
- provenance files
- figure references and figure metadata
- registry artifacts
- selected existing knowledge files as importable resources, not yet as a
  required graph core

### Requirements

- preserve stable project and artifact IDs where they already exist
- add resource metadata without forcing all items into one entity schema
- record normalization rules used by the importer
- keep ingest idempotent

### Exit criteria

- OpenViking import completes for all baseline projects
- project and figure counts match the baseline
- deterministic L0/L1/L2 renders exist for core resource kinds
- re-running ingest does not create duplicate logical resources

## Phase 2: Read Parity And Shared Context

Add the Observatory Context Service on top of OpenViking.

### Scope

- search, browse, get-resource, get-project-workspace
- note and observation writes into OpenViking
- related-resource retrieval using soft links and metadata
- lexical fallback when semantic retrieval is unavailable

### Deliberate non-goals in this phase

- no universal graph traversal contract
- no SQLite sidecar
- no multi-tenant account model
- no session memory design

### Exit criteria

- retrieval on representative prompts is materially better than the current CLI
  for context discovery
- a note written by one client is retrievable by another without a Git commit
- project and resource detail retrieval works at L0/L1/L2
- observability is in place for ingest, search, and write failures

## Phase 3: Materialize Deterministic Exports

Once shared-context retrieval is stable:

1. Materialize reviewable exports from OpenViking back into Git
2. Keep exported files deterministic and validator-friendly
3. Stop direct editing of generated export paths

### Initial export targets

- `docs/project_registry.yaml`
- `docs/figure_catalog.yaml`
- additional digest-style files if still useful

### Exit criteria

- exported artifacts remain repository-compatible
- existing repo validators still pass on exported content
- no undocumented ID drift occurs during materialization

## Phase 4: Reintroduce Structured Overlays Selectively

Only after the document-first context layer is stable:

1. decide which overlay families are still worth keeping
2. migrate entity/relation/hypothesis/timeline content into overlay namespaces
   only where they add real value
3. export overlay files to Git only if the repository still needs them

### Exit criteria

- overlay use cases are explicit and justified
- overlays improve retrieval or workflow quality for their target domains
- overlays remain optional, not mandatory for all projects

## Optional Later Phases

### SQLite sidecar

Only add SQLite if one of these becomes a real bottleneck:

- deterministic reporting latency
- ad hoc tabular joins across exported records
- analytics over stable materialized projections

If added later:

- treat SQLite as **derived and read-only**
- use SQLite WAL for concurrent readers with a single rebuilder/writer
- do not make SQLite a co-equal source of truth

### Memory and tenancy

Only design user memory, agent memory, session memory, or multi-tenant account
separation after the observatory context layer is stable and accepted.

## Concurrency And Availability

### Concurrency model

- live context writes in OpenViking should be append-only or revisioned
- generated Git exports should be written by a single materializer
- do not rely on concurrent in-place mutation of the same logical record

### Retrieval fallback

- semantic retrieval depends on embedding infrastructure
- when embeddings are unavailable, the Context Service must fall back to
  lexical/path/metadata search instead of failing closed

## Rollback Strategy

Rollback must remain simple throughout the migration:

- the current Git-native validators and query scripts stay functional until the
  OpenViking path is accepted
- if retrieval quality or data fidelity is not good enough, continue using the
  current deterministic toolchain as the primary path
- OpenViking remains removable until Phase 3 export materialization is proven

## Acceptance Checks

The migration is not complete until these checks pass.

### Baseline validation

- `uv run scripts/validate_provenance.py`
- `uv run scripts/validate_knowledge_graph.py`
- `uv run scripts/validate_registry_freshness.py`

### Import parity

- project count matches `46`
- figure count matches `361`
- project workspaces and authored assets ingest without duplicate logical
  resources

### Shared-context behavior

- a note added through the Context Service becomes visible to another client
  without a Git commit
- retrieval on representative prompts finds the correct project/workspace or
  artifact with materially better context coverage than the current CLI

### Export parity

- exported artifacts remain repository-compatible
- repo validators pass on exported content
- no undocumented ID drift occurs

### Topology

- multiple clients successfully use one shared OpenViking HTTP server
- no design depends on multiple OpenViking processes sharing one data directory
- the exporter/materializer is the only writer for generated Git outputs

## Why This Version Is Better Aligned

Compared with the earlier draft, this version:

- solves the actual problem of **shared live context**
- keeps OpenViking where it is strongest: resource-oriented retrieval
- stops forcing heterogeneous observatory data into one rigid global graph
- removes the undefined dual-write model
- preserves deterministic exports only where they are still useful
- keeps graph structure available as an overlay, not a universal constraint

## External References

These should be re-checked during implementation:

- OpenViking official repository:
  https://github.com/volcengine/openviking
- SQLite WAL:
  https://sqlite.org/wal.html

## Implementation Notes

The migration plan is now accompanied by implementation-specific docs:

- [docs/openviking_setup.md](openviking_setup.md)
- [docs/openviking_tutorial.md](openviking_tutorial.md)
- [docs/openviking_resource_model.md](openviking_resource_model.md)

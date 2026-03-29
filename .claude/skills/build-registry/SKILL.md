---
name: build-registry
description: Re-ingest all observatory resources into OpenViking. Use when data is missing, stale, or after bulk changes to projects.
allowed-tools: Bash, Read
user-invocable: true
---

# Build Registry Skill

Re-ingest observatory resources into OpenViking so that `/knowledge` queries reflect the latest project state.

## Usage

```
/build-registry              — incremental ingest (resources + knowledge graph)
/build-registry --check      — verify ingest status without re-ingesting
/build-registry --clean      — full rebuild from scratch (wipes graph + cache)
```

## Workflow

### Incremental Ingest (default)

Run:

```bash
uv run scripts/viking_ingest.py --rebuild-graph --wait
```

This does three phases:
1. **Phase 1** — Upload project resources (README, REPORT, provenance, figures). Uses `--resume` by default to skip existing resources.
2. **Phase 2** — Extract knowledge graph via CBORG (gpt-5.4-mini). Uses a local cache (`.kg_cache/`) to skip projects whose REPORT.md and provenance.yaml haven't changed since last extraction. Entities and hypotheses are deduplicated and merged across projects.
3. **Phase 3** — Generate L0/L1 tier summaries for entity directories and hypotheses.

The knowledge graph is uploaded as a single batch (one `add_resource` call with a directory), replacing the previous graph atomically.

Requires `CBORG_API_KEY` env var.

### Knowledge Graph Only

Skip Phase 1 resource upload, only rebuild the knowledge graph:

```bash
uv run scripts/viking_ingest.py --graph-only --wait
```

This is the fastest option when project resources are already uploaded and only the graph needs updating (e.g., after editing a REPORT.md).

### Full Rebuild from Scratch

```bash
uv run scripts/viking_ingest.py --no-resume --rebuild-graph --clean --wait
```

- `--no-resume`: re-uploads all project resources
- `--clean`: wipes the existing knowledge graph in OpenViking and the local extraction cache
- All projects are re-extracted via CBORG

### Single Project Update

```bash
uv run scripts/viking_ingest.py --graph-only --project <project_id> --wait
```

Note: with `--project`, only that project's resources are in scope, but the cached extractions for all other projects are still merged into the graph to maintain completeness.

### Check Status

```bash
uv run scripts/viking_ingest.py --check
```

Verifies all expected resources are present in OpenViking. Use `--fix` to re-ingest missing ones.

### Server Health

```bash
uv run scripts/viking_server_healthcheck.py          # one-shot status
uv run scripts/viking_server_healthcheck.py --watch   # auto-refresh until queues drain
```

To use a specific CBORG model: `--model claude-haiku` or `--model gpt-5.4-mini`

## Integration

- **Called by**: `/synthesize` (Step 7.6), `/submit` (Step 2), `/berdl_start` (Phase B)
- **Generates for**: `/knowledge` (query skill), `/suggest-research` (landscape analysis)
- **Source of truth**: OpenViking (all queries go through OpenViking)
- **Local cache**: `.kg_cache/` stores per-project extraction results for incremental rebuilds

## When to Re-ingest

Run an incremental ingest (`--graph-only --wait`) when:
- A project's REPORT.md or provenance.yaml changed
- A new project was added
- After running `/synthesize` on a project

Run a full rebuild (`--no-resume --rebuild-graph --clean --wait`) when:
- OpenViking data store was wiped or corrupted
- After merging branches that modified many projects
- When `/knowledge` queries return unexpected results

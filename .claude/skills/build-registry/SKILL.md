---
name: build-registry
description: Re-ingest all observatory resources into OpenViking. Use when data is missing, stale, or after bulk changes to projects.
allowed-tools: Bash, Read
user-invocable: true
---

# Build Registry Skill

Re-ingest all observatory resources into OpenViking so that `/knowledge` queries reflect the latest project state.

## Usage

```
/build-registry              — full re-ingest of all resources
/build-registry --check      — verify ingest status without re-ingesting
/build-registry --rebuild-graph  — re-ingest + extract knowledge graph via CBORG
/build-registry --graph-only     — rebuild knowledge graph only (skip resource upload)
```

## Workflow

### Full Re-ingest

Run:

```bash
uv run scripts/viking_ingest.py --no-resume --wait
```

This scans all project directories and ingests into OpenViking:
- Project documents (README, REPORT, RESEARCH_PLAN, provenance)
- Figures
- Knowledge graph data (entities, relations, hypotheses, timeline)

Present the summary output to the user (resource count, project count, any errors).

### Rebuild Knowledge Graph

Run:

```bash
uv run scripts/viking_ingest.py --rebuild-graph --wait
```

This runs Phase 1 (resource upload) + Phase 2 (CBORG entity extraction) + Phase 3 (L0/L1 tier generation). Requires `BERIL_CBORG_API_KEY` env var.

To rebuild only the knowledge graph without re-uploading resources:

```bash
uv run scripts/viking_ingest.py --graph-only --wait
```

To use a specific model: `--model claude-haiku` or `--model gpt-5.4-mini`

### Check Status

Run:

```bash
uv run scripts/viking_ingest.py --check
```

This verifies that all expected resources are present in OpenViking without re-ingesting. Reports any missing or stale resources.

## Integration

- **Called by**: `/synthesize` (Step 7.6), `/submit` (Step 2), `/berdl_start` (Phase B)
- **Generates for**: `/knowledge` (query skill), `/suggest-research` (landscape analysis)
- **Source of truth**: OpenViking (all queries go through OpenViking)

## When to Re-ingest

Run a full re-ingest when:
- Multiple projects changed since last ingest
- OpenViking was restarted or rebuilt
- After merging branches that modified multiple projects
- After running `/synthesize` on multiple projects
- When `/knowledge` queries return stale or missing results

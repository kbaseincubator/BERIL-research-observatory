---
name: build-registry
description: Regenerate the knowledge registry (project index, figure catalog, findings digest) from all project files. Use when registry files are missing, stale, or after bulk changes to projects.
allowed-tools: Bash, Read
user-invocable: true
---

# Build Registry Skill

Regenerate the observatory's knowledge registry files from project provenance.yaml and markdown sources.

## Usage

```
/build-registry                  — full rebuild of all registry files
/build-registry <project_id>     — incremental update for one project
```

## Workflow

### Full Rebuild

Run:

```bash
uv run scripts/build_registry.py
```

This scans all project directories and generates:
- `docs/project_registry.yaml` — aggregated project index
- `docs/figure_catalog.yaml` — searchable figure catalog
- `docs/findings_digest.md` — concise findings with links

Present the summary output to the user (project count, figure count, findings count, status breakdown).

### Incremental Update

Run:

```bash
uv run scripts/build_registry.py --project <project_id>
```

This updates only the specified project's entry in the registry while preserving all other entries.

Use this after:
- `/synthesize` completes (report written)
- `/submit` completes (project validated)
- `/berdl_start` creates a new project
- Any manual edits to a project's README.md or REPORT.md

### Dry Run

To preview without writing files:

```bash
uv run scripts/build_registry.py --dry-run
```

## Data Sources

The script uses a two-tier strategy:
1. **Primary**: If `projects/{id}/provenance.yaml` exists, reads structured metadata (references, findings, data sources, cross-project deps)
2. **Fallback**: If no provenance.yaml, parses `README.md` and `REPORT.md` with regex

Projects without a README.md are skipped. The `hackathon_demo` directory is always excluded.

## Output Files

| File | Content | Typical Size |
|------|---------|-------------|
| `docs/project_registry.yaml` | All projects with tags, findings, deps, data artifacts | ~15-20K tokens |
| `docs/figure_catalog.yaml` | All figures with captions, notebooks, tags | ~10-15K tokens |
| `docs/findings_digest.md` | Grep-searchable findings summary with REPORT links | ~5-8K tokens |

## Integration

- **Called by**: `/synthesize` (Step 7.5), `/submit` (Step 2), `/berdl_start` (Phase B)
- **Generates for**: `/knowledge` (query skill), `/suggest-research` (landscape analysis)
- **Source of truth**: provenance.yaml + markdown files (registry is a derived cache)

## When to Rebuild

The registry is always derivable from source files. If it drifts, a full `/build-registry` regenerates everything. Run a full rebuild when:
- Multiple projects changed since last build
- Registry files were deleted or corrupted
- After merging branches that modified multiple projects
- After running `generate_provenance.py` on multiple projects

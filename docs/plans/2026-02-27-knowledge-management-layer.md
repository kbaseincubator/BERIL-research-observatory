# Knowledge Management Layer - Design Document

**Date**: 2026-02-27
**Status**: Implemented
**Branches**: `feature/structured-provenance` (Layer 1+2), `feature/semantic-knowledge-graph` (Layer 3 + workflow improvements)

## Problem

The observatory has 35+ projects with standardized reports, figures, and data artifacts, but no structured index connecting them. Skills like `/suggest-research` must read ALL project READMEs and REPORTs sequentially (~200K+ tokens) to understand the landscape. There's no efficient way to ask "which projects studied defense genes?" or "find figures about pangenome openness" or "what reusable data exists for fitness scores?" without reading everything.

## Solution: Three-Layer Architecture

We chose **structured YAML/markdown index files** over knowledge graphs (Neo4j/Graphiti) or vector databases (FAISS/Chroma). At 41 projects, the overhead of infrastructure far exceeds the benefit. Claude Code already has grep/glob/read tools that work perfectly on structured text. Revisit at 500+ projects.

This aligns with the emerging "context engineering" best practice: structured metadata + intelligent agent retrieval outperforms vector search for curated collections at this scale.

```
Layer 1 (per-project):   provenance.yaml           <- feature/structured-provenance
Layer 2 (global index):  project_registry.yaml      <- feature/structured-provenance
                          figure_catalog.yaml
                          findings_digest.md
Layer 3 (semantic graph): knowledge/                 <- feature/semantic-knowledge-graph
                          docs/knowledge_graph_coverage.md
                          docs/knowledge_gaps.md
```

### Layer 1: Structured Provenance (PR #123)

**Branch**: `feature/structured-provenance`

Per-project `provenance.yaml` sidecar files containing machine-readable metadata extracted from project markdown. Each file includes:

- **References**: Literature citations with DOI/PMID, classified by type (primary_data_source, supporting, contradicting, methodology, review)
- **Data sources**: BERDL collection IDs and tables used, with purpose descriptions
- **Cross-project dependencies**: Which projects depend on which, with relationship types (data_input, extends, contradicts, replicates, synthesizes)
- **Findings**: Key results linked to specific notebooks, figures, data files, and statistical evidence
- **Generated data**: Output files with row counts, descriptions, and source notebooks

**New files**:
- `tools/generate_provenance.py` — Claude API-based generator that reads project markdown and produces provenance.yaml
- `ui/app/models.py` additions — `Reference`, `DataSourceRef`, `CrossProjectDep`, `FindingEvidence`, `GeneratedDataEntry`, `Provenance` data classes
- `ui/app/dataloader.py` additions — `_parse_provenance()`, `_scan_notebook_data_deps()` methods

**Skill updates**:
- `/synthesize` Step 7.5 — Generates provenance.yaml after writing REPORT.md
- `/literature-review` Step 6b — Creates/merges provenance.yaml references
- `/submit` — Advisory validation of provenance.yaml (WARN, never FAIL)

### Layer 2: Knowledge Registry

**Branch**: `feature/structured-provenance` (includes both Layer 1 and Layer 2)

A global aggregation layer that reads all provenance.yaml files (or falls back to markdown parsing) and produces three searchable index files.

**New files**:
- `scripts/build_registry.py` — Registry generator (reads provenance.yaml primary, markdown fallback)
- `docs/project_registry.yaml` — Aggregated index of all projects (~15-20K tokens)
- `docs/figure_catalog.yaml` — Searchable catalog of all figures
- `docs/findings_digest.md` — Concise findings summary with links
- `.claude/skills/knowledge/SKILL.md` — `/knowledge` query skill
- `.claude/skills/build-registry/SKILL.md` — `/build-registry` regeneration skill

**Skill updates**:
- `/suggest-research` Steps 2-3 — Reads registry (~15K tokens) instead of all project files (~200K+ tokens), deep-reads only the top 3-5 relevant projects
- `/synthesize` Step 7.6 — Runs `build_registry.py --project {id}` after generating provenance.yaml
- `/submit` Step 2 — Runs `build_registry.py --project {id}` after validation checks
- `/berdl_start` Step 18b — Registers new projects immediately so they're discoverable

## Data Flow

```
/synthesize  -->  REPORT.md  -->  provenance.yaml  -->  build_registry.py  -->  project_registry.yaml
                                       |                                        figure_catalog.yaml
                                       |                                        findings_digest.md
                                       v                                        knowledge_graph_coverage.md
                                  knowledge/                                    knowledge_gaps.md
                                  (entities, relations,                              |
                                   hypotheses, timeline)                             v
                                       |                                      /knowledge (queries)
                                       +------------------------------------> /suggest-research (landscape)
                                                                              /status (dashboard)
                                                                              /interpret (context)
                                                                              /compare (cross-project)
```

## Synchronization Strategy

| Trigger | Layer 1 (provenance) | Layer 2 (registry) | Layer 3 (graph) |
|---------|---------------------|--------------------|-----------------|
| `/synthesize` | Generates (Step 7.5) | `--project {id}` (Step 7.6) | Required updates (Step 7.7) |
| `/submit` | Validates (advisory) | `--project {id}` | — |
| `/literature-review` | Merges refs (Step 6b) | — | — |
| `/berdl_start` | — | `--project {id}` | — |
| `/build-registry` | — | Full regeneration | Coverage/gap reports |
| `/knowledge backfill` | Reads | — | Retroactive population |
| `generate_provenance.py` | Generates/regenerates | Run `/build-registry` after | — |

The registry is always **derivable from provenance.yaml + markdown files** — if it drifts, `/build-registry` regenerates it completely. Skills treat it as a cache, not the source of truth.

## build_registry.py Design

**Two-tier parsing strategy**:
1. **Primary**: If `projects/{id}/provenance.yaml` exists, read structured data directly
2. **Fallback**: If no provenance.yaml, parse README.md + REPORT.md with regex

**Key capabilities**:
- Status detection handles: `Complete —`, `Completed --`, `In Progress`, `Proposed`
- Tag extraction uses controlled vocabulary (18 bio tags + method tags + auto-detected databases)
- Cross-project dependency detection via provenance.yaml, notebook code scanning (3 regex patterns from dataloader.py), and README Dependencies section
- Bidirectional dependency graph: `depends_on` + `enables` (reverse)
- Incremental updates: `--project <id>` flag for single-project updates
- Skips `hackathon_demo` (no README)
- Strips leading numbers from finding titles

**Current stats** (as of 2026-03-09):
- 41 projects indexed (35 complete, 3 in-progress, 3 proposed)
- 330 figures cataloged
- ~195 findings extracted
- 41 provenance.yaml files (full coverage)
- 80 entities, 32 relations, 20 hypotheses, 43 timeline events (Layer 3)

## Skills

### Querying skills (read-only)

| Skill | Purpose |
|-------|---------|
| `/knowledge <topic>` | Search projects and findings by keyword |
| `/knowledge figures <topic>` | Search figure catalog |
| `/knowledge data <topic>` | Search reusable data artifacts |
| `/knowledge project <id>` | Full summary of a specific project |
| `/knowledge landscape` | Status overview, top tags, collection usage, dependency graph |
| `/knowledge entities <type>` | List entities by type (organism, gene, pathway, method, concept) |
| `/knowledge connections <entity>` | Find all relations for an entity |
| `/knowledge hypotheses [status]` | List hypotheses by lifecycle status |
| `/knowledge gaps` | Unexplored entity combinations and method coverage gaps |
| `/knowledge timeline [project]` | Chronological research events |
| `/knowledge backfill [project_id]` | Retroactively populate Layer 3 from reports |
| `/status` | Dashboard: active work, hypotheses, gaps, recent progress |
| `/interpret [project_id]` | Discuss intermediate results (conversation only, no file writes) |
| `/compare <A> <B>` | Side-by-side comparison of projects, organisms, or entities |

### Workflow skills (read-write)

| Skill | Knowledge layer interaction |
|-------|---------------------------|
| `/synthesize` | Writes Layer 1 + updates Layer 2 + requires Layer 3 updates |
| `/suggest-research` | Reads Layer 2+3 for gap-driven recommendations |
| `/build-registry` | Regenerates Layer 2 and Layer 3 coverage/gap reports |
| `/submit` | Validates Layer 1, updates Layer 2 |

## Merge Strategy

These are **stacked branches**:
1. Merge `feature/structured-provenance` into `main` first (Layer 1+2: provenance model, generator, registry, `/knowledge` skill)
2. Rebase `feature/semantic-knowledge-graph` onto `main`
3. Merge `feature/semantic-knowledge-graph` (Layer 3: knowledge graph, new skills, workflow improvements, all 41 provenance.yaml files)

## Future Considerations

- **Scale threshold**: At 500+ projects, consider graph database or vector search. Current approach works well at 41 projects.
- **Provenance generation**: Currently requires Claude API. Could add a lightweight regex-only mode for CI/CD.
- **UI integration**: The registry YAML files could feed a dashboard page showing the research landscape, dependency graph, and search interface.
- **Automated staleness detection**: `validate_registry_freshness.py` exists; could become a pre-commit hook.
- **Layer 3 backfill**: 24/41 projects need retroactive graph population via `/knowledge backfill`.
- **Graph density**: As more projects are backfilled and new projects use mandatory Layer 3 updates, relation density should increase significantly from the current 32 edges.

## References

- [Anthropic: Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Is RAG Dead? Context Engineering & Semantic Layers](https://towardsdatascience.com/beyond-rag/) — structured metadata > vector search for curated collections
- [Claude Code Memory System](https://code.claude.com/docs/en/memory) — hierarchical memory patterns

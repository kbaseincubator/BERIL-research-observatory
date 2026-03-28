---
name: knowledge
description: "Search the research observatory knowledge base through OpenViking first — projects, findings, figures, reusable data, entities, hypotheses, and cross-project connections. Use when the user wants to find projects by topic, search for figures, locate reusable data, explore the knowledge graph, get a landscape overview, or asks questions like 'what do we know about X', 'have we studied Y', 'which projects involve Z', or 'show me findings on W'."
allowed-tools: Read, Bash, Grep
user-invocable: true
---

# Knowledge Query Skill

Search the observatory's knowledge via OpenViking. OpenViking must be running for all queries.

## Usage

```
/knowledge <topic>              — search projects and findings by keyword
/knowledge figures <topic>      — search figure catalog
/knowledge data <topic>         — search reusable data artifacts
/knowledge project <id>         — full summary of a specific project
/knowledge landscape            — high-level overview of all research
/knowledge entities <type>      — list entities (organism, gene, pathway, method, concept)
/knowledge connections <entity> — find all relations involving an entity
/knowledge hypotheses [status]  — list hypotheses, optionally filtered by status
/knowledge gaps                 — find unexplored entity combinations
/knowledge timeline [project]   — show research evolution
/knowledge backfill [project_id]  — retroactively populate Layer 3 from project reports
/knowledge related <id_or_uri>  — find related resources via metadata + knowledge graph
/knowledge grep <pattern> [--uri <scope>] [--ignore-case]  — content search (requires OpenViking)
/knowledge glob <pattern>                                   — file pattern match (requires OpenViking)
```

## Prerequisites

OpenViking must be running. If any query fails with a connection error, tell the user:

> "OpenViking is not reachable. See `docs/openviking_tutorial.md` for setup."

Then stop.

## Workflow

Run the unified query script for every subcommand:

```bash
uv run scripts/query_knowledge_unified.py <subcommand> ...
```

Map subcommands directly:
- `/knowledge <topic>` → `search "<topic>"`
- `/knowledge <topic> --project <id>` → `search "<topic>" --project <id>`
- `/knowledge figures <topic>` → `figures "<topic>"`
- `/knowledge data <topic>` → `data "<topic>"`
- `/knowledge project <id>` → `project <id>`
- `/knowledge landscape` → `landscape`
- `/knowledge entities <type>` → `entities <type> [--query <keyword>]`
- `/knowledge connections <entity>` → `connections <entity>`
- `/knowledge hypotheses [status]` → `hypotheses [status]`
- `/knowledge gaps` → `gaps`
- `/knowledge timeline [project]` → `timeline [project]`
- `/knowledge backfill [project_id]` → `backfill [project_id]`
- `/knowledge related <id>` → `related <id_or_uri> [--limit N]`
- `/knowledge grep <pattern>` → `grep "<pattern>"`
- `/knowledge grep <pattern> --ignore-case` → `grep "<pattern>" --ignore-case`
- `/knowledge grep <pattern> --uri <scope>` → `grep "<pattern>" --uri <scope>`
- `/knowledge glob <pattern>` → `glob "<pattern>"`

### Subcommand: `/knowledge <topic>`

**Search projects and findings by keyword.**
Run: `uv run scripts/query_knowledge_unified.py search "<topic>"`

Scoped to a project: `uv run scripts/query_knowledge_unified.py search "<topic>" --project <project_id>`

Output format:
```markdown
### Results for "{topic}"

**1. {project_id}** ({status})
- **Q**: {research_question}
- **Findings**: {top 2-3 key findings}
- **Tags**: {tags}
- **Data**: {databases_used}
- [README](projects/{id}/README.md) | [REPORT](projects/{id}/REPORT.md)
```

### Subcommand: `/knowledge figures <topic>`

**Search the figure catalog.**
Run: `uv run scripts/query_knowledge_unified.py figures "<topic>"`

Output: table of matching figures with project, file, and caption. Cap at 20.

### Subcommand: `/knowledge data <topic>`

**Search reusable data artifacts.**
Run: `uv run scripts/query_knowledge_unified.py data "<topic>"`

Output: table of matching artifacts with project, file, description, and reusable flag.

### Subcommand: `/knowledge project <id>`

**Full summary of a specific project.**
Run: `uv run scripts/query_knowledge_unified.py project <id>`

Output: title, status, research question, key findings, tags, data sources, artifacts, dependencies, provenance status.

### Subcommand: `/knowledge landscape`

**High-level overview of all research.**
Run: `uv run scripts/query_knowledge_unified.py landscape`

Output: status counts, top tags, BERDL collections, dependency graph, coverage gaps.

### Subcommand: `/knowledge entities <type>`

**List entities of a given type from the knowledge graph.**
Run: `uv run scripts/query_knowledge_unified.py entities <type> [--query <keyword>]`

Valid types: `organism`, `gene`, `pathway`, `method`, `concept`

Output: table with ID, name, project count, description.

### Subcommand: `/knowledge connections <entity_id>`

**Find all relations involving a specific entity.**
Run: `uv run scripts/query_knowledge_unified.py connections <entity_id>`

Output: outgoing and incoming relation tables with predicate, target/source, evidence project, confidence.

### Subcommand: `/knowledge hypotheses [status]`

**List hypotheses, optionally filtered by lifecycle status.**
Run: `uv run scripts/query_knowledge_unified.py hypotheses [status]`

Valid statuses: `proposed`, `refined`, `testing`, `validated`, `rejected`, `merged`, `superseded`

Output: table with ID, status, statement, origin project, evidence counts.

### Subcommand: `/knowledge gaps`

**Find unexplored entity combinations and research opportunities.**
Run: `uv run scripts/query_knowledge_unified.py gaps`

Output: organisms needing analysis, method coverage gaps, untested hypotheses, unexplored entity pairs.

### Subcommand: `/knowledge timeline [project]`

**Show research evolution chronologically.**
Run: `uv run scripts/query_knowledge_unified.py timeline [project]`

Output: table with date, type, project, summary.

### Subcommand: `/knowledge backfill [project_id]`

**Retroactively populate Layer 3 from project reports.**

1. If `project_id` is given: target that project. If omitted: run `uv run scripts/query_knowledge_unified.py backfill` to list projects missing graph coverage, then ask the user which to process.
2. Read `projects/{id}/REPORT.md` and `projects/{id}/provenance.yaml` (if exists)
3. Extract entities, relations, hypotheses, and timeline events following `/synthesize` Step 7.7 logic (a)-(e)
4. Present proposed additions to the user for confirmation before writing

### Subcommand: `/knowledge related <id_or_uri>`

**Find related resources via metadata overlap and knowledge graph connections.**
Run: `uv run scripts/query_knowledge_unified.py related <id_or_uri> [--limit N]`

Output: list of related resources ranked by metadata overlap, link connections, and graph proximity.

### Subcommand: `/knowledge grep <pattern>`

**Search inside resource content for a text pattern (requires OpenViking).**
Run: `uv run scripts/query_knowledge_unified.py grep "<pattern>" [--uri <scope>] [--ignore-case]`

Requires a live OpenViking server. If the server is not running, tell the user:

> "grep requires a live OpenViking server. See `docs/openviking_tutorial.md` for setup."

Output: matches grouped by resource URI with line numbers.

### Subcommand: `/knowledge glob <pattern>`

**Find resources by file pattern (requires OpenViking).**
Run: `uv run scripts/query_knowledge_unified.py glob "<pattern>"`

Requires a live OpenViking server. If the server is not running, tell the user:

> "glob requires a live OpenViking server. See `docs/openviking_tutorial.md` for setup."

Output: list of matching resource URIs with total count.

## Integration

- **Query backend**: `scripts/query_knowledge_unified.py` (requires OpenViking)
- **Data source**: OpenViking (single source of truth for all observatory knowledge)
- **Re-ingested by**: `/build-registry` (re-ingests all resources into OpenViking)
- **Consumed by**: agents and users exploring the research landscape
- **Related skills**: `/suggest-research` (landscape analysis), `/build-registry` (re-ingest), `/synthesize` (updates knowledge after project completion)

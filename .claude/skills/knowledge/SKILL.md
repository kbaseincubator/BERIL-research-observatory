---
name: knowledge
description: "Search the research observatory knowledge base — projects, findings, figures, reusable data, entities, hypotheses, and cross-project connections. Use when the user wants to find projects by topic, search for figures, locate reusable data, explore the knowledge graph, get a landscape overview, or asks questions like 'what do we know about X', 'have we studied Y', 'which projects involve Z', or 'show me findings on W'."
allowed-tools: Read, Bash, Grep
user-invocable: true
---

# Knowledge Query Skill

Search the observatory's knowledge registry and semantic knowledge graph to find projects, findings, figures, reusable data, entities, relationships, and hypotheses.

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
```

## Prerequisite

This skill reads from the auto-generated registry files in `docs/`:
- `docs/project_registry.yaml` — aggregated index of all projects
- `docs/figure_catalog.yaml` — searchable catalog of all figures
- `docs/findings_digest.md` — concise summary of key findings with links
- `docs/knowledge_graph_coverage.md` — Layer 3 graph coverage report
- `docs/knowledge_gaps.md` — deterministic graph-derived research opportunities

If these files do not exist, tell the user:

> "The knowledge registry hasn't been generated yet. Run `/build-registry` to create it."

Then stop.

### Freshness Check
Run: `uv run scripts/validate_registry_freshness.py`
If exit code 1 (stale), warn: "The knowledge registry may be out of date.
Run `/build-registry` to refresh, or proceed with current data."
Proceed regardless — stale data is better than no data.

## Workflow

Use the deterministic backend for every subcommand:

```bash
uv run scripts/query_knowledge.py <subcommand> ...
```

Map subcommands directly:
- `/knowledge <topic>` → `search <topic>`
- `/knowledge figures <topic>` → `figures <topic>`
- `/knowledge data <topic>` → `data <topic>`
- `/knowledge project <id>` → `project <id>`
- `/knowledge landscape` → `landscape`
- `/knowledge entities <type>` → `entities <type> [--query <keyword>]`
- `/knowledge connections <entity>` → `connections <entity>`
- `/knowledge hypotheses [status]` → `hypotheses [status]`
- `/knowledge gaps` → `gaps`
- `/knowledge timeline [project]` → `timeline [project]`

### Subcommand: `/knowledge <topic>`

**Search projects and findings by keyword.**
Run: `uv run scripts/query_knowledge.py search "<topic>"`

1. Read `docs/project_registry.yaml`
2. Search across all project entries for matches in: `title`, `research_question`, `key_findings`, `tags`, `organisms`, `databases_used`
3. Rank results by relevance — prioritize:
   - Direct tag match (highest)
   - Keyword in research question or title
   - Keyword in key findings
   - Keyword in organisms or databases
4. For the top 3-5 matches, present:

```markdown
### Results for "{topic}"

**1. {project_id}** ({status})
- **Q**: {research_question}
- **Findings**: {top 2-3 key findings}
- **Tags**: {tags}
- **Data**: {databases_used}
- [README](projects/{id}/README.md) | [REPORT](projects/{id}/REPORT.md)

**2. {project_id}** ({status})
...
```

5. If the topic matches entries in `docs/findings_digest.md`, also list relevant individual findings with links.

### Subcommand: `/knowledge figures <topic>`

**Search the figure catalog.**
Run: `uv run scripts/query_knowledge.py figures "<topic>"`

1. Read `docs/figure_catalog.yaml`
2. Search `caption`, `tags`, `file` name, and `project` for keyword matches
3. Present matching figures:

```markdown
### Figures matching "{topic}"

| Project | Figure | Caption |
|---------|--------|---------|
| {project} | [{file}](projects/{project}/figures/{file}) | {caption} |
```

4. Group by project if many results. Cap at 20 figures.

### Subcommand: `/knowledge data <topic>`

**Search reusable data artifacts.**
Run: `uv run scripts/query_knowledge.py data "<topic>"`

1. Read `docs/project_registry.yaml`
2. Search `key_data_artifacts` across all projects for matches in `file` name or `description`
3. Also match against project tags and research questions for topical relevance
4. Present:

```markdown
### Data artifacts matching "{topic}"

| Project | File | Description |
|---------|------|-------------|
| {project_id} | `{file}` | {description} |
```

5. Note which artifacts have `reusable: true`.

### Subcommand: `/knowledge project <id>`

**Full summary of a specific project.**
Run: `uv run scripts/query_knowledge.py project <id>`

1. Read `docs/project_registry.yaml` and find the project by ID
2. If not found, suggest close matches or list all project IDs
3. Present all fields:

```markdown
## {title}
**Status**: {status} | **Date**: {date_completed}
**Research Question**: {research_question}

### Key Findings
1. {finding 1}
2. {finding 2}
...

### Tags
{tags}

### Data Sources
{databases_used}

### Data Artifacts
| File | Description |
|------|-------------|
| {file} | {description} |

### Dependencies
- **Depends on**: {depends_on}
- **Enables**: {enables}

### References
| ID | Title | DOI |
|----|-------|-----|
| {id} | {title} | {doi} |

**Provenance**: {"Available" if has_provenance else "Not yet generated"}
```

4. If `has_provenance` is true, suggest: "Run `cat projects/{id}/provenance.yaml` for detailed structured metadata."

### Subcommand: `/knowledge landscape`

**High-level overview of all research.**
Run: `uv run scripts/query_knowledge.py landscape`

1. Read `docs/project_registry.yaml`
2. Compute and present:

```markdown
## Research Landscape

### Status
| Status | Count |
|--------|-------|
| complete | {n} |
| in-progress | {n} |
| proposed | {n} |

### Top Tags (by project count)
| Tag | Projects |
|-----|----------|
| {tag} | {count} |

### BERDL Collections Used
| Collection | Projects |
|------------|----------|
| {collection} | {count} |

### Dependency Graph
Projects with most downstream dependents:
- {project}: enables {n} projects ({list})

Projects with most upstream dependencies:
- {project}: depends on {n} projects ({list})

### Coverage Gaps
- Collections not yet used: {list}
- Tags with only 1 project: {list}
```

3. If the user asks follow-up questions, drill into specific areas.

### Subcommand: `/knowledge entities <type>`

**List entities of a given type from the knowledge graph.**
Run: `uv run scripts/query_knowledge.py entities <type> [--query <keyword>]`

Valid types: `organism`, `gene`, `pathway`, `method`, `concept`

1. Read the corresponding file from `knowledge/entities/`:
   - `organism` → `knowledge/entities/organisms.yaml`
   - `gene` → `knowledge/entities/genes.yaml`
   - `pathway` → `knowledge/entities/pathways.yaml`
   - `method` → `knowledge/entities/methods.yaml`
   - `concept` → `knowledge/entities/concepts.yaml`
2. Present a summary table:

```markdown
### {Type} Entities ({count} total)

| ID | Name | Projects | Description |
|----|------|----------|-------------|
| {id} | {name} | {project_count} projects | {description (truncated)} |
```

3. If a topic is also provided (`/knowledge entities organism metal`), filter to entities whose name, description, or project list matches the keyword.

### Subcommand: `/knowledge connections <entity_id>`

**Find all relations involving a specific entity.**
Run: `uv run scripts/query_knowledge.py connections <entity_id>`

1. Read `knowledge/relations.yaml`
2. Filter relations where `subject` or `object` matches the entity ID (or a substring match on entity name)
3. Present:

```markdown
### Connections for {entity_name} ({entity_id})

**Outgoing relations (this entity → other):**
| Predicate | Target | Evidence Project | Confidence | Note |
|-----------|--------|-----------------|------------|------|
| {predicate} | {object} | {evidence_project} | {confidence} | {note} |

**Incoming relations (other → this entity):**
| Source | Predicate | Evidence Project | Confidence | Note |
|--------|-----------|-----------------|------------|------|
| {subject} | {predicate} | {evidence_project} | {confidence} | {note} |
```

4. Also check `knowledge/hypotheses.yaml` for hypotheses that reference this entity in their `entities` list. List any matching hypotheses.

### Subcommand: `/knowledge hypotheses [status]`

**List hypotheses, optionally filtered by lifecycle status.**
Run: `uv run scripts/query_knowledge.py hypotheses [status]`

Valid statuses: `proposed`, `refined`, `testing`, `validated`, `rejected`, `merged`, `superseded`

1. Read `knowledge/hypotheses.yaml`
2. If a status filter is given, show only matching hypotheses
3. Present:

```markdown
### Hypotheses ({status filter or "all"})

| ID | Status | Statement | Origin Project | Evidence |
|----|--------|-----------|---------------|----------|
| {id} | {status} | {statement (truncated to 80 chars)} | {origin_project} | {n} supporting, {n} contradicting |
```

4. For detailed view, user can ask about a specific hypothesis ID to see full statement, all evidence, evolution timeline, and parent/child relationships.

### Subcommand: `/knowledge gaps`

**Find unexplored entity combinations and research opportunities.**
Run: `uv run scripts/query_knowledge.py gaps`

1. Read all entity files and `knowledge/relations.yaml`
2. Build an entity-entity co-occurrence matrix from relations
3. Identify:

   **a) Organisms with data but no cross-project analysis:**
   - Find organisms that appear in only 1 project but have RB-TnSeq data
   - These are candidates for cross-organism comparison

   **b) Methods applied to some organisms but not others:**
   - Cross-reference method-organism pairs to find gaps
   - E.g., "ICA applied to 32 organisms but GapMind only to 7"

   **c) Hypotheses in "testing" or "proposed" state:**
   - These are untested hypotheses needing validation

   **d) Entity pairs not yet studied together:**
   - Find pairs of organisms, or organism-pathway pairs, that appear in separate projects but have no relation connecting them

4. Present:

```markdown
### Research Gaps

#### Organisms Needing Cross-Project Analysis
| Organism | Current Projects | Suggested Analysis |
|----------|-----------------|-------------------|
| {name} | {projects} | {suggestion} |

#### Method Coverage Gaps
| Method | Applied To | Not Yet Applied To |
|--------|-----------|-------------------|
| {method} | {organisms/entities} | {missing organisms/entities} |

#### Untested Hypotheses
| ID | Statement | Status | Blocking |
|----|-----------|--------|----------|
| {id} | {statement} | {status} | {what's needed} |

#### Unexplored Entity Pairs
| Entity A | Entity B | Why Interesting |
|----------|----------|----------------|
| {entity_a} | {entity_b} | {rationale} |
```

### Subcommand: `/knowledge timeline [project]`

**Show research evolution chronologically.**
Run: `uv run scripts/query_knowledge.py timeline [project]`

1. Read `knowledge/timeline.yaml`
2. If a project filter is given, show only events for that project
3. Present chronologically:

```markdown
### Research Timeline {("for " + project) if filtered}

| Date | Type | Project | Summary |
|------|------|---------|---------|
| {date} | {type} | {project} | {summary} |
```

4. Highlight hypothesis state changes and cross-project connections
5. If no filter, group by month for readability

### Subcommand: `/knowledge backfill [project_id]`

**Retroactively populate Layer 3 from project reports.**

This is an LLM-driven workflow (not a deterministic script for the full extraction).

1. If `project_id` is given: target that project. If omitted: run `uv run scripts/query_knowledge.py backfill` to list projects missing graph coverage, then ask the user which to process.
2. Read `projects/{id}/REPORT.md` and `projects/{id}/provenance.yaml` (if exists)
3. Extract entities, relations, hypotheses, and timeline events following `/synthesize` Step 7.7 logic (a)-(e)
4. Present proposed additions to the user in a structured diff:
   ```
   ### Proposed Knowledge Graph Additions for {project_id}
   **New entities**: {list}
   **New relations**: {list}
   **New hypotheses**: {list}
   **Timeline events**: {list}
   ```
5. On user confirmation, write to `knowledge/` files
6. Run `uv run scripts/build_registry.py --project {project_id}` to update coverage report

## Integration

- **Reads from**: `docs/project_registry.yaml`, `docs/figure_catalog.yaml`, `docs/findings_digest.md`, `docs/knowledge_graph_coverage.md`, `docs/knowledge_gaps.md`, `knowledge/entities/*.yaml`, `knowledge/relations.yaml`, `knowledge/hypotheses.yaml`, `knowledge/timeline.yaml`
- **Deterministic backend**: `scripts/query_knowledge.py`
- **Regenerated by**: `/build-registry` (Layer 2), `/synthesize` (Layer 3 updates)
- **Consumed by**: agents and users exploring the research landscape
- **Related skills**: `/suggest-research` (uses registry and knowledge graph for landscape analysis), `/build-registry` (regenerates the Layer 2 index), `/synthesize` (updates Layer 3 after project completion)

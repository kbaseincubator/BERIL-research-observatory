---
name: knowledge
description: Search the research observatory knowledge base — projects, findings, figures, and reusable data artifacts. Use when the user wants to find projects by topic, search for figures, locate reusable data, or get a landscape overview.
allowed-tools: Read, Bash, Grep
user-invocable: true
---

# Knowledge Query Skill

Search the observatory's knowledge registry to find projects, findings, figures, and reusable data artifacts without reading every project file.

## Usage

```
/knowledge <topic>              — search projects and findings by keyword
/knowledge figures <topic>      — search figure catalog
/knowledge data <topic>         — search reusable data artifacts
/knowledge project <id>         — full summary of a specific project
/knowledge landscape            — high-level overview of all research
```

## Prerequisite

This skill reads from the auto-generated registry files in `docs/`:
- `docs/project_registry.yaml` — aggregated index of all projects
- `docs/figure_catalog.yaml` — searchable catalog of all figures
- `docs/findings_digest.md` — concise summary of key findings with links

If these files do not exist, tell the user:

> "The knowledge registry hasn't been generated yet. Run `/build-registry` to create it."

Then stop.

## Workflow

### Subcommand: `/knowledge <topic>`

**Search projects and findings by keyword.**

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

## Integration

- **Reads from**: `docs/project_registry.yaml`, `docs/figure_catalog.yaml`, `docs/findings_digest.md`
- **Regenerated by**: `/build-registry`
- **Consumed by**: agents and users exploring the research landscape
- **Related skills**: `/suggest-research` (uses registry for landscape analysis), `/build-registry` (regenerates the index)

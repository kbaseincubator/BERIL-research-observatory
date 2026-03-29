---
name: compare
description: "Compare findings, data, or methods across projects or organisms. Use when the user wants to see how results differ, compare organisms, find cross-project patterns, or asks 'how does X compare to Y'."
allowed-tools: Read, Bash
user-invocable: true
---

# Compare Skill

Compare two projects, organisms, or entities side-by-side to identify shared patterns, differences, and research opportunities.

## Usage

```
/compare <A> <B>
```

Where `<A>` and `<B>` are project IDs, organism entity IDs, or other entity IDs.

## Workflow

### Step 1: Determine Comparison Type

Check if the arguments match:
1. **Project IDs**: Run `uv run scripts/query_knowledge_unified.py project <id>` for each
2. **Entity IDs**: Run `uv run scripts/query_knowledge_unified.py entities <type>` to look up entities (check organism, then gene, pathway, method, concept)
3. **Entity names**: If not exact ID matches, search entities for name matches

If one arg matches a project and the other an entity, tell the user and ask for clarification.

### Step 2a: Project Comparison

If both arguments are project IDs:

1. Run `uv run scripts/query_knowledge_unified.py project <id>` for each project
2. Compare:

| Dimension | Project A | Project B |
|-----------|-----------|-----------|
| Status | {status} | {status} |
| Research Question | {question} | {question} |
| Organisms | {organisms} | {organisms} |
| Tags | {tags} | {tags} |
| Databases Used | {databases} | {databases} |
| Key Findings | {findings} | {findings} |

3. Identify shared elements:
   - Common organisms studied
   - Common databases used
   - Overlapping tags/themes
   - Cross-project dependencies (from `depends_on`/`enables`)

4. Run `uv run scripts/query_knowledge_unified.py traverse <shared_entity_uri> --hops 2` for any shared entities to find relation paths between the projects. Also run `uv run scripts/query_knowledge_unified.py recall "comparison patterns" --store patterns` for learned comparison heuristics

5. Highlight gaps: methods applied in A but not B, organisms in A but not B

### Step 2b: Organism Comparison

If both arguments are organism entity IDs:

1. Run for each organism:
   ```bash
   uv run scripts/query_knowledge_unified.py traverse <org_entity_uri> --hops 2
   ```
2. Run `uv run scripts/query_knowledge_unified.py entities organism --query <name>` for each organism
3. Compare:

| Dimension | Organism A | Organism B |
|-----------|-----------|-----------|
| Name | {name} | {name} |
| Projects | {projects} | {projects} |
| Methods Applied | {from relations} | {from relations} |
| Hypotheses | {related hypotheses} | {related hypotheses} |
| Pathways | {connected pathways} | {connected pathways} |

4. Highlight:
   - Methods applied to A but not B (gap opportunities)
   - Shared projects where both appear
   - Hypotheses that reference one but not the other

### Step 2c: General Entity Comparison

For other entity types (methods, pathways, concepts):

1. Run `uv run scripts/query_knowledge_unified.py entities <type>` to look up each entity
2. Run `uv run scripts/query_knowledge_unified.py connections <entity_id>` for each entity
3. Compare project coverage, connected entities, and relation types
4. Present a side-by-side summary

### Step 3: Present Comparison

Present a clear, structured comparison with:
1. **Side-by-side table** of key attributes
2. **Shared elements** — what they have in common
3. **Unique to A** — what only A has
4. **Unique to B** — what only B has
5. **Research opportunities** — gaps suggested by the comparison (e.g., "Method X was applied to Organism A but not B")

### Step 4: Suggest Follow-ups

Based on the comparison, suggest:
- `/knowledge gaps` if significant coverage gaps were found
- `/suggest-research` if the comparison reveals a promising new direction
- Specific `/knowledge connections <entity>` queries for deeper exploration

## Integration

- **Reads from**: OpenViking (via `scripts/query_knowledge_unified.py`)
- **Query backend**: `scripts/query_knowledge_unified.py` (all subcommands)
- **Consumed by**: users exploring cross-project patterns
- **Related skills**: `/knowledge` (deeper exploration), `/suggest-research` (gap-driven recommendations)

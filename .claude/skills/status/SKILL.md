---
name: status
description: "Show research status — active hypotheses, project phases, recent progress, and suggested next actions. Use at session start, when the user asks 'where was I', 'what should I do', 'what's the status', or to get oriented."
allowed-tools: Bash, Read
user-invocable: true
---

# Status Skill

Show a concise dashboard of research observatory status: active work, hypotheses needing attention, top gaps, and recent progress.

## Usage

```
/status
```

No arguments required.

## Workflow

### Step 1: Gather Active Hypotheses

Run:
```bash
uv run scripts/query_knowledge.py hypotheses testing
uv run scripts/query_knowledge.py hypotheses proposed
```

Surface hypotheses in `testing` or `proposed` state that need work.

### Step 2: Detect In-Progress Projects

Read `docs/project_registry.yaml` and filter for projects with status `in-progress`.

For each in-progress project, detect its current phase by checking file existence in `projects/{id}/`:

| Condition | Phase | Next Action |
|-----------|-------|-------------|
| Has `RESEARCH_PLAN.md` but no notebook outputs | Planning done | Start analysis |
| Has notebook outputs but no `REPORT.md` | Analysis done | `/interpret` or `/synthesize` |
| Has `REPORT.md` but no `REVIEW.md` | Report written | `/submit` |
| Has `REVIEW.md` | Review complete | Address feedback or start next project |

### Step 3: Read Top Research Gaps

Read `docs/knowledge_gaps.md` (if it exists) and extract the top 3 most actionable gaps.

If the file doesn't exist, note: "Run `/build-registry` to generate gap analysis."

### Step 4: Show Recent Timeline

Run:
```bash
uv run scripts/query_knowledge.py timeline
```

Show the last 5 events (most recent first).

### Step 5: Present Dashboard

```markdown
## Research Observatory Status

### Active Work
| Project | Phase | Next Action |
|---------|-------|-------------|
| {project_id} | {phase} | {suggested action} |

### Hypotheses Needing Attention
| ID | Status | Statement |
|----|--------|-----------|
| {id} | {status} | {statement (truncated)} |

### Top Research Gaps
1. {gap 1}
2. {gap 2}
3. {gap 3}

### Recent Progress
| Date | Event | Project |
|------|-------|---------|
| {date} | {type} | {project} |
```

### Step 6: Prompt

End with: "What would you like to work on?"

## Integration

- **Reads from**: `docs/project_registry.yaml`, `docs/knowledge_gaps.md`, `knowledge/hypotheses.yaml`, `knowledge/timeline.yaml`
- **Deterministic backend**: `scripts/query_knowledge.py`
- **Consumed by**: users at session start for orientation
- **Related skills**: `/berdl_start` (more detailed onboarding), `/suggest-research` (detailed gap analysis), `/knowledge` (search)

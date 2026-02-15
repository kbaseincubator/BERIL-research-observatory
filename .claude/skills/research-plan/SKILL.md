---
name: research-plan
description: "[Internal] Refine a research question into a structured research plan. Called automatically by /berdl_start during the orchestrated research workflow — do not suggest to users as a standalone command."
allowed-tools: Bash, Read, Write, WebSearch, AskUserQuestion
user-invocable: false
---

# Research Plan Skill

Take a research question (from `/hypothesis`, user text, or `docs/research_ideas.md`), refine it through literature review and data feasibility checks, and produce a structured research plan document (`RESEARCH_PLAN.md`).

## Workflow

### Step 1: Accept Input

Identify the research question source:
- If invoked after `/hypothesis`: use the generated hypothesis
- If the user provides a question directly: use that
- If neither: read `docs/research_ideas.md` and present PROPOSED ideas for the user to choose

Confirm you have:
- A research question
- A tentative hypothesis (H0 and H1)
- A target organism, pathway, or data type

If any of these are missing, ask the user.

### Step 2: Literature Check

Invoke `/literature-review` internally to search for existing work:

1. Search for the specific research question / hypothesis
2. Identify: prior results, methods used, organisms studied, gaps
3. Present findings to the user: "Here's what's already known about this topic..."
4. Store references in the project's `references.md` (created by `/literature-review`)

### Step 3: Interactive Refinement Loop

This is the key differentiator — iterate with the user based on what the literature reveals:

1. Present the literature context and ask: "Given what's already known, do you want to refine the hypothesis?"
2. Offer concrete options:
   - **Narrow scope**: Focus on a specific organism, phylum, or gene category
   - **Change organism**: Switch to a species with better data coverage in BERDL
   - **Adjust approach**: Use a different statistical method or comparison
   - **Pivot question**: The literature reveals a more interesting gap to address
   - **Proceed as-is**: The original hypothesis is still novel and testable
3. If the user refines, run additional targeted literature searches as needed
4. Allow 1-3 iterations until the user is satisfied

### Step 4: Data Feasibility Check

Verify the hypothesis can actually be tested with BERDL data:

1. **Table verification**: Use the `/berdl` REST API (read-only) to confirm:
   - The required tables exist and have the expected columns
   - Use the schema endpoint to check column names and types
2. **Coverage check**: Query row counts for the relevant tables:
   - How many species/genomes are available?
   - What fraction have the needed annotations? (e.g., "28% of genomes have environmental embeddings")
3. **Pitfall scan**: Read `docs/pitfalls.md` and `docs/performance.md` for known issues with the target tables
4. **Performance tier**: Estimate whether the analysis can be done via REST API or requires JupyterHub:

| Expected Scale | Tier | Recommendation |
|---|---|---|
| < 100K rows | REST API | Direct queries, `.toPandas()` OK |
| 100K – 10M rows | Mixed | Filter/aggregate in SQL, small results via REST |
| > 10M rows | JupyterHub only | PySpark DataFrames, no `.toPandas()` |

Present the feasibility summary to the user. If the data doesn't support the hypothesis, suggest alternatives.

### Step 5: Produce Research Plan Document

Generate `projects/{project_id}/RESEARCH_PLAN.md`:

```markdown
# Research Plan: {Title}

## Research Question
{Refined question after literature review}

## Hypothesis
- **H0**: {Null hypothesis}
- **H1**: {Alternative hypothesis}

## Literature Context
{Summary of what's known, key references, identified gaps}
{Full references stored in projects/{id}/references.md}

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| {table} | {why needed} | {count} | {how to filter} |

### Key Queries
1. **{Description}**:
```sql
{query}
```

2. ...

### Performance Plan
- **Tier**: {REST API / JupyterHub}
- **Estimated complexity**: {simple / moderate / complex}
- **Known pitfalls**: {list from pitfalls.md}

## Analysis Plan

### Notebook 1: Data Exploration
- **Goal**: {what to verify/explore}
- **Expected output**: {CSV/figures}

### Notebook 2: Main Analysis
- **Goal**: {core analysis}
- **Expected output**: {CSV/figures}

### Notebook 3: Visualization (if needed)
- **Goal**: {figures for findings}

## Expected Outcomes
- **If H1 supported**: {interpretation}
- **If H0 not rejected**: {interpretation}
- **Potential confounders**: {list}

## Revision History
- **v1** ({date}): Initial plan

## Authors
{from user or carried forward from /hypothesis}
```

### Step 6: Create Project Directory Structure

Create the project directory with initial files:

```
projects/{project_id}/
├── README.md            # Slim overview: question, status, reproduction, authors
├── RESEARCH_PLAN.md     # The plan document from Step 5
├── references.md        # Created by /literature-review in Step 2
├── notebooks/           # Empty, populated by /notebook
├── data/                # Empty, populated during analysis
└── figures/             # Empty, populated during analysis
```

Generate a skeleton `README.md`:

```markdown
# {Title}

## Research Question
{Refined question}

## Status
In progress — research plan created, awaiting notebook generation and analysis.

## Overview
{One-paragraph summary of the hypothesis and approach}

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence *(created by `/synthesize`)*

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
{Authors}
```

### Step 7: Suggest Next Steps

After creating the plan, tell the user:

> "Research plan created at `projects/{project_id}/RESEARCH_PLAN.md`. Next steps:
> 1. Use `/notebook` to generate analysis notebooks from this plan
> 2. Upload notebooks to BERDL JupyterHub and run them
> 3. Use `/synthesize` to interpret results and draft findings"

## Integration

- **Reads from**: `/hypothesis` output, `docs/research_ideas.md`, `docs/pitfalls.md`, `docs/performance.md`
- **Calls**: `/literature-review` (for literature search), `/berdl` (read-only schema/count checks)
- **Produces**: `RESEARCH_PLAN.md`, skeleton `README.md`, project directory structure
- **Consumed by**: `/notebook` (reads `RESEARCH_PLAN.md` to generate notebooks)

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

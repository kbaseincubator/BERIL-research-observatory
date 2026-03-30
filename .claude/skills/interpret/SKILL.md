---
name: interpret
description: "Discuss intermediate analysis results — help interpret statistics, identify patterns, check against hypotheses, and suggest next analysis steps. Use when notebooks have partial results and the user wants to think about them before full synthesis, or asks 'what does this mean', 'is this significant', or 'what should I analyze next'."
allowed-tools: Read, Bash, AskUserQuestion
user-invocable: true
---

# Interpret Skill

Help the user think through intermediate analysis results before formal synthesis. This is a conversational skill — it reads data and notebooks, interprets patterns, checks against hypotheses, and suggests next steps, but does NOT write any files.

## Usage

```
/interpret [project_id]
```

If no `project_id` argument is provided, detect from the current working directory (if inside `projects/{id}/`).

## Workflow

### Step 1: Gather Project Context

1. Detect the project from cwd or the argument
2. Read `projects/{project_id}/RESEARCH_PLAN.md` for:
   - The hypothesis (H0/H1)
   - Expected outcomes
   - Analysis plan

### Step 2: Read Available Results

1. Scan `projects/{project_id}/data/*.csv` — read the most recently modified files
   - Summarize: column names, row counts, basic statistics
   - Identify key result variables
2. List `projects/{project_id}/figures/` — note available visualizations
3. Read recent notebook outputs in `projects/{project_id}/notebooks/`:
   - Focus on output cells: printed summaries, DataFrames, statistical test results
   - Note any error cells or incomplete analyses

### Step 3: Check Knowledge Graph Context and Memory

Run `uv run scripts/query_knowledge_unified.py search "<project topic>" --with-memory` to get related findings blended with past insights.

Also run `uv run scripts/query_knowledge_unified.py recall "<topic>" --store conversations` to check for past observations ("we saw this before" déjà vu detection).

Run `uv run scripts/query_knowledge_unified.py hypotheses` and find hypotheses related to this project:
- Hypotheses originated by this project
- Hypotheses from other projects that share entities/organisms

### Step 4: Present Interpretation

Structure the interpretation as:

#### Key Observations
- List specific numbers, correlations, and patterns from the data
- Note sample sizes and coverage

#### Hypothesis Check
- Does the data support H1 or fail to reject H0?
- What is the strength of evidence so far?
- Are there confounders or alternative explanations?

#### Unexpected Patterns
- Anything surprising or anomalous in the data
- Patterns that weren't part of the original hypothesis

#### Knowledge Graph Context
- Related findings from other projects (if available)
- How this fits into the broader research landscape

#### Suggested Next Steps
- Additional analyses that could strengthen the findings
- Missing data or coverage gaps to address
- Statistical tests to run
- Figures to generate

### Step 5: Discuss with User

Ask the user:
- "Does this interpretation make sense?"
- "Are there patterns I missed?"
- "Would you like to explore any of these further?"

Iterate based on feedback. This is a conversation, not a one-shot output.

### Step 6: Suggest Transition

When the user is satisfied with the interpretation:

> "When you're ready to write up these findings formally, use `/synthesize {project_id}`."

## Important

- **Do NOT write any files.** This skill is conversation-only.
- **Do NOT generate REPORT.md.** That's what `/synthesize` does.
- Focus on helping the user think, not on producing artifacts.

## Integration

- **Reads from**: `projects/{id}/RESEARCH_PLAN.md`, `projects/{id}/data/*.csv`, `projects/{id}/notebooks/*.ipynb`, `projects/{id}/figures/`, OpenViking (hypotheses via `scripts/query_knowledge_unified.py`)
- **Produces**: Conversational interpretation only (no files)
- **Leads to**: `/synthesize` (when user is ready for formal writeup)
- **Related skills**: `/synthesize` (formal writeup), `/knowledge` (search for related findings)

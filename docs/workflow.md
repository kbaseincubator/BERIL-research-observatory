# Research Workflow

**Purpose**: Step-by-step guide to conducting a research project using the BERIL Research Observatory, from hypothesis generation through peer review.

See [overview.md](overview.md) for the data architecture and [collections.md](collections.md) for the database inventory.

---

## Overview

The research workflow is orchestrated by `/berdl_start`. When you choose "Start a new research project", the agent drives the entire process — from ideation through review — checking in with you at natural decision points.

```
/berdl_start
  ├── Orientation & Ideation    (read docs, explore data, develop hypotheses)
  ├── Research Plan             (write RESEARCH_PLAN.md, README.md, create project)
  ├── Analysis                  (generate & run notebooks, iterate)
  ├── Synthesis                 (interpret results → REPORT.md via /synthesize)
  └── Review & Submission       (validate & review via /submit)
```

You can also enter at any point. If you already have results, jump straight to `/synthesize`. If you have a complete project, use `/submit` for review.

---

## Skills Reference

### User-Invocable Skills

| Skill | Purpose | Key Inputs | Key Outputs |
|-------|---------|------------|-------------|
| `/berdl_start` | Orchestrate a full research project or get oriented | Research interest | Complete project (plan, notebooks, report, review) |
| `/berdl` | Query BERDL databases via REST API | SQL query or natural-language question | Query results, schema info, data samples |
| `/berdl-discover` | Explore and document a new BERDL database | Database name | Module file in `.claude/skills/berdl/modules/`, documentation |
| `/literature-review` | Search PubMed, Europe PMC, CORE, OpenAlex | Research topic or question | Literature summary, `references.md` |
| `/synthesize` | Interpret results and draft findings | Project ID, notebook outputs (CSV, figures) | `REPORT.md` with findings, literature context, limitations |
| `/submit` | Validate documentation and request automated review | Project ID, complete project directory | Pre-submission checklist, `REVIEW.md` |
| `/cts` | Run batch compute jobs on the CTS cluster | Job configuration | Compute results |

Hypothesis generation, research planning, and notebook creation are handled automatically by `/berdl_start` as part of the orchestrated workflow. The `pitfall-capture` protocol runs automatically when errors or data surprises occur.

---

## Orchestrated Workflow (via `/berdl_start`)

### Phase A: Orientation & Ideation

The agent reads the core documentation (`PROJECT.md`, `docs/overview.md`, `docs/collections.md`, `docs/pitfalls.md`, `docs/performance.md`, `docs/research_ideas.md`), checks the environment (auth token, gh CLI), and engages with you about your research interest.

**What happens**:
- Explores relevant BERDL tables and their row counts
- Checks existing projects to avoid duplicating work
- Proposes 2-3 testable hypotheses with null and alternative formulations
- Searches literature for context
- Identifies potential confounders and data limitations

### Phase B: Research Plan

The agent writes a structured research plan and scaffolds the project directory.

**Files produced**:

| File | Description |
|------|-------------|
| `projects/{id}/RESEARCH_PLAN.md` | Full plan: question, hypothesis, lit context, query strategy, analysis plan, revision history |
| `projects/{id}/README.md` | Slim README: question, status, overview, reproduction, authors |
| `projects/{id}/notebooks/` | Empty directory for notebooks |
| `projects/{id}/data/` | Empty directory for output data |
| `projects/{id}/figures/` | Empty directory for visualizations |

**Best practices**: The agent suggests naming the session to match the project ID, creates a `projects/{id}` branch by default, and commits the initial files before proceeding. (If you prefer to stay on main, you can opt out.)

### Phase C: Analysis (Notebooks)

The agent generates numbered notebooks (`01_data_exploration.ipynb`, `02_analysis.ipynb`, etc.) with PySpark boilerplate, SQL queries, and visualization scaffolding, then runs them.

**What happens**:
- Notebooks follow safety rules from `docs/pitfalls.md` and query patterns
- Includes NULL checks, row counts, and data-quality validation cells
- Updates `RESEARCH_PLAN.md` with revision tags when the approach changes
- Commits after each major milestone

### Phase D: Synthesis & Writeup

The agent discusses results with you, then runs `/synthesize` to create `REPORT.md`.

**Files produced**:

| File | Description |
|------|-------------|
| `REPORT.md` | Key Findings, Results, Interpretation, Supporting Evidence, Future Directions, References |

### Phase E: Review & Submission

The agent runs `/submit` to validate documentation and generate an automated review.

**Files produced**:

| File | Description |
|------|-------------|
| `REVIEW.md` | Automated review with assessment, suggestions, and metadata |

---

## Tutorial: Your First Research Project

### 1. Start the workflow

```
/berdl_start
```

Choose "Start a new research project" and describe your research interest. For example:

> "I'm interested in whether species with open pangenomes tend to occupy more diverse environments than species with closed pangenomes."

### 2. The agent takes it from there

The agent will:
- Explore BERDL data to check feasibility
- Propose testable hypotheses
- Search the literature for context
- Write a research plan and ask for your approval
- Generate and run analysis notebooks
- Draft findings in `REPORT.md`
- Run an automated review

You'll be consulted at key decision points (hypothesis selection, plan approval, result interpretation). The agent will create a project branch and suggest a session name by default.

### 3. Final project structure

```
projects/core_size_openness/
  README.md          <-- project overview, status updated
  RESEARCH_PLAN.md   <-- hypothesis, approach, revision history
  REPORT.md          <-- findings, interpretation, evidence
  REVIEW.md          <-- automated review
  references.md
  notebooks/
    01_data_exploration.ipynb
    02_analysis.ipynb
  data/
    species_pangenome_stats.csv
  figures/
    core_vs_accessory_scatter.png
```

---

## Standalone Skills for Ad-Hoc Work

| Skill | When to use |
|-------|-------------|
| `/berdl` | Run exploratory queries against BERDL without a full project |
| `/berdl-discover` | Document a new or unfamiliar BERDL database |
| `/literature-review` | Search papers on a topic outside of a research project |
| `/synthesize` | Interpret results for an existing project with completed notebooks |
| `/submit` | Validate and review a complete project |
| `/berdl_start` | Get oriented if you are new to the system |

### When to use `/berdl` directly

Use `/berdl` for quick, ad-hoc data exploration:
- Checking what tables exist in a database
- Sampling rows to understand data shape
- Running one-off queries to answer a quick question
- Validating assumptions before committing to a full project

### Handling errors

When queries fail or return unexpected results, the pitfall-capture protocol activates automatically. It documents the issue in [pitfalls.md](pitfalls.md) so future projects avoid the same problem.

### Key references

- [overview.md](overview.md) -- Data architecture and table descriptions
- [collections.md](collections.md) -- Full database inventory
- [pitfalls.md](pitfalls.md) -- Common query issues and solutions
- [research_ideas.md](research_ideas.md) -- Backlog of research questions
- [schema.md](schema.md) -- Schema documentation index

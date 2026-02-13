# Research Workflow

**Purpose**: Step-by-step guide to conducting a research project using the BERIL Research Observatory skill pipeline, from hypothesis generation through peer review.

See [overview.md](overview.md) for the data architecture and [collections.md](collections.md) for the database inventory.

---

## Overview

A typical research project moves through six stages. Each stage has a dedicated skill (slash command) that handles the heavy lifting:

```
/hypothesis  -->  /research-plan  -->  /notebook  -->  JupyterHub  -->  /synthesize  -->  /submit
  (ideas)        (lit + feasibility)   (generate       (run the         (interpret       (automated
                                        .ipynb)         notebooks)       results)         review)
```

You can enter the pipeline at any stage. For example, if you already have a research plan, skip straight to `/notebook`. Supporting skills (`/literature-review`, `/berdl`, `/berdl-discover`) can be called at any point for ad-hoc exploration.

---

## Skills Reference

| Skill | Purpose | Key Inputs | Key Outputs |
|-------|---------|------------|-------------|
| `/hypothesis` | Generate testable research hypotheses from BERDL data | Research interest, target organism or pathway | 2-3 hypotheses with H0/H1, example SQL, relevant tables |
| `/research-plan` | Refine a question into a structured research plan | Hypothesis, target data | `research_plan.md`, project directory skeleton, `references.md` |
| `/notebook` | Generate Jupyter notebooks from a research plan | Project ID, `research_plan.md` | `.ipynb` files in `notebooks/` with PySpark boilerplate |
| `/synthesize` | Interpret results and draft findings | Project ID, notebook outputs (CSV, figures) | Updated `README.md` with findings, literature context, limitations |
| `/submit` | Validate documentation and request automated review | Project ID, complete project directory | Pre-submission checklist, `REVIEW.md` |
| `/literature-review` | Search PubMed, Europe PMC, CORE, OpenAlex | Research topic or question | Literature summary, `references.md` |
| `/berdl` | Query BERDL databases via REST API | SQL query or natural-language question | Query results, schema info, data samples |
| `/berdl-discover` | Explore and document a new BERDL database | Database name | Module file in `.claude/skills/berdl/modules/`, documentation |
| `/pitfall-capture` | Document errors and data surprises | Error context (invoked automatically) | Entry in [pitfalls.md](pitfalls.md) |

---

## Workflow Steps

### Step 1: Generate a Hypothesis (`/hypothesis`)

Start with a broad research interest. The hypothesis skill queries BERDL to check data availability and produces testable hypotheses grounded in what the lakehouse actually contains.

**What it does**:
- Explores relevant BERDL tables and their row counts
- Proposes 2-3 testable hypotheses with null and alternative formulations
- Identifies potential confounders and data limitations
- Suggests example SQL queries to test each hypothesis

**Files produced**: None (output is conversational; copy what you need into later steps).

**Example prompt**:
```
/hypothesis I'm interested in whether species with open pangenomes tend to
occupy more diverse environments than species with closed pangenomes.
```

---

### Step 2: Create a Research Plan (`/research-plan`)

Turn a hypothesis into a structured plan. This skill runs a literature review, checks data feasibility against BERDL, and produces a comprehensive plan document.

**What it does**:
- Calls `/literature-review` internally to gather relevant papers
- Validates that required tables and columns exist in BERDL
- Estimates query complexity and recommends a performance tier
- Writes the plan and scaffolds the project directory

**Files produced**:

| File | Description |
|------|-------------|
| `projects/{id}/research_plan.md` | Full plan: question, lit context, query strategy, analysis plan |
| `projects/{id}/references.md` | Citations from the literature review |
| `projects/{id}/README.md` | Skeleton README for the project |
| `projects/{id}/notebooks/` | Empty directory for notebooks |
| `projects/{id}/data/` | Empty directory for output data |
| `projects/{id}/figures/` | Empty directory for visualizations |

**Example prompt**:
```
/research-plan My hypothesis is that pangenome openness (accessory/core gene
ratio) correlates with metabolic pathway diversity as measured by GapMind.
Project ID: pangenome_pathway_diversity
```

---

### Step 3: Generate Notebooks (`/notebook`)

Convert the research plan into ready-to-run Jupyter notebooks with PySpark boilerplate, SQL queries, and visualization scaffolding.

**What it does**:
- Reads `research_plan.md` and [pitfalls.md](pitfalls.md) for query safety rules
- Generates notebooks with proper Spark session setup and auth
- Includes NULL checks, row counts, and data-quality validation cells
- Adds visualization cells using matplotlib/seaborn

**Files produced**:

| File | Description |
|------|-------------|
| `notebooks/01_data_exploration.ipynb` | Session setup, row counts, sample data, NULL checks |
| `notebooks/02_analysis.ipynb` | Main analysis queries and aggregations |
| `notebooks/03_visualization.ipynb` | Plots and figures (generated when the plan calls for it) |

**Example prompt**:
```
/notebook pangenome_pathway_diversity
```

---

### Step 4: Run Notebooks on JupyterHub

This is the only manual step. Upload the generated notebooks to the BERDL JupyterHub and execute them.

**What to do**:
1. Upload the `.ipynb` files from `projects/{id}/notebooks/` to JupyterHub
2. Run each notebook in order (01, 02, 03)
3. Review outputs and fix any query issues (check [pitfalls.md](pitfalls.md) if stuck)
4. Download result CSVs into `projects/{id}/data/`
5. Download figures into `projects/{id}/figures/`

**Tip**: The generated notebooks include safety patterns from [pitfalls.md](pitfalls.md) (LIMIT clauses, CAST operations, retry logic). If you encounter new issues, use `/pitfall-capture` to document them for future projects.

---

### Step 5: Synthesize Findings (`/synthesize`)

Once notebooks have been run and outputs are saved locally, this skill reads the results, compares them against the literature, and drafts findings.

**What it does**:
- Reads CSV files, figures, and executed notebook cells
- Compares results against the research plan's expected outcomes
- Searches for additional literature to contextualize findings
- Drafts a findings section with interpretation and limitations

**Files produced**:

| File | Description |
|------|-------------|
| `README.md` (updated) | Key Findings, Interpretation, Literature Context, Limitations, Future Directions |
| `references.md` (updated) | New citations found during synthesis |

**Example prompt**:
```
/synthesize pangenome_pathway_diversity
```

---

### Step 6: Submit for Review (`/submit`)

Run a pre-submission checklist and request an automated AI review of the project.

**What it does**:
- Checks that all required files exist (plan, notebooks, README, data)
- Validates documentation completeness (findings, limitations, references)
- Generates an independent review covering methodology, code quality, and findings

**Files produced**:

| File | Description |
|------|-------------|
| `REVIEW.md` | Automated review with assessment, suggestions, and metadata |

**Example prompt**:
```
/submit pangenome_pathway_diversity
```

---

## Tutorial: Your First Research Project

This walkthrough creates a small project investigating whether core genome size predicts pangenome openness.

### 1. Generate a hypothesis

```
/hypothesis Do species with smaller core genomes tend to have more open
pangenomes (higher accessory-to-core ratio)?
```

The skill responds with testable hypotheses and relevant tables (`pangenome`, `gene_cluster`, `gtdb_species_clade`). Pick the hypothesis you want to pursue.

### 2. Create the research plan

```
/research-plan Hypothesis: species with fewer core gene clusters have a
higher proportion of accessory genes. Project ID: core_size_openness
```

Your project directory now looks like this:

```
projects/core_size_openness/
  research_plan.md
  references.md
  README.md
  notebooks/
  data/
  figures/
```

### 3. Generate notebooks

```
/notebook core_size_openness
```

The directory grows:

```
projects/core_size_openness/
  ...
  notebooks/
    01_data_exploration.ipynb
    02_analysis.ipynb
```

### 4. Run on JupyterHub

Upload the notebooks. Execute them in order. Download results:

```
projects/core_size_openness/
  ...
  data/
    species_pangenome_stats.csv
  figures/
    core_vs_accessory_scatter.png
```

### 5. Synthesize findings

```
/synthesize core_size_openness
```

The README is updated with findings, interpretation, and literature context.

### 6. Submit for review

```
/submit core_size_openness
```

The final project directory:

```
projects/core_size_openness/
  research_plan.md
  references.md
  README.md          <-- now includes Key Findings
  REVIEW.md          <-- automated review
  notebooks/
    01_data_exploration.ipynb
    02_analysis.ipynb
  data/
    species_pangenome_stats.csv
  figures/
    core_vs_accessory_scatter.png
```

---

## Tips and Shortcuts

### Entering the workflow at different points

You do not need to start at Step 1. Common entry points:

- **Have a question but no hypothesis**: Start at `/hypothesis`
- **Have a hypothesis, need a plan**: Start at `/research-plan`
- **Have a plan, need notebooks**: Start at `/notebook {project_id}`
- **Have results, need writeup**: Start at `/synthesize {project_id}`
- **Have a complete project, need review**: Start at `/submit {project_id}`

### Supporting skills for ad-hoc work

| Skill | When to use |
|-------|-------------|
| `/literature-review` | Search papers on a topic outside of the research-plan workflow |
| `/berdl` | Run exploratory queries against BERDL without a full project |
| `/berdl-discover` | Document a new or unfamiliar BERDL database |
| `/berdl_start` | Get oriented if you are new to the system |

### When to use `/berdl` directly

Use `/berdl` for quick, ad-hoc data exploration:
- Checking what tables exist in a database
- Sampling rows to understand data shape
- Running one-off queries to answer a quick question
- Validating assumptions before committing to a full project

### Handling errors

If a query fails or returns unexpected results during any step, the `/pitfall-capture` skill activates automatically. It documents the issue in [pitfalls.md](pitfalls.md) so future projects avoid the same problem. You can also invoke it manually:

```
/pitfall-capture The genome_ANI table returns empty results when filtering
by species clade ID without the full prefix.
```

### Key references

- [overview.md](overview.md) -- Data architecture and table descriptions
- [collections.md](collections.md) -- Full database inventory
- [pitfalls.md](pitfalls.md) -- Common query issues and solutions
- [research_ideas.md](research_ideas.md) -- Backlog of research questions
- [schema.md](schema.md) -- Schema documentation index

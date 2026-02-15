---
name: notebook
description: Generate Jupyter notebooks from a research plan with PySpark boilerplate, SQL queries, and visualization placeholders. Use when the user has a research plan and wants to create analysis notebooks.
allowed-tools: Bash, Read, Write
user-invocable: true
---

# Notebook Generation Skill

Generate `.ipynb` notebook files from a research plan, with PySpark boilerplate, SQL queries, visualization placeholders, and markdown narrative.

## Usage

```
/notebook <project_id>
```

If no `<project_id>` argument is provided, detect from the current working directory (if inside `projects/{id}/`).

## Workflow

### Step 1: Read Research Plan

1. Read `RESEARCH_PLAN.md` (or `research_plan.md` for legacy projects) in `projects/{project_id}/`
2. Extract: tables needed, key queries, analysis steps, expected outputs, performance tier
3. If no research plan exists, ask the user for the analysis goal and generate notebooks from that description

Also read these reference files:
- `.claude/skills/berdl/modules/query-patterns.md` — mandatory safety rules
- `docs/pitfalls.md` — known data issues to guard against

### Step 2: Generate Notebooks

Create notebooks based on the plan's analysis sections. Each notebook follows a standard structure.

#### Notebook 1: `01_data_exploration.ipynb`

| Cell | Type | Content |
|------|------|---------|
| 1 | markdown | Title, purpose, data sources from the research plan |
| 2 | code | Spark session setup: `spark = get_spark_session()` |
| 3 | code | Row counts for all relevant tables (`spark.sql("SELECT COUNT(*) ...")`) |
| 4 | code | Sample data inspection (5 rows per table with `LIMIT 5`) |
| 5 | code | NULL/coverage checks for annotation columns and key fields |
| 6 | markdown | Summary placeholder: "## Findings\n\nRecord what you observed..." |

#### Notebook 2: `02_analysis.ipynb`

| Cell | Type | Content |
|------|------|---------|
| 1 | markdown | Research question, hypothesis, approach summary |
| 2 | code | Spark session + imports (`pandas`, `numpy` for final steps) |
| 3+ | code | Query cells from `research_plan.md` Key Queries section |
| N-2 | code | Aggregation / statistical summary cells |
| N-1 | code | Save results: `df.toPandas().to_csv('../data/{output}.csv', index=False)` |
| N | markdown | Interpretation placeholder: "## Results\n\nDescribe what the analysis shows..." |

#### Notebook 3: `03_visualization.ipynb` (only if plan calls for it)

| Cell | Type | Content |
|------|------|---------|
| 1 | code | Imports: `import matplotlib.pyplot as plt`, `import seaborn as sns`, `import pandas as pd` |
| 2 | code | Load CSVs: `pd.read_csv('../data/{output}.csv')` |
| 3+ | code | One visualization cell per figure in the plan |
| N | code | Save figures: `plt.savefig('../figures/{name}.png', dpi=150, bbox_inches='tight')` |

### Step 3: Apply Safety Rules

Before writing any SQL into notebook cells, verify against the query-patterns.md checklist:

- [ ] **Partitioned column filter**: Queries filter on indexed columns (e.g., `gtdb_species_clade_id`)
- [ ] **Large table guard**: Billion-row tables (`gene`, `genome_ani`, `genefitness`) are filtered before joins
- [ ] **Bounded results**: All queries have LIMIT, aggregation, or narrow WHERE
- [ ] **Type safety**: String-typed numeric columns use CAST before comparison
- [ ] **Species ID quoting**: IDs with `--` are properly quoted
- [ ] **Annotation NULL filter**: `-` and NULL filtered for annotation columns
- [ ] **ORDER BY present**: Included for any paginated queries
- [ ] **Correct JOIN keys**: `eggnog_mapper_annotations.query_name` joins to `gene_cluster.gene_cluster_id`

Also apply these notebook-specific rules:

- **PySpark-first**: Keep data as Spark DataFrames for all filtering, joins, and aggregations
- **`.toPandas()` only for final small results**: Never call `.toPandas()` on unfiltered/unaggregated DataFrames
- **Checkpoint pattern**: Save intermediate results to CSV so notebooks can be re-run partially
- **Self-contained**: Each notebook re-initializes the Spark session (don't assume prior notebook state)

### Step 4: Write Notebooks

Write `.ipynb` files to `projects/{project_id}/notebooks/`.

Use the standard Jupyter notebook JSON format:

```json
{
 "cells": [...],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.9.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
```

Each cell follows this structure:

**Markdown cell**:
```json
{
 "cell_type": "markdown",
 "metadata": {},
 "source": ["# Title\n", "\n", "Description text"]
}
```

**Code cell**:
```json
{
 "cell_type": "code",
 "execution_count": null,
 "metadata": {},
 "outputs": [],
 "source": ["spark = get_spark_session()"]
}
```

### Step 5: Update REPORT.md

If `projects/{project_id}/REPORT.md` exists, update the Supporting Evidence > Notebooks table:

```markdown
## Supporting Evidence

### Notebooks
| Notebook | Purpose |
|----------|---------|
| `01_data_exploration.ipynb` | {purpose} |
| `02_analysis.ipynb` | {purpose} |
| `03_visualization.ipynb` | {purpose} |
```

If `REPORT.md` does not yet exist, create it with a stub `## Supporting Evidence` section containing the notebooks table.

### Step 6: Suggest Next Steps

After generating notebooks, tell the user:

> "Notebooks generated in `projects/{project_id}/notebooks/`. Next steps:
> 1. Upload notebooks to BERDL JupyterHub
> 2. Run them in order (01 → 02 → 03)
> 3. Download output CSVs to `projects/{project_id}/data/` and figures to `figures/`
> 4. Use `/synthesize` to interpret results and draft findings"

## PySpark Boilerplate Reference

### Spark Session (always first code cell)
```python
spark = get_spark_session()
```

Note: `get_spark_session()` is a JupyterHub built-in — no import needed. It is **not available** outside JupyterHub.

### Query Pattern
```python
df = spark.sql("""
    SELECT column1, column2, COUNT(*) as cnt
    FROM database.table
    WHERE filter_column = 'value'
    GROUP BY column1, column2
    ORDER BY cnt DESC
""")
df.show(20)
```

### Safe `.toPandas()` (only for small results)
```python
# Only after aggregation or with tight filters
pdf = df.toPandas()
pdf.to_csv('../data/results.csv', index=False)
```

### Large Result Handling
```python
# Write directly from Spark — no .toPandas()
df.write.mode('overwrite').parquet('../data/large_results.parquet')
```

## Integration

- **Reads from**: `RESEARCH_PLAN.md` (or `research_plan.md` for legacy projects), `query-patterns.md`, `docs/pitfalls.md`
- **Produces**: `.ipynb` files in `notebooks/`, updated `REPORT.md` (Supporting Evidence > Notebooks table)
- **User then**: Uploads to JupyterHub, runs notebooks, downloads outputs
- **Next step**: `/synthesize` to interpret results

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

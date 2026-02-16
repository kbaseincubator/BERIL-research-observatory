---
name: synthesize
description: Read analysis outputs, compare against literature, and draft findings for a project REPORT.md. Use when notebooks have been run and the user wants to interpret results and write up findings.
allowed-tools: Bash, Read, Write, Edit, WebSearch, AskUserQuestion
user-invocable: true
---

# Synthesis Skill

After notebooks have been run, read the outputs, compare against literature, and draft the findings/interpretation sections in the project's `REPORT.md`. Also update `## Status` in `README.md` to reflect completion.

## Usage

```
/synthesize <project_id>
```

If no `<project_id>` argument is provided, detect from the current working directory (if inside `projects/{id}/`).

## Workflow (Two-Pass Approach)

### Pass 1: Read Data and Draft Findings

#### Step 1: Gather Project Context

Read these project files:
1. `projects/{project_id}/RESEARCH_PLAN.md` — the hypothesis, expected outcomes, analysis plan (or `research_plan.md` for legacy projects)
2. `projects/{project_id}/README.md` — current state of the project (preserve Research Question, Authors)
3. `projects/{project_id}/references.md` — existing literature references

If `RESEARCH_PLAN.md` doesn't exist, check for `research_plan.md` (legacy). If neither exists, read the README for research question and hypothesis context.

#### Step 2: Read Analysis Outputs

Scan the project for results:

1. **CSV files** in `projects/{project_id}/data/`:
   - Read each CSV and interpret: column names, row counts, distributions, key statistics
   - Identify the main result variables (correlations, counts, p-values, effect sizes)

2. **Figures** in `projects/{project_id}/figures/`:
   - List available figures and their filenames (infer content from names)

3. **Notebook outputs** in `projects/{project_id}/notebooks/`:
   - If executed `.ipynb` files are present, read output cells for results
   - Look for printed summaries, DataFrames, and statistical test outputs

#### Step 3: Draft Initial Findings

Based on the data, draft findings that address:

1. **Key results**: What did the data show? (specific numbers, correlations, counts)
2. **Hypothesis outcome**: Was H1 supported or H0 not rejected?
3. **Statistical significance**: Report p-values, effect sizes, confidence intervals if available
4. **Unexpected patterns**: Note any surprising results or anomalies

#### Step 4: Present Draft to User

Show the initial findings interpretation and ask:
- "Does this interpretation look correct?"
- "Are there results I missed or misinterpreted?"
- "Any additional context to include?"

Wait for user feedback and revise if needed.

### Pass 2: Literature Cross-Reference and Synthesis

#### Step 5: Search Literature for Context

Invoke `/literature-review` to search for papers that:
- Tested similar hypotheses in related organisms
- Used comparable methods or data
- Reported results that align or conflict with the BERDL findings

Focus searches on:
- The specific organisms/taxa analyzed in the project
- The specific biological question (e.g., "pangenome openness environmental adaptation")
- Key methods used (e.g., "partial correlation phylogenetic signal")

#### Step 6: Compare Findings Against Literature

For each key finding, assess:

| Question | Assessment |
|---|---|
| Does this agree with published work? | Cite supporting papers |
| Does this contradict published work? | Note methodology differences that could explain discrepancies |
| Is this novel? | Identify what BERDL data adds that wasn't known before |
| Are there caveats? | Data coverage, confounders, methodological limitations |

#### Step 7: Produce Synthesis

Create or update `projects/{project_id}/REPORT.md` with the following sections:

```markdown
# Report: {Title}

## Key Findings

### {Finding 1 Title}

![Description of figure](figures/relevant_figure.png)

{Statistical result with specific numbers}

*(Notebook: {notebook_name}.ipynb)*

### {Finding 2 Title} (if applicable)

{Statistical result}

*(Notebook: {notebook_name}.ipynb)*

## Results
{Detailed results with embedded figures and markdown tables}

## Interpretation
{What the results mean biologically}

### Literature Context
- {Finding} aligns with Author et al. (Year) who found {similar result} in {organism}
- {Finding} contradicts Author et al. (Year) — possible explanation: {methodology difference}

### Novel Contribution
{What BERDL data adds that wasn't known before}

### Limitations
- {Data coverage limitations}
- {Potential confounders}
- {Methodological caveats}

## Data

### Sources
| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `{collection_id}` | `{table1}`, `{table2}` | {what this data provides} |

### Generated Data
| File | Rows | Description |
|------|------|-------------|
| `data/{filename}.csv` | {row_count} | {what the data contains} |

## Supporting Evidence

### Notebooks
| Notebook | Purpose |
|----------|---------|
| `{filename}.ipynb` | {what the notebook does} |

### Figures
| Figure | Description |
|--------|-------------|
| `{filename}.png` | {what the figure shows} |

## Future Directions
1. {Suggested next step based on findings}
2. {Follow-up analysis addressing limitations}
3. {New questions raised by the results}

## References
- Author et al. (Year). "Title." *Journal*. PMID: {pmid}
```

**Important guidelines for the template:**

- **Inline figures**: Place `![description](figures/filename.png)` near the finding each figure supports. The UI rewrites these paths automatically for web rendering. Every figure in the project's `figures/` directory should appear inline at least once.
- **Notebook provenance**: End each finding subsection with `*(Notebook: filename.ipynb)*` to trace results back to the analysis code.
- **Data section**: The `## Data` section documents data lineage. `### Sources` lists BERDL collections and tables queried. `### Generated Data` lists output files with row counts.
- **Collection IDs**: Use the exact BERDL collection identifier (e.g., `kescience_fitnessbrowser`, `kbase_ke_pangenome`) in the Sources table. These IDs link to the collection detail pages on the Research Observatory, which include citation and attribution information for data providers.
- **README update**: Ensure the collection IDs appear somewhere in the README.md text so the UI can auto-detect and display Data Collections links on the project page.
- **References**: Always include references, even for well-known data sources. At minimum cite the primary data sources (e.g., Price et al. 2018 for Fitness Browser, Arkin et al. 2018 for KBase).

Also update `projects/{project_id}/README.md`:
- Update `## Status` to reflect completion (e.g., "Complete — see [Report](REPORT.md) for findings")
- Preserve existing `## Research Question` and `## Authors` sections

#### Step 8: Update References

Add any new papers found during synthesis to `projects/{project_id}/references.md`.

If the file doesn't exist, create it following the format from `/literature-review`.

#### Step 9: Trigger Pitfall Capture (if needed)

If unexpected data patterns were found during interpretation (missing data, anomalous distributions, coverage gaps), follow the pitfall-capture protocol.

### Step 10: Suggest Next Steps

After completing the synthesis, tell the user:

> "Findings drafted in `projects/{project_id}/REPORT.md`. Next steps:
> 1. Review the Key Findings and Interpretation sections
> 2. Use `/submit` to run pre-submission checks and get an automated review
> 3. Address any review feedback and re-submit"

## Integration

- **Reads from**: `data/*.csv`, `figures/`, `notebooks/*.ipynb`, `RESEARCH_PLAN.md`, `references.md`
- **Calls**: `/literature-review` (for literature comparison)
- **Produces**: `REPORT.md` (Key Findings, Results, Interpretation, Supporting Evidence, Future Directions, References); updated `README.md` (Status)
- **Consumed by**: `/submit` (reviewer assesses the findings in REPORT.md)

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

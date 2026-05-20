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

#### Step 0: Precondition check

Read `projects/{project_id}/beril.yaml` and validate status. If `beril.yaml` is missing (pre-manifest project), skip this check and rely on the file-existence checks below.

- `status: exploration` — **stop**. Tell the user:
  > "This project is still in exploration — there's no `RESEARCH_PLAN.md` to synthesize against yet. Write the plan first (use `/berdl_start` to resume the workflow), then re-run `/synthesize`."
- `status: proposed` — **stop**. Tell the user:
  > "This project has a research plan but no analysis yet. Run the analysis notebooks first (Phase C of the workflow) so `/synthesize` has results to interpret. Resume via `/berdl_start`."
- `status: active` — proceed; this is the normal forward path (`active` → `analysis`).
- `status: analysis` — proceed (re-synthesis on a project still pre-review; no status change).
- `status: reviewed` — **silent demote**. Existing `REVIEW_N.md` files were against the previous `REPORT.md` and will go stale via hash mismatch. No prompt; just inform the user in the agent's reply: "Demoted to `analysis`; existing reviews are now stale. Run `/berdl-review` again before submitting." Then proceed.
- `status: complete` — **explicit confirmation prompt** before proceeding:
  > "This project is currently complete (approved {approval.at} by {approval.by}). Running /synthesize will overwrite `REPORT.md` and demote the project to `analysis`. The previous approval will be archived under `previous_approvals`. Continue? (y/n)"
  - **Yes**: move the current `approval` block in `beril.yaml` to `previous_approvals: []` (append) with an added `archived_at: "<now>"` field, set `status: analysis`, delete `projects/{project_id}/REVIEW.md` (the canonical copy of the now-archived review), and delete both `SUBMITTED.md` and `SUBMISSION_FAILED.md` if present (audit lives in `beril.yaml.previous_approvals` and `beril.yaml.submissions[]`). The README Status update happens in Step 7 below as part of the normal `/synthesize` flow. Then proceed.
  - **No**: abort with no changes.

Synthesizing without analysis outputs (the `exploration` and `proposed` cases) produces empty or fabricated findings, which is exactly what the new lifecycle is designed to prevent. The `reviewed`/`complete` demotes are how the iteration loop and reopen-and-resubmit flow stay honest.

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

## Discoveries

(Optional section — include only if the analysis surfaced non-trivial findings worth elevating across projects. Skip the section entirely if there's nothing material to capture; an absent section is the natural representation of "no claims of this kind." Each entry is a self-contained insight a reader from another project could learn from.)

- {One-line discovery 1, e.g., "Pangenome openness correlates with environmental breadth in soil-associated genera (rho=0.38, p<0.01)."}
- {One-line discovery 2 (if applicable)}

## Performance Notes

(Optional section — include only if this project hit non-obvious query timings, optimizations, or anti-patterns that future projects on similar data should know. Skip the section entirely if there's nothing material to capture.)

- {One-line performance observation, e.g., "Joining `species_pangenome_genes` to `species_function_genes` via `species_id` is 3x faster than via `cluster_id` for queries spanning >100 species."}

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
- **Discoveries / Performance Notes sections**: optional. Populate when there's something material to capture. **Do not write to per-project memory files directly** — these sections flow through `/berdl-review` (the reviewer evaluates them as part of the report), then `/submit` extracts the approved-and-reviewed content into `projects/{project_id}/memories/{discoveries,performance}.md` at approval time. Writing memories at synthesize time would propagate unvetted claims; the approval-gated path keeps OV-ingestible memories tied to content that survived review. If a section has no entries, omit it from REPORT.md entirely (don't write an empty `## Discoveries` heading); `/submit` treats absent + empty identically and won't write a memory file.

Also update `projects/{project_id}/README.md`:
- After Step 0, status is always either `active` (forward path) or `analysis` (re-synthesis path, possibly after a `reviewed`/`complete` demote). In both cases, set `## Status` to "Analysis — report drafted, awaiting `/berdl-review` and `/submit`." This is honest about the project's state: any prior approval was archived in Step 0, and any prior reviews are stale via hash mismatch.
- Preserve existing `## Research Question` and `## Authors` sections.

#### Step 7b: Update Manifest

Update `projects/{project_id}/beril.yaml` (skip silently if the file is missing — pre-manifest project):

- `status`: set to `analysis`. (Step 0 already handled the demote cases for `reviewed`/`complete` and rejected `exploration`/`proposed`, so the only statuses that reach Step 7b are `active` — flipping forward — and `analysis` — already there, idempotent.)
- `artifacts.report`: `true`
- `last_session_at`: current ISO 8601 timestamp

This makes `/synthesize` self-contained: when invoked directly (outside the `/berdl_start` orchestration), the manifest reflects the correct state without bypassing the plan-review checkpoint or the `proposed` → `active` transition that Phase C owns.

#### Step 8: Update References

Add any new papers found during synthesis to `projects/{project_id}/references.md`.

If the file doesn't exist, create it following the format from `/literature-review`.

#### Step 9: Trigger Pitfall Capture (if needed)

If unexpected data patterns were found during interpretation (missing data, anomalous distributions, coverage gaps), follow the pitfall-capture protocol.

### Step 10: Suggest Next Steps

After completing the synthesis, tell the user:

> "Findings drafted in `projects/{project_id}/REPORT.md`. Next steps:
> 1. Review the Key Findings and Interpretation sections.
> 2. Run `/berdl-review` to produce a numbered review of the current report (`REVIEW_N.md`). Iterate as much as you want — each review embeds the report's hash so `/submit` knows which one is current.
> 3. When you're ready to stand behind the project, run `/submit` to approve and archive it to the lakehouse."

## Integration

- **Reads from**: `data/*.csv`, `figures/`, `notebooks/*.ipynb`, `RESEARCH_PLAN.md`, `references.md`
- **Calls**: `/literature-review` (for literature comparison)
- **Produces**: `REPORT.md` (Key Findings, Results, Interpretation, Supporting Evidence, Future Directions, References); updated `README.md` (Status)
- **Consumed by**: `/submit` (reviewer assesses the findings in REPORT.md)

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to the active project's `projects/<id>/memories/pitfalls.md`.

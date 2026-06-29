---
name: execute-plan
description: Read a frozen RESEARCH_PLAN.md and build, run, and write up the analysis — running each notebook's discriminating query first, then synthesizing a REPORT.md. Use when a project's plan is approved (`status: proposed` or `active`) and analysis should begin or resume.
allowed-tools: Bash, Read, Write, Edit, WebSearch, AskUserQuestion
user-invocable: true
---

# Execute Plan Skill

This is the **EXECUTE** workflow — the middle of the research arc. It reads the *frozen* `RESEARCH_PLAN.md` (the contract) and `research_state.json` (orientation), then builds and runs the planned notebooks, updates the world-model as understanding changes, and hands off to synthesis and review.

It owns the lifecycle transitions `proposed → active → analysis`. The plan pins the science and the decision rules; execution owns the exact code and may revise the plan — but a *material* change demotes the project and re-runs the plan-review checkpoint (see the Revision Loop). `beril.yaml` remains the sole lifecycle authority; `research_state.json` is non-authoritative orientation only and never gates a transition.

## Usage

```
/execute-plan <project_id>
```

If no `<project_id>` argument is provided, detect from the current working directory (if inside `projects/{id}/`). This skill is normally reached from `/berdl_start` (it delegates Phase C/D here), but it is independently invocable.

## Precondition: the plan must be frozen and approved

1. Read the **frozen** `projects/<id>/RESEARCH_PLAN.md` (the contract: competing hypotheses, falsification tests, decision criteria, per-notebook analysis plan) and `projects/<id>/research_state.json` (orientation: question, open questions, assumptions, dead ends).
2. Confirm the **plan-review checkpoint was approved**. If `beril.yaml` `status` is `proposed`, the plan was written but you must verify the user explicitly approved at the checkpoint (`/research-plan` step 8). If you are unsure whether the checkpoint was passed, **do not start analysis** — return to `/research-plan` and run the checkpoint. Never skip the plan-review checkpoint.
3. If `status` is already `active`, the analysis is being resumed — pick up at the next unfinished notebook.

## Phase C: Analysis (Notebooks)

Status transition: `proposed` → `active`.

- Update `beril.yaml`: `status: active`, `last_session_at` to now.
- For **each notebook in the Analysis Plan**, in order:
  1. Create the numbered analysis notebook (`01_data_exploration.ipynb`, `02_analysis.ipynb`, …) following the per-notebook spec in `RESEARCH_PLAN.md`.
  2. **Run the discriminating/refuting query FIRST** (Platt's strong inference): the crucial test the plan named for this step goes *before* any confirmatory cells. Lead with the result that could refute the hypothesis, not the one that would confirm a favorite. This is the forward complement of post-hoc refutation.
  3. Produce the **expected output** named in the plan (the CSV(s) / figure(s)), then execute the remaining cells, inspect outputs, iterate.
  4. **Commit** after the notebook is complete (and after any data extraction or key result reproduced).
- Notebooks are the primary audit trail — do as much work as possible in notebooks so humans can inspect intermediate results. When parallel execution or complex pipelines are needed, write scripts in `projects/<id>/src/` but call them from notebooks.
- **Capture pitfalls** as you go via `.claude/skills/pitfall-capture/SKILL.md` (appends to `projects/<id>/memories/pitfalls.md`). Re-read `docs/pitfalls.md` and `docs/performance.md` when something doesn't behave as expected.
- **Update the world-model** as understanding changes — resolve `open_questions`, revise `assumptions`, record `dead_ends` (avenues tried and abandoned, so they aren't re-attempted):
  ```bash
  beril state set <project_id> --json '{"open_questions": ["..."], "assumptions": ["..."], "dead_ends": ["..."]}'
  ```
  This is orientation only — **never** record settled findings or hypothesis verdicts here. Those live in `RESEARCH_PLAN.md` and (when the claims ledger is present) `claims.json`.

### Revision Loop

The plan is a contract; revisions are explicit, not silent. As analysis proceeds:

- **Minor deviation** (a tweaked filter, a renamed output, an extra exploratory cell that doesn't change the science): append to `RESEARCH_PLAN.md` Revision History as `- **v{n}** ({date}): {change}` and **continue**.
- **MATERIAL change** to the pre-registered contract — dropping or adding a hypothesis, moving a decision threshold, abandoning the discrimination strategy, or changing what result would refute H1: this is no longer the plan that was approved. **Demote `active → proposed`** in `beril.yaml`, record the reason in Revision History, and **re-run the plan-review checkpoint** (return to `/research-plan` step 8). Do not continue analysis on a materially-changed plan without re-approval.

### Checkpoint: Results Review

After notebooks are executed and committed, pause and present key results before synthesis.

- Summarize the key results: main statistics, notable patterns, anything unexpected. Render computed signals as words, not fabricated numbers — the only numbers shown are real counts and statistics actually produced by the notebooks.
- Ask: "Look at the notebooks/figures before I write up findings, or proceed with `/synthesize`?"
- If the user wants to explore first, wait. If they want changes, iterate on the notebooks before proceeding.

## Phase D: Synthesis & Writeup

Status transition: `active` → `analysis` (handled by `/synthesize` itself).

- Run `/synthesize` to create `REPORT.md`. The skill compares results against the **pre-registered decision rule** and confidence prior in `RESEARCH_PLAN.md`, updates `beril.yaml` automatically (`status: analysis`, `artifacts.report: true`, `last_session_at`), and updates `README.md` Status to "Analysis — report drafted, awaiting `/berdl-review` and `/submit`."
- Commit the report and updated `beril.yaml`.
- Discuss the report with the user — revise if needed.

## Hand-off to Review & Submit

Execution ends at synthesis. Hand the project to the existing back of the arc:

- **`/berdl-review {project_id}`** — produces a numbered `REVIEW_N.md` with a report-hash footer; flips `status: analysis → reviewed`. Iterate freely (different models, multiple opinions).
- **`/submit {project_id}`** — verifies the latest review covers the current `REPORT.md`, checks the configured ORCID, asks for explicit approval, uploads to the lakehouse, and writes the `SUBMITTED.md` marker; flips `status: reviewed → complete`.

When the provenance/trust layer is present, `/berdl-refute` and the claims ledger (`claims.json`) complement this back-of-arc handoff — `/berdl-refute` is the post-analysis counterpart to the discriminating-query-first discipline above. These are referenced as complementary **when present**; everything here works unchanged on a repo without them, and the canonical handoff is `/berdl-review` + `/submit`.

## Integration

- **Reads from**: `projects/<id>/RESEARCH_PLAN.md` (frozen contract), `projects/<id>/research_state.json` (orientation), `docs/pitfalls.md`, `docs/performance.md`, `projects/*/memories/pitfalls.md`.
- **Writes**: numbered notebooks under `projects/<id>/notebooks/`, data under `data/`, figures under `figures/`, `RESEARCH_PLAN.md` Revision History, `beril.yaml` (`status: active`; demote to `proposed` on a material change), `research_state.json` (via `beril state set` — orientation only).
- **Calls**: `/berdl` or `/berdl-query` (running queries), `/pitfall-capture` (logging gotchas), `/synthesize` (Phase D → `REPORT.md`).
- **Hands off to**: `/berdl-review` + `/submit` (and `/berdl-refute` + the claims ledger when present).

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to the active project's `projects/<id>/memories/pitfalls.md`.

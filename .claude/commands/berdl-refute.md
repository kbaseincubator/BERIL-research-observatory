---
description: Adversarial red-team pass that tries to BREAK each Key Finding and writes REFUTATION_N.md (advisory; no lifecycle change).
argument-hint: "[project_id] [--model <model_id>]"
allowed-tools: Bash, Read
---

# Refutation Pass (`/berdl-refute`)

Run a disconfirmation-first red-team over a project's `REPORT.md`. For each Key Finding the refuter designs a disconfirming check, looks for contradicting literature, and renders a verdict (`holds` / `holds-with-caveats` / `needs-replication` / `undermined` / `unverifiable`). It is **advisory** — it writes a numbered `REFUTATION_N.md` and changes no lifecycle state. "Couldn't find disconfirming evidence" is a real, reportable outcome, not a pass.

Arguments: `$ARGUMENTS`

## Workflow

### Step 1: Resolve the project

- Take the project id from the first argument, or detect it from the current working directory if inside `projects/{id}/`.
- Validate that `projects/{project_id}/` exists and contains a `REPORT.md`. If there is no REPORT.md, stop: `FAIL  No REPORT.md to refute yet — run /synthesize first.`

### Step 2: Run the refuter

Run from the repository root. `--type refute` selects the `.claude/reviewer/REFUTATION_PROMPT.md` rubric, auto-numbers `REFUTATION_N.md`, writes **no** report-hash footer, and makes **no** lifecycle change:

```bash
bash tools/review.sh {project_id} --type refute
```

- A refutation pass benefits from the **strongest available model** (weak models have a high false-positive rate on falsification). Pass `--model <model_id>` to override the default, e.g. `--model claude-opus-4-8`.
- The script claims the next `REFUTATION_N.md` immediately (race-safe). It does **not** touch `beril.yaml`, `README.md`, or the project status.

### Step 3: Verify completion

Confirm `projects/{project_id}/REFUTATION_N.md` exists and is non-empty (more than the placeholder line; contains YAML frontmatter). If the file is missing or empty, surface the error and stop.

### Step 4: Present surviving checks

Read the new `REFUTATION_N.md` and summarize for the user:
- Per finding: the verdict and the disconfirming check that was designed.
- Highlight any finding marked `undermined` or `needs-replication`, and any concrete disconfirming check that **survived** (the author could not rule it out from existing data).

### Step 5: Lift surviving checks into the report (the author decides)

The refuter is read-only over the project — it never edits the report. **You** (the parent agent), with the author, decide what to act on:
- For each surviving disconfirming check or contradiction, offer to record it under the relevant Key Finding's limitations / refuting notes in `REPORT.md` and re-tag that finding's confidence and status accordingly (follow `/synthesize`). Rank competing explanations by **survival of a disconfirming check** — an unfalsified hypothesis is not a survived one.
- If `REPORT.md` changes as a result, re-run the claims step (`beril claims build {project_id}`) and `/berdl-review` so the review and `claims.json` reflect the updated report.

## Notes

- Refutations are numbered (`REFUTATION_1.md`, `REFUTATION_2.md`, …) and preserved as a history, like reviews.
- A refutation pass has **no** report-hash footer and does **not** advance the lifecycle; it is purely advisory input for the author.
- For the standard quality review (methodology, evaluation integrity, findings), use `/berdl-review`. Refutation complements it by actively trying to break the findings rather than judge a finished report.

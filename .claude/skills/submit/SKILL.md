---
name: submit
description: Submit a project for automated review. Use when the author is ready to validate documentation and request an AI review.
allowed-tools: Bash, Read, Write
---

# Project Submission Skill

Submit a BERDL analysis project for automated review. This runs pre-submission validation checks, then invokes a headless reviewer agent to produce an independent `REVIEW.md`.

## Usage

```
/submit <project_id>
```

If no `<project_id>` argument is provided, detect from the current working directory (if inside `projects/{id}/`).

## Workflow

### Step 1: Resolve Project

1. Accept `<project_id>` from the argument, or detect from cwd if inside a `projects/` subdirectory
2. Validate that `projects/{project_id}/` exists in the repository root
3. If the directory does not exist, print an error and stop

### Step 2: Pre-Submission Checks

Run these checks against the project directory and print a checklist summary:

**Critical checks** (block submission on failure):
- `README.md` exists in `projects/{project_id}/`
- `## Research Question` section is present and non-empty in README.md
- `## Authors` section is present with at least one entry that is not a placeholder (e.g., not "Your Name")
- `REPORT.md` exists in `projects/{project_id}/` and contains a `## Key Findings` section

**Advisory checks** (warn but allow submission):
- Discoveries documented in `docs/discoveries.md` — search for `[{project_id}]` tag
- Pitfalls documented in `docs/pitfalls.md` — search for the project name or id
- Research plan documented — check if `projects/{project_id}/RESEARCH_PLAN.md` exists (or `research_plan.md` for legacy projects)
- Interpretation documented — check if `projects/{project_id}/REPORT.md` exists and contains a `## Interpretation` section
- References documented — check if `projects/{project_id}/references.md` exists (created by `/literature-review`)
- Project files committed to git — run `git status --porcelain projects/{project_id}/` and warn if there are uncommitted or untracked changes
- **Notebook outputs**: Check that notebooks have saved outputs (not just empty code cells). For each `.ipynb` in `notebooks/`, parse the JSON and count code cells with non-empty `outputs` arrays. Warn if any notebook has 0 cells with outputs.
- **Figures**: Check that `figures/` directory exists and contains at least one PNG file. Warn if empty or missing.
- **Dependencies**: Check that `requirements.txt` exists in the project directory. Warn if missing.
- **Reproduction guide**: Check that README.md contains a `## Reproduction` section. Warn if missing.

Print the checklist as:
```
Pre-submission checklist for: {project_id}
─────────────────────────────────────────
  PASS  README.md exists
  PASS  Research question present
  FAIL  Authors section missing or empty
  WARN  No discoveries documented
  PASS  Pitfalls documented
  WARN  No research plan documented
  WARN  No references documented
  WARN  Uncommitted changes in project directory
```

Use PASS/FAIL/WARN labels. If any critical check fails (FAIL), print the failures and stop — do not invoke the reviewer.

### Step 3: Status Check

Before invoking the reviewer, read the `## Status` section in `projects/{project_id}/README.md`. If the status is not "Completed" (i.e., it still says "In Progress", "Proposed", or similar), ask the user:

> "The project status is currently '{current_status}'. Should I update it to 'Completed' before submitting?"

If the user agrees, update the `## Status` section in README.md to "Completed" with a brief summary of findings (pull from the `## Key Findings` section of REPORT.md). For example:

```
## Status

Completed — {one-line summary from Key Findings}.
```

If the user declines, proceed with the current status.

### Step 4: Invoke Reviewer

If all critical checks pass, invoke the reviewer subprocess:

```bash
claude -p \
  --system-prompt "$(cat .claude/reviewer/SYSTEM_PROMPT.md)" \
  --allowedTools "Read,Write" \
  --dangerously-skip-permissions \
  "Review the project at projects/{project_id}/. Read all files in the project directory — especially README.md, RESEARCH_PLAN.md, and REPORT.md. Also read docs/pitfalls.md for known issues. Write your review to projects/{project_id}/REVIEW.md."
```

Run this command from the repository root directory.

### Step 5: Verify Completion

After the reviewer subprocess completes:

1. Check that `projects/{project_id}/REVIEW.md` was created
2. If it exists, print a success message with a brief summary
3. If it was not created, print an error indicating the reviewer did not produce output

### Step 5: Post-Review Guidance

After presenting the review summary, provide next steps based on the review outcome:

**If the review has no critical or important issues** (clean review):
- Remind the user to mark the project as complete in these locations:
  1. `projects/{project_id}/README.md` — ensure `## Status` says "Completed" with a one-line summary
  2. `docs/research_ideas.md` — move the project entry from "High/Medium Priority Ideas" to "Completed Ideas" with a results summary
- Suggest committing all changes

**If the review has critical or important issues**:
- List the issues to address
- Suggest re-running `/submit` after fixes

### Notes

- The reviewer prompt is stored at `.claude/reviewer/SYSTEM_PROMPT.md` and is not controlled by the author
- Each `/submit` produces a fresh review, replacing any existing `REVIEW.md`
- To address review feedback, update the project and run `/submit` again

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

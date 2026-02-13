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

**Advisory checks** (warn but allow submission):
- Discoveries documented in `docs/discoveries.md` — search for `[{project_id}]` tag
- Pitfalls documented in `docs/pitfalls.md` — search for the project name or id
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
  WARN  Uncommitted changes in project directory
```

Use PASS/FAIL/WARN labels. If any critical check fails (FAIL), print the failures and stop — do not invoke the reviewer.

### Step 3: Invoke Reviewer

If all critical checks pass, invoke the reviewer subprocess:

```bash
claude -p \
  --system-prompt "$(cat .claude/reviewer/SYSTEM_PROMPT.md)" \
  --allowedTools "Read,Write" \
  --dangerously-skip-permissions \
  "Review the project at projects/{project_id}/. Read all files in the project directory. Also read docs/pitfalls.md for known issues. Write your review to projects/{project_id}/REVIEW.md."
```

Run this command from the repository root directory.

### Step 4: Verify Completion

After the reviewer subprocess completes:

1. Check that `projects/{project_id}/REVIEW.md` was created
2. If it exists, print a success message with a brief summary
3. If it was not created, print an error indicating the reviewer did not produce output

### Notes

- The reviewer prompt is stored at `.claude/reviewer/SYSTEM_PROMPT.md` and is not controlled by the author
- Each `/submit` produces a fresh review, replacing any existing `REVIEW.md`
- To address review feedback, update the project and run `/submit` again

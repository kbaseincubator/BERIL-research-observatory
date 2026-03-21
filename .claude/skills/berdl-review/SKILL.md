---
name: berdl-review
description: Run an independent AI review of a project or research plan. Use when you want feedback without the full /submit checklist.
allowed-tools: Bash, Read, Write
---

# Project Review Skill

Run an independent AI review of a BERDL analysis project or research plan. This is a lightweight alternative to `/submit` — no pre-submission checks, no lakehouse upload. Use it to iterate on feedback during development.

## Usage

```
/berdl-review <project_id> [--type project|plan] [--reviewer claude|codex] [--model <model_id>]
```

Options:
- `--type project|plan` — Review type (default: `project`)
- `--reviewer claude|codex` — Reviewer backend (default: `claude`)
- `--model <model_id>` — Model override (default: `claude-sonnet-4-20250514` for claude, `gpt-5.4` for codex)

If no `<project_id>` argument is provided, detect from the current working directory (if inside `projects/{id}/`).

## Workflow

### Step 1: Resolve Project

1. Accept `<project_id>` from the argument, or detect from cwd if inside a `projects/` subdirectory
2. Validate that `projects/{project_id}/` exists in the repository root
3. If the directory does not exist, print an error and stop

### Step 2: Find Next Review Number

Scan the project directory for existing numbered review files:
- For project reviews: find all `REVIEW_N.md` files, pick the next number
- For plan reviews: find all `PLAN_REVIEW_N.md` files, pick the next number

If no numbered reviews exist, start at 1.

```bash
# Example: find next project review number
NEXT_N=$(ls projects/{project_id}/REVIEW_*.md 2>/dev/null | grep -oP 'REVIEW_\K[0-9]+' | sort -n | tail -1)
NEXT_N=$(( ${NEXT_N:-0} + 1 ))
```

### Step 3: Invoke Reviewer

Run `tools/review.sh` with the `--output` flag pointing to the numbered file:

```bash
bash tools/review.sh {project_id} \
  --type {type} \
  --reviewer {reviewer} \
  --model {model} \
  --output projects/{project_id}/REVIEW_{N}.md
```

For plan reviews, use `PLAN_REVIEW_{N}.md` instead.

Run this command from the repository root directory.

### Step 4: Verify Review Completion

After the reviewer subprocess completes:

1. Check that the output file was created **and is non-empty** (more than 0 bytes)
2. If it exists and is non-empty, print a success message
3. If it was not created or is empty, print an error indicating the reviewer did not produce output

### Step 5: Present Summary

Read the review file and present a brief summary to the user:
- Overall assessment (from the Summary section)
- Number of suggestions by priority (critical, important, nice-to-have)
- Key issues to address

### Step 6: Guidance

Based on the review outcome:

**If the review has no critical or important issues**:
- Note that the project looks ready for `/submit`
- Remind them that `/submit` will clear these numbered reviews and produce a final canonical `REVIEW.md`

**If the review has critical or important issues**:
- List the issues to address
- Offer to help fix them
- Suggest running `/berdl-review` again after fixes to verify

## Notes

- Reviews are numbered sequentially: `REVIEW_1.md`, `REVIEW_2.md`, `REVIEW_3.md`, ...
- Each review contains reviewer/model info in its YAML frontmatter and Review Metadata section
- Plan reviews use `PLAN_REVIEW_N.md` — these are working documents for the development process
- Running `/submit` clears all numbered `REVIEW_*.md` files and produces a fresh canonical `REVIEW.md`
- The reviewer prompt is stored at `.claude/reviewer/SYSTEM_PROMPT.md` (project) or `.claude/reviewer/PLAN_REVIEW_PROMPT.md` (plan) and is not controlled by the author

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

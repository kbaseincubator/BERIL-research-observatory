---
name: berdl-review
description: Run an independent AI review of a project or research plan. Use when you want feedback without the full /submit checklist.
allowed-tools: Bash, Read, Write
---

# Project Review Skill

Run an independent AI review of a BERDL analysis project or research plan. `/berdl-review` is the canonical review tool: each run produces a numbered `REVIEW_N.md` file with an embedded report-hash footer that lets `/submit` later confirm the review still covers the current `REPORT.md`. Use it to iterate on feedback during development before approving the project via `/submit`.

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

### Step 2: Status precondition (project reviews only)

Read `projects/{project_id}/beril.yaml` (skip silently if missing — pre-manifest projects bypass this check). For `--type project` reviews:

- **Allowed starting statuses**: `analysis`, `reviewed`, `complete`. Earlier statuses are rejected — there's no `REPORT.md` to review yet.
  - `exploration` / `proposed` / `active` → `FAIL  No REPORT.md to review yet — run /synthesize first (resume via /berdl_start)`.
- **`complete` precondition**: recompute `sha256sum projects/{project_id}/REPORT.md` and compare to `approval.report_hash` in `beril.yaml`. If mismatch:

  > "REPORT.md has changed since this project was approved ({approval.at}). Producing a review against the new report will leave the project in a confusing state: `complete` with a fresh review for an unapproved report. Demote to `analysis` first (the previous approval will be archived under `previous_approvals`) before running the new review? (y/n)"

  - **Yes**: move `approval` to `previous_approvals: []` (append), set `status: analysis`, delete both `SUBMITTED.md` and `SUBMISSION_FAILED.md` if present (audit lives in `beril.yaml`). Then continue to Step 3.
  - **No**: abort. Tell the user to re-run after deciding (either revert REPORT.md, or accept the demote next time).

For `--type plan` reviews this precondition does not apply (plans are reviewed independent of the lifecycle).

### Step 3: Invoke Reviewer

Run `tools/review.sh` — the script automatically numbers the output file (`REVIEW_1.md`, `REVIEW_2.md`, etc.) and, for project reviews, embeds a `<!-- report_hash: sha256:<hex> -->` footer recording the SHA-256 of `REPORT.md` at review time:

```bash
bash tools/review.sh {project_id} --type {type} --reviewer {reviewer} --model {model}
```

- Omit `--type` if reviewing the project (default).
- Omit `--reviewer` and `--model` if using defaults.
- The script claims the next available number immediately (race-condition safe).
- The footer is written automatically — **do not** add your own footer manually. The script also performs a TOCTOU check: if `REPORT.md` changed during review, the output file is discarded and the script aborts.

Run this command from the repository root directory.

### Step 4: Verify Review Completion

After the reviewer subprocess completes:

1. Check that the output file was created **and is non-empty** (more than 0 bytes).
2. For project reviews, confirm the file ends with the `<!-- report_hash: sha256:... -->` footer (the script writes this; if it's missing, something is wrong).
3. If the script aborted because of a TOCTOU mismatch, surface that error to the user and explain that REPORT.md changed during review — they should let the report stabilize and re-run.

### Step 5: Update beril.yaml status (project reviews only)

For `--type project` reviews against a project at `status: analysis` (or coming out of the `complete`-with-mismatch demote in Step 2), flip status to `reviewed` after the new review writes successfully:

- Update `beril.yaml`:
  - `status: reviewed`
  - `last_session_at`: current ISO 8601 timestamp.

For `reviewed` and `complete` (matching hash) starting statuses, leave the manifest unchanged — re-running `/berdl-review` only adds another opinion file. Plan reviews never touch `beril.yaml`.

### Step 6: Present Summary

Read the review file and present a brief summary to the user:
- Overall assessment (from the Summary section).
- Number of suggestions by priority (critical, important, nice-to-have).
- Key issues to address.

### Step 7: Guidance

Based on the review outcome:

**If the review has no critical or important issues**:
- Note that the project looks ready for `/submit`.
- `/submit` will use the latest review (selected by numeric N order) as the canonical record; the user's explicit approval and lakehouse upload turn it into the formal submission.

**If the review has critical or important issues**:
- List the issues to address.
- Offer to help fix them. If fixes touch `REPORT.md`, re-run `/synthesize` first (which silently demotes to `analysis`); existing `REVIEW_N.md` files become stale via hash mismatch.
- Suggest running `/berdl-review` again after fixes to produce a current review.

## Notes

- Reviews are numbered sequentially: `REVIEW_1.md`, `REVIEW_2.md`, `REVIEW_3.md`, … and are **preserved** across `/submit` runs (they form the review history). The latest by numeric N is what `/submit` consults.
- Plan reviews use `PLAN_REVIEW_N.md`; these are working documents for the development process and have no effect on the project lifecycle.
- Each review carries reviewer/model info in its YAML frontmatter and a `<!-- report_hash: sha256:... -->` footer (project reviews only) that proves which `REPORT.md` it covered.
- The reviewer prompt is stored at `.claude/reviewer/SYSTEM_PROMPT.md` (project) or `.claude/reviewer/PLAN_REVIEW_PROMPT.md` (plan) and is not controlled by the author.

## Footer invariant

Anything that produces or modifies a project `REVIEW_N.md` must preserve the report-hash footer as the final non-empty line, in the exact form `<!-- report_hash: sha256:[0-9a-f]{64} -->` (lowercase hex, sha256: prefix, exactly one occurrence in the file). If you edit a review file by hand for any reason, do not modify or duplicate the footer — `/submit` will reject the file otherwise.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

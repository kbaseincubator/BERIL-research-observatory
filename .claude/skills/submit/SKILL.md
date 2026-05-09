---
name: submit
description: Approve a project and upload it to the lakehouse. Use when the author is ready to stand behind the report and submit the project for archival.
allowed-tools: Bash, Read, Write
---

# Project Submission Skill

`/submit` is the **approval + lakehouse upload** event. It does NOT run the reviewer — produce reviews via `/berdl-review` first (you can run as many as you want with whatever model). When the user is ready to stand behind the project, `/submit`:

1. Verifies pre-submission checklist passes.
2. Verifies a *current* review (matching the latest `REPORT.md` hash) exists.
3. Asks the user to explicitly approve completeness.
4. Uploads to the lakehouse.
5. Records approval and submission marker files so anyone (the user, future agents) can see at a glance that the project landed in the lakehouse.

The lakehouse archive is the source of truth for "this project was submitted." Local files (`beril.yaml`, `README.md`, `SUBMITTED.md` / `SUBMISSION_FAILED.md`) tell the user what's happened on their machine; git is convenience.

## Usage

```
/submit <project_id>
```

If no `<project_id>` argument is provided, detect from the current working directory (if inside `projects/{id}/`).

## Hash comparison convention

All hash values stored in `beril.yaml.approval.*` and in REVIEW footer lines are prefixed with `sha256:` (e.g., `"sha256:abcdef..."`). Hash values produced by `sha256sum` (or `hashlib.sha256(...).hexdigest()`) are raw hex without the prefix. **Never compare these forms directly** — that's a category error that produces false-positive mismatches.

Use the helpers in `tools/notebook_hash.py`:

- `unprefixed(stored_value)` strips the `sha256:` prefix and returns raw hex. Bare-hex inputs pass through unchanged. Other algorithm prefixes (`sha512:` etc.) raise `ValueError`.
- `prefixed(raw_hex)` adds the `sha256:` prefix. Idempotent if input already has it.

Comparison rule, applied at every hash check site in this skill:

```
computed_hex == unprefixed(stored_value)
```

When this skill text says "compare to `approval.report_hash`" or "verify `sha256sum X == approval.foo_hash`", read it as the rule above — pass the stored value through `unprefixed()` first.

## Workflow

### Step 1: Resolve Project

1. Accept `<project_id>` from the argument, or detect from cwd if inside a `projects/` subdirectory.
2. Validate that `projects/{project_id}/` exists in the repository root.
3. If the directory does not exist, print an error and stop.

### Phase 0 — exclusion lock

`/submit` mutates approval state and uploads to a shared remote, so two concurrent invocations on the same project would race. Acquire the lock **before** any other workflow step (including the read-only checklist) so two agents running concurrently both see the second one's lock check fail rather than both passing the checks and racing into Phase 2.

- Check for `projects/{project_id}/.submit.lock`. If it exists, abort with:
  > `Error: another /submit run appears to be in progress for this project (lock at .submit.lock, created {file_mtime}). If no /submit is actually running, delete the file manually and retry.`
- Otherwise, write the lock file with the current ISO timestamp as its only content (acts as a human-readable "when did this start"). Hold it through the whole `/submit` flow.
- Delete `.submit.lock` at the end of Phase 3 (success path), at the end of Phase 3 (failure path), at any FAIL exit (including the pre-submission checklist), and on the explicit reopen abort path. **Always** clean up — never leave the lock behind.

The lock is advisory and skill-text-enforced, not OS-level. It defends against the common case (the user running `/submit` twice in quick succession) but a determined parallel run can still bypass it. Document the limitation rather than try to engineer around it.

### Step 2: Pre-submission checklist

Run these checks against the project directory and print a checklist summary:

**Critical checks** (block submission on failure):
- `README.md` exists in `projects/{project_id}/`.
- `## Research Question` section is present and non-empty in README.md.
- `## Authors` section is present with at least one entry that is not a placeholder (e.g., not "Your Name").
- `REPORT.md` exists in `projects/{project_id}/` and contains a `## Key Findings` section.

**Advisory checks** (warn but allow submission):
- `beril.yaml` exists — if present, check that `status` field is set and that `artifacts` flags are consistent with actual file existence.
- Discoveries documented in `docs/discoveries.md` — search for `[{project_id}]` tag.
- Pitfalls documented in `docs/pitfalls.md` — search for the project name or id.
- Research plan documented — `projects/{project_id}/RESEARCH_PLAN.md` exists.
- Interpretation documented — `REPORT.md` contains a `## Interpretation` section.
- References documented — `projects/{project_id}/references.md` exists.
- **Author identity match**: Run `beril user --json`. If `orcid` is non-empty, verify it appears in the README's `## Authors` section. If found, print `PASS  Your ORCID present in README Authors`. If absent, print `WARN  Your ORCID ({orcid}) not found in README Authors — confirm intentional or update the README`. If `beril user` returns no orcid, skip silently (the Phase 1 ORCID gate below will fail anyway).
- Project files committed to git — run `git status --porcelain projects/{project_id}/` and warn on uncommitted/untracked changes.
- **Notebook outputs**: each `.ipynb` in `notebooks/` should have at least one code cell with non-empty `outputs`. Warn on any with zero outputs.
- **Figures**: `figures/` directory should exist with at least one PNG.
- **Dependencies**: `requirements.txt` should exist.
- **Reproduction guide**: README.md should contain a `## Reproduction` section.
- **User-provided data**: if `user_data/` has content, print an `INFO` line with file count and total size.

Print the checklist in PASS/FAIL/WARN/INFO format. If any critical check FAILs, print failures, **release the lock**, and stop — do not enter Phase 1.

### Phase 1 — pre-flight gates

This phase performs no state changes *except* for the explicit reopen confirmation flow on hash mismatch (which has its own user prompt).

#### 1a. Status gate

Read `projects/{project_id}/beril.yaml`. If it is missing (pre-manifest project), **reject submission**:

> `FAIL  This project has no beril.yaml manifest. The new submission flow requires a manifest to record approval and submission history. Run /berdl_start on this project to scaffold a manifest (it will detect the existing artifacts), then re-run /submit.`

Pre-manifest projects cannot go through approval/upload tracking until upgraded. (Migrating legacy projects to the new manifest format is a separate effort, not handled inline by `/submit`.)

For projects with `beril.yaml`:

- `status: exploration` → `FAIL  Project is in exploration status — write RESEARCH_PLAN.md and run analysis (resume via /berdl_start) before submitting`.
- `status: proposed` → `FAIL  Project is in proposed status — run analysis notebooks (Phase C of /berdl_start) before submitting`.
- `status: active` → `FAIL  Project is in active status — run /synthesize to draft REPORT.md before submitting`.
- `status: analysis` → `FAIL  No review found — run /berdl-review first to produce a current review of the report`.
- `status: reviewed` → proceed to Phase 1b (the normal forward path through approval).
- `status: complete` → handle per the rules below (the approval/report hash check **dominates** marker handling):

##### Status `complete` resolution

  1. **First** validate the approved content against `beril.yaml.approval` along three axes:

     **Existence checks** (a missing file is a recoverability question, not a hash-mismatch):

     - `projects/{project_id}/REPORT.md` must exist. Missing → abort with `Error: REPORT.md is missing on a complete project; restore it from version control before re-running /submit.` (No automated demote path: the report is the project's primary artifact, and proceeding without it would silently archive an incomplete project.)
     - `projects/{project_id}/REVIEW.md` may be missing — Phase 3a recreates it from the numbered review.
     - `projects/{project_id}/{approval.review}` (the numbered file named in the approval, e.g. `REVIEW_3.md`) may be missing on its own (Phase 3a recovers from `REVIEW.md`), **but** if both `REVIEW.md` AND the numbered file are missing, the approved review content is unrecoverable. Treat as approved-content loss and offer the same demote prompt as the hash-mismatch branch (see below). Wording: "Both `REVIEW.md` and `{approval.review}` are missing on this complete project. The approved review content is unrecoverable. Demote to `analysis`? …"

     **Hash checks** (only on files that exist; apply the prefix convention — `unprefixed(stored)` before comparing to `sha256sum` output):

     - `sha256sum projects/{project_id}/REPORT.md` vs `approval.report_hash`.
     - `sha256sum projects/{project_id}/REVIEW.md` vs `approval.review_hash` (skip if missing).
     - `sha256sum projects/{project_id}/{approval.review}` vs `approval.review_hash` (skip if missing).
     - **Notebook hashes** (v5): compute current canonical hashes via `python -c "from tools.notebook_hash import compute_notebook_hashes; ..."` (or equivalent) and compare against `approval.notebook_hashes`. Three failure modes:
       - A notebook in `approval.notebook_hashes` whose current hash differs (or the file is missing) → mismatch, mention the specific notebook.
       - A `.ipynb` file in the current `notebooks/` set that is not in `approval.notebook_hashes` (a new notebook was added after approval) → drift, mention the specific notebook.
       - `approval.notebook_hashes` is omitted or empty (legacy approval predating v5, or project with no notebooks) → skip notebook checks; the absence of the field doesn't fail validation.

     Any hash mismatch (REPORT, REVIEW, or notebooks) OR the both-review-files-missing case triggers the **reopen prompt** (phrase the explanation according to which condition fired):

     > "{REPORT.md changed | REVIEW.md changed | REVIEW_N.md changed | both REVIEW.md and REVIEW_N.md missing | notebook(s) changed: <list of specific files>} since this project was approved ({approval.at}). The previous approval no longer reflects the current approved content. Demote status to `analysis`? Previous approval will be archived under `previous_approvals`; both `SUBMITTED.md` and `SUBMISSION_FAILED.md` will be removed (audit lives in `beril.yaml`)."

     - Yes → move `approval` to `previous_approvals: []` with an added `archived_at: "<now>"` field, set `status: analysis`, update `README.md` `## Status` to "Analysis — report drafted, awaiting `/berdl-review` and `/submit`.", delete `projects/{project_id}/REVIEW.md` if present (the canonical copy of the now-archived review is no longer current), and delete both marker files if present. Tell the user "/submit aborted; run `/berdl-review` to produce a current review, then `/submit` again." Stop.
     - No → leave alone, warn that the project is in an inconsistent state, abort `/submit`.

     Markers are not consulted in this branch — the approved content no longer matches what's on disk. Doing these checks in Phase 1a (rather than only in Phase 3a) avoids an infinite-retry loop where review drift or loss is only detected mid-flight, after Phase 2 has been skipped: without an automated demote path, the user has no way out.

  2. **Then** branch on markers (`SUBMISSION_FAILED.md` always wins on conflict):

     - `SUBMITTED.md` present **and** `SUBMISSION_FAILED.md` absent → **verify both the join key and the latest submissions entry** before treating as idempotent. (1) Parse `SUBMITTED.md`'s `**Approved at**: {iso}` line and compare to the current `beril.yaml.approval.at`; mismatch (the marker is from a prior approval that should have been cleared during a re-open) → treat `SUBMITTED.md` as stale, delete it, and fall through to the "both markers absent" branch below. (2) On match, also consult `beril.yaml.submissions[]` for the **most recent** entry with `approved_at == approval.at`. If that latest entry's `status: success` → idempotent. Print `INFO  Already submitted on {SUBMITTED.md submitted_at}; archive: {archive_key}; see SUBMITTED.md for details.` Exit 0. If the latest entry's `status: failed` (a stale `SUBMITTED.md` from an earlier success that was followed by a failed retry, plus the failure marker was then deleted somehow) → delete the stale `SUBMITTED.md` and proceed to Phase 3 only. If no submissions entry exists for this `approved_at` at all → recreate-from-marker case, accept idempotent.
     - `SUBMISSION_FAILED.md` present (regardless of `SUBMITTED.md`) → proceed to Phase 3 only (skip approval; approval is recorded and report hash is current). Phase 3's pre-upload normalization will clean up the marker conflict.
     - Both markers absent → consult `beril.yaml.submissions[]` for the **most recent** entry with `approved_at == approval.at`. If that entry's `status: success` → marker file was lost (manual deletion, filesystem mishap); recreate `SUBMITTED.md` from the recorded entry, report idempotent, exit 0. If that entry's `status: failed`, or no entry exists → upload was never attempted or last attempt failed; proceed to Phase 3 only.

#### 1b. Review-currency check (status: reviewed)

- Find the latest `REVIEW_N.md` in `projects/{project_id}/` by **numeric N order** (e.g., `REVIEW_10.md` > `REVIEW_2.md`). **Ignore** `REVIEW.md` for selection — it is the canonical-copy artifact written at approval time, not a review file produced by `/berdl-review`.
- Parse the trailing `<!-- report_hash: sha256:<hex> -->` footer. Strict rules: lowercase hex, sha256: prefix, exact form `<!-- report_hash: sha256:[0-9a-f]{64} -->`, exactly **one** occurrence anywhere in the file, must be the final non-empty line.
- Compute `sha256sum projects/{project_id}/REPORT.md` and compare:
  - No `REVIEW_N.md` found → `FAIL  No review found — run /berdl-review first` (this should already be caught by the `analysis` status gate, but defensive).
  - Latest review missing footer (legacy review predating hash tracking) → `FAIL  Review predates hash tracking — run /berdl-review for a current one`.
  - Hashes mismatch → `FAIL  Latest review (REVIEW_N.md) is on an older REPORT.md — run /berdl-review for a fresh one`.
  - Hashes match → proceed.
- Also compute `sha256sum projects/{project_id}/REVIEW_N.md` (the file selected above). Hold both hashes (`REPORT_HASH_PHASE1`, `REVIEW_HASH_PHASE1`) for the Phase 2 TOCTOU re-check.

#### 1c. Author identity check

Run `beril user --json`. If `orcid` is empty → `FAIL  No ORCID configured — run beril setup before submitting. The approval record requires a verified ORCID.` (No anonymous approvals.)

#### 1d. Present review summary

Show the latest review's filename, mtime, critical/important issue counts (parsed from the review body), and the one-line abstract (first non-blank paragraph or H1 of the review).

### Phase 2 — approval (the human event)

Reached only from `status: reviewed` with all gates passed.

#### 2a. Approval prompt

Compute `last_success` = the most recent entry in `beril.yaml.submissions[]` (if any) with `status: success`, joined to the corresponding `previous_approvals[*]` entry via `approved_at`.

- **No prior successful submission** (whether or not `previous_approvals` is non-empty — prior approvals with only failed uploads do not count):

  > "Latest review `REVIEW_N.md` is on the current REPORT.md. Critical: X, important: Y. Reviews are advisory; you can approve with open issues. As the responsible author, do you approve this project complete? (y/n)"

- **Prior successful submission exists** (re-submit will overwrite the lakehouse archive):

  > "Latest review `REVIEW_N.md` is on the current REPORT.md. Critical: X, important: Y. **This project was previously submitted on {last_success.attempted_at} (archive: {last_success.archive_key}). Approving now will replace the existing lakehouse archive.** As the responsible author, do you approve this project complete? (y/n)"

- **No** → exit cleanly. No state change, no files modified. The user can iterate via `/berdl-review` and re-run `/submit`.
- **Yes** → continue.

#### 2b. TOCTOU re-check

Immediately before writing approval artifacts, recompute `sha256sum REPORT.md` and `sha256sum REVIEW_N.md` (the file selected in Phase 1b). Compare against `REPORT_HASH_PHASE1` and `REVIEW_HASH_PHASE1` captured at the end of Phase 1b. If either has changed, abort with `Error: files changed during /submit; please re-run.` This guards the brief window between Phase 1 inspection and Phase 2 write.

#### 2c. Write approval artifacts (local filesystem)

- Compute notebook hashes (v5): call `compute_notebook_hashes(project_path)` from `tools.notebook_hash` to get a `{relpath: hex}` dict. The result is sorted by path, ready for stable YAML output. Empty dict for projects without `notebooks/`. Each value is raw hex; pass through `prefixed()` when writing to YAML.
- Update `projects/{project_id}/beril.yaml`:
  ```yaml
  status: complete
  last_session_at: "<now ISO 8601>"
  approval:
    by: "<orcid from beril user --json>"
    at: "<now ISO 8601>"
    report_hash: "sha256:<REPORT.md hex>"
    review: "REVIEW_N.md"
    review_hash: "sha256:<REVIEW_N.md hex>"
    notebook_hashes:                              # v5; omit (or write {}) if no notebooks/
      "notebooks/01_setup.ipynb": "sha256:<hex>"
      "notebooks/02_analysis.ipynb": "sha256:<hex>"
  ```
  - If a previous `approval` block existed at this point, it should already have been moved to `previous_approvals` by the `/synthesize`-on-`complete` reopen step. `/submit` does not duplicate the archival.
- Copy the approved `REVIEW_N.md` to `projects/{project_id}/REVIEW.md` (canonical filename for downstream tools / UI).
- Update `projects/{project_id}/README.md` `## Status` to:
  ```
  ## Status

  Completed — {one-line summary from REPORT.md `## Key Findings`}.
  ```
  If `REPORT.md` doesn't have a clear one-liner, write a brief summary based on the report's findings.
- **Do NOT pre-clear** existing `SUBMITTED.md` or `SUBMISSION_FAILED.md`. Markers are managed exclusively by Phase 3 success/failure handlers. This avoids ambiguity if Phase 3 is interrupted.

At this point the project is **approved locally** regardless of upload outcome. The user can `git add` and commit if they want git history to reflect the approval.

### Phase 3 — lakehouse upload (the system event)

#### 3a. Pre-upload normalization + final hash recheck

Run unconditionally (including retry-only flows that entered Phase 3 directly from Phase 1 on `status: complete`):

- **Recover from interrupted Phase 2 if needed**: check whether `projects/{project_id}/REVIEW.md` exists. If it does not (the previous run died between writing the approval block and copying the review file), recreate it: copy `projects/{project_id}/{approval.review}` (e.g., `REVIEW_3.md`) to `projects/{project_id}/REVIEW.md`. Then verify `sha256sum REVIEW.md == approval.review_hash`; mismatch means the underlying numbered review was edited since approval — abort with `Error: REVIEW_N.md changed since approval; cannot recover. Demote the project (rerun /berdl-review) and re-approve.`
- **Verify the canonical and numbered review hashes**. Recompute `sha256sum REPORT.md`, `sha256sum REVIEW.md` (the canonical copy), AND `sha256sum projects/{project_id}/{approval.review}` (the numbered file named in the approval, e.g. `REVIEW_3.md` — both files end up in the lakehouse archive). All three must match `approval.report_hash` / `approval.review_hash` / `approval.review_hash` respectively (apply `unprefixed()` to the stored values). If any has changed, abort with `Error: files changed since approval; please re-run /submit.` This guards retry paths and the brief window between Phase 2 and Phase 3, and catches the case where the canonical `REVIEW.md` is unchanged but the numbered `REVIEW_N.md` was edited.
- **Verify notebook hashes** (v5). Call `compute_notebook_hashes(project_path)` and compare against `approval.notebook_hashes` (apply `unprefixed()` to each stored value). Any mismatch, missing, or new notebook → abort with `Error: notebook(s) changed since approval: <list>; please re-run /submit.` If `approval.notebook_hashes` is omitted/empty (legacy approval or project without notebooks), skip this check.
- **Clear both marker files** before upload, so the post-upload step (success or failure) writes a clean state and an interrupt mid-Phase-3 doesn't leave a stale marker that misleads the next `/submit` run. Delete both `SUBMITTED.md` and `SUBMISSION_FAILED.md` if present. Also remove the `(Submission pending; see SUBMISSION_FAILED.md.)` parenthetical from `README.md` `## Status` if present. The `beril.yaml.submissions[]` audit log retains history; markers are reconstituted by Phase 3c per outcome.

#### 3b. Run upload

```bash
python tools/lakehouse_upload.py {project_id}
```

The script archives all project files to `s3a://cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/{project_id}/`. If the `berdl-minio` `mc` alias isn't configured, set it up first:
```bash
mc alias set berdl-minio $MINIO_ENDPOINT_URL $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
```

**Re-submission overwrite semantics**: the upload script pre-clears the remote prefix (`mc rm --recursive --force`) before `mc cp` whenever the prefix already has contents. This prevents stale files from a previous submission from contaminating the new archive when files are dropped or renamed between submissions. The brief mid-upload window during which the archive is empty is acceptable: a `complete + SUBMISSION_FAILED.md` state already signals "incomplete archive" to anyone consuming it. First-time submissions skip the clear because the remote prefix is empty.

The script's **final stdout line is a single-line JSON object** describing the outcome. Exit-code contract:

- **Exit 0** — full success. JSON schema: `{"archive_key", "file_count", "byte_total", "duration_seconds"}`. Use these values for the success record.
- **Exit 1** — hard failure (mc alias not configured, `mc cp` returned non-zero, project directory missing). No JSON on stdout; the error is on stderr. Treat as Phase 3 failure with the stderr text as `error`.
- **Exit 2** — partial success: the archive was written but `mc ls` shows fewer files than the local manifest. JSON has the success schema PLUS an `error` field describing the mismatch. The archive at `archive_key` exists but is incomplete — **treat as a Phase 3 failure** (write `SUBMISSION_FAILED.md` using the JSON's `error` field; do NOT write `SUBMITTED.md`). Surface `archive_key` in the failure marker for forensics.

In all cases, parse the JSON if exit is 0 or 2; on exit 1 fall back to the stderr text.

#### 3b.5. Post-upload integrity rehash

If `lakehouse_upload.py` returned exit 0, repeat the Phase 3a verification once more: recompute `sha256sum REPORT.md`, `sha256sum REVIEW.md`, `sha256sum projects/{project_id}/{approval.review}`, AND `compute_notebook_hashes(project_path)`. Compare each against the corresponding stored values in `approval` (apply `unprefixed()` to stored values). If any has changed since Phase 3a, the lakehouse archive may now contain content that doesn't match the recorded approval (the user edited a file during the upload window). **Treat as a Phase 3 failure**: do NOT write `SUBMITTED.md`; jump to Phase 3c failure handling with `error: "files changed during upload; archive may be inconsistent — re-run /submit"` (mention which file(s) drifted).

This is best-effort: by the time we detect drift, the archive already exists at `archive_key`. The failure marker tells the user to re-run, which will overwrite the archive with the (now hopefully stable) approved content. The advisory `.submit.lock` does not block file edits, only concurrent `/submit` runs — see Notes for the full limitation.

#### 3c. Record outcome

Markers and `beril.yaml.submissions[]` are managed exclusively by this step. `submissions[i].approved_at` is the **join key** linking each upload attempt to the corresponding `approval.at` (or `previous_approvals[*].at`).

**Ordering invariant**: always write the `beril.yaml.submissions[]` entry **first**, then the marker file. `beril.yaml` is the source of truth for the audit log; the marker is a derived view for at-a-glance user visibility. If the run dies between the YAML write and the marker write, the next `/submit` invocation rebuilds the marker from `submissions[]` (Phase 1a's "both markers absent" branch already covers this for success entries; the failure-case reconstruction is documented at the end of this section).

##### On success

1. **First**, append to `beril.yaml.submissions: []`:
   ```yaml
   submissions:
     - status: success
       attempted_at: "<iso>"
       archive_key: "{archive_key}"
       file_count: {file_count}
       byte_total: {byte_total}
       duration_seconds: {duration_seconds}
       approved_at: "{approval.at}"
   ```
2. **Then**, write `projects/{project_id}/SUBMITTED.md`:
   ```markdown
   # Project Submitted

   This project was successfully archived to the BERDL lakehouse.

   - **Project**: {project_id}
   - **Archive**: {archive_key}
   - **Submitted at**: {iso}
   - **Submitted by**: {name} ({orcid})
   - **Approved at**: {approval.at}    <!-- join key into beril.yaml -->

   ## Stats
   - Files: {file_count}, total {byte_total} bytes
   - Upload duration: {duration_seconds}s

   ## Approved content
   - `REPORT.md` hash: {approval.report_hash}
   - Review: `{approval.review}` (hash {approval.review_hash})

   ## History
   {M} previous submission(s) archived in `beril.yaml.submissions`.
   ```
3. **Then**, delete `SUBMISSION_FAILED.md` if present (defensive — should already be gone after Phase 3a's normalization).
4. Remind the user about `docs/research_ideas.md` — move the project entry from "High/Medium Priority Ideas" to "Completed Ideas" with a results summary.
5. Suggest committing all changes.

##### On failure

1. **First**, append to `beril.yaml.submissions: []` with `status: failed`, `error: "..."`, `attempted_at`, `approved_at`, and `archive_key: "{archive_key}"` when known (include for exit-2 and Phase-3b.5 failures where the upload script emitted JSON containing `archive_key`; omit for hard exit-1 failures with no archive written).
2. **Then**, write `projects/{project_id}/SUBMISSION_FAILED.md`:
   ```markdown
   # Submission Pending

   The lakehouse upload for this project failed.

   - **Project**: {project_id}
   - **Last attempt**: {iso}
   - **Error**: {error}
   - **Approved at**: {approval.at}    <!-- join key into beril.yaml -->
   - **Archive key (partial)**: {archive_key}    <!-- only if upload exit was 2 or Phase 3b.5 detected drift; archive exists but is incomplete or content-drifted -->

   Status is `complete` (the approval is recorded in `beril.yaml`).
   Re-run `/submit` to retry the upload — it will skip the approval step
   and only retry the upload.
   ```
   Omit the `Archive key (partial)` line when the failure is a hard error (exit 1) with no archive written. Include it whenever the upload script emitted JSON containing `archive_key` (exit 0 but rehash-failed in Phase 3b.5, or exit 2 partial-success).
3. Status stays `complete`. Update `README.md` `## Status` to add a parenthetical:
   ```
   ## Status

   Completed — {summary}. (Submission pending; see SUBMISSION_FAILED.md.)
   ```
   On a subsequent successful retry, the parenthetical is removed by Phase 3a.
4. Delete `SUBMITTED.md` if present (a previous successful submission is no longer the latest state).
5. Print the error and tell the user how to fix the underlying issue (e.g., `mc alias` config, network) and to re-run `/submit`.

##### Marker reconstruction from `submissions[]`

If `/submit` is invoked and finds an inconsistent state where the audit log has a recent `submissions[]` entry whose marker is missing (because the run died after step 1 but before step 2 above), reconstruct the marker on the next pass:

- Phase 1a's "both markers absent" branch reconstructs `SUBMITTED.md` from a `status: success` entry with matching `approved_at`. Already documented above.
- For a missing failure marker (last `submissions[]` entry is `status: failed` matching current `approval.at` and both markers absent), the next `/submit` proceeds to Phase 3 anyway and will overwrite either marker with its outcome — no explicit reconstruction needed; the missing failure marker doesn't trap the user. The README's "Submission pending" parenthetical may be missing in this gap; Phase 3a's normalization handles it on the next attempt.

##### Marker invariant

After Phase 3 completes, exactly one of `SUBMITTED.md` or `SUBMISSION_FAILED.md` is present, never both. If for any reason both are seen later (manual edits, partial failures outside `/submit`'s control), `SUBMISSION_FAILED.md` always wins — it represents the more recent attempt's outcome.

## Notes

- `/submit` does **not** run the reviewer. Use `/berdl-review` to produce reviews; `/submit` consumes the latest one.
- Numbered `REVIEW_N.md` files are **preserved** across submissions (they form the review history). The latest by numeric N is what `/submit` consults.
- `REVIEW.md` (no number) is the canonical copy of the approved review, written at Phase 2c. Don't edit it manually — it's overwritten on each successful approval.
- `/submit` is idempotent on retries: re-running on `status: complete` with the existing approval is safe; the workflow recognizes which phase needs to run.
- Reviews are advisory. You can approve a project with open critical or important issues — that's what the explicit y/n prompt is for. Approval is the responsible author's act of standing behind the work given everything they know.
- `/submit` uses an advisory `.submit.lock` file to serialize concurrent invocations on the same project. It's skill-text-enforced, not OS-level — don't run two `/submit` invocations against the same project at the same time. The lock does **not** prevent the user from editing project files during upload; Phase 3b.5 catches that case after the fact and marks the submission failed so a retry will re-archive the stable content.
- The lakehouse archive's `beril.yaml.submissions[]` lags by one entry — the success record for the upload that created the archive itself is written locally after the upload completes. The archive's existence at `archive_key` is the proof of submission; the missing entry is metadata only. See `PROJECT.md` "Filesystem markers" for the full design rationale.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

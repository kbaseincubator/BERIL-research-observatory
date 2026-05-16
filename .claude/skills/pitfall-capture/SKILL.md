---
name: pitfall-capture
description: Detect and document pitfalls encountered during BERDL work. Invoked by other BERDL skills when errors, retries, or data surprises occur.
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# Pitfall Capture Protocol

This skill is not user-invocable. It is referenced by BERDL skills (berdl, berdl-discover, hypothesis, submit) and should be followed whenever an issue is encountered during BERDL work.

## Where pitfalls live

Pitfalls discovered during a specific project's work go in **`projects/<id>/memories/pitfalls.md`** — that project's own memory file, append-only. The central `docs/pitfalls.md` is a frozen historical archive of pre-redirect content; it's still useful for grep/reference when checking for known gotchas, but new pitfalls are NOT written there. The future plan is for OpenViking to ingest `projects/*/memories/pitfalls.md` files for cross-project semantic retrieval; until then, agents can grep both locations.

If a pitfall genuinely doesn't belong to any specific project (e.g., a global BERDL gotcha encountered during free exploration with no current project), prefer to either (a) attach it to the most-relevant active project's memory file, or (b) ask the user where it should live. Don't write to `docs/pitfalls.md`.

## When to Trigger

Activate this protocol when any of the following occur:

1. **Query failure** — API returns an error (504, 524, 503, empty response) or SQL fails with a syntax/semantic error
2. **Incorrect results** — Data returned is wrong due to bad join key, string-vs-numeric comparison, wrong table, etc.
3. **Retry/correction cycle** — You had to substantially change your approach after an initial attempt failed
4. **Performance issue** — Query is unreasonably slow or causes OOM
5. **Data surprise** — Missing data, unexpected NULLs, coverage gaps, schema differs from documentation
6. **Environment issue** — Spark session problems, import errors, JupyterHub quirks

## Protocol Steps

### Step 1: Check for Duplicates

Check both locations, in order:

1. **Project-local first**: read `projects/<id>/memories/pitfalls.md` (if it exists) and look for a matching entry. Iteration on the same project commonly hits the same gotcha twice — checking the project's own memory first catches that.
2. **Central archive second**: grep `docs/pitfalls.md` for the same issue — many gotchas were captured there pre-redirect.

- **If already documented (in either location):** Tell the user: "This is a known pitfall — see {path}, '[Section Name]' section." Quote or summarize the relevant guidance so the user can apply it immediately. **Stop here** — do not proceed to Step 2.
- **If the user already has a related entry that's slightly off** (e.g., the original entry's framing has been refined by later understanding, or a fix has been improved): proceed to Step 2 but draft a **follow-up/correction entry** rather than a new pitfall (see Step 3 below).
- **If not documented:** Proceed to Step 2.

### Step 2: Ask the User

Ask the user this question directly:

> "I ran into an issue: **[brief description of what went wrong]**. Do you think this could have been avoided if it were documented in the pitfalls guide? If so, I'll draft an entry for your review."

Wait for the user's response.

- **If the user says no** or indicates it's not worth documenting: Acknowledge and continue with the original task.
- **If the user says yes:** Proceed to Step 3.

### Step 3: Draft the Entry

Write a draft pitfall entry. Two shapes depending on whether this is a new pitfall or a correction to an earlier one:

**New pitfall** — use this template:

```markdown
### [Descriptive Title]

**[project_id]** Explanation of the issue — what goes wrong and why.

```sql
-- WRONG: Description of the incorrect approach
<incorrect code>

-- CORRECT: Description of the correct approach
<correct code>
```

**Solution**: One-sentence actionable fix.
```

**Correction or follow-up to an existing entry** — use this template (append-only; never edit a prior entry directly):

```markdown
### Correction to "[earlier entry's title]" ({earlier_entry_date_or_marker})

**[project_id]** What we got wrong before, or what we now know that refines the earlier guidance.

```sql
-- Updated approach (replaces the earlier "CORRECT" example):
<refined code>
```

**Updated solution**: One-sentence actionable fix that supersedes the earlier solution.
```

The correction entry references the earlier entry by title (and date if helpful), but the earlier entry stays in the file unchanged. This preserves the audit trail of "what we thought when, and how our understanding evolved" — important for future readers/agents and for OV ingestion later.

Adapt the templates as needed — not every pitfall involves SQL. Some may be about Python, environment setup, or data interpretation. The code block language and content should match the actual issue.

### Step 4: Determine Placement

The destination file is `projects/<id>/memories/pitfalls.md` for the active project.

If `projects/<id>/memories/` doesn't exist, create it (mkdir -p). If `projects/<id>/memories/pitfalls.md` doesn't exist, the entry is the file's first content — start with a brief one-line preamble (e.g., "# Pitfalls — <project name>") and then the entry.

If the file does exist, append the new entry at the end. There's no rigid section structure required for a per-project file (it's much smaller than the central archive); but if the project has accumulated a meaningful number of entries (~10+), it's reasonable to add `## Section` groupings at that point.

### Step 5: Present for Review

Show the user:
1. The drafted entry text (full markdown)
2. The destination path: `projects/<id>/memories/pitfalls.md`
3. Whether it's a new entry or a correction-to-existing

Ask: "Here's the draft entry. Does this look accurate? Should I add it to `projects/<id>/memories/pitfalls.md`?"

Wait for approval. If the user wants changes, revise and re-present.

### Step 6: Write to per-project memories

On approval, append the entry to `projects/<id>/memories/pitfalls.md` using the Edit tool (or Write if the file is being created).

After writing, confirm: "Added to `projects/<id>/memories/pitfalls.md`."

Then **resume the original task** — pitfall capture should not derail the user's workflow.

## Important Notes

- **Don't interrupt flow unnecessarily.** If the issue is minor and you already know the fix, apply the fix first, then ask about documenting it. The user's primary task always comes first.
- **One pitfall at a time.** If multiple issues arise, handle each separately to avoid overwhelming the user.
- **Be specific.** Vague entries like "queries can be slow" are not useful. Include the exact table, the exact error, the exact fix.
- **Always include the project tag** (`[project_id]`) at the start of the entry. The per-project memory file is implicitly project-scoped, but the explicit tag keeps OV ingestion and cross-project search consistent.
- **Append-only.** Never edit historical entries — write a follow-up "Correction to ..." entry instead. Preserves the audit trail of evolving understanding.
- **Don't write to the central `docs/pitfalls.md`** — it's a frozen archive. New writes always go per-project.

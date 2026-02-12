---
name: pitfall-capture
description: Detect and document pitfalls encountered during BERDL work. Invoked by other BERDL skills when errors, retries, or data surprises occur.
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# Pitfall Capture Protocol

This skill is not user-invocable. It is referenced by BERDL skills (berdl, berdl-discover, hypothesis, submit) and should be followed whenever an issue is encountered during BERDL work.

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

Read `docs/pitfalls.md` and determine whether this issue is already documented.

- **If already documented:** Tell the user: "This is a known pitfall — see the '[Section Name]' section in `docs/pitfalls.md`." Quote or summarize the relevant guidance so the user can apply it immediately. **Stop here** — do not proceed to Step 2.
- **If not documented:** Proceed to Step 2.

### Step 2: Ask the User

Ask the user this question directly:

> "I ran into an issue: **[brief description of what went wrong]**. Do you think this could have been avoided if it were documented in the pitfalls guide? If so, I'll draft an entry for your review."

Wait for the user's response.

- **If the user says no** or indicates it's not worth documenting: Acknowledge and continue with the original task.
- **If the user says yes:** Proceed to Step 3.

### Step 3: Draft the Entry

Write a draft pitfall entry following the format conventions in `docs/pitfalls.md`. The entry must include:

1. **A descriptive heading** (### level)
2. **A project tag** in bold if the issue arose in a specific project context, e.g., `**[project_name]**`
3. **Brief explanation** of what the issue is and why it's a problem
4. **Code example** showing the wrong approach and the correct approach (SQL, Python, or shell as appropriate)
5. **Solution line** with actionable guidance

Use this template:

```markdown
### [Descriptive Title]

**[project_tag]** Explanation of the issue — what goes wrong and why.

```sql
-- WRONG: Description of the incorrect approach
<incorrect code>

-- CORRECT: Description of the correct approach
<correct code>
```

**Solution**: One-sentence actionable fix.
```

Adapt the template as needed — not every pitfall involves SQL. Some may be about Python, environment setup, or data interpretation. The code block language and content should match the actual issue.

### Step 4: Determine Placement

Identify which section of `docs/pitfalls.md` the entry belongs under. The current sections are:

- **General BERDL Pitfalls** — REST API, auth, schema introspection, string-typed columns
- **Pangenome (`kbase_ke_pangenome`) Pitfalls** — SQL syntax, ID formats, species-specific issues
- **Data Sparsity Issues** — Coverage gaps, EAV format, coordinate quality
- **Foreign Key Gotchas** — Orphan records, join key mismatches
- **Data Interpretation Issues** — Flag definitions, count relationships
- **JupyterHub Environment Issues** — Spark session, Java processes, CLI execution
- **Pandas-Specific Issues** — `.toPandas()`, NaN handling, type conversion
- **Fitness Browser Pitfalls** — String columns, case sensitivity, large tables
- **Genomes Pitfalls** — UUID identifiers, billion-row tables

If the issue doesn't fit any existing section, propose a new section heading.

### Step 5: Present for Review

Show the user:
1. The drafted entry text (full markdown)
2. Where it will be placed (which section of pitfalls.md, after which existing entry)

Ask: "Here's the draft entry. Does this look accurate? Should I add it to `docs/pitfalls.md` under the [Section Name] section?"

Wait for approval. If the user wants changes, revise and re-present.

### Step 6: Write to pitfalls.md

On approval, append the entry to the appropriate section in `docs/pitfalls.md` using the Edit tool. Place it at the end of the relevant section (before the `---` separator or the next section heading).

After writing, confirm: "Added to `docs/pitfalls.md` under [Section Name]."

Then **resume the original task** — pitfall capture should not derail the user's workflow.

## Important Notes

- **Don't interrupt flow unnecessarily.** If the issue is minor and you already know the fix, apply the fix first, then ask about documenting it. The user's primary task always comes first.
- **One pitfall at a time.** If multiple issues arise, handle each separately to avoid overwhelming the user.
- **Be specific.** Vague entries like "queries can be slow" are not useful. Include the exact table, the exact error, the exact fix.
- **Include the project tag** when the pitfall was discovered in the context of a specific project. This helps with traceability.
- **Update the Quick Checklist** at the bottom of pitfalls.md if the new pitfall warrants a new checklist item.

# Pitfall Capture Skill - Design Document

**Date**: 2026-02-12
**Status**: Approved

## Problem

When Claude works with BERDL data through skills (berdl, berdl-discover, hypothesis, submit), it frequently encounters issues — API timeouts, wrong join keys, string-typed numerics, missing data, etc. These issues are currently documented in `docs/pitfalls.md` only when someone manually remembers to add them. Many issues get rediscovered across sessions because they were never captured.

## Goal

Automatically detect potential pitfalls during BERDL work and offer to document them in `docs/pitfalls.md`, with the user's review and approval.

The key question to ask the user: **"Could this issue have been avoided if it were documented in the pitfalls guide beforehand?"**

## Design

### Approach: Standalone skill with cross-references

- **New skill**: `.claude/skills/pitfall-capture/SKILL.md` (not user-invocable)
- **Cross-references**: Small "Pitfall Detection" section added to each BERDL skill

### Trigger Conditions

Claude should recognize a potential pitfall when any of the following occur:

1. **Query failure** — API error (504, 524, 503, empty response) or SQL syntax/semantic error
2. **Incorrect results** — Wrong data due to bad join key, string comparison, etc.
3. **Retry/correction cycle** — Claude has to substantially change approach after initial failure
4. **Performance issue** — Unreasonably slow query or OOM
5. **Data surprise** — Missing data, unexpected NULLs, coverage gaps, schema mismatch
6. **Environment issue** — Spark session problems, import errors, JupyterHub quirks

### Deduplication

Before proposing a new pitfall:
1. Read `docs/pitfalls.md`
2. If the issue is already documented, tell the user and quote the relevant section
3. Only proceed with the capture flow if the issue is genuinely new

### User Interaction Flow

1. Detect issue during BERDL work
2. Check `docs/pitfalls.md` for existing coverage
3. If new, ask: "I hit [issue]. Could this have been avoided if it were documented in the pitfalls guide beforehand?"
4. If yes, draft entry matching the existing pitfalls.md format
5. Present draft to user for review/approval
6. On approval, append to the appropriate section in `docs/pitfalls.md`
7. Continue with the original task

### Entry Format

Matches existing pitfalls.md conventions:

```markdown
### [Descriptive Title]

**[project_tag]** Brief explanation of the issue.

\```sql
-- WRONG: What doesn't work
SELECT ...

-- CORRECT: What works instead
SELECT ...
\```

**Solution**: Actionable guidance.
```

### Cross-References

Each BERDL skill (berdl, berdl-discover, hypothesis, submit) gets:

```markdown
## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
```

## Implementation Plan

1. Create `.claude/skills/pitfall-capture/SKILL.md` with full protocol
2. Add cross-reference section to `.claude/skills/berdl/SKILL.md`
3. Add cross-reference section to `.claude/skills/berdl-discover/SKILL.md`
4. Add cross-reference section to `.claude/skills/hypothesis/SKILL.md`
5. Add cross-reference section to `.claude/skills/submit/SKILL.md`

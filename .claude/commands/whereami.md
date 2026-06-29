---
description: Show where the current line of inquiry stands and what to do next — the readiness surface for a BERIL project.
allowed-tools: Bash, Read
---

# /whereami

Thin entry point onto the deterministic readiness surface. Run the `beril whereami` CLI and
present what it returns — do not recompute or embellish the state.

## Steps

1. Run the readiness surface via Bash, passing through any argument (a project id, or nothing
   to resolve the most-recently-touched non-`complete` project by mtime):

   ```bash
   beril whereami $ARGUMENTS
   ```

2. Present its output to the user as-is. It renders:
   - the breadcrumb `explore · plan · ▸analyze · review · submit` (`▸` = current phase,
     done phases dimmed/checked),
   - a `Next:` line with the deterministic next action for the current `beril.yaml.status`,
   - the open questions and dead ends from the world-model.

3. Point the user at the `Next:` action. The phase → next-action mapping is fixed:

   | status | `Next:` |
   |---|---|
   | exploration | frame the question + competing hypotheses, then draft the plan (`/research-plan`) |
   | proposed | plan written — run the plan-review checkpoint, then start analysis (`/execute-plan`) |
   | active | execute the planned notebooks; run the discriminating query first |
   | analysis | review the report (`/berdl-review`), then `/submit` |
   | reviewed | approve and submit (`/submit`) |
   | complete | complete — start a new line of inquiry (`/suggest-research`) |

## Notes

- The CLI exits 0 even when no project resolves — it prints a friendly note instead of
  erroring. If you see that note, suggest `/berdl_start` to scaffold or pick a project.
- This is **orientation only** (drawn from the non-authoritative `research_state.json` +
  `beril.yaml` phase + the optional `claims.json` tally) — not established findings.
  `beril.yaml` is the sole lifecycle authority.
- Computed signals are words, not invented numbers; the only numbers shown are real counts
  (e.g. the claims tally, when `claims.json` is present).

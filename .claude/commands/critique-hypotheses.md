---
description: Run the read-only hypothesis-critic on a project's draft research plan to stress-test its competing hypotheses, discrimination strategy, and falsifiability before analysis.
allowed-tools: Task, Read, Bash
---

# /critique-hypotheses

Dispatch the **`hypothesis-critic`** subagent (`.claude/agents/hypothesis-critic.md`) against
a project's draft `RESEARCH_PLAN.md` and present its critique. This is the optional, on-demand
form of the plan-review checkpoint's hypothesis critique — the **pre-analysis** complement to
the post-analysis `/berdl-refute` (PR #303, when present).

It is **advisory**. The critic is read-only and writes nothing; it never changes the plan,
`beril.yaml`, or `research_state.json`, and it never gates a lifecycle transition. The
researcher and `beril.yaml` keep final authority.

## Steps

1. Resolve the target project id from `$ARGUMENTS`. If none is given, run `beril whereami` to
   find the active project, and confirm with the user before proceeding. The plan must exist
   at `projects/<id>/RESEARCH_PLAN.md` (best at `status: proposed`, i.e. the plan-review
   checkpoint). If there is no plan yet, say so and point at `/research-plan`.

2. Launch the `hypothesis-critic` subagent via the Task tool, instructing it to read
   `projects/<id>/RESEARCH_PLAN.md` (and `projects/<id>/references.md`) and critique:
   - are the rivals (H2/H3) genuinely competing, or strawmen?
   - is there a discrimination strategy that actually tells the rivals apart?
   - does each hypothesis name a falsification test **and** a decision criterion?
   - is the question answerable given the feasibility verdict?
   Pass the concrete `<id>` so the agent reads the right files.

3. Present the critic's returned text to the user verbatim under a clear heading, and frame
   it as advisory input to the plan-review checkpoint — not a verdict. Offer to iterate on
   `RESEARCH_PLAN.md` (logging a new Revision History entry) if the user wants to act on it.

## Notes

- Grounding: Chamberlin (multiple working hypotheses), Platt (strong inference / discriminate
  first), Popper-Lakatos (falsifiability), Mayo (severe testing — *unfalsified is not
  survived*; never rank by idea-stage novelty).
- The agent has only `Read`, `Grep`, and read-only `Bash` (for `berdl-query` feasibility
  probes) — no `Write`, no `Edit`. Any change to the plan is the researcher's call, made
  outside this command.

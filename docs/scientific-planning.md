# Scientific Planning & Execution

**Purpose**: Companion guide to the planning ⇄ execution workflow — what each
construct is for, how authority is divided, and the scientific ideas the design
is grounded in. For step-by-step usage see [workflow.md](workflow.md); for the
full rationale see [scientific-planning-design.md](scientific-planning-design.md).

This layer adds the **front of the research arc** — a way to *form, rank, and
sustain a line of inquiry* — to complement the existing retrospective trust and
review tooling at the back.

---

## The three-stage arc

A line of inquiry moves through three composable workflows over one shared
substrate:

```
/research-plan  ──►  /execute-plan  ──►  /berdl-review · /submit
   PLAN                 EXECUTE             REVIEW / SUBMIT (existing)
```

| Stage | Skill | Owns lifecycle | What it produces |
|---|---|---|---|
| **Plan** | `/research-plan` | `exploration → proposed` | A frozen, pre-registered `RESEARCH_PLAN.md`: a sharp question, competing hypotheses, a falsification test and decision criterion per hypothesis, a discrimination strategy, a feasibility verdict, and a per-notebook analysis spec. |
| **Execute** | `/execute-plan` | `proposed → active → analysis` | Reads the *frozen* plan, builds and runs the notebooks (the discriminating query first), then `/synthesize` → `REPORT.md`. |
| **Review / Submit** | `/berdl-review`, `/submit` | `analysis → reviewed → complete` | The existing back of the arc — independent review, then ORCID-gated approval and archival. |

`/berdl_start` keeps onboarding and the 3-door menu and now acts as a **router**:
it delegates planning to `/research-plan` and execution to `/execute-plan`, and
routes a resumed project to the right stage by `beril.yaml.status`.

**The plan is a contract, frozen before results are seen.** This is
pre-registration: predictions and disconfirming checks are committed *before* the
analysis runs. Execution may revise the plan, but a *material* change (dropping or
adding a hypothesis, moving a decision threshold, abandoning the discrimination
strategy) demotes `active → proposed` and re-triggers the plan-review checkpoint.
Minor deviations are logged inline and execution continues.

---

## The three-plane authority model

Three files carry state, with strictly separated roles. Keeping them apart is what
lets orientation stay rich without ever being mistaken for a settled result.

| Plane | File | Role | Gates? |
|---|---|---|---|
| **Authoritative** | `beril.yaml` | Lifecycle status, ORCID approval, hashes. The single source of truth for "what stage is this project in" and "was it approved". | **Yes** — sole gate authority |
| **Gate-validated ledger** | `claims.json` | Per-claim status / confidence / groundedness (from the provenance/trust layer). Read **optionally** here. | Yes (in its own layer) |
| **Non-authoritative orientation** | `research_state.json` | The cross-session **world-model**: the question, open questions, assumptions, dead ends, last checkpoint. | **Never** |

`research_state.json` carries **orientation only** — never settled findings or
hypothesis verdicts. Those live in `RESEARCH_PLAN.md` and, when present,
`claims.json`. There is no `findings` field, by design. The world-model exists to
keep a long arc coherent across sessions, not to record conclusions.

**Computed signals render as words, never fabricated numbers.** Readiness and
progress are shown qualitatively (a breadcrumb, a `Next:` line); the only numbers
ever displayed are real counts, such as a `claims.json` tally when that file
exists.

---

## The constructs and how they fit

| Construct | What it is | Where it lives |
|---|---|---|
| **`/research-plan`** | User-invocable PLAN skill. Frames the question, drafts genuine competing hypotheses *before* asking your preference, attaches a falsification test + decision criterion to each, writes the discrimination strategy, runs a cheap feasibility probe, and freezes `RESEARCH_PLAN.md`. | `.claude/skills/research-plan/` |
| **`/execute-plan`** | User-invocable EXECUTE skill. Reads the frozen plan, runs each notebook's discriminating/refuting query first, updates the world-model as understanding changes, and hands off to review. | `.claude/skills/execute-plan/` |
| **World-model** (`research_state.json`) | Per-project, non-authoritative orientation file (bounded: short lists, single-line entries). Read-modify-**write merge** so the world-model is never clobbered by a whole-block overwrite. | `projects/<id>/research_state.json` |
| **`beril state` / `beril whereami`** | CLI verbs. `state get`/`state set` read and merge the world-model; `whereami` resolves the active project and renders a deterministic readiness surface (the `explore · plan · ▸analyze · review · submit` breadcrumb, a `Next:` action, open questions, dead ends). | `beril_cli/state_cmd.py` |
| **SessionStart hook** | Best-effort shell hook that runs `beril whereami --reinject` and injects a guard-wrapped orientation block at session start. It refreshes the derived core but **never mutates world-model content and never gates**; it always exits 0 so a session can never be broken by it. | `.claude/hooks/beril-research-state.sh` |
| **hypothesis-critic** | Read-only subagent invoked at the plan-review checkpoint (also via `/critique-hypotheses`). Asks: are the rivals genuine or strawmen? is there a discrimination strategy? does each hypothesis have a falsification test + decision criterion? is the question answerable given feasibility? It critiques and writes nothing — the **pre-analysis** complement to the post-analysis `/berdl-refute`. | `.claude/agents/hypothesis-critic.md` |
| **Plan reviewer** | `tools/review.sh --type plan` uses `PLAN_REVIEW_PROMPT.md`, which now includes a *Multiple Working Hypotheses & Falsifiability* item that lints single-hypothesis plans and any hypothesis without a stated falsification test or decision criterion. | `.claude/reviewer/PLAN_REVIEW_PROMPT.md` |

The orientation guard string, rendered by `--reinject`, frames the world-model
honestly:

> `[beril cross-session context — orientation only, NOT established findings]`
> Treat the above as where we left off, not as proof. Re-open the plan/report and
> re-run checks before asserting any result as settled.

---

## Named-idea grounding

The design is a deliberate application of long-standing ideas about how inquiry
should be structured. Each idea lands on a specific construct.

| Idea | What it asks of a plan | Where it lands |
|---|---|---|
| **Chamberlin (1890) — multiple working hypotheses** | Hold several rival explanations at once; don't fall in love with one. | The Competing Hypotheses block; hypothesis-critic; the new PLAN_REVIEW item. |
| **Platt (1964) — strong inference** | Design the *crucial experiment* that excludes alternatives, and run it first. | The discrimination strategy; "discriminating/refuting query first" in `/execute-plan`. |
| **Popper / Lakatos — falsification** | A claim that nothing could refute is not science; state the disconfirming test. | The per-hypothesis falsification test; the PLAN_REVIEW "not yet testable" lint. |
| **Mayo — severe testing** | A hypothesis earns credence only by surviving a test that *could* have caught it failing; *unfalsified ≠ severely tested*. | The pre-registered decision rule; hypothesis-critic's posture. |
| **FINER / PICO — question quality** | Make the question Feasible, Interesting, Novel, Ethical, Relevant; state problem / comparator / outcome. | Research-question framing; the feasibility verdict. |
| **Kosmos — coherence decays over long arcs** | A multi-session investigation loses its thread; re-orient explicitly. | `research_state.json` world-model + SessionStart re-injection. |

### Why "survival of a disconfirming check," not persuasion

Recent agentic research systems (e.g. Google's AI co-scientist, Sakana's
approaches) often rank hypotheses by **debate or persuasiveness** — which argument
wins. This design deliberately ranks by a different criterion: **whether a
hypothesis survives a check that was designed to disconfirm it.** A persuasive
hypothesis that no one tried to refute has earned nothing; a hypothesis that
withstood its own falsification test has. That is why the plan must name, *in
advance*, the result that would prove it wrong — and why execution runs the
disconfirming query before the confirmatory cells.

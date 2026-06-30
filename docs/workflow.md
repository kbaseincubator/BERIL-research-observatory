# Research Workflow

**Purpose**: How to run a research project in the BERIL Research Observatory — from
a question to an archived report. For *why* the workflow is shaped this way and the
scientific ideas behind it, see [scientific-planning.md](scientific-planning.md);
for the data architecture see [overview.md](overview.md) and [schema.md](schema.md).

---

## The arc at a glance

A line of inquiry moves through three stages over one shared substrate. Each stage
is a skill; `beril.yaml.status` records where the project is.

```
/research-plan   ──►   /execute-plan   ──►   /berdl-review   ──►   /submit
   PLAN                  EXECUTE               REVIEW                SUBMIT
exploration→proposed   proposed→active→analysis      →reviewed            →complete
```

- **`/berdl_start`** is onboarding **and a router**: it scaffolds a project and
  sends you to the right stage. For an existing project it resumes at the stage
  matching the current `status`.
- **`/whereami`** tells you, at any point, which stage you're in and the single
  best next action.

Run the whole thing through `/berdl_start`, or invoke any stage directly.

---

## Stage 1 — Plan (`/research-plan`)

Turns a research interest + live BERDL data + literature into a **frozen,
pre-registered** `RESEARCH_PLAN.md`. Owns `exploration → proposed`.

The plan must contain:
- a sharp, answerable **research question** (FINER / PICO framing);
- **competing hypotheses** — H0/H1 plus 2–3 *genuine* rivals, drafted before you
  state a preference (Chamberlin's multiple working hypotheses);
- per hypothesis: a **prediction**, a **falsification test** (the result that would
  reject it), and a **decision criterion**;
- a **discrimination strategy** — the query/figure that tells the rivals apart;
- a **feasibility verdict** (`answerable | partial | not-answerable`) from cheap
  data probes; `not-answerable` stops and reshapes the question;
- a **per-notebook analysis spec** (goal + expected output + the discriminating
  query that runs first).

It ends at the **mandatory plan-review checkpoint** — approve, run an independent
review (`tools/review.sh --type plan` and/or the read-only **hypothesis-critic** via
`/critique-hypotheses`), or iterate. Nothing proceeds to analysis until you approve.
**The plan is a contract, frozen before any results are seen.**

---

## Stage 2 — Execute (`/execute-plan`)

Reads the *frozen* plan and runs it. Owns `proposed → active → analysis`.

- For each planned notebook, runs the **discriminating/refuting query first**
  (Platt's strong inference — try to break the hypothesis before confirming it),
  then the rest; commits after each milestone.
- Updates the cross-session **world-model** as understanding shifts (open
  questions, assumptions, dead ends) — never findings.
- **Revision loop:** a minor deviation is logged in the plan's Revision History and
  execution continues; a *material* change (dropping/adding a hypothesis, moving a
  decision threshold, abandoning the discrimination strategy) **demotes
  `active → proposed`** and re-runs the plan-review checkpoint — you can't silently
  rewrite a pre-registered contract after seeing data.
- Ends by running `/synthesize` → `REPORT.md`, then hands off to review.

---

## Stage 3 — Review & Submit

- **`/berdl-review`** — independent review of the report (`analysis → reviewed`).
  When the provenance/trust layer is present, **`/berdl-refute`** adds a post-hoc
  disconfirmation pass and the claims ledger tracks groundedness.
- **`/submit`** — ORCID-gated approval and lakehouse archival
  (`reviewed → complete`). This is the one human hard gate.

---

## Staying oriented across sessions

A long investigation loses its thread when a session ends. Three things keep it
coherent — **none of which ever gate the lifecycle**:

- **`research_state.json`** — a per-project, non-authoritative **world-model**: the
  question, open questions, assumptions, dead ends, last checkpoint. Orientation
  only.
- **`beril whereami`** / **`/whereami`** — a deterministic readiness surface: the
  `explore · plan · ▸analyze · review · submit` breadcrumb and a `Next:` action.
- **SessionStart hook** — best-effort re-injection of the world-model at session
  start, framed explicitly as "orientation only, NOT established findings."

`beril.yaml` remains the single lifecycle authority; the world-model is advisory.
Progress renders as words (a breadcrumb, a `Next:` line) — the only numbers shown
are real counts.

---

## Skills & commands

| Entry point | Stage | What it does |
|---|---|---|
| `/berdl_start` | onboarding | Orient, scaffold a project, route to the right stage |
| `/research-plan` | Plan | Frame the question + competing hypotheses → frozen `RESEARCH_PLAN.md` |
| `/critique-hypotheses` | Plan | Run the read-only hypothesis-critic on a draft plan (advisory) |
| `/execute-plan` | Execute | Build/run notebooks from the frozen plan → `REPORT.md` |
| `/whereami` | any | Show where the project stands and the next action |
| `/synthesize` | Execute | Interpret notebook outputs → `REPORT.md` |
| `/berdl-review` | Review | Independent review of the report |
| `/submit` | Submit | ORCID-gated approval + lakehouse archival |
| `/berdl`, `/berdl-query` | any | Discover and query BERDL data |
| `/literature-review` | Plan | Search the literature → `references.md` |
| `/suggest-research` | — | Propose the next high-impact research topic |

The **hypothesis-critic** subagent (`.claude/agents/hypothesis-critic.md`) is
read-only and writes nothing — the pre-analysis complement to `/berdl-refute`. The
`pitfall-capture` protocol runs automatically when errors or data surprises occur.

---

## Tutorial: your first project

1. **Start.** Run `/berdl_start`, choose "Start a new research project", and
   describe your interest — e.g. *"do species with open pangenomes occupy more
   diverse environments than those with closed pangenomes?"*
2. **Plan.** `/research-plan` explores the data, drafts competing hypotheses with a
   falsification test and decision criterion each, checks feasibility, and writes a
   frozen `RESEARCH_PLAN.md`. Review it at the checkpoint and approve.
3. **Execute.** `/execute-plan` runs each notebook's discriminating query first,
   iterates, and synthesizes `REPORT.md`. If a result forces a material change to
   the plan, it returns you to the checkpoint.
4. **Review & submit.** `/berdl-review`, then `/submit` to approve and archive.
5. **Resume anytime.** `/whereami` (or just reopening `/berdl_start`) shows the
   current stage and next step; the world-model re-orients you across sessions.

Final project layout:

```
projects/pangenome_openness_environment/
  beril.yaml            <-- lifecycle authority (status, authors, approval)
  README.md             <-- overview, status, reproduction
  RESEARCH_PLAN.md      <-- frozen plan: competing hypotheses, falsification tests
  research_state.json   <-- non-authoritative world-model (orientation only)
  REPORT.md             <-- findings, interpretation, evidence
  REVIEW.md             <-- approved review
  references.md
  notebooks/  data/  figures/
```

---

## Key references

- [scientific-planning.md](scientific-planning.md) — the design, authority model, and named-idea grounding
- [overview.md](overview.md) — data architecture and table descriptions
- [pitfalls.md](pitfalls.md) — common query issues and solutions
- [performance.md](performance.md) — query strategies for large tables
- [research_ideas.md](research_ideas.md) — backlog of research questions

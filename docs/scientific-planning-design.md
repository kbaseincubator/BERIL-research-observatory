# Design Spec: Scientific Planning ⇄ Execution Workflows

**Date:** 2026-06-29
**Status:** Proposed (design approved; pending implementation plan)
**Branch:** `feat/planning-workflow` (off `main`)
**Relationship to PR #303 (`feat/provenance-trust`):** complementary, **not stacked** (see §8)

---

## 1. Summary

The BERIL Research Observatory has a strong *retrospective* trust layer (PR #303: claims
ledger, `/berdl-refute`, evaluation-integrity rubric, passive provenance) and a single
end-to-end orchestrator skill (`berdl_start`) that walks a project through its whole
lifecycle. What it lacks is a **front of the research arc**: a way to *form, rank, and
sustain a line of inquiry* — structured competing hypotheses with falsification-first
framing, a detailed pre-registered plan, a cross-session investigation world-model, and a
"where am I / what's next" surface.

This spec separates the arc into two dedicated, composable workflows over one shared
substrate:

- a **PLAN** workflow (`research-plan` skill) that turns interests + data + literature into
  a *detailed, frozen, pre-registered* `RESEARCH_PLAN.md`, and
- an **EXECUTE** workflow (`execute-plan` skill) that *reads the frozen plan* and builds,
  runs, and writes up the analysis,

with `berdl_start` refactored into onboarding + a **router** that delegates to them. Review,
refutation, and submission remain the existing back of the arc.

## 2. Background & motivation

### 2.1 The seam already exists — it is just soft and fused

`berdl_start` is a single ~540-line orchestrator covering onboarding → environment →
inventory → project context → Phase 0 scaffold → A exploration → B plan →
**plan-review checkpoint** → C analysis → results checkpoint → D synthesis → E1 review →
E2 submit. Plan and execution are two *phases of one skill*, stitched together by the
`beril.yaml` lifecycle:

```
exploration ──► proposed ──(human OK)──► active ──► analysis ──► reviewed ──► complete
                  └── RESEARCH_PLAN.md = "the contract for what comes next" ──┘
```

`status: proposed` already means *"plan written, awaiting analysis — STOP"*; the mandatory
plan-review checkpoint already sits on the seam; `proposed → active` already *is* the
plan→execute handoff; and Entry-Door-1 resume already restarts execution from a frozen plan.
The boundary is latent in the lifecycle — this work makes it a first-class, two-entry-point
structure and raises the plan to a standard where a fresh session can execute it.

### 2.2 Gaps confirmed against this repo (not assumed)

| Gap | State on `main` | Verdict |
|---|---|---|
| Multiple working hypotheses + falsifiable predictions / decision criteria in the plan | `RESEARCH_PLAN.md` template has only a single `H0/H1` block | **Real — highest value** |
| Cross-session investigation world-model | Absent; explicitly deferred from #303 | **Real — the WS3 core** |
| "What to do next" / readiness surface | `beril.yaml` holds lifecycle state, but nothing surfaces "where am I + next move" | **Real — cheap, deterministic** |
| A dedicated execute-from-plan workflow | Phase C/D is inline prose in `berdl_start` | **Real** |
| Idea capture / triage | `suggest-research` + `docs/research_ideas.md` already cover "next topic" | **Covered — out of scope** |

### 2.3 Precedents

This is the **spec → implementation** separation already used by superpowers
(`writing-plans` → `executing-plans`) and Claude Code plan mode, applied to the scientific
arc. The reference `beril-pi-agent` project split it the same way (`/research-plan` →
`/analyze`) over the same lifecycle. Scientifically it is **pre-registration**: predictions
and disconfirming checks committed *before* results are seen — the forward complement to
#303's post-hoc `/berdl-refute`, and a direct expression of its severe-testing ethos.

## 3. Goals / non-goals

**Goals**
- Make planning and execution two distinct, resumable workflows over one substrate.
- Raise `RESEARCH_PLAN.md` to a detailed, pre-registered contract (competing hypotheses,
  predictions, falsification tests, decision criteria, per-notebook spec, feasibility).
- Persist a **non-authoritative** investigation world-model so long arcs stay coherent
  across sessions.
- Provide a deterministic "where am I / what's next" surface.
- Keep everything Claude-Code-native, stdlib-only, zero new dependencies, advisory.

**Non-goals (see §12 for the full list)**
- Re-running notebooks, reproducibility evals, lifecycle/approval/hashing changes,
  multi-specialist review panels, Pi UI, idea tournaments, or anything #303 already ships.

## 4. Architecture

```
 ┌──────────── PLAN ─────────────┐   ┌──────────── EXECUTE ───────────┐   ┌──── REVIEW/SUBMIT (exists) ────┐
 /research-plan                       /execute-plan                        /berdl-review · /submit
 interests + data + literature        reads FROZEN plan                    (+ /berdl-refute · claims when #303 present)
 + feasibility → competing             → builds/runs notebooks
   hypotheses + predictions            → /synthesize → REPORT.md
   + falsification tests
   + decision criteria
 → RESEARCH_PLAN.md (frozen)
 exploration ──► proposed ──►[plan-review + hypothesis-critic]──► active ──► analysis ──► reviewed ──► complete
                    └──────────◄ demote on MATERIAL plan revision ◄──────────┘
 ────────────────────────────────── shared substrate ──────────────────────────────────
 research_state.json (world-model) · beril state/whereami (CLI) · SessionStart hook · beril.yaml (authority)
```

`berdl_start` keeps onboarding (Phases 1–1.7), Phase 0 scaffold, the 3-door menu, and
Entry-Door-1 resume; it **delegates** Phase A/B to `research-plan` and Phase C/D to
`execute-plan`, and routes a resumed project to the right skill by `beril.yaml.status`. The
phase prose **moves into** the two skills (extract, not duplicate). The lifecycle state
machine is unchanged.

### 4.1 Three-plane authority model

| Plane | File | Role |
|---|---|---|
| Authoritative | `beril.yaml` | Lifecycle state, ORCID approval, hashes. Sole gate authority. |
| Gate-validated ledger | `claims.json` (#303) | Per-claim status / confidence / groundedness. Optional here. |
| Non-authoritative orientation | `research_state.json` (this PR) | The world-model. Never gates. |

`research_state.json` carries *orientation only* — never settled findings or hypothesis
verdicts (those live in `RESEARCH_PLAN.md` and, when present, `claims.json`).

## 5. Decisions (recorded)

1. **Extract + route**, not add-alongside or enrich-in-place. One source of truth; both
   skills independently invocable; `berdl_start` orchestrates.
2. **Detailed-intent, flexible-code contract.** The plan pins the science and the decision
   rules; execution owns the exact code and may revise the plan (logged + re-checkpoint).
3. **Both workflows in this PR** (larger than "moderate"; each piece kept minimal).
4. **Revision loop:** minor deviations logged inline and execution continues; a *material*
   change (drop/add a hypothesis, move a decision threshold, abandon the discrimination
   strategy) demotes `active → proposed` and re-triggers the plan-review checkpoint.
5. **Feasibility** reuses `berdl`/`berdl-query` cheap probes (`DESCRIBE`, bounded coverage);
   no new probing engine.
6. **Dedicated `research_state.json`**, not extending `provenance.json` or `beril.yaml`.
   This is what keeps the PR standalone (§8).
7. **Standalone off `main`, not stacked on #303.**

## 6. Detailed design

### 6.1 PLAN workflow — `.claude/skills/research-plan/SKILL.md` (user-invocable)

Owns `exploration → proposed`. Frontmatter follows the repo convention
(`name`, `description` = "does X. Use when Y.", `allowed-tools`, `user-invocable: true`).

Inputs: the researcher's interest; live data discovery (`berdl` / `berdl-query`); literature
(`literature-review` → `references.md`). Steps:

1. Frame a sharp, answerable **research question** (FINER/PICO: problem / comparator /
   outcome).
2. Draft **competing hypotheses** (H0, H1, + 2–3 genuine rivals — "not strawmen") *before*
   asking the user's preference.
3. For each hypothesis, write a **prediction**, a **falsification test** (the single result
   that would reject it), and **decision criteria** (the threshold/comparison that
   adjudicates).
4. Write the **discrimination strategy** (the query/figure that tells the rivals apart) and
   a **confidence prior** (high/med/low + why; cite literature for high).
5. Run a **feasibility** check via `berdl-query` cheap probes; record
   `answerable | partial | not-answerable` + limiting tables. `not-answerable` stops and
   reshapes the question before any plan is frozen.
6. Write the **Analysis Plan** as a per-notebook spec (goal + expected output + the
   discriminating/refuting query that notebook runs first).
7. Write `RESEARCH_PLAN.md` (template §6.1.1), seed `research_state.json` via
   `beril state set` (`question`, `assumptions`, `open_questions`), set `beril.yaml`
   `status: proposed`,
   `artifacts.research_plan: true`, update `README.md`, commit.
8. **Plan-review checkpoint** (kept from `berdl_start`): present the plan; offer
   (a) approve → execute, (b) independent review (`tools/review.sh --type plan` and/or the
   **hypothesis-critic agent**, §6.5), (c) iterate. Do not advance to execute until (a).

#### 6.1.1 Enriched `RESEARCH_PLAN.md` template (the frozen contract)

```markdown
# Research Plan: {Title}

## Research Question
{FINER/PICO-framed: the problem, the comparison, the outcome — sharp and answerable}

## Competing Hypotheses
- **H0** (null): {…}
- **H1**: {…}
- **H2** (rival): {a genuine alternative the available data could distinguish — not a strawman}
- **H3** (rival, optional): {…}

### Per-hypothesis predictions, falsification & decision criteria
| Hypothesis | Prediction (what we'd observe if true) | Falsification test (result that rejects it) | Decision criterion (threshold/comparison) |
|---|---|---|---|
| H1 | {…} | {…} | {…} |
| H2 | {…} | {…} | {…} |

## Discrimination Strategy
{The specific query/figure result that would tell H1 / H2 / H3 apart.}

## Confidence Prior
{HIGH / MEDIUM / LOW + why. Cite literature for HIGH. Compared against the posterior at synthesis.}

## Literature Context
{What's known, key references (references.md), identified gaps.}

## Feasibility
- **Verdict**: {answerable | partial | not-answerable}
- **Limiting tables / coverage**: {what was probed and found}

## Query Strategy
### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| {table} | {why} | {count} | {how to filter} |
### Performance Plan
- **Tier**: {local bounded Spark SQL / JupyterHub Spark SQL}
- **Estimated complexity**: {simple / moderate / complex}
- **Known pitfalls**: {from pitfalls.md}

## Analysis Plan
### Notebook 1: {name}
- **Goal**: {what it establishes}
- **Discriminating/refuting query (run first)**: {the crucial test for this step}
- **Expected output**: {CSV/figures}
### Notebook 2: …

## Pre-registered Decision Rule
{How evidence is adjudicated at synthesis:
 strong-support > refuting and signal not swamped → H1 supported, with caveats;
 refuting ≥ strong → H0 not rejected;
 balanced → mixed evidence (say so plainly).}

## Expected Outcomes
- **If H1 supported**: {interpretation}
- **If H0 not rejected**: {interpretation}
- **Potential confounders**: {list}

## Revision History
- **v1** ({date}): Initial plan

## Authors
{name, affiliation, ORCID}
```

### 6.2 EXECUTE workflow — `.claude/skills/execute-plan/SKILL.md` (user-invocable)

Owns `proposed → active → analysis`. Steps:

1. Read the **frozen** `RESEARCH_PLAN.md` (the contract) and `research_state.json`
   (orientation). Confirm the plan-review checkpoint was approved.
2. `beril.yaml` `status: proposed → active`.
3. For each notebook in the Analysis Plan: create the numbered notebook, **run the
   discriminating/refuting query first** (Platt: crucial test before confirmatory cells),
   produce the expected output, execute cells, commit. Capture pitfalls via
   `pitfall-capture`. Update the world-model (`open_questions` / `assumptions` / `dead_ends`)
   as understanding changes (`beril state set`).
4. **Revision loop:** minor deviation → append to Revision History, continue. Material
   change to the pre-registered contract → demote `active → proposed`, record the reason,
   re-run the plan-review checkpoint.
5. **Results checkpoint** (kept from `berdl_start`): present key results before synthesis.
6. `/synthesize` → `REPORT.md` (`status: active → analysis`, handled by `synthesize`).
7. Hand off to the existing back: `/berdl-review` + `/submit` (and `/berdl-refute` + the
   claims ledger when #303 is present).

### 6.3 `berdl_start` router changes — `.claude/skills/berdl_start/SKILL.md` (edit)

- Phase A/B section body → "invoke `/research-plan`" (the detailed steps move into that
  skill; the `RESEARCH_PLAN.md` template moves there too).
- Phase C/D section body → "invoke `/execute-plan`".
- Entry-Door-1 resume table routes by status: `exploration`/`proposed` → `/research-plan`;
  `active` → `/execute-plan`; `analysis` → `/berdl-review`; `reviewed` → `/submit`
  (unchanged endpoints).
- The mandatory plan-review checkpoint and the "never skip it" principle are preserved (they
  now live in `research-plan`, referenced from `berdl_start`).

### 6.4 Shared substrate — `beril` CLI + world-model

#### 6.4.1 `research_state.json` (new, per-project, non-authoritative)

```json
{
  "project": "string",
  "updated_at": "ISO-8601 Z (server-stamped by the CLI)",
  "phase": "string (derived from beril.yaml.status)",
  "step": "explore|plan|analyze|review|submit (derived)",
  "claims": { "total": 0, "supported": 0, "refuted": 0 },
  "question": "string (<=240 chars, single line)",
  "open_questions": ["string (<=8 entries, <=160 chars each)"],
  "assumptions": ["string (<=8, <=160)"],
  "dead_ends": ["string (<=8, <=160)"],
  "last_checkpoint": "string (<=160)"
}
```

Bounds (from the reference): `MAX_LIST = 8`, `MAX_ENTRY = 160`, `MAX_QUESTION = 240`.
`claims` is included only if `claims.json` exists; otherwise omitted. No `findings` field —
ever.

#### 6.4.2 CLI verbs (`beril_cli/state_cmd.py`, dispatched from `cli.py`)

Convention: stdlib argparse, zero deps, `run_<verb>(args: argparse.Namespace) -> int`, lazy
import inside the matching `if args.command == ...` branch, JSON to stdout, diagnostics to
stderr, exit 0 = success / 1 = failure / 2 = usage.

- **`beril state get <project>`** → prints `research_state.json` (or `{}` if absent). Exit 0.
- **`beril state set <project> --json '<obj>'`** → read-modify-write **merge**: overlay
  supplied keys (`open_questions`/`assumptions`/`dead_ends`/`question`/`last_checkpoint`)
  onto the current file (supplied replaces that field; absent leaves prior), recompute the
  derived core (`phase` from `beril.yaml`, `claims` from `claims.json` if present), clamp to
  bounds, server-stamp `updated_at`, write, and print the result. Exit 0; exit 2 on bad JSON
  or unknown project. (Merge-before-write because a whole-block overwrite would clobber the
  world-model — the documented reference pitfall.)
- **`beril whereami [project] [--reinject] [--json]`** → resolve the project (the arg, else
  the most-recently-touched non-`complete` `projects/*/beril.yaml` by mtime). Read
  `beril.yaml` (phase), `claims.json` (tally if present), `research_state.json`
  (orientation). Render:
  - default → human readiness surface: the breadcrumb
    `explore · plan · ▸analyze · review · submit` (▸ = current, ✓/dim = done), a `Next:`
    line, and the open-questions / dead-ends.
  - `--reinject` → a guard-wrapped orientation block for the SessionStart hook, and refresh
    the derived core into `research_state.json` as a side effect.
  - `--json` → a machine-readable object.
  Exit 0 always (prints a friendly note if no project resolves, so the hook never breaks).

Phase → step → next-action table (deterministic):

| status | step | `Next:` |
|---|---|---|
| exploration | explore | frame the question + competing hypotheses, then draft the plan (`/research-plan`) |
| proposed | plan | plan written — run the plan-review checkpoint, then start analysis (`/execute-plan`) |
| active | analyze | execute the planned notebooks; run the discriminating query first |
| analysis | review | review the report (`/berdl-review`), then `/submit` |
| reviewed | submit | approve and submit (`/submit`) |
| complete | done ✓ | complete — start a new line of inquiry (`/suggest-research`) |

#### 6.4.3 SessionStart hook — `.claude/hooks/beril-research-state.sh` (+ `settings.json`)

Reads the hook JSON payload from stdin and runs `beril whereami --reinject` (which resolves
the active project itself, by mtime), emitting the guard-wrapped orientation as
`additionalContext`.
Strictly best-effort: swallows all errors, always `exit 0`. It refreshes the derived core
and surfaces orientation; it **never mutates world-model content and never gates**. Registered
under `hooks.SessionStart` in `.claude/settings.json` (which has no `hooks` key on `main`
today, so this PR creates the array).

Guard strings (rendered by `--reinject`):
> `[beril cross-session context — orientation only, NOT established findings]`
> … (the orientation) …
> `Treat the above as where we left off, not as proof. Re-open the plan/report and re-run
> checks before asserting any result as settled.`

### 6.5 Hypothesis-critic agent — `.claude/agents/hypothesis-critic.md` (new)

A read-only, isolated subagent invoked at the plan-review checkpoint (and optionally via a
`/critique-hypotheses` command). Reads `RESEARCH_PLAN.md`'s hypotheses block and critiques:
are the rivals genuinely competing or strawmen? is there a discrimination strategy? does each
hypothesis have a falsification test + decision criterion? is the question answerable given
the feasibility verdict? Returns critique text; writes nothing. This is the **pre-analysis**
complement to #303's **post-analysis** `/berdl-refute`. Frontmatter: `name`, `description`,
read-only `tools` (Read, Grep, Bash for `berdl-query`), optional `model`.

### 6.6 Plan reviewer addition — `.claude/reviewer/PLAN_REVIEW_PROMPT.md` (edit)

Add a "multiple working hypotheses + falsifiability" rubric item: flag single-hypothesis
plans and plans whose hypotheses lack a stated falsification test / decision criterion —
*"a plan that cannot state what result would refute its hypothesis is not yet testable."*
Additive to #303's Evaluation-Integrity item.

### 6.7 Grounding doc — `docs/scientific-planning.md` (new)

User-facing companion (mirrors #303's `docs/provenance-and-trust.md`): names the ideas
(§9) and the three-plane authority model, and explains why each construct exists. May
consolidate with this spec at implementation time.

## 7. Lifecycle & authority guarantees

- `beril.yaml` remains the **sole lifecycle authority**; `research_state.json` never gates a
  transition.
- **No new hard gate.** The ORCID `/submit` gate is untouched.
- Computed signals are rendered as **words**, never fabricated numbers. (The only numbers
  shown are real counts, e.g. the claims tally.)
- **No notebook re-running**; the notebook-with-outputs remains the reproducible record.

## 8. Dependencies & PR strategy

**Standalone off `main`. Not stacked on #303.**

- The *only* thing consumed from #303 is `claims.json`, read **optionally** — absent →
  the claims tally is omitted; everything else works unchanged.
- All other touched files either are **new** or **already exist on `main`**
  (`berdl_start/SKILL.md`, `PLAN_REVIEW_PROMPT.md`, `settings.json`, `cli.py`, `PROJECT.md`).
  Nothing requires a file or symbol introduced by #303.
- **Additive merge-coordination** (not a dependency) in three files both PRs edit —
  `PLAN_REVIEW_PROMPT.md` (separate rubric items), `settings.json` (separate `SessionStart`
  entries), `cli.py` (separate dispatch branches). These resolve cleanly in either merge
  order; flagged in the PR body.
- **Soft references:** `/berdl-refute`, `beril claims`, and the eval-integrity rubric are
  #303-only. Skill/agent prose references them as "complementary, when present" and points
  the execute→review handoff at `/berdl-review` + `/submit` (present on `main`).
- Stacking is rejected: #303 is a draft, so stacking would block this self-contained PR
  behind an unmerged branch. The dedicated `research_state.json` (Decision 6) is what
  enables the standalone property.

## 9. Named-idea grounding map

| Idea | Where it lands |
|---|---|
| Chamberlin 1890 — multiple working hypotheses | Competing Hypotheses block; hypothesis-critic; PLAN_REVIEW item |
| Platt 1964 — strong inference | Discrimination strategy; "discriminating query first" in execute |
| Popper / Lakatos — falsification | Per-hypothesis falsification test; PLAN_REVIEW "not yet testable" lint |
| Mayo — severe testing | Pre-registered decision rule; hypothesis-critic ("unfalsified ≠ survived") |
| FINER / PICO — question quality | Research-question framing; feasibility verdict |
| Kosmos — coherence decays over long arcs | `research_state.json` world-model + SessionStart re-injection |
| Google AI co-scientist / Sakana | Contrast targets (we rank by survival, not persuasion) — noted in grounding doc |

## 10. File / construct map

| File | New/Edit | Construct | Grounding |
|---|---|---|---|
| `.claude/skills/research-plan/SKILL.md` | New | skill | Chamberlin, Platt, FINER/PICO |
| `.claude/skills/execute-plan/SKILL.md` | New | skill | Platt (crucial test first) |
| `.claude/agents/hypothesis-critic.md` | New | agent | Chamberlin, Mayo |
| `.claude/commands/whereami.md` | New | command | workflow UX |
| `.claude/commands/critique-hypotheses.md` | New (optional) | command | Chamberlin |
| `.claude/hooks/beril-research-state.sh` | New | hook | Kosmos |
| `beril_cli/state_cmd.py` | New | CLI | three-plane authority |
| `beril_cli/cli.py` | Edit | CLI dispatch | — |
| `tests/test_cli_state.py` | New | tests | — |
| `.claude/skills/berdl_start/SKILL.md` | Edit | router | — |
| `.claude/reviewer/PLAN_REVIEW_PROMPT.md` | Edit | reviewer | Popper/Mayo |
| `.claude/settings.json` | Edit | hook registration | — |
| `docs/scientific-planning.md` | New | docs | all named ideas |
| `PROJECT.md` | Edit (light) | docs | — |

## 11. Testing strategy

`pytest` mirroring `tests/test_cli_user.py` (no `CliRunner`; call `run_<verb>()` with a
hand-built `argparse.Namespace`; `tmp_path` + `monkeypatch` for the project dir; `capsys`
for output; assert return codes). Cases:

- `state get` on absent file → `{}`, exit 0.
- `state set --json` → merge semantics (supplied replaces, absent preserved), clamp
  (lists truncated to 8, lines to 160, question to 240), `updated_at` stamped.
- `state set` recomputes the derived core from `beril.yaml`; omits `claims` when
  `claims.json` is absent and includes it when present.
- `whereami` → correct breadcrumb + next-action per status; resolves active project by mtime
  when omitted; exit 0 with a note when no project resolves; `--reinject` emits the guard
  block and refreshes the core.

Skills, agent, hook, and prose edits verified by inspection.

## 12. Out of scope

Idea-tournament / heavy idea triage (covered by `suggest-research`); a `berdl_feasibility`
probing engine; anything in #303 (claims ledger, `/berdl-refute`, eval-integrity rubric,
provenance — reuse/reference, never rebuild); Pi UI (cockpit / cards / HUD); session reroll /
bookmarking; the off-the-record "aside"; reproducibility evals or notebook re-running;
lifecycle / approval / hashing changes; a multi-specialist review panel; RO-Crate / new
attestation files.

## 13. Conventions to match

- **SKILL.md frontmatter:** `name` (= dir), `description` ("does X. Use when Y."),
  `allowed-tools` (comma string), `user-invocable: true` for slash-invocable skills.
- **CLI:** stdlib argparse, `dependencies = []`, `run_<verb>(args) -> int`, lazy dispatch in
  `cli.py:main()`, `from __future__ import annotations`, JSON→stdout / messages→stderr.
- **Tests:** top-level `tests/`, `argparse.Namespace` + `capsys` + `monkeypatch`/`tmp_path`,
  no `CliRunner`.
- **Layout:** flat per-project files under `projects/<id>/`; `beril.yaml` is the lifecycle
  authority.

## 14. Open questions / risks

- **PR size:** both workflows + substrate is larger than "moderate." Mitigation: each piece
  is small; the diff is dominated by prose (two skills + the moved template) and one CLI
  module.
- **`berdl_start` refactor risk:** extracting Phase A/B and C/D from a load-bearing skill
  must preserve the "never skip the plan-review checkpoint" guarantee and Entry-Door-1
  resume. Mitigation: move prose verbatim into the new skills, reference (don't reword) the
  checkpoint.
- **Hook proliferation:** if #303 also lands, two `SessionStart` hooks run per session. Both
  are best-effort/exit-0; acceptable. A future cleanup could share project-resolution logic.

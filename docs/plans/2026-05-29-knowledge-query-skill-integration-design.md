# Knowledge-layer query integration with skill workflows — design

**Date:** 2026-05-29
**Status:** approved (brainstorm), pending implementation plan
**Branch:** `context-kg-wiki`

## Problem

The OpenViking context layer (`observatory_context/` + `knowledge/scripts/`)
ships a rich query surface — `find`, `grep`, `glob`, `ls`, `tree`, `stat`,
`relations`, `overview`, `read` — documented in the `knowledge-context` skill.
But it is **not load-bearing** in the research workflows: `berdl_start`,
`suggest-research`, `synthesize`, and `pitfall-capture` still answer
cross-project questions by brute-force file reads (e.g. "`ls projects/` and read
every README", full-file reads of `docs/pitfalls.md`, db-name `grep`). The PR
added only thin advisory notes.

Two problems follow:

1. **The layer teaches vocabulary, not judgment.** The skill documents each
   primitive but not *when `find` is the wrong tool*, *how to refine a query
   that returned too much / too little*, *how to drill from a pointer into the
   source*, or *when to stop*. Skills can't use the toolkit the way a person
   uses bash.
2. **No graceful degradation.** `knowledge_query.py` hard-exits (`SystemExit`)
   the moment the server is unreachable, so any skill that depends on it breaks
   when OpenViking is down — unacceptable for workflows meant to run anywhere.

## Goals

- Make the knowledge layer **load-bearing** in all read-heavy skills, without
  each skill re-implementing query logic.
- Teach skills to use the **whole** query surface with judgment — pick the right
  primitive, iterate/refine, drill down, follow relations, know when to stop.
  Flexible like a bash toolkit, not a single canned command.
- **Graceful fallback lives in the query layer**, not in each skill: when the
  server is unreachable, search degrades to local keyword search and still
  returns results, clearly labeled.

## Non-goals (this iteration)

- Ingesting the `atlas/` synthesis layer (deferred — see
  `atlas-ingest-deferred` decision).
- Automated / CI ingestion (ingestion stays a manual writer-host operation).
- An assembled "context brief" / digest mode — the entrypoint returns **ranked
  file pointers** (a map), and skills read the source.
- Any change to the write/ingest path beyond what fallback search reuses.

## Deployment context

OpenViking is a client/server HTTP service. Clients are thin: they set
`OPENVIKING_URL` (+ `OPENVIKING_API_KEY` for remote/prod) and connect over HTTP.
Model keys (embeddings, VLM) live server-side in `ov.conf`. Read queries are
stateless and safe to share against one remote server; only ingestion is
per-machine (manifest-bound, one designated writer). This design therefore
behaves identically against a local or shared-remote server — the only runtime
check that matters is "is `OPENVIKING_URL` reachable?", and that is precisely
the fallback trigger.

## Design

### Component 1 — graceful fallback (query layer, code)

New module `observatory_context/fallback.py` plus a change to
`knowledge_query.py`'s `main()` so an unreachable server routes search to local
search instead of exiting.

- **Trigger:** reuse the existing reachability probe
  (`openviking_client._ensure_reachable`). Today it raises `SystemExit`; the CLI
  will instead catch the unreachable case for search commands and dispatch to
  the local searcher. (Refactor the probe to return a boolean / raise a typed
  `ServerUnreachable` the CLI can branch on, rather than `SystemExit`.)
- **Corpus parity:** the local searcher reuses `selection.py`
  (`iter_project_dirs` + `select_project_files` + `select_project_memories` +
  `select_central_docs`) so it searches **exactly the corpus the server would
  hold** — `projects/<id>/{curated files, memories/*.md}` + `docs/*.md`. It
  never reads un-ingested content (`data/`, `figures/`, notebooks).
- **URI ↔ path mapping** (already implied by `config.py`/`selection.py`):
  - `viking://resources/projects/<id>/...` ↔ `projects/<id>/...`
  - `viking://resources/docs/<slug>/` ↔ `docs/<slug>.md`
  Local results carry the same `viking://` URIs, so a skill reads them
  identically regardless of which path produced them.
- **Per-command fallback semantics:**
  | Command | Degraded behavior |
  |---|---|
  | `find` | keyword search over the selection corpus; rank by match heuristic; same result shape (`uri`, `score`, `abstract`=snippet) |
  | `grep` | local ripgrep-equivalent over the selection corpus |
  | `read`, `overview` | map URI → local file and read it |
  | `relations`, `glob`, `ls`, `tree` | no local equivalent worth building → clean "unavailable in degraded mode" notice |
- **Labeled but transparent:** degraded results include `degraded: true` +
  `source: "local"`, and a stderr banner: *"⚠ knowledge layer unavailable —
  used local keyword search; recall may be less complete."* Exit code 0; never
  a traceback.

### Component 2 — `knowledge-context` becomes an agentic query playbook (guidance)

Keep the existing reference (resource layout, per-command docs, relations,
refresh, config, common workflows). Add the judgment layer, in
**principles-plus-worked-examples** style (not a rigid flowchart):

- **Choosing & sequencing primitives** — the principle behind the table, incl.
  *when `find` is the wrong tool*: need exhaustiveness → `grep`; enumeration →
  `glob`/`ls`; an exact token (gene, ORCID, error string) → `grep`; exploring an
  unfamiliar concept → `find`.
- **The retrieval loop** — the follow-up moves:
  - *Too many / vague* → tighten terms, add `--score-threshold`, scope
    `--project`/`--target-uri`.
  - *Too few / zero* → broaden terms, drop threshold, widen scope, or switch
    `find` → `grep` on a defining token.
  - *Promising hit* → `overview` → `read` the specific file → `relations` to
    walk to neighbors.
  - *Stop when* you can name the source files that answer the question, or two
    refinements surface nothing new.
- **Drill-down chains** — 3–4 worked multi-step examples (e.g. "what's known
  about X" → broad `find` → `read` top REPORT → `relations` → `read` neighbor's
  FINDINGS; "has anyone done Y" → `find`, if vague `grep` a defining term,
  `glob` to confirm; "pitfalls for database Z" → `grep` Z across `docs/pitfalls`
  + `projects/*/memories/pitfalls.md` → `read` matched sections).
- **Degraded mode** — how to read the banner: local search is keyword-only, so
  prefer exact tokens and treat recall as partial; still read the source.
- **Calling convention for other skills** — a short, stable contract any
  read-heavy skill references: *"Before reading project files to answer a
  cross-project question, consult the knowledge layer (see this skill); treat
  results as a map and read the source; if degraded, verify."*

### Component 3 — wire read-heavy skills (pointer + one seed example each)

Single source of truth: the judgment/loop lives once in `knowledge-context`.
Each consuming skill adds a short step at its natural moment, linking to it and
supplying **one** domain-specific seed query:

- **berdl_start** — Phase 0 "what's been done" (`find` instead of reading every
  README) and Phase A "what's known / pitfalls" (`find`/`grep` over docs +
  memories before full reads).
- **suggest-research** — `find` for gaps + prior art before proposing; upgrade
  the existing advisory note to a real step.
- **synthesize** — `find` related prior work to compare against and cite.
- **pitfall-capture** — `find`/`grep` to dedup before writing.
- **General rule** — a one-line convention in `knowledge-context` that any skill
  reading project files can reference, so future skills inherit it without
  bespoke wiring.

Skills contribute only their seed query; they never embed the loop (no drift).

## Testing

- Fallback path: server unreachable → `find`/`grep` return local results with
  `degraded: true` + banner + exit 0 (no traceback).
- Result-shape parity: degraded `find` output matches server `find` output shape
  so callers don't branch.
- URI ↔ path round-trip mapping for projects + docs.
- Corpus reuse: local search reads only the selection corpus, never
  `data/`/`figures/`/notebooks.
- `read`/`overview` degraded path resolves URI → local file.
- `relations`/`glob`/`ls`/`tree` degraded path emits the unavailable notice, not
  a crash.

## Risks & mitigations

- **Local recall is weaker than semantic.** Mitigated by the explicit banner +
  guidance to prefer exact tokens in degraded mode; this is a graceful
  degradation, not a silent one.
- **Guidance drift across skills.** Mitigated by single-source playbook +
  pointer-only references.
- **Probe refactor touches the hard-fail path.** Keep the existing clean-exit
  behavior for ingest (write path still needs a reachable server); only the
  read/search CLI gains the fallback branch.

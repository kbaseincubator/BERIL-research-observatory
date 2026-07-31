# Provenance & Trust

How BERIL records *how* a result was produced (provenance) and *how well* its
claims are supported (trust). Everything here is **advisory** and sits behind the
one human hard gate — the ORCID-bound `/submit` approval. The design borrows
recognized ideas so each artifact is trackable by name, but adopts the *idea*, not
a heavyweight dependency.

## The pillars

### 1. Trust — a claims–evidence ledger

- Each Key Finding can be written as a falsifiable **claim** with typed
  **evidence** pointers (notebook cell, query, figure, paper) and a confidence
  **word**, in a `## Claims` block in `REPORT.md`. `beril claims build` mirrors it
  to `claims.json`.
- This is a minimal **nanopublication** / **Model Card** shape — assertion +
  evidence + attribution (Mitchell et al. 2019, *Model Cards*; Gebru et al. 2018,
  *Datasheets for Datasets*; Kuhn et al., *nanopublications*).
- **Resolved artifact support** is a conservative computed axis: only notebook
  or durable-query pointers that actually resolve can count. Multiple artifacts
  stay in one default stream unless the report explicitly labels different
  `[stream: ...]` groups; filenames never imply scientific independence.
  **`confidence_mismatch`** flags written `high`/`medium` confidence without
  multiple explicit resolved streams. A stream label is author metadata, not
  independent scientific verification.
- Confidence is a **word, never a number** — following **GRADE** (which replaced
  numeric scores with an ordinal word ladder) and the LLM-calibration literature
  (Guo et al. on ECE; Steyvers/Leng on overconfidence): an artifact-derived word
  avoids a false precision BERIL has no held-out outcomes to back. The canonical
  definition of the words `high`/`medium`/`low` for this repo is
  `atlas/methods/evidence-grading.md` (graded by independent evidence streams), and
  `science.py` uses the same ladder. Status and confidence remain author
  assertions; `supported` and `refuted` are not independently proven by the CLI.
  The generated schema and migration contract are documented in
  [`claims-json-schema.md`](claims-json-schema.md).

### 2. Runtime provenance — a record of how a session ran

- A per-project `runtime.json` history (schema `2.0`), shaped loosely to **W3C
  PROV** (entity = the project, activity = a session, agent = beril + the model),
  written passively by a `SessionStart` hook. It captures, best-effort: the **beril
  version**, the **model** (e.g. `claude-opus-4-8`) and effort, the session
  id / source / permission mode, the **git sha** of the code, the **tenant** (the
  observatory's fixed warehouse), the **actor** (shell user + the ORCID from
  `beril.yaml`), and a **documented datasets snapshot** (BERDL collections +
  tables parsed from the report's `## Data` section, with the report hash and
  observation time). Every field is omitted when absent, never
  fabricated; the whole writer always exits 0. This is the **Sumatra / noWorkflow**
  passive-capture pattern — record what produced the work, don't re-run it. Named
  `runtime.json` (not `provenance.json`) because on `main` "provenance" already
  means *source / lineage* (`data/PROVENANCE.md`, the Atlas's source frontmatter);
  this is the narrower runtime/execution facet.
- Each `sessions[]` entry is one atomic observation. A new session never inherits
  another session's model, effort, activity, actor, git state, or documented
  datasets. Repeating the same effective session snapshot is a no-op. A corrupt
  or non-schema-2 file is replaced by a fresh atomic history rather than merged.
- Project resolution is conservative and reusable: explicit project/session
  binding, then a `projects/<id>` path in the hook payload, then cwd inside a
  project, then an exact unambiguous git-branch mapping. Unknown or ambiguous
  inputs write nothing; file mtimes are never used.
- `documented_datasets_snapshot` is what the author wrote in `REPORT.md` at
  SessionStart. It does **not** prove which queries the session executed; the
  heavier per-tool trace remains deliberately out of scope.
- The **integrity** of an approved submission already lives in
  `beril.yaml.approval` (report / review / notebook SHA-256 digests + ORCID),
  which is an **in-toto-style attestation** (subject digests + agent). The two
  hashes are integrity / TOCTOU checks only — never a trust tier.

### 3. The durable query registry — `journal.jsonl`

- An append-only per-project journal, `projects/<id>/journal.jsonl`, one JSON object
  per line: `{ts, session_id, kind, locator, payload}`. Written with a single
  `O_APPEND` write per record, so concurrent tool calls cannot corrupt it. `locator`
  is the evidence pointer exactly as `REPORT.md` cites it — for a query, `q:<id>`.
- This is the *durable query registry* the `claims.json` `2.0` contract already
  reserved a slot for. A `query:` pointer now resolves against it: found →
  `resolved` (with `query_id` and `recorded_at`), absent → `unresolved` with reason
  `query-not-recorded`. Resolved query pointers feed
  `computed.resolved_artifact_support` through the existing path — **no schema
  change and no new version of `claims.json`.**
- **Capture is agent-invoked and best-effort — the same reliability tier as
  `WORKLOG.md`, not the passive tier of `runtime.json`.** `beril capture-event` is
  called by the `berdl-query` and `synthesize` skills. It is deliberately *not* a
  `PostToolUse` hook: a BERDL query runs inside a notebook cell against a Spark
  session, so it is never a distinct tool call a matcher could observe, and a `Bash`
  matcher both produces false positives and is defeated by a single `cd`. Passive
  capture, if it is ever wanted, belongs in a wrapper around the Spark session in the
  `berdl-query` skill — the layer that actually sees the query — not in a hook.
- The consequence is worth stating plainly: an unregistered query grounds nothing.
  That is the honest failure mode. A pointer written at synthesis time from SQL
  recalled out of a notebook is reconstructed, not observed, and backfilling one
  would reintroduce exactly the gap the registry closes.

Two scope boundaries hold:

- It is an **evidence / query registry**, not the general per-tool trace, which stays
  out of scope (below). Capturing the queries that ground a claim is not the same as
  tracing every tool call.
- **Claims stay author-written.** Evidence is an observable event and can be
  captured; a claim is an interpretation and cannot. The journal *feeds* curation —
  it never replaces the `## Claims` block as the source of truth.

## Review — one adversarial path

- The reviewer hunts **evaluation-integrity** failures from a single checklist,
  `.claude/reviewer/EVALUATION_INTEGRITY.md`, anchored to the **Kapoor &
  Narayanan** leakage taxonomy and the **REFORMS** reporting checklist.
- `/berdl-refute` is the **severe-testing** pass (Mayo) framed as **strong
  inference** (Platt 1964): per finding, the strongest rival explanation + the
  observation that would disconfirm it. Advisory — it never edits the report or
  changes lifecycle state.
- Every review artifact identifies its exact subject and is discarded if the
  subject changes while the reviewer runs. `REVIEW_N.md` and `REFUTATION_N.md`
  end with exactly one `<!-- report_hash: sha256:<hex> -->`; `PLAN_REVIEW_N.md`
  ends with exactly one `<!-- plan_hash: sha256:<hex> -->`. The project-review
  footer remains the exact contract consumed by `/submit`.

## The governing reproducibility principle

The analysis **notebook with its saved outputs IS the reproducible record** —
BERIL never re-runs notebooks to "prove" reproducibility, and no hash is a
reproducibility metric. The field's own evidence supports this (Pimentel et al.
found ~4% of published notebooks re-execute with identical results; Sandve et al.,
*Ten Simple Rules for Reproducible Computational Research*, Rule 1: track
provenance rather than rely on re-execution).

## Deliberately out of scope

RDF / JSON-LD / triple stores; a provenance graph database or lineage server
(Marquez / DataHub); full RO-Crate packaging; signed attestations (cosign).
**RO-Crate** — the convergence point the workflow/notebook-provenance world is
standardizing onto (WorkflowHub, Nextflow, Galaxy, CWLProv) — is the natural
*future* step if cross-project, machine-readable interoperability is ever wanted:
`runtime.json` + `claims.json` + `beril.yaml.approval` already hold the
entities, digests, and agents needed to assemble one `ro-crate-metadata.json`
later, with zero new tooling now.

## Relationship to the Atlas and OpenViking

These per-project artifacts are the **project level** of a larger stack; they feed
upward rather than duplicate it:

- The `REPORT.md` `## Claims` block is the **single** structured per-project block.
  Any future findings/hypothesis extraction must read it, never re-extract a
  parallel list.
- `claims.json` is the canonical **per-project** claims ledger. The canonical
  **cross-project** home is the Atlas (`atlas/claims/*.md`, on `main`); `claims.json`
  is the structured input that *feeds* Atlas promotion — it does not create a second
  cross-project store.
- OpenViking stages a human-readable projection of `claims.json` and numbered
  `REFUTATION_N.md` files alongside existing curated project context. The
  projection labels author assertions, resolved/unresolved evidence, supporting
  versus contradicting evidence, and computed support. Original project files
  remain authoritative; OpenViking results are pointers. `runtime.json` is
  deliberately excluded from semantic scientific recall and remains available
  only by direct project inspection.
- *Source / lineage* provenance (references, data sources, cross-project deps) is
  owned by the Atlas `data/` pages today; if a structured file is ever wanted, the
  bare name `provenance` / a `lineage.yaml` is reserved for it (a team decision),
  keyed by `claim_id`.

## Where each artifact lives

| Artifact | What it holds | Authority |
|---|---|---|
| `REPORT.md` `## Claims` | source of truth: claim + evidence + confidence word | author-written |
| `projects/<id>/claims.json` | versioned author assertions + resolved artifact-support projection | generated, advisory |
| `projects/<id>/journal.jsonl` | append-only query registry: the locators captured while they ran | observed, best-effort |
| `projects/<id>/runtime.json` | atomic per-session runtime history (PROV-shaped) | non-authoritative |
| `beril.yaml.approval` | ORCID + SHA-256 digests (in-toto-style) | authoritative |
| `REVIEW_N.md` / `REFUTATION_N.md` / `PLAN_REVIEW_N.md` | hashed-subject review artifacts | advisory |

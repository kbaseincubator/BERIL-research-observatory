# Provenance & Trust

How BERIL records *how* a result was produced (provenance) and *how well* its
claims are supported (trust). Everything here is **advisory** and sits behind the
one human hard gate — the ORCID-bound `/submit` approval. The design borrows
recognized ideas so each artifact is trackable by name, but adopts the *idea*, not
a heavyweight dependency.

## The two pillars

### 1. Trust — a claims–evidence ledger

- Each Key Finding can be written as a falsifiable **claim** with typed
  **evidence** pointers (notebook cell, query, figure, paper) and a confidence
  **word**, in a `## Claims` block in `REPORT.md`. `beril claims build` mirrors it
  to `claims.json`.
- This is a minimal **nanopublication** / **Model Card** shape — assertion +
  evidence + attribution (Mitchell et al. 2019, *Model Cards*; Gebru et al. 2018,
  *Datasheets for Datasets*; Kuhn et al., *nanopublications*).
- **Groundedness** = the count of *distinct independent* re-runnable sources
  behind a claim (two cells of one notebook = one source). **`tier_mismatch`**
  flags when a written `high`/`medium` confidence outruns that groundedness —
  surfaced as exactly ONE advisory warning at `/submit`.
- Confidence is a **word, never a number** — following **GRADE** (which replaced
  numeric scores with an ordinal word ladder) and the LLM-calibration literature
  (Guo et al. on ECE; Steyvers/Leng on overconfidence): an artifact-derived word
  avoids a false precision BERIL has no held-out outcomes to back.

### 2. Provenance — a runtime record

- A per-project `provenance.json` snapshot, shaped loosely to **W3C PROV** (entity
  = the project, activity = the session, agent = beril + the model), written
  passively by a `SessionStart` hook. This is the **Sumatra / noWorkflow** pattern
  — capture what produced the record, don't re-run it.
- The **integrity** of an approved submission already lives in
  `beril.yaml.approval` (report / review / notebook SHA-256 digests + ORCID),
  which is an **in-toto-style attestation** (subject digests + agent). The two
  hashes are integrity / TOCTOU checks only — never a trust tier.

## Review — one adversarial path

- The reviewer hunts **evaluation-integrity** failures from a single checklist,
  `.claude/reviewer/EVALUATION_INTEGRITY.md`, anchored to the **Kapoor &
  Narayanan** leakage taxonomy and the **REFORMS** reporting checklist.
- `/berdl-refute` is the **severe-testing** pass (Mayo) framed as **strong
  inference** (Platt 1964): per finding, the strongest rival explanation + the
  observation that would disconfirm it. Advisory — it never edits the report or
  changes lifecycle state.

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
`provenance.json` + `claims.json` + `beril.yaml.approval` already hold the
entities, digests, and agents needed to assemble one `ro-crate-metadata.json`
later, with zero new tooling now.

## Where each artifact lives

| Artifact | What it holds | Authority |
|---|---|---|
| `REPORT.md` `## Claims` | source of truth: claim + evidence + confidence word | author-written |
| `projects/<id>/claims.json` | computed projection: groundedness + tier_mismatch | gate-validated, advisory |
| `projects/<id>/provenance.json` | runtime snapshot (PROV-shaped) | non-authoritative |
| `beril.yaml.approval` | ORCID + SHA-256 digests (in-toto-style) | authoritative |
| `REVIEW_N.md` / `REFUTATION_N.md` | independent review + severe-testing pass | advisory |

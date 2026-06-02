---
title: KG-Centered Scientific Aggregation Wiki — Design Spec
status: draft v3 (awaiting user review)
date: 2026-06-01
branch: feat/kg-wiki
authors:
  - Dileep Kishore (dkishore@lbl.gov)
companion: docs/kg-wiki/RESEARCH_AND_RECOMMENDATION.md
revision_notes: >
  v1 baseline. v2 added the Codex-review fixes (canonicalization, typed assertions,
  reproducible-build, corpus audit) and the minimal-review trust model + correction loop.
  v3 (this) adds: content-addressed assertion ids, honest entities-only tiers
  (grounded/asserted/conflict), a cross-project synthesis skill, re-ingest/retract flow,
  review queue + author self-check + quality dashboard, schema/skill migration events,
  and section-level narration.
---

# KG-Centered Scientific Aggregation Wiki — Design Spec (v3)

## 1. Goal

A **deterministic, knowledge-graph-centered wiki** that distills the `projects/` corpus
(~70 microbial-genomics projects) into a **human-readable scientific knowledge aggregation**.
It must convey: (1) what science has been done, (2) next steps / new science, (3) cross-project
synthesis, (4) provenance to source REPORTs / notebooks / BERDL datasets, in (5) a review-paper /
Wikipedia-quality form. The KG is built **deterministically**; LLMs only write prose *from*
committed facts. **Human review is minimal/occasional**; trust comes from machine-verified
provenance + honest tiers, and occasional corrections feed back into the skills.

## 2. Non-goals

- No LLM on the render/request path.
- Not per-item human-gated (D12); the wiki publishes continuously.
- Not byte-identical re-extraction; we target **reproducible-build** determinism (§6).
- Not adopting Graphify/GraphRAG/DeepWiki as system of record (companion doc).

## 3. Decisions

| # | Decision | Choice |
|---|---|---|
| D1 | Determinism bar | Reproducible-**build**: deterministic KG + cached/offline LLM + template render |
| D2 | Wiki spine | Synthesis units (Topics/Claims/Conflicts/Opportunities/Directions/Hypotheses); biology entities = connective tissue + drill-down |
| D3 | Schema | Single **LinkML** source of truth, Biolink-aligned; replaces `atlas_lint.py`/`models.py` duplication |
| D4 | Grounding | **Hybrid**: type all in LinkML; CURIE-ground `Organism/Gene/KO/Pathway` first |
| D5 | Extraction trigger | At `/submit` (incremental) + backfill 70; **optional skippable author self-check** (D15), no blocking gate |
| D6 | Next-science | LLM+KG hypothesis overlay — non-canonical, versioned, flagged |
| D7 | Graph viz | **Cytoscape.js** preset (deterministic) + **Mermaid** neighborhoods |
| D8 | Substrate | Extend FastAPI `ui/`; `/wiki/<entity>`, `/wiki/graph`, `/api/graph.json` |
| D9 | Implementation | Skills-native (subscription) + pure-Python core; **API drop-in** for the auditable backfill |
| D10 | Runtime | Portable SKILL.md (Claude Code + Codex) + shared Python core |
| D11 | Ingestion | Incremental-first; wiki = deterministic union of per-project `kg.yaml` + corrections; graph-diff → blast-radius; write-if-changed |
| D12 | Trust model | Publish-then-correct; deterministic **entities-only tiers** `grounded / asserted / conflict` (no tier claims the *relation* is true); minimal review |
| D13 | Correction loop | NL → `kg-correct` skill → structured append-only override (instance default + proposed class rule) → deterministic reapply + rebuild + skill learning |
| D14 | Cross-project synthesis | **Cached LLM synthesis skill** writes Topic/Direction/home narrative from member assertions; provenance-stamped, tier-flagged, cites assertions |
| D15 | Author self-check | At `/submit`, show the author their ~dozen extracted assertions for an optional, skippable sanity pass |

## 4. Architecture

```
            ┌──────────── DETERMINISTIC core (pure Python, $0, headless) ──────────┐  ┌ LLM, cached, offline ┐
projects/<p>/ ─► Stage-1 parser ─► typed assertions ─► AUTO-VERIFY (entities@span) ──◄── Stage-2 extract
  REPORT.md       + coverage          (kg.yaml v3,        ├ entities grounded+located → grounded   (subagent draft,
  RESEARCH_PLAN   (Phase-0 gated)     content-addressed   ├ else → asserted (flagged)              provenance-stamped,
  REVIEW.md                            ids)               └ contradicts grounded → conflict        content-hash cached)
  beril.yaml                                │
   corrections/ ──► override layer ─► CANONICALIZE + merge (deterministic union-find) ─► KGX + baked layout (frozen)
   (skill-authored)                   stable surrogate ids; CURIE=alias; precedence+redirect      │
                                              │                                                    │
   ┌───────────────────────────────┬──────────┴───────────────┬───────────────────────────────────┤
   ▼                               ▼                           ▼                                   ▼
 /wiki/<entity>          /wiki/<Topic|Direction|home>    /wiki/graph (Cytoscape)            hypothesis overlay
 (facts; tier badges;    cross-project SYNTHESIS skill   + Mermaid neighborhoods            (non-canonical, flagged)
  coverage; provenance)  (cached, cited, tier-flagged)   search · review queue · quality dashboard · CI: validate+idempotency
```

## 5. Components (each one job)

### 5.1 Schema (`kg/schema/*.yaml`) — LinkML, Biolink-aligned
Single source of truth; generates the `kg.yaml` validator, KGX classes/slots, page-type/predicate
vocabularies (ends the `atlas_lint.py`/`models.py` duplication). Deps `linkml`. No LLM.

### 5.2 Stage-1 extractor (`kg/extract/structural.py`) + coverage
Byte-stable scaffold from `projects/`; emits a per-project **coverage report**. No LLM. Phase-0 gated (§14.0).

### 5.3 Grounders (`kg/ground/`) — deterministic
Gilda/OGER/oaklib → CURIEs (NCBITaxon/GO/Pfam/COG/CHEBI/ENVO); `Organism/Gene/KO/Pathway` first.
Grounding is an **attribute**, not an identity change (§7).

### 5.4 Stage-2 extraction skill (`kg-extract`) — candidate authoring
Subagents draft **typed assertions** (schema-constrained, each with a source span and a
**content-addressed id**, §7). Validated, retried, content-hash cached, with a **provenance
manifest** per run (skill/prompt/tool/commit/model/retry/candidate hashes). Candidates only; tier set
by §5.5. Subscription tokens (API for backfill).

### 5.5 Auto-verification (`kg/verify/`) — deterministic, no LLM
Re-read each assertion's cited span; confirm its entities are **grounded and present at the span** +
schema-valid. Sets the tier (D12): **grounded** (entities real + located; relation stands *as
extracted*, not independently verified), **asserted** (ungrounded entity / weak-or-missing span / low
confidence → rendered with an "unverified extraction" badge), **conflict** (a grounded assertion that
contradicts another grounded assertion → both surfaced). *No tier asserts the relation is true* —
relation errors are caught by conflicts + corrections + the review queue.

### 5.6 Canonicalizer + assembler (`kg/build/`) — deterministic, no LLM
Applies the correction override layer (§11); union-find canonicalization with fixed precedence (§7);
cross-project edges from shared `gtdb_species_clade_id`/`genome_id`; surfaces conflicts; **canonically
sorted triples** → KGX + baked preset layout. Handles **re-ingest/retract** (§10). Build **writes a
page section only when its section fact-hash changes** (§6). Deps `networkx`, `kgx`.

### 5.7 Cross-project synthesis skill (`kg-synthesize`) — D14, the core-value component
Deterministic step selects each Topic/Direction/home page's **member set** (assertions/claims/
conflicts via shared entities + controlled-vocab topic membership). An LLM synthesis skill then writes
the **cross-project narrative from that member set** — cached (keyed on the member-set hash),
provenance-stamped, **citing the underlying assertion ids**, and **tier-flagged** by the weakest tier
of its inputs (a synthesis resting on `asserted` facts is itself badged). Conflicts render inline.
Re-narrated only when the member-set hash changes (§6). This is what makes goal #3 (cross-project
synthesis) and the home "state of the science" real.

### 5.8 Renderer (extend `ui/app/`)
`/wiki/<entity>` (synthesis-unit + biology pages, **tier badges**, **coverage metadata**, provenance
links), `/wiki/<Topic|Direction>` + home (from §5.7), `/wiki/graph` (Cytoscape), `/api/graph.json`,
Mermaid neighborhoods. Plus **search** (entity + full-text index), the **review queue** (candidate/
conflict assertions ranked by centrality/traffic — reuse `atlas/meta/review-queue.md`), and a
**quality dashboard** (tier distribution, provenance completeness, conflict rate, orphan/broken-link
checks, accuracy-sample results — reuse `atlas/meta/metrics-to-watch.md`). Pure Jinja, no render-time LLM.

### 5.9 Correction skill (`kg-correct`) — §11
NL correction → resolve target(s) against the KG → structured append-only override + proposed class
rule → blast-radius rebuild; distills corrections into skill few-shot/rules/regression fixtures.

### 5.10 Narration skill (`kg-narrate`) — optional, section-level
Review-paper prose **from committed facts**, cited + tier-aware, generated **per section** and
regenerated only when that section's fact-hash changes (§6) — so a new finding updates one paragraph,
not the whole article. Mostly templated for entity stubs; LLM narrative reserved for synthesis-heavy pages.

### 5.11 Hypothesis overlay (reuse `suggest-research`) — D6
LLM+KG agent over the committed graph; non-canonical, versioned, flagged; refreshed on demand /
scheduled, never merged into the canonical KGX core.

### 5.12 CI gate
`linkml-validate` + `kgx validate` + `atlas_lint` + **idempotency test** (§7) + orphan/broken-link
checks; merge blocked on failure.

## 6. Determinism contract (reproducible-build)

1. **Deterministic extraction** — only the Stage-1 scaffold.
2. **Reproducible build** *(target)* — the LLM steps (extraction §5.4, synthesis §5.7, narration §5.10)
   run offline, content-hash cached with provenance manifests, and their committed output is the frozen
   artifact; rebuilds replay committed `kg.yaml` + corrections + cached prose, never the model.
3. **Template-driven render** — pure templates over the committed graph.

**Section-level fact-hash:** each page is decomposed into sections; a section's fact-hash = hash of the
canonical sorted facts feeding *that section*, computed **before** prose/layout. Prose/synthesis
re-narrate only for sections whose fact-hash changed → minimal git diff + stable narrative. Layout
coords are a deterministic seeded function of the graph (never perturb fact-hashes).

**Schema/skill migrations:** the cache key includes schema + prompt hashes, so a schema or skill change
invalidates extraction. These are handled as **deliberate, versioned migration events** (batch
re-extract → diff/QA → commit), never silent cache busts, and corrections re-bind via content-addressed
ids (§7). The LLM never sits on the render path; the hypothesis overlay (§5.11) is the only deliberately
non-deterministic surface, quarantined.

## 7. Identity & canonicalization

- **Mention** — immutable source-local reference with its span.
- **Node identity** = stable content-addressed surrogate `n:hash(normalized_label + type)`; **CURIE
  grounding is an alias/attribute**, never an identity change.
- **Assertion identity** = content-addressed `a:hash(subject + predicate + object)` (project-scoped if a
  triple recurs) — **stable across re-extraction and minor report edits**, so corrections re-bind
  correctly (closes the v2 volatile-seq-id gap). The span is evidence metadata, not identity.
- **Merges** — explicit, append-only, deterministic union-find with fixed precedence (CURIE-bearing wins;
  else lexicographic); a cluster's canonical id is a pure function of the evidence set, independent of
  order/timing. **Redirect + tombstone** on merge; `force-split` reverses via the correction layer.
- **Canonical sorted serialization** of triples → stable graph + section fact-hashes.
- **Proof obligation (CI):** idempotency test under shuffled ingest order *and* correction/merge timing →
  identical graph + identical section fact-hashes.

## 8. Trust model: tiers, provenance, occasional review (D12, D15)

- **Typed, diffable assertions** with `{id (content-addressed), kind, subject, predicate, object,
  polarity, qualifiers, source_span, evidence_ids, extractor_provenance, confidence, tier}`. CI rejects a
  **grounded**-tier assertion lacking a machine-checkable span.
- **Deterministic tiers** (§5.5): `grounded` (entities verified present + located), `asserted` (flagged
  unverified), `conflict`. *No tier claims relation truth.*
- **Author self-check (D15):** at `/submit`, the author sees their project's ~dozen extracted assertions
  for an optional, skippable "anything obviously wrong?" pass → flags become corrections. Highest-leverage,
  near-free; not a gate.
- **Review queue + quality dashboard** (§5.8) aim occasional review at the highest-impact `asserted`/
  `conflict` items and track product health — essential precisely because review is minimal.

## 9. Schema (core artifact)

**Layer A — Synthesis units** (subclasses of `biolink:InformationContentEntity`): `Topic · Claim ·
Conflict · Opportunity · Direction · Hypothesis · Finding · DerivedProduct · Method`.
**Layer B — Biology entities** (Biolink, CURIE-grounded): `Organism`→OrganismTaxon · `Gene/GeneCluster`→
Gene (xref Pfam/COG) · `KO/OrthologGroup` · `Pathway` (GO/Reactome) · `Function`→Bio/MolecularActivity
(GO) · `Metabolite`→ChemicalEntity (CHEBI) · `Phenotype`→PhenotypicFeature · `Condition/Environment`→
Environmental* (ENVO) · `Dataset`/`Notebook`→Dataset · `Project`→Study · `Publication` (PMID).
**Add** `GeneFitness`, `Cofitness` (class vs edge-qualifier — §17 Q1).
**Predicates** carry `knowledge_level, agent_type, has_evidence, provided_by, confidence, p_value, tier`:
`in_taxon · enables/participates_in · genetically_interacts_with · has_phenotype · associated_with ·
supported_by/refuted_by · contradicts · has_evidence · motivates · advances · produced_by`.

**Per-project `kg.yaml` (v3):**
```yaml
project:
  id: amr_pangenome_atlas
  report_hash: <sha>
  archive_key: <key>
  extraction: {skill: kg-extract@<hash>, model: <id>, prompt_bundle: <hash>,
               tool_manifest: <hash>, repo_commit: <sha>, stage1_coverage: 0.92}
mentions:
  - {id: amr_pangenome_atlas/m/0007, label: "Acinetobacter baumannii", type: Organism,
     span: {file: REPORT.md, heading: Results, char: [1204, 1229], quote: "..."}}
entities:
  - {node: n:ab12cd, type: Organism, label: "Acinetobacter baumannii",
     curie: NCBITaxon:470, mentions: [amr_pangenome_atlas/m/0007], confidence: 0.98, tier: grounded}
assertions:
  - id: a:9f3c1e            # content hash of (s,p,o) — stable across re-extraction (§7)
    kind: relation
    s: n:ab12cd
    p: has_phenotype
    o: n:ef34gh
    polarity: positive
    evidence: {span: {file: REPORT.md, heading: Results, char: [...], quote: "..."},
               notebook: 12_x.ipynb, p_value: 1.0e-3}
    extractor: {agent_type: automated_agent, confidence: 0.86}
    tier: grounded          # set by §5.5, deterministic
  - id: a:71b0aa
    kind: claim
    statement: "metal-specific transporter genes are core-enriched"
    supported_by: [a:9f3c1e]
    entities: [n:ab12cd]
    tier: asserted          # ungrounded/low-conf → flagged in wiki
```

## 10. Incremental ingestion + change/retraction (D11)

- **Add** (default): append `kg.yaml`; deterministic union keyed by stable ids → order-independent,
  idempotent, monotonic except merges. Write-if-changed (section-level) → diff is exactly the changed
  sections. Blast-radius scoped recompute. Integration at ingest (entity resolution, new-conflict
  detection, controlled-vocab topics, no silent overwrite) — all machine-tiered, no gate. Only the new
  project is LLM-drafted.
- **Change** (a project's REPORT edits): re-extract → diff new vs old `kg.yaml` → prune removed
  assertions, add new → blast-radius rebuild. Content-addressed ids mean unchanged assertions keep their
  ids (no churn); corrections survive.
- **Retract/remove**: drop the project's `kg.yaml` → prune its mentions/assertions → recompute affected
  canonical nodes/merges/conflicts → **redirect/tombstone** orphaned entity pages → flag corrections whose
  target vanished for review. (graphify's `--update` ghost-node pruning is precedent.)

## 11. Correction-feedback loop (D13)

- **Capture (NL → skill):** human tells `kg-correct` e.g. *"Mug113 isn't in E. coli, it's in
  Acinetobacter."* The skill **queries the KG to resolve target assertion(s)** (confirming when ambiguous
  or class-wide across projects), writes a structured append-only record, and triggers a blast-radius rebuild:
  ```yaml
  # kg/corrections/<entity-or-project>.yaml  (append-only, versioned)
  - id: corr/0001
    targets: [a:9f3c1e]          # resolved by the skill (may be many across projects)
    kind: reground               # retract | fix-value | force-merge | force-split | reground | promote | demote
    value: {o: NCBITaxon:62977}
    scope: instance              # default; rule proposed below
    proposed_rule: {kind: grounding_override, label: "ADP1", curie: NCBITaxon:62977}
    rationale: "ADP1 is A. baylyi, not E. coli"
    author: dkishore
    timestamp: 2026-06-01
  ```
- **Authoritative override**, applied deterministically after extraction at highest precedence, **keyed to
  content-addressed ids so it survives re-extraction** (§7).
- **Scope (D13):** instance applied now; skill **proposes** a class rule (grounding override / heading
  synonym / extraction rule) adopted only when machine-safe or human-confirmed.
- **Correction integrity:** corrections carry author + rationale; the skill **flags a correction that
  contradicts strong grounded evidence** for a second look; conflicting corrections on the same target
  resolve by timestamp (append-only, last-wins, surfaced in the review queue).
- **Learning:** each correction → skill few-shot/negative examples + deterministic rule tables + a
  regression fixture (the error can't return).
- **Propagation:** a correction is another deterministic build input → §10 blast-radius rebuild.

## 12. Implementation mechanism (D9, D10)

Deterministic core = pure Python (`kg/` + `beril_cli`): parser, grounders, verifier, canonicalizer,
assembler, KGX, layout, validators, renderer, search index, dashboards. **Zero LLM, headless, CI-runnable.**
LLM steps = portable SKILL.md skills dispatching subagents → subscription tokens; **API drop-in** for the
auditable backfill. Live wiki never calls an LLM.

## 13. Data flow

- **`/submit`:** `synthesize` → `kg-extract` (Stage-1 + Stage-2, cached, manifest) → auto-verify tiers →
  **optional author self-check (D15)** → canonicalize + apply corrections → affected synthesis pages
  re-narrate (§5.7) → blast-radius rebuild. No blocking gate.
- **Backfill (one-time):** API fan-out drafts all 70 with archived I/O; tiers + author/spot-check seed the queue.
- **Correction:** human → `kg-correct` → override + proposed rule → rebuild (§11).
- **Build (headless, no LLM):** canonicalize → KGX → baked layout → `data.pkl.gz` → FastAPI serves.

## 14. Build sequence (tracer-bullet phases)

0. **Corpus-structure audit (GATE)** — enumerate report files/headings/metadata/notebook/table/link
   patterns + parser coverage; thresholds + fixtures; below-threshold → `asserted` tier + visible coverage
   gap; calibrate schema + synonym map.
1. **Schema + identity + CI** — LinkML; canonicalization (entity + assertion content-addressing) +
   idempotency test; CI gate.
2. **Deterministic tracer (one project, no LLM)** — Stage-1 + auto-verify + canonicalize + KGX + one
   `/wiki/<page>` with tier badge.
3. **Renderer** — entity pages, Cytoscape graph, Mermaid neighborhoods, coverage metadata, **search**.
4. **`kg-extract` + manifest + backfill** — typed-assertion Stage-2; API backfill of 70.
5. **`/submit` hook + author self-check + review queue + quality dashboard**.
6. **Cross-project synthesis (`kg-synthesize`)** — Topic/Direction/home pages, cached + cited + tiered.
7. **Correction loop (`kg-correct`)** — override layer, target resolution, rule proposal, fixtures.
8. **`kg-narrate` (section-level)** + **hypothesis overlay** (reuse `suggest-research`, flagged).

## 15. Reuse map

| Need | Reuse |
|---|---|
| Schema | `linkml-schema` |
| Findings input | `synthesize` |
| Next-science overlay | `suggest-research` |
| Extraction trigger | `submit` |
| Review queue / metrics seeds | `atlas/meta/review-queue.md`, `atlas/meta/metrics-to-watch.md` |
| Topic vocabulary seed | `atlas/topics/` |
| Graph builders, parsing, cache, render | `ui/app/atlas_graph.py`, `dataloader.py`, `data.pkl.gz`, templates |

## 16. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Volatile assertion ids orphan corrections | Content-addressed `a:hash(s,p,o)` ids (§7). |
| Retroactive id churn / non-idempotent merges | Stable surrogate ids; CURIE-as-alias; deterministic precedence; redirect/tombstone; idempotency CI (§7). |
| "Verified" over-claims relation truth | Honest `grounded` tier = entities-only; relation errors via conflicts + corrections + queue (§5.5/§8). |
| Cross-project synthesis unspecified | `kg-synthesize` skill, cached + cited + tier-flagged (§5.7). |
| Change/retraction non-monotonic | Defined re-ingest/retract flow with pruning + tombstones (§10). |
| Bad/ambiguous corrections poison graph | Skill-resolved targets + author/rationale + contradiction flag + timestamp resolution (§11). |
| Schema/skill bump re-extracts everything | Versioned migration events with diff/QA; ids stable so corrections survive (§6). |
| Prose churn on small fact change | Section-level fact-hash + narration (§6/§5.10). |
| Opaque skill drift | Provenance manifest; reproducible-build (not -extraction); API backfill archives I/O. |
| Stage-1 over-trusts inconsistent corpus | Phase-0 gate; coverage → tier demotion + visible metadata. |
| Two truth surfaces (atlas vs wiki) confuse readers | Resolve coexistence (§17 Q2) before launch. |
| Hosted-LLM non-determinism | LLM offline + cached + committed; never on render path. |

## 17. Open questions

1. **Schema redlines (§9)** — entity types/predicates; `GeneFitness`/`Cofitness` class vs qualifier; is `kg.yaml` v3 shape right?
2. **`atlas/` coexistence/migration** — `/wiki` replaces / runs alongside / backfills into `atlas/`? (Default: generate `/wiki`, subsume atlas page types, keep `atlas/` as seed/override until parity, then deprecate hand-authoring.) Resolve before launch — it's reader-facing.
3. **Temporal tracking** — not in v1; schema reserves valid-time slots.
4. **Search scope** — entity + full-text in v1 (recommended) vs entity-only first?
5. **Topic vocabulary seeding** — seed controlled vocab from `atlas/topics/`; clustering *proposes* new topics, curation *adopts* (confirm).

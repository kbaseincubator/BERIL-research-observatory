# BERIL Synthesis Wiki Implementation Plan

> **For agentic workers:** Use Superpowers-style execution: work task-by-task, keep checkboxes current,
> write focused tests for each contract, and verify before moving on. This plan supersedes the older
> entity-centric compendium plan for future work. Full design:
> `docs/kg-wiki/2026-06-02-synthesis-wiki-design.md`.

**Goal:** Build a generated, prose-rich human wiki that replaces the current Codex-authored `atlas/`.
The wiki is centered on synthesis pages, backed by a deterministic statement-card knowledge graph
extracted from `projects/`.

**Core invariant:** The KG is a graph of evidence-backed **statement cards**, not primarily an entity
graph. Entities connect statements across projects; synthesis pages are the main human reading path.

**Implementation stance:** Keep using `compendium/` as the package unless explicitly renamed. Python
scripts are deterministic and never call LLMs. Skills orchestrate LLM extraction/prose, validate outputs,
write artifacts, and rebuild.

**Tracer scope:** two ADP1 projects:

- `projects/acinetobacter_adp1_explorer`
- `projects/adp1_deletion_phenotypes`

**Success criteria for tracer:**

- generated home page;
- generated ADP1 topic page;
- generated ADP1 organism entity page;
- at least two claim pages;
- at least one opportunity/future-step page;
- project pages for both tracer projects;
- graph view with typed edge classes;
- quality report with zero dangling edges and zero broken links;
- all statement cards validate and have source evidence.

---

## Architecture Summary

```text
projects/<id>/                         OpenViking context (optional input)
   │                                                │
   ▼                                                ▼
deterministic audit + context pack  ─────►  kg-ingest-project skill
   │                                                │
   │                                      LLM structured extraction
   │                                                ▼
   └──────────────► validated statement cards + entities + links
                                                    │
                                                    ▼
corrections ───────────────► build graph ───► plan pages ───► kg-synthesize-page skill
                                                    │                    │
                                                    ▼                    ▼
                                             graph artifacts       prose-rich pages
                                                    │                    │
                                                    └──────► render + quality
```

---

## Artifact Layout

```text
compendium/
  schema/
    synthesis_wiki.yaml
  context-packs/
    <project_id>.json
  kg/
    <project_id>.kg.yaml
    corrections/
      *.yaml
    graph/
      nodes.tsv
      edges.tsv
      graph.json
  pages/
    home.md
    topics/
    claims/
    conflicts/
    opportunities/
    directions/
    hypotheses/
    projects/
    entities/
  skills/
    kg-ingest-project/
    kg-synthesize-page/
    kg-curate/
    kg-backfill/
    kg-review-queue/
  out/
    site/
```

---

## Data Contracts

### StatementCard

```python
class StatementCard(BaseModel):
    id: str
    kind: Literal[
        "finding", "claim", "caveat", "conflict", "hypothesis",
        "opportunity", "direction", "method_note", "derived_product",
    ]
    statement: str
    scope: Literal["project_local", "cross_project", "corpus_level", "hypothesis"]
    tier: Literal["asserted", "grounded", "reviewed", "conflict", "retracted"]
    confidence: Literal["low", "medium", "high"]
    about: AboutRefs
    links: StatementLinks
    qualifiers: dict[str, str]
    evidence: EvidenceAnchor
    extraction: ExtractionManifest
```

### EvidenceAnchor

Evidence anchors should use exact text plus context, not char offsets alone:

```python
class EvidenceAnchor(BaseModel):
    source_project: str
    source_doc: str
    source_section: str | None = None
    exact: str
    prefix: str = ""
    suffix: str = ""
    notebook: str | None = None
    figure: str | None = None
    p_value: float | None = None
```

### PagePlan

```python
class PagePlan(BaseModel):
    id: str
    type: str
    title: str
    member_statement_ids: list[str]
    sections: list[PageSectionPlan]
    outgoing_links: list[str]
    backlinks: list[str]
    member_hash: str
```

---

## Task 0 — Reframe Existing Compendium Around Statement Cards

**Goal:** Make the implemented package direction match the v4 design without a package rename.

**Files:** `compendium/src/compendium/models.py`, `compendium/schema/synthesis_wiki.yaml`,
`compendium/README.md`, tests.

- [x] Add `StatementCard`, `EvidenceAnchor`, `ExtractionManifest`, `PagePlan`, and edge-class models.
- [x] Keep existing entity/assertion models only if needed for transition; mark them as lower-level graph records.
- [x] Add tests for statement card serialization and evidence anchor validation.
- [x] Update README to point to the v4 design.
- [x] Verify: `cd compendium && uv run pytest -q`.

**Acceptance:** A statement card can round-trip through YAML/JSON and validate required evidence.

---

## Task 1 — Deterministic Corpus Audit + Source Section Model

**Goal:** Build the raw evidence scaffold without LLM calls.

**Files:** `audit.py`, `extract/structural.py`, tests.

- [x] Parse project canonical files: `REPORT.md`, `RESEARCH_PLAN.md`, `REVIEW.md`, `README.md`, `beril.yaml`.
- [x] Emit source sections with stable IDs, headings, exact text hashes, and line/char metadata.
- [x] Extract deterministic source anchors: datasets, notebooks, figures, PMIDs/DOIs, explicit project links.
- [x] Extract deterministic identifier-like entities: KOs, Pfams, COGs, GTDB/genome IDs.
- [x] Add tests on fixture projects.
- [x] Verify no LLM/model/API calls in this path.

**Acceptance:** The two ADP1 projects produce stable source-section inventories and source anchors.

---

## Task 2 — Context Pack Builder

**Goal:** Build deterministic context packs that skills consume.

**Files:** `context_pack.py`, CLI dispatch, tests.

- [x] Implement `build_context_pack(project_dir) -> ContextPack`.
- [x] Include project metadata, source hashes, source sections, deterministic entities, dataset hints, and allowed vocabularies.
- [x] Add optional field for OpenViking context references, but do not require them in this branch.
- [x] Hash the full context pack and expose the hash for extraction manifests.
- [x] CLI: `compendium context-pack projects/<id> --out compendium/context-packs/<id>.json`.
- [x] Test deterministic byte output across repeated runs.

**Acceptance:** Both ADP1 context packs are byte-stable and contain enough source text for extraction.

---

## Task 3 — Schema + Validation Gate

**Goal:** Statement cards and page plans must fail fast when malformed.

**Files:** `schema/synthesis_wiki.yaml`, `validate.py`, tests.

- [x] Define LinkML schema or pydantic schema for statement cards, evidence anchors, entities, edge classes, page plans, corrections.
- [x] Add validator commands:
  - `compendium validate-card <file>`;
  - `compendium validate-project-kg <file>`;
  - `compendium validate-page-plan <file>`.
- [x] Validate evidence anchor shape and required statement fields.
- [x] Validate controlled vocabularies for statement kinds, tiers, edge classes, page types.
- [x] Add tests for invalid missing evidence, invalid edge kind, unknown tier, and valid card.

**Acceptance:** Invalid LLM outputs cannot enter graph assembly.

---

## Task 4 — `kg-ingest-project` Skill

**Goal:** Skill-driven LLM extraction publishes structured statement cards.

**Files:** `compendium/skills/kg-ingest-project/SKILL.md`, support prompts/templates if needed.

- [x] Create skill instructions.
- [x] Skill workflow:
  - run audit/context-pack;
  - extract statement cards, entities, proposed links, caveats, conflicts, and opportunities;
  - validate output;
  - retry invalid sections;
  - write `compendium/kg/<project_id>.kg.yaml`;
  - rebuild graph/page plans/quality;
  - summarize extracted cards and diffs.
- [x] Require evidence anchors for every non-retracted statement.
- [x] Forbid uncited claims and free-form relation types.
- [ ] Demonstrate on one fixture/tracer project.

**Acceptance:** Running the skill on one ADP1 project writes validated statement cards and a manifest.

---

## Task 5 — Graph Assembly From Statement Cards

**Goal:** Build a typed graph where statement cards are first-class nodes.

**Files:** `build/assemble.py`, `build/canonicalize.py`, `ids.py`, tests.

- [x] Convert statement cards into graph nodes.
- [x] Convert `about`, `links`, `qualifiers`, and evidence into typed edge classes:
  `scientific_edge`, `provenance_edge`, `navigation_edge`, `derivation_edge`, `review_edge`.
- [ ] Canonicalize entities by deterministic IDs/CURIEs.
- [x] Keep statement-card IDs stable across re-ingestion.
- [ ] Detect conflicts from explicit contradictions and opposing claims.
- [x] Emit sorted graph artifacts: `nodes.tsv`, `edges.tsv`, `graph.json`.
- [x] Idempotency test under shuffled project/card/correction order.

**Acceptance:** Graph output is byte-stable and statement cards remain queryable as first-class nodes.

---

## Task 6 — Page Planner

**Goal:** Select deterministic member sets before prose generation.

**Files:** `pages/plan.py`, tests.

- [x] Generate page plans for home, topics, claims, opportunities, projects, and entities.
- [x] Home page plan includes top topics, strong claims, conflicts, opportunities, reusable data/products, recent changes, browse lanes.
- [x] Topic page plans use statement membership by topic plus related claims/conflicts/opportunities.
- [x] Claim page plans include support/refutation/caveats/downstream uses.
- [x] Entity page plans include backlinks grouped by statement kind and topic.
- [x] Compute `member_hash` per page and section.
- [x] Test page-plan determinism.

**Acceptance:** The ADP1 tracer produces deterministic page plans with sensible backlinks/outlinks.

---

## Task 7 — `kg-synthesize-page` Skill

**Goal:** Generate prose-rich pages from fixed page plans and statement cards.

**Files:** `compendium/skills/kg-synthesize-page/SKILL.md`, page templates.

- [x] Create skill instructions.
- [x] Input is a `PagePlan` and referenced statement cards only.
- [x] Require citations to statement IDs/source projects.
- [x] Write prose sections from member cards; do not invent unsupported claims.
- [ ] Store synthesis manifest with model, prompt hash, page-plan hash, member hash.
- [ ] Write generated page artifact under `compendium/pages/`.
- [ ] Demonstrate on home and ADP1 topic pages.

**Acceptance:** Generated prose is readable, cited, and reproducible via unchanged member hashes.

---

## Task 8 — Renderer And Obsidian-Like Navigation

**Goal:** Render the human wiki with backlinks, outgoing links, local graph, and graph view.

**Files:** `render/`, templates, static assets, tests.

- [x] Render synthesis pages as the primary pages.
- [x] Render project and entity pages.
- [ ] Each page includes:
  - readable prose;
  - source statement list;
  - backlinks;
  - outgoing links;
  - local graph/neighborhood;
  - provenance links.
- [ ] Add graph view with typed edge filters.
- [x] Vendor/pin frontend assets; do not depend on CDN for core render.
- [x] Test no broken internal links.

**Acceptance:** The generated ADP1 site is navigable by home, topic, claim, project, entity, and graph.

---

## Task 9 — Corrections And Curation

**Goal:** Corrections target statement cards and graph nodes safely.

**Files:** `corrections.py`, `skills/kg-curate/SKILL.md`, tests.

- [ ] Correction kinds:
  `retract`, `fix-statement`, `fix-qualifier`, `reground-entity`, `force-merge`, `force-split`,
  `promote`, `demote`, `mark-conflict`, `resolve-conflict`.
- [ ] Apply corrections deterministically before graph assembly.
- [ ] Preserve retracted statements for provenance but exclude from normal synthesis.
- [ ] Skill writes append-only correction records.
- [ ] Corrections become regression fixtures.
- [ ] Test corrections survive re-extraction by stable statement IDs.

**Acceptance:** A correction to an ADP1 statement survives re-ingestion and updates affected pages only.

---

## Task 10 — Quality Dashboard

**Goal:** Measure wiki usefulness, not just graph validity.

**Files:** `quality/`, tests, rendered dashboard page.

- [ ] Metrics:
  - statement count by kind/tier/source project;
  - evidence resolution rate;
  - topic coverage;
  - claim support/refutation balance;
  - active conflicts;
  - opportunities with target outputs;
  - high-centrality asserted statements;
  - orphan pages and weakly connected pages;
  - broken links and dangling edges;
  - synthesis pages regenerated in last build.
- [ ] Add CLI `compendium quality`.
- [x] Render quality dashboard page.
- [x] Tests for metric correctness on small graphs.

**Acceptance:** Quality report catches missing evidence, dangling links, and orphan synthesis pages.

---

## Task 11 — Backfill Skill

**Goal:** Batch ingestion without losing per-project accountability.

**Files:** `skills/kg-backfill/SKILL.md`, optional helper scripts.

- [x] Skill iterates project-by-project and calls `kg-ingest-project`.
- [x] Records failed projects and validation failures.
- [x] Produces batch diff and quality summary.
- [x] Supports `--limit`, explicit project list, and resume from previous run.
- [x] Does not ingest all projects by default during tracer work.

**Acceptance:** Backfill can process the two ADP1 projects as a batch and report extracted cards/pages.

---

## Task 12 — Review Queue Skill

**Goal:** Route occasional human attention to high-value weak points.

**Files:** `skills/kg-review-queue/SKILL.md`, `quality/review_queue.py`, tests.

- [x] Rank statements by centrality, low confidence, conflict status, synthesis use, and missing review.
- [x] Generate review briefs with source evidence and affected pages.
- [x] Support actions via `kg-curate`.
- [x] Test ranking on a fixture graph.

**Acceptance:** The queue identifies the most important asserted/conflicted ADP1 statements.

---

## Task 13 — End-To-End Tracer

**Goal:** Prove the full workflow on the two ADP1 projects.

- [ ] Run `kg-ingest-project` for each tracer project.
- [x] Build graph and page plans.
- [ ] Run `kg-synthesize-page` for home, ADP1 topic, claims, opportunity, projects, and organism page.
- [x] Render the site.
- [x] Run quality checks.
- [ ] Confirm outputs:
  - home page exists;
  - ADP1 topic page exists;
  - ADP1 organism page has backlinks from both projects;
  - at least two claim pages exist;
  - at least one opportunity/future-step page exists;
  - graph view exists;
  - no broken links/dangling edges;
  - every published statement has evidence.

**Acceptance:** Tracer site is readable enough to replace the current Atlas shape for this limited scope.

---

## Deferred Work

- Full 70-project backfill.
- Deeper OpenViking integration.
- FastAPI integration if static render is not sufficient.
- Search ranking and full-text index.
- Advanced ontology grounding beyond curated dictionaries/regex.
- Hypothesis-generation overlay beyond extracted project future steps.

---

## Immediate Next Step

Start at Task 0. Do not continue implementing the old entity-first plan until the statement-card
models and validation gate are in place.

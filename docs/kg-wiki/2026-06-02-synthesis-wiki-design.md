---
title: BERIL Synthesis Wiki — Statement-Card KG Design
status: draft v4
date: 2026-06-02
branch: feat/kg-wiki
supersedes:
  - docs/kg-wiki/2026-06-01-kg-wiki-design.md
companion_plan: docs/superpowers/plans/2026-06-02-synthesis-wiki.md
---

# BERIL Synthesis Wiki — Statement-Card KG Design

## 1. Goal

Replace the current Codex-generated `atlas/` with a **human-readable, prose-rich synthesis wiki**
generated from `projects/` and organized by a deterministic, auditable knowledge graph.

The wiki should feel like the useful parts of the current Atlas: topic synthesis, reusable claims,
conflicts, hypotheses, directions, opportunities, methods, data products, and evidence trails. The
new source of truth is not hand-authored Atlas pages. It is a **statement-card knowledge graph**:
evidence-backed scientific statements extracted from raw projects, connected to synthesis pages,
source projects, and biological/data entities.

## 2. Product Model

### Human-facing layers

1. **Synthesis pages** — primary reading path:
   `home`, `topic`, `claim`, `conflict`, `opportunity`, `direction`, `hypothesis`,
   `derived_product`, `method`.
2. **Evidence pages** — source and reuse path:
   `project`, `finding`, `source_section`, `dataset`, `notebook`, `publication`.
3. **Entity pages** — connective tissue and local graph path:
   `organism`, `gene`, `KO`, `ortholog_group`, `pathway`, `phenotype`, `condition`,
   `environment`, `data_collection`.

Synthesis pages are the main wiki. Entity pages behave like Obsidian local-graph/backlink pages,
not like the main narrative spine.

### Entry page

The home page is a generated **state-of-the-science** page, not a directory. It should include:

- short cross-project overview;
- topic map;
- strongest reusable claims;
- active conflicts and caveats;
- high-value opportunities and directions;
- reusable data/products;
- recently changed projects/pages;
- browse lanes: topics, claims, opportunities, projects, entities, data, graph.

## 3. Source Layers

1. **Raw project corpus:** `projects/<project_id>/` is the evidence source. Important files include
   `REPORT.md`, `RESEARCH_PLAN.md`, `REVIEW.md`, `README.md`, notebooks, figures, and data artifacts.
2. **OpenViking context:** agent-facing context, incorporated in a separate PR. It may be used by
   ingestion skills to improve extraction and synthesis, but it is not itself the human wiki.
3. **Generated wiki:** this branch's human-facing artifact, produced from statement cards and rendered
   pages. It replaces the current Atlas as the public knowledge surface.

## 4. Core Invariant

The KG is not primarily an entity graph. It is a graph of **statement cards**:

> evidence-backed scientific statements connected to synthesis pages, source projects, and
> biological/data entities.

Entities are valuable because they connect statements across projects. They are not sufficient by
themselves to produce a useful scientific wiki.

## 5. Statement Card Contract

Statement cards are the unit of extraction, correction, validation, graph assembly, and synthesis.

```yaml
id: stmt:<content-hash>
kind: finding | claim | caveat | conflict | hypothesis | opportunity | direction | method_note | derived_product
statement: "Carbon sources define a three-tier essentiality landscape in ADP1."
scope: project_local | cross_project | corpus_level | hypothesis
tier: asserted | grounded | reviewed | conflict | retracted
confidence: low | medium | high
about:
  entities:
    - entity:<id>
  topics:
    - topic:<id>
links:
  supports: []
  contradicts: []
  motivates: []
  refines: []
  requires_validation: []
qualifiers:
  organism: entity:<id>
  condition: "quinate"
  method: "RB-TnSeq"
  data_collection: collection:<id>
evidence:
  source_project: adp1_deletion_phenotypes
  source_doc: REPORT.md
  source_section: "Key Findings"
  exact: "Carbon sources define a three-tier essentiality landscape"
  prefix: "..."
  suffix: "..."
  notebook: null
  figure: null
  p_value: null
extraction:
  agent_type: llm_extractor
  skill: kg-ingest-project
  model: "<model-id>"
  prompt_hash: "<hash>"
  context_pack_hash: "<hash>"
  repo_commit: "<sha>"
  timestamp: "<iso8601>"
```

### Tier semantics

- `asserted`: LLM-extracted or structurally extracted and published with evidence, but not manually
  reviewed.
- `grounded`: source span resolves and referenced entities are grounded/schema-valid. This still does
  not mean relation truth.
- `reviewed`: human-accepted statement or generated synthesis section.
- `conflict`: contradiction or unresolved tension detected across statement cards.
- `retracted`: statement preserved for provenance but excluded from normal synthesis.

## 6. Edge Classes

Edges must be typed by purpose. Do not treat all links as equal.

- `scientific_edge`: supports, contradicts, refines, generalizes, narrows, motivates, tests.
- `provenance_edge`: has_evidence, extracted_from, cites, uses_dataset, uses_notebook.
- `navigation_edge`: related_page, member_of_topic, backlink, next_read.
- `derivation_edge`: produced_by, reused_by, depends_on, derived_from.
- `review_edge`: needs_review, caveat_for, resolves_conflict, supersedes, retracted_by.

Graph rendering and ranking should expose these classes separately.

## 7. Extraction Strategy

### Stage 1 — deterministic structural extraction

No LLM. Extract:

- project metadata and file inventory;
- report headings and source sections;
- key findings and future directions headings/bullets;
- source documents, notebooks, figures, datasets, PMIDs/DOIs;
- explicit project links and data collection names;
- identifier-like entities (`K\d{5}`, `PF\d{5}`, `COG\d+`, GTDB/genome IDs);
- exact source spans with `exact`, `prefix`, `suffix` where possible.

### Stage 2 — skill-driven LLM extraction

LLM extraction is central and publishable, but it is orchestrated by skills and constrained by schema.

The `kg-ingest-project` skill:

1. builds a context pack from deterministic source data;
2. asks the LLM/subagents for statement cards, entities, topic memberships, caveats, conflicts, and
   opportunities;
3. validates outputs with deterministic scripts;
4. retries invalid or weak outputs;
5. writes project KG artifacts;
6. rebuilds graph/wiki/quality reports.

The Python core must never call a model directly. Skills call deterministic scripts, use LLMs for
extraction/synthesis, then validate and write artifacts.

## 8. Context Packs

A context pack is a deterministic JSON/YAML artifact handed to skills. It should contain:

- project metadata and source file hashes;
- section inventory and source text snippets;
- deterministic entities and evidence anchors;
- relevant BERDL collection/schema hints;
- related project hints;
- prior statement cards for neighboring entities/topics;
- OpenViking context when available;
- extraction instructions and allowed vocabularies.

Context packs are hashed. LLM outputs record the hash.

## 9. Synthesis Page Generation

Every generated synthesis page has two artifacts:

1. `page_plan.yaml`: deterministic member set, sections, and source statement IDs.
2. rendered markdown/html: LLM-written prose from the fixed page plan.

The page writer skill may only use the member set and approved context pack. It must cite statement
IDs/source projects. Each section stores a fact/member hash so unchanged sections are not regenerated.

### Page types

- `home`: corpus-level state of science and browse lanes.
- `topic`: cross-project synthesis, caveats, key claims, next actions.
- `claim`: one reusable claim, support/refutation, scope, caveats, downstream uses.
- `conflict`: sides, evidence, affected pages, resolving work.
- `opportunity`: motivating evidence, required data, target output, readiness.
- `direction`: broader research program with child hypotheses/opportunities.
- `hypothesis`: testable statement, data needed, success criteria.
- `project`: extracted statement summary and source trail.
- `entity`: backlink/local graph page grouped by statement kind and topic.

## 10. Skills

### `kg-ingest-project`

Input: `projects/<project_id>`.

Outputs:

- `compendium/context-packs/<project_id>.json`;
- `compendium/kg/projects/<project_id>.yaml`;
- extraction manifest;
- graph/page/quality diff.

### `kg-synthesize-page`

Input: page ID or page seed.

Outputs:

- `compendium/wiki/<page_path>.md` as the human-facing generated page artifact;
- synthesis manifest under `compendium/wiki/.manifests/` with model/prompt/member hash.

### `kg-curate`

Handles retraction, correction, entity merge/split, tier promotion/demotion, and correction-to-regression
fixtures.

### `kg-backfill`

Batch wrapper that calls `kg-ingest-project` project-by-project, records failures, and creates a batch
quality report.

### `kg-review-queue`

Ranks high-centrality, conflicted, low-confidence, or synthesis-critical statements for occasional human
review.

## 11. Deterministic Scripts

Scripts provide the substrate skills rely on. They do not call LLMs.

```bash
compendium audit projects/<id>
compendium context-pack projects/<id> --out compendium/context-packs/<id>.json
compendium validate-card compendium/kg/projects/<id>.yaml
compendium build-graph
compendium plan-pages
compendium render
compendium quality
compendium diff --before <dir> --after <dir>
```

## 12. Artifact Layout

```text
compendium/
  schema/
    synthesis_wiki.yaml
  context-packs/
    <project_id>.json
  kg/
    projects/
      <project_id>.yaml
    corrections/
      *.yaml
    graph/
      nodes.tsv
      edges.tsv
      graph.json
  wiki/
    index.md
    topics/
    claims/
    conflicts/
    opportunities/
    directions/
    .manifests/
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

## 13. Quality Gates

Minimum build gates:

- all statement cards validate against schema;
- every non-retracted statement has evidence;
- every evidence quote resolves by exact/prefix/suffix or is explicitly marked unresolved;
- no dangling links;
- no orphan synthesis pages except intentional indexes;
- topic pages have member statements from at least two projects or are marked single-project;
- claim/opportunity/conflict pages have the required supporting statements;
- graph build and page plans are idempotent across shuffled input order;
- rendered wiki has no broken internal links.

Product-health metrics:

- statement count by kind/tier/source project;
- evidence resolution rate;
- topic coverage;
- claim support/refutation balance;
- active conflicts;
- opportunities with target outputs;
- high-centrality asserted statements;
- pages with no backlinks/outgoing links;
- synthesis pages regenerated in the last build.

## 14. Tracer Scope

Initial tracer remains two ADP1 projects:

- `projects/acinetobacter_adp1_explorer`
- `projects/adp1_deletion_phenotypes`

Required tracer outputs:

- one generated home page;
- one ADP1 topic page;
- one organism entity page;
- at least two claim pages;
- at least one opportunity or future-step page;
- project pages for both projects;
- graph view with typed edge filters;
- quality report with zero broken links/dangling edges.

## 15. Defaults For Open Decisions

- **Home/index entry point:** state-of-the-science home page with browse lanes.
- **LLM publishing:** publish validated LLM extraction as `asserted`; allow promotion to `reviewed`.
- **Current Atlas:** design reference only; do not preserve as source of truth.
- **OpenViking:** optional context-pack input in this branch; deeper integration in separate PR.
- **Implementation package name:** keep `compendium/` unless a later rename is explicitly requested.

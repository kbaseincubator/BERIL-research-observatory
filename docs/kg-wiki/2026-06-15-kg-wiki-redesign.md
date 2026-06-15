# KG-Wiki Redesign: Topic-MOC over a Thin Link Layer — Design + Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the formal/typed knowledge-graph machinery in `compendium/` with a lightweight,
topic-centered "Maps of Content" wiki that one scientist-engineer can maintain, while keeping the parts
that actually make pages good (deterministic source-context packs + statement-level provenance).

**Architecture:** Per-project LLM extraction produces thin statement cards. A single global LLM
*reconcile* pass **autonomously** generates `registry.yaml` (canonical topics + entities + aliases) — it
decides the topic vocabulary itself; no human approval gate. The registry is an **additive** lookup layer
(append/extend only, so canonical keys stay stable across re-runs) — per-project cards are never
rewritten. A deterministic `plan` step joins cards + registry + two zero-LLM indexes (authors by ORCID,
shared data by collection) into page contexts, and an LLM `write` step authors topic/data/author/home
pages. A deterministic `check` step enforces link + citation integrity. The entire flow is driven by
skills (see §2.4) so Claude Code or Codex can run it end-to-end.

**Tech Stack:** Python 3.13 + `uv` (deterministic core, `pytest`), LinkML (one trimmed schema), Markdown
wiki output, Claude Code/Codex skills for extraction, reconciliation, and page authoring, plus a
top-level orchestrator skill that chains the deterministic CLI steps.

---

## 1. Decisions (locked)

These were decided with the maintainer and are not open in this plan:

| # | Decision | Choice |
|---|---|---|
| D1 | Backbone | **Lightweight topic-MOC + thin link layer.** No user-facing typed KG; no Biolink/LinkML entity grounding. |
| D2 | Reconciliation | **Additive `registry.yaml`.** Cards stay immutable; `plan` looks up canonical IDs/aliases. No Pass-3 card rewrite. |
| D3 | Topic governance | **LLM-autonomous.** The reconcile pass clusters raw topics into canonical themes and writes definitions itself; **no human approval gate.** Quality is enforced deterministically (`plan` warns on unresolved topics, `check` fails on broken links). The seed theme list (§5) is an optional prior the LLM may revise, not a fixed vocabulary. `registry.yaml` is git-tracked and human-editable, but edits are never required to ship. |
| D4 | Statement cards | **Keep, thin.** Cards carry provenance + `supports`/`contradicts`/`refines` links (auto-surface conflicts). |
| D5 | Topic definition | A topic is a **cross-cutting theme shared by ≥2 (ideally ≥3) projects.** ~12 topics for 70 projects; a project sits in 1–3. |
| D6 | Literature depth | **Deterministic citation rollup only for v1** (PMID/DOI list per topic). Narrative "what's known / how advanced" deferred to v2. |

### Why (one line each, from the exploration)

- The rendered wiki contains **zero** `curie`/`biolink`/`grounded`/typed-predicate strings; 88% of graph
  edges are navigation/provenance bookkeeping. The KG layer is invisible ceremony.
- Shipping science-synthesis systems (STORM, PaperQA2/WikiCrow, Asta, Elicit, Consensus) don't put a
  formal KG in front of users; the GraphRAG synthesis benefit is *topic clustering*, not typed predicates.
- Authors (70/70 READMEs, ORCID) and shared data (14 canonical collections in `ui/config/collections.yaml`)
  are **deterministically extractable** — the strongest connectors need no LLM.

---

## 2. Target architecture

### 2.1 Data model — one card schema + one registry

**Per-project card** `compendium/kg/<project>.yaml` (≈ what the LLM already emits, trimmed):

```yaml
project: <id>
statements:
  - id: <slug>                                   # stable human slug, not content hash
    kind: finding | claim | opportunity          # 3 kinds (was 9)
    statement: <one sentence>
    confidence: low | medium | high
    about:
      entities: [<registry-key>, ...]            # FK into registry.entities
      topics:   [<registry-key>, ...]            # FK into registry.topics
    links:
      supports:    [<stmt-id>]                    # 3 scientific edges (was 25 across 6 enums)
      contradicts: [<stmt-id>]
      refines:     [<stmt-id>]
    evidence:
      source: REPORT.md
      section: <heading>
      quote: <exact source span>
```

**Global registry** `compendium/registry.yaml` (NEW, LLM-generated; git-tracked and human-editable but not gated):

```yaml
topics:
  metal-resistance:
    label: Metal Resistance & Critical Minerals
    definition: <one line>
    aliases: [metal_fitness, critical-minerals, ...]   # raw per-project topic slugs that merge here
    projects: [metal_fitness_atlas, metal_cross_resistance, ...]   # filled deterministically
entities:
  adp1:
    label: Acinetobacter baylyi ADP1
    kind: organism | dataset | gene | method
    aliases: [a_baylyi_adp1, acinetobacter_baylyi, adp1]
```

**Cut from the data model:** `schema/compendium.yaml` (entire Biolink layer), the over-enumerated half of
`schema/synthesis_wiki.yaml` (6 edge enums + flat `EdgeKindEnum`, 25-value `PageTypeEnum`, `TierEnum`,
`StatementScopeEnum`), per-card `qualifiers`, the 7-field `ExtractionManifest`, `Correction`,
content-addressed ids.

### 2.2 Pipeline — 3 deterministic commands, 4 skills, 4 artifacts

```
projects/* ─[D] pack ─────▶ packs/<project>.json        (audit + bounded source excerpts)
                               │
              ─[LLM] extract ─▶ kg/<project>.yaml         skill: kg-extract
                               │
   ALL cards ─[LLM] reconcile ▶ registry.yaml             skill: kg-reconcile  ★ NEW (global 2nd pass)
                               │
   cards + registry ─[D] plan ▶ out/page-contexts/        (topic / data / author / home contexts)
                               │
              ─[LLM] write ───▶ wiki/*.md                 skill: kg-write
                               │
              ─[D] check ─────▶ exit 0 / nonzero          (link + citation integrity)
```

- **Deterministic (no model):** `pack`, `plan`, `check`. These plus the author/data indexes are pure
  Python, exposed as CLI subcommands so skills (and Claude Code/Codex) can invoke them.
- **LLM skills (3):** `kg-extract` (per project), `kg-reconcile` (once, global, **autonomous**),
  `kg-write` (per page).
- **Orchestrator skill (1):** `kg-wiki` — the single entry point that chains
  pack → extract → reconcile → plan → write → check end-to-end (dispatching `kg-extract`/`kg-write`
  per project/page, parallelizing where possible). This is what a user runs in Claude Code or Codex.
- **Dropped skills:** `kg-curate` (edit YAML + re-run; git is the correction log), `kg-review-queue`
  (no human gate any more — D3), `kg-backfill` (folded into `kg-wiki`'s batch loop), and
  `kg-generate-wiki`/`kg-synthesize-page` (become `kg-wiki` + `kg-write`).

### 2.4 Skills (what Claude Code / Codex invoke)

| Skill | Kind | Responsibility |
|---|---|---|
| `kg-wiki` | orchestrator | Run the whole pipeline (or a filtered subset) over `projects/`. Calls the deterministic CLI steps and dispatches the LLM skills; the only skill a user normally invokes. |
| `kg-extract` | LLM | Extract thin statement cards for **one** project from its deterministic context pack. |
| `kg-reconcile` | LLM | Read all cards' raw topic/entity slugs and **autonomously** emit/extend `registry.yaml` (canonical topics, entities, aliases). No human gate. |
| `kg-write` | LLM | Author **one** wiki page (topic/data/author/home) from a single deterministic page context. |

Each skill's `SKILL.md` documents the exact deterministic CLI commands it shells out to (`compendium
pack`/`plan`/`check`/`validate-card`), so the functionality is fully reachable from skills without the
user memorizing the Python surface.

### 2.3 Page taxonomy — 4 types (was 8)

| Page type | Count | Source | Notes |
|---|---|---|---|
| **Topic** (backbone) | ~12 | registry + cards | MOC template: *Overview → Projects → Adjacent topics → Shared data → Cited literature → Open directions*. Claims/conflicts/opportunities are **sections**, not pages. |
| **Data** | ~14 | `collections.yaml` + cards | One per BERDL collection: which projects share it, reuse/lineage. |
| **Author** | ~12 | README `## Authors` (ORCID) | One per contributor: projects owned, topics touched. |
| **Home** | 1 | all | Topic map + author map + data map. |
| Organism (optional) | ~6 | registry | Materialize only recurring model-system hubs (ADP1, DvH, FW300). |

**Cut as pages (keep as sections/tags):** per-claim, per-opportunity, generic per-entity, per-project
synthesis pages (UI already shows REPORT.md — link out), and `graph.md` (build artifact).

**Citation style change:** drop inline `[stmt:id; project]` brackets from prose; render provenance as
footnotes or a single consolidated "Sources" section so prose reads like the Atlas.

---

## 3. File structure (create / modify / cut)

Paths relative to `compendium/`.

**Create**
- `registry.yaml` — global canonical topics + entities (LLM-seeded, human-curated).
- `src/compendium/people.py` — deterministic author extraction (README `## Authors` → ORCID index).
- `src/compendium/data_index.py` — deterministic shared-collection index (cards/projects → collection).
- `src/compendium/registry.py` — load `registry.yaml`, resolve a raw entity/topic slug → canonical key.
- `skills/kg-reconcile/SKILL.md` — the global, autonomous reconcile pass.
- `skills/kg-wiki/SKILL.md` — orchestrator entry point chaining the full pipeline.
- `tests/test_people.py`, `tests/test_data_index.py`, `tests/test_registry.py`, `tests/test_check.py`.

**Modify**
- `schema/synthesis_wiki.yaml` — trim to: `StatementKindEnum`(3), `ConfidenceEnum`, one `LinkKindEnum`
  (supports/contradicts/refines), `PageTypeEnum`(topic/data/author/home/organism), `StatementCard`,
  `AboutRefs`, `StatementLinks`, `EvidenceAnchor`, `Topic`, `Entity`(registry), `PagePlan`. Remove the
  rest.
- `src/compendium/models.py` — drop `Entity`(KG)/`Assertion`/`Mention`/`ProjectKG`/`Span`; keep the thin
  card + registry dataclasses.
- `src/compendium/pages/plan.py` — page membership for the 4 page types; consult `registry.py`.
- `src/compendium/render/markdown.py` — render 4 page types; footnote citations; no `graph.md`.
- `src/compendium/build/statement_graph.py` — keep in-memory adjacency for `plan`; drop
  `nodes.tsv`/`edges.tsv`/`graph.json` exports and edge-class taxonomy.
- `src/compendium/cli.py` — collapse to: `pack`, `plan`, `check` (+ keep `validate-card`). Remove
  `statement-graph`, `page-context`, `page-artifact`, `wiki-contexts`, `render-markdown` split,
  `quality`, `quality-synthesis`, `review-queue`, `tracer` (or fold tracer into a test).
- `skills/kg-ingest-project/` → rename to `skills/kg-extract/`; trim schema contract to the 6-field card.
- `skills/kg-synthesize-page/` → rename to `skills/kg-write/` (one page-authoring skill).
- `skills/kg-generate-wiki/` → rename to `skills/kg-wiki/`; rewrite as the orchestrator that chains
  pack → extract → reconcile → plan → write → check (absorbs the old `kg-backfill` batch loop).
- `README.md` — update the pipeline description to the 3-command flow (single source of truth).

**Cut**
- `schema/compendium.yaml`, `src/compendium/ids.py`, `src/compendium/extract/structural.py`,
  `src/compendium/quality/review_queue.py`, `src/compendium/quality/synthesis_dashboard.py`,
  `skills/kg-curate/`, `skills/kg-review-queue/`, `skills/kg-backfill/`.
- Tests for the above: `test_ids.py`, `test_structural.py`, `test_review_queue.py`,
  `test_synthesis_quality_dashboard.py`.

---

## 4. Implementation plan

Phases are ordered so the codebase stays green and each phase yields something runnable. Deterministic
tasks are full TDD (test first). LLM-skill tasks specify the contract + acceptance criteria (they can't be
unit-TDD'd, but their *output* is validated by deterministic `validate-card` / `check`).

### Phase 0 — Prune dead weight (no behavior change to live pipeline)

Goal: delete the invisible KG layer and unused quality machinery so the remaining surface is small enough
to refactor confidently. Do this first; it is mostly deletion + fixing imports.

- [ ] **Step 1:** Delete `schema/compendium.yaml`, `src/compendium/ids.py`,
  `src/compendium/extract/structural.py`, `src/compendium/quality/review_queue.py`,
  `src/compendium/quality/synthesis_dashboard.py` and their tests
  (`tests/test_ids.py`, `tests/test_structural.py`, `tests/test_review_queue.py`,
  `tests/test_synthesis_quality_dashboard.py`).
- [ ] **Step 2:** Grep for orphaned imports/refs and remove them:
  Run: `cd compendium && grep -rn "from .ids\|import ids\|structural\|review_queue\|synthesis_dashboard\|compendium.yaml" src tests`
  Expected after fixes: no matches.
- [ ] **Step 3:** Remove the now-dead CLI subcommands (`statement-graph` tsv/json artifacts, `quality`,
  `review-queue`) from `src/compendium/cli.py`. Keep `pack`/`context-pack`, `plan-pages`,
  `validate-card`, `render-markdown` for now (renamed in later phases).
- [ ] **Step 4:** Run the suite to confirm green after pruning.
  Run: `cd compendium && uv run --group test pytest -q`
  Expected: PASS (with the deleted-feature tests removed).
- [ ] **Step 5:** Commit.
  `git add -A && git commit -m "refactor(compendium): drop invisible KG layer and unused quality machinery"`

### Phase 1 — Deterministic author index (zero-LLM connector)

Goal: `people.py` parses every `projects/<id>/README.md` `## Authors` block and `beril.yaml` `authors:`,
normalizes on ORCID, and yields an author→projects index. (Verified: 70/70 READMEs have the block.)

- [ ] **Step 1: Write the failing test** — `compendium/tests/test_people.py`

```python
from compendium.people import parse_authors, build_author_index

README = """# Title
## Authors
- Beril Admin (https://orcid.org/0009-0007-0287-2979), Lawrence Berkeley National Laboratory
- Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory
## Overview
"""

def test_parse_authors_extracts_name_orcid_affiliation():
    authors = parse_authors(README)
    assert authors[0].orcid == "0000-0001-5810-2497" or authors[1].orcid == "0000-0001-5810-2497"
    dehal = next(a for a in authors if a.orcid == "0000-0001-5810-2497")
    assert dehal.name == "Paramvir S. Dehal"
    assert "Lawrence Berkeley" in dehal.affiliation

def test_build_author_index_groups_projects_by_orcid():
    idx = build_author_index({"proj_a": README, "proj_b": README})
    assert sorted(idx["0000-0001-5810-2497"].projects) == ["proj_a", "proj_b"]
```

- [ ] **Step 2: Run it, verify failure.**
  Run: `cd compendium && uv run --group test pytest tests/test_people.py -q`
  Expected: FAIL (`ModuleNotFoundError: compendium.people`).
- [ ] **Step 3: Implement `src/compendium/people.py`** — a `Author` dataclass (`name`, `orcid`,
  `affiliation`), a `parse_authors(readme_text)` that regex-matches the `## Authors` bullet lines
  (`- <name> (https://orcid.org/<id>), <affiliation>`; tolerate missing ORCID/affiliation), and
  `build_author_index(project_to_readme)` returning `{orcid: AuthorRecord(name, projects=[...])}`,
  preferring the longest-seen name per ORCID.
- [ ] **Step 4: Run tests, verify pass.**
  Run: `cd compendium && uv run --group test pytest tests/test_people.py -q` → PASS.
- [ ] **Step 5: Add a corpus smoke check** asserting the real corpus parses (run against `../projects`):
  every project yields ≥1 author and ≥1 valid ORCID for ≥85% of projects (61/70 carry ORCID).
- [ ] **Step 6: Commit.** `git commit -am "feat(compendium): deterministic author index from README authors"`

### Phase 2 — Deterministic shared-data index (zero-LLM connector)

Goal: `data_index.py` maps the 14 canonical collection IDs (`ui/config/collections.yaml`) to the projects
that cite them, reusing the regex extraction already in `audit.py`.

- [ ] **Step 1: Write the failing test** — `compendium/tests/test_data_index.py`

```python
from compendium.data_index import build_collection_index

def test_groups_projects_by_canonical_collection():
    cited = {  # project -> set of raw collection mentions
        "metal_fitness_atlas": {"kbase_ke_pangenome", "kescience_fitnessbrowser"},
        "amr_pangenome_atlas": {"kbase_ke_pangenome"},
    }
    canonical = {"kbase_ke_pangenome", "kescience_fitnessbrowser", "enigma_coral"}
    idx = build_collection_index(cited, canonical)
    assert sorted(idx["kbase_ke_pangenome"].projects) == ["amr_pangenome_atlas", "metal_fitness_atlas"]
    assert idx["kescience_fitnessbrowser"].projects == ["metal_fitness_atlas"]
    assert "enigma_coral" not in idx  # no project cites it -> omitted
```

- [ ] **Step 2: Run it, verify failure.**
  Run: `cd compendium && uv run --group test pytest tests/test_data_index.py -q` → FAIL.
- [ ] **Step 3: Implement `src/compendium/data_index.py`** — load canonical IDs from
  `ui/config/collections.yaml` (`collections[].id`), reuse `audit.py`'s collection-mention extraction,
  and return `{collection_id: CollectionRecord(projects=[...])}`, dropping collections no project cites.
- [ ] **Step 4: Run tests, verify pass.** → PASS.
- [ ] **Step 5: Commit.** `git commit -am "feat(compendium): deterministic shared-collection index"`

### Phase 3 — Registry + reconcile (the global 2nd pass)

Goal: an autonomously generated `registry.yaml` plus deterministic resolution. The LLM produces the registry;
`registry.py` applies it; `plan` consults it. **Cards are never rewritten (D2).**

- [ ] **Step 1: Write the failing test for resolution** — `compendium/tests/test_registry.py`

```python
from compendium.registry import Registry

RAW = {
  "topics": {"metal-resistance": {"label": "Metal Resistance & Critical Minerals",
                                   "definition": "x", "projects": []}},
  "entities": {"adp1": {"label": "Acinetobacter baylyi ADP1", "kind": "organism",
                        "aliases": ["a_baylyi_adp1", "acinetobacter_baylyi", "adp1"]}},
}

def test_resolves_entity_alias_to_canonical_key():
    reg = Registry(RAW)
    assert reg.entity_key("a_baylyi_adp1") == "adp1"
    assert reg.entity_key("ADP1") == "adp1"            # case-insensitive
    assert reg.entity_key("unknown_x") == "unknown_x"  # unknown passes through unchanged

def test_resolves_topic_key():
    reg = Registry(RAW)
    assert reg.topic_key("metal-resistance") == "metal-resistance"
```

- [ ] **Step 2: Run it, verify failure.** → FAIL.
- [ ] **Step 3: Implement `src/compendium/registry.py`** — `Registry(raw_dict)` building a case-folded
  alias→canonical map for entities and a topic-key set; `entity_key()`/`topic_key()` return the canonical
  key or pass the input through unchanged when unknown (additive, never destructive).
- [ ] **Step 4: Run tests, verify pass.** → PASS. Commit.
  `git commit -am "feat(compendium): additive registry resolution layer"`
- [ ] **Step 5: Write `skills/kg-reconcile/SKILL.md`.** This skill runs **autonomously** — it owns the
  topic vocabulary and ships without a human approval step (D3). Contract:
  - **Input:** the deduped flat list of every `about.entities` + `about.topics` slug across all
    `kg/*.yaml` (a few hundred strings), the seed topic themes (from §5, **as an optional prior the LLM
    may revise, merge, split, or rename**), and the existing `registry.yaml` (for append-only updates).
  - **Output:** an updated `registry.yaml` only — canonical `entities` (with `aliases`, `kind`) and the
    canonical `topics` the LLM decides on (each raw topic mapped into exactly one canonical theme;
    one-line definition). The LLM chooses the topic set and granularity itself, guided by D5 (a topic
    spans ≥2, ideally ≥3 projects; aim ~12 for 70 projects).
  - **Prohibitions:** never edit `kg/*.yaml`; never delete an existing canonical key (append/extend only,
    so keys stay stable across runs); never invent entities not present in the input list.
  - **Acceptance (deterministic, no human gate):** every raw topic slug maps to a canonical topic, and
    running `plan` then `check` after reconcile produces no "unresolved topic/entity" warnings and no
    broken links. These guards — not a human reviewer — are what make autonomy safe.
- [ ] **Step 6:** Run reconcile over the current `kg/*.yaml` (3 ADP1 projects) to produce the first
  `registry.yaml`; verify `plan` + `check` pass clean, then commit the registry.
  `git commit -am "feat(compendium): generate registry.yaml via autonomous kg-reconcile"`

### Phase 4 — Page plan + render for the 4 page types

Goal: `plan.py` emits topic/data/author/home page contexts (joining cards + registry + author index +
data index); `render/markdown.py` writes the 4 page types with footnote citations and the topic MOC
template; no `graph.md`.

- [ ] **Step 1: Write the failing test for topic membership** — extend `tests/test_page_planner.py`

```python
def test_topic_page_collects_member_projects_and_statements(sample_cards, sample_registry):
    plans = plan_pages(sample_cards, sample_registry, authors, data_index)
    topic = next(p for p in plans if p.type == "topic" and p.id == "metal-resistance")
    assert set(topic.projects) >= {"metal_fitness_atlas", "metal_cross_resistance"}
    assert topic.sections[0].heading == "Overview"
    assert any(s.heading == "Shared data" for s in topic.sections)
```

- [ ] **Step 2: Run it, verify failure.** → FAIL.
- [ ] **Step 3: Implement** the 4-page-type membership in `pages/plan.py`: group cards by resolved topic
  key; attach member projects, adjacent topics (topics sharing ≥1 project), shared-data rows (from
  `data_index`), cited PMIDs/DOIs (regex rollup), and open directions (`kind == opportunity`). Author/data
  page plans come from the Phase 1/2 indexes. Drop claim/opportunity/entity/project page types.
- [ ] **Step 4: Run tests, verify pass.** → PASS.
- [ ] **Step 5: Rework `render/markdown.py`** to emit `wiki/topics/`, `wiki/data/`, `wiki/authors/`,
  `wiki/index.md` with the MOC template and a single consolidated **Sources** footnote section per page
  (no inline `[stmt:id; project]`). Remove `graph.md` emission. Update `tests/test_page_artifact.py`
  to assert prose paragraphs contain no inline `[stmt:` bracket and that a Sources section exists.
- [ ] **Step 6:** Run suite. → PASS. Commit.
  `git commit -am "feat(compendium): topic/data/author/home pages with footnote provenance"`

### Phase 5 — Integrity check + rename skills + README

- [ ] **Step 1: Write the failing test** — `compendium/tests/test_check.py`

```python
def test_check_flags_broken_wiki_link(tmp_wiki_with_dangling_link):
    problems = check_wiki(tmp_wiki_with_dangling_link)
    assert any("dangling" in p for p in problems)

def test_check_passes_clean_wiki(tmp_clean_wiki):
    assert check_wiki(tmp_clean_wiki) == []
```

- [ ] **Step 2: Run it, verify failure → implement `check` in `cli.py`** (~30 lines: every relative
  Markdown link resolves to a file; every footnote source ref exists in some card). Run: PASS.
- [ ] **Step 3:** Settle the skill set (§2.4): rename `skills/kg-ingest-project` → `skills/kg-extract`
  (trim schema contract to the 6-field card); rename `skills/kg-synthesize-page` → `skills/kg-write`;
  rename `skills/kg-generate-wiki` → `skills/kg-wiki` and rewrite it as the orchestrator that chains
  pack → extract → reconcile → plan → write → check (dispatching `kg-extract`/`kg-write` per project/page,
  parallel where possible, absorbing the old batch loop); delete `skills/kg-curate`,
  `skills/kg-review-queue`, `skills/kg-backfill`. Each surviving `SKILL.md` lists the exact `compendium`
  CLI commands it shells out to, so the full flow is runnable from Claude Code/Codex via the skills.
- [ ] **Step 4:** Rewrite `compendium/README.md` to the 3-command flow (`pack` → extract → reconcile →
  `plan` → write → `check`) as the single source of truth.
- [ ] **Step 5:** Full suite green. Commit.
  `git commit -am "feat(compendium): integrity check, slim skills, updated README"`

### Phase 6 — Backfill over the real corpus (validation, not code)

- [ ] **Step 1:** Invoke the `kg-wiki` orchestrator skill over a first batch (~10 diverse projects from
  §5); it runs pack → `kg-extract` (per project) → `kg-reconcile` → `plan` → `kg-write` (per page) → check.
- [ ] **Step 2:** Inspect the autonomously generated `registry.yaml` (sanity, not approval — `check`
  already gates correctness); open `wiki/index.md` and 2–3 topic pages and confirm cross-project
  connections (shared data, shared authors, supports/contradicts) actually render.
- [ ] **Step 3:** If a topic split looks off, adjust the §5 prior or the `kg-reconcile` prompt and re-run
  (no card changes needed — registry is additive). Then run the orchestrator over all 70 projects.

---

## 5. Seed topic list (optional prior for `kg-reconcile`)

This is a **prior, not a fixed vocabulary** — `kg-reconcile` decides the final topics autonomously (D3)
and may revise, merge, split, or rename these. Empirically derived from all 70 project titles/reports;
project counts approximate:

1. AMR & the Resistome (~8) · 2. Metal Resistance & Critical Minerals (~11) · 3. Pangenome Architecture:
Core/Accessory & Openness (~9) · 4. Gene Fitness & Genotype→Phenotype (~10) · 5. Functional Dark Matter &
Annotation Gaps (~6) · 6. Microbial Ecotypes & Niche Differentiation (~6) · 7. Subsurface & Clay-Confined
Genomics (ENIGMA) (~7) · 8. Mobile Genetic Elements & HGT (~5) · 9. Metabolic Capability, Pathways &
Dependency (~8) · 10. *A. baylyi* ADP1 Model System (~6) · 11. Environment, Biogeography & Geospatial
Embeddings (~6) · 12. Microbiome Engineering & Health Applications (~3).

A project belongs to 1–3 topics; the overlap *is* the connection structure (e.g.
`prophage_amr_comobilization` bridges AMR + MGE).

---

## 6. Out of scope (v1)

- Narrative literature synthesis ("what's known in the literature", "how projects advanced it"). Only a
  deterministic PMID/DOI rollup per topic ships in v1 (D6).
- Embedding-based entity clustering (the autonomous LLM reconcile pass is sufficient at a few-hundred
  slugs; embeddings reintroduce non-determinism and complexity).
- Per-claim / per-opportunity / generic per-entity / per-project pages.
- Any live-LLM call at UI request time (the UI reads the checked-in Markdown wiki, unchanged).

---

## 7. Self-review — spec coverage

| Decision/requirement | Covered by |
|---|---|
| D1 drop typed KG | Phase 0; §3 cuts |
| D2 additive registry | Phase 3 (`registry.py`, no card rewrite) |
| D3 autonomous topic governance | Phase 3 Step 5–6 (LLM owns topics; guarded by `plan`+`check`, no human gate) |
| All functionality as skills | §2.4; Phase 5 Step 3 (`kg-wiki` orchestrator + `kg-extract`/`kg-reconcile`/`kg-write`) |
| D4 keep thin cards | §2.1 card schema; links preserved |
| D5 topic definition/granularity | Phase 3/4 membership rule; §5 seed list |
| D6 literature rollup only | Phase 4 Step 3 (PMID/DOI rollup); §6 |
| Authors connector | Phase 1 |
| Shared-data connector | Phase 2 |
| 4 page types | Phase 4 |
| Footnote citations (drop inline) | Phase 4 Step 5 |
| 4 skills / 3 commands | §2.4; Phase 5 |
| Integrity check | Phase 5 Step 1–2 |

Gaps: none blocking. The `kg-extract`/`kg-write`/`kg-reconcile` skill *prompts* are specified by contract
(inputs/outputs/acceptance), not pre-written prose — intentional, since they are LLM steps validated by
deterministic `validate-card` and `check`.

---

## 8. Addendum A (2026-06-15): coupling corrections from baseline code-read

A read of the actual `compendium/src` before implementation found that **Phase 0 is a refactor, not a
pure deletion** — the "dead KG layer" is entangled with modules we keep. Corrections (these supersede the
optimistic "cut" lines in §3/Phase 0):

1. **`ids.py` is not fully dead.** Live modules use only two pure helpers: `ids.normalize` and
   `ids.content_hash` (member-hashing for page-reuse) — `build/statement_graph.py:108,383,509,536,574`,
   `pages/artifact.py:297`, `pages/plan.py:42`. (Other `ids.` hits in `plan.py` are a local dict named
   `ids`, not the module.) **Action:** keep `ids.py` trimmed to `normalize` + `content_hash`; delete only
   `node_id` / `assertion_id` (the content-addressed Biolink ids) once `structural.py` is gone.

2. **`context_pack.py` depends on `extract/structural.py`.** `context_pack.py:50` calls
   `extract_project()` and embeds its `ProjectKG` scaffold (project meta + typed entities/mentions/
   assertions) into the pack. So `structural.py` + the `ProjectKG`/`Entity`/`Assertion`/`Mention`/`Span`/
   `Evidence`/`ProjectMeta` model half are **feeders of the context pack we keep**, not orphans.
   **Action (new Phase R, replaces the structural/ids parts of Phase 0):** rework `context_pack.py` to
   drop the typed scaffold — keep project meta (title from `beril.yaml`/README H1; **authors from the new
   `people.py`**) + source excerpts, and optionally a flat `candidate_terms` string list from audit
   anchors as soft extraction hints. *Then* delete `extract/`, the dead model classes, and
   `node_id`/`assertion_id`. This makes Phase R depend on Phase 1 (`people.py`).

3. **Tests need updating, not just deletion:** `test_structural.py` (delete), `test_ids.py` (trim to the
   two kept helpers), and `test_validate.py` / `test_statement_card_fixture.py` / `test_cli_commands.py`
   (drop `ProjectKG`/`validate-project-kg` references).

### Revised build order (supersedes the Phase 0→6 ordering for execution)

- **Batch A — additive deterministic modules (no edits to live files):** `people.py` (Phase 1),
  `data_index.py` (Phase 2), `registry.py` (Phase 3 resolution). New files + unit tests only; CLI wiring
  deferred. Lowest risk, highest immediate value. **← building now.**
- **Phase R — entangled prune + `context_pack` rework** (depends on Batch A's `people.py`).
- **Phase 4** — page plan + render for the 4 page types (also removes remaining `ids`/graph ceremony).
- **Phase 5** — integrity `check` + skill consolidation + README + CLI trim (single shared-file edit pass).
- **Phase 3-LLM / Phase 6** — `kg-reconcile` skill + orchestrated corpus backfill.

Baseline before Batch A: `uv run --group test pytest` = **85 passing**. This is the green bar every batch
must preserve.

### Progress log

- **Batch A — DONE** (suite 85 → 99). `people.py`, `data_index.py`, `registry.py` built + unit-tested.
  Adversarial corpus verification caught real author-parsing bugs (nested sub-bullets, em-dash
  affiliations, ORCID/name fragmentation) — fixed; author index is clean (17 distinct people, Dehal 39 /
  Arkin 10). `data_index` made deterministic (`sorted(canonical)`).
- **Phase R — DONE** (suite 99 → 80; the drop is deleted-subject tests, coverage intact).
  - R1: `context_pack` reworked to v2 — meta from `audit` + `people`, `candidate_terms` from
    `source_anchors`; deleted `extract/structural.py`, the transition-KG model classes
    (`Span`/`Mention`/`Entity`/`Evidence`/`Assertion`/`ProjectMeta`/`ProjectKG`), and `ids.node_id`/
    `assertion_id` (kept `normalize`/`content_hash`). Verified on 6 real projects.
  - R2 (partial, by design): deleted `schema/compendium.yaml`; removed the `validate-project-kg` and
    `review-queue` CLI surfaces and the `--dashboard-out` path. **Deferred to Phase 5 (coupled cluster):**
    `review_queue.py`, `synthesis_dashboard.py`, the `quality` command, and `tracer` all still consume
    each other — delete them together, then inline `validate_project_kg_file` (now a StatementCard loader,
    not a ProjectKG validator) into `_load_statement_cards`.
  - Known leftover (pre-existing, not Phase R's doing): `context_pack.py` still has orphaned
    `_source_files`/`_source_sections`/`_markdown_sections`/`_section_dict`/`_line_starts`/`_line_at`
    helpers (build sources these from `audit`). Delete in the Phase 4/5 cleanup.
- **Next: Phase 4** — deterministic page-model rework (topic/data/author/home), wire registry + author +
  data indexes into `plan`, footnote citations, drop `graph.md`. Then Phase 5 (check + CLI trim + cluster
  deletion + skills), then the LLM skills + corpus backfill.
- **Deferred: card-schema shrink** (kind 9→3, drop `scope`/`tier`). Not required for function; fold into
  Phase 4/5 where it touches validation + fixtures, or let the new `kg-extract` emit the trimmed shape.

### Addendum B: Phase 4 detailed page-model design (grounded in the current code)

The current `pages/plan.py` emits home/project/topic/entity/claim/opportunity pages, groups by **raw**
`card.about.topics`, and takes only `cards`. Phase 4 reworks it to the 4 page types, canonicalizing via
the registry and wiring in the author + collection indexes. Because `tracer`/`quality`/`page-artifact`
consumed the old plan shape, the cluster-removal step runs first; then Phase 4 is one coherent change
across `plan.py` + `pages/artifact.py` + `render/markdown.py` + `context_pack`-adjacent context + pipeline
wiring + tests (suite goes green at the end of the bundle).

**New signature:** `plan_pages(cards, *, registry=None, authors=None, collections=None)` where
`registry` is a `compendium.registry.Registry` (or None → identity), `authors` is
`people.build_author_index(...)` output (`{key: AuthorRecord}`), `collections` is
`data_index.build_collection_index(...)` output (`{id: CollectionRecord}`). Canonicalize every
`card.about.topics` via `registry.topic_key` and `card.about.entities` via `registry.entity_key` before
grouping.

**Page types (drop project/claim/conflict/opportunity/direction/hypothesis/entity standalone pages):**

| Type | id | members | sections (statement groupings) | outgoing cross-links |
|---|---|---|---|---|
| `home` | `home` | all active cards | Cross-Project Overview · Topic Map · Author Map · Data Map | every page |
| `topic` | canonical topic key | cards with that canonical topic (+ linked claim/conflict/opportunity) | Overview · Key Claims · Conflicts & Caveats · Open Directions | adjacent topics (share ≥1 project), data pages (collections those projects cite), author pages (authors of those projects) |
| `data` | `data:<collection_id>` | cards from projects in the collection's record | Overview · Projects Using This Collection | topic + author pages of those projects |
| `author` | `author:<slug(orcid or name)>` | cards from that author's projects | Overview · Projects · Topics | topic + data pages of those projects |

Findings fold into Overview (no standalone finding pages). Claims/conflicts/opportunities are **sections
inside topic pages**, not pages.

**`pages/artifact.py`:** `_PAGE_DIRS = {"topic": "topics", "data": "data", "author": "authors"}`;
`wiki_page_path`: home→`index.md`, else `<dir>/<slug(id-tail)>.md`. Keep `_validate_authored_markdown`
(the `[stmt:id; project]` citation guard) — the inline→footnote move is a `kg-write` prompt choice; the
validator matches the ref anywhere, so a consolidated "Sources" section satisfies it. Author/data/home
pages may have members but need not be cited unless they have member statements.

**`render/markdown.py`:** drop `graph.md` emission and its stale-artifact expectation (graph is a build
artifact, not a reader page); keep the authored-page + manifest validation and stale-page rejection.

**`models.py`:** ensure `PAGE_TYPES` ⊇ {home, topic, data, author}; remove the now-unused page types when
convenient (not required for green).

**Pipeline wiring (`plan-pages`, `wiki-contexts`):** load `compendium/registry.yaml` if present
(`Registry.from_yaml`), build the author index over `--source-root` READMEs and the collection index from
`ui/config/collections.yaml` + audit collection anchors, and pass all three into `plan_pages`.

**Tests:** a multi-project fixture (cards across ≥2 topics/projects/authors/collections + a small
registry) exercising: topic canonicalization/merge, data & author page generation, cross-links, and an
end-to-end `plan → build_page_context → (hand-authored page) → render` smoke that validates clean.

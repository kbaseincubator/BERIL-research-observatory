# Compendium Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Steps use `- [ ]` checkboxes. This plan is the blueprint for an autonomous build; the deterministic core is fully built+tested, LLM steps are skills demonstrated on 1–2 projects.

**Goal:** Build `compendium/` — a deterministic, knowledge-graph-centered scientific aggregation wiki distilled from `projects/`, distinct from the existing hand-authored `atlas/`.

**Architecture:** A pure-Python deterministic core (parse → ground → verify → canonicalize → assemble KGX → render) with content-addressed identity, honest entity-only tiers (`grounded/asserted/conflict`), and reproducible-build determinism. LLM steps (extraction enrichment, cross-project synthesis, narration, correction) are portable skills that dispatch subagents; the live render never calls an LLM. Full design: `docs/kg-wiki/2026-06-01-kg-wiki-design.md`.

**Tech Stack:** Python ≥3.11, pydantic, LinkML (schema), networkx (+ KGX-style TSV), Jinja2 (static render), Cytoscape.js (vendored, graph page), pytest. Package manager: uv.

**Scope guardrails (per user):** Do NOT ingest all 70 projects — build + test on **2 projects** (`acinetobacter_adp1_explorer`, `adp1_deletion_phenotypes`; shared organism *A. baylyi* ADP1). Tests + KG-quality + wiki-quality assessment are first-class.

---

## File structure

```
compendium/
  README.md
  schema/compendium.yaml              # LinkML: entity/synthesis/assertion/tier model
  src/compendium/
    __init__.py
    models.py                         # pydantic data contracts (shared by all modules)
    ids.py                            # content-addressed id helpers (node/assertion hashing, canonical serialization)
    audit.py                          # Phase-0 corpus-structure audit
    extract/structural.py             # Stage-1 deterministic parser  -> ProjectKG
    ground/grounder.py                # deterministic dict+regex grounder (Gilda stub)
    ground/dictionary.yaml            # curated label->CURIE seed (organisms, etc.)
    verify/verifier.py                # auto-verification -> assertion tiers
    build/canonicalize.py             # union-find merges, content-addressed ids -> Graph
    build/assemble.py                 # ProjectKGs(+corrections) -> Graph -> KGX nodes/edges TSV
    build/layout.py                   # deterministic seeded layout (x,y)
    corrections.py                    # load + apply correction override layer
    render/render.py                  # deterministic Jinja render -> static site (pages + graph.json)
    render/templates/*.html.j2        # entity, synthesis, graph, index templates
    render/static/cytoscape.min.js    # vendored (pinned)
    quality/kg_quality.py             # KG quality metrics
    quality/wiki_quality.py           # wiki quality metrics
    cli.py                            # `compendium audit|build|render|quality|all`
  skills/                             # LLM-step SKILL.md (kg-extract, kg-synthesize, kg-correct, kg-narrate)
  kg/                                 # generated per-project kg.yaml (tracer location; spec seam = projects/<p>/)
  corrections/                        # human correction records (append-only yaml)
  out/                                # generated KGX + site (gitignored)
  tests/                              # pytest suite (see Task list)
  fixtures/                           # tiny synthetic projects for deterministic tests
```

Add to root `pyproject.toml`: a `compendium` package entry + deps (`pydantic`, `jinja2`, `networkx`, `pyyaml`, `linkml-runtime`) and a `compendium` script.

## Core data contracts (`compendium/models.py`) — the shared interface every module codes against

```python
class Span(BaseModel): file: str; heading: str|None; char: tuple[int,int]; quote: str
class Mention(BaseModel): id: str; label: str; type: str; span: Span
class Entity(BaseModel): node: str; type: str; label: str; curie: str|None=None; mentions: list[str]=[]; confidence: float=1.0; tier: str="asserted"
class Evidence(BaseModel): span: Span|None=None; notebook: str|None=None; figure: str|None=None; dataset: str|None=None; p_value: float|None=None
class Assertion(BaseModel): id: str; kind: str; s: str|None=None; p: str|None=None; o: str|None=None; polarity: str|None=None; statement: str|None=None; supported_by: list[str]=[]; entities: list[str]=[]; evidence: Evidence|None=None; extractor: dict=...; tier: str="asserted"
class ProjectMeta(BaseModel): id: str; title: str; authors: list[dict]=[]; status: str|None=None; report_hash: str|None=None; stage1_coverage: float=0.0; extraction: dict={}
class ProjectKG(BaseModel): project: ProjectMeta; mentions: list[Mention]=[]; entities: list[Entity]=[]; assertions: list[Assertion]=[]
class Node(BaseModel): id: str; type: str; label: str; curie: str|None=None; tier: str="asserted"; x: float=0.0; y: float=0.0; provenance: list[str]=[]
class Edge(BaseModel): s: str; p: str; o: str; tier: str="asserted"; evidence: list[str]=[]; provenance: list[str]=[]
class Graph(BaseModel): nodes: list[Node]=[]; edges: list[Edge]=[]
class Correction(BaseModel): id: str; targets: list[str]; kind: str; value: dict={}; scope: str="instance"; proposed_rule: dict|None=None; rationale: str; author: str; timestamp: str
class Page(BaseModel): slug: str; title: str; type: str; sections: list[dict]; links: list[str]; fact_hash: str
```

**Identity rules (`ids.py`):** `node_id = "n:"+blake2(normalize(label)+"|"+type)[:12]`; `assertion_id = "a:"+blake2(s+"|"+p+"|"+o)[:12]` (claim assertions: hash the normalized statement). `canonical_triples(graph)` returns triples sorted by (s,p,o) with normalized literals — used for graph hash + idempotency.

---

## Tasks

### Task 0 — Package scaffold + models + ids (FOUNDATION, main loop, do first)
**Files:** create `compendium/src/compendium/{__init__,models,ids}.py`, `compendium/schema/compendium.yaml`, update `pyproject.toml`, `compendium/.gitignore` (`out/`).
- [ ] models.py with the contracts above; ids.py with hashing + `canonical_triples`.
- [ ] LinkML schema mirroring the entity/synthesis/assertion/tier model (Biolink-aligned classes; predicates; tier enum `grounded|asserted|conflict`).
- [ ] `tests/test_ids.py`: same (label,type) → same node id; different order of triples → identical `canonical_triples`. Run: `uv run pytest compendium/tests/test_ids.py -v` → PASS.
- [ ] Commit.

### Task 1 — Phase-0 corpus audit (`audit.py`)
**Files:** `compendium/src/compendium/audit.py`, `compendium/tests/test_audit.py`, `compendium/fixtures/`.
**Contract:** `audit_corpus(projects_dir: Path) -> AuditReport` (per-project: which files exist, heading inventory, detected metadata source, parser-field coverage 0..1; corpus rollup).
- [ ] Failing test on a tiny fixture project (one REPORT.md with known headings) asserting coverage + heading list.
- [ ] Implement: walk dirs, presence of REPORT/RESEARCH_PLAN/README/beril.yaml/REVIEW, parse `^#{1,3} ` headings, compute coverage of required sections (Key Findings, Data, Future Directions, References).
- [ ] CLI `compendium audit` prints rollup + writes `out/audit.json`.
- [ ] Tests PASS; commit.
**Acceptance:** running on the 2 ADP1 projects reports ≥0.9 coverage (they have all canonical sections).

### Task 2 — Stage-1 deterministic extractor (`extract/structural.py`)
**Files:** `extract/structural.py`, `tests/test_structural.py`.
**Contract:** `extract_project(project_dir: Path) -> ProjectKG`. Deterministic, no LLM.
Extraction rules (from observed REPORT.md structure):
- Project: title from `# Report: <title>`; authors/status from `beril.yaml` if present else README; `report_hash` = blake2 of REPORT.md bytes; `stage1_coverage` from audit.
- Findings: each `### N. <statement>` under `## Key Findings` → an `Assertion(kind="finding", statement=..., evidence span=heading range)`.
- Future Directions bullets → `Assertion(kind="opportunity", statement=...)`.
- Datasets: under `## Data`/`### Sources`, backticked table names + known BERDL collection tokens → `Entity(type="Dataset")` + `Assertion(kind="relation", p="uses")`.
- Publications: `## References` PMIDs (`PMID:\d+`)/DOIs → `Entity(type="Publication")`.
- Biology entities via regex+dictionary: organism dictionary (e.g. "Acinetobacter baylyi ADP1"), gene/ortholog ids (`K\d{5}`,`COG\d{3,4}`,`PF\d{5}`), → `Mention` + `Entity`.
- Notebooks/figures under `## Supporting Evidence` → provenance on relevant assertions.
- [ ] Failing test on fixture asserting N findings, dataset entities, organism mention.
- [ ] Implement; assertion ids via `ids.py` (stable).
- [ ] PASS; commit.

### Task 3 — Grounder (`ground/grounder.py` + `dictionary.yaml`)
**Contract:** `ground(pkg: ProjectKG) -> ProjectKG` — sets `Entity.curie` where resolvable. Deterministic: curated dictionary (`A. baylyi ADP1 → NCBITaxon:62977`, etc.) + regex passthrough (`K12345→KEGG:K12345`, `PF…→Pfam:…`, `COG…→COG:…`, `PMID:…`). Gilda is a documented future swap-in (no LLM).
- [ ] Test: known organism → NCBITaxon CURIE; `K00845` → `KEGG:K00845`; unknown → None.
- [ ] Implement; PASS; commit.

### Task 4 — Auto-verification (`verify/verifier.py`)
**Contract:** `verify(pkg, project_dir) -> ProjectKG` — sets each `Assertion.tier`: `grounded` if all referenced entities are grounded (curie set) AND its evidence span quote is found verbatim in the source file; else `asserted`. (Conflict assigned later at graph build across projects.) Deterministic, no LLM. *Tier never claims relation truth.*
- [ ] Test: assertion with grounded entities + matching span → grounded; ungrounded entity → asserted; span quote not found → asserted.
- [ ] Implement; PASS; commit.

### Task 5 — Canonicalize + assemble + layout (`build/`)
**Contract:** `build(pkgs: list[ProjectKG], corrections: list[Correction]) -> Graph`:
- apply corrections override (Task 7) first; resolve entities to canonical `Node`s by `node_id` (union-find merges on shared curie / force-merge corrections, deterministic precedence: curie-bearing wins else lexicographic; record redirects);
- emit `Edge`s from relation assertions (+ provenance, tier); cross-project edges arise naturally from shared nodes;
- **conflict detection:** two `grounded` relation edges with same (s,p) but opposing polarity, or same (s,o) contradictory p → mark both `tier="conflict"` + a `Conflict` synthesis node;
- `to_kgx(graph, out_dir)` writes sorted `nodes.tsv`/`edges.tsv`; `layout(graph, seed=0)` sets deterministic x,y (networkx spring_layout with fixed seed, rounded).
- [ ] **Idempotency test (critical):** `build(shuffle(pkgs), shuffle(corrections))` → identical `canonical_triples` + identical KGX bytes across 5 shuffles.
- [ ] Test: 2 projects sharing ADP1 organism → single canonical Organism node with provenance from both (cross-project link).
- [ ] Implement; PASS; commit.

### Task 6 — Render (`render/render.py` + templates)
**Contract:** `render_site(graph, out_dir, narration=None) -> list[Page]`. Deterministic Jinja → static HTML:
- per-entity pages (`/wiki/<node>.html`) with facts, **tier badges**, provenance links, Mermaid neighborhood;
- synthesis-unit pages (Topic/Conflict/Opportunity) listing member assertions;
- `/wiki/graph.html` embedding vendored Cytoscape over baked `graph.json` (preset coords from layout);
- `index.html` (home) with rollup + links; each `Page.fact_hash` = blake2 of its canonical section facts (section-level).
- [ ] Test: render produces an Organism page containing both projects' findings + a graph.json with the shared node; no broken internal links.
- [ ] Implement; PASS; commit.

### Task 7 — Corrections overlay (`corrections.py`)
**Contract:** `load_corrections(dir) -> list[Correction]`; applied inside Task 5 build at highest precedence, keyed to content-addressed ids; supports `retract|fix-value|reground|force-merge|force-split|promote|demote`.
- [ ] Test: a `reground` correction overrides an entity curie and **survives a re-extract** (same assertion id); a `retract` removes an edge.
- [ ] Implement; PASS; commit.

### Task 8 — KG quality assessment (`quality/kg_quality.py`)
**Contract:** `assess_kg(graph) -> dict`: node/edge counts by type; **tier distribution** (grounded/asserted/conflict %); **grounding rate** (entities with curie); **provenance completeness** (edges with ≥1 source span); **orphan nodes**; **dangling edges**; cross-project edge count.
- [ ] Test on a known small graph asserting metric values.
- [ ] Implement; CLI `compendium quality --kg`; PASS; commit.

### Task 9 — Wiki quality assessment (`quality/wiki_quality.py`)
**Contract:** `assess_wiki(site_dir, graph) -> dict`: page count by type; **coverage** (entities/assertions with a page); **broken internal links**; **pages per tier**; **% pages with provenance link**; orphan pages.
- [ ] Test on a rendered fixture site.
- [ ] Implement; CLI `compendium quality --wiki`; PASS; commit.

### Task 10 — CLI + end-to-end (`cli.py`)
**Contract:** `compendium audit|build|render|quality|all [--projects ...]`. `all` runs audit→extract→ground→verify→build→render→quality on the named projects, writing `kg/<p>.yaml`, `out/{nodes,edges}.tsv`, `out/site/`, `out/quality.json`.
- [ ] e2e test: `all --projects acinetobacter_adp1_explorer adp1_deletion_phenotypes` exits 0, produces shared ADP1 node, both findings on the organism page, quality.json with tier distribution.
- [ ] Implement; PASS; commit.

### Task 11 — LLM-step skills (SKILL.md, portable; demonstrated not unit-tested)
**Files:** `compendium/skills/{kg-extract,kg-synthesize,kg-correct,kg-narrate}/SKILL.md`.
- [ ] `kg-extract`: dispatch subagents to enrich a project's `kg.yaml` with typed relation assertions + spans (schema-constrained, validate-retry, provenance manifest). Cache by content hash.
- [ ] `kg-synthesize`: given a synthesis page's deterministic member set, write a cached, cited, tier-flagged cross-project narrative.
- [ ] `kg-correct`: NL → resolve target assertions via the KG → write structured `corrections/*.yaml` + proposed rule → rebuild.
- [ ] `kg-narrate`: section-level prose from committed facts.
- [ ] Commit.

### Task 12 — Demo the LLM synthesis on the 2 projects
- [ ] Run `compendium all` on the 2 projects (deterministic).
- [ ] Dispatch a subagent (kg-synthesize) to write the ADP1 Organism page's cross-project synthesis narrative from its member findings (cited + tier-flagged); inject as `narration` into render.
- [ ] Re-render; confirm the page reads like a short review and cites the 2 projects' findings. Commit the sample site.

## Testing & quality strategy
- **Unit tests** per module (Tasks 1–9). **Idempotency test** (Task 5) is the determinism gate. **e2e test** (Task 10) on the 2 ADP1 projects.
- **KG quality** (Task 8) + **wiki quality** (Task 9) run in `compendium all` and are asserted in the e2e test (e.g. grounding rate > 0, 0 dangling edges, 0 broken links).
- CI target: `uv run pytest compendium/tests -v` all green; `compendium all --projects <2>` exits 0 with quality thresholds met.

## Self-review notes
- Spec coverage: identity/canonicalization (Task 0/5), tiers grounded/asserted/conflict (Task 4/5), corrections survive re-extraction (Task 7), cross-project synthesis (Task 11/12), Phase-0 audit gate (Task 1), KG+wiki quality (Tasks 8/9), deterministic render (Task 6). Cross-project edges (Task 5). Section-level fact-hash (Task 6).
- Deferred (documented, not built this pass): FastAPI integration (static render used instead for self-containment), full Gilda/OGER grounding (dict stub), full backfill, hypothesis overlay, /submit hook — all have clear seams.

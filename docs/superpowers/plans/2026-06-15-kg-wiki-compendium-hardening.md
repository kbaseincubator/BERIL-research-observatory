# KG Wiki Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the compendium into a small Obsidian-style synthesis wiki backed by a minimal knowledge graph that exists to give the LLM good page context and enough structure to write synthesized prose, not statement dumps.

**Architecture:** The current methodology is the source of truth: statement cards provide evidence, `registry.yaml` canonicalizes topics/entities, deterministic planning builds page contexts, and the LLM writes human-readable pages. The graph is deliberately simple: statements connect to topics, entities, projects, authors, data collections, evidence anchors, and a few statement-to-statement links. The page context adds a small deterministic narrative scaffold (`lead`, `section_plan`, `navigation_targets`, `source_policy`) so the LLM has enough guidance to synthesize a coherent wiki page. No Biolink, no KGX, no generated models, and no LinkML dependency in v1.

**Tech Stack:** Python stdlib dataclasses, `pyyaml`, `jinja2`, `pytest`, `uv`, Markdown, existing `kg-*` skills.

---

## Design Rules

- Prioritize `docs/kg-wiki/methodology.md` over reviewer suggestions when they conflict.
- The KG exists to feed page generation, not to be a public ontology product.
- Keep only graph concepts that improve page membership, adjacent-topic links, source auditability, or reader navigation.
- Prioritize the rendered wiki over the graph. If a graph field does not help a reader-facing page become clearer, better connected, or more auditable, remove it.
- Treat statement cards as source material, not page copy. The writer must synthesize across cards into prose with a clear introduction, section flow, cross-links, caveats, and open directions.
- Prefer one YAML convention plus runtime validation over parallel schema/model systems.
- Avoid introducing new dependencies unless they delete more code than they add.
- Do not add glossary systems, ontology lookup, schema generation, review queues, or formal mappings in v1.

## The Minimal KG Contract

Per-project cards:

```yaml
project:
  id: adp1_deletion_phenotypes
  title: ADP1 deletion phenotypes
statements:
  - id: stmt:adp1-condition-independence-finding
    kind: finding        # finding | caveat | opportunity
    text: ADP1 carbon-source growth assays provide several independent phenotypic dimensions.
    confidence: high     # low | medium | high
    topics: [topic:adp1-carbon-fitness]
    entities: [entity:adp1, entity:quinate]
    links:
      supports: [stmt:adp1-continuum-claim]
      contradicts: []
      refines: []
    evidence:
      - source_project: adp1_deletion_phenotypes
        source_doc: REPORT.md
        source_section: Results
        quote: The low pairwise correlations (median Pearson r = 0.25, maximum r = 0.58) demonstrate that each carbon source imposes a largely independent set of gene requirements.
```

Registry:

```yaml
topics:
  adp1-carbon-fitness:
    label: ADP1 Carbon Fitness
    definition: Condition-dependent gene fitness and essentiality of ADP1 across carbon sources.
    aliases: [topic:adp1-carbon-fitness]
entities:
  adp1:
    label: Acinetobacter baylyi ADP1
    kind: organism
    definition: A naturally competent soil bacterium used as a model system for metabolism and genetics.
    aliases: [entity:adp1]
    url: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=62977
```

Page context graph:

```json
{
  "page": {"id": "topic:adp1-carbon-fitness", "type": "topic", "title": "ADP1 Carbon Fitness"},
  "statements": [],
  "projects": [],
  "topics": [],
  "entities": [],
  "authors": [],
  "data_collections": [],
  "adjacent_pages": [],
  "narrative": {
    "lead": "Explain what this page is about and why it matters.",
    "section_plan": []
  },
  "allowed_citations": []
}
```

This is enough graph for the LLM: what the page is about, what statements support it, what story the page should tell, what neighboring pages to link, what entities need plain-language definition, and which citations are allowed.

## Reader-Facing Page Contract

Every generated page should read like a short synthesis note, not an extracted-record view.

Topic pages:

```markdown
# <Topic Label>

## Overview
Introduce the topic in plain language. Explain why this cross-project theme matters and define the core organism, method, condition, or dataset when needed.

## What the Corpus Shows
Synthesize the main findings across projects. Group related statements into a reasoned argument.

## Projects and Evidence
Explain which projects contribute what, with enough detail for a reader to follow provenance.

## Connections
Link to adjacent topics, shared data pages, and author pages when those links help navigation.

## Caveats and Open Directions
Name limitations, conflicts, weak evidence, and concrete follow-up questions.

## Sources
List allowed statement citations.
```

Data pages:

- define the collection;
- explain which projects use it and why it matters;
- link to topics that depend on it;
- avoid pretending the collection is important when only one weak reference exists.

Author pages:

- summarize the author's project/topic footprint;
- link to projects/topics/data;
- avoid biographical prose not present in the deterministic context.

Home page:

- introduce the corpus and wiki purpose;
- give a compact topic map;
- expose the major cross-project connections;
- route readers into topics, data, and authors.

---

## Phase 1: Demote Aspirational Schema and Lock the Simple Contract

### Task 1: Replace LinkML Schema With a Markdown Contract

**Files:**
- Delete: `compendium/schema/synthesis_wiki.yaml`
- Create: `compendium/SCHEMA.md`
- Modify: `compendium/README.md`
- Modify: `docs/kg-wiki/methodology.md`
- Modify: `docs/kg-wiki/2026-06-15-kg-wiki-redesign.md`

- [ ] **Step 1: Create the contract document**

Create `compendium/SCHEMA.md` with the YAML examples from "The Minimal KG Contract" above and these rules:

```markdown
# Compendium Artifact Contract

This is the v1 contract for the lightweight topic-MOC wiki. It is intentionally not LinkML, Biolink, KGX, or an ontology schema. Runtime validation lives in `src/compendium/validate.py` and tests.

## Statement Cards

Required fields:
- `project.id`
- `statements[].id`
- `statements[].kind`: `finding`, `caveat`, or `opportunity`
- `statements[].text`
- `statements[].confidence`: `low`, `medium`, or `high`
- `statements[].topics`
- `statements[].entities`
- `statements[].evidence[].source_project`
- `statements[].evidence[].source_doc`
- `statements[].evidence[].quote`

Optional fields:
- `project.title`
- `statements[].links.supports`
- `statements[].links.contradicts`
- `statements[].links.refines`
- `statements[].evidence[].source_section`
- `statements[].evidence[].notebook`
- `statements[].evidence[].figure`

## Registry

Required fields:
- `topics.<key>.label`
- `topics.<key>.definition`
- `topics.<key>.aliases`
- `entities.<key>.label`
- `entities.<key>.kind`
- `entities.<key>.definition`
- `entities.<key>.aliases`

Optional fields:
- `entities.<key>.url`
- `topics.<key>.url`
```

- [ ] **Step 2: Delete LinkML schema**

Delete `compendium/schema/synthesis_wiki.yaml`.

- [ ] **Step 3: Update docs references**

Replace references to `schema/synthesis_wiki.yaml` in `compendium/README.md` and `docs/kg-wiki/*.md` with `compendium/SCHEMA.md`.

Add this sentence to `docs/kg-wiki/methodology.md` section 8:

```markdown
- Not schema-first: v1 uses a small documented YAML contract and Python validation instead of maintaining parallel LinkML/generated-model machinery.
```

- [ ] **Step 4: Verify no stale schema references**

Run:

```bash
rg -n "synthesis_wiki.yaml|LinkML|Biolink|KGX|gen-json-schema|linkml" compendium docs/kg-wiki
```

Expected: only methodology/design-history text that explicitly says these are out of scope or removed.

- [ ] **Step 5: Run tests**

Run:

```bash
uv run --directory compendium --group test pytest -q
```

Expected: tests pass or fail only where they referenced the deleted schema. Fix stale tests by pointing them at `SCHEMA.md` or deleting schema-tool tests.

- [ ] **Step 6: Commit**

```bash
git add -A compendium docs/kg-wiki
git commit -m "docs(compendium): define simple wiki KG contract"
```

---

## Phase 2: Shrink the Runtime Data Model

### Task 2: Simplify Statement Cards

**Files:**
- Modify: `compendium/src/compendium/models.py`
- Modify: `compendium/src/compendium/validate.py`
- Modify: `compendium/fixtures/statement_cards/adp1_tracer.yaml`
- Modify: `compendium/tests/test_statement_cards.py`
- Modify: `compendium/tests/test_validate.py`
- Modify: `compendium/tests/test_statement_card_fixture.py`

- [ ] **Step 1: Update tests for the simple shape**

In tests, expect statement cards to use:

```python
{
    "id": "stmt:abc123",
    "kind": "finding",
    "text": "Carbon sources define multiple ADP1 fitness dimensions.",
    "confidence": "high",
    "topics": ["topic:adp1-carbon-fitness"],
    "entities": ["entity:adp1"],
    "links": {"supports": [], "contradicts": [], "refines": []},
    "evidence": [
        {
            "source_project": "adp1_deletion_phenotypes",
            "source_doc": "REPORT.md",
            "source_section": "Results",
            "quote": "The low pairwise correlations (median Pearson r = 0.25, maximum r = 0.58) demonstrate that each carbon source imposes a largely independent set of gene requirements.",
        }
    ],
}
```

Add explicit rejection tests for:

```python
def test_statement_card_rejects_legacy_kind() -> None:
    card = _statement_card_dict()
    card["kind"] = "derived_product"
    with pytest.raises(ValueError, match="kind must be one of"):
        StatementCard.from_dict(card)


def test_statement_card_requires_evidence_quote() -> None:
    card = _statement_card_dict()
    del card["evidence"][0]["quote"]
    with pytest.raises(ValueError, match="quote"):
        StatementCard.from_dict(card)
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
uv run --directory compendium --group test pytest tests/test_statement_cards.py tests/test_validate.py tests/test_statement_card_fixture.py -q
```

Expected: failures from old `statement`, `about`, `scope`, `tier`, `qualifiers`, and singular `evidence.exact` assumptions.

- [ ] **Step 3: Replace model classes with the simple contract**

In `compendium/src/compendium/models.py`, keep only these runtime concepts for cards and page plans:

```python
STATEMENT_KINDS = ("finding", "caveat", "opportunity")
CONFIDENCE_LEVELS = ("low", "medium", "high")
LINK_KINDS = ("supports", "contradicts", "refines")
PAGE_TYPES = ("home", "topic", "data", "author", "organism")


@dataclass
class EvidenceAnchor:
    source_project: str
    source_doc: str
    quote: str
    source_section: str | None = None
    notebook: str | None = None
    figure: str | None = None


@dataclass
class StatementLinks:
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)
    refines: list[str] = field(default_factory=list)


@dataclass
class StatementCard:
    id: str
    kind: str
    text: str
    confidence: str
    topics: list[str]
    entities: list[str]
    evidence: list[EvidenceAnchor]
    links: StatementLinks = field(default_factory=StatementLinks)
```

Preserve backward compatibility only inside `StatementCard.from_dict` for one migration:

```python
text = d.get("text", d.get("statement"))
topics = d.get("topics", d.get("about", {}).get("topics", []))
entities = d.get("entities", d.get("about", {}).get("entities", []))
raw_evidence = d["evidence"]
if isinstance(raw_evidence, dict):
    raw_evidence = [raw_evidence]
```

Map old evidence `exact` to new `quote` while reading:

```python
quote = item.get("quote", item.get("exact"))
```

Do not keep `scope`, `tier`, `qualifiers`, `StatementEdge`, or edge-class constants.

- [ ] **Step 4: Update fixture to the simple shape**

Edit `compendium/fixtures/statement_cards/adp1_tracer.yaml` so each statement has:

```yaml
    text: ...
    topics:
      - topic:adp1-carbon-fitness
    entities:
      - entity:adp1
    evidence:
      - source_project: ...
        source_doc: REPORT.md
        source_section: ...
        quote: ...
```

Remove `scope`, `tier`, `about`, `qualifiers`, `extraction`, `prefix`, `suffix`, and `p_value`.

- [ ] **Step 5: Verify**

Run:

```bash
uv run --directory compendium --group test pytest tests/test_statement_cards.py tests/test_validate.py tests/test_statement_card_fixture.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add compendium/src/compendium/models.py compendium/src/compendium/validate.py compendium/fixtures/statement_cards/adp1_tracer.yaml compendium/tests/test_statement_cards.py compendium/tests/test_validate.py compendium/tests/test_statement_card_fixture.py
git commit -m "refactor(compendium): simplify statement cards"
```

---

## Phase 3: Keep Only the Graph Needed for Page Context

### Task 3: Replace Formal Statement Graph Output With Page Context Graphs and Narrative Scaffolds

**Files:**
- Modify: `compendium/src/compendium/pages/plan.py`
- Modify: `compendium/src/compendium/pages/artifact.py`
- Modify: `compendium/src/compendium/build/statement_graph.py`
- Modify: `compendium/src/compendium/cli.py`
- Modify: `compendium/src/compendium/pipeline.py`
- Modify: `compendium/tests/test_page_planner.py`
- Modify: `compendium/tests/test_page_artifact.py`
- Modify: `compendium/tests/test_cli_commands.py`
- Delete if now unused: `compendium/src/compendium/ids.py`
- Delete if now unused: `compendium/tests/test_ids.py`

- [ ] **Step 1: Add page context expectations**

Add tests asserting that `build_page_context` returns exactly the useful graph context:

```python
def test_topic_page_context_contains_simple_graph_inputs() -> None:
    plans = _plans()
    topic = plans["adp1-carbon-fitness"]
    context = build_page_context(topic, _cards(), page_plans=list(plans.values()))

    assert context["page"]["type"] == "topic"
    assert context["statements"]
    assert context["projects"]
    assert context["topics"]
    assert context["entities"]
    assert context["adjacent_pages"]
    assert context["allowed_citations"]
    assert context["narrative"]["lead"]
    assert [section["heading"] for section in context["narrative"]["section_plan"]] == [
        "Overview",
        "What the Corpus Shows",
        "Projects and Evidence",
        "Connections",
        "Caveats and Open Directions",
        "Sources",
    ]
```

- [ ] **Step 2: Run tests and note current excess fields**

Run:

```bash
uv run --directory compendium --group test pytest tests/test_page_planner.py tests/test_page_artifact.py -q
```

Expected: existing tests may pass but context includes graph/export concepts that are not needed by the writer.

- [ ] **Step 3: Make `plan_pages` the graph builder**

In `compendium/src/compendium/pages/plan.py`, compute page membership directly from cards:

- Topic pages: group by canonical topic.
- Home page: all active cards.
- Data pages: collection index entries whose projects have cards.
- Author pages: author index entries whose projects have cards.
- Adjacent links: shared projects, shared entities, shared data collections, and explicit statement links.

Do not emit generic graph nodes/edges from this path.

- [ ] **Step 4: Simplify `build_page_context`**

In `compendium/src/compendium/pages/artifact.py`, output only:

```python
{
    "page": plan.to_dict(),
    "statements": [...],
    "projects": [...],
    "topics": [...],
    "entities": [...],
    "authors": [...],
    "data_collections": [...],
    "adjacent_pages": [...],
    "allowed_citations": [...],
    "narrative": {
        "lead": "...",
        "section_plan": [...],
    },
    "instructions": {
        "audience": "scientist-engineer new to this specific niche",
        "style": "human-readable Obsidian-style synthesis page",
        "body_rule": "synthesize across statements; do not emit statement-by-statement summaries",
    },
}
```

Each statement context should include `id`, `kind`, `text`, `confidence`, `topics`, `entities`, `evidence`, and `links`.

Build `narrative` deterministically from page type:

```python
TOPIC_SECTIONS = [
    ("overview", "Overview"),
    ("what_the_corpus_shows", "What the Corpus Shows"),
    ("projects_and_evidence", "Projects and Evidence"),
    ("connections", "Connections"),
    ("caveats_and_open_directions", "Caveats and Open Directions"),
    ("sources", "Sources"),
]
```

For topic pages, the lead should include the registry topic definition when available. For data pages, the lead should identify the collection and why it connects projects. For author pages, the lead should identify the contributor by ORCID/name and summarize their project/topic footprint. For home, the lead should explain that this is a synthesis wiki for cross-project navigation.

Do not generate prose in Python. Generate only the outline, available facts, and navigation targets.

- [ ] **Step 5: Remove persistent graph export surface**

Remove `statement-graph` and graph artifact export from `compendium/src/compendium/cli.py` and `pipeline.py`.

Keep `compendium/src/compendium/build/statement_graph.py` only if `quality_synthesis` still needs it. If it is only supporting deleted CLI/export behavior, delete it and its tests.

- [ ] **Step 6: Verify**

Run:

```bash
uv run --directory compendium --group test pytest tests/test_page_planner.py tests/test_page_artifact.py tests/test_cli_commands.py -q
uv run --directory compendium --group test pytest -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add -A compendium/src/compendium compendium/tests
git commit -m "refactor(compendium): simplify wiki graph context"
```

---

## Phase 4: Simplify the Reader-Facing Wiki

### Task 4: Make the Writer Contract Enforce Synthesis

**Files:**
- Modify: `compendium/skills/kg-write/SKILL.md`
- Modify: `compendium/skills/kg-reconcile/SKILL.md`
- Modify: `compendium/src/compendium/registry.py`
- Modify: `compendium/registry.yaml`
- Modify: `compendium/tests/test_registry.py`

- [ ] **Step 1: Simplify registry metadata**

Update `compendium/registry.yaml` so recurring entities have plain definitions:

```yaml
entities:
  adp1:
    label: Acinetobacter baylyi ADP1
    kind: organism
    definition: A naturally competent soil bacterium used as a model system for metabolism and genetics.
    aliases:
      - entity:adp1
    url: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=62977
  quinate:
    label: Quinate
    kind: compound
    definition: A plant-derived aromatic compound tested as a carbon source in ADP1 fitness assays.
    aliases:
      - entity:quinate
```

Use only one optional `url` field. Do not add `external_ids`, ontology mappings, or multiple URL arrays.

- [ ] **Step 2: Ensure registry preserves metadata**

Add or update `compendium/tests/test_registry.py`:

```python
def test_registry_keeps_entity_definitions_and_urls(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        """
topics: {}
entities:
  adp1:
    label: Acinetobacter baylyi ADP1
    kind: organism
    definition: A naturally competent soil bacterium.
    aliases: [entity:adp1]
    url: https://example.org/adp1
""",
        encoding="utf-8",
    )

    registry = Registry.from_yaml(path)

    assert registry.entities["adp1"]["definition"] == "A naturally competent soil bacterium."
    assert registry.entities["adp1"]["url"] == "https://example.org/adp1"
```

- [ ] **Step 3: Update `kg-write` skill**

Add these rules to `compendium/skills/kg-write/SKILL.md`:

```markdown
## Reader Contract

- Write for a scientist-engineer who understands biology and data analysis but may not know this exact project niche.
- The page must read as synthesized prose, not a list of extracted claims.
- The first paragraph must define the page subject in plain language and state why the page exists in the wiki.
- Follow the `narrative.section_plan` from the page context unless doing so would create an empty or misleading section.
- Each body section must combine related statements into a reasoned paragraph. Do not make one bullet per statement.
- When an entity in the page context has a `definition`, use that definition naturally the first time the entity matters.
- Define specialist terms in prose when they first appear. Examples: FBA, gapfilling, quinate, condition-dependent essentiality, TnSeq.
- Link to adjacent wiki pages when they help navigation. Do not create link lists for their own sake.
- Explain connections: when linking another page, say why that page is adjacent.
- Include caveats or uncertainty when the page context contains caveats, contradictions, low confidence statements, or thin evidence.
- Keep provenance in `Sources`; do not clutter body prose with statement IDs.
```

- [ ] **Step 4: Update `kg-reconcile` skill**

Add:

```markdown
## Entity Simplicity

- Only create registry entities that recur across pages or help page writing.
- Prefer broad useful nodes over exhaustive biological ontology terms.
- Use kinds from this small set: `organism`, `compound`, `gene_or_pathway`, `method`, `dataset`, `place`, `concept`.
- Add a one-sentence plain-language `definition` for every entity.
- Add `url` only when a stable public page is obvious.
```

- [ ] **Step 5: Verify registry tests**

Run:

```bash
uv run --directory compendium --group test pytest tests/test_registry.py -q
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add compendium/registry.yaml compendium/src/compendium/registry.py compendium/tests/test_registry.py compendium/skills/kg-write/SKILL.md compendium/skills/kg-reconcile/SKILL.md
git commit -m "feat(compendium): define simple registry writing contract"
```

### Task 5: Add Lightweight Readability Checks

**Files:**
- Modify: `compendium/src/compendium/render/markdown.py`
- Modify: `compendium/src/compendium/pages/artifact.py`
- Modify: `compendium/tests/test_page_artifact.py`
- Modify: `compendium/tests/test_check.py`

- [ ] **Step 1: Add rendering expectations**

Add tests that rendered pages:

- have normal Markdown links to adjacent pages;
- have one `## Sources` section;
- have an introductory `## Overview` section for topic/data/author pages;
- have at least one non-source section with paragraph prose longer than one sentence;
- do not expose graph jargon (`curie`, `biolink`, `edge_class`, `node_id`);
- do not require entity pages for every entity.

Example:

```python
def test_rendered_topic_page_omits_graph_jargon(tmp_path: Path) -> None:
    # Build or write a small authored page artifact, then render it.
    page_text = (tmp_path / "wiki" / "topics" / "adp1-carbon-fitness.md").read_text()
    forbidden = ["curie", "biolink", "edge_class", "node_id"]
    assert not any(term in page_text.lower() for term in forbidden)
    assert "## Overview" in page_text
    assert "## Sources" in page_text
```

Add a helper in tests, not production code, for minimum prose quality:

```python
def _non_source_paragraphs(markdown: str) -> list[str]:
    before_sources = markdown.split("## Sources", 1)[0]
    return [
        block.strip()
        for block in before_sources.split("\n\n")
        if block.strip() and not block.startswith("#") and not block.startswith("- ")
    ]


def test_rendered_topic_page_has_synthesized_paragraphs(tmp_path: Path) -> None:
    page_text = (tmp_path / "wiki" / "topics" / "adp1-carbon-fitness.md").read_text()
    paragraphs = _non_source_paragraphs(page_text)
    assert any(paragraph.count(".") >= 2 for paragraph in paragraphs)
```

- [ ] **Step 2: Remove automatic entity-page generation if present**

Ensure `plan_pages` only creates:

- `home`
- `topic`
- `data`
- `author`
- optional `organism` pages for recurring model systems with at least three member statements

Do not generate generic `entities/*.md` pages.

- [ ] **Step 3: Keep external links and term definitions minimal**

When an entity has `url`, let the LLM include it in prose or a short `External links` line only if useful. Do not add a renderer-level external-link section; that creates template noise and code.

Do not add a production glossary renderer. Definitions belong in prose. The registry and page context should give the writer enough plain-language definitions to introduce terms naturally.

- [ ] **Step 4: Verify wiki output**

Run:

```bash
uv run --directory compendium --group test pytest tests/test_page_artifact.py tests/test_check.py -q
uv run compendium check --wiki compendium/wiki
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add compendium/src/compendium/render/markdown.py compendium/src/compendium/pages/artifact.py compendium/tests/test_page_artifact.py compendium/tests/test_check.py
git commit -m "refactor(compendium): keep wiki pages simple"
```

### Task 6: Add a Page Quality Smoke Test for Authored Pages

**Files:**
- Create: `compendium/tests/test_wiki_readability.py`
- Modify: `compendium/README.md`

- [ ] **Step 1: Add smoke tests for committed wiki pages**

Create `compendium/tests/test_wiki_readability.py`:

```python
from pathlib import Path


WIKI = Path(__file__).resolve().parents[1] / "wiki"
FORBIDDEN_GRAPH_TERMS = ("curie", "biolink", "edge_class", "node_id")


def _markdown_pages() -> list[Path]:
    if not WIKI.exists():
        return []
    return sorted(path for path in WIKI.rglob("*.md") if ".manifests" not in path.parts)


def test_committed_wiki_pages_have_sources() -> None:
    pages = _markdown_pages()
    assert pages
    for page in pages:
        text = page.read_text(encoding="utf-8")
        assert "## Sources" in text or page.name == "index.md"


def test_committed_wiki_pages_do_not_expose_graph_jargon() -> None:
    for page in _markdown_pages():
        text = page.read_text(encoding="utf-8").lower()
        assert not any(term in text for term in FORBIDDEN_GRAPH_TERMS), page


def test_topic_pages_have_introductions_and_connections() -> None:
    topic_pages = sorted((WIKI / "topics").glob("*.md")) if (WIKI / "topics").exists() else []
    assert topic_pages
    for page in topic_pages:
        text = page.read_text(encoding="utf-8")
        assert "## Overview" in text
        assert "## Connections" in text or "## Adjacent topics" in text
        before_sources = text.split("## Sources", 1)[0]
        assert before_sources.count("[") >= 2
```

- [ ] **Step 2: Run smoke tests**

Run:

```bash
uv run --directory compendium --group test pytest tests/test_wiki_readability.py -q
```

Expected: pass after the wiki pages have been regenerated with the revised writer contract. If existing committed pages fail before regeneration, mark the failures as the acceptance criteria for the next wiki regeneration rather than weakening the tests.

- [ ] **Step 3: Document the readability gate**

In `compendium/README.md`, add:

```markdown
`tests/test_wiki_readability.py` is a smoke test, not a prose judge. It only guards against obvious regressions: missing introductions, missing sources, missing wiki links, and leaked graph jargon.
```

- [ ] **Step 4: Commit**

```bash
git add compendium/tests/test_wiki_readability.py compendium/README.md
git commit -m "test(compendium): add wiki readability smoke tests"
```

---

## Phase 5: Prune Dead Code and Add Only Useful CI

### Task 7: Remove Non-Core Quality and Export Paths

**Files:**
- Delete if unused: `compendium/src/compendium/quality/synthesis_quality.py`
- Delete if unused: `compendium/src/compendium/quality/__init__.py`
- Delete if unused: `compendium/tests/test_synthesis_quality.py`
- Modify: `compendium/src/compendium/cli.py`
- Modify: `compendium/src/compendium/pipeline.py`
- Modify: `compendium/README.md`

- [ ] **Step 1: List CLI commands**

Run:

```bash
uv run --directory compendium compendium --help
```

Target retained commands:

```text
audit
context-pack
validate-kg
plan-pages
wiki-contexts
page-context
page-artifact
render-markdown
check
```

Remove commands that exist only for internal graph export or quality dashboards.

- [ ] **Step 2: Delete unused modules**

After removing CLI references, delete quality/export modules whose only consumer was a removed command.

- [ ] **Step 3: Verify no stale imports**

Run:

```bash
rg -n "quality_synthesis|statement-graph|export_statement_graph_artifacts|schema/synthesis_wiki.yaml|StatementEdge|EDGE_CLASS" compendium/src compendium/tests compendium/README.md
```

Expected: no matches.

- [ ] **Step 4: Run tests**

Run:

```bash
uv run --directory compendium --group test pytest -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add -A compendium
git commit -m "refactor(compendium): prune non-core graph machinery"
```

### Task 8: Add Compendium Tests to CI, Nothing More

**Files:**
- Modify: `.github/workflows/run-tests.yml`

- [ ] **Step 1: Add a compendium test job**

Add:

```yaml
  compendium_tests:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout
        uses: actions/checkout@v4

      - name: Install Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Run compendium tests
        run: |
          uv run --directory compendium --group test pytest
```

Do not add LinkML, ontology, or schema-generation CI.

- [ ] **Step 2: Run local equivalent**

Run:

```bash
uv run --directory compendium --group test pytest -q
```

Expected: pass.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/run-tests.yml
git commit -m "ci(compendium): run lightweight wiki tests"
```

---

## Phase 6: Final Documentation Pass

### Task 9: Update Methodology and README

**Files:**
- Modify: `docs/kg-wiki/methodology.md`
- Modify: `docs/kg-wiki/2026-06-15-kg-wiki-redesign.md`
- Modify: `compendium/README.md`

- [ ] **Step 1: Update methodology summary**

Make the methodology explicit:

```markdown
The KG is a context graph for page writing, not a public ontology. Its only durable nodes are statements, topics, recurring entities, projects, authors, data collections, and evidence anchors. Its only durable statement links are supports, contradicts, and refines.

The wiki is the product. Page contexts must help the writer produce introductions, synthesized sections, useful cross-links, caveats, open directions, and auditable sources.
```

- [ ] **Step 2: Update run commands**

In `compendium/README.md`, document only:

```bash
uv run --directory compendium --group test pytest
cd compendium
uv run compendium context-pack ../projects/<id> --out context-packs/<id>.json
uv run compendium validate-kg fixtures/statement_cards/adp1_tracer.yaml
uv run compendium plan-pages fixtures/statement_cards/adp1_tracer.yaml --source-root ../projects --out out/plans.json
uv run compendium wiki-contexts fixtures/statement_cards/adp1_tracer.yaml --source-root ../projects --out out/page-contexts
uv run compendium render-markdown fixtures/statement_cards/adp1_tracer.yaml --source-root ../projects --out wiki
uv run compendium check --wiki wiki
```

- [ ] **Step 3: Mark out-of-scope items**

In the redesign doc, add a short "Simplification update" note:

```markdown
This plan intentionally drops LinkML/Biolink/KGX validation from v1. The maintained contract is `compendium/SCHEMA.md` plus Python validation. The graph remains a small context graph for topic-MOC page generation.
```

- [ ] **Step 4: Verify stale text**

Run:

```bash
rg -n "LinkML|Biolink|KGX|gen-json-schema|linkml|ontology-grounded|schema/synthesis_wiki.yaml|quality-synthesis|statement-graph" compendium/README.md docs/kg-wiki
```

Expected: matches only in sections explaining what v1 deliberately does not do.

- [ ] **Step 5: Final verification**

Run:

```bash
uv run --directory compendium --group test pytest -q
uv run compendium check --wiki compendium/wiki
```

Expected: both pass.

- [ ] **Step 6: Commit**

```bash
git add compendium/README.md docs/kg-wiki/methodology.md docs/kg-wiki/2026-06-15-kg-wiki-redesign.md
git commit -m "docs(compendium): align wiki methodology with simple KG"
```

---

## What This Plan Removes From the Previous Plan

- No LinkML dependency.
- No `linkml-lint`, `gen-json-schema`, or `linkml-validate`.
- No generated models.
- No structured measurement model.
- No ontology mappings, `external_ids`, or multi-URL metadata.
- No renderer-owned glossary system.
- No generic entity pages.
- No persistent graph export as product surface.

## Final Verification

The finished system is good enough when:

- A maintainer can explain the whole data model from `compendium/SCHEMA.md` in a few minutes.
- `validate-kg` catches malformed statement cards.
- `plan-pages` creates stable home/topic/data/author page membership.
- Page contexts give the LLM enough graph context to write linked Obsidian-style pages.
- `check` catches broken wiki links and invalid citations.
- The wiki reads like synthesis prose, not a graph dump.

## Self-Review

- Spec coverage: The plan addresses the user's priority shift toward methodology, simple KG concepts, low code volume, and Obsidian-style human-readable pages.
- Placeholder scan: No task uses placeholder tokens or unspecified verification.
- Scope check: This is one simplification project, not a formal interoperability project.
- Type consistency: The plan consistently uses the simple `StatementCard`, `EvidenceAnchor`, registry, page plan, and page context concepts.

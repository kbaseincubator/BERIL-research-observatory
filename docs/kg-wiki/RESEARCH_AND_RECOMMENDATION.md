---
title: KG-Centered Wiki — Research, Comparison & Recommendation
status: research-deliverable
generated_by: deep-research workflow (14 agents, adversarially verified)
date: 2026-06-01
branch: feat/kg-wiki
---

# BERIL Research Observatory: A Deterministic, KG-Centered Scientific Aggregation Wiki — Comparison & Recommendation

## 1. Executive Summary

**Recommendation: Do not adopt Graphify, GraphRAG, or a DeepWiki clone as the system of record. Instead, evolve the repo's existing Atlas subsystem into a schema-first, LinkML/Biolink-grounded knowledge graph with deterministic data-driven page rendering.** The Atlas (`atlas/` corpus + `ui/app/atlas_*.py`) already implements ~80% of the requested architecture: a 16-type knowledge-graph node taxonomy, a pure/sorted deterministic edge-and-metrics derivation layer with zero render-time LLM calls, a strict non-mutating linter that *is* the schema spec, and a FastAPI/Jinja renderer. The single missing piece is automated, deterministic extraction from `projects/` — today every page is hand/agent-authored (`generated_by: Codex GPT-5`), so edges can drift from the corpus. The corpus is unusually amenable: 70 projects share a near-universal four-document skeleton with canonical headings, letting a deterministic parser build the entire scaffold (projects, authors/ORCID, sections, 425 PMIDs, BERDL tables, cross-project links, file inventory) and confining the irreducibly stochastic LLM step to schema-constrained prose extraction. Formalize the schema in LinkML aligned to Biolink, emit KGX, wire `atlas_lint` into CI as the determinism gate, and reuse `synthesize`/`suggest-research`/`linkml-schema` skills. Build effort: moderate; risk: contained.

---

## 2. How the Existing Atlas Works

**Mechanism.** The Atlas is a curated semantic layer over the corpus, *not* a live LLM service. It is ~141 static checked-in markdown files under `atlas/`, each carrying strict YAML frontmatter and a prose body, authored/revised offline by an LLM agent (all 141 declare `generated_by: Codex GPT-5`). At request time, `ui/app/dataloader.py::RepositoryParser.parse_atlas()` rglobs `atlas/*.md`, parses frontmatter (regex + `yaml.safe_load`), validates `REQUIRED_ATLAS_FIELDS`/`ATLAS_PAGE_TYPES` (permissively skipping malformed pages so the app still boots), rewrites repo-relative links to `/atlas/` routes, and builds an `AtlasIndex` of `AtlasPage` dataclasses with `AtlasLink` edges from each page's `related_pages`. The live app serves a frozen `data.pkl.gz` built once per main-branch commit by the `build-data-cache` GitHub Action, so derivation runs at cache-build time.

**Schema.** The de-facto schema is encoded twice — as Python constants in `ui/app/atlas_lint.py` (`ATLAS_PAGE_TYPES`, lines 46-63) and as stdlib dataclasses in `ui/app/models.py` (`AtlasPage`, lines 356-466). The node taxonomy is 16 types: `atlas, topic, data_tenant, data_collection, data_type, derived_product, join_recipe, data_gap, conflict, opportunity, claim, direction, hypothesis, person, method, meta`. `ui/app/atlas_graph.py` (lines 14-139) builds a typed, deduplicated, sorted reuse/provenance graph with edge relationships `derived_input, project_uses_collection, source_for, collection_for, related_page, produces, reused_by, affects, addresses_conflict, uses_product`. `ui/app/atlas_lint.py` (the real invariant spec, lines 32-561) enforces required fields, type/enum vocabularies, id/title uniqueness, that `source_projects` resolve to real `projects/` dirs, that `related_collections` exist in the BERDL snapshot, evidence requirements on `{claim,direction,hypothesis,derived_product,opportunity}`, per-type required fields, and resolvable internal links.

**Determinism.** The derivation/render layer is fully deterministic and reproducible: all builders sort and dedupe by stable keys; rendering reads only checked-in markdown + `berdl_collections_snapshot.json` + `collections.yaml`, no model calls. Reproducibility breaks at three upstream points: (a) page bodies/edges are LLM-authored, so re-running the agent is **not** reproducible; (b) project dates come from `git log` with mtime fallback, and research-area clustering uses corpus-sensitive agglomerative text-cosine clustering; (c) collection coverage depends on a regenerated live-Spark snapshot.

**What it surfaces.** "What science was done" → `topic`/`claim`/`derived_product` pages with explicit `source_projects` + `evidence[].support` (e.g. `claims/metal-specific-genes-core-enriched.md`). "Next steps" → `opportunity`/`direction`/`hypothesis`/`conflict` pages with categorical `impact/feasibility/readiness/evidence_strength` scores, `target_outputs`, `resolving_work`, deterministically sorted by status→impact→readiness→feasibility (no fabricated numeric scores).

**Strengths.** Already the requested shape (authored knowledge layer + deterministic derivation layer); ready-made KG node/edge schema; lint as executable invariant spec; coverage/health metrics (`atlas_inventory.py`); categorical non-fabricated prioritization; cross-surfacing into project/collection pages.

**Weaknesses.** Page bodies, evidence prose, and most edges are LLM-authored, so the corpus is not deterministically distilled from `projects/` and can drift; lint explicitly does not guarantee scientific correctness. The "graph" is recomputed in memory each render, never persisted as a queryable graph (no Cypher/SPARQL, no URIs/ontology grounding). No pydantic; schema duplicated across `atlas_lint.py` + `models.py` (drift risk). Lint/inventory are **not** wired into CI or `beril_cli` — nothing prevents committing a corpus that fails lint. Visualization is text panels/cards, not a rendered graph.

---

## 3. How Graphify Was Used Here

**Mechanism.** Graphify (upstream `safishamsi/graphify`, PyPI `graphifyy` v0.6.0) is a Claude-Code skill that turns a folder into a knowledge graph plus three outputs: interactive `graph.html`, a GraphRAG-ready `graph.json`, and a plain-language `GRAPH_REPORT.md`, with an optional markdown wiki. In a **sibling** worktree (`BERIL-research-observatory/context-kg-wiki/`), it was run once over `knowledge/staging/projects/` (the project REPORT/PLAN/REVIEW markdown — *not* code), producing a 150-node, 178-edge graph in 12 Leiden communities plus a 23-article wiki. Pipeline: `detect` → hybrid `extract` (deterministic tree-sitter AST for code — none here; parallel LLM subagents for the prose) → `build` (NetworkX) → `cluster` (Leiden, stable IDs) → `analyze` (god nodes, surprises) → `report`/`export` → LLM community labels → `to_html`/`to_wiki`.

**KG schema it built.** `graph.json` is a NetworkX node-link export. Node attrs: `id` (`{stem}_{entity}`), `label`, `file_type` (uniformly `document` here), `source_file`, `community`, `author`. Edge attrs: `relation`, `confidence` (`EXTRACTED|INFERRED`), `confidence_score`, `weight`, `source_location`. Observed relations: `cites, references, implements, conceptually_related_to, shares_data_with, semantically_similar_to, rationale_for`. Community labels are free-text (e.g. "ADP1 Respiratory Chain", "Truly Dark Genes"). This is a **loose, emergent, free-text schema** — not a typed scientific vocabulary.

**Output format.** Per-community and per-god-node markdown articles with Obsidian `[[wikilinks]]`, "Key Concepts" with connection counts, "Source Files", and an "Audit Trail" (EXTRACTED/INFERRED/AMBIGUOUS percentages).

**Determinism.** Hybrid and partial. Graph *assembly* (Leiden clustering with stable IDs, god-node/surprise analysis, report/HTML/wiki rendering) is deterministic given a fixed extraction JSON. But the *substance* for prose inputs — every node, edge, relation type, confidence, and the 12 community labels — is produced by stochastic LLM subagents, so a re-run would not reproduce the same 150 nodes/178 edges/labels. Only the (absent) code-AST path is genuinely deterministic; `projects/` is prose. (`cost.json` reports 0 tokens for the run — anomalous, likely subagent tokens not tallied back, making cost/provenance opaque.)

**Why it falls short for this goal.** (1) **Non-reproducible content** for prose inputs directly conflicts with the determinism requirement. (2) **Mechanically shallow wiki** — community/node summaries with connection counts and source lists, *no narrative scientific argument, no typed evidence, no review state, no conflict/hypothesis epistemics* — strictly weaker than the Atlas's hand-curated reasoning units. (3) **No controlled vocabulary / ontology grounding** — free-text relations like `semantically_similar_to` are not scientific predicates. (4) **No provenance to immutable snapshots** (no approval hash / archive_key). (5) The run covered only 26/70 projects — a partial snapshot. **Verification note:** the upstream tool's primary deliverable is the graph + report, *not* a navigable prose wiki; `--wiki` is an optional, secondary output, and the "OpenDeepWiki exports graphify-out/graph.json" claim from research is a refuted conflation of two same-named tools.

**Reusable ideas vs. Atlas:** Graphify's deterministic graph *backbone* (NetworkX), Leiden communities for topic clustering, and the `EXTRACTED/INFERRED/AMBIGUOUS` audit-tagging discipline are worth borrowing. Everything epistemic (typed claims, conflicts, hypotheses, provenance, review) is better served by the Atlas pattern.

---

## 4. Comparison Matrix

Scale: ●●● strong · ●● partial · ● weak. Footnotes follow.

| Dimension | Atlas (existing) | Graphify | Custom schema-first KG+wiki *(recommended)* | GraphRAG-based | DeepWiki-style |
|---|---|---|---|---|---|
| Determinism / reproducibility | ●●● ⁽¹⁾ | ●● ⁽²⁾ | ●●● ⁽³⁾ | ● ⁽⁴⁾ | ● ⁽⁵⁾ |
| KG-centricity | ●● ⁽⁶⁾ | ●●● ⁽⁷⁾ | ●●● ⁽⁸⁾ | ●●● | ●● ⁽⁹⁾ |
| Scientific-aggregation fit | ●●● ⁽¹⁰⁾ | ● ⁽¹¹⁾ | ●●● ⁽¹²⁾ | ●● ⁽¹³⁾ | ● ⁽¹⁴⁾ |
| Next-steps / hypothesis support | ●●● ⁽¹⁵⁾ | ● ⁽¹⁶⁾ | ●●● ⁽¹⁷⁾ | ●● ⁽¹⁸⁾ | ● |
| Provenance / citations | ●●● ⁽¹⁹⁾ | ●● ⁽²⁰⁾ | ●●● ⁽²¹⁾ | ● ⁽²²⁾ | ●● ⁽²³⁾ |
| Human-readability | ●●● ⁽²⁴⁾ | ●● ⁽²⁵⁾ | ●●● | ●● ⁽²⁶⁾ | ●●● ⁽²⁷⁾ |
| Cross-project synthesis | ●● ⁽²⁸⁾ | ●● ⁽²⁹⁾ | ●●● ⁽³⁰⁾ | ●●● ⁽³¹⁾ | ● ⁽³²⁾ |
| Build effort (●●● = low) | ●●● ⁽³³⁾ | ●●● ⁽³⁴⁾ | ●● ⁽³⁵⁾ | ● ⁽³⁶⁾ | ●● ⁽³⁷⁾ |
| Maintainability | ●● ⁽³⁸⁾ | ● ⁽³⁹⁾ | ●●● ⁽⁴⁰⁾ | ● ⁽⁴¹⁾ | ●● |
| Hosting / cost (●●● = cheap) | ●●● ⁽⁴²⁾ | ●●● ⁽⁴³⁾ | ●●● ⁽⁴⁴⁾ | ● ⁽⁴⁵⁾ | ●● ⁽⁴⁶⁾ |

**Footnotes.** ⁽¹⁾ Render/derivation fully deterministic & sorted; only upstream agent authoring non-reproducible. ⁽²⁾ Graph assembly/Leiden deterministic; node/edge content LLM-extracted, non-reproducible. ⁽³⁾ Deterministic scaffold + cached, schema-constrained LLM extraction committed as a versioned artifact; render is a pure function. ⁽⁴⁾ LLM extraction + per-community LLM reports; temp=0 insufficient (batch-invariance/FP non-associativity); not bit-reproducible. ⁽⁵⁾ Cached snapshot only; documented inaccuracies (LibreOffice/Buck); no reproducibility guarantee. ⁽⁶⁾ Typed graph but recomputed in memory, no persisted queryable graph/URIs. ⁽⁷⁾ Persistent NetworkX graph + exports (Neo4j/GraphML/MCP). ⁽⁸⁾ Persisted KGX nodes/edges TSV, ontology CURIEs. ⁽⁹⁾ OpenDeepWiki builds mind-maps; clones are code-tree-centric. ⁽¹⁰⁾ Claims/conflicts/hypotheses/evidence as first-class epistemics. ⁽¹¹⁾ Community summaries, no typed evidence/argument. ⁽¹²⁾ Biolink covers organism/gene/pathway/phenotype/environment + InformationContentEntity for findings. ⁽¹³⁾ Community reports are prose but flat, no scientific epistemics. ⁽¹⁴⁾ Assumes "code is single ground truth"; no contradiction/confidence handling. ⁽¹⁵⁾ Opportunity/direction/hypothesis/conflict with scored prioritization. ⁽¹⁶⁾ "Suggested questions" only, ungrounded. ⁽¹⁷⁾ ABC/metapath link prediction over committed graph + existing `suggest-research`. ⁽¹⁸⁾ Global Q&A surfaces themes, not ranked experiments. ⁽¹⁹⁾ source_projects/source_docs resolve to real dirs; evidence[].support. ⁽²⁰⁾ EXTRACTED/INFERRED tags + source_file, but no immutable anchor. ⁽²¹⁾ PROV-O/PAV fields + approval hash/archive_key + PMID/DOI. ⁽²²⁾ Answers synthesized through summary layers lose source-span linkage (community-documented GraphRAG limitation). ⁽²³⁾ file:line citations, but to mutable code. ⁽²⁴⁾ Progressive-disclosure prose + maps. ⁽²⁵⁾ Mechanical, connection-count prose. ⁽²⁶⁾ Reports readable but not a cross-linked site without custom work. ⁽²⁷⁾ Purpose-built navigable wiki + Mermaid. ⁽²⁸⁾ Cross-links hand-authored, can drift. ⁽²⁹⁾ Leiden surfaces cross-community edges. ⁽³⁰⁾ Deterministic cross-project edges from BERDL tables + `projects/<name>` links + shared join keys. ⁽³¹⁾ Hierarchical Leiden global summaries are the design strength. ⁽³²⁾ One-repo assumption; no cross-document entity resolution. ⁽³³⁾ Already built. ⁽³⁴⁾ One-command run. ⁽³⁵⁾ Reuses Atlas infra; new work = extractor + LinkML + render. ⁽³⁶⁾ Index pipeline + custom wiki rendering + determinism engineering. ⁽³⁷⁾ Clone/skill setup + science adaptation. ⁽³⁸⁾ Manual maintenance, schema duplicated. ⁽³⁹⁾ Re-run = different graph; opaque cost. ⁽⁴⁰⁾ Single LinkML source of truth + CI lint gate. ⁽⁴¹⁾ Re-index churn, schema rebuilds. ⁽⁴²⁾ Static files + frozen pickle, GitHub Action. ⁽⁴³⁾ Local, no server. ⁽⁴⁴⁾ Static/committed files + existing FastAPI. ⁽⁴⁵⁾ High "LLM tax" (~75% tokens pre-query). ⁽⁴⁶⁾ Hosted (paid) or self-host index.

---

## 5. External Methods Survey (corrected by verification notes)

**GraphRAG family (Microsoft GraphRAG, nano-graphrag, LightRAG, HippoRAG/2, RAPTOR, Zep/Graphiti).**
- *GraphRAG* — Pros: the only one that natively emits wiki-like prose (per-community "community reports": LLM title + summary + full report + ranked findings) over an entity/relationship KG with a hierarchical Leiden topic tree; parquet artifacts (`entities/relationships/communities/community_reports`) + GraphML export. Cons: LLM extraction is non-reproducible (temp=0 insufficient; *verification clarifies the root cause is batch-invariance failure, with FP non-associativity as the enabling mechanism, not co-equal causes*); high indexing cost (~75% of tokens pre-query; LazyGraphRAG cuts indexing to ~0.1% and global query >700x but then *removes* the wiki-like reports); weak claim-to-span provenance through summary layers (*correction: this is documented in a community discussion, not an official Microsoft concession*). *Verification scopes the "only one with wiki-like output" claim: GraphRAG's reports are flat per-community summaries, not a cross-linked site — rendering a real wiki is custom work regardless.*
- *nano-graphrag* — ~1100 LOC, same community-report mechanism, far easier to fork/instrument for determinism; ideal base if a GraphRAG path were chosen.
- *RAPTOR* — most algorithmically deterministic (UMAP+GMM clustering), but a *summary tree*, not an entity KG — weak KG substrate. *Correction: UMAP is only reproducible with fixed random_state AND single-threaded (`n_jobs=1`); multithreaded UMAP is not bit-reproducible even seeded.*
- *LightRAG / HippoRAG/2* — excellent retrieval engines (dual-level retrieval; Personalized PageRank), but output *rankings*, not human-readable topic pages — not wiki generators.
- *Zep/Graphiti* — bi-temporal agent-memory KG (Apache-2.0), valuable *only* if the wiki must track how findings evolve/conflict over time; not a corpus-distillation tool.

**DeepWiki / code-wiki generators (DeepWiki, deepwiki-open, OpenDeepWiki, MS deep-wiki skill).**
- Pros: the convergent, transferable pattern — **structure-first** (emit an explicit machine-parseable page tree *before* prose), per-page importance ranking, materialized cross-links, hard citation discipline, Mermaid diagrams, cache + incremental diff-scoped regeneration, MCP/llms.txt export. OpenDeepWiki's *separable catalogue-model vs content-model* is the key determinism lever (pin the page list, LLM only writes bodies).
- Cons: non-deterministic regeneration (cached snapshot only); documented accuracy failures (DeepWiki falsely claimed LibreOffice uses Buck); no entity resolution, contradiction/confidence handling, immutable provenance, or human-verification layer — all of which a scientific wiki needs. The breaking assumptions: "code is the single ground truth" and "file tree is the structural prior" (absent here — *the KG is the page tree*). *Corrections: Mutable.ai is defunct; OpenDeepWiki is now .NET 10 + Microsoft.Agents.AI (not .NET 9 + Semantic Kernel); the "built on DeepResearch agent" attribution is unconfirmed.*

**LLM-KG construction tooling (LangChain LLMGraphTransformer, Neo4j LLM Graph Builder, OntoGPT/SPIRES, constrained decoding, discriminative models).**
- *LangChain LLMGraphTransformer* — `allowed_nodes`/`allowed_relationships` (tuple form = full head→REL→tail typing) + `strict_mode`; *type-level constraint that bounds the relation vocabulary but does not make edges true* (verification confirms the report correctly avoids overstating this).
- *Neo4j LLM Graph Builder* — production-ready Document→Chunk lexical graph + entity graph, EXTRACTED/FREE/Provided schema modes, entity resolver.
- *OntoGPT/SPIRES* — **best fit for ontology-grounded scientific extraction**: LinkML schema drives recursive extraction, entities grounded to real ontology IDs via Gilda/OGER (98% correct GO IDs *with* grounding vs 3% without — *cite as the authors' reported task-specific result, not a general fact*). Does **not** claim run-to-run determinism; reproducibility comes from the deterministic grounders + schema, and overall RE F≈41 means outputs must be validated.
- *Enforcement* — constrained decoding (Outlines/XGrammar) guarantees on-schema output but **local models only** and can *degrade* reasoning on hard cases (EMNLP 2024); post-hoc validate-and-retry (instructor/BAML) works on any API. For typed edges, closed *enum* constraints are the high-value, low-risk use.
- *Discriminative models* (GLiNER/GLiREL/ReLiK, self-hosted Triplex) — argmax over a fixed label set is far more reproducible than hosted generation; use as the typed-edge classifier with the LLM proposing candidates.
- **Hard limit (verified):** temperature=0 does *not* make hosted LLMs deterministic — true determinism needs batch-invariant kernels on self-hosted inference (demonstrated 1000/1000 identical on vLLM, single-node only). *Precision matters: BF16 ~9% variance, FP32 near-deterministic. The "120B identical only ~12.5%" and "larger=more variable" findings are from Atil et al. (arXiv:2506.09501), distinct from the precision paper — verification flags the report conflated these citations.*

**Scientific KG standards (Biolink / LinkML / KGX, OBO/Pfam/COG/KEGG).**
- *Biolink Model* (LinkML-authored, v4.x; adopted by NCATS Translator & Monarch) covers nearly every corpus entity: `Gene, Genome, OrganismTaxon, Bacterium, Pathway, BiologicalProcess, MolecularActivity, ChemicalEntity, PhenotypicFeature, EnvironmentalFeature/Exposure` + an `InformationContentEntity` hierarchy (`Publication/Study/Dataset`) for findings/datasets. Required edge slots `knowledge_level`, `agent_type` (`manual_agent` vs `automated_agent` — critical for marking analysis-derived vs LLM-asserted edges), `has_evidence`, `publications`, `has_confidence_score`, `p_value` make a citable, deterministic wiki feasible. *Gap: lacks first-class `GeneFitness`/`Cofitness`/`Finding`/`Hypothesis` classes — add as project subclasses.*
- *KGX* — Biolink-conformant `nodes.tsv`/`edges.tsv` with CURIE ids + provenance columns + `kgx validate`; the wiki renders as a pure function over committed TSVs.
- *Vocabularies* — GO/ENVO/CHEBI/NCBITaxon/Pfam/InterPro/COG are CC0 or US-gov public domain. **KEGG/KO is the licensing exception** — reference KO ids but do not redistribute KEGG-derived descriptive content; prefer GO/Reactome.
- *Next-experiment mechanisms* — Swanson ABC literature-based discovery (open triples = candidate experiments), Hetionet/Rephetio metapath+DWPC link prediction, INDRA belief-scored/contradiction-resolved edges, and 2025-era LLM+KG agents (SciAgents, Robin, KG-CoI). *Caveat: no published microbiology-specific LLM+KG-traversal hypothesis system exists — this is novel integration work; keep the LLM suggestion layer as a non-deterministic versioned overlay.*

**Doc substrates & graph viz.** MkDocs + Material + `mkdocs-gen-files` + `literate-nav` is the best static, diffable, Python-native substrate (one virtual page per KG entity); Quarto only if pages execute code. Cytoscape.js is the best balanced graph viz, **deterministic when node coordinates are pinned** (bake layout offline into static `graph.json`); Sigma+graphology for >10k nodes; Mermaid is client-side so pin the version. Graph databases add a stateful server that breaks "reproducible from files."

---

## 6. What a "Deterministic KG-Centered Wiki" Really Requires

**Three determinism levels (distinct, achievable to different degrees):**

1. **Deterministic extraction** — same input bytes → same nodes/edges every run. Achievable *only* for the structural scaffold via rule-based parsing (project enumeration, headings, authors/ORCID, PMIDs/DOIs, BERDL-table mentions, cross-project links, file inventory, markdown tables). **Not** achievable for prose-bound semantics via any hosted LLM (verified: batch-invariance + FP non-associativity defeat temperature=0). For genuine extraction determinism you need a self-hosted batch-invariant model or a discriminative argmax extractor over a fixed label set.

2. **Reproducible pipeline** — the *artifact* is reproducible even if the extraction step is not, because the LLM step is run **offline, cached (keyed on input-content-hash + model id + prompt hash + schema hash), and committed to version control as a frozen graph**. Re-runs replay the cache, not the model. This is the pragmatically correct target.

3. **Template-driven prose** — pages are rendered by pure deterministic templates over the committed graph, with **no LLM call at render time**. Same graph + same template → byte-identical pages. The Atlas already achieves this.

**Residual non-determinism of any LLM step** is irreducible without self-hosting; therefore the LLM must never sit on the render path and must be treated as a draft-producing, cached, human-gated stage.

**Safeguards (all required):**
- **Provenance** — every published edge carries PROV-O/PAV-style fields: source span (REPORT.md heading + `(Notebook: NN.ipynb)` tag), dataset/notebook id, extractor+model+version+timestamp, plus the existing `beril.yaml` approval `report_hash`/`archive_key`. Quarantine claims lacking provenance.
- **Schema constraints** — a single LinkML source of truth (closed enums, typed head→REL→tail), validated by `linkml-validate` + `kgx validate` + the existing `atlas_lint`.
- **Drift detection** — on each re-extraction, compute a **graph diff** of canonicalized triples (new/changed/removed edges, entity-resolution merges, schema violations); only the diff goes to review. Track temporal validity so stale facts are flagged, not silently overwritten.
- **Human review gate** — extraction produces *candidates*, not published pages; a curator (ORCID-stamped) approves changes before they go live, mirroring the existing `/submit` Phase 2c approval pattern. (DeepWiki's documented inaccuracies and SPIRES's "validate before entering KBs" both make this non-negotiable.)

---

## 7. Recommended Architectures

### ★ Option A (RECOMMENDED): Schema-First Atlas-Native KG — extend the existing subsystem

**Why lead with this.** The repo already contains the deterministic distillation infrastructure (parse→graph→lint→inventory→render, all pure/sorted, no render-time LLM). The *only* missing piece is automated deterministic extraction. Building on the Atlas reuses every existing component, keeps one deployment, and produces the most deterministic, most provenance-rich, most scientifically-shaped result for the least net new code. It directly attacks the Atlas's one real weakness (hand-authored edges that drift from `projects/`) by computing edges from the corpus.

**Proposed typed KG schema (LinkML, aligned to Biolink; emits KGX).**
- *Entities (Biolink class → corpus source):* `Organism` → `biolink:OrganismTaxon`/`Bacterium` (id `NCBITaxon:` or `gtdb_species_clade_id`); `Gene`/`GeneCluster` → `biolink:Gene` (xref Pfam/COG); `OrthologGroup`/`KO` → `biolink:OntologyClass` (reference KEGG ids, no redistribution); `Pathway` → `biolink:Pathway` (prefer GO/Reactome); `Function` → `biolink:BiologicalProcess`/`MolecularActivity` (GO:); `Metabolite` → `biolink:ChemicalEntity` (CHEBI:); `Phenotype` (AMR, fitness, metal tolerance) → `biolink:PhenotypicFeature`; `Condition`/`Environment` (metal, media, compartment) → `biolink:EnvironmentalFeature`/`Exposure` (ENVO:); `Dataset`/`Notebook` → `biolink:Dataset`; `Project` → `biolink:Study`; `Publication` → `biolink:Publication` (PMID/doi); and the Atlas epistemic types `Finding, Hypothesis, Claim, Conflict, Opportunity, Direction` as project subclasses of `biolink:InformationContentEntity` (these already exist as `atlas/` files).
- *Relations (Biolink predicates; every edge carries `knowledge_level`, `agent_type`, `has_evidence`, `provided_by`, `has_confidence_score`, `p_value`):* `Gene -in_taxon-> Organism`; `Gene -orthologous_to/genetically_interacts_with-> Gene` (cofitness); `Gene -enables/participates_in-> Pathway`; `Gene/Organism -has_phenotype-> Phenotype`; `Phenotype -associated_with-> EnvironmentalFeature`; `Hypothesis -supported_by/refuted_by-> Finding`; `Conflict -contradicts-> Finding↔Finding`; `Finding -has_evidence-> Dataset/Study`. This is a typed superset of the Atlas's current edge relationships, grounded in Biolink so it inherits validation and KGX export.

**Extraction approach (hybrid, two-stage).**
- *Stage 1 — deterministic (rule-based, byte-stable, the bulk of the scaffold):* walk `projects/`; read `beril.yaml` (9/70) or fall back to README convention (title=H1, `## Status`, `## Authors` bullets + ORCID, `## Research Question`); segment REPORT.md/RESEARCH_PLAN.md by canonical H2/H3 with a heading-synonym map; regex-harvest 425 PMIDs/DOIs, backtick BERDL tables (`kbase_ke_pangenome` 79×, `kescience_fitnessbrowser` 26×), `projects/<name>` cross-links; parse embedded markdown tables (Hypothesis|Prediction|Result verdicts, Data Sources); inventory 377 notebooks/figures/data as provenance nodes; link findings→notebooks via inline `(Notebook: NN.ipynb)`. Cross-project edges come deterministically from shared `gtdb_species_clade_id`/`genome_id` join keys and explicit `projects/<name>` references (hubs: `fitness_modules`, `conservation_vs_fitness`, `essential_genome`, `metal_fitness_atlas`).
- *Stage 2 — schema-constrained LLM (enrichment only):* within each segmented section, extract prose-bound entities/relations using **OntoGPT/SPIRES** driven by the LinkML schema with Gilda/OGER ontology grounding (KEGG/COG/Pfam/GO), temperature 0, closed relation enums, source-span provenance per triple. **Cache keyed on file-content-hash + model + prompt + schema** so unchanged projects never re-extract; commit the extracted graph as a frozen KGX artifact. Special-case the structural outlier `gene_function_ecological_agora` (11 adversarial-review files, ~50 diagnostics JSON).

**Page generation.** Data-driven templates over the committed KGX graph — exactly the Atlas pattern. Reuse `atlas_graph.py` builders for edges/contexts and add deterministic per-entity pages (one per KG node). No LLM at render time.

**Rendering substrate.**
- *App-integrated (recommended primary):* extend the existing FastAPI/Jinja `ui/` with a Cytoscape.js graph view backed by a JSON endpoint serializing `build_atlas_reuse_edges()`, plus a static `graph.json` snapshot per data-cache commit (recovers diffability). Zero new build system; reuses auth, provenance, webhook refresh, and all per-entity pages. Pin Cytoscape/Mermaid versions; precompute layout coordinates.
- *Static option:* MkDocs + Material + `mkdocs-gen-files` + `literate-nav`, generating one virtual markdown page per KG entity from the same builders, deployable to GitHub Pages — fully diffable/reproducible from git, at the cost of a second pipeline and loss of live auth/chat.

**Skill reuse.** `linkml-schema` → formalize the Atlas frontmatter as the single LinkML source of truth (enums→`permissible_values`, `AtlasReuseEdge`→association class), ending the `atlas_lint`/`models.py` duplication. `synthesize` → its fixed REPORT.md section contract (Key Findings, Discoveries, Data Sources) is the structured extraction input. `suggest-research` → populate `Opportunity`/`Direction`/`Hypothesis` nodes; layer ABC-open-triple + metapath/DWPC computation over the committed graph for ranked next experiments. **Seam:** attach extraction + Atlas-page emission right after `/submit` Phase 2c (approval-gated, mirroring the existing memories extraction), with `atlas_lint` wired into CI as the determinism/validity gate.

**Effort: moderate (~4–7 engineer-weeks).** Stage-1 parser + LinkML schema + KGX emitter (~2–3 wk), SPIRES enrichment + caching + diff/review gate (~1–2 wk), Cytoscape view + CI lint wiring (~1–2 wk).

**Pros.** Most deterministic and reproducible; strongest provenance (approval hashes + ontology CURIEs + PMIDs); best scientific epistemics (claims/conflicts/hypotheses already first-class); reuses ~80% existing infra; single deployment; cheapest hosting (static files + frozen pickle). **Cons.** Requires bespoke microbial-genomics schema subclassing (no off-the-shelf class for GeneFitness/Finding); SPIRES RE accuracy is mid-range so the human gate is load-bearing; cross-project entity resolution (normalizing gene/organism mentions) is real work.

### Option B: Atlas backbone + Graphify-style graph layer (hybrid)

Keep the Atlas as system of record, but borrow Graphify's NetworkX backbone + Leiden community detection to *auto-cluster* the deterministic KG into topic communities, and adopt its `EXTRACTED/INFERRED/AMBIGUOUS` audit tagging on edges. Render community overviews alongside Atlas topic pages. **Pros:** richer auto-topic structure, cheap clustering, honest audit trail. **Cons:** Leiden community *labels* require an LLM (non-deterministic — cache them); adds a second graph representation to maintain; lower marginal value than Option A since the Atlas already has hand-curated topics. **Effort: low-moderate (~2–3 wk)** on top of Option A. Best as a *follow-on* to Option A, not a standalone.

### Option C: GraphRAG/nano-graphrag exploratory overlay (non-authoritative)

Run nano-graphrag (forkable, ~1100 LOC, instrumentable for determinism) over the corpus purely as an **exploratory search + Q&A layer**, never as the published source of truth. The LinkML-validated Atlas KG remains canonical for any citable claim. **Pros:** strong open-ended global Q&A, community reports for serendipitous discovery, freezes the extracted graph as a versioned artifact. **Cons:** high LLM tax; non-reproducible content; weak claim-to-span provenance; duplicate infrastructure. **Effort: moderate (~3–4 wk).** Only justified if ad-hoc cross-corpus Q&A becomes a primary user need — not the case at 70 slowly-growing projects.

---

## 8. Risks & Pitfalls (and mitigations)

| Risk | Mitigation |
|---|---|
| **Hosted-LLM non-determinism** (temp=0 insufficient; batch-invariance/FP/BF16 variance) | Never call LLM at render time; run extraction offline, cache by content+model+prompt+schema hash, commit frozen graph; prefer SPIRES grounding + discriminative classifiers; self-host only if byte-determinism is mandated. |
| **Hallucinated/spurious edges** (LLM invents relations from co-occurrence) | Schema enum constraints bound *type* not *truth* → require source-span provenance per triple, human review gate, drop off-enum edges. |
| **Duplicate entities** (gene "LLM"/"LLMs", organism synonyms) | Deterministic entity resolution to ontology CURIEs (Gilda/OGER) + canonical node + `same_as`-to-source edges; review merges in the diff. |
| **Schema duplication/drift** (`atlas_lint.py` vs `models.py`) | Single LinkML source of truth; generate validators/dataclasses from it. |
| **Lint not enforced** (can commit a corpus that fails lint) | Wire `atlas_lint` + `kgx validate` + `linkml-validate` into CI; block merge on failure (exit-code contract already exists). |
| **KEGG redistribution** | Reference KO ids only; redistribute GO/Reactome/Pfam/COG content (CC0/public domain). |
| **Generated-wiki accuracy** (DeepWiki/Buck precedent) | Human-verification layer with ORCID approval; mark superseded/conflicting findings via `conflict` nodes. |
| **Notebook irreducibility** (only ~4% reproduce same results) | Pin environments; provenance points to committed REPORT.md findings + notebook *hashes*, not live re-execution. |
| **Corpus outlier** (`gene_function_ecological_agora`) skews per-project assumptions | Special-case handling; heading-synonym map; tolerate missing/relocated source projects. |
| **Graph viz / DB statefulness breaks diffability** | Bake fixed Cytoscape coordinates into static `graph.json`; pin Mermaid; avoid a graph DB. |
| **LLM suggestion layer pollutes canonical graph** | Isolate next-experiment text as a separately-versioned, regenerable overlay, never part of the committed KGX core. |

---

## 9. Open Questions for the User

1. **Determinism bar:** Is *reproducible-artifact* determinism (offline cached LLM + committed frozen graph + template rendering) sufficient, or do you require *byte-identical extraction on re-run* — which forces self-hosted batch-invariant inference and a discriminative-model extractor (much higher effort)?
2. **Substrate:** App-integrated (extend the existing FastAPI `ui/`, keep auth/chat/one deployment) vs. static MkDocs site (maximally diffable/reproducible, GitHub Pages, but read-only and a second pipeline)?
3. **Ontology grounding depth:** Full Biolink/KGX with CURIE grounding (interoperable, citable, more setup) vs. the lighter existing Atlas frontmatter formalized in LinkML without external ontology resolution? KEGG redistribution constraints — acceptable to use GO/Reactome substitutes for redistributable pathway content?
4. **Extraction seam:** Attach KG extraction at `/submit` Phase 2c (post-approval, per-project incremental) vs. a separate batch job over the whole corpus? Per-project incremental is cheaper and matches the existing approval-gated pattern.
5. **Human review capacity:** Who is the curator, and what review throughput is realistic? The human gate is load-bearing (SPIRES F≈41; DeepWiki precedent) — this caps how much LLM-extracted content can be published per cycle.
6. **Next-experiment ambition:** Is a deterministic structural mechanism (ABC open-triples + metapath/DWPC link prediction over the committed graph) enough, or do you want an LLM+KG hypothesis-agent overlay (SciAgents/KG-CoI-style) — which is research-grade, non-deterministic, and novel integration work for microbial genomics?
7. **Graphify's role:** Retire it for this goal, or retain it as a throwaway exploratory visualizer in the sibling worktree? (It is not on the recommended critical path.)
8. **Temporal tracking:** Do you need to track how findings *evolve and conflict across project iterations over time* (bi-temporal, Graphiti-style)? If yes, this changes the schema (valid-time/transaction-time edge slots) and argues for Conflict-node supersession semantics from the start.
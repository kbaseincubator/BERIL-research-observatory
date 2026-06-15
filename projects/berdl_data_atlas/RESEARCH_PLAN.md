# Research Plan: BERDL Data Atlas — Inventory, Topic Map, and Cross-Reference Synergies

## Research Question

What data is currently available in the KBase BERDL Lakehouse, what biological
and environmental topics does each dataset cover, and where do datasets
*amplify each other* when combined? Produce a depiction that simultaneously
serves:

1. **KBase users** — choosing what to analyze, deciding which databases to
   combine, sizing query plans.
2. **Funders and PIs** — evaluating cross-agency / cross-program synergies and
   identifying coverage gaps worth filling.

This is a **knowledge-synthesis project**, not a hypothesis-test in the
biological sense. It still has falsifiable claims about the *structure of the
data inventory* (see Hypothesis below), but the deliverable is an atlas, not a
p-value.

## Hypothesis

Framed as falsifiable claims about the data landscape:

- **H0 (null)**: BERDL is a collection of independent databases with no
  meaningful join keys across tenants. The "data lakehouse" framing is
  organizational, not analytical.
- **H1 (alternative)**: BERDL contains a dense, partially-realized network of
  cross-tenant linkages anchored by a small set of shared identifiers
  (GTDB taxonomy, genome accessions, KEGG/COG/PFAM/ModelSEED IDs, geolocation,
  ASV/biosample IDs). The ~70 existing BERIL projects have already exercised
  many of these linkages; many more remain unexercised.

H1 is what we expect to confirm. The interesting science is in
*quantifying* the network — coverage rates, ID-collision pitfalls, realized
versus theoretical edges — not in whether linkages exist at all.

## Literature Context

This project synthesizes internal documentation rather than published
literature. The internal corpus is the substrate:

- `docs/overview.md` — the canonical pangenome briefing (Dehal), data
  generation workflow for the GTDB-derived pangenome.
- `docs/pitfalls.md` — 30+ per-database H2 sections enumerating known
  gotchas; the most authoritative source for join-key failure modes.
- `docs/discoveries.md` — running insights, many of which are
  cross-database findings.
- `docs/research_ideas.md` — backlog of cross-database project ideas,
  many already executed or in flight.
- ~70 project READMEs and RESEARCH_PLAN.md files — empirical record of
  which cross-references have been *successfully exercised*.
- `data/berdl_inventory.md` — per-database catalog generated this session.

External literature anchors will be cited only where they ground a
cross-reference claim (e.g., MetaCyc/ModelSEED reaction IDs link biochemistry
to KEGG via canonical ontology mappings; GTDB r214 provides the taxonomic
backbone). We will not do a primary literature search.

## Approach (Three Deliverable Layers)

### Layer 1 — Catalog + Topic Map (foundation)

Group all 1,531 tables across 14 tenants into biological / environmental
**topic clusters**. Topic axes (initial — to be refined during NB01):

- **Taxonomy / phylogeny** — GTDB, NCBI, species-clade tables
- **Genome structure** — assemblies, annotations (eggNOG, bakta, COG, PFAM)
- **Pangenome content** — gene clusters, gene families, core/accessory flags
- **Pathways / function** — GapMind, KEGG, ModelSEED, BRITE
- **Biochemistry** — ModelSEED reactions/compounds, FBA models
- **Fitness / phenotype** — RB-TnSeq (Fitness Browser), BacDive, Web of
  Microbes, carbon source phenotypes, growth curves
- **Mobile elements / virome** — GeNomad, prophage tables, PhageFoundry
- **Multi-omics** — NMDC metabolomics / proteomics / lipidomics
- **Environment / sample metadata** — NCBI_env, IMG_env, AlphaEarth
  embeddings, ENVO/GOLD, MGnify biomes, geolocation
- **Field / observational** — ENIGMA CORAL, USGS, Harvard Forest, Planet
  Microbe, ESE
- **Structural / experimental** — AlphaFold, PDB, structural biology tables
- **Literature / reference** — PaperBLAST, UniRef50/90/100, refdata

Each table gets:
- One primary topic + 0–2 secondary topics (multi-label tagging)
- Approximate row count (computed once, cached — never re-counted on every load)
- Tenant + agency/program provenance (NMDC=DOE/NIH/multi-agency,
  ENIGMA=DOE-SFA, PROTECT=ARPA-H, NETL=DOE, USGS=federal,
  Planet Microbe=NSF, Phage Foundry=DOD-BTO?, etc. — confirm in NB01)
- Coverage axes where derivable: % of genomes covered, geographic extent,
  temporal span

Outputs:
- `data/table_topic_map.csv` — every table with topic tags, agency, size,
  coverage flags
- `figures/topic_map.png` — tenant × topic heatmap or Sankey

### Layer 2 — Linkage Atlas (the "amplify each other" piece)

Enumerate shared join keys and *verify they actually match in practice*. The
candidate join keys (from `docs/pitfalls.md`, `MEMORY.md`, and the briefing
memo):

| Join key | Crosses | Known caveats |
|---|---|---|
| GTDB species clade / taxon ID | pangenome ↔ everything taxonomic | r214 vintage, MAG mis-placements |
| Genome accession (GCA/GCF) | pangenome ↔ BacDive ↔ NCBI ↔ ENIGMA ↔ NMDC | GCF vs GCA fallback patterns |
| KEGG KO | pangenome ↔ FB ↔ NMDC ↔ GapMind | eggNOG K assignments vs bakta vs IPS divergence |
| COG / PFAM / EC | annotation tables across tenants | bakta vs IPS PFAM coverage gap (12/22 markers silently missing) |
| ModelSEED reaction / compound ID | biochem ↔ pathways ↔ FBA | name vs ID, alias resolution |
| Lat/lon coordinates | NCBI biosample ↔ AlphaEarth ↔ NMDC ↔ ENIGMA ↔ MicrobeAtlas | institutional addresses (36% flagged) |
| ENVO / GOLD ecosystem | env metadata across tenants | sparse population especially for environmental samples |
| ASV / biosample ID | NMDC ↔ MGnify ↔ ENIGMA ↔ Planet Microbe | format heterogeneity |
| Fitness Browser locusId / orgId | FB ↔ pangenome (via fb_pangenome_link.tsv, 30 orgs) | only 30 organisms, BBH-derived |
| Bakta product / domain | pangenome ↔ structural | bakta_pfam_domains missing many PFs |

For each candidate edge, compute:
- **Theoretical edge**: do both tables contain the key?
- **Realized coverage**: what fraction of rows on each side actually join?
- **ID format collisions**: GCF↔GCA, species ID with `--`, KEGG K vs PFAM
  PF, integer-as-string casts, etc.
- **Sample example join**: a 2–5-row toy SELECT that demonstrates the edge

Outputs:
- `data/join_key_atlas.csv` — every candidate edge with theoretical vs
  realized coverage + caveat note
- `figures/linkage_graph.png` — tenant-level graph with edge weights =
  realized coverage; node colors = agency/program
- `data/synergy_use_cases.md` — narrative "if you have X you can amplify
  with Y to answer Q" — 10–15 concrete combinations

### Layer 3 — Realized-Use Audit (validation)

Mine the ~70 existing BERIL projects to extract every cross-database
combination *already attempted*, with outcome:

- **Sources**: `projects/*/README.md`, `projects/*/RESEARCH_PLAN.md`,
  `projects/*/REPORT.md`, plus `docs/research_ideas.md` completed-ideas
  section.
- **Extraction**: for each project, identify (a) which BERDL databases /
  tables it touched, (b) which cross-database joins it performed, (c) the
  outcome category — *worked / partial / null result / blocked by data
  limitation*. Status comes from `beril.yaml` plus the project's `## Status`
  section.
- **Aggregation**: per cross-database edge, count the number of successful
  projects, partial, and null. This is the *empirically validated* layer.

This is the validation step for Layer 2: an edge with high theoretical
coverage but zero realized projects is suspicious; an edge with many
projects across multiple groups is robust.

Likely delegated to an `Explore` agent for the bulk read (70 READMEs × ~3
docs each = ~200 file reads) to keep main context clean.

Outputs:
- `data/realized_use_audit.csv` — project × database matrix + outcome tag
- `figures/realized_linkage_network.png` — same node set as Layer 2,
  edges weighted by realized-project count
- Side-by-side comparison: theoretical (Layer 2) vs realized (Layer 3)

## Data Sources

All sources are internal to this repo (no external API calls except `berdl_notebook_utils.get_databases()` etc. for live queries against BERDL):

- BERDL Lakehouse: live via Spark Connect (on-cluster session)
- `data/berdl_inventory.md` (just generated)
- `docs/` (overview, pitfalls, performance, research_ideas, discoveries)
- `projects/*/` (all ~70 projects' README + RESEARCH_PLAN + REPORT)
- `MEMORY.md` (cross-collection linkages already known)

## Query Strategy

### Tables Required
The atlas itself doesn't run heavy queries — it inspects schema and computes
**bounded coverage statistics** per join key.

| Operation | Where | Cost |
|---|---|---|
| Enumerate tables per tenant | `berdl_notebook_utils.get_databases(return_json=False)` + `get_tables()` | trivial |
| Row count per table | one-shot cached `COUNT(*)` per table, then never repeated | one-time, parallelized |
| Sample 5 rows per table for schema inspection | `SELECT * FROM <t> LIMIT 5` | trivial |
| Coverage of GTDB ID across tables | `SELECT COUNT(DISTINCT taxon_id)` filtered by presence in candidate tables | moderate |
| Realized join: rows that match across a key pair | `SELECT COUNT(*) FROM A JOIN B ON A.k = B.k` with sampled subsets when full join is expensive | moderate |

### Performance Plan
- **Tier**: on-cluster Spark SQL (we are on JupyterHub; direct access). For
  expensive cross-tenant joins, sample (TABLESAMPLE or LIMIT N) before
  computing the full join.
- **Estimated complexity**: moderate. Row counts on the largest tables
  (`gene`, `genome_ani`, `reaction_similarity`) are individually fast with
  `COUNT(*)` but require care.
- **Known pitfalls** (apply per `docs/pitfalls.md`):
  - Species IDs contain `--` (use exact equality, not LIKE)
  - String-typed numeric columns (CAST before comparison)
  - eggNOG K assignments vs bakta product can disagree (8% concordance for xoxF
    per lanthanide atlas — relevant for our KEGG-as-join-key claim)
  - `bakta_pfam_domains` missing many PFAMs (12/22 markers silently absent
    per plant_microbiome_ecotypes audit)
  - `nmdc.biosample_set_associated_studies` joins on `parent_id` not `id`
    (per harvard_forest_warming)

## Analysis Plan

### Notebook 1 (`00_inventory_audit.ipynb`) — Catalog + agency provenance

- **Goal**: produce `table_topic_map.csv`. Walk every accessible database;
  for each table, capture (name, tenant, agency/program, row count once,
  primary topic, secondary topics, brief description from
  `DESCRIBE EXTENDED`).
- **Expected output**: `data/table_topic_map.csv`, agency provenance lookup
  table (`data/tenant_to_agency.csv` — curated manually + cross-referenced
  with on-cluster tenant metadata).
- **Pitfalls to surface**: tenants with restricted access; row-count
  failures on huge tables.

### Notebook 2 (`01_topic_map_visual.ipynb`) — Topic map figure

- **Goal**: render `figures/topic_map.png` (tenant × topic heatmap with
  cell values = table counts, sized by total row count). Optionally a
  parallel Sankey: tenant → topic → table-class.
- **Expected output**: `figures/topic_map.png`, `figures/topic_map_sankey.html`.

### Notebook 3 (`02_join_key_atlas.ipynb`) — Linkage atlas

- **Goal**: per candidate join key, enumerate tables that carry it, compute
  coverage rate and realized cross-tenant join sizes. Document caveats
  inline. Build `data/join_key_atlas.csv` and `figures/linkage_graph.png`.
- **Expected output**: the CSV, the graph figure, plus a markdown
  appendix of failure modes and worked SELECT examples per edge.

### Notebook 4 (`03_realized_use_audit.ipynb`) — Project-driven audit

- **Goal**: parse all ~70 projects' READMEs / plans / reports; extract
  database touchpoints and outcomes. Likely uses an `Explore` agent for
  bulk reads, aggregates results in this notebook. Produce
  `data/realized_use_audit.csv` and `figures/realized_linkage_network.png`.
- **Expected output**: CSV + figure + side-by-side comparison to Layer 2.

### Notebook 5 (`04_synthesis.ipynb`) — Synergy use cases

- **Goal**: write `data/synergy_use_cases.md` — 10–15 narrative use cases
  framed for two audiences: "as a KBase user, if you have X you can
  combine with Y to ask Q" and "as a funder, the X-program × Y-program
  combination enables research direction Z". Include 3–5 prioritized
  *gap* findings (edges that look high-value but are blocked or
  unexercised).
- **Expected output**: the markdown deliverable, plus the depiction
  artifact (a single high-quality figure suitable for slide use,
  combining topic map + linkage graph + cross-agency overlay).

## Expected Outcomes

- **If H1 supported** (expected): the linkage atlas shows ≥10 high-coverage
  cross-tenant join keys, the realized-use audit confirms most are
  exercised by existing projects, and we produce 10+ ranked synergy
  use-cases with concrete query templates. Gap findings identify 3–5
  high-value linkages that remain unexercised.
- **If H0 not rejected**: most join keys turn out to have <10% realized
  coverage in practice (e.g., taxonomy maps don't align, biosample IDs
  don't match across tenants). The depiction becomes "BERDL is mostly a
  set of independent silos" with prioritized harmonization recommendations.
  Still useful — just a different story.
- **Potential confounders**:
  - **Access asymmetry** — what we can see depends on tenant membership.
    Note this explicitly in every figure. The "u" tenant and several
    others may be invisible.
  - **Stale schema docs** — `docs/pitfalls.md` was written across many
    months; some entries may be out of date. Verify live where possible.
  - **Project README quality variance** — some projects under-document
    which databases they touch; the realized-use audit will have
    extraction noise.
  - **Topic-tagging subjectivity** — multi-label topic assignment is a
    judgment call; commit the tagging schema as a separate file and
    invite challenge.

## Revision History
- **v1** (2026-05-12): Initial plan.

## Authors
- Adam Arkin (University of California, Berkeley, ORCID: 0000-0002-4999-2931)

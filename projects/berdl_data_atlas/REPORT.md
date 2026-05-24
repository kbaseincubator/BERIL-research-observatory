# BERDL Data Atlas — Inventory, Topic Map, and Cross-Reference Synergies

**Status:** complete (analysis), pending external validation of agency mapping.

## Executive summary

BERDL hosts **1,740 deduplicated tables across 119 databases, 17 tenants, and 9 funding agencies / programs**, covering 17 biological topics. The atlas finds:

1. **DOE-BER is the only broad-coverage agency** (15/15 topics; 63% of all tables, 80% of BERIL projects); ARPA-H (PROTECT), Defense/HHS (PhageFoundry), NSF (Planet Microbe), DOE-FE (NETL), and DOI (USGS) contribute narrower but unique slices.
2. **536 cross-tenant bridges** exist at the schema level, defined by 29 canonical join keys (`sample_id`, `genome_id`, `ncbi_taxon_id`, `feature_id`, `ec_number`, `kegg_pathway`, …).
3. **77% (51/66) of audited BERIL projects already span multiple tenants** — the lakehouse architecture is delivering on cross-program synergy. Realized use is concentrated on the `kbase × kescience` axis (36 projects).
4. **The five highest-leverage bridges have zero realized use**: `kescience ↔ refdata` (12 keys, including AlphaFold IDs), `enigma ↔ phagefoundry` (11), `kbase ↔ refdata` (11, including `gtdb_taxonomy`), `nmdc ↔ protect` (10), `nmdc ↔ refdata` (9). Five concrete use cases derived from these bridges are documented in NB04 and recommended as the next class of analyses to scope.

The depiction was built for two audiences: KBase users who want to know "where to look for what" and funders / PIs evaluating cross-agency synergies. Both views are summarized in NB04 §3.

## Approach

The atlas was built in three layers, each delivered as a Jupyter notebook with saved outputs (audit-trail artifacts):

| Layer | Notebook | Output |
|---|---|---|
| Catalog + topic tagging | NB00 | `data/table_topic_map.csv` (1,740 rows) + `data/tenant_to_agency.csv` |
| Topic map (agency + concentration + synergy) | NB01 | 3 figures + topic concentration / synergy capacity tables |
| Linkage atlas (29 join keys, 536 bridges) | NB02 | `data/join_keys.json`, `data/cross_tenant_bridges.csv`, `data/join_key_coverage.csv` |
| Realized-use audit (66 projects) | NB03 | `data/realized_use.csv`, `data/theoretical_vs_realized.csv`, `data/untapped_bridges.csv` |
| Synthesis + 5 synergy use cases | NB04 | Composite atlas figure + use-case spec |

Supporting code lives in `src/`:
- `build_inventory.py` — parallel schema walker (16 workers, ~95 s for 1,740 tables). Filters out dotted-namespace duplicates the Spark Connect catalog exposes alongside legacy underscored names.
- `topic_tags.py` — ordered regex rules over `(db, table, columns)`, plus the tenant → agency / program / funder map.

## Key findings

### Inventory (NB00)

- **1,740 tables / 119 dbs / 17 tenants** is the canonical scale.
- A first walk reported 3,587 tables; the Spark Connect catalog exposes every Delta table under two names (`enigma.coral` AND `enigma_coral`). `walk_inventory()` now drops dotted duplicates by default.
- Topic-distribution highlights: `field_observational` 40%, `mobile_phage` 14%, `fitness_phenotype` 11%, `genome` 6.4%, then everything else <4%. Unclassified residual is 0.9% (16 rows), all personal-namespace / one-off survey data.

### Topic map (NB01)

- **DOE-BER covers every topic.** ENIGMA contributes 601 `field_observational` tables; the rest is spread across KBase reference, KE Science phenotype, NMDC multi-omics, refdata reference.
- **Defense/HHS is mono-topic** (PhageFoundry, all `mobile_phage`) — high inbound-cross-reference potential.
- **Topic concentration**: highly concentrated topics are reference resources (`mobile_phage` 96% PhageFoundry, `pangenome` 79% kbase, `reference_protein` 78% refdata); cross-tenant topics are natural join surfaces (`taxonomy` 12 tenants, `genome` 8, `annotation` 8, `multiomics` 7).
- **Synergy capacity** (distinct topics × entropy): `kbase` (10 topics, 2.87 bits), `nmdc` (11, 2.61), `protect` (6, 2.37), `kescience` (11, 1.83) are the broadest anchors. `enigma` is deep-but-narrow (5 topics, 0.43 bits). `phagefoundry` and `usgs` are mono-topic.

### Linkage atlas (NB02)

- **29 canonical join keys** scanned across the catalog. Workhorses by tenant span: `sample_id` (10), `genome_id` (9), `ncbi_taxon_id` (9), `feature_id` (9), `ec_number` (8).
- **536 cross-tenant bridges** identified. Top bridges share up to 7 keys: `kbase.pathway ↔ kescience.pathway`, `kescience.pathway ↔ phagefoundry.mobile_phage`, `refdata.structural ↔ kescience.structural` (via `alphafold_pdb` + `protein_id` + `ncbi_taxon_id`).
- **Surprises:** `gtdb_taxonomy` appears in only 5 tables despite being the modern standard. `assembly_accession` / `gcf_gca` are refdata-only. `envo` ontology IDs are limited to NMDC + refdata; other field tenants use ad-hoc `isolation_source` strings.

### Realized-use audit (NB03)

- **66 BERIL projects audited** via README "Data Sources" mining; 4 excluded (`berdl_data_atlas`, `misc_exploratory`, plus 2 incomplete).
- **51 / 66 (77%) are already cross-tenant.** `kbase` is in 53/66, `kescience` in 35/66. `kbase ↔ kescience` is the dominant realized bridge (36 projects).
- **Heavy in BERDL ≠ heavy in reuse.** ENIGMA holds 36% of tables but is in 6 projects (9%). PhageFoundry holds 14% / 5 projects. PROTECT holds 4% / 2 projects.
- **Untapped high-key bridges**: see §Findings overview.

### Synthesis (NB04)

The composite atlas figure (`figures/nb04_atlas_composite.png`) shows tenant × topic heat plus per-tenant realized-reuse bars and the theory-vs-practice scatter on a single sheet.

**Five synergy use cases** derived from the top untapped bridges, each with motivating question + join recipe + payoff + audience message:

| UC | Bridge | Keys | Question |
|---|---|---|---|
| UC1 | kescience ↔ refdata | 12 | Do high-fitness-impact genes have structural signatures detectable in AlphaFold? |
| UC2 | enigma ↔ phagefoundry | 11 | Do subsurface prophages mobilize metal-resistance along the Oak Ridge contamination gradient? |
| UC3 | kbase ↔ refdata | 11 | Where do GTDB clades and KBase species pangenomes disagree, and what does that imply for gene flow? |
| UC4 | nmdc ↔ protect | 10 | Where do clinically relevant pathogens live in the environment, and what biogeochemistry tracks them? |
| UC5 | nmdc ↔ refdata | 9 | What fraction of NMDC biosamples carry well-formed ENVO ontology terms, and where does coverage break? |

## What this atlas does not establish

- **Value-space validity of joins.** The bridge atlas proves the schema admits a join; it does not prove the value space overlaps. `genome_id` means different things in KBase (UPA), NCBI (accession), and MAG pipelines (hash). Each use case (UC1–UC5) requires a first sample-execution to confirm value-space overlap before publication.
- **Agency provenance for two tenants.** `msyscolo` and `phagefoundry` primary funders are flagged "likely" in `tenant_to_agency.csv`. `evaluation` and `lambda` are not yet mapped (7 tables total). Verify with program documentation before external use.
- **Audit completeness.** The realized-use audit was README-based; data-source mentions buried in research plans or referenced only in notebook source may have been missed. True per-project tenant breadth is a **lower bound**.

## Reproduction

**Prerequisites:** BERDL JupyterHub access with valid `KBASE_AUTH_TOKEN`. Python 3.11+ with `pandas`, `numpy`, `matplotlib`, `seaborn`, `networkx`, `berdl_notebook_utils` (already on JupyterHub).

```bash
# 1. Rebuild the catalog (~95 s; parallel Spark Connect schema walk)
python -m projects.berdl_data_atlas.src.build_inventory

# 2. Re-execute the four notebooks in order
cd projects/berdl_data_atlas/notebooks
for nb in 00_inventory_audit 01_topic_map 02_linkage_atlas 03_realized_use_audit 04_synthesis_and_use_cases; do
    jupyter nbconvert --to notebook --execute --inplace ${nb}.ipynb
done
```

Re-runs are idempotent against `data/realized_use.csv` (the project audit). To refresh the project audit, re-run the Explore-agent prompt in NB03's intro against `projects/`.

## Artifacts

**Data:**
- `data/table_topic_map.csv` — canonical inventory (1,740 rows; 11 columns including tenant, agency, program, primary_topic, secondary_topics, n_columns, column_names).
- `data/tenant_to_agency.csv` — manual tenant → agency / program / funder map.
- `data/join_keys.json` — `{key: [{tenant, topic, db, table}, …]}` for 29 canonical keys.
- `data/cross_tenant_bridges.csv` — 536 ranked (tenant×topic) bridge pairs with key inventory.
- `data/join_key_coverage.csv` — per-key coverage stats.
- `data/realized_use.csv` — 66 BERIL projects × tenants × databases × topic_focus.
- `data/theoretical_vs_realized.csv` — bridge overlay (72 tenant pairs).
- `data/untapped_bridges.csv` — 20 prioritized unrealized bridges.
- `data/tenant_reuse_frequency.csv` — per-tenant project count.

**Figures (10):** `figures/nb0[0-4]_*.png` — topic distribution, tenant×topic heatmap, agency×topic heatmap, topic concentration, synergy capacity, key×tenant heatmap, linkage graph, tenant frequency, theory vs realized scatter, composite atlas.

**Notebooks (5):** `notebooks/0[0-4]_*.ipynb` — each with executed outputs as audit-trail artifacts.

## Authors
- Adam Arkin (University of California, Berkeley, ORCID: 0000-0002-4999-2931)

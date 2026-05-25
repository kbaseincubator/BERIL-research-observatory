# BERDL Data Atlas — Inventory, Topic Map, and Cross-Reference Synergies

## Research Question
What data is available in BERDL (across tenants, agencies, and programs), what
biological topics does it cover, and where do datasets amplify each other when
combined? Build a depiction that serves both KBase users picking what to
analyze and funders / PIs evaluating cross-agency, cross-program synergies.

## Status
Completed — BERDL Lakehouse mapped end-to-end: 1,740 tables, 17 tenants, 10 funders, 17 topics, billion-row depth; 536 cross-tenant bridges identified; 77% of 66 BERIL projects already cross-tenant; UC1 (structural fitness) sample-validated against the live cluster.
See [Report](REPORT.md) for full findings.

## Overview
KBase BERDL hosts **1,740 deduplicated tables** across 119 databases, 17
tenants, and 10 funding agencies / programs (DOE-BER, DOE BRaVE, DOE-FE,
DOE/NSF, ARPA-H, NSF, DOI, plus academic / multi / user) spanning 17
biological topics. Underneath those tables sits **billion-row scale data**:
~1.01 B KBase pangenome genes (293K genomes / 27.7K species pangenomes),
475M UniRef100 clusters, 241M AlphaFold predicted structures, 27.4M
FitnessBrowser measurements, 75M metatranscriptomic abundance rows, 40M
PubMed records, plus reference layers for biochemistry, mass spec, growth
phenotype, and environmental embeddings. The project builds a cohesive
depiction in four layers:

1. **Catalog + topic map** (NB00, NB01) — every table tagged by tenant,
   agency, primary biological topic; tenant × topic and agency × topic
   coverage; topic concentration and per-tenant synergy capacity.
2. **Linkage atlas** (NB02) — 29 canonical join keys scanned across the
   catalog, yielding **536 cross-tenant bridges** (tenant×topic pairs sharing
   ≥ 1 join key).
3. **Realized-use audit + synthesis** (NB03, NB04) — 66 BERIL projects mined
   for actual cross-tenant use. **77% are already cross-tenant**; `kbase ×
   kescience` dominates realized use. Five concrete synergy use cases derived
   from the highest-leverage *untapped* bridges (structural fitness, subsurface
   viral ecology, GTDB ↔ KBase harmonization, pathogens-in-environment, ENVO
   ontology coverage). UC1 (structural fitness) sample-validated against the
   live cluster (55,454 genes × AlphaFold).
4. **Depth inventory** (NB05) — 65 curated headline tables × `COUNT(*)` /
   `COUNT(DISTINCT)` against the live cluster, rolled up by biological
   entity class (genomes, genes, proteins, structures, fitness, samples,
   community profiles, mass spec, viruses, biochemistry, literature).

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy.
- [Report](REPORT.md) — findings, interpretation, supporting evidence,
  reproduction instructions, artifact list.
- Notebooks (`notebooks/`) — NB00 inventory audit, NB01 topic map, NB02 linkage
  atlas, NB03 realized-use audit, NB04 synthesis + use cases.
- Data (`data/`) — table_topic_map, tenant_to_agency, join_keys,
  cross_tenant_bridges, realized_use, theoretical_vs_realized, untapped_bridges.
- Figures (`figures/`) — 10 figures including the composite atlas
  (`nb04_atlas_composite.png`).

## Reproduction
**Prerequisites:** BERDL JupyterHub access with valid `KBASE_AUTH_TOKEN`.
Python 3.11+ with `pandas`, `numpy`, `matplotlib`, `seaborn`, `networkx`,
and `berdl_notebook_utils` (already on JupyterHub).

```bash
# 1. Rebuild the catalog (~95 s; parallel Spark Connect schema walk)
python -m projects.berdl_data_atlas.src.build_inventory

# 2. Refresh per-entity volume counts (~60 s; 65 COUNT queries against Spark).
#    See REPORT.md "Reproduction" for the inline runner snippet.

# 3. Re-execute the six notebooks in order
cd projects/berdl_data_atlas/notebooks
for nb in 00_inventory_audit 01_topic_map 02_linkage_atlas 03_realized_use_audit 04_synthesis_and_use_cases 05_data_volume; do
    jupyter nbconvert --to notebook --execute --inplace ${nb}.ipynb
done
```

## Authors
- Adam Arkin (University of California, Berkeley, ORCID: 0000-0002-4999-2931)

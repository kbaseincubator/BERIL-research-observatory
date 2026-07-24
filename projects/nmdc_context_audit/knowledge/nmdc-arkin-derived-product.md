---
name: nmdc-arkin-derived-product
description: kbase.nmdc_arkin is the Arkin-lab enriched derivative of NMDC omics — embeddings, traits, unified annotations
metadata:
  type: reference
  provenance: LBNL Arkin Lab derivation of NMDC omics
  tenant: kbase
  databases: [kbase.nmdc_arkin]
  currency: "2026-05-27"
  authority: LBNL Arkin Lab (built on NMDC)
related: [nmdc-data-outside-nmdc-tenant, nmdc-value-added-by-berdl, nmdc-prior-project-usage, nmdc-choosing-the-right-resource]
---

# `kbase.nmdc_arkin` — the Arkin-lab derived product

The most feature-rich and most-used "NMDC" resource in BERDL, and the one whose name is
most misleading: it is **not raw NMDC** but an **LBNL Arkin Lab derivation** built *on top
of* NMDC omics — 63 tables of processed, embedded, and inferred data. Last snapshot
2026-05-27.

## What's in it (by kind)
- **Omics "gold" matrices**: `metabolomics_gold` (3,129,061), `lipidomics_gold`,
  `proteomics_gold`, `metatranscriptomics_gold` (~75M), `nom_gold` (~9.9M NOM mass-spec),
  `nom_matrix_optimized`, `kraken_gold` (~29M), `gottcha_gold`, `centrifuge_gold`.
- **Taxonomy**: `taxonomy_dim` (2,594,787), `contig_taxonomy`, `covstats_taxonomy_rollup`,
  `taxstring_lookup`, `taxonomy_features` (wide numeric matrix).
- **Embeddings**: `embeddings_v1` (5,316; 256-dim), `unified_embeddings`,
  `taxonomy_embeddings` (+ phylum/order/family/genus variants), `trait_embeddings`,
  `abiotic_embeddings`, `biochemical_embeddings`, `embedding_metadata`.
- **Inferred traits**: `trait_unified`, `trait_features`, `trait_sources`,
  `trait_taxonomy_mapping`.
- **Unified annotations/ontologies**: `annotation_terms_unified`,
  `annotation_hierarchies_unified`, `*_hierarchy_flat` for COG/EC/GO/KEGG/MetaCyc,
  `kegg_ko_pathway`, `metacyc_pathways`, `rhea_reactions`. *(Note: `rhea_reactions`,
  `go_terms`, etc. are external ontologies embedded here — provenance blur; cf.
  [[nmdc-ref-data-is-pfam]].)*
- **Join fabric**: `omics_files_table` (385,562), `sample_file_lookup` (6,700),
  `sample_file_selections`, `study_table` (48).

## Critical join/typing pitfalls (from prior projects)
- Classifier and metabolomics tables key on **`file_id`, not `sample_id`**; the
  classifier `file_id` namespace (`nmdc:dobj-11-*`) and metabolomics (`nmdc:dobj-12-*`)
  **do not overlap** — bridge through `omics_files_table`.
- `abiotic_features` numeric columns are **STRING**; cast before comparison. Columns use a
  `_has_numeric_value` suffix (exception: `annotations_ph`). Some parse as all-zeros.
- `taxonomy_features` is a wide matrix with numeric column names and no `sample_id`/`file_id`.
- `trait_features` exposes ~90 `functional_group:*` columns — use `stack()`.
- Embedding dimensionality **varies across tables**.
- DECIMAL columns (e.g. `centrifuge_gold.abundance`) return `decimal.Decimal`, not float.
- `metabolomics_gold` KEGG annotation rate is ~2% → expect string-matching, not clean joins.

Full pitfalls: `docs/pitfalls.md` `## nmdc_arkin` and `## NMDC (nmdc_arkin) Pitfalls`.

## Provenance summary
Origin: **LBNL Arkin Lab** (derived from NMDC omics). Host: `kbase` tenant. Class-4
("other-group derivation") in [[nmdc-label-is-overloaded]]. This is where most prior BERIL
NMDC work happened — see [[nmdc-prior-project-usage]].

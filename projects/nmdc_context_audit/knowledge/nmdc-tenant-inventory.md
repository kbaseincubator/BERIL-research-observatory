---
name: nmdc-tenant-inventory
description: What the four databases in the real nmdc tenant contain (and which are actually external)
metadata:
  type: reference
  provenance: mixed (NMDC + NCBI + Pfam)
  tenant: nmdc
  databases: [nmdc.metadata, nmdc.results, nmdc.ncbi_biosamples, nmdc.ref_data]
  currency: "2026-05-20"
  authority: microbiomedata.org
related: [nmdc-program-what-it-is, ncbi-biosamples-not-nmdc, nmdc-ref-data-is-pfam, nmdc-completeness-and-currency]
---

# The `nmdc` tenant: four databases, three origins

The `nmdc` tenant (steward `mamillerpa`, data owner `tgu2`, org LBNL) holds **four**
databases. Two are genuine NMDC; two are external data re-hosted here.

## `nmdc.metadata` — genuine NMDC metadata (49 tables)
The NMDC data model flattened from LinkML into Iceberg. Core `*_set` tables and their
child/association tables:
- `biosample_set` (**16,640**) — biosamples; the entry point for environmental context.
- `study_set` (**84**) — studies; `nmdc:sty-*`.
- `data_generation_set` (**12,026**) — omics data generation events.
- `workflow_execution_set` (**30,882**) — processing runs (`_has_input`/`_has_output`/`_was_informed_by` join tables).
- `functional_annotation_agg` (**54,348,408**) — aggregated functional annotations.
- Environmental child tables: `biosample_set_agrochem_addition`, `_air_temp_regm`,
  `_chem_administration`, `_fertilizer_regm`, `_gaseous_environment`, `_host_diet`,
  `_humidity_regm`, `_watering_regm`, `_perturbation`, `_misc_param`, …
- **Join note** (from prior projects): `biosample_set_associated_studies` joins on
  `parent_id`, not `id`.

## `nmdc.results` — genuine NMDC processing outputs (9 tables)
- `annotation_kegg_orthology` (**1,831,998,811**) — huge; always filter before scanning.
- `annotation_enzyme_commission`, `pfam_annotation_gff` — functional annotation.
- `gtdbtk_bacterial_summary` (**18,410**), `kraken2_classification_report`,
  `gottcha2_classification_report`, `centrifuge_output_report_file` — taxonomy.
- `checkm_statistics` (**69,723**), `annotation_statistics` (**4,815**) — QC/summary.

## `nmdc.ncbi_biosamples` — **NOT NMDC** (17 tables)
An NCBI biosample harvest (51.7M biosamples, 756M attribute rows). Fully detailed in
[[ncbi-biosamples-not-nmdc]]. Staler than the rest (2026-03-09).

## `nmdc.ref_data` — **NOT NMDC** (1 table)
`pfam_terms` (27,481) — the Pfam controlled vocabulary. See [[nmdc-ref-data-is-pfam]].

---
Scale/currency for all four: [[nmdc-completeness-and-currency]]. What BERDL added on top
of upstream NMDC: [[nmdc-value-added-by-berdl]].

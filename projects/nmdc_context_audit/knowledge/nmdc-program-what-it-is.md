---
name: nmdc-program-what-it-is
description: NMDC the program (National Microbiome Data Collaborative) vs "nmdc" the BERDL tenant
metadata:
  type: reference
  provenance: NMDC (DOE-BER)
  tenant: nmdc
  databases: [nmdc.metadata, nmdc.results]
  currency: "2026-05-20"
  authority: microbiomedata.org
related: [nmdc-tenant-inventory, nmdc-label-is-overloaded, nmdc-neon-namesake-collision]
---

# NMDC the program vs "nmdc" the tenant

**NMDC = National Microbiome Data Collaborative** (https://microbiomedata.org/), a
DOE-BER program that integrates multi-omics microbiome data under a shared, standards-based
data model. It is a real, external scientific consortium — its authoritative outputs are
FAIR biosample/study metadata and standardized omics processing results.

In BERDL this maps to the **`nmdc` tenant** (tenant description: *"Enabling microbiome
science by connecting data, people, and ideas"*, org LBNL, steward `mamillerpa`, data
owner `tgu2`). But two things break the naive "nmdc tenant = NMDC program" equation:

1. **Not everything in the `nmdc` tenant is NMDC-generated.** `nmdc.ncbi_biosamples` is an
   NCBI harvest and `nmdc.ref_data` is Pfam — both external. See
   [[ncbi-biosamples-not-nmdc]] and [[nmdc-ref-data-is-pfam]].
2. **Not all NMDC-derived data is in the `nmdc` tenant.** `kbase.nmdc_mags` and
   `kbase.nmdc_arkin` live in the `kbase` tenant. See [[nmdc-data-outside-nmdc-tenant]].

And the acronym collides: **NEON** (National Ecological Observatory Network, an NSF program)
appears as `kbase.nmdc_neon` — a different program entirely. See
[[nmdc-neon-namesake-collision]].

## The genuinely-NMDC core
The parts that *are* faithful NMDC program outputs:
- **`nmdc.metadata`** — the NMDC data model, flattened from LinkML/Mongo into 49 `*_set`
  Iceberg tables (`biosample_set`, `study_set`, `data_generation_set`,
  `workflow_execution_set`, …). 16,640 biosamples across 84 studies.
- **`nmdc.results`** — standardized NMDC processing outputs: functional annotation
  (`annotation_kegg_orthology` 1.83B rows, `annotation_enzyme_commission`), taxonomic
  classification (`gtdbtk_bacterial_summary`, `kraken2_*`, `gottcha2_*`, `centrifuge_*`),
  and QC (`checkm_statistics`).

NMDC-native identifiers you will see: `nmdc:bsm-*` (biosample), `nmdc:sty-*` (study),
`nmdc:dgns-*`/`nmdc:dobj-*` (data generation/object), `nmdc:wf*` (workflow execution).

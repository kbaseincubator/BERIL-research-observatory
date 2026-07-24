---
name: nmdc-completeness-and-currency
description: Per-resource scale (row counts) and data currency (Iceberg snapshot ages) for every NMDC-labeled resource
metadata:
  type: reference
  provenance: audit measurement
  tenant: nmdc, kbase
  databases: [nmdc.metadata, nmdc.results, nmdc.ncbi_biosamples, nmdc.ref_data, kbase.nmdc_arkin, kbase.nmdc_mags, kbase.nmdc_neon]
  currency: "2026-07-10"
  authority: nmdc_context_audit project (live catalog)
related: [nmdc-label-is-overloaded, nmdc-choosing-the-right-resource, nmdc-value-added-by-berdl]
---

# Completeness & currency

Measured 2026-07-10 on the live catalog (`../notebooks/00_nmdc_landscape.ipynb`,
`../data/nmdc_landscape.csv`). Counts via Iceberg metadata; currency =
`max(committed_at)` from `.snapshots`. See `../figures/nmdc_currency.png` and
`../figures/nmdc_scale.png`.

## Scale (spans 5+ orders of magnitude)
| Resource | Signature table | Rows | Notes |
|---|---|---:|---|
| `nmdc.results` | `annotation_kegg_orthology` | 1,831,998,811 | filter before any scan |
| `nmdc.ncbi_biosamples` | `biosamples_attributes` | 756,112,544 | attribute key/values |
| `nmdc.metadata` | `functional_annotation_agg` | 54,348,408 | |
| `nmdc.ncbi_biosamples` | `biosamples_flattened` | 51,711,888 | NCBI samples |
| `nmdc.ncbi_biosamples` | `sra_biosamples_bioprojects` | 33,738,101 | |
| `kbase.nmdc_arkin` | `metabolomics_gold` | 3,129,061 | |
| `kbase.nmdc_arkin` | `taxonomy_dim` | 2,594,787 | |
| `nmdc.ncbi_biosamples` | `bioprojects_flattened` | 1,034,221 | |
| `kbase.nmdc_arkin` | `omics_files_table` | 385,562 | join fabric |
| `kbase.nmdc_neon` | `sample_data` | 340,871 | NEON |
| `checkm_statistics` (`nmdc.results`) | | 69,723 | |
| `kbase.nmdc_mags` | `mag_catalog` | 62,346 | |
| `nmdc.ref_data` | `pfam_terms` | 27,481 | Pfam |
| `gtdbtk_bacterial_summary` (`nmdc.results`) | | 18,410 | |
| `kbase.nmdc_neon` | `neon_mag_catalog` | 16,093 | |
| `nmdc.metadata` | `biosample_set` | 16,640 | **NMDC biosamples** |
| `nmdc.metadata` | `workflow_execution_set` | 30,882 | |
| `nmdc.metadata` | `data_generation_set` | 12,026 | |
| `nmdc.metadata` | `study_set` | 84 | |
| `kbase.nmdc_arkin` | `study_table` | 48 | |

**Key contrast**: the genuine NMDC biosample universe is **16,640** samples, while the
co-hosted NCBI mirror is **51.7M** — a ~3,000× difference that is invisible from the names.

## Currency (latest Iceberg snapshot)
| Resource | Last commit | Freshness |
|---|---|---|
| `kbase.nmdc_mags` | 2026-07-02 | freshest (days) |
| `kbase.nmdc_neon` | 2026-07-02 | fresh |
| `kbase.nmdc_arkin` | 2026-05-27 | ~6 weeks |
| `nmdc.metadata` | 2026-05-20 | ~7 weeks |
| `nmdc.results` | 2026-05-20 | ~7 weeks |
| `nmdc.ref_data` | 2026-05-20 | ~7 weeks |
| `nmdc.ncbi_biosamples` | 2026-03-09 | **stalest (~4 months)** |

## Completeness caveats
- All resources are **point-in-time snapshots**, not live mirrors. `nmdc.metadata` (16,640
  biosamples / 84 studies) is a subset of the growing upstream NMDC portal; the NCBI mirror
  lags NCBI BioSample by months.
- Different tables **within** a database can carry different snapshot times (they were
  ingested per-table), so check the specific table you depend on, not just the database.
- Empty/broken artifacts exist and should not be counted as "NMDC data": see
  [[nmdc-naming-aliases-and-cruft]].

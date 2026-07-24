---
name: nmdc-choosing-the-right-resource
description: Decision guide — translate a research goal into the correct NMDC resource, with the gotcha to expect
metadata:
  type: reference
  provenance: audit synthesis
  tenant: nmdc, kbase
  databases: [nmdc.metadata, nmdc.results, nmdc.ncbi_biosamples, nmdc.ref_data, kbase.nmdc_arkin, kbase.nmdc_mags, kbase.nmdc_neon]
  currency: "2026-07-10"
  authority: nmdc_context_audit project
related: [nmdc-label-is-overloaded, nmdc-tenant-inventory, nmdc-data-outside-nmdc-tenant, nmdc-prior-project-usage, nmdc-completeness-and-currency]
---

# Choosing the right NMDC resource

Start from your goal, not from the name. Pick the row, use the resource, expect the gotcha.

| I want… | Use | Not | Expect / gotcha |
|---|---|---|---|
| **NMDC biosample/study metadata** (environmental context, sample provenance) | `nmdc.metadata` (`biosample_set`, `study_set`) | `nmdc.ncbi_biosamples` (that's NCBI) | 16,640 biosamples; `*_associated_studies` joins on `parent_id` |
| **NMDC functional/taxonomic annotation** (KEGG, EC, GTDB, CheckM) | `nmdc.results` | `kbase.nmdc_arkin` if you need the *raw* NMDC pipeline output | `annotation_kegg_orthology` is 1.83B rows — filter first |
| **Metabolomics / lipidomics / proteomics / NOM, embeddings, inferred traits** | `kbase.nmdc_arkin` | `nmdc.*` (no embeddings/traits upstream) | file_id≠sample_id; STRING numerics; bridge via `omics_files_table` — see [[nmdc-arkin-derived-product]] |
| **NMDC-derived MAGs / genome catalog** | `kbase.nmdc_mags` (`mag_catalog`, 62,346) | `kbase.nmdc_neon` (NEON MAGs) | freshest resource (2026-07-02) |
| **NEON-site metagenomes** (ecological monitoring, weather covariates) | `kbase.nmdc_neon` | anything labeled "NMDC" for attribution | attribute to **NEON/NSF**, not NMDC |
| **Universe-scale environmental metadata / ENV-triads across all of NCBI** | `nmdc.ncbi_biosamples` (`env_triads_flattened`, harmonized attrs) | `nmdc.metadata` (only 16.6k NMDC samples) | NCBI mirror; stale (2026-03-09); 51.7M samples |
| **Pfam family names for annotation joins** | `nmdc.ref_data.pfam_terms` | — | it's Pfam, cite Pfam/InterPro |
| **Cross-database NMDC × pangenome analysis** | `kbase.nmdc_arkin` taxonomy × `kbase.ke_pangenome` | — | precedents: `phb_granule_ecology`, `prophage_ecology` |

## Three rules that prevent most mistakes
1. **"nmdc tenant" ≠ "all NMDC" and ≠ "only NMDC."** It excludes `kbase.nmdc_*`
   ([[nmdc-data-outside-nmdc-tenant]]) and includes NCBI/Pfam
   ([[ncbi-biosamples-not-nmdc]], [[nmdc-ref-data-is-pfam]]).
2. **Check currency before you trust freshness.** Snapshots range days→months
   ([[nmdc-completeness-and-currency]]).
3. **Search both `nmdc.*` and `kbase.nmdc_*`, and skip the cruft** (aliases, tests,
   phantom, broken — [[nmdc-naming-aliases-and-cruft]]).

## Fastest start
Match your goal above → open the linked resource page for scale/pitfalls → find a worked
precedent in [[nmdc-prior-project-usage]]. That is the "get to the optimal data in the
first minutes" path this knowledge base exists to provide.

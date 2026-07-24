---
name: ncbi-biosamples-not-nmdc
description: nmdc.ncbi_biosamples is a harvested NCBI BioSample mirror, not NMDC-generated data
metadata:
  type: reference
  provenance: NCBI (harvested, re-hosted under nmdc tenant)
  tenant: nmdc
  databases: [nmdc.ncbi_biosamples]
  currency: "2026-03-09"
  authority: ncbi.nlm.nih.gov/biosample
related: [nmdc-tenant-inventory, nmdc-label-is-overloaded, nmdc-value-added-by-berdl, nmdc-choosing-the-right-resource]
---

# `nmdc.ncbi_biosamples` is NCBI, not NMDC

Despite living in the `nmdc` tenant, this database is a **harvest of NCBI BioSample/SRA**,
not NMDC program output. It is the largest "NMDC"-labeled resource by far and the one most
likely to be misattributed.

## Scale (why it dominates)
- `biosamples_attributes` — **756,112,544** rows (attribute key/value pairs)
- `biosamples_flattened` — **51,711,888** biosamples
- `sra_biosamples_bioprojects` — **33,738,101** biosample↔bioproject links
- `bioprojects_flattened` — **1,034,221** bioprojects
- Plus harmonization/stats tables: `attribute_harmonized_pairings`,
  `harmonized_name_usage_stats`, `harmonized_name_dimensional_stats`,
  `env_triads_flattened`, `measurement_evidence_percentages`, `unit_assertion_counts`,
  `ncbi_attributes_flattened`, `ncbi_packages_flattened`, `content_pairs_aggregated`, …

## Currency
Latest Iceberg snapshot **2026-03-09** — the **stalest** NMDC-labeled resource, ~2–4
months behind the genuine NMDC tables (2026-05-20) and the MAG catalogs (2026-07-02). NCBI
BioSample grows continuously, so treat this as a **fixed point-in-time mirror**, not live.

## When to use it (and when not)
- **Use** for: universe-scale environmental metadata, ENV-triad (`env_triads_flattened`)
  and harmonized-attribute analyses, linking sequences to bioprojects, or as a broad
  denominator for "how common is context X across all of NCBI."
- **Do NOT use** it when you mean NMDC-curated microbiome samples — that is
  [[nmdc-tenant-inventory]] `nmdc.metadata.biosample_set` (16,640 samples, NMDC data model).
- The **value BERDL added** here is the attribute *harmonization* layer (mapping messy NCBI
  attribute names to controlled names, ENV-triad extraction) — see
  [[nmdc-value-added-by-berdl]]. That harmonization is the reason to prefer this mirror
  over raw NCBI dumps.

## Provenance summary
Origin: **NCBI** (public BioSample/SRA). Re-host: `nmdc` tenant, owner `tgu2`. This is a
class-2 ("external re-host") resource in [[nmdc-label-is-overloaded]].

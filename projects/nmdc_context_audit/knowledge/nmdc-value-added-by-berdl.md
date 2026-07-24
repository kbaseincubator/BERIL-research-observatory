---
name: nmdc-value-added-by-berdl
description: What BERDL adds on top of upstream NMDC/NCBI — flattening, harmonization, embeddings, Iceberg, cross-joins
metadata:
  type: reference
  provenance: audit synthesis
  tenant: nmdc, kbase
  databases: [nmdc.metadata, nmdc.ncbi_biosamples, kbase.nmdc_arkin]
  currency: "2026-07-10"
  authority: nmdc_context_audit project
related: [nmdc-tenant-inventory, ncbi-biosamples-not-nmdc, nmdc-arkin-derived-product, nmdc-choosing-the-right-resource]
---

# What value BERDL adds over upstream

A fair audit asks not just "is this really NMDC?" but "why use the BERDL copy instead of
the upstream source?" The answer differs per resource — and is itself a reason the "NMDC"
label hides value.

## 1. Relational flattening (`nmdc.metadata`)
Upstream NMDC is a LinkML/MongoDB document model. BERDL flattens it into **49 queryable
Iceberg `*_set` tables** with explicit child/association tables
(`workflow_execution_set_has_input`, `study_set_associated_dois`, …). This makes SQL joins
and column-level filtering possible without parsing nested JSON.

## 2. Attribute harmonization (`nmdc.ncbi_biosamples`)
The biggest added value on the NCBI side: messy free-text NCBI attribute names are mapped
to controlled names (`attribute_harmonized_pairings`, `harmonized_name_usage_stats`,
`harmonized_name_dimensional_stats`), ENV-triads are extracted (`env_triads_flattened`),
and measurement units/values are parsed with evidence stats
(`measurement_evidence_percentages`, `unit_assertion_counts`). This is what makes a
51.7M-sample NCBI mirror analytically usable rather than a raw dump. See
[[ncbi-biosamples-not-nmdc]].

## 3. Enrichment & embeddings (`kbase.nmdc_arkin`)
The Arkin-lab layer adds representations that don't exist upstream at all: per-entity
**embeddings** (taxonomy/trait/abiotic/biochemical, plus taxon-rank rollups), **inferred
traits** (`trait_unified`), **unified cross-ontology annotation hierarchies** (COG/EC/GO/
KEGG/MetaCyc flattened + graph forms), and a **cross-omics join fabric**
(`omics_files_table`, `sample_file_lookup`). See [[nmdc-arkin-derived-product]].

## 4. Lakehouse mechanics (all resources)
Iceberg gives cheap metadata `COUNT(*)`, per-table **snapshot history** (the only currency
signal available — see [[nmdc-completeness-and-currency]]), time-travel, and dual catalog
exposure. It also enables **cross-database joins** to the rest of BERDL (e.g. NMDC taxonomy
× `kbase.ke_pangenome`), which is the basis of most prior NMDC projects
([[nmdc-prior-project-usage]]).

## The catch
None of this value is announced at discovery time (no table `Comment`, no schema doc, no
skill module). The added value and the provenance caveats are **the same missing context** —
which is why this knowledge base pairs them.

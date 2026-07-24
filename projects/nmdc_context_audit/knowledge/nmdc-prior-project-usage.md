---
name: nmdc-prior-project-usage
description: Which prior BERIL projects used which NMDC resource — a reuse and precedent map
metadata:
  type: reference
  provenance: audit synthesis (repo project scan)
  tenant: nmdc, kbase
  databases: [kbase.nmdc_arkin, nmdc.metadata, nmdc.results, nmdc.ncbi_biosamples]
  currency: "2026-07-10"
  authority: nmdc_context_audit project
related: [nmdc-arkin-derived-product, nmdc-tenant-inventory, nmdc-choosing-the-right-resource]
---

# Prior BERIL project usage of NMDC data

A precedent map: which resource each prior project used, so a new user can find worked
examples (and inherited pitfalls) fast. Notably, **almost all prior work used
`kbase.nmdc_arkin`**, not the genuine `nmdc` tenant — reinforcing that the Arkin derivative
is the de-facto "NMDC" people reach for.

**Read this as a default-choice skew, not a catalogue of documented errors.** 8 of the 10
projects below reached for `kbase.nmdc_arkin`; this shows what users gravitate to and is a
reasonable *proxy* for the label's confusability, but it is not proof that any of them chose
a wrong table for their question. No prior project's notebooks record an explicit
wrong-resource misstep — the evidence here is about defaults and discoverability, which is
why the [[nmdc-label-is-overloaded]] causal claim is framed as inferred, not observed.

| Project | Resource(s) used | Note |
|---|---|---|
| `nmdc_community_metabolic_ecology` | `kbase.nmdc_arkin` (`taxonomy_features`, `kraken_gold`, `centrifuge_gold`, `metabolomics_gold`, `abiotic_features`, `study_table`) × `kbase.ke_pangenome` | Authored most `nmdc_arkin` pitfalls/discoveries |
| `harvard_forest_warming` | `nmdc.metadata` + `nmdc.results` **only** (no arkin) | Genuine-NMDC exemplar; study `nmdc:sty-11-8ws97026` |
| `enigma_carbon_census_1` | `kbase.nmdc_arkin` (`covstats_taxonomy_rollup`) + `nmdc.metadata` | Global environmental atlas; species→genus rollup pitfall |
| `phb_granule_ecology` | `kbase.nmdc_arkin` + `nmdc.ncbi_biosamples` × `kbase.ke_pangenome` | NB `04_nmdc_metagenomic_analysis.ipynb` |
| `prophage_ecology` | `kbase.nmdc_arkin` × `kbase.ke_pangenome` | NB `05_nmdc_environmental_analysis.ipynb` |
| `snipe_defense_system` | `kbase.nmdc_arkin` (+ phagefoundry, kbase) | |
| `functional_dark_matter` | `kbase.nmdc_arkin` + `nmdc.results` | Lab-field concordance |
| `plant_microbiome_ecotypes` | `kbase.nmdc_arkin` | Complementarity NB |
| `gene_function_ecological_agora` | `kbase.nmdc_arkin` | Feasibility audit |
| `euk_in_prok_correlates` | NMDC read-based taxonomy (`nmdc:wfrbt-*`, `nmdc:bsm-*`, `nmdc:sty-*`) | Orphan scaffold; exact source table undocumented |

## Reading the map
- **Want a genuine-NMDC precedent?** → `harvard_forest_warming` (metadata + results).
- **Want an omics/embedding/trait precedent?** → `nmdc_community_metabolic_ecology`
  (the richest `kbase.nmdc_arkin` worked example, and its pitfalls in `docs/pitfalls.md`).
- **Cross-database NMDC × pangenome?** → `phb_granule_ecology`, `prophage_ecology`.

See [[nmdc-choosing-the-right-resource]] to translate a goal into a resource + precedent.

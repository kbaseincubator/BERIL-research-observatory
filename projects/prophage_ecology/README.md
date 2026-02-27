# Prophage Gene Modules and Terminase-Defined Lineages Across Bacterial Phylogeny and Environmental Gradients

## Research Question

How are prophage gene modules and terminase-defined prophage lineages distributed across bacterial phylogeny and environmental gradients, and which modules/lineages show environmental enrichment exceeding phylogenetic expectation?

## Status

Complete — see [Report](REPORT.md) for findings.

## Overview

This project quantifies the distribution of seven operationally defined prophage gene modules (packaging, head morphogenesis, tail, lysis, integration, lysogenic regulation, anti-defense) and TerL-based prophage lineages across 27,690 bacterial species in the BERDL pangenome. Using eggNOG functional annotations (Pfam domains, KEGG KOs, descriptions) as proxies for prophage marker genes, we map module prevalence across GTDB taxonomy and environmental gradients. Variance partitioning (PERMANOVA) separates phylogenetic from environmental effects, controlling for genome size and assembly completeness. Null models with constrained permutations identify modules and lineages with environment enrichment beyond phylogenetic expectation. NMDC metagenomic samples provide independent environmental validation via taxonomy-based inference.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `kbase_ke_pangenome` | `eggnog_mapper_annotations`, `gene_cluster`, `gene`, `gene_genecluster_junction`, `genome`, `gtdb_species_clade`, `gtdb_taxonomy_r214v1`, `gtdb_metadata`, `pangenome`, `ncbi_env`, `alphaearth_embeddings_all_years` | Prophage gene identification, taxonomy, environment metadata |
| `nmdc_arkin` | `taxonomy_features`, `taxonomy_dim`, `abiotic_features`, `study_table` | Metagenomic cross-validation |

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory

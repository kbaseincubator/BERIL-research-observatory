# Aromatic Catabolism Support Network in ADP1

## Research Question
Why does aromatic catabolism in *Acinetobacter baylyi* ADP1 require Complex I (NADH dehydrogenase), iron acquisition, and PQQ biosynthesis when growth on other carbon sources does not?

## Status
In Progress — research plan created, awaiting analysis.

## Overview
The prior project (`adp1_deletion_phenotypes`) identified 51 genes with quinate-specific growth defects. Unexpectedly, these include not just the 6 core aromatic degradation genes but also 10 Complex I subunits, 3 iron acquisition genes, 2 PQQ biosynthesis genes, and 6 transcriptional regulators. This project investigates whether these form a coherent metabolic dependency network — Complex I for NADH reoxidation during aromatic catabolism, iron for the Fe²⁺-dependent ring-cleavage dioxygenase, and PQQ for the quinoprotein quinate dehydrogenase — or whether the quinate-specificity is an artifact. Uses FBA predictions across 230 carbon sources (including 9 aromatics), genomic organization, co-fitness networks, and cross-species validation via the Fitness Browser.

## Data Sources
- **User-provided**: `user_data/berdl_tables.db` — SQLite database with ADP1 genome features, FBA predictions (230 conditions), gene-reaction mappings (from `projects/acinetobacter_adp1_explorer/`)
- **Prior project**: `projects/adp1_deletion_phenotypes/` — condition-specific gene analysis identifying the 51 quinate-specific genes
- **BERDL**: `kescience_fitnessbrowser` for cross-species aromatic fitness data; `kbase_ke_pangenome` for conservation analysis

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)), Lawrence Berkeley National Laboratory

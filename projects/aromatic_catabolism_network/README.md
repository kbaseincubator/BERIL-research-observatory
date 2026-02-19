# Aromatic Catabolism Support Network in ADP1

## Research Question
Why does aromatic catabolism in *Acinetobacter baylyi* ADP1 require Complex I (NADH dehydrogenase), iron acquisition, and PQQ biosynthesis when growth on other carbon sources does not?

## Status
Complete — aromatic catabolism requires a 51-gene support network dominated by Complex I (21 genes, 41%), with iron acquisition and PQQ biosynthesis addressing specific cofactor requirements. Cross-species data shows the dependency is on high-NADH-flux substrates, not aromatics exclusively. See [Report](REPORT.md) for findings.

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

### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- The ADP1 database file at `user_data/berdl_tables.db` (136 MB, symlinked from `projects/acinetobacter_adp1_explorer/user_data/`)
- Quinate-specific gene list from `projects/adp1_deletion_phenotypes/`

### Running the Pipeline
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_metabolic_dependencies.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_genomic_organization.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_cofitness_network.ipynb
jupyter nbconvert --to notebook --execute --inplace 04_cross_species.ipynb
```

All notebooks run locally (no Spark required).

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)), Lawrence Berkeley National Laboratory

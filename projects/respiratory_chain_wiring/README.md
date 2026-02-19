# Condition-Specific Respiratory Chain Wiring in ADP1

## Research Question
How is *Acinetobacter baylyi* ADP1's branched respiratory chain wired across carbon sources — which NADH dehydrogenases and terminal oxidases are required for which substrates?

## Status
Complete — each carbon source uses a qualitatively different respiratory configuration. Complex I's quinate-specificity is explained by NADH flux rate (concentrated TCA burst from ring cleavage), not total NADH yield. See [Report](REPORT.md) for findings.

## Overview
ADP1 has a branched respiratory chain with multiple NADH dehydrogenases (Complex I, NDH-2, ACIAD3522) and terminal oxidases (cytochrome bo, cytochrome bd). The prior project (`aromatic_catabolism_network`) showed that Complex I is specifically essential for aromatic catabolism but dispensable on glucose, while ACIAD3522 is acetate-lethal but quinate-fine. This project systematically maps the condition-dependent wiring of the entire respiratory chain using the 8-condition growth matrix, FBA stoichiometry, and cross-species Fitness Browser data. The central hypothesis: Complex I's quinate-specificity reflects the high NADH flux from aromatic catabolism exceeding NDH-2's reoxidation capacity.

## Data Sources
- **User-provided**: `user_data/berdl_tables.db` — SQLite database with ADP1 genome features, FBA predictions (230 conditions), gene-reaction mappings
- **Prior projects**: `projects/aromatic_catabolism_network/` (Complex I support network), `projects/adp1_deletion_phenotypes/` (condition-specific growth data)
- **BERDL**: `kescience_fitnessbrowser` for cross-species respiratory chain fitness data; `kbase_ke_pangenome` for NDH-2/Complex I co-occurrence

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction

### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- The ADP1 database file at `user_data/berdl_tables.db` (136 MB)
- BERDL Spark access for NB04 (JupyterHub or local Spark Connect)

### Running the Pipeline
```bash
pip install -r requirements.txt
cd notebooks/
# NB01-03 run locally
jupyter nbconvert --to notebook --execute --inplace 01_respiratory_chain_map.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_ndh2_indirect.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_stoichiometry.ipynb
# NB04 requires BERDL Spark (run on JupyterHub)
jupyter nbconvert --to notebook --execute --inplace 04_cross_species_respiratory.ipynb
```

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)), Lawrence Berkeley National Laboratory

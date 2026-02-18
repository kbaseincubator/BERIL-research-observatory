# Acinetobacter baylyi ADP1 Data Explorer

## Research Question
What is the scope and structure of a comprehensive ADP1 database, and how do its annotations, metabolic models, and phenotype data intersect with BERDL collections (pangenome, biochemistry, fitness, PhageFoundry)?

## Status
Completed — all 5 connection types to BERDL validated (100% genome, 91% reaction, 100% compound, 100% cluster mapping). Multi-omics exploration of essentiality, fitness, proteomics, and metabolic model complete. See [Report](REPORT.md) for findings.

## Overview
This project explores a user-provided SQLite database (`berdl_tables.db`, 136 MB) containing comprehensive data for *Acinetobacter baylyi* ADP1 and related genomes. The database includes 15 tables spanning genome features (5,852 genes with 51 annotation columns), metabolic model reactions (17,984), gene-phenotype associations (239K), essentiality classifications, proteomics, mutant growth data, and a 14-genome pangenome (43K features).

The goal is to (1) characterize what's in the database, (2) identify connection points to BERDL collections, and (3) demonstrate the `user_data/` convention for bringing external data into observatory projects.

## Data Sources
- **User-provided**: `user_data/berdl_tables.db` — SQLite database with ADP1 genome, annotations, metabolic model, phenotypes, essentiality, proteomics, and pangenome data
- `kbase_ke_pangenome` — Pangenome data for Acinetobacter species (pangenome cluster IDs in user DB)
- `kbase_msd_biochemistry` — ModelSEED reactions (reaction IDs in user DB)
- `kescience_fitnessbrowser` — Fitness data if ADP1 or relatives have RB-TnSeq data
- `phagefoundry_acinetobacter_genome_browser` — Acinetobacter genome browser (891 strains)
- `kbase_uniref50/90/100` — UniRef protein clusters (UniRef IDs in user DB)

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — exploration approach and connection mapping strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction
### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- The ADP1 database file at `user_data/berdl_tables.db` (136 MB, not in git — download from lakehouse after upload)

### Running the Pipeline
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_database_exploration.ipynb
```

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy

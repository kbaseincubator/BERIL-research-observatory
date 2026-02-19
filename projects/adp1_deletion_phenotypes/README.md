# ADP1 Deletion Collection Phenotype Analysis

## Research Question
What is the condition-dependent structure of gene essentiality in *Acinetobacter baylyi* ADP1, as revealed by the de Berardinis single-gene deletion collection grown on 8 carbon sources?

## Status
Complete — the phenotype landscape is a continuum with ~5 independent dimensions; 625 condition-specific genes map precisely to expected metabolic pathways. See [Report](REPORT.md) for findings.

## Overview
The de Berardinis et al. (2008) complete deletion collection for ADP1 provides growth ratio measurements for ~2,350 single-gene deletion mutants across 8 carbon sources (acetate, asparagine, butanediol, glucarate, glucose, lactate, quinate, urea). This project performs a phenotype-first analysis of the 2,034×8 complete growth matrix to discover: (1) which carbon sources produce redundant vs independent essentiality profiles, (2) functionally coherent gene modules with correlated growth defects, (3) genes with condition-specific importance, and (4) patterns in TnSeq-classified genes that lack deletion mutant data. No FBA — the prior project (adp1_triple_essentiality) showed FBA class adds no predictive value for growth defects among dispensable genes (p=0.63).

## Data Sources
- **User-provided**: `user_data/berdl_tables.db` — SQLite database (136 MB) with ADP1 genome features, growth data, TnSeq essentiality, and annotations (symlinked from `projects/acinetobacter_adp1_explorer/user_data/`)
- **Prior project**: `projects/adp1_triple_essentiality/` — FBA-TnSeq-growth concordance analysis

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction

### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- The ADP1 database file at `user_data/berdl_tables.db` (136 MB, not in git — symlinked from `projects/acinetobacter_adp1_explorer/user_data/`)

### Running the Pipeline
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_data_extraction.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_condition_structure.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_gene_modules.ipynb
jupyter nbconvert --to notebook --execute --inplace 04_condition_specific.ipynb
jupyter nbconvert --to notebook --execute --inplace 05_tnseq_gap.ipynb
```

All notebooks run locally (no Spark required). Data source: `kbase_ke_pangenome` (pangenome core/accessory annotations cross-referenced via the SQLite database).

## Authors
- Paramvir Dehal (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)), Lawrence Berkeley National Laboratory

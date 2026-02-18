# ADP1 Triple Essentiality Concordance

## Research Question
Among genes that TnSeq says are dispensable in *Acinetobacter baylyi* ADP1, does FBA correctly predict which ones have growth defects? Can direct mutant growth rate measurements serve as an independent axis to evaluate where computational (FBA) and genetic (TnSeq) methods agree or disagree?

## Status
Complete — FBA essentiality class does not predict growth defects among TnSeq-dispensable genes (chi-squared p=0.63). See [Report](REPORT.md) for findings.

## Overview
The `acinetobacter_adp1_explorer` project found 74% concordance between FBA and TnSeq essentiality for ADP1, but never incorporated the mutant growth rate data as a third axis. This project adds mutant growth rates on 8 carbon sources as an independent experimental measure.

**Key constraint**: All 478 triple-covered genes (having TnSeq + FBA + growth data) are TnSeq-dispensable on minimal media. This is biologically expected — TnSeq-essential genes have no viable deletion mutants, so they cannot have growth rate measurements. The analysis therefore asks: among dispensable genes, does FBA correctly predict which ones matter for growth?

The `gene_phenotypes` table provides per-carbon-source FBA flux predictions, enabling condition-matched comparisons for 6 of 8 carbon sources (glucose, acetate, asparagine, butanediol, glucarate, lactate).

## Data Sources
- **User-provided**: `user_data/berdl_tables.db` — SQLite database with ADP1 genome features, metabolic model, phenotypes, and pangenome data (from `acinetobacter_adp1_explorer`)
  - `genome_features` table: 5,852 genes, 51 columns (TnSeq, FBA class, mutant growth x 8 conditions, COG, KO, pangenome)
  - `gene_phenotypes` table: 239K rows — per-gene per-carbon-source FBA flux predictions
- **Cluster mapping**: `data/cluster_id_mapping.csv` — 4,891 BERDL-to-ADP1 pangenome cluster ID mappings (from `acinetobacter_adp1_explorer`)

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, analysis plan
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction
### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- The ADP1 database file at `user_data/berdl_tables.db` (136 MB, not in git)

### Running the Pipeline
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_data_assembly.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_concordance_analysis.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_discordant_characterization.ipynb
```

## Key References
- Durot M et al. (2008) "Iterative reconstruction of a global metabolic model of Acinetobacter baylyi ADP1 using high-throughput growth phenotype and gene essentiality data." *BMC Systems Biology* 2:85.
- de Berardinis V et al. (2008) "A complete collection of single-gene deletion mutants of Acinetobacter baylyi ADP1." *Molecular Systems Biology* 4:174.

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy

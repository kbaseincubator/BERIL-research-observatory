# Research Plan: ADP1 Triple Essentiality Concordance

## Research Question
Among genes that TnSeq says are dispensable in *Acinetobacter baylyi* ADP1, does FBA correctly predict which ones have growth defects? Can mutant growth rate measurements break ties between computational and genetic essentiality predictions?

## Hypothesis
FBA-essential genes that are TnSeq-dispensable should show measurable growth defects in mutant growth assays, while FBA-blocked (zero flux) genes should not. If this holds, growth measurements validate FBA predictions even when TnSeq disagrees. If it doesn't, the discordance reveals systematic biases in one or both computational/genetic approaches.

## Literature Context
- Durot et al. (2008) built an iterative FBA model for ADP1 using growth phenotype data, achieving ~75% concordance with TnSeq essentiality.
- de Berardinis et al. (2008) created a complete single-gene deletion mutant collection for ADP1, enabling systematic growth measurements.
- The prior `acinetobacter_adp1_explorer` project established 74% FBA-TnSeq concordance on 866 genes with both measurements, with 89 FBA-essential/TnSeq-dispensable discordant genes.

## Approach

### Phase 1: Data Assembly (NB01)
1. Load `genome_features` from SQLite — extract TnSeq essentiality, FBA class, mutant growth rates, annotations
2. Define the triple-covered gene set: genes with TnSeq + FBA + any growth measurement (~478 genes)
3. Define growth defect thresholds per condition using condition-specific distributions
4. Create binary "growth_important" flags per condition
5. Load `gene_phenotypes` for per-condition FBA flux predictions, join to triple table
6. Join pangenome annotations via `cluster_id_mapping.csv`
7. Save assembled table to `data/triple_gene_table.csv`

### Phase 2: Concordance Analysis (NB02)
1. **Triple concordance matrix**: Cross-tabulate FBA class x growth defect status; compute Cohen's kappa for FBA-essential vs growth-defect agreement
2. **Growth as tie-breaker**: For FBA-TnSeq discordant genes, test whether mutants show growth defects (FBA-essential/TnSeq-dispensable) or grow normally (FBA-blocked/TnSeq-dispensable)
3. **Condition-specificity**: For 6 matched conditions, scatter FBA flux vs growth rate; compute Spearman correlations; identify which conditions show best/worst agreement

### Phase 3: Discordant Characterization (NB03)
1. Define discordance classes (FBA-essential+growth-normal, FBA-blocked+growth-defect, etc.)
2. COG category enrichment via Fisher's exact test
3. Pangenome status (core vs accessory) of discordant genes
4. Functional annotation clustering by KEGG pathway and RAST function

## Analysis Plan

### Notebook 1: Data Assembly
- **Goal**: Build the triple-covered gene table with all annotations
- **Expected output**: `data/triple_gene_table.csv` (~478 rows, ~30 columns)

### Notebook 2: Concordance Analysis
- **Goal**: Quantify agreement/disagreement across three essentiality measures
- **Expected output**: Concordance statistics, contingency tables, condition-specific correlations, violin/box plots

### Notebook 3: Discordant Gene Characterization
- **Goal**: Characterize what makes discordant genes different
- **Expected output**: COG enrichment tables, pangenome status comparisons, pathway heatmaps

## Expected Outcomes
- Confirmation or refinement of the 74% FBA-TnSeq concordance in the triple-covered subset
- Quantification of how often growth measurements support FBA predictions vs TnSeq calls
- Identification of carbon-source-specific patterns in FBA-growth agreement
- Functional characterization of systematically discordant genes

## Revision History
- **v1** (2026-02-18): Initial plan

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy

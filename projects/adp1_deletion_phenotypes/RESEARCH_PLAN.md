# Research Plan: ADP1 Deletion Collection Phenotype Analysis

## Research Question
What is the condition-dependent structure of gene essentiality in *Acinetobacter baylyi* ADP1, as revealed by the de Berardinis single-gene deletion collection grown on 8 carbon sources?

## Hypothesis
- **H0**: Growth defect profiles across 8 carbon sources are independent — each condition affects a random subset of genes, and no coherent functional modules emerge from the growth matrix.
- **H1**: Carbon source growth profiles reveal structured condition dependencies and functionally coherent gene modules, reflecting the metabolic architecture of ADP1.

## Literature Context
- **de Berardinis et al. (2008)** constructed the complete deletion collection for ADP1: 2,594 viable single-gene deletions out of 3,093 attempted (499 candidate essentials). They reported systematic phenotyping on multiple carbon sources but focused primarily on essentiality statistics and agreement with *E. coli* Keio collection data.
- **Durot et al. (2008)** used the deletion collection to iteratively refine an FBA model of ADP1, reporting ~75% concordance between FBA essentiality predictions and experimental data.
- **Stuani et al. (2014)** used multi-omics (transcriptomics, metabolomics, proteomics) to characterize ADP1's response to quinate vs succinate as sole carbon source, revealing novel metabolic features including amino acid biosynthesis pathway restructuring.
- **Fischer et al. (2008)** characterized carbon catabolite repression of aromatic degradation pathways in ADP1, showing coordinate regulation of multiple catabolic operons.
- **Nichols et al. (2011)** demonstrated that chemical genomic profiling of *E. coli* reveals a "phenotypic landscape" — correlated sensitivity profiles define functional modules that extend beyond operon and pathway boundaries.
- **Guzman et al. (2018)** proposed reframing gene essentiality as "adaptive flexibility," arguing that gene importance is condition-dependent and continuous. Our growth matrix across 8 conditions is ideal for testing this framework.
- **Prior project (adp1_triple_essentiality)**: FBA class does not predict growth defects among dispensable genes (p=0.63). Aromatic degradation genes drive most FBA-growth discordance (OR=9.7). 70% of genes show condition-specific growth defects. This project picks up where that one left off — focusing on the phenotype matrix itself, without FBA.

## Approach

### Data Overview

The analysis centers on the `genome_features` table from `user_data/berdl_tables.db`:
- **5,852 total genes** in the ADP1 genome
- **2,350 genes** with growth data on any of 8 carbon sources
- **2,034 genes** with growth data on all 8 conditions (the "complete matrix")
- **3,405 genes** with TnSeq essentiality calls (minimal media)
- **2,226 genes** with both growth data and TnSeq classification

Growth conditions and their mean growth ratios (mutant/WT):
| Condition | n genes | Mean | Interpretation |
|-----------|---------|------|----------------|
| Urea | 2,312 | 0.409 | Most deletions impair growth — urea is demanding |
| Acetate | 2,279 | 0.562 | Many defects — acetate metabolism constrained |
| Butanediol | 2,300 | 0.644 | Moderate defects |
| Asparagine | 2,312 | 0.798 | Moderate |
| Lactate | 2,316 | 0.810 | Moderate |
| Glucarate | 2,222 | 1.254 | Few defects — robust growth |
| Glucose | 2,251 | 1.298 | Few defects — robust, many bypass routes |
| Quinate | 2,310 | 1.355 | Few defects — robust on aromatic carbon |

The conditions naturally split into two groups: "demanding" (urea, acetate, butanediol) where many genes are needed, and "robust" (glucose, quinate, glucarate) where most deletions have no effect.

### Aim 1: Condition Structure
**Goal**: Characterize which carbon sources produce redundant vs independent gene essentiality profiles.

**Methods**:
- Pairwise Pearson and Spearman correlations of the 8 conditions across 2,034 shared genes
- PCA of the 2,034×8 growth matrix (conditions as variables): how many principal components capture most variance?
- Hierarchical clustering of conditions (Ward's method, 1-correlation distance)
- Compare condition groupings to carbon source biochemistry: do conditions cluster by metabolic entry point (glycolysis vs TCA vs aromatic degradation)?

**Expected output**: Condition correlation heatmap, PCA biplot, condition dendrogram, interpretation of condition clusters.

### Aim 2: Gene Modules
**Goal**: Identify groups of genes with correlated growth defect profiles across conditions.

**Methods**:
- Z-score normalize growth values per condition (center and scale to account for different mean levels)
- Hierarchical clustering of the 2,034 genes by their 8-condition growth profiles (Ward's method, Euclidean distance on z-scores)
- Determine optimal number of clusters via silhouette analysis and gap statistic
- Alternative: NMF decomposition of the (shifted non-negative) growth matrix to find latent factors
- Functional enrichment of each module: RAST functions (100% coverage), KO terms (57% coverage), PFAM domains (95% coverage). Apply Benjamini-Hochberg FDR correction (q<0.05) for multiple testing across all module × category tests. Use `pd.notna()` checks before string operations on annotation columns with partial coverage.
- Compare modules to known ADP1 pathway structure: do modules correspond to operons, regulons, or metabolic pathways?

**Expected output**: Clustered heatmap, module membership table with functional annotations, enrichment analysis per module.

### Aim 3: Condition-Specific Genes
**Goal**: For each condition, identify genes whose importance is specific to that carbon source.

**Methods**:
- Per-gene z-score profile across 8 conditions: genes with one extreme value and 7 near-zero values are condition-specific
- Condition specificity score: max(|z_i|) - mean(|z_j|) for j != i
- For each condition, extract top 20-50 condition-specific genes
- Functional annotation of condition-specific gene sets: RAST categories, KEGG pathways
- Focus on quinate (aromatic degradation) and urea (nitrogen metabolism) as biologically distinctive conditions
- Cross-reference with prior project: are the aromatic degradation genes identified in adp1_triple_essentiality condition-specific for quinate?

**Expected output**: Condition-specificity rankings, annotated gene lists per condition, pathway mapping of condition-specific genes.

### Aim 4: TnSeq Coverage Gap Analysis
**Goal**: Among the 1,179 TnSeq-classified genes that lack deletion mutant growth data, characterize which genes are missing and why.

**Methods**:
- Partition the 1,179 genes by TnSeq class:
  - 499 essential (expected — no viable deletion mutant)
  - 370 dispensable (unexpected — should have been in the collection)
  - 310 uncertain
- For the 370 dispensable genes without growth data: compare functional annotations (RAST, KO, PFAM) to the 2,223 dispensable genes WITH growth data
- Test whether the missing dispensable genes are enriched for specific functions, genomic locations, or gene lengths. Apply Benjamini-Hochberg FDR correction for enrichment tests.
- Check whether the 310 uncertain genes show properties intermediate between essential and dispensable

**Expected output**: Functional comparison table, enrichment tests, characterization of the "missing dispensable" gene set.

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `genome_features` (SQLite) | Growth matrix, TnSeq, annotations | 5,852 | Full scan (small table) |
| `gene_phenotypes` (SQLite) | Per-condition FBA flux predictions — may be used in Aim 3 to compare condition-specific genes with FBA predictions | 239,584 | Filter by ADP1 genome_id |

### Key Queries
1. **Growth matrix extraction**:
```sql
SELECT feature_id, old_locus_tag, rast_function, ko, pfam,
       essentiality_minimal, essentiality_lb,
       pangenome_cluster_id, pangenome_is_core,
       mutant_growth_acetate, mutant_growth_asparagine,
       mutant_growth_butanediol, mutant_growth_glucarate,
       mutant_growth_glucose, mutant_growth_lactate,
       mutant_growth_quinate, mutant_growth_urea
FROM genome_features
```

2. **Complete matrix subset**:
```sql
SELECT * FROM (query above)
WHERE mutant_growth_acetate IS NOT NULL
  AND mutant_growth_asparagine IS NOT NULL
  AND mutant_growth_butanediol IS NOT NULL
  AND mutant_growth_glucarate IS NOT NULL
  AND mutant_growth_glucose IS NOT NULL
  AND mutant_growth_lactate IS NOT NULL
  AND mutant_growth_quinate IS NOT NULL
  AND mutant_growth_urea IS NOT NULL
```

### Performance Plan
- **Execution environment**: Local machine (no Spark required)
- **Tier**: Local Python (SQLite + pandas/scipy/sklearn)
- **Estimated complexity**: Simple — all data fits in memory (<10K rows)
- **Known pitfalls**:
  - Use `pd.BooleanDtype()` for boolean columns with NaN
  - COG column has COG IDs (e.g., COG0189), not functional category letters — use RAST for enrichment
  - `cluster_id_mapping.csv` has duplicate `adp1_cluster_id` — deduplicate before joining
  - Growth values are ratios, not absolute rates — z-score normalization per condition is essential

## Analysis Plan

### Notebook 1: Data Extraction and Quality Assessment
- **Goal**: Load growth matrix from SQLite, assess completeness, validate distributions
- **Expected output**: `data/growth_matrix_complete.csv` (2,034×8), `data/growth_matrix_all.csv` (2,350 genes), summary statistics, distribution plots per condition

### Notebook 2: Condition Structure Analysis
- **Goal**: PCA, correlation analysis, hierarchical clustering of conditions
- **Expected output**: Condition correlation heatmap, PCA biplot, condition dendrogram, variance explained plot. Figures saved to `figures/`.

### Notebook 3: Gene Module Discovery
- **Goal**: Cluster genes by growth profile, identify functional modules
- **Expected output**: `data/gene_modules.csv` (gene-to-module assignments), clustered heatmap, module enrichment table, `data/module_enrichment.csv`

### Notebook 4: Condition-Specific Genes
- **Goal**: Identify condition-specific genes, compute specificity scores, annotate per condition
- **Expected output**: `data/condition_specific_genes.csv`, annotated gene lists per condition, pathway mapping

### Notebook 5: TnSeq Coverage Gap Analysis
- **Goal**: Characterize TnSeq coverage gaps — which dispensable genes lack growth data and why
- **Expected output**: `data/tnseq_gap_analysis.csv`, functional comparison of missing vs present dispensable genes

## Expected Outcomes
- **If H1 supported**: Carbon source growth profiles cluster into biochemically meaningful groups (e.g., organic acids vs sugars vs aromatic compounds). Gene modules correspond to known metabolic pathways and regulatory units. Condition-specific genes reveal the metabolic specializations of ADP1.
- **If H0 not rejected**: Growth profiles are noisy and lack structure — the deletion collection growth assay may lack resolution to distinguish condition-dependent effects. This would suggest that single-timepoint growth ratios capture too little information about gene function.
- **Potential confounders**:
  - Growth ratio measurements may have different dynamic ranges per condition (the mean growth ratios vary from 0.41 to 1.36)
  - The 2,034 complete-matrix genes are a biased subset (only dispensable genes with viable deletion mutants)
  - Some "condition-specific" effects may reflect assay noise rather than biology

## Revision History
- **v2** (2026-02-19): Addressed reviewer feedback — added BH-FDR correction to enrichment methods, specified execution environment, clarified gene_phenotypes table role, split NB04 into two notebooks (condition-specific genes + TnSeq gap analysis)
- **v1** (2026-02-19): Initial plan

## Authors
- Paramvir Dehal (ORCID: 0000-0001-5810-2497), Lawrence Berkeley National Laboratory

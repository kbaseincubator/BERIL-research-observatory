# Research Plan — per_ko_metal_associations

**Question:** Across the entire functional genome of environmental MAGs, are there individual KEGG orthologs whose presence or copy number is significantly associated with bioavailable metal concentrations at the MAG's sampling site?

**Status:** Scaffold complete. NB00–NB03 pending execution.

**All analyses in this project are exploratory.** Results are hypothesis-generating, not hypothesis-confirming.

---

## Motivation

P1 (`comprehensive_metal_ecology`) found a significant genus-level PGLS association between metal-gene density and niche breadth using a curated 730-KO list. P4 (`metagenomic_environment_prediction`) found that per-Mb metal-gene density does not predict local metal mobility at the individual MAG level (H1/H2 not supported; soil geochemistry dominates).

These results leave open a broader question: is the failure of the curated KO set a failure of the curated list, or a failure of the signal itself? If the curated KOs are not the right genes to look at, a genome-wide screen may find genes—metal-related or not—that do carry an environmental metal association.

This project performs that screen.

---

## Pre-specified decisions

### Dataset selection and priority
- **Primary:** MGnify MAGs — larger coverage, well-annotated, established coordinates via `final_mags_geospatial_traits.csv`
- **Secondary:** SPIRE MAGs — smaller coverage (~6,270 in internal eggnog table), used for replication only
- If SPIRE annotation coverage is < 500 MAGs after quality filtering and CSU join, report as insufficient for replication and skip NB02 SPIRE results

### KO prevalence filter
- Retain KOs present in ≥ max(10, floor(0.01 × n_mags)) MAGs
- Applied independently to each dataset
- "Present" = binary (at least 1 gene annotated with that KO in the MAG)

### Metal targets
PF1_Cu, PF1_Zn, PF1_Pb, PF1_Cr, PF1_As, PF1_Cd, PF1_Hg — all seven. Tests run for each KO × metal combination independently.

### Primary statistical test
Logistic regression: `KO_present ~ PF1_metal + log(genome_size_mb) + phylum`
- PF1_metal is the predictor of interest; genome_size_mb and phylum are covariates
- Report coefficient β for PF1_metal, SE, p-value (Wald test), odds ratio

### Secondary tests (for validation only, not for multiple-testing correction)
- Spearman ρ between KO copy number and PF1_metal (non-parametric, no covariates)
- GAM `KO_present ~ s(PF1_metal) + log(genome_size_mb) + phylum` — compare ΔAIC to linear model; flag KOs where ΔAIC > 2

### Multiple testing correction
Benjamini-Hochberg FDR across all KO × metal tests within each dataset. Primary FDR threshold: q < 0.05. Secondary threshold: q < 0.10 (to assess enrichment sensitivity).

### Cross-dataset comparison
For directional consistency (H2):
- Merge MGnify and SPIRE results on KO × metal
- Spearman ρ between β_MGnify and β_SPIRE (all KOs present in both, regardless of FDR status)
- H2 threshold: ρ > 0.2

### Enrichment test (H3)
- Compare fraction of curated-list KOs (730-KO metal list) among FDR-significant associations vs. all tested KOs
- Fisher's exact test; p < 0.05

### Reporting null results
If H1 fails (< 20 FDR-significant KO-metal pairs), report the distribution of p-values and discuss whether the null is consistent with no signal vs. underpowered. Do not inflate claims.

---

## Spatial join

CSU metal mobility fractions are joined to each MAG by finding the nearest CSU grid cell within ≤ 50 km (BallTree haversine), consistent with P1, P4, and microbeatlas_metal_ecology. Use `env_utils.batch_csu_join()` from `metagenomic_environment_prediction/scripts/`.

---

## KO matrix format

Long-format (tidy) Parquet: one row per (genome_id, ko_id).
Columns: `genome_id`, `ko_id`, `count` (copy number), `present` (binary).
Wide-format matrices for modelling are built in-memory in NB01 via pivot.

---

## Negative results policy

All hypotheses will be reported as tested regardless of outcome. A null result (H1 not supported) is scientifically meaningful: it would suggest that the metal bioavailability signal, if it exists, is not detectable at the KO level with current sample sizes and that future work requires either larger sample sizes or different feature engineering. This will be stated explicitly in the interpretation, not buried.

---

## Timeline

Pending NB00 execution (Spark data pull may take 15-30 min for MGnify gene table). NB01 is the compute-intensive step (up to thousands of logistic regressions). NB02 and NB03 are fast post-hoc analyses.

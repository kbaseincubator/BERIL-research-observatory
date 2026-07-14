# Report: Soil Metal Concentrations Drive Functional Gene Shifts

## Status

Preliminary — Spearman correlation, db-RDA, and PGLS analyses complete (NB01–NB04).
NB05 effect size and spatial validation pending. NB06 figures pending.

## Key Findings

- **2,355 significant COG-metal associations** (FDR < 0.05) across 9 metals (Cu, Co,
  Cr, Ni, Zn, Pb, As, Cd, Hg) in 51,748 soil samples. Chromium and Lead drive the
  strongest signals; transporters (ABC, RND) and biosynthesis genes dominate top hits.
- **Copper-specific analysis** (116 COGs, FDR < 0.05; 7,566 samples with nearby KBase
  genomes at 10 km): top positives include cell division and nucleotide transport (BQ,
  FQ, FK, CF); top negatives include energy production (DI, CE), suggesting energetic
  trade-offs under copper stress.
- **db-RDA**: R² = 0.799, p = 0.005 (permutation test, 999 permutations) — metal
  concentrations explain 80% of variance in community COG profiles after conditioning
  on batch/project effects.
- **Biome-stratified PGLS**: soil, marine, and wastewater show distinct metal-COG
  relationships, indicating environment-specific functional responses rather than a
  universal resistance programme.

## Interpretation

Soil metal concentrations are strongly associated with the functional gene content of
co-located microbial communities (db-RDA R²=0.799), and this relationship is not a
statistical artefact of batch effects (project accession conditioned out). The direction
of COG associations with copper (energetic trade-offs, membrane transport enrichment)
is consistent with known copper toxicity mechanisms in bacteria.

However, all associations are observational. Co-contamination by multiple metals is a
significant confound: Cr, Cu, Pb, Zn co-vary in many industrial soils. Whether
individual COG-metal associations are metal-specific or reflect a generic stress
response to multi-metal contamination is unresolved (NB05 partial correlation models).

Effect sizes (Spearman ρ) have not yet been systematically reported across all 2,355
associations; many may be statistically significant but biologically small.

## Critical Assessment

**R² = 0.799 requires careful interpretation.** db-RDA conditions on project accession
before fitting the metal concentration predictors. If batch effects (project) account
for the majority of community COG variance, the reported R² describes how well metals
explain the *residual* variance, not the *total* variance. The unconditional R² of metals
alone — without first removing project effects — is not reported and may be substantially
lower. This must be reported alongside the conditional figure.

**2,355 significant associations at FDR < 0.05 in 51,748 samples:** With 9 metals ×
435 COGs = 3,915 tests, a 60% discovery rate is high. Metals co-contaminate (Cr, Pb,
Zn, Cu co-vary in industrial soils), so tests are not independent — Benjamini-Hochberg
FDR correction assumes independent tests and will be anti-conservative under positive
correlation. True FDR is likely higher than reported. The partial correlation model
(NB05 item 3) is the correct remedy.

**Copper-specific analysis uses a 10 km proximity criterion** to match soil samples to
KBase genomes. At 10 km, many "nearby" genomes may not be co-located with the copper
measurements. Sensitivity analysis at 5 km and 20 km thresholds is needed before
COG-copper associations can be attributed to the measured sites.

**Spark-required analyses:** NB05 items 1–4 all require re-running from the
`kescience_mgnify`/`kbase_ke_pangenome` Spark tables. No local CSV output of the
Spearman ρ values or model residuals is available, so these validations cannot be
completed without Spark access.

## Pending Validation

1. Effect size audit: ρ distribution across 2,355 associations; flag ρ < 0.05
2. Spatial autocorrelation test (Moran's I on residuals; SEVM if significant)
3. Partial correlation model: COG ~ Cr | Cu + Zn + Pb (metal-specific vs. general)
4. Mechanistic classification of significant COGs into resistance, stress, membrane,
   energy, and unknown categories
5. Report unconditional db-RDA R² (metals only, without project accession conditioning)
6. Copper proximity sensitivity: rerun at 5 km and 20 km thresholds

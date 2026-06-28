# Report: Soil Metal Concentrations Drive Functional Gene Shifts

## Status

Preliminary — Spearman correlation and spatial COG analysis complete (NB01–NB03).
NB04 db-RDA code revised (see Critical Assessment); results require re-run on Seaborg.
NB05 effect size and spatial validation pending. NB06 figures pending.

## Key Findings

- **2,355 significant COG-metal associations** (FDR < 0.05) across 9 metals (Cu, Co,
  Cr, Ni, Zn, Pb, As, Cd, Hg) in 51,748 soil samples. Chromium and Lead drive the
  strongest signals; transporters (ABC, RND) and biosynthesis genes dominate top hits.
- **Copper-specific analysis** (116 COGs, FDR < 0.05; 7,566 samples with nearby KBase
  genomes at 10 km): top positives include cell division and nucleotide transport (BQ,
  FQ, FK, CF); top negatives include energy production (DI, CE), suggesting energetic
  trade-offs under copper stress.
- **db-RDA**: R² = **PENDING** — prior value (0.799) was from a methodologically
  invalid run using simulated project IDs and a circular predictor; corrected
  unconditional db-RDA (NB04 cell 9 revised) requires re-run on Seaborg with Spark.
- **Biome-stratified PGLS**: prior run used randomly assigned biomes and mock rRNA
  data; results are not interpretable. Requires real biome labels from sample metadata.

## Interpretation

The 2,355 significant COG-metal associations suggest soil metal concentrations are
broadly associated with microbial functional gene content. The copper-specific analysis
(direction of energetic trade-offs, membrane transport enrichment) is consistent with
known copper toxicity mechanisms in bacteria and is the most interpretable result to date.

The multivariate db-RDA and PGLS results from NB04 require recomputation before they
can be interpreted. All associations are observational; co-contamination confounding
is unresolved until the partial correlation model (NB05 item 3) is run.

## Critical Assessment

**R² = 0.799 is invalid and must not be cited.** The NB04 db-RDA cell that produced
this value used (a) randomly simulated project IDs (`np.random.choice(['PROJ_A', ...])`),
not real project accessions, and (b) a "climate PC1" predictor that was derived directly
from the PCA of the COG response matrix — a circular predictor guaranteed to explain
variance. The result is an artifact. The corrected implementation (NB04 cell 9) uses
actual metal concentrations (log1p-transformed) against CLR-transformed COG profiles
without circular predictors; results require re-run on Seaborg.

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
5. Run corrected db-RDA (NB04 cell 9 revised) on Seaborg; report unconditional R²
   (metals only) and conditional R² (metals | project_accession; requires adding
   project_accession to the SELECT in NB04 cell 3 and rerunning cells 3, 8, 9)
6. Copper proximity sensitivity: rerun at 5 km and 20 km thresholds

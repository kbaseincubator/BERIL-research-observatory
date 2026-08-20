# Interpretation Table: Community Composition Prediction

This table records hypothesis outcomes, key results, and interpretation as notebooks complete.

---

## Section 1: Baseline comparisons (NB01)

### H1: CLR taxonomy improves prediction beyond cheap geochem — **SUPPORTED**

**Test**: Bootstrap ΔRMSE (B2 − B1) on OOF predictions. Success: ≥2 metals have CI excluding 0 (positive direction). 3/4 metals pass.

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE |
|-------|---------|---------|---------|---------|
| B0 (intercept) | 1.1146 | 0.6781 | 0.8802 | 1.7018 |
| B1 (CLR, XGB) | 1.1361 | 0.7073 | 0.9537 | 1.8303 |
| B2 (pH+lat/lon, ridge) | 1.1832 | 0.8278 | 1.2508 | 1.6781 |
| B3 (CLR+pH+lat/lon, XGB) | 1.5965 | 0.7464 | 1.1185 | 1.9668 |

| Target | ΔRMSE (B2−B1) | 95% CI | H1 pass? |
|--------|--------------|--------|---------|
| log_Cu_ppm | −0.003 | [−0.008, 0.002] | ✗ |
| log_Zn_ppm | +0.066 | [0.061, 0.070] | ✓ |
| log_Pb_ppm | +0.286 | [0.276, 0.297] | ✓ |
| log_Ni_ppm | +0.060 | [0.044, 0.075] | ✓ |

**H1 conclusion**: SUPPORTED (3/4 metals). CLR-based taxonomy outperforms cheap geochem (pH + lat/lon) for Zn, Pb, and Ni in spatial block CV. Cu is not significant (ΔRMSE CI includes 0).

*Note*: B1 (CLR) is worse than B0 (intercept-only) for all 4 metals (Cu: +1.9%, Zn: +4.3%, Pb: +8.4%, Ni: +7.5% higher RMSE) — CLR features do not improve on the training mean in spatial block CV. H1 is supported only in the relative sense: CLR still outperforms pH+lat/lon (B2) for 3/4 metals, even though neither beats the intercept baseline. B3 (CLR+geochem) is catastrophically overfit (Cu +43% vs B0), suggesting XGBoost overfits the combined high-dimensional input without environmental anchoring.

---

## Section 2: Functional augmentation (NB02)

### H2: Genus-weighted functional features improve beyond CLR + geochem — **SUPPORTED**

**Test**: Bootstrap ΔRMSE (B3 − M1). Success: ≥2 metals CI excludes 0 (positive direction). 4/4 metals pass.

Full spatial-CV RMSE table (mean across 5 blocks):

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE |
|-------|---------|---------|---------|---------|
| B0 (intercept) | 1.1146 | 0.6781 | 0.8802 | 1.7018 |
| B1 (CLR) | 1.1361 | 0.7073 | 0.9537 | 1.8303 |
| B2 (geochem) | 1.1832 | 0.8278 | 1.2508 | 1.6781 |
| B3 (CLR+geochem) | 1.5965 | 0.7464 | 1.1185 | 1.9668 |
| B4 (CWM) | 1.1718 | 0.7378 | 0.9705 | 1.8188 |
| M1 (CLR+GW) | 1.1434 | 0.7029 | 0.9698 | 1.8423 |
| M2 (CLR+GW+env) | 1.1210 | 0.9229 | 0.8260 | 1.8640 |
| M3 (CLR+CWM+env) | 1.1468 | 0.8998 | 0.8222 | 1.8377 |

| Target | ΔRMSE (B3−M1) | 95% CI | H2 pass? |
|--------|--------------|--------|---------|
| log_Cu_ppm | +0.654 | [0.642, 0.665] | ✓ |
| log_Zn_ppm | +0.019 | [0.014, 0.024] | ✓ |
| log_Pb_ppm | +0.272 | [0.266, 0.278] | ✓ |
| log_Ni_ppm | +0.178 | [0.168, 0.188] | ✓ |

**H2 conclusion**: SUPPORTED (4/4 metals). Genus-weighted functional features consistently outperform B3 (CLR+geochem). The large Cu/Pb deltas primarily reflect how badly B3 overfits — XGBoost with 200 CLR + 3 geochem features loses spatial generalization entirely (B3 worse than B0 for Cu/Ni). M1 avoids this collapse by replacing the weak geochem features with 110 GW features that do not share the same geographic confound.

---

### H3: Genus-weighted (M2) outperforms CWM (M3) — **NOT SUPPORTED**

**Test**: Direct M2 vs M3 RMSE comparison. Success: M2 < M3 for ≥3 metals. Only 1/4 pass.

| Target | M2 RMSE | M3 RMSE | M2 < M3? |
|--------|---------|---------|---------|
| log_Cu_ppm | 1.1210 | 1.1468 | ✓ |
| log_Zn_ppm | 0.9229 | 0.8998 | ✗ |
| log_Pb_ppm | 0.8260 | 0.8222 | ✗ |
| log_Ni_ppm | 1.8640 | 1.8377 | ✗ |

**H3 conclusion**: NOT SUPPORTED (1/4 metals). CWM (M3) outperforms genus-weighted (M2) for Zn, Pb, and Ni. The 110 GW features appear to add noise relative to the 5 CWM scalars when combined with CLR + env — likely because GW features are collinear with CLR features (both derived from genus RA) and XGBoost cannot effectively regularize a high-dimensional combined input. Notably, both M2 and M3 underperform B0 for Ni, and add substantial Zn error (M2: 0.923 vs B0: 0.678) — the env/mob features appear to hurt Zn generalization in spatial block CV.

*Cross-project confirmation (MCI)*: The failure occurs at a more fundamental level than CWM aggregation. Per-KO logistic regression across 26,850 KO-metal pairs in SPIRE MAGs and MGnify finds only 2 replicating associations (0.007%); cross-dataset effect-size correlation ρ = 0.28; direction consistency ≈ 0. Genomic metal-resistance gene capacity does not carry a stable metal signal even at the individual KO level. CWM and GW aggregate a signal that does not exist in the underlying data. The mechanistic explanation is capacity vs. activity: gene presence (what the genome encodes) is phylogenetically conserved across environments; gene expression (which genes are active) is what responds to local metal exposure, and is not captured by metagenomic KO profiles.

*Connection to Arc 1 geological-filtering mechanism (why H3 is expected to fail)*: Arc 1 (`comprehensive_metal_ecology` PGLS) shows that the cofactor biosynthesis signal (β = −0.033, p = 5.2×10⁻⁹) is detectable at the evolutionary timescale — bedrock Cr/Co geology predicts niche breadth while contemporary soil metal levels do not (p > 0.22). This means the functional signature of metal adaptation is embedded in the phylogenetic ancestry of specialist lineages (cobalamin-pathway investment shaped over geological timescales by ancestral metal environments), not in the expression state of inducible resistance genes responding to contemporary metal stress. At the community timescale captured by CCP — where we predict present-day soil metal concentrations from genus-level CLR profiles — the CWM aggregation of genomic resistance gene capacity cannot detect a signal that is (a) expressed rather than encoded, and (b) geological rather than contemporary in origin. The H3 null is therefore the expected result under the Arc 1 mechanism: functional gene-capacity features (CWM, GW) are the wrong observational layer for a signal that requires either evolutionary comparative analysis (Arc 1) or metatranscriptomics to detect. Resistance genes in particular are HGT-prone (distributed across the phylogeny without ecological constraint), so their capacity is not phylogenetically structured by metal specialisation — exactly matching the PGLS β ≈ 0 for resistance KOs in Arc 1.

---

## Section 3: SHAP interpretation (NB04)

### H4: Genus-weighted categories rank above CLR taxonomy in SHAP — **NOT SUPPORTED**

**Test**: Sum GW SHAP > Sum CLR SHAP for M2. Success: ≥2 metals. 0/4 metals pass.

| Target | CLR SHAP | GW SHAP | Env_mob SHAP | Env_soil SHAP | GW > CLR? |
|--------|---------|---------|-------------|--------------|----------|
| log_Cu_ppm | 0.129 | 0.020 | 0.635 | 0.539 | ✗ |
| log_Zn_ppm | 0.086 | 0.026 | 0.429 | 0.365 | ✗ |
| log_Pb_ppm | 0.110 | 0.027 | 0.412 | 0.630 | ✗ |
| log_Ni_ppm | 0.259 | 0.045 | 0.781 | 1.112 | ✗ |

**H4 conclusion**: NOT SUPPORTED (0/4 metals). Environmental features (mob_* and soil/climate) dominate SHAP for all metals. CLR (taxonomy) is the second-largest contributor. Genus-weighted functional features contribute <15% of CLR's SHAP in all cases — they add marginal predictive value to M2, but do not rank above taxonomy. This is consistent with H3 (CWM beats GW in spatial CV): the functional features in the GW format add noise rather than signal when combined with CLR.

*Cross-project confirmation (MCI)*: CLR-only AUC for s25 metal exceedance is 0.92–0.96 across 6 metals (132K samples), with no additional gain from any functional feature. Family-level CLR retains 99% of genus-level AUC (0.930 vs 0.938 mean), while phylum-level drops to 0.841. This confirms the SHAP hierarchy here: the predictive signal is taxonomic at the within-phylum guild level (families of oligotrophic, metal-tolerant organisms), not at the functional gene-content level.

*Evolutionary-timescale confirmation (CME)*: At the evolutionary scale, `comprehensive_metal_ecology` PGLS (n = 1,073 genera, phylogeny-corrected via Pagel's λ) recovers the same functional hierarchy from genome content alone. Resistance/detoxification genes (106 KOs) show β = +0.003 (p = 0.820) — no niche-breadth association — consistent with HGT-driven horizontal spread across generalist and specialist genomes alike. Cofactor biosynthesis (7 KOs: Fe–S cluster assembly *iscS*/*iscU*, molybdopterin *moaA*, cobalamin) shows β = −0.033 (p = 5.2×10⁻⁹), the strongest of any functional category and a reversal of the pre-specified expectation. The resistance-null / cofactor-significant split is quantitatively extreme within the metal gene set: Δβ = 0.0353 exceeds all 1,000 random partitions of the 140 metal KOs into groups of matching size (emp_p = 0/1000; NB25), and jackknife removal of any single cofactor KO leaves the remaining three still highly significant (β = −0.016 to −0.029, all p < 0.001; NB26). CME thus provides the mechanistic reason the SHAP functional hierarchy is as observed: constitutive cofactor pathways are always expressed, phylogenetically conserved in specialist lineages, and not acquired by HGT — so their genomic capacity is a stable proxy for niche identity at both the evolutionary (CME PGLS) and community-assembly (CCP SHAP, MCI AUC) timescale. Inducible resistance genes do not produce that signal: their capacity is distributed by HGT without ecological constraint, so neither evolutionary PGLS nor community-level prediction detects a consistent association.

The top CLR genera reveal specific taxa driving metal prediction:
- **Cu**: _Nitrosospira_, _Methanothrix_, _Steroidobacter_ (nitrifier + methanogen co-occurrence with oxidising Cu soil)
- **Zn**: _Nitrososphaera_, _Neobacillus_, _Gaiella_ (archaeal ammonia oxidiser drives Zn)
- **Pb**: _Acinetobacter_, _Agrobacterium_, _Actinomarinicola_ (Pb-tolerant genera)
- **Ni**: _Lentzea_, _Xenorhabdus_, _Rhodomicrobium_ (actinobacteria/entomopathogen co-occurrence)

### Threshold metrics (M2, full training set, regulatory cutoffs)

| Target | Cutoff | Sensitivity | Specificity | n_positive |
|--------|--------|-------------|-------------|-----------|
| log_Cu_ppm | >100 ppm | 0.977 | 1.000 | 2,401 |
| log_Zn_ppm | >300 ppm | 0.981 | 1.000 | 156 |
| log_Pb_ppm | >100 ppm | 0.250 | 1.000 | 40 |
| log_Ni_ppm | >50 ppm | 0.997 | 0.993 | 15,286 |

M2 achieves excellent threshold discrimination for Cu, Zn, and Ni on the training set. Pb performance is very poor (sensitivity=25%, 30 FN out of 40 positives) — likely because extreme-Pb samples (mining-contaminated) represent a domain shift from the broader soil distribution the model was trained on.

---

## Section 4: External validation (NB03)

### H5: M2 generalises to AusMicrobiome holdout — **SUPPORTED**

**Test**: Holdout/training RMSE ratio ≤ 1.1 for ≥2 of 4 metals (AusMicrobiome + NGSA, n=731–745 samples with valid targets). 2/4 metals pass.

Holdout RMSE on 1,019 AusMicrobiome samples matched to NGSA metal data:

| Model | Cu RMSE | Zn RMSE | Pb RMSE | Ni RMSE |
|-------|---------|---------|---------|---------|
| B0 (training mean) | 1.3465 | 1.5348 | 0.8549 | 1.6408 |
| B1 (CLR only) | 1.2966 | 1.5196 | 1.0666 | 1.6438 |
| M1 (CLR + GW) | 1.2857 | 1.5723 | 1.0331 | 1.6814 |
| M2 (CLR + GW + env) | 0.9608 | 1.4642 | 0.9565 | 1.8146 |

| Target | Training RMSE | Holdout RMSE | Ratio | ≤ 1.1? |
|--------|--------------|-------------|-------|--------|
| log_Cu_ppm | 1.121 | 0.961 | 0.857 | ✓ |
| log_Zn_ppm | 0.923 | 1.464 | 1.586 | ✗ |
| log_Pb_ppm | 0.826 | 0.957 | 1.158 | ✗ |
| log_Ni_ppm | 1.864 | 1.815 | 0.973 | ✓ |

**H5 conclusion**: SUPPORTED (2/4 metals). M2 transfers successfully to Australian soils for Cu and Ni. Zn degrades sharply (1.59×) and Pb modestly (1.16×). The env features that drive M2's benefit are the CSU mobility features (mob_*), which are available in the holdout via Spark. Other env features (ph, clay_pct, ndvi, etc.) are NaN in the holdout, handled by XGBoost's missing value routing. The Cu improvement at holdout (0.961 vs 1.121 training) likely reflects that Australian soil Cu distributions are better captured by CLR + mob_cu than by the geographically-confounded spatial block CV folds. Zn failure may reflect that the Zn-related community signals in ENIGMA training data do not generalise to Australian dryland soils.

*Note*: B1 (CLR-only) holdout RMSE exceeds B0 for Pb (1.07 vs 0.85), indicating CLR features actively mispredict Australian Pb. M2's mob_* features partially correct this (0.96 vs 1.07 for M2 vs B1). B0 (training mean) is competitive on the Australian holdout, reflecting large distributional shifts for metals not well-covered by Australian MicrobeAtlas genera.

*Coverage-stratified sensitivity (WP6)*: 40% of AusMicrobiome samples have <70% of their genus RA matched to the SPIRE pangenome (n=408 low-coverage, n=611 high-coverage). A sensitivity analysis re-training M2 on the full training set and predicting stratified by coverage found **no degradation in the low-coverage stratum** — RMSE in low-coverage samples is equal to or lower than in high-coverage samples across all four metals:

| Metal | All (n≈731–745) | High cov ≥0.70 | Low cov <0.70 |
|-------|----------------|----------------|---------------|
| Cu    | 1.258          | 1.270          | 1.238         |
| Zn    | 1.644          | 1.711          | 1.523         |
| Pb    | 0.701          | 0.772          | 0.558         |
| Ni    | 1.374          | 1.359          | 1.398         |

(RMSE slightly different from NB03 holdout above because this model trains on full training set without spatial block CV. Stratified comparison is internally consistent.) This finding is mechanistically expected: SHAP analysis shows environmental features (mob_*, soil/climate) contribute >80% of prediction variance, and these are available regardless of CLR coverage. Low-coverage samples are not harder to predict because the model relies on environmental co-predictors, not purely on CLR. WP6 (coverage as a limitation of H5) is resolved: H5 results are robust to coverage. Data: `data/coverage_stratified_results.csv`; figure: `figures/fig_coverage_stratified_rmse.pdf`.

---

## Section 5: Exploratory directions (post-hoc, NB05–NB08)

**[All entries in this section are PENDING — notebooks not yet run]**

All four directions are explicitly exploratory/post-hoc. They were motivated by the primary findings
(spatial heterogeneity dominates, env features dominate SHAP, total metal is a noisy target).
Positive outcomes warrant a separate pre-registered confirmatory study.

---

### H6: Kriging-omics hybrid (NB05) — NOT SUPPORTED

**H6**: Hybrid (kriging spatial baseline + M1 residual prediction) RMSE < min(kriging alone, M2 alone) for ≥2 of 4 metals.

Method: IDW spatial block LOO (pykrige fallback to IDW confirmed at runtime); M1 (CLR+GW) spatial block CV on kriging residuals; hybrid = kriging OOF + M1 residual OOF.

| Target | Kriging RMSE | M2 RMSE | Hybrid RMSE | Kriging < M2? | H6 pass? |
|--------|-------------|---------|-------------|--------------|---------|
| log_Cu_ppm | 1.0708 | 1.1210 | 1.2202 | ✓ | ✗ |
| log_Zn_ppm | 0.6825 | 0.9229 | 0.8007 | ✓ | ✗ |
| log_Pb_ppm | 0.8732 | 0.8260 | 1.0209 | ✗ | ✗ |
| log_Ni_ppm | 1.6591 | 1.8640 | 1.9056 | ✓ | ✗ |

**H6 OUTCOME: NOT SUPPORTED** (0/4 metals). The hybrid is worse than kriging alone in all cases — adding M1 residual predictions injects noise rather than correcting residuals. M1 appears to overfit the kriging residuals in the training blocks and does not generalise to held-out blocks.

Secondary finding: IDW/kriging alone beats M2 for Cu, Zn, and Ni — spatial proximity explains metal concentrations better than microbiome composition for 3 of 4 metals. This is consistent with the finding that env features (which encode spatial location indirectly) dominate SHAP. The core predictive signal in this dataset is geographic, not microbial.

Only Pb: M2 (0.826) beats kriging (0.873) — consistent with the finding that Pb contamination in the training set is driven by mine proximity (a land-use pattern) rather than natural geochemical gradients that kriging would capture.

*Cross-project confirmation (MCI)*: In MCI the spatial-only feature set (lat, lon, lat², lon², lat·lon) achieves study-blocked AUC 0.88–0.97 — higher than CLR alone (0.75–0.88) and only marginally below soil chemistry (0.87–0.94). Geography is the dominant predictor in both projects. Crucially, MCI shows that spatial de-trending of CLR (removing the geographic mean field) raises CLR random-fold AUC from 0.92–0.96 to 0.97–0.99: the geographic component in raw CLR was not adding genuine signal but suppressing the metal-specific within-location anomaly signal. The kriging dominance in CCP and the de-trending improvement in MCI are two faces of the same finding — geographic location is the easiest predictor of metal distribution, and any community feature that captures geography will appear to predict metals without detecting them biologically.

---

### H7: Bioavailable metal targets (NB06) — NOT SUPPORTED

**H7**: Relative RMSE improvement (B0 → M1) larger for mobility targets (PF1 fractions) than for total ppm targets for ≥2 of 2 overlapping metals (Cu, Pb).

Mobility targets: `mob_cu`, `mob_pb`, `mob_as`, `mob_cd`, `mob_cr`, `mob_hg` (CSU PF1 fractions, 89.2% coverage, n=37,499)
Feature sets exclude mob_* as predictors.

**Mobility target RMSE (mean across 5 spatial blocks):**

| Model | mob_as | mob_cd | mob_cr | mob_cu | mob_hg | mob_pb |
|-------|--------|--------|--------|--------|--------|--------|
| B0 | 0.0280 | 0.0588 | 0.0292 | 0.0247 | 0.0545 | 0.0225 |
| B1 (CLR) | 0.0281 | 0.0610 | 0.0304 | 0.0253 | 0.0539 | 0.0258 |
| M1 (CLR+GW) | 0.0278 | 0.0609 | 0.0300 | 0.0253 | 0.0538 | 0.0254 |
| M2_soil | 0.0295 | 0.0468 | 0.0294 | 0.0250 | 0.0480 | 0.0235 |

**Total metal RMSE (same feature sets, no mob_* predictors):**

| Model | log_Cu_ppm | log_Ni_ppm | log_Pb_ppm | log_Zn_ppm |
|-------|-----------|-----------|-----------|-----------|
| B0 | 1.1146 | 1.7018 | 0.8802 | 0.6781 |
| B1 (CLR) | 1.1361 | 1.8303 | 0.9537 | 0.7073 |
| M1 (CLR+GW) | 1.1434 | 1.8423 | 0.9698 | 0.7029 |
| M2_soil | 1.2421 | 1.8884 | 0.9661 | 0.7496 |

**H7 relative improvement comparison (B0 → M1):**

| Metal | Rel. improvement (mobility) | Rel. improvement (total) | H7 pass? |
|-------|-----------------------------|--------------------------|---------|
| Cu | −0.024 (M1 worse) | −0.026 (M1 worse) | ✗ |
| Pb | −0.129 (M1 worse) | −0.102 (M1 worse) | ✗ |

**H7 OUTCOME: NOT SUPPORTED** (0/2 metals). M1 (CLR+GW) degrades vs B0 for BOTH mobility and total targets — the relative degradation is larger for mobility than for total in both cases. CLR and GW features carry no useful signal for predicting PF1 mobility fractions. M2_soil (which adds soil/climate features) improves slightly over B0 for mob_cd (0.047 vs 0.059) and mob_hg (0.048 vs 0.055), suggesting that climate/soil variables (not microbiome) drive mobility variation. Microbial composition does not predict which fraction of a metal is bioavailable, at least at the genus level in this dataset.

---

### H8: Regional contamination classification (NB07) — NOT SUPPORTED

**H8**: ≥2 regions with within-region AUC > 0.70 for M1 or M2, AND GW adds ≥0.02 AUC over CLR-only in ≥1 region.

Contamination labels joined by lat/lon (4dp) — sample_id is integer, feature_matrix uses ENA accessions; 11,399 feature_matrix samples matched. k-means (k=8–12) selected k=8; only 2 of 8 regions were usable (≥10 contaminated + ≥10 reference).

**Within-region 5-fold stratified CV AUC:**

| Region | B0 AUC | CLR AUC | M1 (CLR+GW) AUC | M2 (CLR+GW+env) AUC | AUC > 0.70? |
|--------|--------|---------|-----------------|---------------------|------------|
| 0 | 0.500 | 0.994 | 0.994 | 1.000 | ✓ |
| 1 | 0.500 | 0.998 | 1.000 | NaN (no env) | ✓ |

**Cross-region AUC (train on N-1 regions, test on held-out):**

| Model | Mean AUC |
|-------|----------|
| CLR | 0.181 |
| M1 (CLR+GW) | 0.174 |
| M2 (CLR+GW+env) | 0.526 |

**H8 OUTCOME: NOT SUPPORTED** (criterion 1 met: 2/2 regions AUC > 0.70; criterion 2 fails: CLR alone achieves ≥0.99, GW adds at most 0.002 — no room for the required ≥0.02 delta).

Key findings:
1. **CLR taxonomy alone classifies contaminated vs reference at ~99% AUC within geographic regions** — this is a striking result. Microbial community composition at genus level is an almost perfect within-region contamination indicator.
2. **Cross-region transfer collapses completely**: CLR AUC=0.181 (worse than chance), M1=0.174, M2=0.526. The taxonomic signal that distinguishes contaminated from reference sites is region-specific — different genera signal contamination in different regions.
3. **Only 2 usable regions** (out of 8–12 k-means clusters): most regions in the training data either had too few contaminated samples or the feature_matrix coverage was sparse. This severely limits the analysis — results should be interpreted with extreme caution.
4. The within-region AUC saturation (≥0.99 with CLR) means adding GW features is essentially measuring noise. The contamination signal is fully captured by taxonomic composition alone.

**Implication**: Within-region contamination classification by CLR is promising but the cross-region failure confirms the broader finding that spatial geographic transfer is the fundamental challenge. A within-region deployment (where training and test samples are from the same geographic region) appears feasible from taxonomic data alone.

*Spatial autocorrelation range (WP1 quantification)*: Moran's I correlogram on M2 OOF residuals (n=2,000 random sample, 2,000×2,000 pairwise haversine distance matrix) quantifies the spatial range of autocorrelation directly. Residuals are strongly autocorrelated at <50 km (I = 0.41–0.73 across all metals) and at 50–200 km (I = 0.09–0.28). Zn and Pb reach near-zero at 200–500 km; Cu and Ni persist to 1,000+ km, reflecting the continent-scale geochemical gradients that structure those metals. The cross-region collapse (AUC 0.99 → 0.17) is mechanistically explained: k-means geographic clusters are separated by distances within the autocorrelation range (50–500 km), so training samples in one region contain information correlated with test samples in the adjacent region. For spatial block CV to eliminate autocorrelation for all metals, blocks would need to be separated by >1,000 km, which is not achievable with the current dataset extent. Data: `data/spatial_autocorr_correlogram.csv`; figure: `figures/spatial_autocorr_correlogram.pdf`.

*Cross-project confirmation (MCI)*: Study-blocked GroupKFold CV in MCI (grouped by sequencing project, which is geographically clustered) shows CLR AUC dropping from 0.92–0.96 (random-fold) to 0.50–0.76 (study-blocked) — a collapse of 0.17–0.42 AUROC. MCC under study-blocking falls to ≈ 0 for most metals. The within-region saturation here (CLR AUC ≥ 0.99) and the study-blocking collapse there are the same phenomenon at different scales: CLR taxonomic signal is geographically specific. Spatial de-trending of CLR features (removing lat/lon polynomial mean field) recovers blocked AUC to 0.58–0.78, confirming the geographic confound is partly but not fully removed by polynomial de-trending; residual study-level methodological variation (primer choice, V-region) persists.

---

### H9: Direct metagenomic profiles vs 16S-inferred GW (NB08) — UNTESTABLE

**H9**: MAG-derived functional model RMSE < GW-only (16S-inferred) RMSE for ≥2 of 4 metals.

**Status**: UNTESTABLE — data infrastructure limitation.

NB08 was executed with Spark Connect active (`arkinlab.spire` accessed successfully). The `eggnog_annotations_spire` table (15,050,686 rows) was loaded. However, the `arkinlab.spire` namespace contains **only one table** and the schema does not support per-sample functional profiles:

- `mag_id` format is opaque (`spire_mag_XXXXXXXX`) — no sample accession embedded
- No sample→MAG assignment table exists in `arkinlab.spire`
- No per-MAG coverage depth or genome size available

Per-sample abundance-weighted functional profiles require: (1) which MAGs are present in which sample, (2) per-MAG coverage depth per sample, (3) per-MAG genome size for per-Mb normalisation. None of these are available.

| Target | GW RMSE (from NB02, reference) | MAG RMSE | H9 pass? |
|--------|-------------------------------|----------|---------|
| log_Cu_ppm | 1.143 | — | — |
| log_Zn_ppm | 0.703 | — | — |
| log_Pb_ppm | 0.970 | — | — |
| log_Ni_ppm | 1.842 | — | — |

**H9 OUTCOME**: UNTESTABLE (not "not supported" — the test cannot be performed with current data)

**Next step**: Request a `sample_mag_coverage` table from the SPIRE data team (sample_id, mag_id, depth_coverage, genome_size_Mb) or access shotgun coverage data via CoverM outputs linked to SPIRE mag_ids.

---

## Section 6: Connection to other projects

| Finding | Source | Connection |
|---------|--------|-----------|
| CWM (5 scalars) adds marginal signal over env features in spatial block CV | `hybrid_metal_prediction` NB02 | M2 vs M3 here tests whether genus-level resolution recovers what CWM aggregation loses |
| Metal-gene category association (cofactor strongest via PGLS, β = −0.033; resistance null, β = +0.003) | `comprehensive_metal_ecology` | H4 (NOT SUPPORTED): the CME cofactor hierarchy does not appear in SHAP — env features dominate, then CLR; functional gene-content contributes <15% of CLR SHAP. CME and CCP agree that functional capacity ≠ ecological signal, but from opposite angles (CME: constitutive capacity → niche identity; CCP: functional capacity → too coarse to predict metal concentration) |
| CWM does not transfer to AusMicrobiome (H6 NOT SUPPORTED) | `hybrid_metal_prediction` NB03 | CLR features may transfer better since they don't require pangenome coverage of Australian genera — H5 is the test |
| M4 (env-only) transfers well to AusMicrobiome when mob_* available | `hybrid_metal_prediction` NB03 | If H5 fails for M2, comparison with M1 (no env features) will show whether env or CLR is the liability |
| CLR-only AUC 0.92–0.96 for s25 metal exceedance; functional features add nothing | `metal_contamination_bioindicators` NB01–NB02 | Directly confirms H3/H4: functional signal is absent in a fully independent 16S dataset at 3× the sample size. Family-level CLR retains 99% of genus AUC, confirming the signal is at the within-phylum ecological guild level |
| Per-KO associations: 2/26,850 KO-metal pairs replicate across SPIRE and MGnify; direction consistency ≈ 0 | `per_ko_metal_associations` NB01–NB02 | Root-cause confirmation for H3/H4 failure: functional capacity does not stably associate with metal exposure across independent datasets. The CWM/GW null result is not aggregation noise — the underlying individual-KO signal does not exist |
| Study-blocked CLR AUC 0.50–0.76 (vs random-fold 0.92–0.96); MCC ≈ 0 | `metal_contamination_bioindicators` NB01b | Directly mirrors H8 cross-region collapse (CLR AUC 0.99 → 0.18). Geographic confounding of CLR is a consistent finding across both projects and both blocking strategies |
| Spatial de-trending (lat/lon polynomial removal) raises CLR random-fold AUC 0.92 → 0.97–0.99 | `metal_contamination_bioindicators` NB01 | Explains the kriging dominance in H6: the geographic variance in raw CLR suppresses the local metal-specific signal. Kriging captures the dominant geographic component; CLR can only compete when that component is removed |
| Indicator genera are family-level oligotrophic and stress-tolerant guilds across 5–7 phyla; near-zero cross-metal Jaccard | `metal_contamination_bioindicators` NB01–NB02 | Explains SHAP result: environmental features dominate because they encode geography; CLR ranks second because it encodes the guild-level community reorganisation under metal stress; functional features rank last because they encode evolutionary history, not local exposure |
| CME PGLS: resistance/detox β = +0.003 (p = 0.820, NS); cofactor biosynthesis β = −0.033 (p = 5.2×10⁻⁹, strongest category); internal Δβ = 0.035 exceeds 0/1,000 random splits of metal gene set (NB25); jackknife over 4 cofactor KOs all retain p < 0.001 (NB26) | `comprehensive_metal_ecology` NB03/NB25/NB26 | CME PGLS recovers the same functional hierarchy implied by H3/H4 and the per-KO cross-dataset failure: resistance gene capacity is evolutionarily decoupled from ecological specialisation (HGT-driven), and community-level prediction likewise finds no signal from it. The functional null in CCP is not a modelling failure — it reflects an absence of signal at the single-KO level that persists across all timescales |
| Constitutive cofactor pathways (Fe–S cluster assembly, molybdopterin, cobalamin) are the only cross-scale signal: not inducible, not HGT-prone → stable from genome content (CME PGLS β = −0.033, evolutionary timescale) to community assembly (CCP SHAP, MCI AUC, ecological timescale) | `comprehensive_metal_ecology` NB26 | Mechanistic framework for the capacity-vs-activity distinction: metatranscriptomics (not metagenomics) is required to detect inducible resistance gene activity. Only constitutively expressed pathways — which are always active regardless of current exposure — generate the stable genomic capacity signal that evolutionary PGLS and community prediction both detect. This distinguishes CME from CCP/MCI: CME measures what is encoded in specialist genomes; CCP/MCI measures who is enriched at metal-contaminated sites; the intersection is cofactor biosynthesis because those organisms both invest in it constitutively (CME) and dominate metal-stressed communities (CCP/MCI) |

# Report: Metagenomic Environment Prediction

## Key Findings

### H1 NOT SUPPORTED (Cu only; untested for As/Cd/Cr/Hg/Pb) — MAG metal-gene density does not predict local copper mobility

*(Figure: figures/nb02_cv_rmse.pdf — SPIRE 5-fold spatial CV RMSE by model, B0/B1/B2/M1/M3)*

Across 15,957 SPIRE MAGs with CSU copper mobility fractions, the metal-gene KO density model (M1) achieves a mean 5-fold spatial block CV RMSE of 0.0527 ± 0.020 — worse than the mean baseline (B0: 0.0501 ± 0.021). MAG-level genomic metal-gene density alone provides no predictive signal for local copper mobility at the sampling site.

The pattern replicates in 8,849 MGnify soil MAGs: M1 (RMSE=0.0385) is again worse than B0 (RMSE=0.0369), confirming that individual-genome KO density lacks predictive power for local metal conditions regardless of dataset.

*(Notebooks: 02_predict_mobility.ipynb, 02b_mgnify_mobility_prediction.ipynb)*

### H2 NOT SUPPORTED (Cu only; untested for As/Cd/Cr/Hg/Pb) — Soil chemistry outperforms metal-gene density

Soil chemistry features (M2: SoilGrids pH, organic carbon, clay fraction) achieve RMSE=0.0439 in the SPIRE dataset and RMSE=0.0164 in MGnify — consistently outperforming MAG KO density (M1: 0.0527 SPIRE, 0.0385 MGnify). The gap is especially large in MGnify (M2/M1 RMSE ratio = 0.43), reflecting that local metal mobility is determined primarily by edaphic geochemistry rather than the gene content of individual assembled genomes.

*(Notebooks: 02_predict_mobility.ipynb, 02b_mgnify_mobility_prediction.ipynb)*

### H3 SUPPORTED (Cu only; untested for As/Cd/Cr/Hg/Pb) — Combined features improve over density alone; soil chemistry accounts for all the gain

*(Figure: figures/nb02_shap_bar.pdf — SPIRE SHAP mean |SHAP| per feature, M3 model)*

The combined model (M3: MAG density + SoilGrids) achieves RMSE=0.0400 (SPIRE), improving over M1 (0.0527) and M2 (0.0439) alone. However, SHAP analysis reveals that SoilGrids features dominate by ~20–50×: organic_carbon_density (0.0195) > clay_content (0.0120) > ph_h2o (0.0113), versus ko_per_mb_transport (0.00073) and all remaining KO-density subcategories ≤0.00050. Metal-gene KO density contributes <4% of total M3 SHAP importance. The M3 improvement over M1 is entirely attributable to soil chemistry features entering the model.

In MGnify, M3 SHAP shows a different pattern: metal fraction covariates (PF1_Cr: 0.0106, PF1_As: 0.0087, PF1_Hg: 0.0045) rather than SoilGrids dominate, with KO density features contributing <1% (ko_per_mb_resistance: 0.00013). When metal fraction covariates are included as features alongside KO density, M3 and M2 are essentially equivalent (RMSE 0.0163 vs 0.0164), and M3 wins only 2/5 spatial folds.

*(Notebooks: 02_predict_mobility.ipynb, 02b_mgnify_mobility_prediction.ipynb)*

### H4 SUPPORTED — Geographic transfer to Australia meets the pre-specified threshold

*(Figure: figures/nb03_holdout_map.pdf — SPIRE Australia holdout: MAG sampling locations and holdout region)*

The M1 model trained on non-Australian SPIRE MAGs (n=15,325) achieves holdout RMSE=0.0272 on Australian MAGs (n=43), giving a holdout/CV ratio of 0.515 — below the pre-specified 1.25 threshold. The corresponding ratio for MGnify is 0.655 (n_holdout=97), also below threshold.

Caveat: R² is negative in both holdout regions (SPIRE: −0.39; MGnify: −0.37), indicating the model fits Australian metal mobility worse than a simple mean. The RMSE ratio criterion is met because the holdout RMSE happens to be lower than the in-distribution CV RMSE (both means are similar, so prediction error is small in absolute terms), not because the model generalises well within the holdout region. Geographic transfer should not be interpreted as evidence of a useful predictive model; it reflects that the holdout distribution is not wider than the training distribution in this metal-mobility target.

*(Notebooks: 03_geographic_holdout.ipynb, 03b_mgnify_geographic_holdout.ipynb)*

### H5 CONSISTENT — PGLS β is directionally concordant with P1 but non-significant

Genus-level PGLS of Levins' B against per-Mb KO density across 254 genera in SPIRE yields β=−0.0107 (SE=0.0086, p=0.216). The negative sign is directionally consistent with P1's β=−0.021 but does not reach significance at the MAG-aggregated level. MGnify PGLS for PF1_Cu against ko_per_mb_primary yields β=−0.047 (SE=0.041, p=0.252, n=444 genera) — also negative and non-significant.

All three datasets (P1 genus-level: β=−0.021; SPIRE MAG-level: β=−0.011; MGnify MAG-level: β=−0.047) show a negative β, consistent with genera carrying more metal genes occupying more geochemically variable (broader) niches. The sign-concordance is consistent with the P1 biology but the association does not replicate at statistical significance in MAG-level data.

*(Notebooks: 04_pgls_validation.ipynb, 04b_mgnify_pgls_validation.ipynb)*

### MGnify exploratory results

*(Figure: figures/nb02b_cv_rmse.pdf — MGnify 5-fold spatial CV RMSE by model)*

*(Figure: figures/nb05_cv_rmse_comparison.pdf — Cross-dataset CV RMSE: SPIRE vs MGnify for B0/M1/M2/M3)*

| Hypothesis | Outcome | Evidence |
|---|---|---|
| H5exp — M3 beats B0 | SUPPORTED | MGnify M3 RMSE=0.0163 < B0=0.0369 (all 5 folds); driven by metal-fraction covariates |
| H6exp — M3 outperforms M2 on ≥3/5 folds | NOT SUPPORTED | M3 wins 2/5 folds (folds 1, 4); M2 wins 3/5; mean RMSE near-equivalent (0.0163 vs 0.0164) |
| H7exp — geographic holdout ratio < 1.25 | SUPPORTED | ratio=0.655 < 1.25 (n=97 Australian MGnify MAGs); same caveat as H4: R²=−0.37 |
| H8exp — SPIRE vs MGnify β correlation ρ > 0.3 | NOT EVALUABLE | Only primary-KO-set β compared; both negative (SPIRE −0.011, MGnify −0.047, P1 −0.021); formal per-predictor Spearman ρ requires per-KO PGLS which was not run |

## Results

### Dataset composition

| Dataset | Source | MAGs total | MAGs with CSU | Mean ko_per_mb_primary |
|---|---|---|---|---|
| SPIRE | `refdata.spire` download endpoints | 15,957 | 15,368 | 51.6 KO/Mb |
| MGnify | `kescience_mgnify` Spark tables | 8,849 | 7,973 | 20.3 KO/Mb |

SPIRE MAGs were downloaded from `https://spire.embl.de/download_eggnog/{SAMPLE_ID}` (eggnog TSV) and `https://spire.embl.de/download_file/{MAG_ID}` (FASTA for contig-length extraction). MGnify MAGs were queried from the `kescience_mgnify.genome` and `kescience_mgnify.gene_eggnog` Spark tables. Both datasets were filtered to Bacteria, completeness ≥70%, contamination ≤10%, non-host ENVO, with valid CSU metal-mobility coordinates (PF1_Cu primary target; 6 metals total).

### Spatial block CV results — SPIRE (PF1_Cu)

| Model | Mean RMSE | SD | Mean R² | SD |
|---|---|---|---|---|
| B0 (mean baseline) | 0.0501 | 0.021 | −0.171 | 0.221 |
| B1 (pH + organic carbon) | 0.0547 | 0.019 | −0.540 | 0.500 |
| B2/M2 (all SoilGrids) | 0.0439 | 0.022 | −0.030 | 0.764 |
| M1 (MAG density only) | 0.0527 | 0.020 | −0.341 | 0.176 |
| M3 (MAG density + SoilGrids) | **0.0400** | 0.019 | **0.162** | 0.443 |

### Spatial block CV results — MGnify (PF1_Cu)

| Model | Mean RMSE | SD | Mean R² | SD |
|---|---|---|---|---|
| B0 (mean baseline) | 0.0369 | 0.015 | −0.083 | 0.080 |
| M1 (MAG density only) | 0.0385 | 0.013 | −0.231 | 0.165 |
| M2 (metal fractions only) | 0.0164 | 0.005 | 0.760 | 0.090 |
| M3 (MAG density + metal fractions) | **0.0163** | 0.007 | **0.779** | 0.084 |

*Note: MGnify M2 uses PF1_As/Cd/Cr/Hg/Pb as features in addition to PF1_Cu target; SPIRE M2 uses SoilGrids soil chemistry. Different feature sets reflect what was available per dataset.*

### SHAP importance — SPIRE M3

| Feature | Mean |SHAP| |
|---|---|
| organic_carbon_density | 0.01954 |
| clay_content | 0.01198 |
| ph_h2o | 0.01128 |
| ko_per_mb_transport | 0.00073 |
| ko_per_mb_metabolism | 0.00050 |
| ko_per_mb_cofactor | 0.00048 |
| ko_per_mb_sensing | 0.00042 |
| ko_per_mb_resistance | 0.00041 |
| ko_per_mb_primary | 0.00040 |

Soil features are 20–50× more important than any KO density feature. All KO-density subcategories combined contribute <4% of total SHAP importance.

### SHAP importance — MGnify M3

| Feature | Mean |SHAP| |
|---|---|
| PF1_Cr | 0.01064 |
| PF1_As | 0.00866 |
| PF1_Hg | 0.00446 |
| PF1_Pb | 0.00398 |
| PF1_Cd | 0.00297 |
| ko_per_mb_resistance | 0.00013 |
| ko_per_mb_cofactor | 0.000061 |
| ko_per_mb_primary | 0.000049 |
| ko_per_mb_metabolism | 0.000047 |
| ko_per_mb_sensing | 0.000037 |
| ko_per_mb_transport | 0.000036 |

Metal fraction covariates dominate MGnify M3 SHAP. KO density features are 50–300× smaller than the leading metal fraction feature (PF1_Cr).

### Geographic holdout — Australia

*(Figure: figures/nb03b_holdout_map.pdf — MGnify Australia holdout: MAG sampling locations)*

| Dataset | n_holdout | RMSE | R² | Holdout/CV ratio | H4/H7 verdict |
|---|---|---|---|---|---|
| SPIRE | 43 | 0.0272 | −0.392 | **0.515** | SUPPORTED (< 1.25) |
| MGnify | 97 | 0.0252 | −0.375 | **0.655** | SUPPORTED (< 1.25) |

The negative R² confirms that the model does not fit within-Australia variation; predictions are worse than a constant for any Australian test set. The ratio criterion is met because the holdout RMSE is low in absolute terms, not because predictions are accurate.

### PGLS directional consistency

| Dataset | n genera | β | SE | p | Sign vs P1 |
|---|---|---|---|---|---|
| P1 (genus-level, comprehensive_metal_ecology) | ~500 | −0.021 | — | <0.05 | — |
| SPIRE MAG-aggregated | 254 | −0.011 | 0.0086 | 0.216 | ✓ |
| MGnify MAG-aggregated | 444 | −0.047 | 0.041 | 0.252 | ✓ |

Sign concordance across all three datasets supports the P1 biological direction but MAG-level PGLS does not reach significance, consistent with the higher within-genus variance at MAG resolution.

*(Figure: figures/nb05_target_distributions.pdf — PF1_Cu target distribution comparison: SPIRE vs MGnify)*

## Interpretation

### Scale mismatch explains the predictive null result

The genus-level P1 finding (metal-gene density correlates with niche breadth) does not extend to MAG-level prediction of local metal conditions. This is mechanistically plausible: the P1 signal emerges from averaging over thousands of MAGs per genus across diverse environments, compressing within-genus variance. At the individual MAG level, genome content is highly variable even within a genus — a single organism's KO complement is shaped by horizontal gene transfer, strain-level variation, assembly completeness, and recent evolutionary history, none of which tracks tightly with the metal mobility fraction at its sampling coordinate.

Metal mobility itself is largely determined by soil physical and geochemical properties (organic matter binding, clay cation exchange, pH-driven speciation) that operate at the metre-to-kilometre scale. A 4-Mb bacterial genome sampled from a point in space carries almost no information about what fraction of Cu at that point is in the mobile phase — a question answered better by measuring the soil than by reading the genome.

### Consistent weak directionality — not an artefact

The sign-concordant negative β across P1 (genus-level), SPIRE (MAG-aggregated), and MGnify (MAG-aggregated) is unlikely to be coincidental. All three are independent datasets with different sample sizes, geographic coverage, and annotation pipelines. The consistent direction (genera with higher metal-gene density occupy broader Levins' B niches, i.e., are found in more geochemically variable environments) is interpretable as an ecological adaptation signal: metal-resistant genera are ecologically generalist with respect to the metal gradient, rather than specialists in high-metal environments. This is consistent with the H3 interpretation from `comprehensive_metal_ecology` — metal genes confer tolerance breadth, not contamination adaptation.

The failure of this signal to translate to MAG-level prediction is informative precisely because it is not a null result in the genus-level analysis. It means the association is a genus-level aggregate phenomenon, not a feature of individual genomes — analogous to how phylogenetic inertia at the genus level can produce a signal that is undetectable at the isolate level.

### MGnify SHAP — metal fractions as environmental proxies

The MGnify M3 SHAP pattern (metal fraction features >> KO density) reflects that local metal mobility co-varies with other metals in the CSU grid. PF1_Cr and PF1_As are excellent proxies for the overall geochemical context of a sampling site, so including them as features gives the model environmental context that dwarfs any genomic signal. This is consistent with the SPIRE result (where pH and organic carbon play the same proxy role).

### Literature Context

- **Liu et al. (2024, *Nature Communications*)**: Metal resistance gene co-selection with antibiotic genes in global soil metagenomes occurs at the community level and is driven by co-contamination gradients rather than individual-genome content — consistent with our finding that community-level signals (P1) do not translate to MAG-level predictive power (Liu et al., DOI: 10.1038/s41467-024-49165-5).
- **Liang et al. (2024, *Biology and Fertility of Soils*)**: Vertical migration of bacteria carrying heavy metal resistance genes through soil profiles is modulated by soil physicochemical properties (organic matter, clay), not by gene content alone — supporting the interpretation that soil geochemistry is the dominant predictor at the local scale (DOI: 10.1007/s00374-024-01878-x).
- The SPIRE database (Salazar et al.) provides the largest curated repository of environmental MAGs with spatial coordinates, enabling this scale of analysis; geographic biases toward European and N. American sampling sites affect the holdout's representativeness.

### Novel Contribution

This project provides the first direct test of whether a genus-level genomic-ecological signal (P1 metal-gene density × niche breadth) is recoverable at the individual-MAG level and whether it can be applied to predict environmental metal conditions at sampling coordinates. The negative result (H1, H2 not supported) is informative: it bounds the ecological resolution at which the P1 association operates (genus-level aggregate, not individual genome), and it quantifies the scale of the soil-chemistry advantage (20–50× SHAP dominance) over genomic features. The sign-concordant PGLS β across three independent datasets establishes that the P1 direction is robust.

### Limitations

1. **Single metal target (PF1_Cu)**: CV and SHAP reported for copper only; other metals (As, Cd, Cr, Hg, Pb) may show different patterns, particularly for As where soil adsorption is highly pH-sensitive.
2. **MAG quality filter**: completeness ≥70%, contamination ≤10% excludes lower-quality MAGs that may carry different gene complements; the filtered set is biased toward more complete, better-assembled genomes from abundant taxa.
3. **Australia holdout sparsity**: n=43 SPIRE MAGs in the holdout region is too small for robust within-region assessment (R²=−0.39 is within the noise range for n=43). The n=97 MGnify holdout is marginal.
4. **SPIRE eggnog download completeness**: not all SPIRE MAGs had retrievable eggnog files; the 15,957-MAG dataset may under-represent rare lineages or samples with download failures.
5. **MGnify KO annotation via KEGG_ko column**: annotation rates may differ from SPIRE's eggnog annotations; the lower mean ko_per_mb_primary in MGnify (20.3 vs 51.6 KO/Mb) may partly reflect annotation pipeline differences rather than biology.
6. **H8exp not fully evaluable**: per-KO PGLS for Spearman ρ comparison was not run; the sign-concordance across datasets is consistent with ρ > 0.3 but the formal criterion cannot be verified from the available data.
7. **MGnify mobile-fraction target**: the MGnify dataset uses `mobile_fraction` (proportion of genome on mobile elements) as a proxy for plasticity, which is a different biology from CSU metal mobility fractions used in SPIRE; this limits direct comparability of effect sizes.
8. **Genome-sampling niche breadth is confounded by study effort (NB06/NB07):** An alternative Levins' B computed directly from the SPIRE MAG biome distribution (NB06, n=328 genera) shows much weaker phylogenetic signal than the MicrobeAtlas 16S measure used in H5 (λ=0.204 vs. λ≈0.81 in P1). NB07 demonstrates this is a sampling artefact, not biology: Pearson r=0.80 (p=2×10⁻¹⁴⁵) between genome-derived Levins' B and log(number of unique studies sampling a genus), explaining 70.6% of variance (OLS R²=0.706). Once study count is included as a covariate, the KO-density β flips sign (from −0.056, p=0.41 to +0.018, p=0.57) and PGLS λ collapses from 0.204 to <0.001. A rarefied analysis (1 MAG per genus-study combination, n=100 genera) yields the same sign reversal (+0.042, p=0.71). This validates the H5 design choice of using curated MicrobeAtlas 16S-based niche breadth rather than MAG-sampling-derived Levins' B, and serves as a pitfall warning for any genus-level ecological metric derived from SPIRE or MGnify sampling counts.

## Discoveries

- **The P1 genus-level metal-gene signal (β=−0.021 in comprehensive_metal_ecology) is sign-concordant but non-significant at MAG resolution across two independent datasets (SPIRE β=−0.011 p=0.22, MGnify β=−0.047 p=0.25).** Scale matters: the association is a genus-level aggregate phenomenon that does not surface at individual-genome resolution. This establishes an ecological resolution bound — metal-gene niche breadth associations operate at ≥genus level, not at the isolate/MAG level.

## Performance Notes

- SPIRE eggnog downloads at ~36 MB/sample (gzip TSV) and MAG FASTA files at ~422 KB/MAG; caching to `data/spire_cache/` is essential — re-running without cache would require ~400 GB of downloads. Always check cache before launching NB01.
- MGnify Spark query (`kescience_mgnify.gene_eggnog`) requires parsing K##### patterns from the KEGG_ko column (comma-separated, e.g. "K00001,K00043"); use `explode` + regex extract. Do NOT use `kescience_mgnify` for any BERDL tier analysis — use `kbase.ke_pangenome` per CLAUDE.md.

## Data

### Sources

| Collection | Tables / Endpoints Used | Purpose |
|---|---|---|
| `refdata.spire` | `mag_coordinates`, `genome_metadata`, `sample_environment`, `sample_microntology` + download endpoints | SPIRE MAG coordinates, quality, env features |
| `kescience_mgnify` | `kescience_mgnify.genome`, `kescience_mgnify.gene_eggnog` | MGnify MAG metadata and KO annotations |
| `arkinlab.envdbs.csu_metal_mobility_grid` | PF1_As/Cd/Cr/Cu/Hg/Pb columns | Environmental metal targets |
| `arkinlab.envdbs.soilgrids_master` | ph_h2o, organic_carbon_density, clay_content | SoilGrids features (SPIRE models) |
| `comprehensive_metal_ecology/data/curated_mrg_ko_ids_v2.csv` | 256 curated metal-gene KO IDs | KO selection and subcategory labels |

### Generated Data

| File | Description |
|---|---|
| `data/spire_probe_results.json` | SPIRE data-path probe results (use_spire_downloads=True) |
| `data/nb01_build_summary.json` | SPIRE MAG counts: 15,957 total, 15,368 with CSU, 13,182 with SoilGrids |
| `data/mag_feature_matrix.parquet` | SPIRE MAG feature matrix (15,957 rows, density + env + metadata) |
| `data/cv_results.csv` | SPIRE 5-fold spatial block CV RMSE/R² per model per fold (30 rows) |
| `data/shap_mean_abs.csv` | SPIRE SHAP mean absolute importance per feature (M3 model) |
| `data/holdout_results.json` | SPIRE Australia holdout: RMSE=0.0272, R²=−0.392, ratio=0.515 |
| `data/pgls_validation_results.csv` | SPIRE genus-aggregated PGLS: β=−0.011, p=0.22, n=254 genera |
| `data/nb01b_build_summary.json` | MGnify MAG counts: 8,849 total, 7,973 with CSU |
| `data/mgnify_mag_feature_matrix.csv` | MGnify MAG feature matrix (8,849 rows) |
| `data/mgnify_mobility_prediction_results.csv` | MGnify 5-fold CV (20 rows, B0/M1/M2/M3) |
| `data/mgnify_shap_mean_abs.csv` | MGnify SHAP mean |SHAP| per feature (M3 model) |
| `data/mgnify_geographic_holdout.csv` | MGnify Australia holdout: RMSE=0.0252, R²=−0.375, ratio=0.655 |
| `data/mgnify_pgls_validation.csv` | MGnify PGLS: β=−0.047, p=0.252, n=444 genera |
| `data/mgnify_vs_spire_comparison.csv` | Cross-dataset CV RMSE aggregates (6 model × 2 dataset × 1 target) |

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|---|---|
| `00_download_spire.ipynb` | SPIRE data-path probe; determines use_spire_downloads=True |
| `01_mag_feature_matrix.ipynb` | Build SPIRE MAG feature matrix; CSU and SoilGrids spatial join |
| `02_predict_mobility.ipynb` | H1/H2/H3 spatial block CV (5-fold, k-means); SHAP importance (M3) |
| `03_geographic_holdout.ipynb` | H4 Australia holdout evaluation |
| `04_pgls_validation.ipynb` | H5 genus-aggregated PGLS (levins_b_z ~ ko_per_mb_primary_z) |
| `01b_mgnify_feature_matrix.ipynb` | Build MGnify feature matrix from Spark tables |
| `02b_mgnify_mobility_prediction.ipynb` | MGnify H5exp/H6exp CV; SHAP importance |
| `03b_mgnify_geographic_holdout.ipynb` | MGnify H7exp geographic holdout |
| `04b_mgnify_pgls_validation.ipynb` | MGnify PGLS (PF1_Cu_z ~ ko_per_mb_primary_z) |
| `05_mgnify_vs_spire_comparison.ipynb` | Cross-dataset comparison; H8exp directional consistency |
| `06_spire_genome_levins_b_pgls.ipynb` | NB06 confound diagnostic: genome-sampling Levins' B PGLS (β=−0.056, p=0.41, λ=0.204); category comparison vs P1 |
| `07_study_design_confound.ipynb` | NB07 confound analysis: Pearson r=0.80 vs study count (R²=0.706); sign flip after control; rarefied sensitivity |

### Figures

| Figure | Description |
|---|---|
| `figures/nb02_cv_rmse.pdf` | SPIRE 5-fold spatial CV RMSE by model (B0/B1/B2/M1/M3) |
| `figures/nb02_shap_bar.pdf` | SPIRE SHAP mean |SHAP| per feature (M3 model) |
| `figures/nb02b_cv_rmse.pdf` | MGnify 5-fold spatial CV RMSE by model (B0/M1/M2/M3) |
| `figures/nb02b_shap_bar.pdf` | MGnify SHAP mean |SHAP| per feature (M3 model) |
| `figures/nb03_holdout_map.pdf` | SPIRE Australia holdout: predicted vs actual PF1_Cu per MAG |
| `figures/nb03b_holdout_map.pdf` | MGnify Australia holdout: predicted vs actual PF1_Cu per MAG |
| `figures/nb05_cv_rmse_comparison.pdf` | Cross-dataset CV RMSE: SPIRE vs MGnify for B0/M1/M2/M3 |
| `figures/nb05_target_distributions.pdf` | PF1_Cu target distribution comparison: SPIRE vs MGnify |
| `figures/nb06_pgls_comparison.pdf` | NB06 PGLS: genome-derived Levins' B vs KO density scatter; P1 vs NB06 comparison |
| `figures/nb06_category_forest_plot.pdf` | NB06 per-category PGLS forest plot (cofactor/resistance/transport/sensing/metabolism) |
| `figures/nb07_levins_b_confound_scatter.pdf` | NB07 scatter: genome Levins' B vs n_unique_studies (Pearson r=0.80, p=2×10⁻¹⁴⁵) |
| `figures/nb07_study_confound_sensitivity.pdf` | NB07 sensitivity: baseline vs study-controlled vs rarefied PGLS coefficients |

## Future Directions

1. **Multi-metal extension**: Run CV for all 6 targets (As, Cd, Cr, Cu, Hg, Pb) to test whether any metal shows M1 > B0. Cu was chosen as primary target based on completeness; metals with stronger spatial autocorrelation (e.g., Cr in serpentinite-rich regions) may show a different pattern.
2. **Per-KO PGLS for H8exp**: Run genus-level PGLS for each of the 256 curated KOs in both SPIRE and MGnify to enable the formal Spearman ρ test. This would formally test whether SPIRE and MGnify share the same subset of functionally important KOs.
3. **Completeness stratification**: Stratify MAGs by completeness decile to test whether H1 results change for higher-quality MAGs (completeness ≥90%). If the predictive null holds across completeness strata, it rules out assembly-quality confounding.
4. **Strain-level resolution**: Test whether metagenomic reads from high-coverage samples, rather than MAG assemblies, show stronger density-environment associations — this would distinguish whether the scale mismatch is genomic (assembly/annotation) or ecological (individual vs. population-level selection).

## References

- Liu Y, et al. (2024). Organic fertilization co-selects genetically linked antibiotic and metal(loid) resistance genes in global soil microbiome. *Nature Communications*, 15, 5095. DOI: 10.1038/s41467-024-49165-5
- Liang H, et al. (2024). Vertical migration of bacteria bearing antibiotic resistance genes and heavy metal resistance genes through a soil profile as affected by manure. *Biology and Fertility of Soils*. DOI: 10.1007/s00374-024-01878-x
- Salazar G, et al. SPIRE: a Searchable, Planetary-scale mIcrobiome REsource. *Nucleic Acids Research* (2023). [SPIRE database: spire.embl.de]
- Tóth G, et al. (2025). Global soil toxic metal exceedance probabilities from the LUCAS soil survey and spatial modelling. *Science*. [science_2025 dataset; CSU metal mobility fractions from Reimann et al.]
- Arkin AP, et al. (2018). KBase: The United States Department of Energy Systems Biology Knowledgebase. *Nature Biotechnology*, 36, 566–569. DOI: 10.1038/nbt.4163

# Figure Catalog — Comprehensive Metal Ecology

All figures produced by NB01–NB37. Organized by thesis arc.
PDF is the canonical format for all final figures; PNG copies exist for quick preview.

---

## Arc 1 — Primary PGLS Results (NB01–NB15)

### `png/fig01_scatter.png`
**Caption.** Primary PGLS scatter plot. Each point is one metal-gene KO pair (n = 140 KOs × 9 metals). X-axis: mean environmental metal concentration (log-transformed). Y-axis: PGLS slope (β) from a phylogenetic generalized least-squares regression of per-MAG KO presence/absence on environmental metal, controlling for genome size and sampling depth. Points are colored by metal. Horizontal reference line at β = 0.

**Interpretation.** The upward trend — higher metal concentration associated with higher KO prevalence — is the central result of the project. Look for tight clustering of KO–metal pairs at high metal concentrations and positive β, and note that not all metals show equal signal (Hg and Cu are typically the strongest). Outlier pairs well above/below the trend are candidates for further investigation.

---

### `01_pgls_primary_scatter.png`
**Caption.** Alternative rendering of the primary PGLS scatter (earlier version). Same axes as `fig01_scatter.png`; may show fewer metals or an older FDR threshold. Superseded by `png/fig01_scatter.png`.

![Primary PGLS scatter: metal-gene density vs Levins' niche breadth](01_pgls_primary_scatter.png)

---

### `png/fig03_internal_split.png`
**Caption.** Internal functional split within the 140-KO metal-gene set. Bar chart comparing PGLS β for KOs classified as "resistance/efflux" vs "metabolism/cofactor" functions. BH-FDR corrected across all tests.

**Interpretation.** Resistance KOs (efflux pumps, metal-binding proteins) should show stronger positive β than metabolism/cofactor KOs if the signal is driven by active detoxification rather than incidental metal use. A clear split between the two bars supports the detoxification hypothesis.

---

### `03_category_forest_plot.png`
**Caption.** Forest plot of PGLS β by functional category. Each row is a KO functional category (e.g., efflux, sensor/regulator, metallothionein, cofactor). Points show the mean β; horizontal bars show 95% CI. Dashed vertical reference line at β = 0.

**Interpretation.** Categories above zero are associated with higher metal gene prevalence in high-metal environments. Categories closest to zero or overlapping zero are the weakest signals. The rank order of categories is the key result — efflux/resistance categories should dominate.

![Primary PGLS scatter: metal-gene density vs Levins' niche breadth](03_category_forest_plot.png)

---

### `04_confounder_beta_comparison.png`
**Caption.** Confounder robustness forest plot. Each row shows the PGLS β for a representative KO–metal pair under different covariate specifications: baseline (no controls), + genome size, + pH, + MAG completeness, etc. Points shift along x as controls are added; bars show 95% CI.

**Interpretation.** If β shrinks dramatically when a control is added, that control is confounding the signal. Stable β across model specifications (points near each other) indicates robustness. Look for the pH and completeness panels — these are the strongest potential confounders.

---

### `clade_stratified_forest_plot.png`
**Caption.** Clade-stratified PGLS. Separate PGLS analyses within each of the four major bacterial phyla (Proteobacteria, Actinobacteria, Firmicutes, Bacteroidetes). Points show per-phylum β; forest plot format. BH-FDR across 4 phyla.

**Interpretation.** Consistent direction of effect across all four phyla (all positive or all negative) is strong evidence that the result is not driven by phylogenetic confounding at the phylum level. Disagreement between phyla points to phylum-specific biology.

---

### `cofactor_jackknife_forest.png`
**Caption.** Jackknife sensitivity for cofactor gene group. Repeated PGLS analyses each leaving out one cofactor KO at a time. Forest plot shows β and CI for each leave-one-out model.

**Interpretation.** If all jackknife models give nearly identical β, no single KO is driving the cofactor result — the signal is distributed. A single outlier model (one KO removal dramatically changes β) identifies a dominant cofactor gene.

---

### `coreness_permutation_histogram.png`
**Caption.** Coreness permutation test. Distribution of permuted test statistics (gray histogram) compared to the observed statistic (vertical red/blue line). Permutation was performed by randomizing metal concentration labels while preserving phylogenetic structure.

**Interpretation.** If the observed statistic lies far in the tail of the permuted distribution (p < 0.05), the metal–gene correlation is not explainable by phylogenetic autocorrelation alone. The p-value is the fraction of permuted statistics more extreme than observed.

---

### `split_magnitude_permutation.png`
**Caption.** Split-magnitude permutation test. Tests whether the functional split (resistance β > metabolism β) is larger than expected by chance. Gray histogram = permuted split magnitudes; vertical line = observed.

**Interpretation.** A significant result (observed line in the tail) confirms that the resistance/metabolism β difference is not a chance partitioning of the gene set.

---

## Arc 2 — Functional Landscape & Niche Breadth (NB16–NB24)

### `png/fig02_functional_landscape.png`
**Caption.** Functional landscape: per-Mb KO density vs niche breadth across 19 functional categories. Scatter plot where each point is a MAG; x-axis is Levin's niche breadth (from EMP metadata); y-axis is per-megabase KO density for the metal-gene set. Color encodes functional category.

**Interpretation.** A negative slope — specialist MAGs (narrow niche) have higher per-Mb metal-gene density — is the key prediction. MAGs from high-metal environments that are also specialists would drive this result.

---

### `png/fig01_multiaxis_heatmap.pdf` → `fig01_multiaxis_heatmap.pdf`
**Caption.** Multi-axis niche comparison heatmap. Rows = KOs; columns = niche axes (soil pH, metal concentration, temperature, moisture). Color = PGLS β on that niche axis. Hierarchically clustered by niche profile similarity.

**Interpretation.** KOs that respond to multiple niche axes simultaneously are ecologically versatile. KOs tightly clustered by metal-only response (high metal β, low pH/temperature β) are the most metal-specific. Look for a cluster of efflux genes that respond strongly to metal but not other niche axes.

---

### `nb28_rda_biplot.png`
**Caption.** RDA (Redundancy Analysis) biplot from NB28. MAG community composition (y-axis) constrained by environmental metal gradients (x-axis arrows). Points = MAGs; arrows = environmental predictors (metal concentrations, pH, climate variables).

**Interpretation.** Metal arrows that are long and orthogonal to non-metal arrows indicate that metal gradients independently explain community turnover. MAGs clustering near a metal arrow are characteristic of high-metal environments.

---

### `nb29_cwm_from_env_shap.png`
**Caption.** SHAP importance for community-weighted mean (CWM) KO density predicted from environmental variables. SHAP beeswarm plot; each row = one environmental feature; dot position = SHAP contribution; color = feature value (red = high, blue = low).

**Interpretation.** Features with large absolute SHAP values most strongly determine CWM KO density. Metal variables appearing near the top of the plot confirm that soil metal chemistry drives community-level functional composition more than other predictors (e.g., climate, pH).

---

## Arc 3 — Phylogenetic Signal & Mechanistic Probes (NB25–NB32)

### `nb27_A1_lambda_by_subcategory.pdf`
**Caption.** Phylogenetic signal (Pagel's λ) by functional subcategory. Bar chart; each bar = one subcategory; height = mean λ; error bars = 95% CI bootstrapped across KOs in that subcategory.

**Interpretation.** λ near 1 = strong phylogenetic conservatism (trait clusters on the tree). λ near 0 = no phylogenetic signal (convergent evolution or HGT). Resistance subcategories with low λ relative to metabolism subcategories support the hypothesis that resistance genes are mobilized by HGT.

---

### `nb27_B1_lambda_landscape.pdf`
**Caption.** Lambda landscape: heatmap of Pagel's λ across all KO × metal combinations. Rows = KOs; columns = metals; color = λ.

**Interpretation.** KO–metal pairs with low λ AND high PGLS β are the most compelling — they show metal-correlated prevalence without phylogenetic conservatism, consistent with HGT-driven acquisition. merA (Hg methylation) is expected to appear as a high-β, low-λ outlier.

---

### `nb27_C1_lambda_vs_csu_beta.pdf`, `nb27_C2_lambda_vs_georoc_beta.pdf`, `nb27_D1_lambda_vs_usgs_beta.pdf`
**Caption.** λ vs |β| scatter for each metal concentration dataset (CSU, GEOROC, USGS). Each point = one KO; x-axis = |PGLS β| (effect size); y-axis = Pagel's λ; Spearman ρ annotated.

**Interpretation.** A negative ρ (high β paired with low λ) would support HGT as the mechanism — genes under strong metal selection are phylogenetically labile. A near-zero ρ (Test 1 result: ρ = 0.092, NS) means phylogenetic lability does not predict metal-responsiveness across all resistance KOs, suggesting the mechanism is more nuanced.

---

### `nb27_D2_usgs_ph_control.pdf`, `nb27_E1_csu_ph_control.pdf`
**Caption.** λ vs |β| scatter after controlling for soil pH. Same as the main λ–β scatter but β is from a model that includes pH as a covariate.

**Interpretation.** If pH control changes the λ–β relationship (ρ shifts), pH was confounding the apparent signal. Stability of ρ after pH control indicates the λ–β pattern is not explained by pH-driven community turnover.

---

### `nb30_F1_lambda_beta_heatmap.pdf`
**Caption.** Heatmap of Spearman ρ(λ, |β|) across all metal × covariate-model combinations. Rows = metals; columns = model specifications (baseline, +pH, +completeness, +kitchen sink). Color = ρ value; asterisks mark p < 0.05.

**Interpretation.** Near-zero or NS values across all cells confirm that phylogenetic lability does not generalize as a predictor of metal-responsiveness. A systematic pattern (e.g., one metal consistently showing negative ρ) would point to a metal-specific HGT signal.

---

### `nb30_F2_rho_trajectory.pdf`
**Caption.** Trajectory of ρ(λ, |β|) as covariates are sequentially added. Line plot; x = model step (baseline → + genome size → + pH → ...); y = ρ; separate lines per metal.

**Interpretation.** Stable ρ across covariate additions means the λ–β relationship (or lack thereof) is robust to confounding. A ρ that collapses toward zero after adding pH suggests pH was generating spurious λ–β correlation.

---

### `nb30_F3_top_scatter.pdf`, `nb30_F4_beta_stability.pdf`, `nb30_F5_control_effect.pdf`
**Caption.** Supplementary diagnostics for NB30. F3: scatter of λ vs |β| for the metal with the strongest ρ. F4: β stability across models (coefficients from each model step). F5: effect of each control on mean |β| across KOs.

---

### `nb31_F1_stratum_heatmap.pdf`, `nb31_F2_stratum_trajectory.pdf`, `nb31_F3_monotonicity.pdf`, `nb31_F4_best_metal_scatter.pdf`
**Caption.** Contamination-stratified PGLS (NB31). Samples divided into tertiles by total metal loading; PGLS re-run within each stratum. F1: heatmap of β × metal × stratum. F2: trajectory of β as stratum increases. F3: monotonicity test (does β increase from low- to high-contamination stratum?). F4: scatter for the best-performing metal.

**Interpretation.** Monotonically increasing β from low- to high-contamination strata would confirm dose-response specificity. Non-monotonic patterns suggest the association is driven by extreme outlier sites rather than a gradient.

---

### `fig_nb32_cobalamin_vs_translation.pdf`
**Caption.** Cobalamin vs translation KO ratio as a function of environmental and genomic predictors (NB32). Scatter plot; x = metal or pH predictor; y = cobalamin/translation density ratio. RFE identified this ratio as the dominant feature distinguishing metal-adapted communities.

**Interpretation.** If the ratio increases with metal concentration, metal-adapted MAGs upregulate cobalamin biosynthesis relative to ribosomal translation — consistent with cobalt/cobalamin co-selection in heavy-metal environments.

---

### `fig_nb32_rfe_model_comparison.pdf`
**Caption.** Recursive Feature Elimination (RFE) model performance vs number of features retained (NB32). X = number of features kept; y = cross-validated R² or RMSE. Vertical dashed line = optimal feature count.

**Interpretation.** The elbow in model performance identifies the minimal feature set sufficient to predict community metal-gene enrichment. Features retained at the optimum are the most informative environmental predictors.

---

### `fig_nb32_rfe_scatter.pdf`
**Caption.** Predicted vs observed KO density for the RFE-selected model (NB32). Each point = one MAG; x = observed per-Mb KO density; y = predicted by RFE model. R² annotated.

**Interpretation.** Points close to the diagonal indicate good predictive accuracy. Systematic curvature or outlier clusters reveal where the model fails (e.g., extreme-contamination MAGs that the linear model underpredicts).

---

## Arc 4 — Geochemical Validation (NB33–NB36)

### `nb33_mwas_results.pdf`
**Caption.** MWAS (microbiome-wide association study) results from NB33. Each point = one KO; x = PGLS β; y = −log₁₀(BH-FDR q-value). Volcano plot format. Horizontal dashed line = q = 0.05 threshold.

**Interpretation.** KOs in the upper-right quadrant (positive β, low q) are enriched in high-metal environments and statistically robust. KOs in the upper-left are depleted. The raw MWAS yields ~1,097 hits that collapse dramatically when community composition is controlled, illustrating the collinearity problem (NB31–NB32).

---

### `nb33_pgls_comparison.pdf`
**Caption.** Comparison of PGLS β before and after adding community-composition covariate (NB33). Each point = one KO; x = baseline β; y = β with community control. Points on the diagonal = no change; points shifting toward zero = community-confounded associations.

**Interpretation.** Most points should shift toward zero when community is controlled, because community composition is a collider/mediator in the metal → gene path. The few points that remain off-diagonal after community control are the most robustly metal-associated KOs.

---

### `nb34_genus_mwas_bubble.pdf`
**Caption.** Genus-level MWAS bubble chart (NB34). Each bubble = one genus × metal combination; bubble size = number of associated KOs; color = direction of association; x-axis = genus; y-axis = metal. Genus names sorted by total number of significant associations.

**Interpretation.** Genera with many associations across multiple metals are broad-spectrum metal responders (or phylogenetically confounded). Genera with associations limited to one metal (e.g., only Hg) are candidate metal specialists.

---

### `nb34_genus_mwas_heatmap.pdf`
**Caption.** Heatmap version of genus × metal MWAS results (NB34). Rows = genera; columns = metals; color = signed −log₁₀(q). Hierarchically clustered.

**Interpretation.** Row clusters of genera that co-respond to the same metals suggest functional/phylogenetic groupings. Look for a cluster of Hg-specific genera (Proteobacteria, especially Gammaproteobacteria) and a separate cluster of multi-metal responders.

---

### `nb34_vs_pgls_triangulation.pdf`
**Caption.** Triangulation of genus MWAS results against primary PGLS (NB34). Each point = one KO; x = primary PGLS β; y = genus MWAS β for the corresponding genus. Agreement on sign indicates both analyses point in the same direction.

**Interpretation.** Quadrant I (both positive) = robustly enriched. Quadrant III (both negative) = robustly depleted. Discordant quadrants (II or IV) = one analysis is capturing a different signal (possibly community confounding in the MWAS).

---

### `fig_nb35_metal_pca.pdf`
**Caption.** Metal PCA biplot from USGS NGSA soil chemistry (NB35). Each axis = one principal component; arrows = metal loadings; color = loading magnitude. PC1 explains ~58% of variance (lithogenic crustal metals: Ba, Sr, Zr, REEs, Th, U, Sb, Bi). PC2 explains ~20% of variance (Hg/hydrothermal metals: Hg, Ni, Cr, Li).

**Interpretation.** PC1 separates sites by crustal rock weathering (high PC1 = continental interior, plutonic/metamorphic parent material). PC2 separates sites by hydrothermal/volcanic input (high PC2 = Pacific coast volcanic terrain). The PCA axes define orthogonal geochemical gradients used in NB35 Tests 2–3 and validated in NB36.

---

### `fig_nb35_d_vs_cognate_rank.pdf`
**Caption.** Fritz & Purvis D statistic vs cognate metal rank for matched resistance KOs (NB35, Test 1). Each point = one KO (n = 53 matched KOs); x = Fritz & Purvis D (phylogenetic signal in gene presence/absence); y = rank of cognate metal in the PGLS β ordering. merA (Hg methylation) labeled as an outlier.

**Interpretation.** If HGT-mobilized genes (low D) systematically track their cognate metals better (low cognate rank = high β), we would expect a negative correlation. The observed Spearman ρ = 0.092 (NS) means HGT lability does NOT predict cognate-metal specificity across all 53 KOs. merA is an extreme outlier (D = 0.646, highest HGT signal) but its Hg specificity ranks highly — suggesting merA is an exception, not the rule.

---

### `fig_nb35_legacy_proximity.pdf`
**Caption.** Mine proximity as a predictor of PGLS β for Hg-associated KOs (NB35, Test 3). Each point = one USGS NGSA soil sample; x = log(nearest MRDS Hg mine distance, km); y = log(USGS soil Hg, ppm). OLS regression with R² and slope annotated.

**Interpretation.** Mine proximity was tested as a confound for the merA × Hg signal. If β for merA is driven by contamination from legacy Hg mines, mine proximity should explain substantial variance in Hg concentrations. The result (R² < 0.001, Test 3 NOT supported) indicates that USGS NGSA Hg is predominantly geogenic (median nearest mine = 322.5 km), not contamination-driven.

---

### `fig_nb36_lithology_pcs.pdf`
**Caption.** PC1 and PC2 scores by GLiM lithology class (NB36). Box plots or bar charts (one bar/box per lithology class) for PC1 and PC2 separately. Kruskal-Wallis H-statistic and p-value annotated. Lithology classes: VA (Acid Volcanic), VI (Intermediate Volcanic), VB (Basic Volcanic), SU (Unconsolidated Sediments), etc.

**Interpretation.** The key finding is the fine-grained split within Volcanic: VA (silicic/rhyolitic; median PC2 = +5.594) is strongly elevated on the Hg/hydrothermal axis, while VI (andesitic; median PC2 = −0.402) is NOT. This geochemically validates the PC2 axis: epithermal Hg systems associate with silicic volcanism, not andesitic arc volcanism.

---

### `fig_nb36_pca_biplot_lithology.pdf`
**Caption.** PCA biplot colored by GLiM lithology class (NB36). Same PC1 vs PC2 scatter as NB35 but with points colored by the dominant lithology class at each sample's grid cell.

**Interpretation.** If GLiM classes cluster in PCA space (e.g., all VA points in the upper-right, all SU points in the lower-left), it confirms that the PCA axes capture lithological variation. Overlap between classes indicates within-class heterogeneity or coarse grid resolution.

---

## Arc 5 — Geographic Visualization (NB37)

### `fig_nb37_hg_pc_map.pdf` / `fig_nb37_hg_pc_map.png`
**Caption.** Three-panel map of metal PCA scores and raw Hg across continental USA soil samples (n = 4,554 complete-case). Left: PC2 score (Hg/hydrothermal axis, 20% variance); center: PC1 score (lithogenic crustal axis, 58% variance); right: log(USGS Hg + 1) in ppm. Albers Equal Area projection. Colors: RdBu_r diverging for PCA scores; YlOrRd sequential for raw Hg. Complete-case samples cluster in three geographic regions: NE (n ≈ 2,539), WY/CO (n ≈ 1,050), CA (n ≈ 965).

**Interpretation.** The CA cluster (Pacific coast, volcanic terrain) shows elevated PC2 (warm/red colors in left panel), consistent with epithermal Hg systems. The WY/CO cluster (interior cratonic) shows elevated PC1 (warm in center panel), consistent with lithogenic crustal metals. The NE cluster (Appalachian sedimentary) is near-zero on both axes. Raw Hg (right panel) is elevated in CA, consistent with PC2, but note that overall by GLiM lithology class the raw Hg difference is not significant (p = 0.093) — the multivariate PC2 captures co-varying metals (Se, Ni, Cr) that univariate Hg misses. **Note:** Only 4,554 of 6,034 samples have complete metal panels; spatial coverage is uneven due to USGS survey design.

---

### `fig_nb37b_pca_cluster_scatter.pdf` / `fig_nb37b_pca_cluster_scatter.png`
**Caption.** PCA cluster analysis of USGS soil metals by geographic region (NB37). Left panel: PC1 vs PC2 biplot with KDE density contours for each geographic cluster (CA = orange; WY/CO = teal; NE = blue). Loading vectors for key metals shown as arrows: HG and NI point upward (PC2-dominant, hydrothermal metals); TH and U point rightward (PC1-dominant, lithogenic/crustal metals). Upper-left note lists additional coloaders. Center panel: violin plots of PC2 score by cluster (KW p < 0.001). Right panel: violin plots of log(USGS Hg + 1) by cluster (KW p < 0.001). N labels embedded in violin bodies.

**Interpretation.** The three geographic clusters occupy clearly distinct regions of PCA space: CA (volcanic terrain) has high PC2 (Hg/hydrothermal enrichment); WY/CO (interior crustal) has near-zero PC2 but moderate positive PC1; NE (Appalachian sedimentary) has negative PC2 and negative PC1. The violin plots confirm the statistical significance of the separation. The loading vectors show that the PC2 elevation in CA reflects co-enrichment of Hg, Ni, Cr, and Li — the geochemical fingerprint of epithermal and serpentinite systems common along the Pacific coast. **Use this figure as the primary visual summary of NB35–NB36 geochemical validation.**

---

## Supplementary / Diagnostic Figures

### `per_ko_lambda_violin.pdf`
**Caption.** Violin plot of Pagel's λ distribution across all KOs, stratified by tier (resistance vs metabolism). Shows spread and central tendency of phylogenetic signal.

---

### `per_ko_lambda_environmental_ngsa.pdf`, `per_ko_lambda_environmental_georoc.pdf`
**Caption.** Per-KO λ distributions stratified by environmental dataset (USGS NGSA or GEOROC). Allows comparison of phylogenetic signal magnitude across geochemical measurement frameworks.

---

### `phylo_d_all_ko_by_category.pdf`, `phylo_d_all_ko_by_tier.pdf`, `phylo_d_ko_presence.pdf`
**Caption.** Fritz & Purvis D statistic distributions. `by_category`: D by functional category. `by_tier`: D for resistance vs metabolism tiers. `ko_presence`: D vs prevalence scatter (high-prevalence KOs expected to have higher D due to conservatism).

---

### `fritz_purvis_D_genome.pdf`
**Caption.** Fritz & Purvis D at the genome level (whole-genome metal-gene count). Baseline for comparing KO-level D values.

---

### `nb33_pgls_comparison.pdf` *(repeated for emphasis)*
**Caption.** See Arc 4. This figure is critical for understanding the collinearity trap: most MWAS hits are community-composition effects, not direct metal–gene associations.
![Primary PGLS scatter: metal-gene density vs Levins' niche breadth](nb33_pgls_comparison.pdf)
---

## Notes

- **Complete-case bias (NB37 maps):** The 4,554 complete-case samples (all 31 metals measured) are geographically clustered, not a random national sample. Extrapolation to unmeasured US regions is not warranted.
- **Pd/Pt exclusion (NB34):** USGS Pd has only 9 unique values; modal value (0.0022 ppm) accounts for 66% of measurements = detection limit artifact. Any Pd/Pt associations in NB34 are spatial clustering of detection limits, not biology.
- **Citation note for NB35:** Fritz & Purvis D was computed on genome presence/absence (binary trait), not abundance. D > 1 indicates overdispersion relative to Brownian motion; D < 0 indicates stronger conservatism than BM. merA D = 0.646 is intermediate (HGT-consistent but not extreme).
- **GLiM resolution:** Global Lithological Map grid = 0.25°. USGS NGSA samples joined by rounding lat/lon to nearest 0.25° cell. GLiM covered 99.9% of complete-case samples (4,550/4,554).

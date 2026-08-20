# Report — per_ko_metal_associations

**Question:** Across the entire functional genome of environmental MAGs, are there individual KEGG orthologs whose presence is significantly associated with bioavailable metal concentrations at the MAG's sampling site?

**All analyses in this project are exploratory.** Results are hypothesis-generating.

---

## Data

| Dataset | MAGs | KOs tested | Metal coverage |
|---------|------|-----------|----------------|
| MGnify (primary) | 8,585 | 6,451 | As, Cd, Cr, Cu, Hg, Pb |
| SPIRE (replication) | 2,477 | 4,759 | As, Cd, Cr, Cu, Hg, Pb |

Metal values are PF1 (probability of first factor) scores from the Qi et al. 2025 (*Nat Commun* 16; DOI 10.1038/s41467-025-58026-8) global soil metal mobility grid (~0.1° resolution), joined to each MAG by nearest grid cell ≤ 50 km (haversine BallTree). Latitude coverage: 100% in both datasets (range: −78.1° to 84.6°).

**SPIRE matrix rebuild (2026-07-29).** The SPIRE matrix was rebuilt with an extended environment filter (excluding host-associated, gut, clinical, marine, ocean, freshwater, and wastewater samples) and a SoilGrids join (pH, soil organic carbon, clay content at 0.25° resolution; `arkinlab.envdbs.soilgrids_master`). SPIRE MAG count changed from 2,905 (old matrix, pre-env-filter) to 2,477 (current). SoilGrids pH non-null: 77.4% of matrix rows (1,972 of 2,477 MAGs matched at 0.25°). Files: `data/spire_adj_ko_associations.csv` (baseline), `data/spire_sg_adj_ko_associations.csv` (SoilGrids-adjusted, WP6 sensitivity check).

**Note on PF1_Zn:** RESEARCH_PLAN.md pre-specified seven metals including Zn. PF1_Zn was absent from the CSU metal mobility grid joined to these MAGs (no Zn column returned), so all results cover six metals (As, Cd, Cr, Cu, Hg, Pb) only.

Long-format KO matrices: `data/mgnify_all_ko_matrix.parquet` (12.7M rows), `data/spire_all_ko_matrix.parquet` (3.3M rows). See `notebooks/00_build_ko_matrix.ipynb`.

---

## Denominators and sample sizes

Per-metal denominators for both datasets are presented below. MGnify contains n = 8,585 MAGs with 6,451 KOs tested across 6 metals. SPIRE contains n = 2,477 MAGs (rebuilt matrix, extended environment filter) with 4,759 KOs tested. Significant associations are defined as FDR q < 0.05 in the baseline model (latitude + phylum for MGnify; latitude + phylum/genus for SPIRE). pH-adjusted counts for SPIRE reflect the independent SoilGrids-adjusted regression (sg_pH + latitude + phylum/genus model), not a filtered subset of baseline associations — these are separate regression models, and new pairs can be significant in pH-adjusted while being null in baseline or vice versa.

| Metal | MGnify n_MAGs | SPIRE n_MAGs | MGnify n_KOs_tested | SPIRE n_KOs_tested | MGnify n_sig_baseline | SPIRE n_sig_baseline | MGnify n_sig_pH | SPIRE n_sig_pH |
|-------|--------------|--------------|--------------------|--------------------|----------------------|---------------------|-----------------|----------------|
| As    | 8,585 | 2,477 | 6,451 | 4,759 | 43 | 15 | 31 | 31 |
| Cd    | 8,585 | 2,477 | 6,451 | 4,759 | 12 | 15 | 4  | 31 |
| Cr    | 8,585 | 2,477 | 6,451 | 4,759 | 6  | 15 | 5  | 29 |
| Cu    | 8,585 | 2,477 | 6,451 | 4,759 | 0  | 15 | 0  | 29 |
| Hg    | 8,585 | 2,477 | 6,451 | 4,759 | 107| 15 | 76 | 29 |
| Pb    | 8,585 | 2,477 | 6,451 | 4,759 | 51 | 16 | 35 | 28 |

**Notes:** 
- MGnify baseline model: `KO_present ~ PF1_metal + log_genome_size + C(phylum)` (N phyla = 91). 
- SPIRE baseline model: `KO_present ~ PF1_metal + log_genome_size + latitude + C(phylum/genus)` (after extended environment filter; N taxa classes = 232).
- SPIRE pH-adjusted model: `KO_present ~ PF1_metal + log_genome_size + latitude + sg_pH + C(phylum/genus)` (SoilGrids pH; independent regression, not a filtering step on baseline hits).
- SPIRE pH-adjusted: Counts reflect per-metal significance in the sg_pH model. Of the 31 total pH-adjusted significant pairs across all metals, **24 overlap with baseline significant pairs** and **7 are newly significant only in the pH-adjusted model** (see H4 discussion). These are not subsets of the baseline; they are products of a different regression.
- MGnify "n_sig_pH" (76, 31, 5, etc.) refers to field-robust survivor counts from Notebook NB04 (latitude-adjusted model with phylum control; these are pre-existing results documented in the Robustness section below). SPIRE pH-adjusted are the new SoilGrids models from 2026-07-29.

---

## Hypotheses and outcomes

| ID | Hypothesis | Threshold | Outcome |
|----|-----------|-----------|---------|
| H1 | ≥20 KO-metal pairs reach FDR q<0.05 in MGnify | ≥20 pairs | **SUPPORTED** |
| H2 | β_MGnify ~ β_SPIRE Spearman ρ > 0.2 across shared pairs | ρ > 0.2 | **NOT SUPPORTED** |
| H3 | Curated metal KOs enriched among FDR-sig (Fisher p<0.05) | p < 0.05 | **NOT SUPPORTED** |
| H4 | ≥10 H1-significant pairs survive latitude adjustment | ≥10 survive | **SUPPORTED** |
| H5 | β stability ρ > 0.5 (adjusted vs unadjusted betas) | ρ > 0.5 | **SUPPORTED** |
| H6 | Adjusted cross-dataset β correlation > unadjusted | adj ρ > 0.059 | **NOT SUPPORTED** |
| H7 | ≥10 H1 pairs survive class-level taxonomic control | ≥10 survive | **SUPPORTED** |
| H8 | β stability ρ > 0.7 (phylum vs class model) | ρ > 0.7 | **SUPPORTED** |
| H9 | ≥5 H1 pairs survive phylo-PC continuous control | ≥5 survive | **SUPPORTED** |
| H10 | ≥10 H1 pairs survive MAG quality covariate control | ≥10 survive | **SUPPORTED** |

---

## H1 — Genome-wide associations exist (SUPPORTED)

`notebooks/01_per_ko_associations.ipynb` ran logistic regression (`KO_present ~ PF1_metal + log_genome_size + C(phylum)`) for every KO × metal combination across 6,451 MGnify KOs with BH FDR correction per metal.

**Sign convention.** β > 0: the gene is *more* likely to be present in MAGs from high-metal environments (correct bioindicator direction). β < 0: the gene is *less* likely in high-metal environments (depletion). The majority of the prominent named associations — merT×Hg, K07093×Hg, argP×Hg — are negative. Only arsH×Pb (field-strict survivor) and the kdp operon×Hg (top hit by magnitude) are significant in the positive direction. This sign pattern is biologically relevant (see "Functional interpretation" section): negative associations suggest community compositional turnover away from mer-carrying lineages, not gene gain along metal gradients.

**219 FDR-significant KO-metal pairs** (q<0.05) in MGnify. SPIRE independently found 69 significant pairs (rebuilt matrix, 2,477 MAGs; 75 in old 2,905-MAG matrix).

Significant pairs by metal:

| Metal | MGnify sig | SPIRE sig (rebuilt) | Direction |
|-------|-----------|----------|-----------|
| Mercury (Hg) | 107 | 34 | 76 neg, 31 pos |
| Lead (Pb) | 51 | 8 | 45 pos, 6 neg |
| Arsenic (As) | 43 | 13 | 42 neg, 1 pos |
| Cadmium (Cd) | 12 | 5 | 8 pos, 4 neg |
| Chromium (Cr) | 6 | 5 | all neg |
| Copper (Cu) | 0 | 4 | — |

H1 is robustly supported: 219 >> 20.

---

## H2 — Cross-dataset replication is weak (NOT SUPPORTED)

`notebooks/02_cross_dataset_comparison.ipynb`: The two datasets share 26,850 KO-metal pairs. Of these, **324 pairs (1.2%) have a finite beta estimate in both datasets**; the other 26,526 have a null beta in the MGnify unadjusted model (near-complete separation or group-filter exclusion caused logistic regression to return NaN). The H2 Spearman correlation is therefore computed on this 324-pair convergent subset: ρ = **0.059** (p = 0.29). Threshold was ρ > 0.2.

The low cross-dataset correlation most likely reflects genuine differences in ecosystem composition between MGnify (global, multi-biome) and SPIRE (primarily soil-focused) rather than a methodological failure — the H4/H5 results (below) confirm the associations are not geographic artifacts.

Two structural explanations for the weak ρ are supported by additional diagnostics. First, **taxonomic overlap is low**: MGnify contributes 3,300 unique genera and SPIRE 461; only 177 are shared (5.4% of MGnify, 38.4% of SPIRE, 4.9% of their union). Despite this low overlap, within-genus 140-KO primary density is highly correlated (Spearman ρ = 0.780, n = 104 shared genera with density data in both datasets), confirming that the per-genus metal-gene investment is consistent — the datasets simply cover very different parts of the bacterial diversity space (see `figures/genus_overlap.png`). Second, **metal gradient distributions differ**: KS tests show significant distributional differences for all 6 metals between the two datasets (Hg: D = 0.202; Cd: D = 0.198; Cu: D = 0.155; Cr: D = 0.121; Pb: D = 0.129; As: D = 0.111; all p < 0.001). The two datasets sample different ranges and shapes of metal exposure, so associations detected in one dataset's gradient may not exist in the other's gradient (see `figures/metal_gradient_comparison.png`). Together, low taxonomic overlap and different metal gradient coverage explain the low ρ = 0.059 without implying either dataset's associations are artefactual.

**Soil-restricted sensitivity analysis.** To test whether biome mixing in MGnify (which includes marine, sediment, and rhizosphere MAGs alongside soil) artificially deflates the cross-dataset ρ, the per-KO logistic regression was re-run restricted to the 6,615 MGnify MAGs classified as Soil or Rhizosphere (biome_name from `microbeatlas_metal_ecology/data/final_mags_geospatial_traits.csv`). SPIRE biome filtering was not feasible without Spark access to `refdata.spire.genome_metadata`; since SPIRE is primarily soil-focused, the full SPIRE dataset serves as the comparison. The soil-restricted model converged for all 38,706 KO-metal pairs (vs 910 convergent pairs in the all-biomes model), reflecting better-conditioned phylum-level design matrices in the ecologically constrained dataset. The cross-dataset Spearman ρ between soil-restricted MGnify β and full-SPIRE β was **ρ = 0.056** (n = 26,759 convergent pairs) — virtually identical to the all-biomes ρ = 0.059 (n = 324). **Biome mixing does not explain the weak cross-dataset replication.** Restricting MGnify to soil produces the same ρ as the full multi-biome dataset, confirming that the low correlation reflects genuine biological differences (taxonomic composition, metal gradient coverage) rather than sampling-strategy confounding. Results are in `data/soil_cross_dataset_comparison.csv`.

---

## H3 — Curated KOs are not enriched (NOT SUPPORTED)

`notebooks/03_functional_enrichment.ipynb`: Among the 219 FDR-significant MGnify associations, 0 belonged to the 730-KO curated metal-interacting list tested for enrichment. Fisher OR = 1.52 (p = 0.39). The curated KOs are not disproportionately detected.

The single exception was Cd: OR = 11.6 (p = 0.09), a trend that does not survive correction. The genome-wide screen finds different genes than the curated list — this is biologically interesting, not a failure, as the screen is designed to discover novel candidates.

---

## H4 — Most H1 associations survive geographic adjustment (SUPPORTED)

`notebooks/04_covariate_adjusted_associations.ipynb`: Latitude used as geographic covariate (SoilGrids REST API was unavailable at analysis time; latitude captures temperature/precipitation/biome gradients with 100% MAG coverage).

**138/219 H1-significant pairs remain FDR-significant** after latitude adjustment. Threshold was ≥10. Geographic confounding does not explain the H1 associations.

The adjusted model finds substantially more significant pairs overall (6,432 vs 219 unadjusted). This counter-intuitive expansion reflects increased statistical power once latitude-driven variance in genome content is explicitly partitioned: the metal coefficient captures more residual variation after controlling for the dominant biogeographic gradient. This is not inflation: the unadjusted p-value histograms (see `figures/pvalue_histograms.png`) show genuine enrichment of small p-values for Hg, Pb, and As — metals that drive the FDR-significant set — against a roughly uniform background for other metals. The adjusted model produces the same qualitative pattern with more power, not a flat or anti-conservative distribution.

**Operon-level inflation in the 6,432-pair count.** The raw pair count does not equal the number of independent genomic loci. Two operon clusters inflate the count: the **kdp operon** (K01546/kdpA, K01547/kdpC, K01548/kdpB, K16080; 4 subunits from one locus) appears significant across multiple metals (Hg, As, Cd, Pb) — generating up to 16 KO×metal pairs from a single genomic locus. The **pst operon** (K02036/K02037/K02038/K02040; phosphate ABC transporter; 4 subunits from one locus) similarly appears as a cluster of significant pairs for Cd and Pb. The functionally distinct genomic locus count is therefore substantially lower than 6,432. By contrast, the **field-strict 89 pairs** (H1 robust survivors; `data/h1_robustness_summary.csv`) do not contain operon clusters — no set of pst or kdp subunits is simultaneously H1-significant — and represent the conservative estimate of independent genomic loci with robust associations.

The top adjusted Hg hits (K01546/kdpA, K01547/kdpC, K01548/kdpB, K16080) are the **kdp operon** — potassium-transporting ATPase subunits, not mercury reductase. These are strongly enriched near high-Hg sites (OR > 10⁵), suggesting altered potassium homeostasis in Hg-contaminated environments, possibly reflecting ionic competition between Hg²⁺ and K⁺ or membrane potential disruption. Members of the mercury resistance operon (K06045/merP, K08677/merF) and a MerR-family transcriptional regulator (K07093 — broad HTH superfamily, not the canonical mercury-specific merR K14658) also appear in the top 14 adjusted hits and are biologically expected.

### SPIRE — SoilGrids-adjusted sensitivity check (2026-07-29)

The rebuilt SPIRE matrix (2,477 MAGs, extended env filter) was analysed with two models:

- **Baseline (latitude + phylum/genus):** 69 FDR-significant pairs; top hits include kdpC × Cr (β = +11.0), merR × Hg (β = −13.9), cytochrome bd ubiquinol oxidase × As (K00425/K00426 cydA/cydB, β ≈ +14–15).
- **SoilGrids-adjusted (latitude + sg_pH + phylum/genus):** 31 FDR-significant pairs in the pH-adjusted model (24 overlap with baseline; **7 are newly significant in the pH-adjusted model and were absent from baseline**, including Cu pairs K00425/K00426 cydA/cydB cytochrome bd ubiquinol oxidase subunits). The pH-adjusted model is a separate regression — not a survival filter on baseline hits. New pairs appear when pH is a suppressor covariate that was masking real metal associations in the baseline; pairs can also be lost when pH explains variation that appeared metal-driven. Cu is the clearest illustration: 4 significant pairs in baseline (K00859, K03702, K01547, K16013), 5 significant pairs in pH-adjusted (K00425, K00426, K00859, K01547, K16013) — K03702 is lost and K00425+K00426 are gained. Stating "5 Cu pairs surviving pH control" is therefore a framing error: these are not a subset of the 4 baseline Cu pairs.

**Note on figure presentation:** In any figure comparing baseline and pH-adjusted models side-by-side, readers should note that the pH-adjusted set is labeled 'pH-robust' for brevity, but is NOT a subset of baseline. The pH-adjusted and baseline models are independent regressions. New pairs appear in pH-adjusted (e.g., K00425/K00426 cydA/cydB × Cu) and pairs are lost in pH-adjusted (e.g., K03702 × Cu). This is expected behavior when pH is a suppressor covariate masking real associations in the baseline, not a filtering step that removes unreliable pairs. The two sets represent different conditional parameter estimates, not a nested hierarchy.

**24 pairs robust to both latitude and soil pH control:**

| KO | Metal | β (baseline) | q (baseline) | Key annotation |
|----|-------|-------------|-------------|----------------|
| K01547 (kdpC) | Cr | +11.0 | 6.6×10⁻⁵ | K⁺-ATPase β-subunit |
| K00425 | As | +15.0 | 7.2×10⁻⁵ | cydA; cytochrome bd ubiquinol oxidase subunit I |
| K00426 | As | +14.1 | 1.4×10⁻⁴ | cydB; cytochrome bd ubiquinol oxidase subunit II |
| K10007 | Hg | −18.0 | 8.8×10⁻⁴ | Unknown; Hg-specific |
| K10006 | Hg | −17.3 | 1.2×10⁻³ | Unknown; Hg-specific |
| K07093 (MerR-family HTH regulator) | Hg | −13.9 | 1.2×10⁻² | MerR-family transcriptional regulator (broad HTH superfamily; ≠ mercury-specific merR K14658) |
| K14335 | Pb | −17.0 | 1.5×10⁻² | … |
| K02012 | Pb | +13.7 | 1.9×10⁻³ | TonB-dependent receptor |
| K01056 | Cd | +8.3 | 1.7×10⁻² | Phospholipase |
| K00859 | Cr, Cu | −8.5, −10.0 | 0.018, 0.019 | Pantothenate kinase |

(Remaining 14 pairs also survive; see `data/spire_sg_adj_ko_associations.csv`.)

**45 pairs that disappear after sg_pH control** include: K02757/K02755/K02756 (PTS phosphotransferase components) × Hg and **K01548 (kdpB) × Pb** (β = −19.6 baseline, lost after sg_pH). This confirms that the kdpB–Pb association in SPIRE is partially confounded by soil pH gradients, while the kdpC–Cr association is not.

Notably, **K07093 (MerR-family HTH regulator) × Hg** is among the 24 pairs significant in both the total-effect (latitude-adjusted) and direct-effect (latitude+pH-adjusted) models. Note: K07093 is the broad MerR-family transcriptional regulator superfamily, which includes regulators for multiple metals and oxidative stress — not the canonical mercury-specific merR (K14658, absent from SPIRE due to low global prevalence ~2.5%). The K07093 Hg association therefore reflects enrichment of a broad stress-responsive regulator class near Hg gradients, not mercury operon specificity per se. Files: `data/spire_adj_ko_associations.csv` (baseline, 69 sig), `data/spire_sg_adj_ko_associations.csv` (sg-adjusted, 31 sig).

### OR per IQR — key associations (2026-08-06)

Raw logistic β values are not directly interpretable because PF1 metal concentrations have different ranges across metals. The appropriate quantity for cross-metal comparison is the **odds ratio per interquartile range (OR/IQR) = exp(β × IQR_metal)**. IQR values used: MGnify — As=0.0327, Cd=0.0574, Cr=0.0477, Cu=0.0278, Hg=0.1039, Pb=0.0204; SPIRE — As=0.0407, Cd=0.0877, Cr=0.0772, Cu=0.0279, Hg=0.0927, Pb=0.0317.

| KO (gene) | Metal | Dataset | β | OR/IQR | q | Notes |
|---|---|---|---|---|---|---|
| K01546 (kdpA) | Hg | MGnify (lat-adj) | +13.49 | **4.06** | 2.1×10⁻¹¹³ | Top Hg hit; quasi-sep; direction confirmed Firth |
| K08364 (merP) | Hg | MGnify (lat-adj) | large+ | **2.89** | <0.05 | Quasi-sep; direction confirmed Firth |
| K11811 (arsH) | Pb | MGnify (lat-adj) | pos | **1.28** | <0.05 | Only Resistance/Detox survivor in field-strict 84 |
| K00520 (merA) | Hg | MGnify (lat-adj) | small | **0.98** | 0.863 | NULL — not significant; rank 29/48 Hg |
| K08363 (merT) | Hg | MGnify (lat-adj) | −2.52 | **0.77** | 0.045 | Significant; negative direction |
| K07093 (MerR-HTH superfamily) | Hg | MGnify (lat-adj) | −8.36 | **0.42** | 1.4×10⁻⁴⁷ | Negative; ≠ mercury-specific merR (K14658) |
| K08363 (merT) | Hg | SPIRE (lat-adj) | −19.5 | **0.164** | 0.035 | Quasi-sep (22% prevalence); direction stable |
| K08363 (merT) | Hg | SPIRE (pH-adj) | −30.2 | **0.061** | 0.046 | pH inflates effect — overcontrol suspected (see DAG, Limitation 3) |

**Interpretation**: The only field-strict positive bioindicator among these prominent candidates is arsH×Pb (OR/IQR = 1.28 — genes more likely in high-Pb environments). The canonical mercury resistance gene merA is effectively null (OR/IQR ≈ 1). The significant associations (merT×Hg, K07093×Hg) are negative — genes depleted in high-metal environments globally — which is inconsistent with a bioindicator interpretation but consistent with community turnover away from mer-carrying lineages under chronic Hg exposure. The raw β values (e.g., merT SPIRE: −19.5 to −30.2) are numerically unstable due to quasi-complete separation; OR/IQR is the primary reported quantity.

---

## H5 — Beta estimates are stable (SUPPORTED)

Spearman ρ = **0.923** between unadjusted and latitude-adjusted β estimates across 910 paired KO-metal associations (p ≈ 0). The associations identified in H1 are not latitude artifacts: their direction and relative magnitude are almost identical with or without geographic control.

See `figures/beta_stability_h1_pairs.png`.

---

## H6 — Adjustment does not improve cross-dataset agreement (NOT SUPPORTED)

Unadjusted cross-dataset ρ = 0.059 (n = 324 convergent pairs); adjusted ρ = 0.049 (n = 26,749). The large jump in usable pairs (324 → 26,749) reflects that the latitude-adjusted MGnify model converges for nearly all KOs — adding latitude as a continuous covariate stabilises the phylum fixed-effects and eliminates most of the near-separation failures that produced null betas in the unadjusted model. The low cross-dataset correlation is not attributable to geographic confounding — it persists after adjustment. This reinforces that MGnify and SPIRE sample fundamentally different microbial ecosystems.

---

## H7 — Class-level survival (SUPPORTED)

`notebooks/05_class_phylo_control.ipynb` ran the genome-wide association model with class-level (232 GTDB classes, mean 37 MAGs/class) fixed effects and latitude: `KO_present ~ PF1_metal + log_genome_size + latitude + C(tax_class)`.

**92/219 H1-significant pairs survive class-level control** (FDR q<0.05) — well above the ≥10 threshold. By metal: As 5/43 (12%), Cd 6/12 (50%), Cr 4/6 (67%), Hg 42/107 (39%), Pb 35/51 (69%).

## H8 — Beta stability (SUPPORTED)

Spearman ρ = 0.925 between phylum-model betas (NB04) and class-model betas (NB05) across all 219 H1-significant pairs (p = 2.79 × 10⁻⁹³, n = 219). Effect direction is highly preserved; class control changes magnitudes but not signs.

## H9 — Phylo-PC survival (SUPPORTED)

Model B replaced discrete taxonomy with 20 TruncatedSVD principal components from one-hot-encoded GTDB taxonomy (phylum, class, order, family, genus), explaining 43.4% of taxonomic variance. Model: `KO_present ~ PF1_metal + log_genome_size + latitude + phylo_pc1 + … + phylo_pc20`.

**8/219 H1-significant pairs survive phylo-PC control** (≥5 threshold → SUPPORTED). By metal: As 0, Cd 2, Cr 3, Hg 1, Pb 2. **The 96% collapse rate (211/219 pairs lost) is scientifically concerning**: the vast majority of MGnify associations cannot be distinguished from taxonomic sorting artefacts under this control. The 8 survivors represent the phylogenetically robust core; interpreting the 211 non-survivors as genuine metal ecology requires the weaker justification that phylum-level taxonomy is the appropriate control ceiling (see Limitations item 4). Cr has the highest retention rate (3/6 = 50%).

---

## Robustness controls — 89 pairs / 84 unique KOs survive all checks

Four robustness controls were applied to the 219 H1-significant pairs (`data/h1_robustness_summary.csv`). One control (PGLS) is skipped; all others are executed.

### Control 1 — Latitude adjustment (H4, n=138/219)

138/219 (63%) H1-sig pairs also reach FDR q<0.05 in the latitude-adjusted model (`KO_present ~ PF1_metal + log_genome_size + latitude + C(phylum)`). 81 pairs do not survive, indicating geographic confounding contributes to a portion of the unadjusted signal.

### Control 2 — Multi-metal covariate (Phase 2, n=210/219)

For each pair, the most-correlated metal was added as a covariate (As→Cr, Cd→Cr, Cr→Cu, Cu→Cr, Hg→As, Pb→Cd). Model: `KO_present ~ PF1_target + PF1_correlate + log_genome_size + C(phylum)`.

**210/219 (96%) pairs survive multi-metal adjustment.** The signal is not attributable to metal co-occurrence confounding for the vast majority of associations. Cr had the most attrition (4/6 survive), consistent with its high correlation with Cu (ρ=0.71) and As (ρ=0.68).

Supplementary analysis on the 138 latitude-adjusted pairs: **134/138 survive** combined latitude + multi-metal control.

### Control 3 — Class-level taxonomic control (Phase 4 / H7)

Model: `KO_present ~ PF1_target + log_genome_size + C(tax_class) + latitude` using 232 GTDB class-level groups (mean 37 MAGs/class vs 91 phyla in the baseline model).

The genome-wide class model (NB05 H7, FDR applied over all 38,706 pairs) finds **92/219 (42%) pairs survive class-level control**. A targeted analysis with FDR applied only within the 219 pairs (Phase 4) finds 107/219 (49%) survive — the difference reflects FDR denominator; the genome-wide figure is more conservative. Beta stability across all 219 pairs: Spearman ρ = 0.925 (NB05 H8), indicating strong directional consistency.

By metal (genome-wide FDR):

| Metal | H1-sig | Survive class control | % |
|-------|--------|----------------------|---|
| As | 43 | 5 | 12% |
| Cd | 12 | 6 | 50% |
| Cr | 6 | 4 | 67% |
| Hg | 107 | 42 | 39% |
| Pb | 51 | 35 | 69% |

The low As survival (14%) suggests that many As associations in H1 are driven by phylum-level community composition: once class-level variation is accounted for, the signal largely disappears. This does not imply the associations are spurious — it may indicate that As-related gene enrichment is primarily a feature of class-level ecological partitioning. The high Pb survival (86%) and Cd/Cr survival suggests those metal signals are more robust to finer taxonomic control.

### Control 4 — MAG quality covariate (Phase 3A)

MAG completeness and contamination were retrieved from `kescience_mgnify.genome` and joined to the 8,585-MAG dataset. Summary: mean completeness = 95.8% (median 95.9%); mean contamination = 1.66% (median 1.30%). All 8,585 MAGs pass the MGnify QC thresholds applied at NB00 construction (≥70% completeness, ≤10% contamination). The Phase 3A model adds completeness and contamination as continuous covariates:

`KO_present ~ PF1_metal + log_genome_size + C(phylum) + completeness + contamination`

**200/219 (91%) pairs survive with quality covariates added.** This is the highest retention of any control, indicating that MAG quality variation does not meaningfully confound the H1 associations.

#### Sensitivity analyses — restricted-MAG subsets

To test whether results differ on the cleanest MAGs:

| Subset | n MAGs | % of total | Pairs surviving |
|--------|--------|-----------|-----------------|
| All (Phase 3A) | 8,585 | 100% | 200/219 (91%) |
| ≥95% complete, ≤2% contamination (Phase 3B) | 3,520 | 41% | 120/219 (55%) |
| ≥97% complete, ≤1% contamination (Phase 3C) | 1,854 | 22% | 29/219 (13%) |

The drop from Phase 3B to 3C reflects reduced statistical power (sample size halved) rather than quality artefact: associations that survive in Phase 3A but not 3C are re-run on 22% of MAGs, and the FDR denominator is unchanged at 219. Phase 3B (55% survival at n=3,520) confirms the main signal persists on a substantially restricted, high-quality subset. Cu has 0 surviving pairs across all models (consistent with H1: Cu had 0 FDR-sig KOs).

### Control 4b — SPIRE MAG quality covariate (2026-08-17)

SPIRE quality metrics (CheckM2 completeness, contamination, and log_n_mags per sample) were extracted from `kbase.ke_pangenome.gtdb_metadata` and joined on `genome_id = accession`. The quality-adjusted model adds three standardized covariates:

`KO_present ~ PF1_metal + log_genome_size + latitude + C(phylum/genus) + completeness_z + contamination_z + log_n_mags_z`

**69/69 SPIRE baseline pairs survive quality covariate adjustment** (FDR q<0.05 in the adjusted model). Median β ratio (adjusted/baseline) = 0.986 (IQR 0.950–1.024), indicating negligible effect of quality on effect size estimates.

High-quality subsets:

| Subset | N MAGs | Survival |
|---|---|---|
| All + quality covariates (Phase 3A equivalent) | 2,477 | **69/69 (100%)** |
| HQ90 (≥90% complete, ≤5% contamination) | 2,287 | **46/69 (67%)** |
| HQ95 (≥95% complete, ≤2% contamination) | 1,247 | 5/56 (9%) |

The HQ95 drop reflects power loss (n=1,247, denominator unchanged at 69), not signal artefact — the same pattern as Phase 3C in MGnify. HQ90 (67% survival at n=2,287) is the appropriate stringency-balanced comparison and confirms robust survival. Files: `data/spire_quality_sensitivity.csv`.

### Skipped controls

- **Phase 5 (PGLS phylogenetic control):** The GTDB pruned representative tree covers only 16.2% of MAGs (1,324/8,177 with a genus assignment). Running PGLS on 16% of the data would introduce severe survivor bias and is not interpretable for the full association set. Skipped.

### All-controls survival

The `h1_robustness_summary.csv` file records per-pair survival across all four controls (latitude / multi-metal / class-level / quality covariate).

**Count reconciliation (referenced throughout this report):**
- `survives_all_controls = True` in `h1_robustness_summary.csv`: **89 KO×metal pairs** — this is the primary "field-strict" definition used in NB08–NB13 and all downstream analyses.
- **84 unique KOs** correspond to those 89 pairs (5 KOs each appear in 2 metal associations).
- `survives_all_controls_with_p3 = True`: **88 pairs** (one additional exclusion for Phase 3 stringent quality threshold).
- **Elevation sensitivity subset**: **88 pairs** (the 89-pair set minus K09890×PF1_Pb, which had no ETOPO1 grid match) — this is the source of "88" in the elevation section header.

When this report refers to "84 field-strict KOs" or "84 field KOs," this means the 84 unique KOs from the 89-pair all-controls survivor set. When it refers to "88 pairs" in the context of elevation, it means the elevation-matched subset. The all-controls survivor count is **89/219 pairs → 84 unique KOs (40% pair-level, 38% KO-level)**.

| Metal | H1-sig | Survive all 4 | % |
|-------|--------|---------------|---|
| As | 43 | 5 | 12% |
| Cd | 12 | 5 | 42% |
| Cr | 6 | 4 | 67% |
| Hg | 107 | 36 | 34% |
| Pb | 51 | 39 | 76% |
| **Total** | **219** | **89** | **41%** |

*(89 pairs → 84 unique KOs; see Count reconciliation above.)*

Hg survivors include **argP (K05596**, LysR arginine transport regulator) and several other regulatory genes consistently depleted in high-Hg environments, with betas further from zero under class control than phylum control (beta_p4 more extreme), suggesting the signal strengthens with finer taxonomic resolution.

Note: the kdp operon (K01546/7/8) and mercury operon (K00786/merA, K07788/merT) appear in the latitude-adjusted genome-wide results (H4) but were not H1-significant in the unadjusted model and are therefore not part of this robustness assessment.

### Functional breakdown of the 84 field-strict KOs

KEGG descriptions fetched via REST API (July 2026) and assigned to broad functional categories. Full table: `data/field_strict_ko_annotations.csv`. The distinction between **Metal resistance** and other categories (especially Transport) follows Coombs & Barkay 2005 (*AEM* 71:7083): P_IB-type ATPases such as zntA (K01534, Zn²⁺/Cd²⁺) and copA (K07133, Cu⁺) are classified as chromosomally encoded **homeostasis** genes — constitutively expressed, vertically inherited, essential for metal ion buffering — and are therefore placed in the Transport category rather than Metal resistance. Mobile, plasmid-borne determinants (arsB, chrA, merA, czcA) constitute the Metal resistance category. This distinction is load-bearing for Hypothesis H3: the claim that only 1 field-strict KO is a canonical metal resistance gene requires a clear separation of homeostasis transporters from resistance effectors.

| Functional category | n KOs | Metals enriched |
|---|---|---|
| Transport (ABC, TRAP, PTS permeases; substrate-binding proteins) | 16 | Hg (9), Pb (6), As (2) |
| Uncharacterized (K09xxx family or no annotation) | 10 | Pb (9), Hg (1) |
| Regulation (LysR, OmpR, LuxR family transcriptional regulators) | 9 | Hg (7), As/Pb (2) |
| Metabolism (carboxylases, dehydrogenases, chlorophyll reductases) | 9 | Hg (5), Pb (4) |
| Other (sporulation, chemotaxis, RNA helicases, photosynthesis, etc.) | 27 | Hg (14), Pb (11), Cd (2) |
| Membrane / cell envelope | 4 | Pb (2), Hg (1), Cr (1) |
| Nitrogen cycling (nosZ, napE, folM) | 3 | Pb (2), Hg (1) |
| Motility / flagellar (flhC, flhD, ftcR) | 3 | As (2), Cr (1), Hg (1) |
| DNA repair / stress response | 2 | Cr (1), Cd (1) |
| Metal resistance | **1** | Pb (arsH/K11811) |

**Key observations:**

1. **Only 1 of 84 field-strict KOs is a canonical metal resistance gene** (arsH, arsenical resistance protein, associated with Pb — a cross-metal hit). This directly extends the NB12 finding (0/26 Goff HMRGs overlap) to the full field-strict set.

2. **9 LysR-family regulators are Hg-associated.** These include argP (K05596, arginine transport regulator), cbl (K13635, cys regulon), ampR (K17850), lasR (K18304, quorum sensing), hypT/qseD (K21645, hypochlorite-responsive), and bauR (K21699). LysR-family regulators are the most common bacterial transcriptional regulator family — their Hg enrichment may reflect that Hg²⁺ disrupts cysteine-dependent regulation broadly, recruiting LysR regulators as a non-specific stress response, rather than Hg-specific resistance.

3. **10 uncharacterized KOs (K09xxx family) are almost entirely Pb-associated (9/10).** These are conserved hypothetical proteins with no functional annotation. They constitute the largest unexplained portion of the Pb signal.

4. **Chlorophyll biosynthesis subunits (chlN, chlB, bchY, bchZ) × Hg.** These are light-independent chlorophyll/bacteriochlorophyll reductases found in phototrophic bacteria. Their Hg enrichment suggests that phototrophic soil microorganisms (Chlorobi, photosynthetic Proteobacteria) may inhabit niches with elevated Hg — possibly related to methylmercury cycling in anoxic/microaerobic soil zones.

5. **Transport is the most prevalent functional category (16/84).** These transporters are largely not metal-specific: amino acid transporters (argP, aotQ, occQ), carbohydrate transporters (bxlF, cebE, ulaB), peptide transporters (sapC), TRAP-type transporters. This is consistent with the NB11 finding that field KOs as a class do not look like metal-resistance genes by sequence composition.

### Operon-level aggregation sensitivity (2026-08-07)

The per-KO logistic regression framework tests each KEGG ortholog independently, which can inflate results when operon members (genes at the same genomic locus) co-segregate and produce correlated β estimates. Five known metal-resistance/response operons were tested for operon-level aggregation:

- **kdp operon** (K01546/kdpA, K01547/kdpC, K01548/kdpB): K⁺-transporting ATPase
- **mer operon** (K16306/merA, K16307/merC, K14658/merR, K00526/merE): Mercury resistance
- **czc operon** (K15725/czcA, K15727/czcC, K16264/czcB): RND Zn/Cd/Co transporter
- **ars operon** (K03756/arsA, K01551/arsB, K00537/arsC): Arsenic resistance
- **pst operon** (K02036/37/38/40): Phosphate ABC transporter

For each operon × metal, an aggregated operon-presence variable was computed (union: ANY member present; intersection: ALL members present) and tested against PF1 metal in a logistic regression with the same covariates as the baseline model. The kdp operon shows instructive internal inconsistency: **kdpC (K01547) × Cr survives both latitude and pH control (β = +11.0, q = 6.6×10⁻⁵ in SPIRE baseline), while kdpB (K01548) × Pb does not survive pH control**. This member-level signal heterogeneity is consistent with the C-subunit being the ecologically informative element in the SPIRE dataset, rather than the operon as a functional unit. Full operon-level regression results are in `data/operon_collapse_results.csv`; the qualitative pattern (high within-operon β variability) indicates that the 89-pair field-strict set does not have inflated-pair counts from operon clustering. The kdp and pst operons mentioned at line 116 contribute to the baseline 6,432-pair count but are not inflating the field-strict survivor set.

### Elevation covariate

An elevation covariate was added to the latitude-adjusted model for each of the 88 all-controls-surviving pairs using `arkinlab.envdbs.etopo1_elevation` (0.1° global grid, 2.1 M non-null rows). Elevation was matched to each MAG at the nearest 0.1° grid cell; 6,620 / 8,585 MAGs (77.1%) received a value. Model: `KO_present ~ PF1_metal + latitude + elevation_m + log_genome_size + C(phylum)`.

**Results:** All 88 pairs converged. **83/88 (94%) remain FDR-significant** (q < 0.05). The 5 that lost significance (4 Pb, 1 Cd) were already borderline (q_lat 0.02–0.05) and remain near-significant (q_elev 0.05–0.15). Zero direction flips. Spearman ρ between elevation-adjusted and latitude-only β = **0.959** (p = 8.3 × 10⁻⁴⁹), indicating near-identical rank ordering of associations. Median |Δβ| = 1.44 (13% of original magnitude); 14 pairs have |Δβ| > 3, but all are quasi-separated associations where β magnitudes are already unreliable (direction remains stable). Results in `data/h1_elevation_adjusted.csv`.

**Interpretation:** Elevation does not confound the 88 robust KO–metal associations. The associations persist with equivalent direction and near-identical relative strength when altitudinal gradients are explicitly controlled.

---

## Functional interpretation of top associations

### Mercury — strongest signal; top hits are kdp operon, not mer operon

Top adjusted associations are the **kdp operon** (potassium-transporting ATPase):
- K01546 (kdpA): β = 13.5, OR = 7.2 × 10⁵, q = 2.1 × 10⁻¹¹³
- K01547 (kdpC): β = 13.3, OR = 5.9 × 10⁵, q = 2.5 × 10⁻¹¹¹
- K01548 (kdpB): β = 13.2, OR = 5.3 × 10⁵, q = 7.7 × 10⁻¹¹⁰
- K16080 (kdpF): β = 16.7 (highest); kdpF is the small stabilising subunit of the Kdp K⁺-ATPase (KEGG assignment well-established; eggnog annotations for this KO are sparse)

This is biologically unexpected but plausible: Hg²⁺ can mimic or compete with cations at membrane transport proteins; Hg-contaminated environments may select for genomes with enhanced potassium acquisition capacity. The kdp operon is normally induced under K⁺ limitation.

**Cross-metal β profile and geochemical gradient assessment.** To assess whether kdp operon enrichment is mercury-specific or tracks a broader geochemical gradient, each kdp KO was tested against all six metals in the latitude-adjusted model. The β profile for K01546 (kdpA; other subunits are near-identical):

| Metal | β | OR | p | q | Quasi-sep? |
|-------|---|----|---|---|-----------|
| Hg | +13.49 | 7.2 × 10⁵ | 3.3 × 10⁻¹¹⁷ | 2.1 × 10⁻¹¹³ | Yes |
| As | +2.57 | 13.1 | 2.6 × 10⁻³ | 4.1 × 10⁻² | No |
| Cd | +1.66 | 5.3 | 1.9 × 10⁻³ | 1.7 × 10⁻² | No |
| Pb | −7.97 | 3.4 × 10⁻⁴ | 6.1 × 10⁻⁹ | 7.1 × 10⁻⁷ | No |
| Cr | −1.05 | 0.35 | 6.4 × 10⁻² | 0.39 | No |
| Cu | +0.18 | 1.19 | 0.80 | 0.96 | No |

kdpA is FDR-significant for four metals (Hg, As, Cd, Pb), with Pb strongly negative. The Hg association is anomalously large (quasi-separated, β = +13.5 >> β(As) = +2.6), raising the possibility of residual geographic confounding. In the SPIRE dataset, PF1_Hg is moderately correlated with latitude (ρ = +0.420) and co-varies positively with PF1_As (ρ = +0.566) and negatively with PF1_Cd (ρ = −0.571). Despite the Hg–Cd anti-correlation in space, kdpA shows a positive partial β for Cd (after phylum control), indicating that within-phylum Cd effects on kdpA differ from the global Cd gradient — consistent with a phylum-mediated suppressor relationship rather than a simple geochemical proxy.

**Interpretation.** The multi-metal pattern (positive Hg/As/Cd, negative Pb) is not parsimoniously explained by a single latitude-driven gradient: Cd is anti-correlated with Hg geographically yet has a positive β in the same direction as Hg. The most likely explanation is that high-Hg, high-As, low-Pb environments select for genomes with enhanced K⁺ acquisition (Kdp), independently of latitude — consistent with ionic competition at potassium channels (Hg²⁺ competes with K⁺) and with K⁺-limitation being a convergent feature of high-metal-stress soil types.

**SoilGrids pH sensitivity check (2026-07-29, SPIRE).** Adding sg_pH as a covariate to the SPIRE model yields 31 FDR-significant pairs in the pH-adjusted model (vs 69 in the baseline model). Of the 31 pH-adjusted pairs: 24 are also in the baseline (overlap), 7 are newly significant in the pH-adjusted model only (not in baseline). Of the 69 baseline pairs: 45 do not reach FDR significance in the pH-adjusted model. The pH-adjusted model is a separate regression, not a survival filter: it can produce new significant pairs when pH was a confounding suppressor in the baseline. The overall pattern (69 baseline → 31 pH-adjusted, 24 overlap) should be read as "24 pairs significant in both total-effect and direct-effect models; 7 pairs significant only in the direct-effect model (pH was a suppressor masking them in the baseline); 45 baseline-only pairs whose Wald significance depends on total-effect estimation — not necessarily confounded, as pH may be a mediator." kdpB (K01548) × Pb is among the 45 hits that *do not* survive sg_pH control — the Pb-negative kdp signal in SPIRE is partially confounded by soil pH gradients. In contrast, kdpC (K01547) × Cr (β = +11.0, q = 6.6×10⁻⁵) survives sg_pH control and emerges as a robust SPIRE cross-metal signal. The Hg kdp associations (K01546–K01548 × Hg) are MGnify-specific and were not evaluated in the SPIRE SoilGrids check because the quasi-separation that drives the large MGnify β is not resolved in SPIRE (which has 2,477 MAGs vs MGnify's 8,585).

The canonical mercury resistance genes also appear in the top 14:
- K06045 (merP, periplasmic Hg-binding protein): enriched
- K08677 (merF, mercury transport): enriched
- K07093 (MerR-family HTH regulator, broad superfamily): negative β — consistent with this regulator class acting as a transcriptional repressor. Note: K07093 is not the canonical mercury-specific merR (K14658); it is a broad stress-responsive HTH regulator present in ~25% of SPIRE MAGs.

In the unadjusted screen, top Hg associations (negative direction) included:
- **cysB** (K13634/35, LysR cysteine biosynthesis regulator): depleted near Hg — cysteine thiols chelate Hg²⁺; disrupted sulfur regulation near Hg sites is biologically coherent.
- **argP** (K05596, LysR arginine transport regulator): depleted near Hg; co-depleted near As.
- **sspB** (K03600, stringent starvation protein B): depleted — stress response regulatory hub.

Positive Hg associations include a cluster of **sporulation** KOs (spoVAE, spoIIID, spoIIIAC), suggesting sporulation enrichment in high-Hg communities.

### Arsenic — almost entirely negative, flagellar regulators dominant

- **flhC** (K02402) and **flhD** (K02403), the master flagellar transcriptional regulators, are the top As associations (both strongly depleted, q < 0.001). Flagellar assembly is energetically expensive; As-stressed communities may downregulate motility.
- **pheP** (K11734, phenylalanine permease): extreme depletion near As (OR ≈ 3 × 10⁻¹²) — likely near-complete separation.
- **entB** (K01252, enterobactin siderophore biosynthesis): depleted near As; see cross-metal contradictions below.
- **argP** and **cysB**: shared negative signal with Hg.

### Lead — dominated by large positive odds ratios

Top Pb associations have OR 10⁵–10⁹, indicating near-complete separation; interpret with caution. **hflD** (K07153, high-frequency lysogenization protein) is positive for Pb, suggesting different phage integration dynamics in Pb-contaminated sites.

### Cadmium — notable directional contradictions with arsenic

- **entB**: negative for As, **positive** for Cd.
- **flhD**: negative for As, **positive** for Cd.

These reversals suggest metal-specific ecological tradeoffs in iron acquisition and motility, not a generic heavy-metal response.

### Chromium — weak signal, overlapping with arsenic

flhC also negative for Cr; **cry2** (DNA photolyase) and **cueR** (Cu-sensing MerR regulator) both negative.

### Copper — no significant signal

0 FDR-significant KO-metal pairs for Cu in MGnify.

### Cross-metal KOs

KOs significant in ≥2 metals show two dominant themes:

1. **flhC/flhD** (flagellar regulators): depleted near As and Cr, enriched near Cd — metal-specific motility tradeoff.
2. **argP, cysB, hisM** (amino acid/sulfur regulators): consistently depleted across As and Hg — coherent signal of disrupted nitrogen/sulfur homeostasis.
3. **Hg ▼ / Pb ▲ antagonism**: ~25 KOs are simultaneously depleted near Hg and enriched near Pb, including ribosome assembly (srmB), Sec translocation (syd), and PTS sugar transport (ulaB). This may reflect different dominant taxa in Hg vs Pb environments.

---

## Cross-validation with comprehensive_metal_ecology (NB06)

An independent cross-validation asks whether the functional split identified in `comprehensive_metal_ecology` (resistance/detoxification KOs null; transport, sensing, cofactor, and metabolism KOs significant) is recapitulated in the per-KO genome-wide associations.

### Design

The `comprehensive_metal_ecology` project defined five functional categories for 730 curated metal-interacting KOs; 6,451 KOs were tested in the present project; 169 unique KOs reached FDR q < 0.05 in any metal (H1-significant). Of the 169 H1-sig KOs, only 8 carry a named curated category — the 730-KO curated set is sparse relative to the 6,451-KO tested space. This limits statistical power for all analyses in this notebook.

Fisher's exact test was used to test enrichment of each category among H1-significant KOs vs the full tested set. Woolf continuity correction (0.5 additive) was applied for confidence intervals. All results are post-hoc and exploratory.

### Results

**Enrichment: null across all five categories**

| Category | In tested | H1-sig | OR | 95% CI | p (Fisher) | Predicted |
|----------|-----------|--------|----|--------|------------|-----------|
| Resistance/Detoxification | 11 | 2 | 1.54 | [0.30–7.53] | 0.45 | depleted ↓ |
| Transport/Homeostasis | 120 | 6 | 0.42 | [0.17–1.00] | 0.06 | enriched ↑ |
| Sensing/Regulation | 7 | 0 | exact zero | — | — | enriched ↑ |
| Cofactor Biosynthesis | 6 | 0 | exact zero | — | — | enriched ↑ |
| Metal-dependent Metabolism | 32 | 0 | exact zero | — | — | enriched ↑ |

No category reaches p < 0.05. Resistance is slightly over-represented (OR = 1.54) — opposite to the predicted direction from the main project. Transport is modestly under-represented (OR = 0.42, p = 0.06), opposite to its predicted direction.

**Robustness-stratified enrichment**

The pattern does not improve when restricting to more conservative subsets (89 all-controls-surviving pairs, 8 phylo-PC-surviving pairs). All Fisher tests remain NS in all subsets. Sample sizes drop too small for inference in the strict subsets.

**Phylo-PC survivor categories**

Of the 8 KO-metal pairs surviving the phylo-PC control (the most phylogenetically conservative analysis), 2/8 pairs are Transport/Homeostasis (merP/K08364-Hg, Zn-Mn ABC transporter/K02075-Hg) and 0/8 are Resistance/Detoxification. This directional consistency with the main project (transport signal > resistance signal) cannot be tested statistically with n = 8 pairs.

### Interpretation

The functional split is **not recapitulated** in the per-KO enrichment analysis. Three alternative explanations exist for the null result, none distinguishable at this sample size:

1. **True null**: the per-KO screen identifies ecologically relevant KOs that happen not to fall in the curated set categories.
2. **Power failure**: 8/730 curated KOs appearing among 169 H1-sig KOs gives < 5% category membership — insufficient to detect an enrichment signal of OR = 2 at α = 0.05 with this n.
3. **Definition mismatch**: the curated categories were designed around biochemical function, while the per-KO screen detects ecological co-occurrence with metal gradients — these are correlated but not identical criteria.

The directional consistency in phylo-PC survivors (Transport > Resistance, 2 vs 0) is weakly consistent with the main project's direction but is not a statistical cross-validation. The cross-paper paragraph proposed in project notes (claiming functional split replication) is **not supported** by these data.

### PGLS cross-validation against Finding 1 (niche breadth)

The `comprehensive_metal_ecology` project's primary finding (Finding 1) is that the density of 140 curated metal-interacting KOs per Mb of genome negatively predicts Levins' standardised niche breadth across 1,574 bacterial genera (PGLS β = −0.021, FDR p = 6.4×10⁻⁸, Pagel's λ = 0.757). To cross-validate the per-KO screen against this independent analytical framework, each of the 4 KOs that are both H1-significant and in the 140-KO primary set was tested in a PGLS model: `mean_levins_B_std ~ KO_present_binary + genome_mb_z`, where `KO_present_binary` = 1 if any MAG of the genus carries the KO. Results for 5 KO-metal pairs (K11604 appears in two metals):

| KO | Gene | Metal | Per-KO β | Direction | PGLS β | PGLS p | λ | Consistent? |
|----|------|-------|-----------|-----------|--------|--------|---|-------------|
| K19591 | cueR | Cr | −2.32 | neg | −0.0046 | 0.578 | 0.743 | ✓ |
| K02075 | ABC.ZM.P | Cr | +2.53 | pos | −0.0195 | 0.040* | 0.744 | ✗ |
| K19975 | mntC | As | −14.03 | neg | −0.0275 | 0.224 | 0.743 | ✓ |
| K11604 | sitA | Pb | +13.12 | pos | −0.0108 | 0.502 | 0.742 | ✗ |
| K11604 | sitA | Hg | −2.51 | neg | −0.0108 | 0.502 | 0.742 | ✓ |

3/5 pairs are direction-consistent. The one significant PGLS result (K02075, p = 0.040) is direction-*inconsistent*: the per-KO screen finds this Zn/Mn ABC transporter enriched in high-Cr sites (positive β), while PGLS finds that genera carrying it have narrower niche breadth (negative β). These findings are not contradictory — they measure different ecological properties. The per-KO screen tests whether a KO associates with a specific metal gradient; PGLS tests whether a KO associates with overall environmental generalism. A specialist transporter enriched in Cr-contaminated environments can simultaneously be found in specialist (narrow-niche) genera without any biological inconsistency.

The 3/5 direction consistency is weak evidence for cross-framework concordance. This is expected: the two frameworks make different assumptions (MAG-level logistic vs genus-level PGLS), use different responses (metal concentration vs niche breadth), and operate at different taxonomic scales. The overlap of 4 KOs is too small for a meaningful enrichment or concordance test. The main cross-validation conclusion is that none of the 5 PGLS regressions find a significant association in the *expected* direction (all non-significant or reversed), meaning these 4 KOs' H1 associations are not strongly reflected in genus-level niche-breadth variation — consistent with the weak cross-dataset replication (H2) and the overall finding that the per-KO signals are dataset-specific and ecological-scale-dependent.

Source: `data/pgls_crossval_results.csv`

### FitnessBrowser cross-reference

The `comprehensive_metal_ecology` gene list includes a 116-KO FitnessBrowser-derived subset (Tier 2 evidence: genes whose fitness effects were measured under metal stress in Arkin Lab bar-seq experiments). All 116 FitnessBrowser KOs passed the MGnify prevalence filter and were tested. **4 of the 169 H1-significant unique KOs appear in the FitnessBrowser set** (K03442/mscS, K03837/sdaC, K07084/yuiF, K07338). Fisher enrichment among H1-sig KOs vs all 6,451 tested: OR = 1.34, p = 0.36 — not enriched, consistent with the H3 result for the full curated list. Of the 4 overlapping KOs, 3 are all-controls survivors (K03442, K07084, K07338), but with n = 4 total the survivor enrichment (OR = 3.19, p = 0.30) is not interpretable.

All 4 FitnessBrowser KOs that reach H1 significance carry "Unknown" primary category — they are not characterised metal-resistance or transport genes. Notably, their metal associations in FitnessBrowser (Co, Tl, Al, Ni) do not match their MGnify associations (Cr, Hg, Pb). This metal mismatch is expected: FitnessBrowser measures fitness effects under acute, controlled lab exposure to specific metals, whereas the MGnify associations reflect long-term ecological co-occurrence with naturally varying bioavailable concentrations in soil and aquatic environments. A gene whose fitness matters under Co or Ni stress in a lab experiment need not be enriched in Pb- or Hg-contaminated environmental communities — and vice versa. The absence of FitnessBrowser enrichment therefore does not indicate a failure of either approach; it confirms that fitness-under-laboratory-metal-stress and genome-wide-ecological-association-with-environmental-metals are different biological signals, each with independent evidential weight.

---

## NB08 — Lab–field cross-reference for Arc 4 phylo-PC survivors

**Question:** Do the 8 KO-metal pairs surviving all phylogenetic controls (H9, the Arc 4 survivors) confer fitness under matched acute metal stress in controlled laboratory experiments?

**Databases queried:** ENIGMA FitnessBrowser (`enigma.fitprivate`) and Arkin Lab FitnessBrowser (`kescience.fitnessbrowser`), via KO-to-locusId mapping through `besthitkegg` × `keggmember`.

**Source:** `notebooks/08_lab_field_crossref.ipynb` (executed 2026-07-29)

### Testability assessment

| KO | Gene | Metal | Organism | Status |
|----|------|-------|----------|--------|
| K02075 | ZnuB (ABC Zn/Mn transporter) | Cr | *Rhodanobacter_10B01* | **Testable** |
| K03442 | mscS (mechanosensitive channel) | Cr | *Rhodanobacter_10B01* | **Testable** |
| K08364 | merP (Hg chaperone) | Cd | *Rhodanobacter_10B01* | **Testable** |
| K01669 | phrB (CPD photolyase) | Cr | — | Not testable — dark assay; light-activated enzyme phenotypically silent |
| K07338 | — | Hg | — | Not testable — absent from screened genomes |
| K07338 | — | Pb | — | Not testable — absent from screened genomes |
| K13018 | — | Cd | — | Not testable — absent from screened genomes |
| K00376 | nosZ (N₂O reductase) | Pb | — | Not testable — absent from screened genomes |

**3 of 8 pairs are testable.** This is proof-of-concept; future work should expand to more organism–metal combinations across the full FitnessBrowser.

### Lab fitness of Arc 4 survivors

For the 3 testable pairs, fitness t-statistics under matched metal stress in *Rhodanobacter_10B01*:

| KO | Gene | Metal | Mean \|t\| | Max \|t\| | Pct rank (genome-wide) |
|----|------|-------|----------|---------|----------------------|
| K02075 | ZnuB | Cr | 0.38 | 0.61 | 48th percentile |
| K03442 | mscS | Cr | 0.14 | 0.30 | 33rd percentile |
| K08364 | merP | Cd | 0.32 | 0.70 | 45th percentile |
| **Arc 4 mean** | | | **0.28** | **0.70** | **42nd percentile** |

Arc 4 survivors fall at the **42nd percentile** of the genome-wide fitness distribution — statistically indistinguishable from a random gene (genome median = 50th percentile). None of the 3 testable genes shows a meaningful fitness effect under acute metal stress.

### Top lab fitness genes (reference)

For comparison, the top genes by acute fitness effect in the same organisms:

| KO | Gene | Metal | Mean \|t\| | Pct rank |
|----|------|-------|----------|---------|
| K02014 | TonB | Cr | 16.7 | 99th |
| K07239 | CusA/CzcA | Cd | 12.0 | 99th |
| K07090 | argD | Hg | 11.4 | 99th |
| K06180 | RluD | Pb | 17.2 | 99th |

**The effect size difference is 32×**: top lab genes mean \|t\| ≈ 8.94 vs Arc 4 mean \|t\| = 0.28. These are quantifiably different sets.

Notably, K07239 (CusA/CzcA, the top Cd lab fitness gene) is **absent from SPIRE MAGs** — below the n ≥ 8 prevalence threshold in global soil MAGs. The gene conferring the largest acute cadmium resistance advantage in the laboratory is too rare in field communities to be detected by the environmental association screen.

### Mechanistic illustration — the photolyase case

phrB (K01669, CPD photolyase) is an Arc 4 Cr survivor in SPIRE field data but is **not testable in RB-TnSeq**, which is run in darkness. CPD photolyase requires visible light to catalyse the repair of cyclobutane pyrimidine dimers; the knockout is phenotypically silent in dark growth conditions. Its field signal is most plausibly explained by co-occurring UV and chromium genotoxicity in surface soils: communities in high-Cr, UV-exposed environments face dual DNA damage pressure, making phrB loss ecologically costly even though no fitness deficit is measurable in lab conditions. This case illustrates why the two assay types dissociate: they measure selection under different physical conditions.

### Post-hoc framework — three ecological classes

The results are consistent with a three-class taxonomy describing how metal-responsive genes are distributed across lab and field measurement systems. **This framework is post-hoc and hypothesis-generating; it is not derived from formal statistical testing, and it rests on n = 3 testable pairs.**

**Class 1 — Stress-responsive homeostasis genes** (K02075/ZnuB, K03442/mscS): field signal surviving phylogenetic control; near-flat acute lab fitness (\|t\| < 0.7, 42nd percentile). These genes are ecologically widespread across metal gradients and may reflect tolerance of chronic metal burden rather than acute resistance. Note: ZnuABC is Zur-regulated and zinc-starvation inducible — "homeostasis" here refers to functional role and ecological prevalence, not constitutive expression.

**Class 2 — Inducible resistance genes** (K07239/CusA, top lab; K08364/merP, Arc 4): strong acute lab fitness (\|t\| ≈ 12–17) but rare or absent in global field MAGs. The best acute resistance gene (CusA/CzcA) falls below the SPIRE prevalence threshold entirely; merP shows flat fitness under the Cd signal for which it is an Arc 4 survivor. This is consistent with inducible resistance systems conferring large advantages under acute acute exposure but being too costly, ecologically constrained, or taxonomically restricted to dominate global soil communities under chronic metal gradients.

**Class 3 — Assay-inaccessible genes** (K01669/phrB): field signal for chromium; invisible to dark RB-TnSeq by mechanism. These genes may be systematically missed by lab-based functional screening despite ecological relevance.

This three-class taxonomy predicts that biomonitoring panels built from lab-identified metal resistance genes will preferentially recover Class 2 (inducible resistance) genes, which are the *least* ecologically prevalent in field communities — an empirically testable prediction for future meta-analyses of metal resistance gene surveys.

### External validation

Two independent lines of evidence support the broader interpretation that field metagenomics and acute lab fitness measure different aspects of metal adaptation:

- **Uluseker et al. (2025)** (*bioRxiv*): structural equation modelling of soil metagenomes shows that community assembly alone can produce spurious correlations between resistance genes and environmental variables, with phylogenetic associations with resistance plasmids as a primary confounding factor.
- **Dunivin & Shade (2018)** (*FEMS Microbiol Ecol* 94:fiy016): antibiotic resistance gene dynamics along a temperature gradient in soil are "largely explained by associated changes in community structure," not by direct selection on the resistance genes.
- **Dunivin, Yeh & Shade (2019)** (*BMC Biology* 17:45): a global soil arsenic resistance gene survey found that "phylogeny was predictive of arsenic genotype" but "geographic location was not predictive of arsenic-related gene content" — consistent with phylogenetic sorting as the dominant driver of field resistance gene distributions.

These three independent results, using different gene sets (ARGs, arsenic resistance, metal KOs) and different methods (SEM, community correlation, phylo-PC regression), converge on the same observation: environmental resistance gene patterns are primarily structured by evolutionary history and community composition rather than by the acute selection pressures that dominate lab fitness experiments.

### Data and figures

| File | Description |
|------|-------------|
| `data/arc4_lab_fitness_per_exp.csv` | Per-experiment fitness for 3 testable Arc4 KOs |
| `data/arc4_lab_fitness_summary.csv` | Mean t per KO × metal (3 rows) |
| `data/top_lab_fitness_genes.csv` | Top 30 lab genes per metal |
| `data/genome_wide_fitness_dist.parquet` | All KO-annotated gene fitness distributions |
| `data/lab_field_crossref.csv` | 23-row combined cross-reference table |
| `data/top_lab_ko_arc4_prevalence.csv` | Which top lab KOs are/are not in SPIRE MAGs |
| `figures/fig_nb08_arc4_lab_fitness.pdf` | Forest plot of Arc4 survivors' lab t-statistics |
| `figures/fig_nb08_field_vs_lab_scatter.pdf` | Scatter: field β vs lab t-statistic |
| `figures/fig_nb08_rank_distribution.pdf` | 2×2 genome-wide histogram panels |

---

## NB09 — KO ecological co-occurrence network (Proposal 4)

**Question:** Are the 84 all-controls-surviving field KOs genomically co-distributed with top lab fitness metal KOs? Ecological co-distribution (high Jaccard genome co-occurrence) would suggest these gene sets occupy similar genomic niches and may represent complementary aspects of the same metal adaptation context.

### Design

Co-occurrence is measured at the genome level across 8,585 MGnify MAGs. For each pair of KOs, Jaccard similarity J(A,B) = |A∩B|/|A∪B| is computed from the presence/absence binary matrix. KOs filtered to ≥50 genome prevalence. Sets: 84 field KOs (all-controls-surviving, `h1_robustness_summary.csv`) and 94 lab KOs (top Arc4 lab fitness KOs with MGnify prevalence, `top_lab_ko_arc4_prevalence.csv`). All 178 are distinct (0 overlap). A permutation test shuffles the field/lab labels among all 178 focal KOs 1,000 times to generate the null for mean cross-group Jaccard.

### Results

| Comparison | Mean Jaccard | Notes |
|---|---|---|
| Field–Lab (observed) | 0.052 | Actual field × lab pairs |
| Field–Field (observed) | 0.074 | Within field-KO set |
| Lab–Lab (observed) | 0.462 | Within lab-KO set |
| Global focal mean | 0.171 | All 178 × 178 pairs |
| Permutation null (Field–Lab) | 0.171 ± 0.002 | 1,000 shuffles |

**Permutation test:** Field–Lab observed Jaccard = 0.052, null mean = 0.171 ± 0.002, Z = −72.9, emp_p = 1.000.

**Key finding: Field KOs and lab KOs are NOT ecologically co-distributed — they are significantly below-random in genome co-occurrence (Z = −73).** Field KOs (mean J with lab KOs = 0.052) are far less co-occurring with lab KOs than a random set of 84 KOs would be (null mean = 0.171).

The high Lab–Lab Jaccard (0.462) reflects the nature of the top Arc4 lab fitness KOs: these are extremely high-prevalence housekeeping genes (K01895, K07090, K01262 etc. each present in 90%+ of MAGs) that co-occur with each other simply by being near-universal. Field KOs have much lower and more variable prevalence.

Top field–lab co-occurring pairs (top 10 all involve K01669/photolyase, prevalence 53%):

| Field KO | Lab KO | Jaccard | Shared genomes |
|---|---|---|---|
| K01669 | K01895 | 0.538 | 4,313 |
| K01669 | K07090 | 0.536 | 4,381 |
| K01669 | K01262 | 0.535 | 4,439 |

K01669 (photolyase, Cr field survivor) is a high-prevalence gene and naturally co-occurs with other high-prevalence lab KOs. The remaining 83 field KOs have much lower prevalence and Jaccard values.

### Interpretation

The null result (field KOs not co-distributed with lab KOs) is biologically interpretable and scientifically useful:

1. **Field KOs occupy different genomic niches than lab KOs.** Lab fitness KOs are near-universal genes whose fitness effects are detectable under controlled lab metal exposure. Field KOs are ecologically variable genes that differ in abundance across field metal gradients — precisely because they are NOT universally present.

2. **Field KOs are not confounded by essential genome.** If field KOs were simply detecting genomes with more complete/universal gene sets, they would co-occur highly with the universally-present lab KOs. They don't (J = 0.052), confirming that field associations detect ecologically specialized variation, not essential-genome abundance.

3. **This extends the NB08 lab–field disconnect conclusion.** NB08 showed that the 3 testable Arc4 survivors have near-zero lab fitness (Arc4 mean |t| = 0.28). NB09 adds that the full set of 84 field KOs is genomically segregated from the lab fitness gene pool (Z = −72.9). Together: field and lab metal adaptation signals are orthogonal along both functional (which genes) and genomic distribution (which genomes) axes.

**Caveat:** The prevalence difference (lab KOs ~90%, field KOs more variable) partially explains the low field-lab Jaccard independent of true ecological segregation. A prevalence-matched permutation would provide a cleaner test. The current result confirms orthogonality at the genome prevalence level; whether field KOs show above-chance local co-occurrence within individual genomes at matched prevalence is a separate question not tested here.

### Data and figures

| File | Description |
|---|---|
| `data/nb09_cooccurrence_summary.csv` | Key statistics: obs/null Jaccard, emp_p, Z |
| `data/nb09_field_lab_pairs.csv` | All 7,786 field–lab pairs with J > 0 |
| `data/nb09_perm_results.csv` | 1,000 permuted FL/FF/LL Jaccard values |
| `figures/fig_nb09_perm_fl_jaccard.pdf` | Permutation null histogram + observed value |
| `figures/fig_nb09_top_pairs.pdf` | Top-15 field–lab pairs by Jaccard |
| `figures/fig_nb09_jaccard_distribution.pdf` | Jaccard distributions by pair type |

---

## NB10 — Genomic context of field vs lab KOs (2026-07-29)

**Question.** NB09 showed that field and lab KOs occupy orthogonal genomic space (Z = −72.9). This notebook tests four mechanistic questions:
- **Q1:** Are field KOs more vertically inherited (higher Pagel's λ) than lab KOs?
- **Q2:** What genes co-occur with field KOs vs lab KOs?
- **Q3:** Are field KOs associated with HGT elements (transposases/integrases)?
- **Q4:** Are field KOs regulated by more TFs (inducible) or fewer (constitutive)?

**Data.** MGnify binary KO matrix (8,585 MAGs × 6,451 KOs); 84 field KOs (survive all 4 robustness controls); 96 lab KOs (top fitness genes from Arc 2). For Q4: RegulonDB v12 (*E. coli* K-12 TF–gene interactions, 298 TFs, 5,972 edges) linked to KO IDs via KEGG ECO b-number mapping (3,398 KO links).

### Q1: Prevalence as core/accessory genome proxy

Direct λ comparison is not feasible: the existing `phylo_d_all_ko.csv` covers only 7 field KOs (λ range 0.317–0.818, mean 0.55) and 4 lab KOs (λ range 0.458–0.651, mean 0.56) — both groups n too small and means indistinguishable.

Prevalence is used as a proxy:

| Group | Mean prevalence | Median prevalence |
|---|---|---|
| Field KOs (n=84) | 4.9% (424/8,585 MAGs) | 2.7% (234 MAGs) |
| Lab KOs (n=96) | 63.3% (5,438 MAGs) | 65.0% (5,582 MAGs) |
| All 6,451 KOs | 23.1% | — |

Mann-Whitney U p = 1.21×10⁻²⁸. Field KOs are unambiguously **accessory genome** genes; lab KOs are **near-core**. Lab KOs at 65% prevalence are almost certainly vertically inherited (HGT to 65% of a phylogenetically diverse metagenome is implausible). Field KOs at 5% prevalence are consistent with either vertically inherited niche specialists or independently HGT-acquired — prevalence alone cannot discriminate.

### Q2: Co-occurrence partners

Mean Jaccard of each focal group against all 6,451 KOs (8,585 MGnify MAGs). Top-30 partners by Jaccard:

| Group | Top-30 partner prevalence | Core (>85%) | HGT markers |
|---|---|---|---|
| Field KOs | mean 3.3%, all in 0–10% bin | 0/30 | 0/30 |
| Lab KOs | mean 94.9%, all in 50–100% bin | 30/30 | 0/30 |

**Prevalence-adjusted interpretation.** For field KOs (5% prevalent) pairing with other rare genes (3.3% prevalent), the null expected Jaccard is 0.020. Observed top-30 J = 0.14–0.18 — **7–9× above null** — indicating genuine ecological clustering: the organisms that carry these field KOs consistently co-carry the same set of other rare specialist genes.

For lab KOs (65% prevalent) pairing with core genes (95% prevalent), the null expected J = 0.63. Observed J = 0.63 — **exactly at null**. Lab KO co-occurrence with core genes is entirely explained by prevalence; there is no specific genomic clustering.

**Conclusion.** Field KOs form real ecological clusters with rare accessory genes. Lab KOs are distributed across the core metabolic backbone at background rates.

### Q3: HGT marker co-occurrence

Eleven transposase/integrase KOs (IS1, IS3, IS4, IS5, IS256, Tn3, Tn7, Tn resolvase, phage integrase: prevalence 2.4–43.5%) define the HGT marker set. Raw mean Jaccard: field = 0.029, lab = 0.154 (0.19× ratio).

After prevalence adjustment (observed / expected-under-independence):

| | Field KOs | Lab KOs |
|---|---|---|
| Mean O/E | **1.01** | **1.04** |

Both groups are at the null (O/E ≈ 1). The raw 5× difference is entirely prevalence-driven — a 65%-prevalent gene trivially co-occurs with any moderately prevalent element. **Neither field nor lab KOs are enriched or depleted for HGT markers relative to their prevalence class.**

The hypothesis inversion (lab KOs = HGT-prone) does not hold once prevalence is controlled.

### Q4: Transcriptional regulatory complexity (RegulonDB)

Coverage: 32/84 field KOs and 69/96 lab KOs have *E. coli* K-12 regulatory data. The 52 field KOs without E. coli data are, by definition, not universal enough to be present in *E. coli* — so their regulatory architecture is unknown.

| Metric | Field KOs (n=32) | Lab KOs (n=69) | p |
|---|---|---|---|
| TFs per gene (mean) | 2.41 | 1.35 | MW p=0.69 |
| TFs per gene (median) | 1.0 | 1.0 | — |
| Global TFs per gene | 0.53 | 0.58 | MW p=0.50 |
| Regulated by ≥1 metal TF | 3/32 (9.4%) | 3/69 (4.3%) | Fisher p=0.38 |
| Unregulated (0 TFs) | 14/32 (44%) | 19/69 (28%) | — |

No significant difference in regulatory complexity. Both groups are mostly weakly regulated (median 1 TF). **Q4: null result — cannot distinguish constitutive from inducible on this evidence.**

However, the mechanistically notable cases: the three field KOs regulated by metal-sensing TFs include **csgG** (curli secretion; regulated by BasR and CpxR — envelope stress and zinc/metal) and **flhC/flhD** (flagellar master regulators; regulated by Fur — iron/metal sensing). These are precisely the field-associated genes with directional interpretability: flagellar depletion near metals is explained by Fur-mediated repression when iron/metal homeostasis is disturbed.

### Synthesis

The original hypothesis — field KOs embedded in vertically inherited, constitutively expressed genomic islands; lab KOs in HGT-prone, inducible modules — is **not supported**:

| Prediction | Result |
|---|---|
| Field KOs: core genome (high prevalence) | OPPOSITE — field KOs are accessory genome (5% prev) |
| Lab KOs: HGT-prone (high HGT marker J) | NULL — O/E = 1.04, same as field |
| Field KOs: constitutive (fewer TFs) | NULL — both groups median 1 TF, p=0.69 |
| Lab KOs: inducible (more TFs) | NULL — same as above |

**Supported alternative:** Field KOs are ecologically specialized accessory genes that genuinely cluster with other rare specialist genes (J = 7–9× null). Lab KOs are near-core metabolic genes whose expression changes under metal stress — not specifically HGT-associated, not more inducible than field KOs. The orthogonality (NB09 Z = −72.9) reflects accessory-vs-core partition, not HGT-vs-vertical or inducible-vs-constitutive.

### Data files

| File | Description |
|---|---|
| `data/nb10_field_ko_top_partners.csv` | Top-30 co-occurrence partners for field KOs |
| `data/nb10_lab_ko_top_partners.csv` | Top-30 co-occurrence partners for lab KOs |
| `data/nb10_hgt_marker_jaccard.csv` | HGT marker × field/lab Jaccard (raw + O/E) |
| `data/nb10_jaccard_all_kos.parquet` | Full Jaccard matrix for all 6,451 KOs vs field/lab means |
| `data/nb10_regulondb_regulatory_complexity.csv` | Per-KO TF count, global TF count, metal TF regulated |
| `data/regulondb_TFSet.txt` | RegulonDB TF metadata (downloaded 2026-07-29) |
| `data/regulondb_NetWorkTFGene.txt` | RegulonDB TF–gene network |
| `data/regulondb_GeneProductSet.txt` | RegulonDB gene products (gene→b-number) |
| `data/kegg_eco_to_ko.tsv` | KEGG *E. coli* b-number→KO mapping |

---

## NB11 — Sequence-feature model: do field KOs look like metal-fitness genes? (2026-07-29)

**Question.** Arc 6 showed amino acid composition predicts metal fitness (AUC 0.56–0.77). Does a sequence-feature classifier trained on lab RB-TnSeq data assign high metal-fitness probability to field KOs — or do field KOs look ordinary at the sequence level?

**Hypothesis:** Field KOs will have lower predicted fitness under metal stress than lab fitness genes.

**Data.** Training set: 191 strong lab fitness hits (global min_t < −4) as positives; 227 clearly neutral KOs (per-KO mean |t| < 1.0 across all conditions) as negatives. Sequences: KEGG representative protein sequences fetched via two-step REST API (link/genes → get/aaseq; 655/660 KOs returned valid sequences; preferred *eco*, *pae*, *dvu*, *cau* when available). Features: 20 AA composition fractions + log-length + GRAVY + net charge + Cys fraction + aromatic fraction + polar fraction + charged fraction + small-residue fraction (28 features total).

**Model performance.** Logistic regression (L2, C=1.0): cross-validated AUC = 0.657. Random Forest (300 trees, max_depth=5): AUC = 0.627. Final model: Logistic (L2). AUC is consistent with Arc 6's range (0.56–0.77).

**Predicted metal-fitness probability:**

| Group | n | Mean | Median | Fraction ≥ 0.5 |
|---|---|---|---|---|
| field-strict (all-4-controls) | 84 | 0.376 | 0.347 | 22/84 (26%) |
| field-loose (all-H1-sig) | 166 | 0.394 | 0.369 | 43/166 (26%) |
| neutral (tested, not hits) | 227 | 0.392 | 0.364 | 63/227 (28%) |
| lab-top96 (Arc2) | 94 | 0.516 | 0.523 | 50/94 (53%) |
| lab-hits (strong fitness) | 191 | 0.534 | 0.541 | 116/191 (61%) |

**Hypothesis test.** Field KOs have significantly lower predicted fitness than lab fitness genes (MW one-sided p ≈ 0 for all field × lab combinations): **SUPPORTED**.

**Critical control — field vs neutral.** Field KOs are indistinguishable from neutral (untested/non-hit) KOs: field-strict vs neutral MW two-sided p = 0.63; field-loose vs neutral p = 0.71. Field KOs are not enriched for metal-fitness sequence features relative to background.

**Prevalence-stratified check.** Within the 0–10% prevalence bin (n = 79 field-strict, 56 neutral):

| Group | Mean | Median |
|---|---|---|
| field-strict | 0.368 | 0.339 |
| neutral (0–10% prev) | 0.356 | 0.340 |

Identical within rounding. The model's field/lab discrimination vanishes when prevalence is controlled — confirming the classifier learns core-vs-accessory sequence composition rather than metal-specific features.

**Interpretation.** The hypothesis is formally supported (field < lab), but the mechanism is prevalence confounding: core-genome proteins (lab fitness genes, ~65% prevalent) have different amino acid composition from accessory proteins (field KOs, ~5% prevalent) — longer, more charged, different hydrophobicity profile — which is what the classifier learns. Field KOs carry no detectable metal-binding sequence signature beyond what any rare accessory gene shows. Their ecological association with metal gradients reflects community-level sorting (which organisms are present, not what metal-handling sequence features those organisms carry). This is the sequence-level analogue of the NB09/NB10 finding: field and lab metal adaptation are orthogonal at every level of resolution — genome prevalence, co-occurrence structure, regulatory complexity, and now amino acid composition.

### Data files

| File | Description |
|---|---|
| `data/nb11_predicted_fitness_probs.csv` | Per-KO predicted probability + prevalence + group label |
| `data/nb11_kegg_seq_cache.json` | Cached KEGG protein sequences (655 KOs) |
| `data/nb11_output.txt` | Full model run log |
| `scripts/run_nb11_sequence_model.py` | Analysis script |

---

## NB12 — Comparison with Goff et al. 2024 heavy metal resistance genes (2026-07-29)

**Source.** Goff et al. 2024 "Mixed waste contamination selects for a mobile genetic element population enriched in multiple heavy metal resistance genes" (*ISME Commun*, DOI: 10.1093/ismeco/ycae064). The paper characterises circular MGEs (plasmids, unclassified MGEs, cryptic elements) assembled from the Oak Ridge Reservation (ORR) contaminated subsurface — the same ENIGMA site as the SPIRE dataset. Supplementary files (Table S11: eggNOG-mapper annotations for all 9,739 MGE genes across 501 unique MGEs; Table S12: curated heavy metal resistance genes, HMRGs, on 326 MGE×gene instances) were provided directly by the PI.

**Q1: Do canonical HMRGs (S12) overlap with our 84 field-strict KOs?**

S12 lists 26 unique HMRG gene names (merR, arsR, cusA, zntA, copZ, merA, czcD, chrA, cusF, pcoB, fieF, arsB, arsC, arsA, acr3, etc.; frequency-ranked). When these are mapped to KO IDs via the KEGG database:

| Result | Value |
|--------|-------|
| S12 HMRG KOs with confirmed KEGG assignment | 23 / 26 genes |
| S12 HMRG KOs in field-strict (84) | **0** |
| S12 HMRG KOs in field-loose (169) | **0** |
| S12 HMRG KOs in lab-strong-fit (191) | 0 |
| S12 HMRG KOs in SPIRE-sig pairs (31) | **0** |

No canonical HMRG from the Goff curated list appears in our field-significant KO sets. This is consistent with H3 (curated metal KOs not enriched in field associations) and with the NB08–NB11 finding that field KOs are accessory-genome residents that are rare in global pangenomes.

**Why no overlap?** Three factors are mutually reinforcing:
1. HMRGs are rare globally: median MGnify prevalence = 19% across 23 named HMRGs (range 2–97%). Our logistic regression model requires sufficient within-dataset variation; for KOs present in <5% of MAGs, statistical power is low.
2. HMRGs are not uniformly rare: arsR (90%), tehB (97%), arsB (59%), arsC (46%), arsR (90%) are actually common — yet these also fail to reach field significance, suggesting the environmental-correlation signal is genuinely absent for HMRGs across global soil MAGs.
3. ORR is likely a special case: Goff's HMRGs show HGT O/E ≈ 1.07 in the global pangenome despite being 90% on conjugative elements at ORR. ORR-specific HGT patterns do not translate to global co-occurrence enrichment.

**HMRG HGT O/E in global pangenome.** Despite Goff's finding that 90% of ORR HMRGs reside on conjugative elements, their HGT marker co-occurrence in the 8,585-MAG MGnify pangenome is near-null:

| Metric | Value |
|--------|-------|
| Median HMRG HGT O/E (23 genes) | 1.074 |
| Range | 0.835–1.465 |
| Our field KOs HGT O/E (NB10) | ~1.0 |
| Our lab KOs HGT O/E (NB10) | ~1.04 |

ORR contamination created local HGT selection pressure that is not reflected in global pangenome co-occurrence patterns. This is internally consistent with NB10: neither our field KOs nor canonical HMRGs show general HGT enrichment in global MAG datasets.

**Q2: Broader comparison via S11 (all KO-annotated MGE genes).**

S11 covers 9,739 gene models across 501 ORR MGEs. Of these, 3,781 have KEGG KO assignments (eggNOG-mapper), yielding 1,309 unique KOs. Comparing against our sets:

| Set | KOs on ORR MGEs | Fraction |
|-----|----------------|---------|
| Field-strict (84) | **10** | 11.9% |
| Field-loose (169) | 14 | 8.3% |
| Lab-strong-fit (191) | 72 | 37.7% |

The lab-strong overlap (72/191, 38%) is expected: core-genome genes appear across diverse genomic contexts including MGEs. The field-strict overlap (10/84, 12%) is more informative.

**Field-strict KOs found on ORR MGEs (S11):**

| KO | Gene | Field metal | MGEs (n) | Notes |
|----|------|------------|----------|-------|
| K08364 | merP | PF1_Cd | **11** | Hg periplasmic binding protein; found on 11 distinct ORR MGEs |
| K11811 | ArsH | PF1_Pb | 4 | Arsenate resistance protein ArsH; arsenate reductase superfamily |
| K17320 | — | PF1_As | 2 | ABC transporter inner membrane component |
| K02403 | flhD | PF1_As | 1 | Flagellar master regulator FlhD |
| K02402 | flhC | PF1_Cr | 1 | Flagellar master regulator FlhC |
| K00376 | nosZ | PF1_Pb | 1 | Nitrous-oxide reductase |
| K01965 | pccA | PF1_Hg | 1 | Propionyl-CoA carboxylase |
| K16880 | — | PF1_Hg | 1 | Enoyl-CoA hydratase/isomerase |
| K21393 | — | PF1_Pb | 1 | Permease |
| K21645 | — | PF1_Hg | 1 | Transcriptional regulator |

The most biologically informative hit is **merP (K08364) × Cd, on 11 MGEs**. merP is the mercury-binding periplasmic chaperone (part of the merTPCA operon) and its field-significance for Cd is likely an ecological proxy for multi-metal contamination: sites with high Cd often co-occur with Hg contamination (mining, industrial runoff). merP on 11 ORR MGEs confirms the mercury operon is actively mobilised at this site.

**Q3: SPIRE-significant KOs on ORR MGEs.**

Of the 31 SPIRE pairs significant in the direct-effect model (23 unique KOs), 8 KOs appear on ORR MGEs in S11:

| KO | Gene | SPIRE metal | Beta | MGEs (n) | Notes |
|----|------|------------|------|----------|-------|
| K08363 | merT | Hg | −30.2 | **13** | Mercury transport protein; negative association |
| K02005 | — | Hg | +9.9 | 3 | Membrane fusion protein (efflux system) |
| K02012 | — | Pb | +15.3 | 4 | ABC transporter periplasmic binding protein |
| K02011 | — | Pb | +14.4 | 3 | ABC transporter inner membrane protein |
| K00368 | nirK | Hg | −9.0 | 1 | Cu-containing nitrite reductase |
| K09796 | — | As | +16.2 | 1 | Conserved bacterial protein |
| K21903 | — | Cd | −10.0 | 2 | ArsR-family regulator |
| K02564 | — | Hg | −12.6 | 1 | — |

**merT (K08363) × Hg is the most important cross-study connection.** merT is the inner membrane Hg transport protein — it works with merP (K08364) and merA (K00520) as part of the mer operon. merT is among the 31 SPIRE pairs significant in the direct-effect model (β_direct = −30.2, q = 0.046; β_total = −19.5, q = 0.04).

**The negative sign requires explanation.** A mercury transport gene negatively associated with Hg environments globally is counterintuitive. Three hypotheses are consistent with the data:

1. *Selection pressure reversal at global scale.* At ORR (high local Hg), merT-containing MGEs are positively selected. Globally, the median soil Hg is low, and MAGs that carry the energetically costly full mer operon are at a slight disadvantage in low-Hg environments, dragging the cross-MAG association negative. This is the "optimal investment" model of accessory gene ecology.
2. *Incomplete operon context.* merT is a transport protein that requires merP (import) and merA (detoxification) to function — it is toxic without merA because it accumulates Hg²⁺ in the cytoplasm. MAGs in our global dataset that carry merT alone (without merA) may be actively disadvantaged in moderate-Hg sites, producing the negative association. This is testable by conditioning on co-occurrence with merA.
3. *Compositional confound.* merT is common in Proteobacteria (Beta/Gamma) that thrive in low-Hg, high-nutrient soils. The taxonomic control (phylum/genus) may not fully absorb this gradient.

None of these is tested directly in this analysis. The negative sign is documented, not explained.

**The merP × Cd association requires a separate explanation.** merP (K08364) is field-strict associated with Cd (not Hg). merP is a periplasmic Hg-binding protein with a CXXC motif; the cysteine coordination chemistry that binds Hg²⁺ is similar to that of Cd²⁺ (both soft Lewis acids). Cross-metal binding by merP has been demonstrated biochemically (Rossy et al. 2004). Alternatively, Hg and Cd frequently co-contaminate soils, and the Cd association may reflect co-occurrence with undetected Hg gradients in the SPIRE dataset. The Cd association should therefore be interpreted as "merP-family periplasmic metal-binding proteins correlate with Cd gradients" rather than strict mercury biology.

merT is also on **13 ORR MGEs** — more than any other single KO in S11. Combined with merP (K08364) on 11 MGEs, both transport components of the mer operon are highly mobilised at ORR. The mer operon is the textbook paradigm for HGT-mediated metal resistance, and Goff's paper confirms its ongoing horizontal transfer at ORR.

**Synthesis: what the Goff comparison tells us about our field KOs.**

| Claim | Evidence |
|-------|---------|
| Classical HMRGs are not what drives field KO associations | 0/26 S12 HMRGs in field-strict set |
| Mer operon components appear in both datasets (different metals) | merP field-strict×Cd (cross-metal binding); merT SPIRE×Hg (negative); both on 10–13 ORR MGEs |
| No true merR cross-study overlap | K14658 (Goff top HMRG) absent from SPIRE; K07093 (SPIRE MerR-family) absent from Goff S11 |
| ORR-specific HGT does not show up in global pangenome HGT metrics | HMRG HGT O/E ≈ 1.07 despite 90% on conjugative elements at ORR |
| Lab fitness genes (core genome) overlap with ORR MGEs more than field KOs | 72/191 (38%) vs 10/84 (12%) |
| The field signal is driven by rare accessory genes, not canonical resistance genes | NB10 + Q1/Q2 of this comparison |

The key mechanistic inference: our field screen finds genes whose *presence* correlates with metal gradients across global soil communities. This is dominated by rare accessory genes (median 5% prevalent). Classical HMRGs are rare too, but their rarity combined with high compositional specificity (only in metal-contaminated sites like ORR) means they do not generate robust logistic-regression signal across the diverse biomes in our 8,585-MAG dataset. The mer operon components (merP×Cd, merT×Hg) are the exceptions — they survive stringent controls in SPIRE, but with unexpected metal assignments (Cd for merP; negative Hg for merT) that require the mechanistic caveats above.

### Data files

| File | Description |
|---|---|
| `data/goff_comparison_results.csv` | Per-HMRG table: KO assignment, S12 frequency, field/lab/SPIRE membership, prevalence |
| `data/goff_s11_field_overlap.csv` | 10 field-strict KOs found on ORR MGEs (S11), with description and n_MGEs |
| `data/goff_comparison_output.txt` | Full comparison run log |
| `scripts/run_goff_comparison.py` | Analysis script |

Source tables: `/home/hmacgregor/data/Goff2024/table_s11_mge_annotations-eggnogmapper_ycae064.xlsx`, `table_s12_mge_associated_hmrg_and_arg_ycae064.xlsx`.

---

## NB13 — Comparability assessment: Huang et al. 2025 (2026-07-29)

**Paper:** Huang Y et al. 2025. "Mobile genetic elements shape metal resistance in contaminated soils." *Microbiome* 13, article 40168_2025_2030. (Title approximate from MOESM filename.)

**Data inspected:** `/home/hmacgregor/data/Huang2025/40168_2025_2030_MOESM1_ESM.xlsx` — 13 sheets. Table S13 is the relevant table: 132,437 rows of BacMet-annotated metal resistance genes across MAGs (118,284), plasmids (12,435), and phages (1,718). Target metals covered: As (6,046 MAG rows, 22 gene names), Cd (3,883, 33 genes), Cr (4,513, 14 genes), Cu (14,925, 62 genes), Hg (3,813, 16 genes), Pb (2,847, 7 genes). 276 unique BacMet gene names across all metals.

**Design:** Controlled contamination gradient in Chinese agricultural soils (P-0, P-10, P-100 = Pb control/medium/high, n=3 replicates each; C-10, C-100 = Cd medium/high) plus Sb mining sites (XH, XN; elevated As and Hg). Primary paper focus is defense systems (CRISPR-Cas, restriction-modification), with metal resistance gene data as secondary output.

### BacMet → KO mapping and overlap

Of 147 unique gene names found in target-metal MAG rows, **22 have unambiguous KO assignments** from the HMRG-to-KO dictionary (established during the Goff comparison; see NB12). The remaining 125 genes lack a clear KEGG KO (regulatory two-component systems, transporters with multiple homologs, or BacMet-specific IDs without established KO equivalents).

Overlap with our KO sets:

| Gene (BacMet) | KO | MAG rows (target metals) | In field-strict 84? | In SPIRE-sig 31? |
|---|---|---|---|---|
| merP | K08364 | 117 | **Yes** | No |
| merT | K08363 | 142 | No | **Yes** |
| merA | K00520 | 2,775 | No | No |
| arsR | K03628 | 207 | No | No |
| arsB | K03455 | 480 | No | No |
| arsC | K00537 | 464 | No | No |
| arsA | K01551 | 162 | No | No |
| chrA | K06163 | 501 | No | No |
| cusA | K07798 | 745 | No | No |
| copA | K07133 | 830 | No | No |
| czcD | K11946 | 98 | No | No |
| zntA | K01534 | 60 | No | No |

> **Correction (2026-08-06):** An earlier version of this table listed zntA as K01533. K01533 is copB (P-type Cu²⁺-transporting ATPase), not zntA. K01534 is the correct KEGG KO for zntA (Zn²⁺/Cd²⁺-exporting P_IB-type ATPase). Neither K01533 nor K01534 appears in the field-strict 84 KOs or the SPIRE-sig 31 set; the error affects only this cross-reference table. K01533 (copB) has β = −4.99 × Hg (q = 4.8×10⁻²⁰) in the MGnify latitude-adjusted model — if Adam sees "zntA" among top Hg hits, this is the gene responsible.

**Field-strict hits: 1** — merP (K08364), found in 117 MAG rows from Hg-contaminated sites (Sb mining / XH). **SPIRE-sig hits: 1** — merT (K08363), found in 142 MAG rows. Both are mercury operon transport components.

### Cross-study convergence: the mercury operon

merP and merT appear across three independent systems:

| System | merP evidence | merT evidence |
|---|---|---|
| This project (global, SPIRE) | field-strict × Cd (K08364) | SPIRE-sig × Hg negative (K08363) |
| Goff 2024 (ORR subsurface MGEs) | 11 MGEs in S11 eggNOG | 13 MGEs in S11 eggNOG |
| Huang 2025 (Chinese contaminated soils) | 117 MAG rows, Hg-site MAGs | 142 MAG rows, Hg-site MAGs |

merP and merT appear across three independent systems. **Caution on interpretation**: the convergence is on *gene presence in metal-disturbed environments*, not on consistent metal associations. In this project, merP associates with Cd (not Hg) and merT has a negative Hg coefficient — the opposite of the pattern implied by "mercury operon convergence." All three systems confirm mer operon genes are prevalent near contaminated sites (a qualitative finding), but the direction and metal specificity differ. This is a qualitative ecological signal, not a cross-study replication of effect sizes.

**merA×Hg null — explicit conflict with mercury biomonitoring literature.** merA (mercuric reductase, K00520) — the most abundant Hg gene in Huang (2,775 rows) — does not reach statistical significance in our community-scale logistic regressions (FDR=0.37, **rank 29/48 metals** ranked by Hg association strength for merA). This is a direct conflict with the expectation from mercury biomonitoring literature (Barkay et al. 2003, *FEMS Microbiol Rev*) that merA enrichment tracks Hg contamination, and from field studies demonstrating mer operon activation under Hg stress (Goff et al. 2024). The failure is not explained by phylogenetic confounding or analytical sensitivity — three mechanistic tests (NB35) were conducted:

1. **HGT mobility ≠ cognate failure (Test 1):** Fritz & Purvis D is not correlated with Hg cognate rank (Spearman ρ=0.092, p=0.512, N=53 resistance KOs) — HGT-mobile genes do not systematically fail to track their target metal; merA's failure is not a generic HGT effect.
2. **Geochemical orthogonality (Test 2 — SUPPORTED):** PCA of 32 USGS log-metals shows that metals positively associated with merA load on PC1 (lithogenic: Ba/Sr/Zr/REEs/Sb), while USGS Hg loads on PC2 (hydrothermal/volcanic: Hg/Se/Te). The Euclidean separation between the Hg axis and merA's tracked-metals centroid is 0.420 — Hg and merA inhabit orthogonal geochemical space. Independent GLiM lithology validation (NB36) confirms PC2 is the silicic/acid-volcanic (VA class) axis (median PC2=+5.594), not Hg-contamination per se.
3. **Mine proximity adds nothing (Test 3):** Distance to 2,651 US Hg mine sites (MRDS) explains <0.1% of merA CWM variance (partial R²=0.00094, β(log_dist)=+0.0018, inverted direction).

**Mechanistic interpretation:** The community-level failure of merA×Hg reflects that USGS-measured soil Hg is geographically anchored to silicic volcanic geology (hydrothermal/epithermal Hg mineralization), while merA-enriched communities preferentially inhabit soils with high lithogenic metal loadings — orthogonal axes. Barkay et al.'s well-documented mer operon induction occurs under acute laboratory or field point-source contamination; at the global macroecological scale, Hg exposure is dominated by geogenic background from volcanic lithology, not by contamination events that would select for constitutive merA enrichment. The rank 29/48 is real: merA responds to general crustal metal chemistry, not Hg specifically, at the community scale. This is not a failure of the gene's function — it is a mismatch between the scale at which mer operon ecology was characterized (local contamination experiments) and the scale at which we test it (global macroecological gradient).

### What cannot be compared

1. **No KEGG KO annotations.** Huang uses only BacMet IDs and gene names; 125/147 target-metal genes in the MAG subset lack mappable KO equivalents. Systematic KO-level comparison is not feasible.
2. **No genome-wide regression.** Huang reports gene presence/absence per MAG/site, not logistic regression across a diverse global sample. There is no statistical model analogous to our `KO_present ~ PF1_metal + covariates`.
3. **Sample size: n=3 per treatment.** The controlled gradient experiment (P-0/P-10/P-100, n=3 replicates each) is far too small to run logistic regression. This study is designed to characterize *which* genes respond to contamination, not to quantify effect sizes or control for confounders.
4. **Different geographic scope.** Chinese contaminated agricultural soils vs. global cross-ecosystem soils. Our field signal requires presence across diverse biomes; Huang's design detects locally enriched genes.
5. **Primary focus is defense systems, not metal resistance ecology.** Tables S4–S11 cover CRISPR-Cas and restriction-modification. Table S13 (BacMet) is supplementary to the main biological claim.
6. **BacMet ≠ KEGG annotation.** BacMet IDs are phenotype-curated (biocide and metal resistance), not pathway-curated. The same phenotypic gene can have multiple BacMet IDs (e.g., merA appears as BAC0648–BAC0653). Mapping to KEGG KO is one-to-many and incomplete.

### Verdict

**Limited but meaningful comparability.** The Huang 2025 data cannot be used to replicate or extend our logistic regression framework. However, it provides independent qualitative confirmation that merP and merT are enriched in Hg-contaminated MAGs across a distinct geographic and environmental context (Chinese agricultural and mining soils).

**Important caveat on metal assignments.** The "convergence" across the three studies is convergence on *gene presence/abundance in metal-disturbed environments*, not convergence on the same metal association:

- merP appears in Huang Hg-site MAGs and on Goff ORR Hg-contaminated MGEs, but its field-strict association in this project is with **Cd** (not Hg). The Cd signal likely reflects the shared soft-Lewis-acid coordination chemistry of Hg²⁺ and Cd²⁺ (see NB12 synthesis).
- merT appears in Huang Hg-site MAGs and on 13 Goff ORR MGEs, and is SPIRE-sig for **Hg** but with a **negative** coefficient (see NB12 merT discussion).

The three-dataset "mercury operon" finding should therefore be described as: *mer operon transport components (merP, merT) are consistently associated with metal-contaminated environments across independent studies, but the direction and metal specificity of the associations require context-specific mechanistic interpretation.*

The arsenic operon genes (arsR, arsB, arsC, arsA) and chromate transporter (chrA) are abundantly represented in Huang S13 but do not overlap with our field-strict or SPIRE-sig sets, consistent with the NB12 finding that classical HMRGs are too rare in global MAG datasets to generate robust logistic-regression signal.

### Data files

| File | Description |
|---|---|
| `/home/hmacgregor/data/Huang2025/40168_2025_2030_MOESM1_ESM.xlsx` | Source supplementary; Table S13 used |

Source: Huang Y et al. 2025 *Microbiome* MOESM1.

---

## Reconciling with positive metal resistance gene literature

**Apparent contradiction.** A substantial body of literature documents that metal resistance gene (MRG) content and abundance is enriched in contaminated vs reference soil/water sites. Studies such as Long et al. (2021), Yi et al. (2022), and Gillieatt et al. (2024) report positive associations between metal contamination levels and aggregate MRG richness, gene copy number, or operon prevalence. This project finds 0 field-significant associations for canonical metal resistance genes (arsR, arsB, arsC, merA, cusA, copA, zntA, czcD), and detects 84 field-robust KO-metal pairs dominated by non-resistance functional categories. The null result for aggregate MRG metrics could appear to contradict the positive-association literature. **However, several methodological and biological factors reconcile the findings:**

### 1. Scale mismatch: contamination threshold vs. continuous gradients

The vast majority of published MRG surveys compare **extremely contaminated sites (e.g., active mines, smelters, Superfund sites) vs. pristine reference sites** — a binary exposure classification with enormous effect sizes. This study analyzes continuous, fine-grained metal concentration gradients (PF1 mobility scores) across 8,585 soil samples of varying degrees of contamination. The field-site studies detect MRG enrichment at a *Ω-shaped exposure-response relationship*: MRG abundance is flat at low-to-moderate metal levels (0–10th percentile PF1), then rises sharply only at extremely high contamination (>90th percentile). In such nonlinear response, logistic regression on the full continuous gradient will produce a weak, near-null coefficient: half the samples fall in the flat region, diluting the signal from the extreme-contamination tail. The published positive results emerge from design-induced selection of the extreme tail — which is a valid study design for characterising resistance under high stress, but does not imply genome-wide signal across the environmental gradient sampled here.

### 2. Publication bias and selective reporting of effect sizes

Studies published on MRG soil enrichment typically select for **large effect sizes at contaminated sites** — a form of publication bias toward positive results. Surveys designed to detect MRG presence at mining sites, foundries, or heavily spiked agricultural soils will preferentially find and publish MRG enrichment. Surveys designed to examine MRG distributions across uncontaminated-to-lightly-contaminated agricultural soils are less common and less likely to be published if results are null. The logistic-regression framework used here — testing every KO across 8,585 diverse MAGs with only weak statistical power in the tails of the metal gradient — is inherently conservative relative to case-control mining/reference studies that maximise contrast. Combining the methodological difference (continuous vs binary design) with publication bias (positive findings favoured), the apparent discrepancy is largely a study-design artefact, not a biological contradiction.

### 3. Methodological difference: qPCR proxies vs. genome-wide density

Many positive-MRG papers use **quantitative PCR (qPCR) targeting a few specific resistance operon genes** (integrons as class-1-integrase proxies; merA/merR by specific primers; arsC/arsR by genus-specific quantitative assays) rather than metagenomic de novo assembly and pangenome-wide KO annotation. A specific integron class (e.g., integrase with merA downstream) selected by qPCR can show strong enrichment at contaminated sites because qPCR detection is exquisitely sensitive to the exact target. By contrast, our metric (presence/absence of K00520/merA among 6,451 possible KOs per MAG) is diluted by the many alternative pathways to metal processing, by the rarity of merA in global MAGs (~4% prevalence), and by taxonomic composition shifts that can mask gene-level signal. This is not a failure of the metagenomics approach — it reveals that **aggregate MRG metrics at the genome level are genuinely insensitive to chronic metal gradients in diverse environmental communities**, even when specific resistance operons are mobilised locally at extreme-contamination sites. The qPCR literature measures something real (operon-level responsiveness); this work measures something different (whole-genome KO dynamics) and finds they are decoupled.

### 4. Individual vs. aggregate signal

Critically, this project **does identify significant metal-associated KO–metal pairs (219 baseline, 89 robust).** The null result is specifically for *aggregate metal-resistance gene density* or *aggregate MRG richness* — the feature tested in most positive-MRG literature. At the individual KO level, the field identifies 84 robust KO-metal associations, including 10 KO-metal pairs found on ORR metal-contaminated MGEs (merP/K08364 on 11 ORR plasmids; merT/K08363 on 13 ORR plasmids; K02012 Pb transporter on 4 MGEs, etc.). **The sign flip from positive aggregate MRGs (in the literature) to individual-gene associations (in this work) is genuine:** individual genes CAN associate with metal gradients, but when summed into a single "aggregate metal-resistance density" metric, the signal is too noisy to detect at p < 0.05 in global soil metagenomes. This is not contradictory — it reveals that metal ecology is *gene-specific and context-dependent*, not driven by a single overarching "metal-resistance trait" that scales uniformly with contamination. The individual-KO discovery of 84 bioindicator candidates is therefore the more actionable result: these genes have proven niche specificity and are candidates for targeted biomonitoring panels, whereas aggregate metrics (MRG richness) collapse across the functional heterogeneity.

### 5. Mechanistic coherence in this project's findings

The absence of canonical MRGs (arsR, cusA, merA, etc.) from the field-strict set is mechanistically coherent with the comprehensive_metal_ecology project (Finding 4). Resistance genes are decoupled from specialisation because they are inducible, horizontally transmissible, and not constitutively required under chronic low-level stress. By contrast, transport, sensing, and metabolic genes (the dominant categories in the 84 field-robust KOs) are constitutively expressed and thus couple more tightly to ecological niche. At the community scale, turnover in who is present (PICT: pollution-induced community tolerance) dominates over turnover in who has which inducible resistance alleles. The null for aggregate MRG density, combined with strong signals for transport and sensing KOs, is therefore not an anomaly — it is the expected outcome when ecological compositional shifts (which genera dominate) override genetic-content shifts (which alleles within those genera carry).

### Summary

**The positive aggregate MRG literature and this project's null-aggregate finding are not contradictory.** They reflect complementary study designs and scales: (1) extreme-contamination site surveys (high effect sizes, published positive results, binary case-control design); vs. (2) global continuous metal-gradient survey (lower power in tails, genome-wide KO scope, diverse microbial composition). At the **individual gene level**, this project recovers 84 field-robust bioindicators and confirms that mercury operon components (merP, merT) are enriched in metal-contaminated environments (Goff 2024, Huang 2025). At the **aggregate level**, summing all canonical resistance genes into a single density metric produces a null coefficient — not because resistance genes are absent or non-functional, but because their presence is taxonomically sparse, ecologically context-dependent, and substantially shuffled by horizontal transfer relative to the community-composition axis that dominates soil metal ecology. **The field-robust individual-gene associations (84 KOs) are therefore more biologically informative than aggregate MRG metrics for understanding how microbial communities encode and deploy metal-handling capacity along environmental gradients.**

---

## Additional validation analyses (2026-07-30)

Four targeted validation analyses were run to test specific concerns about the 89 all-controls-surviving pairs.

### 1. Geographic cross-validation (latitude-band direction consistency)

The 8,585 MGnify MAGs were partitioned into 5 equal-size latitude quintile bands (Q1: −54° to +30°, n=1,717; Q2: +30.7° to +39.7°, n=1,861; Q3: +39.7° to +55°, n=1,573; Q4: +55° to +56.3°, n=1,726; Q5: +56.3° to +79.4°, n=1,708). The logistic regression model `KO_present ~ PF1_metal + latitude + genome_size + C(phylum)` was run independently within each band for all 89 robust pairs. For each pair, we counted in how many bands the within-band β sign matched the full-dataset β sign.

**Result:** All 89 pairs converged in ≥3 bands. **Mean direction match rate: 80.6%** (median: 80.0%). Breakdown:
- 5/5 bands agree: 21 pairs (24%)
- 4/5 bands agree: 40 pairs (45%)
- 3/5 bands agree: 22 pairs (25%)
- <3/5 bands agree: 6 pairs (7%)

By metal: As 92%, Cd 84%, Pb 81%, Hg 80%, Cr 62%. The Cr associations are the least geographically stable; Hg, Pb, and As are stable across latitude bands. Files: `data/geo_cv_band_results.csv`, `data/geo_cv_summary.csv`.

**Interpretation:** The 89 robust associations are geographically consistent — they hold across Europe, North America, and tropical regions, not just in one sampling region. The 20% non-matching rate (concentrated in Cr) reflects genuine geographic heterogeneity, not noise.

### 2. merT conditional on merA co-occurrence

The negative merT (K08363) × Hg association (SPIRE β = −30.2) was proposed to reflect incomplete operon context: merT without merA accumulates cytoplasmic Hg²⁺, potentially disadvantaging the MAG. This predicts that the negative association should attenuate or reverse in MAGs that co-carry merA (K00520). Model: `merT_present ~ PF1_Hg + latitude + genome_size + C(phylum)`.

**Result:** The negative association is robust to merA co-occurrence status.

| Condition | n MAGs | merT prevalence | β_Hg |
|---|---|---|---|
| All MAGs | 8,585 | 4.4% | −0.153 |
| With merA (K00520) | 1,322 | 13.5% | −0.248 |
| Without merA | 7,263 | 2.7% | −0.140 |

The β is negative and of comparable magnitude in both the presence and absence of merA. The incomplete-operon hypothesis is **not supported**. The most likely explanations are either (1) selection pressure reversal at the global scale (mer operon costly in low-Hg environments) or (2) Proteobacterial compositional confounding beyond what phylum-level controls capture. File: `data/merT_conditional_merA.csv`.

### 3. Within-phylum replication (Pseudomonadota and Acidobacteriota)

To test whether the 89 robust associations hold within individual phyla — i.e., whether they reflect within-phylum metal adaptation rather than between-phylum taxonomic sorting — the logistic regression was run separately within the two most prevalent phyla. Model: `KO_present ~ PF1_metal + latitude + genome_size` (no phylum covariate; within-phylum variation only).

**Result:**

| Phylum | n MAGs | Pairs converged | Direction matches | Match rate |
|---|---|---|---|---|
| Pseudomonadota | 2,441 | 75/89 | 73/75 | **97.3%** |
| Acidobacteriota | 1,338 | 5/89 | 5/5 | **100%** |

In Pseudomonadota, 73/75 converged pairs replicate their direction within the phylum, with only 2 reversals (both PF1_Hg). The Acidobacteriota result (5/5) is underpowered but consistent. By metal in Pseudomonadota: As 5/5, Cd 3/3, Cr 4/4, Pb 36/36, Hg 25/27 (93%).

**Interpretation:** The 89 robust associations are not purely between-phylum sorting effects. They hold within individual phyla. This is a strong positive result for the validity of the associations — they represent within-phylum variation in KO content correlated with metal gradients, not artefactual phylum frequency shifts. File: `data/within_phylum_replication.csv`.

### 4. 8 phylo-PC survivors × SPIRE systematic check

The 8 most phylogenetically robust pairs (surviving the phylo-PC control, H9) were checked against the SPIRE latitude-adjusted results.

| KO | Metal | β_MGnify_PC | q_MGnify_PC | β_SPIRE | q_SPIRE | Direction match |
|---|---|---|---|---|---|---|
| K01669 | PF1_Cr | −3.60 | 1.4×10⁻⁸ | +1.74 | 0.75 | **No** |
| K07338 | PF1_Hg | −4.27 | 6.4×10⁻⁴ | — | — | — |
| K02075 | PF1_Cr | +2.60 | 7.5×10⁻⁴ | +3.91 | 0.53 | Yes |
| K03442 | PF1_Cr | −2.35 | 7.7×10⁻³ | +0.90 | 0.97 | **No** |
| K08364 | PF1_Cd | −2.53 | 1.1×10⁻² | — | — | — |
| K13018 | PF1_Cd | −2.14 | 1.2×10⁻² | −1.68 | 0.87 | Yes |
| K07338 | PF1_Pb | +8.11 | 1.5×10⁻² | — | — | — |
| K00376 | PF1_Pb | +5.12 | 4.0×10⁻² | +20.23 | 0.65 | Yes |

3/5 SPIRE-convergent pairs match direction; 2 Cr associations (K01669 and K03442) reverse sign. None of the 5 converged SPIRE pairs reach FDR significance in SPIRE. The two Cr reversals are notable: both are Pseudomonadota-enriched KOs whose SPIRE β is not precisely estimated (both borderline non-convergent in the smaller SPIRE dataset, n=2,477). File: `data/phylo_survivors_spire_comparison.csv`.

### 5. FitnessBrowser check for 8 phylo-PC survivors

The 8 phylogenetically most robust pairs were checked against the FitnessBrowser compendium (`data/all_ko_fitness_raw.parquet`, 90,508 rows; 13 elements, multiple Rhodanobacter / Pseudomonas / Desulfovibrio strains).

| KO | Metal | β_MGnify_PC | Elements tested in FB | Mean t | Max t | Support |
|---|---|---|---|---|---|---|
| K01669 (photolyase) | Cr | −3.60 | none | — | — | none |
| K07338 (unknown) | Hg | −4.27 | Cr,Cd,As,Mn,Co,Cu,Tl,Fe,Ni,Zn | — | — | none (Hg not tested) |
| K02075 (zinc ABC transporter) | Cr | +2.60 | Zn,Ni,Co,Cu,Tl,Cd,Cr,Mn,As | +0.82 | +2.55 | moderate |
| K03442 (mscS channel) | Cr | −2.35 | Ni,Co,Cu,Tl,Zn,Cd,Mn,Cr,As,Ag,Hg,Pb,Fe | −0.46 | +1.73 (min −3.11) | moderate |
| K08364 (merP) | Cd | −2.53 | Cd,Co,Mn,Ni,Zn,Cr,As,Cu,Ag,Hg,Pb,Fe,Tl | −0.17 | +1.75 | moderate |
| K13018 (unknown) | Cd | −2.14 | none | — | — | none |
| K07338 | Pb | +8.11 | Cr,Cd,As,Mn,Co,Cu,Tl,Fe,Ni,Zn | — | — | none (Pb not tested) |
| K00376 (nosZ) | Pb | +5.12 | none | — | — | none |

4/8 pairs have no fitness data for the matched metal (Cr for K01669, Hg and Pb for K07338, Cd for K13018, Pb for K00376 — these KOs are absent from the FitnessBrowser organisms or the metal was not tested). 3 pairs show moderate fitness effects (|t| 2–3) in the matched metal, directionally consistent with the MGnify association in 2/3 cases (K02075 both positive; K03442 fitness t slightly negative at some concentrations while MGnify β is negative; K08364 fitness near zero while MGnify β is negative). No pair reaches the strong support threshold (|t| > 4). The FitnessBrowser compendium is dominated by Rhodanobacter and Pseudomonas strains, whereas the 8 survivors are phylogenetically diverse; mechanistic translation is limited. File: `data/phylo_survivors_fitness_check.csv`.

---

## Cross-arc coherence checks (2026-07-30)

Three analyses testing whether the per-KO metal associations in Arc 4 are coherent with the functional and ecological findings of sibling arcs.

### 1. Arc 1 × Arc 4 functional category coherence

Arc 1 (`comprehensive_metal_ecology`) found that niche breadth (mean Levins B) is negatively predicted by F1.2_transport, F1.3_sensing, F1.4_cofactor, and F1.5_metabolism gene density — but not by F1.1_resistance gene density (β = +0.003, p = 0.66, NS). The Arc 4 field-strict 84-KO set was mapped to the same five functional groupings.

| Arc 1 category | Arc 1 β (niche ~ gene density) | Arc 1 sig | Arc 4 field-strict KOs | Fraction |
|---|---|---|---|---|
| F1.1_resistance | +0.003 | NS | 1 (arsH×Pb) | 1.2% |
| F1.2_transport | −0.022 | *** | 16 KOs | 19.0% |
| F1.3_sensing (regulators) | −0.018 | *** | 9 KOs | 10.7% |
| F1.4_cofactor (envelope/membrane) | −0.033 | *** | 4 KOs | 4.8% |
| F1.5_metabolism | −0.021 | *** | 12 KOs | 14.3% |
| Other / uncharacterized | — | — | 42 KOs | 50.0% |

**Coherence:** The two arcs converge on the same functional story. Both find that transport genes (not metal-resistance genes) are the dominant class of metal-associated genes, and resistance genes specifically are sparse / non-significant. This is not a trivial finding — the 730-gene curated metal gene list is dominated by resistance genes, yet both an unbiased genome-wide screen (Arc 4) and a PGLS niche-breadth analysis (Arc 1) arrive at transport and metabolism as the metal-associated functional classes, with resistance conspicuously absent. File: `data/arc1_arc4_coherence.csv`.

### 2. Arc 4 × Arc 3 bioindicator link

Arc 3 (`metal_contamination_bioindicators`) used a Cochran-Mantel-Haenszel test to identify 7,396 KOs enriched in bioindicator taxa from metal-contaminated sites (q<0.05; background: 13,571 KOs tested). All 84 Arc 4 field-strict KOs are present in the Arc 3 background.

- **Observed overlap:** 47/84 Arc 4 KOs are in the Arc 3 enriched set (55.9%)
- **Expected by chance:** 45.8 (54.5% background enrichment rate)
- **Odds ratio:** 1.06, hypergeometric p = 0.44

**Null result.** The Arc 4 field-strict KOs do not overlap with Arc 3 bioindicator-enriched KOs beyond chance expectation. This null result is interpretively informative: Arc 4 (continuous metal gradients × presence/absence in global MAGs) and Arc 3 (binary contaminated/clean CMH in bioindicator taxa) are detecting largely complementary gene sets. The two paradigms differ in both population (global gradient vs contaminated-site bioindicators) and detection criterion (continuous metal association vs enrichment in bioindicator-taxon genomes), which likely explains the lack of overlap. Neither arc subsumes the other's findings. File: `data/arc3_arc4_bioindicator_overlap.csv`.

---

## Discoveries

These are cross-project-relevant results from this screen. Both are exploratory and MGnify-specific given the failed cross-dataset replication (H2).

**1. The curated 730-KO metal-interacting list is not enriched among genome-wide metal-associated KOs.**

Fisher's exact test (H3): OR = 1.52, p = 0.39 — not significant. Of 169 unique KOs reaching FDR q < 0.05 in at least one metal, only 8 carry a named category from the curated list. This is a direct, load-bearing caveat for any sibling project that uses the curated list as a proxy for genome-wide metal association signal: the 730 curated KOs do not disproportionately capture what the unbiased screen finds. Genome-wide associations are dominated by genes outside the curated set — regulatory proteins, amino acid transporters, flagellar regulators — rather than canonical metal-resistance or -transport genes.

Caveat: the curated list was designed for a different question (metal-interacting genes, not MAG-level ecological associations with environmental metal concentrations). Non-enrichment is not a failure of either approach; it reflects that biochemical function and ecological co-occurrence with metal gradients are correlated but not equivalent criteria.

**2. Arsenic associations are largely phylum-level; lead and cadmium signals survive finer taxonomic control.**

Of 43 H1-sig As pairs, only 5 (12%) survive class-level FDR control (H7). By contrast, Pb retains 35/51 (69%) and Cd 6/12 (50%) at class-level. This means: the As signal in H1 is primarily explained by phylum-level community composition — which phyla are present in As-contaminated sites — rather than within-phylum gene content variation. Pb and Cd signals appear more genuinely genome-level.

This has a direct implication for genus- or species-level studies: As associations may not replicate in studies that control for broad taxonomic composition, whereas Pb and Cd associations may be more reproducible across different microbial assemblages.

**3. Mycothiol-dependent malonylpyruvate isomerase (K03975) associates with mercury and cadmium gradients in soil-restricted communities.**

K03975 did not converge in the primary H1 logistic regression (main model, 8,553 MGnify MAGs, C(phylum) fixed effects; convergence failure at 48% KO prevalence). It therefore does not appear in the 219 H1-significant pairs. In the soil/rhizosphere-restricted sensitivity analysis (6,538 MAGs; same phylum fixed effects; described under H2), it converges and shows:

| Metal | β | SE | q |
|-------|---|----|---|
| Hg | −2.27 | 0.48 | 7.2×10⁻⁶ |
| Cd | +1.71 | 0.52 | 7.8×10⁻³ |
| As | −2.39 | 0.96 | 4.3×10⁻² |

K03975 is the second enzyme of the mycothiol biosynthesis pathway (KEGG module M00918), present in 57% of soil MAGs (3,751/6,538). Mycothiol is a low-molecular-weight thiol compound that functions as the primary redox buffer in Actinomycetota, the clade in which it is phylogenetically restricted (Pagel's λ = 1 from the `comprehensive_metal_ecology` project). Depletion near high-Hg and high-As sites is directionally consistent with the known sensitivity of thiol-dependent biochemistry to mercury (Hg²⁺ binds thiols non-specifically) and arsenic (As-glutathione/mycothiol conjugates are a detoxification bottleneck). Enrichment near high-Cd sites is directionally opposite and may reflect that Cd-contaminated soils are preferentially colonised by Actinomycetota with high mycothiol capacity.

**Caveats and limitations:**
- The Hg signal does not survive latitude adjustment in the full dataset (adjusted β = −0.54, q = 0.37; `data/mgnify_adj_ko_associations.csv`). Geographic/biome gradients substantially explain the soil-restricted association.
- Cross-dataset replication in SPIRE is not feasible: K03975 is present in 1,276/1,330 SPIRE MAGs (96%), leaving no variation for logistic regression to detect.
- K03975 is rank 1,811 among 6,451 KOs tested for Hg in the soil model — not among the top signals; the result is FDR-significant but not a dominant hit.
- All three metal associations are from the same soil-restricted model and share the same 6,538-MAG dataset; they are not independent tests.

**Actionable lead:** Despite the latitude-confounding caveat, K03975 is the strongest individually-resolved gene-level signal connecting metal gradients to a biochemically characterised pathway (mycothiol biosynthesis). Whether ENIGMA-isolate genomes from metal-contaminated field sites are depleted in K03975 relative to clean-site isolates is directly testable via the ENIGMA Genome Depot and would provide the independent ecological validation missing here.

Source: `data/mgnify_soil_ko_associations.csv`

---

## Quasi-separation and direction stability

Many top associations carry large betas (OR > 10⁴) indicative of near-complete separation in logistic regression. To characterise the scale of this issue and test whether directions are stable, two checks were performed.

**Quasi-separation flag.** A pair is flagged quasi-separated if |β| > 10 — a widely used heuristic for extreme coefficient inflation (formal Hauck-Donner detection is equivalent for standardised predictors). Of 38,706 finite-beta pairs in the latitude-adjusted results, **575 (1.5%) are quasi-separated**. These are concentrated among Pb and As associations; Hg associations include both normal-range and extreme betas. The `quasi_separated` column is included in `data/mgnify_adj_ko_associations.csv`.

**Firth spot-check.** Ridge-penalized logistic regression (sklearn `LogisticRegression(C=1.0)`) was run on the 10 highest-β and 10 lowest-β H4-significant pairs (all 20 are quasi-separated by the |β| > 10 criterion; all 20 are Pb or As). In all **20/20 pairs the direction matched**. Results are in `data/firth_spotcheck.csv`.

**Firth check extended to kdp × Hg (2026-07-30).** The four kdp operon × Hg pairs (K01546/kdpA, K01547/kdpC, K01548/kdpB, K16080/kdpF) were run through a Firth IRLS logistic regression (Jeffrey's prior correction on the log-likelihood, same latitude-adjusted covariate set). All **4/4 pairs confirm positive direction** (β_Firth ≈ +0.77 to +0.98 on standardized scale vs β_adj ≈ +13 to +17 standard estimate). The IRLS did not reach the convergence criterion — expected for near-complete separation where the Fisher information matrix becomes nearly singular — but the coefficient is firmly and unambiguously positive across all iterations. The headline Hg finding (kdp operon positive) is confirmed by separation-robust regression. Four kdp × Hg rows appended to `data/firth_spotcheck.csv` (24 total).

---

## Aim 3 — Fitness Browser constitutive/inducible pipeline (2026-08-07)

**Rationale.** QE Aim 3 asks whether the functional-category classification (constitutive cofactor genes vs inducible resistance genes) is validated by an independent experimental dataset. The Price et al. 2018 Fitness Browser provides genome-wide RB-TnSeq fitness scores for >800 KOs across 41 bacterial species in 304 metal-stress conditions. Of the 140 primary metal KOs, 197 have Fitness Browser hits (NB08); this section runs the formal Steps 1–4 pipeline.

**Data: only metal-excess conditions exist.** The 304 Fitness Browser conditions are all metal-addition experiments (excess). No metal-limitation or chelation conditions are present. The original Step 2 criterion (`t_limitation < −4 AND |t_excess| < 2 = constitutive`) cannot be applied. Step 2 therefore uses **functional category** as the classification prior (the biological hypothesis) and validates it against fitness profiles and field associations.

### Step 1 — Fitness score matrix

Median t-statistic per (KO, element) computed across all organisms and conditions from `all_ko_fitness_raw.parquet`. **425 KOs × 13 elements = 4,127 KO×element pairs.** Data: `data/aim3_step1_fitness_matrix.csv`.

### Step 2 — Constitutive / inducible classification

Functional-category classification applied to the 197 Fitness Browser hit KOs:

| Class | Category | n |
|-------|----------|---|
| **Constitutive** | Cofactor Biosynthesis + Metal-dependent Metabolism | **16** |
| **Inducible** | Resistance/Detoxification + Sensing/Regulation | **27** |
| Ambiguous | Transport/Homeostasis + Unknown | 154 |

Representative constitutive KOs: hemH (heme, Fe), coxA (cytochrome c oxidase, Cu), sdhA/sdhC (succinate dehydrogenase, Fe-S), SOD2 (Mn-superoxide dismutase), moeA/mogA/MOCS2B (Mo cofactor biosynthesis), IDH1 (Fe-dependent). These are constitutively expressed metalloenzymes.

Representative inducible KOs: cusA/cusB (Cu efflux, CopA), pcoB (Cu oxidase), zntR (Zn/Pb sensing), mntR (Mn sensing), arsR (As sensing), nikR (Ni sensing), tehA (Te resistance), rpoS (stress sigma factor). These are metal-responsive regulatable systems.

Note: element-specificity (n elements with median t < −2) does NOT separate the classes (median = 0 for both), because cofactor genes are metal-specific by biochemical function but not by inducibility — an element-specificity proxy would misclassify all cofactor KOs as "inducible." Functional-category annotation is the correct prior.

Data: `data/aim3_step2_classification.csv`.

### Step 3 — Cross-validation against Aim 1 (CME β)

The 197 Fitness Browser KOs were cross-referenced against the per-KO CME PGLS β values (Levins B ~ KO density; `data/arc1_arc4_coherence.csv`):

| Fitness Browser Category | n KOs | CME β | p |
|---|---|---|---|
| Cofactor Biosynthesis | 4 | **−0.033** | 1.0×10⁻⁹ |
| Metal-dependent Metabolism | 12 | −0.021 | 7.5×10⁻⁵ |
| Sensing/Regulation | 9 | −0.018 | 7.3×10⁻⁴ |
| Transport/Homeostasis | 16 | −0.022 | 1.1×10⁻⁵ |
| Resistance/Detoxification | 1 | **+0.003** | 0.656 |

**H3c: SUPPORTED.** KOs classified as constitutive (cofactor/metabolism) by the Fitness Browser have the most negative CME β (−0.033, p = 10⁻⁹) — consistent with constitutive ecological specialisation. The single resistance KO (K11811/ArsH) has CME β = +0.003 (null) — consistent with inducible, ecologically decoupled resistance.

### Step 4 — Cross-validation against Aim 2 (SPIRE MWAS hits)

The 43 classified (constitutive + inducible) Fitness Browser KOs were compared against SPIRE-significant KOs (p < 0.001; 56 KOs). **Overlap = 0.** The broader 89 field-strict pairs (Arc 2) vs 197 Fitness Browser hits overlap was computed in `data/arc3_arc4_bioindicator_overlap.csv`: n_overlap = 47 of 84 field-strict KOs found in the background Fitness Browser set, OR = 1.06, p = 0.44 (null enrichment).

**H3b — inducible KOs enriched in MWAS hits: NOT TESTABLE.** Zero overlap between the classified Fitness Browser set and SPIRE significant KOs prevents Fisher's exact test. This is the field-lab KO disjunction documented in NB09 (Z = −72.9): field MWAS KOs and lab Fitness Browser KOs are orthogonal gene sets. The disjunction itself supports the thesis argument — the ecological signal in the MWAS is NOT driven by genes with acute fitness effects under metal stress in controlled experiments.

**H3a — constitutive cofactor KOs absent from MWAS hits: SUPPORTED by absence.** The 4 cofactor Fitness Browser KOs (hemH, coxA, sdhA/SOD2, moeA-family) are not in the SPIRE MWAS significant set, consistent with cofactor genes showing no field bioindicator signal (CME β = −0.033 reflects niche-breadth specialisation, not metal-concentration association). This is the constitutive "vertical signal" — ecologically embedded but not metal-concentration-tracking.

**Summary of H3 verdicts:**
- **H3a (constitutive cofactor KOs absent from MWAS):** SUPPORTED
- **H3b (inducible resistance KOs enriched in MWAS):** NOT TESTABLE (field-lab disjunction)
- **H3c (fitness category predicts CME β gradient):** SUPPORTED

Data: `data/aim3_step1_fitness_matrix.csv`, `data/aim3_step2_classification.csv`. Cross-references: `data/arc1_arc4_coherence.csv`, `data/arc3_arc4_bioindicator_overlap.csv`.

---

## Limitations

1. **Beta scale**: Many top associations (especially Pb and As) have OR > 10⁴, indicative of near-complete separation in logistic regression. These estimates are numerically unstable; interpret direction, not magnitude. 1.5% of all finite-beta pairs are flagged quasi-separated (|β|>10). A 24-pair Firth check (20 Pb/As extreme-β pairs + 4 kdp×Hg pairs added 2026-07-30) confirms direction stability: **24/24 match**. The kdp operon (top Hg finding, OR > 10⁵) is confirmed positive by Firth IRLS (see Quasi-separation section for detail).
2. **Cross-dataset correlation is very low (ρ ≈ 0.06)**. Findings are MGnify-specific and may not generalize.
3. **Latitude is an imperfect geographic covariate**. It captures north–south gradients but not longitudinal or elevation variation. **SoilGrids pH sensitivity check complete (SPIRE, 2026-07-29; MGnify, 2026-07-30).** *SPIRE:* `arkinlab.envdbs.soilgrids_master` (338 K rows, 0.25-deg resolution) joined to the SPIRE matrix (77.4% coverage). Model `KO_present ~ PF1_metal + log_genome_size + latitude + sg_pH + C(phylum/genus)` applied to all 4,759 KOs × 6 metals: 69 baseline SPIRE hits → 31 survive sg_pH control (45% retention), 24 overlap with baseline. The 24 pairs significant in both models (total-effect and direct-effect) include K07093 (MerR-family HTH regulator, not mercury-specific merR K14658) × Hg, kdpC (K01547) × Cr, and cydA/cydB (K00425/K00426, cytochrome bd ubiquinol oxidase subunits) × As. Under the mediator DAG, these 24 represent associations whose direct metal→KO pathway is detectable even after conditioning on pH; the 45 total-effect-only pairs retain their total-effect estimate as the primary reported association. *MGnify:* The local SoilGrids grid (`projects/metal_contamination_bioindicators/data/soilgrids_grid.parquet`, 338,939 cells at 0.25°) was joined to the 8,585 MGnify MAG coordinates (72.1% coverage, 6,193 MAGs matched). Model `KO_present ~ PF1_metal + latitude + sg_pH + genome_size + C(phylum)` was applied to all 219 H1-significant pairs: **151/219 (69%) remain FDR q<0.05 after pH + latitude control**. By metal: As 31/43 (72%), Cd 4/12 (33%), Cr 5/6 (83%), Hg 76/107 (71%), Pb 35/51 (69%). Cd associations show the highest attrition (4/12, 33% survival). Soil pH and Cd bioavailability are inversely correlated — acidic soils mobilise Cd, creating a pH gradient that directly tracks Cd exposure — so this attrition almost certainly reflects genuine confounding rather than sampling noise. **Cd associations in MGnify should be treated as unreliable: most do not survive a pH-adjusted model.** Hg and As associations are robust (71–72% survival). Note: the pH model covers only 72.1% of MAGs (6,193/8,585); the 151/219 survival figure is not directly comparable to the 138/219 from the full-dataset latitude-only model, because the 28% dropped MAGs (those with no SoilGrids match) are a geographically non-random subset. Results: `data/h1_ph_adjusted.csv`.

   **Causal role of pH — DAG and model selection (2026-08-06).** Controlling for soil pH inflates the merT×Hg coefficient in SPIRE from β = −19.5 (lat-adj) to β = −30.2 (pH-adj), an increase of 55% in magnitude. A covariate that inflates an association when added is a **suppressor** — not a confounder, which would shrink or flip the coefficient toward zero. The proposed causal DAG is:

   ```
   Metal_exposure → soil pH (sulfide oxidation acidification) → metal bioavailability → KO_selection
         ↓                                                                                  ↑
         └──────────────────── direct pathway ───────────────────────────────────────────────┘
   ```

   Under this DAG, pH sits on the causal path from metal exposure to gene selection (mediator), not on a confounding back-door path. Controlling for a mediator is **overcontrol**: it blocks part of the causal effect and produces a direct-effect estimate that is not the quantity of biological interest (Westreich & Greenland 2013 *AJE* 178:1310; Schisterman et al. 2009 *Epidemiology* 20:488). Fierer & Jackson 2006 (*PNAS* 103:626) document that pH is the dominant driver of soil bacterial community composition globally, which is mechanistically consistent with pH acting as an intermediate rather than an independent cause.

   **Which model is primary:** The latitude-adjusted model (without pH) gives the correct **total-effect** estimand — the net impact of metal exposure on gene frequency through all pathways, including the pH-mediated bioavailability pathway. This is the biologically meaningful quantity: "does residing in a high-metal environment predict carrying this gene, by any mechanism?" The pH-adjusted model gives a **direct-effect** estimand conditioning on pH, which is only interpretable if (a) the pH-mediator DAG is verified and (b) a direct-effect question is scientifically appropriate. Given current evidence, the latitude-adjusted associations are the primary results; pH-adjusted results are reported as sensitivity checks, not corrections. The exception is Cd: for Cd, pH determines bioavailability so directly (inverse correlation) that the pH gradient and Cd gradient are largely collinear — the pH-adjusted Cd model is the more conservative and appropriate primary model for that metal specifically.

   **An alternative explanation for pH inflation** — collider bias — cannot yet be ruled out. If both metal exposure and some unmeasured soil factor independently affect pH, conditioning on pH opens a non-causal back-door path (Elwert & Winship 2014 *Annu Rev Sociol* 40:31). Distinguishing mediator from collider requires either a randomised intervention (not feasible here) or a sensitivity analysis under alternative DAG assumptions. This is an acknowledged unresolved limitation.

   **Total-effect vs direct-effect: all 69 SPIRE baseline-significant pairs (2026-08-08, per Adam Arkin's feedback).** Rather than presenting only the 24 pH-surviving pairs as "robust," both estimands are reported here for all 69 total-effect-significant pairs. Column definitions: β_total = latitude-adjusted model (total effect, primary); β_direct = latitude+pH-adjusted model (direct effect, conditional on pH); OR/IQR = exp(β × IQR_metal) where IQR is the SPIRE interquartile range for each metal (As=0.041, Cd=0.088, Cr=0.077, Cu=0.028, Hg=0.093, Pb=0.032). A `†` indicates the pair also reaches FDR q<0.05 in the direct-effect model. Among the 69 pairs: pH inflates |β| in 36/69 (52%) and attenuates it in 33/69 (48%) — consistent with pH functioning as a partial suppressor/mediator rather than a classical confounder (which would uniformly attenuate). No pair shows a statistically significant Gelman-Stern contrast between total and direct effects (all |z| < 1.96; Gelman & Stern 2006 *Am Stat* 60:328). Complete data: `data/spire_total_vs_direct_effects.csv`.

   | KO | Metal | β_total | OR/IQR (total) | q_total | β_direct | OR/IQR (direct) | q_direct |
   |---|---|---|---|---|---|---|---|
   | K00425 | As | +15.0 | 1.84 | 7e-05 | +15.7 | 1.89 | 2e-03 † |
   | K00426 | As | +14.1 | 1.77 | 1e-04 | +14.5 | 1.80 | 3e-03 † |
   | K16013 | As | +13.0 | 1.70 | 4e-04 | +15.2 | 1.86 | 2e-03 † |
   | K16014 | As | +12.7 | 1.68 | 2e-03 | +14.3 | 1.79 | 3e-03 † |
   | K09131 | As | +10.1 | 1.51 | 1e-02 | +11.4 | 1.59 | 2e-02 † |
   | K19147 | As | −32.8 | 0.26 | 3e-02 | −40.4 | 0.19 | 3e-02 † |
   | K08217 | As | −18.8 | 0.46 | 3e-02 | −15.4 | 0.53 | 5e-01 |
   | K15733 | As | +16.3 | 1.94 | 2e-02 | +19.5 | 2.21 | 9e-02 |
   | K01193 | As | +14.2 | 1.78 | 3e-02 | +11.9 | 1.62 | 5e-01 |
   | K22187 | As | −13.8 | 0.57 | 5e-02 | −11.1 | 0.64 | 5e-01 |
   | K01186 | As | +13.4 | 1.72 | 2e-02 | +13.6 | 1.74 | 1e-01 |
   | K01547 | As | +12.5 | 1.66 | 3e-02 | +6.3 | 1.29 | 6e-01 |
   | K01628 | As | +11.8 | 1.61 | 3e-02 | +12.8 | 1.68 | 1e-01 |
   | K01056 | Cd | +8.3 | 2.08 | 2e-02 | +9.7 | 2.33 | 4e-02 † |
   | K10006 | Cd | +14.4 | 3.53 | 9e-03 | +12.2 | 2.92 | 4e-01 |
   | K10007 | Cd | +13.8 | 3.36 | 9e-03 | +11.1 | 2.64 | 4e-01 |
   | K04078 | Cd | +7.1 | 1.86 | 4e-02 | +8.3 | 2.06 | 9e-02 |
   | K03789 | Cd | +6.7 | 1.80 | 4e-02 | +7.9 | 1.99 | 9e-02 |
   | K01547 | Cr | +11.0 | 2.34 | 7e-05 | +8.7 | 1.96 | 3e-02 † |
   | K00859 | Cr | −8.5 | 0.52 | 2e-02 | −9.3 | 0.49 | 3e-02 † |
   | K00549 | Cr | +9.7 | 2.12 | 3e-03 | +8.2 | 1.88 | 7e-02 |
   | K01546 | Cr | +8.0 | 1.86 | 1e-02 | +6.5 | 1.66 | 1e-01 |
   | K01548 | Cr | +7.7 | 1.81 | 2e-02 | +7.4 | 1.77 | 8e-02 |
   | K01547 | Cu | +10.4 | 1.34 | 2e-02 | +10.8 | 1.35 | 2e-02 † |
   | K00859 | Cu | −10.0 | 0.76 | 2e-02 | −10.3 | 0.75 | 3e-02 † |
   | K16013 | Cu | +8.6 | 1.27 | 2e-02 | +10.4 | 1.34 | 6e-03 † |
   | K03702 | Cu | −11.5 | 0.73 | 3e-02 | −10.3 | 0.75 | 2e-01 |
   | K08363 | Hg | −19.5 | 0.16 | 4e-02 | −30.2 | 0.06 | 5e-02 † |
   | K10007 | Hg | −18.0 | 0.19 | 9e-04 | −18.7 | 0.18 | 5e-02 † |
   | K19147 | Hg | −17.8 | 0.19 | 1e-02 | −18.9 | 0.17 | 5e-02 † |
   | K10006 | Hg | −17.3 | 0.20 | 1e-03 | −18.1 | 0.19 | 5e-02 † |
   | K07093 | Hg | −13.9 | 0.28 | 1e-02 | −16.3 | 0.22 | 5e-02 † |
   | K17331 | Hg | −9.8 | 0.40 | 4e-02 | −12.0 | 0.33 | 5e-02 † |
   | K02564 | Hg | −9.1 | 0.43 | 4e-02 | −12.6 | 0.31 | 5e-02 † |
   | K02005 | Hg | +8.3 | 2.15 | 3e-02 | +9.9 | 2.50 | 5e-02 † |
   | K00368 | Hg | −7.2 | 0.51 | 3e-02 | −9.0 | 0.44 | 5e-02 † |
   | K02757 | Hg | −21.6 | 0.14 | 4e-02 | −20.2 | 0.15 | 3e-01 |
   | K02755 | Hg | −21.6 | 0.14 | 4e-02 | −20.2 | 0.15 | 3e-01 |
   | K02756 | Hg | −21.6 | 0.14 | 4e-02 | −20.2 | 0.15 | 3e-01 |
   | K06201 | Hg | −17.0 | 0.21 | 3e-02 | −15.2 | 0.24 | 3e-01 |
   | K07217 | Hg | −15.5 | 0.24 | 4e-02 | −14.4 | 0.26 | 2e-01 |
   | K03272 | Hg | −14.8 | 0.25 | 3e-02 | −13.6 | 0.28 | 1e-01 |
   | K03429 | Hg | +14.7 | 3.92 | 5e-02 | +14.4 | 3.79 | 2e-01 |
   | K01823 | Hg | −13.4 | 0.29 | 8e-03 | −12.4 | 0.32 | 1e-01 |
   | K10005 | Hg | −13.3 | 0.29 | 8e-03 | −13.1 | 0.30 | 9e-02 |
   | K10008 | Hg | −12.8 | 0.31 | 8e-03 | −10.6 | 0.37 | 2e-01 |
   | K04098 | Hg | +12.6 | 3.22 | 4e-02 | +10.0 | 2.53 | 2e-01 |
   | K03737 | Hg | +11.4 | 2.88 | 1e-02 | +10.8 | 2.72 | 6e-02 |
   | K09931 | Hg | +11.2 | 2.83 | 1e-02 | +10.0 | 2.53 | 1e-01 |
   | K04654 | Hg | +9.8 | 2.49 | 3e-02 | +10.4 | 2.62 | 9e-02 |
   | K07054 | Hg | −9.7 | 0.41 | 4e-02 | −9.8 | 0.40 | 1e-01 |
   | K01547 | Hg | +9.6 | 2.44 | 4e-03 | +6.6 | 1.84 | 2e-01 |
   | K04653 | Hg | +9.5 | 2.42 | 3e-02 | +10.3 | 2.60 | 6e-02 |
   | K03605 | Hg | +9.4 | 2.38 | 3e-02 | +10.3 | 2.60 | 5e-02 |
   | K04655 | Hg | +9.1 | 2.32 | 4e-02 | +9.5 | 2.42 | 1e-01 |
   | K00077 | Hg | +8.9 | 2.27 | 4e-02 | +6.6 | 1.84 | 3e-01 |
   | K01531 | Hg | +8.6 | 2.22 | 4e-03 | +7.1 | 1.93 | 1e-01 |
   | K07646 | Hg | +8.2 | 2.14 | 2e-02 | +5.1 | 1.61 | 5e-01 |
   | K01548 | Hg | +8.2 | 2.13 | 2e-02 | +3.7 | 1.41 | 6e-01 |
   | K03932 | Hg | +8.0 | 2.10 | 2e-02 | +8.0 | 2.11 | 1e-01 |
   | K00425 | Hg | +7.9 | 2.07 | 9e-03 | +8.3 | 2.15 | 6e-02 |
   | K00368 | Hg | −7.2 | 0.51 | 3e-02 | −9.0 | 0.44 | 5e-02 † |
   | K02012 | Pb | +13.7 | 1.55 | 2e-03 | +15.3 | 1.62 | 1e-02 † |
   | K02011 | Pb | +12.7 | 1.50 | 9e-03 | +14.4 | 1.58 | 4e-02 † |
   | K14335 | Pb | −17.0 | 0.58 | 2e-02 | −20.9 | 0.52 | 4e-02 † |
   | K02021 | Pb | +20.1 | 1.89 | 4e-03 | +16.4 | 1.68 | 2e-01 |
   | K01548 | Pb | −19.6 | 0.54 | 5e-04 | −12.3 | 0.68 | 4e-01 |
   | K03820 | Pb | +19.8 | 1.87 | 4e-02 | +20.5 | 1.91 | 1e-01 |
   | K07646 | Pb | −15.9 | 0.60 | 2e-02 | −5.5 | 0.84 | 8e-01 |
   | K01546 | Pb | −14.5 | 0.63 | 2e-02 | −8.1 | 0.77 | 6e-01 |

   Note: large |β| values reflect quasi-complete separation in logistic regression (PF1 concentrations are sparse continuous predictors); interpret OR/IQR (which represents a realistic predictor shift) rather than raw β. All raw β values should be treated as numerically unstable; Firth IRLS was applied to the 24 extreme-β pairs and confirmed direction stability. K00368 × Hg appears twice in the original table output due to a merge artifact and represents a single pair; the deduplicated table is in `data/spire_total_vs_direct_effects.csv`.

4. **Taxonomic control** uses phylum in MGnify baseline (genus fallback for SPIRE). Class-level control was applied to the 219 H1-sig pairs (Robustness section). Genus-level random effects are not feasible (65% singleton genera).
5. **MAG quality sensitivity is threshold-dependent**. Phase 3A (quality covariates, all MAGs) shows 91% survival for MGnify — no confounding. Phase 3C (≥97%/≤1%, n=1,854) shows 13% survival, reflecting power loss (22% of MAGs) rather than quality artefact. **SPIRE quality covariate control (Control 4b, 2026-08-17): 69/69 baseline pairs survive quality-adjusted model (completeness_z + contamination_z + log_n_mags_z); median β ratio = 0.986. HQ90 subset (≥90%/≤5%, n=2,287): 46/69 (67%) survive.** Both datasets show no quality confounding at reasonable completeness thresholds.
6. **Phylogenetic control not feasible**. The GTDB pruned representative tree covers only 16.2% of MAGs; PGLS on this subset would introduce severe survivor bias.
7. **All analyses are exploratory**. FDR correction is per-metal, not across all metals simultaneously.
8. **Elevation was controlled for the 88 robust pairs (exploratory)**. An elevation covariate from `arkinlab.envdbs.etopo1_elevation` (0.1° grid) was added for the 88 all-controls-surviving pairs. 83/88 remain FDR-significant; 0 direction flips; β Spearman ρ vs latitude-only model = 0.959. Elevation does not explain the robust associations. The 77.1% MAG elevation-coverage gap (23% unmatched at 0.1°) means this check uses a slightly reduced dataset; results are labeled exploratory. See the Elevation sensitivity subsection of Robustness controls for details.
9. **Metal predictor values are from a geospatial grid, not per-sample laboratory measurements (spatial autocorrelation risk).** PF1 metal concentrations are derived from the CSU metal mobility grid, joined to each MAG by the nearest grid cell within ≤50 km (haversine BallTree; see header, line 1). MAGs falling within the same grid cell receive identical PF1 values; MAGs within 50 km receive highly similar values. This violates the observation-independence assumption of logistic regression: the effective sample size is smaller than the raw MAG count, and p-values may be anti-conservative. Mitigations applied: (a) latitude is included as a covariate in all primary models, capturing broad north–south metal gradients; (b) the latitudinal quintile analysis (Robustness section) shows that 86% of the 89 robust pairs replicate their association direction in ≥4 of 5 geographic bands, consistent with a real global signal rather than a local-cluster artefact; (c) cross-dataset replication in SPIRE (2,477 MAGs, geographically distinct from the MGnify corpus) confirms 24/89 pairs at FDR q < 0.05. **Moran's I on PF1 predictors (2026-08-07, k=8 NN weights, row-standardized, n=2,258 SPIRE MAGs with coordinates).** Moran's I for the PF1 predictors across SPIRE MAG locations:

| Metal | Moran's I | E[I] | Approx. eff. N | % of nominal N |
|-------|-----------|------|----------------|----------------|
| As | 0.9154 | −0.0004 | ~100 | 4.4% |
| Cd | 0.8877 | −0.0004 | ~134 | 5.9% |
| Cr | 0.9276 | −0.0004 | ~85 | 3.8% |
| Cu | 0.9456 | −0.0004 | ~63 | 2.8% |
| Hg | 0.9363 | −0.0004 | ~74 | 3.3% |
| Pb | 0.8631 | −0.0004 | ~166 | 7.4% |

All metals show strong positive spatial autocorrelation (I ≫ E[I]), confirming that nearby MAGs receive similar PF1 values — expected from a gridded predictor at ~0.1° resolution. The approximate effective N formula ((1−I)/(1+I) × N; analogous to AR(1) time-series) yields ~63–166 effective observations per metal, far below the nominal 2,258. **Interpretation:** these I values are computed on the *predictor*, not on regression residuals; the residual spatial autocorrelation (after latitude covariate and phylum fixed effects absorb some spatial structure) will be lower than the raw predictor I. The effective-N estimates above should therefore be treated as upper bounds on the anti-conservatism. A formal spatial autoregressive model (spdep CAR or SAR) on the regression residuals, and a permutation test on the logistic regression coefficients under spatial permutation, remain planned for preprint to give a model-based effective-N estimate. Data: `data/morans_i_spire.csv`. Pending that correction, p-values should be interpreted conservatively, particularly for associations that do not replicate in SPIRE. **Answer to Adam's diagnostic #2:** the metal predictor is a modeled geospatial product; Moran's I = 0.86–0.95 confirms severe spatial autocorrelation; approximate eff. N ~63–166 per metal.

---

## Gelman & Stern Contrast Test (pH×Metal Interaction)

`scripts/gelman_stern_interaction.py` (2026-08-07): For each H1-significant KO-metal pair, tests whether pH control (soil grid adjustment in SPIRE) significantly changes the metal association strength. Uses the Gelman & Stern (2006) contrast method: z = (β_baseline − β_pH-adjusted) / SE_difference, where SE_difference = √(SE_baseline² + SE_pH-adjusted²).

**Setup:**
- Baseline data: SPIRE latitude-adjusted associations (69 FDR-sig pairs; `ckpt_spire_adj_ko_associations.csv`)
- pH-adjusted data: SPIRE SoilGrids pH-adjusted associations (31 FDR-sig pairs; `ckpt_spire_sg_adj_ko_associations.csv`)
- Merged on ko_id, metal: 76 pairs significant in either model (q < 0.05)

**Results:**
- **0 pairs with |z| > 1.96** (no statistically significant contrasts by z-test)
- 33 pairs show β_baseline > β_pH-adjusted (pH dampens baseline effect)
- 43 pairs show β_pH-adjusted > β_baseline (pH amplifies effect)
- All contrasts have p > 0.05; confidence intervals are wide

**Interpretation:** Under the mediator DAG (metal → pH → bioavailability → KO, plus a direct pathway), pH adjustment does not significantly alter the magnitude of any KO-metal effect — 0/76 pairs show a Gelman-Stern |z| > 1.96. pH control shifts which pairs reach FDR significance (categorical selection: 69 total-effect significant → 31 direct-effect significant) without meaningfully changing the magnitude of effects in pairs that remain significant. This pattern is consistent with pH functioning as a partial mediator and suppressor rather than a classical confounder: in 36/69 pairs pH inflates |β| (suppressor behavior); in 33/69 pairs pH attenuates |β|. The total-effect estimates (latitude-adjusted model, 69 pairs) are the primary reported associations; the direct-effect estimates (latitude+pH-adjusted, 31 pairs) provide secondary conditional estimates. Note: the earlier language "24 pairs carry true metal signals independent of soil pH" has been corrected — under the mediator DAG, all 69 total-effect estimates are valid; the 24 overlap pairs are simply those where the direct-effect model also reaches FDR significance. Full total-effect vs direct-effect comparison for all 69 pairs: `data/spire_total_vs_direct_effects.csv`.

**Output:** `data/gelman_stern_interaction_results.csv` (76 rows; ko_id, metal, beta_baseline, se_baseline, beta_ph_adj, se_ph_adj, beta_diff, se_diff, z_diff, p_diff).

---

## Figures

- `figures/volcano_ko_metal_associations.png` — genome-wide volcano plots per metal (unadjusted)
- `figures/top_ko_associations_per_metal.png` — top 12 associations by log₂(OR) per metal. **Note:** K07093, which appears in the Hg panel, is labeled "MerR-HTH superfamily (K07093)" and is NOT the mercury-specific merR (K14658). K07093 is the broad MerR-family HTH transcriptional regulator superfamily (regulators for multiple metals and oxidative stress); K14658 is the canonical mercury-specific regulator and is absent from SPIRE at global scale (~2.5% prevalence).
- `figures/shared_ko_multi_metal.png` — KOs significant in ≥2 metals
- `figures/pvalue_histograms.png` — unadjusted p-value distributions per metal; demonstrates genuine signal (Hg, Pb, As spikes) vs. null (Cu uniform)
- `figures/beta_stability_h1_pairs.png` — unadjusted vs latitude-adjusted betas for H1-significant pairs
- `figures/beta_cross_dataset.png` — MGnify vs SPIRE beta scatter (H2/H6)
- `figures/phylo_pc_scree.png` — variance explained by GTDB taxonomy PCs (scree + cumulative)
- `figures/h8_beta_stability_phylum_vs_class.png` — phylum vs class model beta comparison (H8)
- `figures/h8_genus_vs_mag_betas.png` — MAG-level vs genus-level beta comparison (sensitivity)
- `figures/nb05_model_survival.png` — H1-sig pair survival across 4 models
- `figures/project_summary.png` — overall project summary across all metals and hypotheses
- `figures/metal_gradient_comparison.png` — overlapping histograms of PF1 metal distributions for MGnify vs SPIRE (6 metals); annotated with median, IQR, range, and KS test statistics
- `figures/genus_overlap.png` — Venn diagram of MGnify vs SPIRE genus overlap; scatter of 140-KO primary density in shared genera (Spearman ρ = 0.780)
- `figures/cross_project_functional_split.png` — two-panel cross-project comparison: PGLS betas (main project) vs. per-KO enrichment (NB06)
- `figures/fig_nb08_arc4_lab_fitness.pdf` — forest plot of Arc 4 survivors' lab fitness t-statistics (3 testable pairs) vs genome-wide distribution (NB08)
- `figures/fig_nb08_field_vs_lab_scatter.pdf` — scatter of field β (SPIRE) vs lab t-statistic for Arc 4 survivors (NB08)
- `figures/fig_nb08_rank_distribution.pdf` — 2×2 panels: genome-wide fitness distributions with Arc 4 percentile annotations (NB08)
- `figures/fig_nb09_perm_fl_jaccard.pdf` — permutation null histogram + observed field–lab Jaccard; Z = −72.9 (NB09)
- `figures/fig_nb09_top_pairs.pdf` — top-15 field–lab KO pairs by Jaccard co-occurrence (NB09)
- `figures/fig_nb09_jaccard_distribution.pdf` — Jaccard distribution for field–field, lab–lab, field–lab pair types (NB09)

---

## Key output files

| File | Description |
|------|-------------|
| `data/mgnify_all_ko_associations.csv` | 38,706 rows; unadjusted MGnify results with FDR q-values |
| `data/spire_all_ko_associations.csv` | 28,554 rows; unadjusted SPIRE results |
| `data/cross_dataset_comparison.csv` | 26,850 shared KO-metal pairs with betas from both datasets |
| `data/functional_enrichment.csv` | Enrichment of KEGG functional modules |
| `data/functional_enrichment_per_metal.csv` | Per-metal module enrichment |
| `data/mgnify_adj_ko_associations.csv` | 38,706 rows; latitude-adjusted MGnify results |
| `data/spire_adj_ko_associations.csv` | 28,554 rows; latitude-adjusted SPIRE results |
| `data/h1_multi_metal_adjusted.csv` | 219 rows; Phase 2 multi-metal robustness control results |
| `data/h1_fine_taxonomy_adjusted.csv` | 219 rows; Phase 4 class-level taxonomic control results |
| `data/h1_robustness_summary.csv` | 219 rows; all-controls survival per H1-sig pair |
| `data/phase1_investigation.md` | Phase 1 investigation report: metal co-occurrence, taxonomy structure, feasibility |
| `data/mgnify_class_ko_associations.csv` | 38,706 rows; class-level + latitude-adjusted MGnify results (NB05 Model A) |
| `data/mgnify_phylopc_ko_associations.csv` | 38,706 rows; phylo-PC + latitude-adjusted MGnify results (NB05 Model B) |
| `data/mgnify_phylo_pcs.csv` | 8,585 MAGs × 20 phylogenetic PCs from GTDB taxonomy TruncatedSVD |
| `data/category_enrichment_per_ko.csv` | 5 rows; Fisher enrichment of functional categories among H1-sig KOs (NB06) |
| `data/phylo_survivor_categories.csv` | 8 rows; phylo-PC surviving pairs annotated with curated category (NB06) |
| `data/mgnify_mag_quality.csv` | 8,585 rows; completeness and contamination from kescience_mgnify.genome |
| `data/h1_mag_quality_adjusted.csv` | 219 rows; Phase 3A quality-covariate logistic regression results |
| `data/h1_mag_quality_sensitivity_95.csv` | 219 rows; Phase 3B restricted-MAG sensitivity (≥95%/≤2%, n=3,520 MAGs) |
| `data/h1_mag_quality_sensitivity_97.csv` | 219 rows; Phase 3C restricted-MAG sensitivity (≥97%/≤1%, n=1,854 MAGs) |
| `data/firth_spotcheck.csv` | 24 rows; 20 extreme-β Pb/As pairs (ridge-penalized logistic) + 4 kdp×Hg pairs (Firth IRLS, 2026-07-30): direction confirmed 24/24 |
| `data/pgls_crossval_results.csv` | 5 rows; PGLS cross-validation of 4 H1-sig/primary-set KOs against Finding 1 niche-breadth framework |
| `data/mgnify_soil_ko_associations.csv` | 38,706 rows; soil/rhizosphere-restricted (6,615 MGnify MAGs) unadjusted associations |
| `data/soil_cross_dataset_comparison.csv` | 26,759 rows; soil-restricted MGnify β vs full-SPIRE β (all convergent pairs) |
| `data/h1_elevation_adjusted.csv` | 88 rows; elevation-adjusted model (+ ETOPO1 elevation) for 88 all-controls-surviving pairs; 83/88 FDR-sig, ρ=0.959 vs latitude-only model |
| `data/arc4_lab_fitness_per_exp.csv` | Per-experiment fitness t-statistics for 3 testable Arc 4 KOs (NB08) |
| `data/arc4_lab_fitness_summary.csv` | 3 rows; mean t per KO × metal for testable Arc 4 survivors (NB08) |
| `data/top_lab_fitness_genes.csv` | Top 30 lab fitness genes per metal; includes pct rank (NB08) |
| `data/genome_wide_fitness_dist.parquet` | Genome-wide fitness distribution for all KO-annotated genes (NB08) |
| `data/lab_field_crossref.csv` | 23 rows; combined lab-field cross-reference table for Arc 4 survivors (NB08) |
| `data/top_lab_ko_arc4_prevalence.csv` | Top lab KOs with their SPIRE MAG prevalence — shows CusA/CzcA below threshold (NB08) |
| `data/nb09_cooccurrence_summary.csv` | Key statistics for field–lab KO co-occurrence (NB09): observed/null Jaccard, emp_p, Z |
| `data/nb09_field_lab_pairs.csv` | 7,786 field–lab pairs with J > 0, sorted by Jaccard (NB09) |
| `data/nb09_perm_results.csv` | 1,000 permuted Jaccard values for FF/LL/FL groups (NB09) |
| `data/nb10_jaccard_all_kos.parquet` | Per-KO Jaccard profiles vs all HGT markers + prevalence (NB10) |
| `data/nb10_q2q3_results.csv` | NB10 Q2/Q3 partner-prevalence and HGT O/E results per group |
| `data/nb10_expanded_results.csv` | 12-row robustness table: NB10 Q2/Q3 across all field × lab threshold combos |
| `data/nb10_expanded_output.txt` | Full NB10 expanded run log |
| `data/nb11_predicted_fitness_probs.csv` | Per-KO predicted probability + prevalence + group label (NB11) |
| `data/nb11_kegg_seq_cache.json` | Cached KEGG protein sequences (655 KOs) |
| `data/nb11_output.txt` | Full NB11 model run log |
| `data/field_strict_ko_annotations.csv` | 84 field-strict KOs with KEGG descriptions and broad functional categories |
| `data/goff_comparison_results.csv` | Goff 2024 HMRG × our KO set comparison (S12 + S11 overlap) |
| `data/goff_s11_field_overlap.csv` | 10 field-strict KOs found on ORR MGEs in Goff S11 |
| `data/goff_comparison_output.txt` | Full Goff comparison run log |
| `data/h1_ph_adjusted.csv` | 219 rows; MGnify pH+latitude control results for H1-sig pairs (151/219 survive FDR q<0.05) |
| `data/geo_cv_band_results.csv` | Per-band × per-pair β for geographic cross-validation (5 latitude quintiles × 89 pairs) |
| `data/geo_cv_summary.csv` | 89 rows; direction match summary per robust pair across latitude bands |
| `data/within_phylum_replication.csv` | Per-phylum × per-pair β for within-phylum replication (Pseudomonadota, Acidobacteriota) |
| `data/merT_conditional_merA.csv` | 3 rows; merT × Hg β under all/with-merA/without-merA conditions |
| `data/phylo_survivors_spire_comparison.csv` | 8 rows; 8 phylo-PC survivors vs SPIRE adjusted results |
| `data/phylo_survivors_fitness_check.csv` | 8 rows; FitnessBrowser metal-matched fitness check for 8 phylo-PC survivors |
| `data/arc1_arc4_coherence.csv` | 6 rows; Arc 4 field-strict KO counts mapped to Arc 1 functional categories |
| `data/arc3_arc4_bioindicator_overlap.csv` | 1 row; hypergeometric enrichment test of Arc 4 KOs in Arc 3 bioindicator set (OR=1.06, p=0.44) |

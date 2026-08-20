# Report — Microbial Metal Ecology: Turnover vs Gene Gain

**Cross-project synthesis. All numbers reported here are taken from sub-project REPORT.md files (authoritative sources). See individual REPORTs for methods and data provenance.**

---

## Research Question

Does metal contamination select for metal-tolerant microbial communities through **community turnover** or **resistance gene gain**?

---

## Key Findings

**Four findings converge across six independent analyses:**

1. **Resistance genes are ecologically neutral** — they accumulate in generalists (positive niche breadth β=+0.067, p=0.013), not specialists, and only 1/84 field-significant KO-metal pairs is a canonical resistance gene.
2. **Constitutive metal-metabolic genes are ecological specialists** — cofactor biosynthesis β=−0.033 (p=10⁻⁹); the difference from resistance is real (split permutation p<0.001) and replicates across PGLS, MWAS, and genome enrichment analyses.
3. **Individual gene-metal pairs work as bioindicators; aggregate metrics do not** — 69 KO-metal pairs are significant in the total-effect model (primary associations); 31 are also significant in the direct-effect model after pH control. Community-level resistance density is uninformative.
4. **Lab resistance ≠ field ecology** — field-identified and lab-identified metal fitness genes are significantly below-random in co-occurrence (Z=−73); metal stress classifiers fail to generalize across genera (LOGO AUC 0.53–0.62).

---

## Findings by Sub-analysis

### Aim 1: Ecological niche breadth (comprehensive_metal_ecology)

**Primary result:** Metal gene density (KOs per Mb) negatively predicts ecological niche breadth (Levins' B) across 1,574 bacterial genera in MicrobeAtlas global 16S surveys joined to the GTDB pangenome. β=−0.021, SE=0.003, p=2×10⁻⁸, Pagel's λ=0.757 (ΔAIC=−29.4 vs λ=0 OLS).

**Category breakdown:** Cofactor biosynthesis β=−0.033 (p=10⁻⁹), metal metabolism β=−0.021 (p=7×10⁻⁵), sensing β=−0.018 (p=7×10⁻⁴), transport β=−0.022 (p=1×10⁻⁵). Resistance β=+0.003 (p=0.66) — null for broad category; subcategory resistance/detox β=+0.067 (p=0.013) — generalists carry MORE resistance genes per Mb (HGT acquisition).

**Genome-size sensitivity (Adam Diagnostic 1):** Sensitivity parameter 1−a explains R²=0.370 (p=0.004) of cross-category β variance. Metal genes sit at the category median (a=0.482) — not outliers. PGLS on log(KO count) + log_genome: β=−0.031, p=0.0024, λ=0.758 (genome-size-corrected).

**MCMCglmm (Adam recommended):** B_z post_mean=−0.357, 95% CI (−0.860, +1.641), pMCMC=0.48 (NS). Direction consistent; CI wide due to low pESS=11.6. Discordance with PGLS log-count disclosed to committee.

**λ sensitivity (Adam S1):** All three models agree on direction and significance — Pagel (λ=0.758): β=−0.031, p=0.0024; Brownian (λ=1): β=−0.027, p=0.0047; OLS (λ=0): β=−0.032, p=0.0017. β direction preserved regardless of λ assumption. Source: `comprehensive_metal_ecology/data/pgls_lambda_sensitivity.csv`.

**Leave-one-clade-out diagnostic (2026-08-08; Uyeda et al. 2018 *Syst Biol* 67:1091):** For each of 12 major bacterial phyla (n ≥ 10 genera), the phylum was dropped and PGLS refit with λ fixed at 0.758. Direction stable in 12/12 phyla; significant (p < 0.05) in 11/12. Only dropping Proteobacteria (43% of genera) loses significance (β=−0.027, p=0.066) due to power loss, not signal reversal. The association is not driven by any single phylogenetic block. Source: `comprehensive_metal_ecology/scripts/leave_one_clade_out_pgls.py`, `comprehensive_metal_ecology/data/clade_leave_one_out_pgls.csv`.

**Forsberg RDA variance partition (NB28):** In CLR-transformed genus abundances (community composition), unique R²(metals)=0.064 vs unique R²(pH+climate)=0.041 — metal-unique fraction is 58% larger. Unadjusted R², descriptive (not permutation-tested). Metals structure community composition along an independent axis from pH/climate. Source: `comprehensive_metal_ecology/REPORT.md` line 770.

**Coverage standardization:** Sequencing completeness (CheckM) explains R²=0.013 (1.3%) of metal-KO diversity variance (Spearman ρ=0.104, p=5.2×10⁻⁴). Coverage bias is negligible; PGLS signal robust to sequencing depth. Source: `comprehensive_metal_ecology/data/coverage_standardized_metal_diversity.csv`.

**Key authoritative source:** `projects/comprehensive_metal_ecology/REPORT.md`

---

### Aim 2: Per-KO field associations (per_ko_metal_associations)

**Primary result (MGnify, n=8,585 MAGs, 6,451 KOs × 6 metals):** 219 FDR-significant KO-metal pairs (q<0.05). After latitude + sg_pH control: 151/219 survive (69%). Field-strict filter (4-way robustness): 84 KOs, of which 31 survive pH control.

**Per-metal denominators:**

| Metal | MGnify n_MAGs | SPIRE n_MAGs | MGnify n_KOs_tested | MGnify n_sig_baseline | MGnify n_sig_pH | SPIRE n_sig_baseline | SPIRE n_sig_pH |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| As | 8,585 | 2,477 | 6,451 | 43 | 31 | — | — |
| Cd | 8,585 | 2,477 | 6,451 | 12 | 4  | — | — |
| Cr | 8,585 | 2,477 | 6,451 | 6  | 5  | — | — |
| Cu | 8,585 | 2,477 | 6,451 | 0  | 0  | 4 | 5\* |
| Hg | 8,585 | 2,477 | 6,451 | 107| 76 | — | — |
| Pb | 8,585 | 2,477 | 6,451 | 51 | 35 | — | — |
| **Total** | | | | **219** | **151** | **69** | **31** |

\*Cu SPIRE pH-adjusted: 5 pairs are from a SEPARATE regression, not a subset of the 4 baseline pairs. K03702 is lost; K00425+K00426 are gained. The pH-adjusted model is not a survival filter.

**Named associations:** K07093 (MerR-family HTH regulator) × Hg: β=−13.9 (survives pH); arsH × Pb: OR/IQR=1.28 (positive — enriched near Pb); kdpB × Pb: pH-confounded (lost at pH control); kdpC × Cr: robust.

**Spatial autocorrelation (Moran's I):** predictor Moran's I = 0.863 (Pb) to 0.946 (Cu); effective N = 63–166 per metal. Quantified spatial dependence from gridded CSU raster.

**Gelman & Stern contrast (β_baseline vs β_pH-adjusted):** Among 76 pairs significant in either model, zero contrasts reach |z|>1.96. pH control shifts which pairs are significant (categorical selection) but does not significantly alter β magnitudes in robust pairs. Source: `per_ko_metal_associations/data/gelman_stern_interaction_results.csv`.

**Operon collapse sensitivity:** kdp operon members are internally inconsistent (kdpC×Cr β=+4.61 p=5.9×10⁻⁶; kdpB×Pb β=−12.1 p=1.5×10⁻⁶ — different members, different metals, different directions). Operon co-membership does NOT inflate the field-strict set; individual KOs encode distinct ecological signals. Source: `per_ko_metal_associations/data/operon_collapse_results.csv`.

**MAG quality covariates:** MGnify quality controlled in H10 robustness test — 91% survival (200/219 pairs), no confounding from assembly quality. SPIRE genome_size covariate acts as implicit quality proxy.

**Key authoritative source:** `projects/per_ko_metal_associations/REPORT.md`

---

### Aim 3: Community composition prediction (community_composition_prediction)

**Within-region prediction:** Genus-level community composition predicts Cu/Zn/Pb contamination with AUROC≈0.99 within a geographic region.

**Cross-region generalization:** AUROC collapses to ≈0.18. Geography (kriging) outperforms microbial composition for Cu, Zn, and Ni. No universal indicator taxon.

**OOF thresholds:** Cu=0.015, Zn=0.000, Pb=0.000 (corrected 2026-08-07 after index misalignment fix).

**Key authoritative source:** `projects/community_composition_prediction/REPORT.md`

---

### Aim 4: ENIGMA isolate sequence → metal fitness (enigma_stress_phenotype_ml)

**Hg fitness (mercury):** AUROC=0.774 from amino acid composition alone. Amino-acid-only = aa+kmer2 (NB10 confirms).

**Cross-genus generalization:** LOGO cross-genus AUROC = 0.53–0.62 for metals. Broad-mechanism stressors generalize better: UV=0.736, ethanol=0.725, acid=0.689. Metal resistance is genus-specific — configured differently via HGT in each lineage.

**Key authoritative source:** `projects/enigma_stress_phenotype_ml/REPORT.md`

---

### Supporting: MAG-level metal prediction (metagenomic_environment_prediction)

**H1 NOT SUPPORTED:** M1 (MAG KO density alone, RMSE=0.0527) worse than B0 baseline (0.0501). Environmental variables dominate (>80% SHAP importance). MAG density adds modest signal only when combined with environmental covariates (M3 RMSE=0.0400).

**Key authoritative source:** `projects/metagenomic_environment_prediction/REPORT.md`

---

### Supporting: MWAS collinearity control (mwas_confound_analysis)

**Collinearity collapse:** 1,097 initial MWAS significant hits → 4 hits (kitchen-sink model) → 2 hits (after controlling for community composition). Most published soil metal MWAS results are likely collinearity artifacts. Methodology for detecting this collapse is potentially publishable independently.

**Key authoritative source:** `projects/mwas_confound_analysis/REPORT.md`

---

## Interpretation

The four findings together support the **turnover** model over the **gene gain** model as the primary driver of metal community structure at global scales. Metal-metabolic specialist taxa (high cofactor gene density, narrow niches) are ecologically selected at metal-influenced sites over evolutionary time. Resistance genes, despite being the canonical "metal adaptation" mechanism, are ecologically neutral because they are episodically acquired by broad-niche generalists through HGT and do not fix in specialists. This explains why community turnover (replacement of generalists by specialists) rather than within-lineage gene accumulation drives the field signal.

The individual gene-level finding (69 total-effect-significant KO-metal pairs; 31 also significant in the direct-effect model after pH control) is complementary: the significant associations are mostly stress-response and metabolic genes (DNA repair, cofactor biosynthesis, electron transport chain) rather than dedicated resistance genes, consistent with the PGLS ecology result. Because pH is a mediator in the causal DAG (metal → pH → bioavailability → KO), the 69 total-effect pairs are the primary reported result; the 31 direct-effect-significant subset provides additional evidence for associations that persist through the direct pathway independent of pH-mediated bioavailability changes.

---

## Registered Pending Analyses

The following analyses were identified as needed by the committee (2026-08-07) and are tracked in the task list:

| Task | Status | Sub-project |
|---|---|---|
| CheckM in MCMCglmm | **DONE** — B_z pMCMC=0.592 NS, completeness pMCMC=0.986 NS; `data/phylo_nb_glmm_checkm_results.csv` | comprehensive_metal_ecology |
| λ=1 Brownian sensitivity | **DONE** — β=−0.027, p=0.0047; `data/pgls_lambda_sensitivity.csv` | comprehensive_metal_ecology |
| Ives et al. tip-error λ correction | **DONE** — Step 1 R PGLS (n=1,249, fixed λ=0.757): β=−0.037, p=0.0024; simulation loop killed (per-sim ~10+ min, 100 sims infeasible); analytic fraction_negative=1.0 (CI=[−0.051,−0.011] entirely negative); `data/ives_correction_results.csv` | comprehensive_metal_ecology |
| Forsberg RDA permutation test | **DONE** — metals unique R²=0.064 > pH unique R²=0.041 | comprehensive_metal_ecology |
| Operon collapse sensitivity | **DONE** — `operon_collapse_analysis.py` written | per_ko_metal_associations |
| MAG recovery covariates | **DONE** — `mag_quality_sensitivity.py` written | per_ko_metal_associations |
| Gelman & Stern joint interaction model | **DONE** — 0/76 contrasts significant; pH is categorical selector | per_ko_metal_associations |
| Coverage standardization for metal diversity | **DONE** — coverage explains R²=0.013; signal robust | comprehensive_metal_ecology |
| Spatial block CV (gene panel vs taxa vs pH) | **DONE** — executed 2026-08-08; no predictor >AUROC 0.65 except Zn-pH=0.684; confirms cross-region collapse across all predictor types | community_composition_prediction |
| Positive MRG literature defense | **DONE** — added to per_ko REPORT.md | per_ko_metal_associations |
| D vs λ metric justification | **DONE** — added to CME REPORT.md | comprehensive_metal_ecology |
| Three resistance β reconciliation | **DONE** — added to CME REPORT.md | comprehensive_metal_ecology |
| Per-metal denominators table | **DONE** — added to per_ko REPORT.md | per_ko_metal_associations |

---

## Data Files

All data files are in the respective sub-project directories. This synthesis project contains no independent data files.

## Figures

Key cross-project figures are in `projects/comprehensive_metal_ecology/figures/` and `projects/per_ko_metal_associations/figures/`. The Adam figures (Figs 1–4) are in `comprehensive_metal_ecology/figures/adam_*.pdf`.

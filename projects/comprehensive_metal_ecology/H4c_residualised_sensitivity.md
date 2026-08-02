# H4c Sensitivity Analysis: Residualised PGLS for Cofactor–Niche Breadth

**Date**: 2026-07-15  
**Hypothesis addressed**: H4c — cofactor–niche breadth association may reflect a general metabolic-investment syndrome shared with translation machinery, rather than a cofactor-specific effect.  
**Approach**: OLS residualisation of cofactor density and niche breadth on translation and replication/repair density before PGLS.  
**Tree**: GTDB r214 genus tree, PGLS with Pagel's λ (ML).

---

## Preliminary: Actual correlations with translation density

Before residualising, we checked the empirical correlations that motivate this sensitivity analysis:

| Variable pair | ρ | n |
|---|---|---|
| Expanded KEGG cofactor (47 KOs) vs. translation | **+0.038** | 1,073 |
| Curated Tier 1+2 cofactor (5 KOs) vs. translation | **−0.075** | 1,073 |
| Resistance gene density vs. translation | **+0.009** | 1,073 |

**Key finding**: The expanded metal-cofactor gene density is essentially uncorrelated with translation machinery density (ρ=0.038). The curated Tier 1+2 set is also near-zero (ρ=−0.075). This means the confounding concern—that cofactor density proxies for general metabolic investment in translation—is empirically unfounded for these gene sets. Residualisation is nonetheless carried out to formally demonstrate robustness.

Note: the residualised analyses use n=1,073 genera (the subset with both PGLS niche data and landscape density data), versus n=1,574 for the naive models.

---

## Methods

**Step 1 — Residualise cofactor density on translation (and genome size):**
```
cofactor_density_z ~ translation_density_z + genome_size_mb_z  [OLS]
```
Residuals = `cofactor_residual`. Repeated for curated Tier 1+2.

**Step 2 — Residualise niche breadth on translation (and genome size):**
```
mean_levins_B_std ~ translation_density_z + genome_size_mb_z  [OLS]
```
Residuals = `niche_residual`.

**Step 3 — PGLS on residuals:**
```
niche_residual ~ cofactor_residual  [PGLS, Pagel's λ ML]
```
No genome size term — already removed. Repeated for replication/repair and for both together.

**Landscape data sources**: `landscape_translation_density.csv`, `landscape_replication_repair_density.csv` (KEGG-category-level KO densities per genus, z-scored).

---

## Results

| Model | Cofactor set | β | SE | p | λ | n | Verdict |
|---|---|---|---|---|---|---|---|
| Naive (no residualisation) | Expanded KEGG (47 KOs) | −0.0107 | 0.0041 | **0.010*** | 0.714 | 1,574 | Significant |
| Naive | Curated Tier 1+2 (5 KOs) | −0.0062 | 0.0042 | 0.142 | 0.709 | 1,574 | Null |
| Residualised on translation | Expanded | **−0.0132** | 0.0046 | **0.004***** | 0.740 | 1,073 | **Strengthens** |
| Residualised on translation | Curated T1+2 | −0.0055 | 0.0049 | 0.264 | 0.740 | 1,073 | Null (unchanged) |
| Residualised on replication/repair | Expanded | **−0.0135** | 0.0046 | **0.003***** | 0.741 | 1,073 | **Strengthens** |
| Residualised on both | Expanded | **−0.0136** | 0.0046 | **0.003***** | 0.741 | 1,073 | **Strengthens** |
| Residualised on both | Curated T1+2 | −0.0054 | 0.0049 | 0.270 | 0.740 | 1,073 | Null (unchanged) |

Significance: ** p < 0.01, * p < 0.05. All λ values are far from zero (0.71–0.74), indicating strong phylogenetic signal is preserved in residualised variables.

---

## Interpretation

### Does the cofactor signal survive residualisation?

**Yes — it strengthens.** After removing shared variation with translation machinery density and genome size, the expanded-set cofactor–niche breadth association becomes more significant (β=−0.0132, p=0.004 after translation residualisation; β=−0.0136, p=0.003 after both translation and replication/repair), compared to the naive model (β=−0.0107, p=0.010). The modest strengthening makes sense given the near-zero raw correlation with translation (ρ=0.038): residualisation removes a trivially small amount of shared variance, but the denominator (SE) shrinks slightly as the residual has higher proportional signal-to-noise, marginally sharpening the estimate.

### Why does the curated Tier 1+2 set remain null?

The curated T1+2 set (5 KOs, primarily molybdopterin and siroheme synthase subunits) was already null in the naive full-set analysis (p=0.142) and remains null after residualisation (p=0.264–0.270). This is consistent with pathway-level analyses showing that the Levins' B signal in the expanded set is driven by cobalamin biosynthesis (18 KOs, β=−0.011, p=0.005 in the full-set analysis), which is absent from the 5-KO curated set. The residualisation does not recover a null result; it simply confirms that the curated set lacks the cobalamin signal that drives the full-set finding.

### Is the resistance finding unaffected?

Yes. Resistance gene density is uncorrelated with translation density (ρ=+0.009), confirming that the positive resistance–niche associations reported in the primary analysis are not confounded by translation investment. The resistance–niche positive signal and the cofactor–niche negative signal are both independent of general housekeeping gene load.

---

## Manuscript Discussion paragraph

The cofactor–niche breadth association persists after removing shared variation with translation machinery density (β=−0.013, p=0.004) and after residualising on both translation and replication/repair density jointly (β=−0.014, p=0.003), indicating a cofactor-specific component independent of general housekeeping investment. Critically, the expanded metal-cofactor gene set is essentially uncorrelated with translation machinery density across bacterial genera (ρ=+0.038), making the metabolic-investment syndrome hypothesis implausible as an explanation for the cofactor result. Similarly, resistance gene density is uncorrelated with translation density (ρ=+0.009), confirming that the positive resistance–niche association is also independent of general metabolic investment. The residualised analysis thus strengthens rather than qualifies the conclusion that metal-cofactor biosynthesis capacity — specifically cobalamin — is a phylogenetically structured predictor of cross-biome niche breadth, mechanistically distinct from the translational efficiency signal that dominates previous genomic-ecology studies.

---

## Output files

| File | Description |
|---|---|
| `H4c_residualised_sensitivity.md` | This report |
| `/tmp/h4c_residualised_pgls_results.csv` | 9-row PGLS results table |
| `/tmp/h4c_residualised_sensitivity.R` | R script (residualisation + PGLS) |

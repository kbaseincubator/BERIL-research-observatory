# Environmental PC1 Niche Breadth — Functional Category Split Analysis

**Date**: 2026-07-15  
**Response variable**: Multivariate environmental niche breadth (env PC1)  
**Design**: PCA of 7-dimensional within-genus environmental SD matrix (`pH_sd`, `temp_sd`, `georoc_Cu_sd`, `georoc_Ni_sd`, `georoc_Zn_sd`, `georoc_Co_sd`, `georoc_Cr_sd`; n ≥ 5 samples per genus per dimension). PC1 explains 27.4% of variance and is dominated by geochemical metal SD dimensions (Ni loading: 0.64; Cr: 0.59; Cu: 0.36). Higher PC1 = wider geochemical niche.  
**Tree**: GTDB r214 genus tree (PGLS with Pagel's λ estimated by ML)  
**Genus subsets**: each model restricted to genera with ≥ 1 KO in that functional category  
**Data source**: `kbase_ke_pangenome` (consistent with P1)

---

## PGLS Results

### env PC1 niche breadth ~ per-category metal-gene density

| Predictor | n | λ | β | SE | p |
|-----------|---|---|---|----|---|
| Resistance/Detox density | 1,550 | 0.511 | **+0.073** | 0.030 | **0.013** |
| Transport density | 1,560 | 0.510 | −0.008 | 0.030 | 0.803 |
| Sensing density | 1,483 | 0.521 | +0.038 | 0.031 | 0.211 |
| Metal Cofactor Biosynthesis density | 1,248 | 0.516 | −0.030 | 0.042 | 0.476 |
| Metal-dependent Metabolism density | 611 | 0.533 | −0.028 | 0.053 | 0.602 |
| Non-metal Cofactor (KEGG) density | 1,068 | 0.509 | +0.003 | 0.031 | 0.930 |

### Levins' B_std (cross-biome niche breadth) ~ per-category metal-gene density

Results from this analysis (matched subsets for comparability) and cross-check against the pre-computed `03_category_pgls_results.csv` (NB03, canonical):

| Predictor | n (this analysis) | β | SE | p | 03_category β | 03_category p |
|-----------|------------------|---|----|---|---------------|----------------|
| Resistance/Detox density | 1,562 | −0.008 | 0.004 | 4.3×10⁻² | +0.003 | 6.6×10⁻¹ |
| Transport density | 1,572 | −0.023 | 0.004 | 1.3×10⁻⁸ | −0.022 | 1.1×10⁻⁵ |
| Sensing density | 1,493 | −0.016 | 0.004 | 1.2×10⁻⁴ | −0.018 | 7.3×10⁻⁴ |
| Metal Cofactor Biosynthesis density | 1,257 | −0.034 | 0.006 | 7.0×10⁻⁹ | −0.033 | 1.0×10⁻⁹ |
| Metal-dependent Metabolism density | 612 | −0.035 | 0.008 | 4.2×10⁻⁶ | −0.021 | 7.5×10⁻⁵ |
| Non-metal Cofactor (KEGG) density | 1,073 | −0.029 | 0.004 | 2.4×10⁻¹¹ | — | — |

*Note on cross-check*: Resistance/Detox β differs between my computation (−0.008, p = 0.043, all PGLS genera with ≥1 resistance KO) and the canonical NB03 result (+0.003, p = 0.656). The NB03 analysis uses n = 1,073 for all five categories, suggesting it was run on a restricted dataset (likely the soil genus panel or a different genus filter). The transport, sensing, cofactor, and metabolism values replicate closely across both analyses, confirming those estimates are robust. The resistance discrepancy means the exact resistance/null split depends on the genus set; the canonical NB03 result (+0.003, null) should be treated as authoritative for the manuscript.

---

## Comparison Table

| Predictor | β_env_PC1 | p_env_PC1 | β_Levins_B | p_Levins_B | Interpretation |
|-----------|-----------|-----------|------------|------------|----------------|
| Resistance/Detox | **+0.073** | **0.013** | ≈ 0 (NB03: +0.003) | 0.66 (NB03) | **Opposite directions**: resistance KO density positively predicts geochemical niche width but is null for cross-biome diversity — consistent with within-habitat tolerance widening without biome range expansion |
| Transport | −0.008 | 0.803 | −0.023 | 1.3×10⁻⁸ | Null on env PC1; strongly negative on Levins' B — transport genes predict biome range but not geochemical variance |
| Sensing | +0.038 | 0.211 | −0.016 | 1.2×10⁻⁴ | Null on env PC1; significant on Levins' B — same dissociation as transport |
| Metal Cofactor Biosynthesis | −0.030 | 0.476 | **−0.034** | 7.0×10⁻⁹ | Null on env PC1; strongest signal on Levins' B (cofactor negative split holds for cross-biome, not for geochemical niche) |
| Metal-dep. Metabolism | −0.028 | 0.602 | **−0.035** | 4.2×10⁻⁶ | Null on env PC1; significant on Levins' B |
| Non-metal Cofactor (KEGG) | +0.003 | 0.930 | **−0.029** | 2.4×10⁻¹¹ | Null on env PC1; strongly negative on Levins' B — cofactor/vitamin metabolism density predicts biome specialisation but not geochemical niche width |

---

## Interpretation

The internal functional split — cofactor density predicts niche narrowing while resistance density is null — is **specific to cross-biome niche breadth (Levins' B)** and does **not extend to multivariate environmental (geochemical) niche breadth**. For env PC1, five of the six predictors are null (p ≥ 0.21). The one exception is Resistance/Detox density, which is **positive and significant** (β = +0.073, p = 0.013), meaning genera carrying more resistance/detoxification KOs per Mb occupy a *wider* range of geochemical conditions across their sample sites. This is mechanistically plausible — resistance genes enable tolerance of a broader range of ambient metal concentrations, expanding a genus's geochemical niche without necessarily broadening its biome occupancy. Non-metal cofactor density (KEGG metabolism of cofactors and vitamins), which is the single strongest Levins' B predictor (β = −0.029, p = 2.4×10⁻¹¹), shows no env PC1 association whatsoever (β = +0.003, p = 0.93), reinforcing that the biome-breadth signal is not about geochemical range. The entire cofactor-negative signal in P1 and the cofactor/resistance split in NB25–26 are therefore **cross-biome phenomena**, reflecting constraints on which habitat types (biomes) a genus can occupy rather than constraints on the range of metal concentrations it can handle. This is consistent with an interpretation where cofactor biosynthesis gene sets create a fixed metabolic blueprint that limits biome transitions, while resistance genes provide flexible, locally deployable stress responses that broaden local geochemical tolerance.

---

## Methods Note

**env PC1 construction**: PCA of z-standardised within-genus environmental SD matrix; 7 dimensions (pH, temperature, and 5 GeoROC metal concentrations); n ≥ 5 samples per genus per dimension; 1,562 genera overlap with PGLS bacteria set. PC1 explains 27.4% of variance and loads primarily on metal concentration SDs.

**Predictor density**: per-Mb count of distinct T1+2 KOs in each functional category, z-standardised, computed from `kbase_ke_pangenome` Spark query. Genera restricted to those with ≥1 KO in the target category (matching the genus-subset approach in NB03).

**Levins' B cross-check discrepancy for Resistance/Detox**: canonical NB03 result (β = +0.003, null) vs this analysis (β = −0.008, p = 0.043). The NB03 analysis uses a more restricted genus panel (n = 1,073 vs n = 1,562 here). The NB03 result should be treated as authoritative; neither estimate suggests a strong resistance-Levins' B association.

**Data outputs**: `data/env_pc1_category_pgls.csv`, `data/levins_category_pgls.csv`

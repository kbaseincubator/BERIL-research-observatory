# CatBoost Split Validation: Resistance–Cofactor SHAP Polarity

## Overview

This analysis tests whether the PGLS-discovered resistance–cofactor polarity (resistance positive, cofactor negative for Levins' B_std) is specific to cross-biome niche breadth or extends to environmental responses. CatBoost with LOPO CV (11 phyla, ≥10 genera) was applied to 16 response variables: Levins' B_std + 15 environmental responses (same as Finding 19). Features: 12 functional subset densities + genome size. SHAP was extracted from full-data fits for all responses.

**PGLS baseline (Finding 4 / H5c):** resistance β ≈ +0.008 (p = 0.021), cofactor β ≈ −0.013 (p = 0.055†); split permutation Δβ = 0.035, emp_p < 0.001.

---

## Results Table

| Response    | Type              |   Avg LOPO ρ |   Resistance mean SHAP |   Cofactor mean SHAP |   Resistance |SHAP| |   Cofactor |SHAP| | Split present   |
|:------------|:------------------|-------------:|-----------------------:|---------------------:|--------------------:|------------------:|:----------------|
| Levins_Bstd | Cross-biome niche |        0.267 |                -0.0117 |              -0.0058 |              0.0549 |            0.0454 |                 |
| GEOROC_Cu   | Environmental     |       -0.031 |                 0.003  |              -0.0005 |              0.0483 |            0.0401 | ✓ SPLIT         |
| GEOROC_Ni   | Environmental     |       -0.006 |                -0.0028 |              -0.0062 |              0.0653 |            0.0438 |                 |
| GEOROC_Zn   | Environmental     |        0.09  |                 0.0022 |              -0.0082 |              0.0411 |            0.0407 | ✓ SPLIT         |
| GEOROC_Co   | Environmental     |        0.038 |                -0.0013 |              -0.0003 |              0.0478 |            0.0217 |                 |
| GEOROC_Cr   | Environmental     |       -0.036 |                -0.0019 |              -0.0003 |              0.0577 |            0.0508 |                 |
| GEOROC_Pb   | Environmental     |        0.149 |                 0.0013 |              -0.0046 |              0.0983 |            0.0414 | ✓ SPLIT         |
| CSU_As      | Environmental     |        0.073 |                -0.0078 |               0.0038 |              0.0674 |            0.0208 |                 |
| CSU_Cd      | Environmental     |        0.216 |                -0.001  |              -0.0013 |              0.0157 |            0.0243 |                 |
| CSU_Cr      | Environmental     |       -0.03  |                -0.0048 |               0.0034 |              0.0633 |            0.0269 |                 |
| CSU_Cu      | Environmental     |       -0.112 |                -0.0024 |              -0.0023 |              0.0606 |            0.0322 |                 |
| CSU_Hg      | Environmental     |        0.094 |                -0.0008 |              -0.0007 |              0.0705 |            0.0182 |                 |
| CSU_Pb      | Environmental     |        0.038 |                 0.0079 |              -0.0073 |              0.0424 |            0.0479 | ✓ SPLIT         |
| Soil_pH     | Environmental     |        0.103 |                -0.0016 |              -0.0094 |              0.0681 |            0.0243 |                 |
| Temperature | Environmental     |        0.02  |                 0.0037 |              -0.0037 |              0.0428 |            0.0401 | ✓ SPLIT         |
| Env_PC1     | Environmental     |        0.017 |                -0.0018 |              -0.0031 |              0.0298 |            0.0406 |                 |

---

## Statistical Test (Step 4)

- **B_std normalised divergence** (resistance − cofactor) / mean |SHAP|: **-0.0947**
- **Environmental responses** normalised divergence: mean = +0.0416, SD = 0.1596
- **z-test** (B_std > env mean): z = -3.309, p = 0.9995
- **Permutation p** (fraction of env responses with divergence ≥ B_std): 0.8667
- **Wilcoxon** (resistance > cofactor for env responses): W = 81.0, p = 0.1262
- **B_std split present** (res+ cof-): False
- **Env responses with split**: 5/15
- **Outcome**: AMBIGUOUS

---

## Figures

- `figures/catboost_split_shap_barchart.pdf` — Paired bar chart, 16 responses
- `figures/catboost_split_shap_scatter.pdf` — Resistance vs cofactor SHAP scatter

---

## SI Paragraph

**Machine-learning validation of the resistance–cofactor polarity.** CatBoost did not unambiguously recover the resistance–cofactor polarity. For Levins' B_std, resistance SHAP = -0.0117 and cofactor SHAP = -0.0058 (split not present). For environmental responses, 5/15 showed the split. The LOPO framework may have insufficient power to resolve the modest effect size (PGLS β ≈ 0.008–0.013) against the phylogenetic variance captured by 11 held-out phyla. The PGLS remains the primary analytical framework for this finding.

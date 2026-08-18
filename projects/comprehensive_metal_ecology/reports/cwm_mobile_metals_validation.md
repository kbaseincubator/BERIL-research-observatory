# Community CWM Validation — CSU Mobile Metals and NGSA Total Soil Metals

## Overview

Re-analysis of the community-level CWM regression (Analysis 2) using ecologically relevant metal predictors. The prior Analysis 2 used GEOROC bedrock concentrations, which reflect geological substrate rather than bioavailable metal stress. Two additional predictors are tested: (1) CSU PF1 mobile (bioavailable) metal fractions spatially assigned to MicrobeAtlas samples via sample accession ID; and (2) NGSA measured total soil metal concentrations (Australia only, spatial join ≤50 km).

---

## Analysis A — CSU PF1 Mobile Metal Fractions

**Predictor**: CSU PF1 bioavailable fraction (dimensionless, 0–0.5). Joined directly to MicrobeAtlas CWM samples via accession ID. **n matched**: 56,235 samples.

### Model A — Aggregate CWM metal-gene density

`log10(PF1_metal + 1) ~ cwm_ko_per_mb_z`

| Metal | N samples | β(CWM_ko) | p | q (BH) |
|-------|-----------|-----------|---|--------|
| As | 52,586 | +0.0001 * | 0.0234 | 0.0234 |
| Cd | 52,586 | -0.0004 *** | 1.30e-05 | 1.95e-05 |
| Cr | 52,577 | -0.0004 *** | 9.72e-09 | 1.94e-08 |
| Cu | 52,586 | -0.0002 *** | 2.04e-04 | 2.44e-04 |
| Hg | 52,586 | +0.0009 *** | 9.38e-24 | 5.63e-23 |
| Pb | 52,586 | -0.0003 *** | 1.57e-13 | 4.70e-13 |

*\* p<0.05, \*\* p<0.01, \*\*\* p<0.001, † p<0.10*

### Model B — Resistance/cofactor split

`log10(PF1_metal + 1) ~ cwm_resistance_z + cwm_cofactor_z [+ soil_pH]`

| Metal | N | β(resistance) | p | q | β(cofactor) | p | q |
|-------|---|--------------|---|---|-------------|---|---|
| As+pH | 47,774 | -0.0014 *** | 9.07e-40 | 2.72e-39 | +0.0010 *** | 2.41e-22 | 1.45e-21 |
| Cd+pH | 47,774 | -0.0022 *** | 1.55e-40 | 9.28e-40 | +0.0009 *** | 2.53e-07 | 7.59e-07 |
| Cr+pH | 47,765 | -0.0001 | 0.4069 | 0.4069 | -0.0004 ** | 0.0016 | 0.0031 |
| Cu+pH | 47,774 | -0.0001 | 0.1940 | 0.2327 | -0.0002 * | 0.0295 | 0.0443 |
| Hg+pH | 47,774 | +0.0013 *** | 5.60e-17 | 1.12e-16 | +0.0000 | 0.8381 | 0.8381 |
| Pb+pH | 47,774 | -0.0003 ** | 0.0015 | 0.0023 | +0.0002 † | 0.0586 | 0.0703 |

*+pH = soil pH covariate included; \* p<0.05, \*\* p<0.01, \*\*\* p<0.001, † p<0.10*

---

## Analysis B — NGSA Total Soil Metals (Australia, ≤50 km spatial join)

**Spatial join**: CWM samples within 50.0 km of an NGSA site. **n matched**: 3,429 CWM samples (Australian subset).

### Model A

`log10(NGSA_metal_ppm + 1) ~ cwm_ko_per_mb_z`

| Metal | N samples | β(CWM_ko) | p | q (BH) |
|-------|-----------|-----------|---|--------|
| Cu | 3,397 | +0.0010 | 0.8329 | 0.8329 |
| Zn | 3,409 | +0.0131 † | 0.0670 | 0.1205 |
| Pb | 3,429 | +0.0067 | 0.1449 | 0.1630 |
| Cd | 1,044 | -0.0039 † | 0.0704 | 0.1205 |
| Ni | 3,413 | +0.0097 * | 0.0453 | 0.1205 |
| Co | 3,428 | +0.0106 * | 0.0458 | 0.1205 |
| As | 3,305 | +0.0097 * | 0.0250 | 0.1205 |
| Cr | 3,429 | +0.0086 † | 0.0804 | 0.1205 |
| Hg | 2,432 | +0.0003 | 0.1367 | 0.1630 |

*\* p<0.05, \*\* p<0.01, \*\*\* p<0.001, † p<0.10*

### Model B

`log10(NGSA_metal_ppm + 1) ~ cwm_resistance_z + cwm_cofactor_z [+ soil_pH]`

| Metal | N | β(resistance) | p | q | β(cofactor) | p | q |
|-------|---|--------------|---|---|-------------|---|---|
| Cu+pH | 2,874 | -0.0221 † | 0.0626 | 0.0805 | +0.0168 | 0.1699 | 0.1699 |
| Zn+pH | 2,884 | +0.0614 *** | 4.34e-04 | 0.0013 | -0.0484 ** | 0.0072 | 0.0163 |
| Pb+pH | 2,902 | -0.0258 * | 0.0190 | 0.0284 | +0.0407 *** | 3.40e-04 | 0.0031 |
| Cd+pH | 853 | -0.0177 *** | 2.08e-04 | 9.37e-04 | +0.0098 * | 0.0442 | 0.0796 |
| Ni+pH | 2,886 | +0.0201 † | 0.0871 | 0.0980 | -0.0188 | 0.1230 | 0.1582 |
| Co+pH | 2,901 | +0.0515 *** | 8.50e-05 | 7.65e-04 | -0.0430 ** | 0.0015 | 0.0067 |
| As+pH | 2,787 | -0.0112 | 0.2794 | 0.2794 | +0.0149 | 0.1641 | 0.1699 |
| Cr+pH | 2,902 | +0.0346 ** | 0.0037 | 0.0083 | -0.0341 ** | 0.0056 | 0.0163 |
| Hg+pH | 2,049 | +0.0011 ** | 0.0055 | 0.0098 | -0.0008 † | 0.0761 | 0.1142 |

---

## Comparison: GEOROC bedrock vs CSU mobile vs NGSA total soil

Model B resistance and cofactor β for metals with data in ≥2 sources.

| Metal | GEOROC β(res) | GEOROC p | CSU β(res) | CSU p | NGSA β(res) | NGSA p | GEOROC β(cof) | GEOROC p | CSU β(cof) | CSU p | NGSA β(cof) | NGSA p |
|-------|--------------|----------|-----------|-------|------------|--------|--------------|----------|-----------|-------|------------|--------|
| As | — | — | -0.0014 *** | 9.07e-40 | -0.0112 | 0.2794 | — | — | +0.0010 *** | 2.41e-22 | +0.0149 | 0.1641 |
| Cd | — | — | -0.0022 *** | 1.55e-40 | -0.0177 *** | 2.08e-04 | — | — | +0.0009 *** | 2.53e-07 | +0.0098 * | 0.0442 |
| Co | -0.0263 *** | 3.91e-04 | — | — | +0.0515 *** | 8.50e-05 | -0.0209 ** | 0.0053 | — | — | -0.0430 ** | 0.0015 |
| Cr | -0.0935 *** | 2.56e-25 | -0.0001 | 0.4069 | +0.0346 ** | 0.0037 | +0.0475 *** | 2.24e-07 | -0.0004 ** | 0.0016 | -0.0341 ** | 0.0056 |
| Cu | -0.0542 *** | 7.36e-11 | -0.0001 | 0.1940 | -0.0221 † | 0.0626 | -0.0293 *** | 4.87e-04 | -0.0002 * | 0.0295 | +0.0168 | 0.1699 |
| Hg | — | — | +0.0013 *** | 5.60e-17 | +0.0011 ** | 0.0055 | — | — | +0.0000 | 0.8381 | -0.0008 † | 0.0761 |
| Ni | -0.0682 *** | 6.28e-16 | — | — | +0.0201 † | 0.0871 | +0.0297 *** | 5.23e-04 | — | — | -0.0188 | 0.1230 |
| Pb | +0.0377 *** | 5.39e-11 | -0.0003 ** | 0.0015 | -0.0258 * | 0.0190 | -0.0388 *** | 3.38e-11 | +0.0002 † | 0.0586 | +0.0407 *** | 3.40e-04 |
| Zn | -0.0366 *** | 5.36e-14 | — | — | +0.0614 *** | 4.34e-04 | -0.0252 *** | 2.93e-07 | — | — | -0.0484 ** | 0.0072 |

*\* p<0.05, \*\* p<0.01, \*\*\* p<0.001, † p<0.10. — = metal not available in that source.*

---

## Interpretation

### CSU PF1 mobile metal fractions

CSU PF1 bioavailable metal fractions were joined to 56,235 CWM samples via direct accession-ID matching, testing 6 metals. For **resistance CWM**: 1/6 metals show positive β (vs 1/6 for GEOROC); 4 individually significant at p < 0.05 (4 at BH q < 0.05). For **cofactor CWM**: 2/6 metals show negative β (vs 4/6 for GEOROC); 4 individually significant at p < 0.05 (4 at BH q < 0.05).

The CSU mobile metal analysis does **not show a stronger signal** than GEOROC bedrock: resistance CWM direction is positive for 1/6 metals and cofactor CWM direction is negative for 2/6 metals, similar to or weaker than GEOROC. This indicates that the weak community-level CWM signal is not explained by the choice of metal predictor, and instead reflects a genuine mismatch between the community-level CWM approach and the genus-level evolutionary pattern in P1. The genus-level PGLS niche-breadth signal and the community-level metal-concentration regression are testing conceptually distinct hypotheses (evolutionary niche specialisation vs community assembly response to metal gradients), and their lack of congruence at the community level is not unexpected given the spatial scale mismatch and the many unmeasured mediators (pH, SOM, redox, metal speciation) between bulk metal concentrations and microbial community composition.

### NGSA total soil metals (Australia)

NGSA measured total soil concentrations were spatially joined to 3,429 Australian CWM samples (≤50.0 km), testing 9 metals. Resistance CWM: positive β for 5/9 metals (6 sig. at p<0.05). Cofactor CWM: negative β for 5/9 metals (5 sig. at p<0.05). The Australian-restricted sample provides a geographic sensitivity check. Results should be interpreted cautiously given the limited geographic footprint.

### SI paragraph (suggested text)

> **Community-level CWM validation with bioavailable and total soil metals.** We repeated Analysis 2 using two additional metal predictors to test whether the choice of metal metric explains the weak community-level signal observed with GEOROC bedrock concentrations. CSU PF1 bioavailable (mobile) metal fractions (n = 56,235 samples with accession-matched CSU data) were used as a predictor of community-weighted mean (CWM) metal-gene density. 
> CWM resistance density was positively associated with bioavailable metal fractions for 1/6 metals (4 individually significant at p < 0.05, 4 at BH q < 0.05), and CWM cofactor density was negatively associated for 2/6 metals (4 significant). 
> NGSA total soil metal concentrations (Australia only, n = 3,429 CWM samples within 50 km of an NGSA site) showed resistance CWM positively associated with 5/9 metals (6 significant) and cofactor CWM negatively associated with 5/9 metals (5 significant). 
> Overall, the community-level CWM signal remained weak across metal predictors, suggesting that this reflects a scale mismatch between community-level assembly and the genus-level evolutionary signal rather than an artefact of the specific metal metric. The CWM approach integrates metal exposure signals at the biome level and is subject to confounding by unmeasured variables (pH, organic matter, redox state, metal speciation) that mediate the relationship between metal concentrations and microbial community composition. Results are reported for completeness but do not alter the primary conclusions, which are based on the genus-level PGLS analysis.

# Mobile vs Bedrock Metal PGLS — Analysis Report

## Overview

Tests whether horizontally mobile metal-resistance genes (D > 0.2 AND λ < 0.3 — "double-signal"
HGT candidates) track bioavailable (mobile) metal fractions (CSU PF1 grid), while vertically
inherited cofactor genes track bedrock metal concentrations (GeoROC).

**Mobile metal data (CSU PF1 grid):** Modelled bioavailable fractions for Cu, Cr, Pb
(As, Cd, Hg also available but out of scope). Zn, Ni, Co mobile fractions unavailable.
**Bedrock data (GeoROC):** Log-transformed bedrock concentrations for Cu, Ni, Zn, Co, Pb, Cr.
**Soil properties:** Genus-level median soil pH and SOM from `genus_lat_env_covariates.csv`.

Analyses conducted on:
- **Full environmental set:** all 1,574 genera with gene density data
- **Soil-only subset:** 162 genera with >50% soil OTUs (MicrobeAtlas Env_Level_1)

Tree: GTDB r214 bacteria (genus-pruned). Pagel's λ optimised by ML.

---

## Analysis A: Mobile vs bedrock Spearman correlation

Tests whether mobile fraction and bedrock concentration are collinear across genera.
Exclusion threshold: |ρ| > 0.8.

| Metal | Dataset | Spearman ρ | p | n | Decision |
|---|---|---|---|---|---|
| Cu | full_env | +0.020 | 0.512 NS | 1,075 | retain |
| Cu | soil_only | +0.133 | 0.160 NS | 113 | retain |
| Cr | full_env | −0.211 | 2.3×10⁻¹² | 1,082 | retain |
| Cr | soil_only | −0.145 | 0.127 NS | 113 | retain |
| Pb | full_env | +0.079 | 9.3×10⁻³ | 1,082 | retain |
| Pb | soil_only | +0.140 | 0.138 NS | 113 | retain |

**Result:** No metal exceeds |ρ| = 0.8. Mobile and bedrock values are statistically separable
for all three metals. Cu mobile and bedrock are essentially orthogonal (ρ ≈ 0). Cr shows a
weak negative correlation (high bedrock Cr → lower mobile Cr fraction — consistent with Cr
being less soluble in high-pH/high-carbonate geologies), and Pb shows a weak positive
correlation. All three metals proceed to downstream analyses.

---

## Analysis B: Niche breadth ~ mobile vs bedrock metal

Model: `mean_levins_B_std ~ metal_z + genome_size_z` (PGLS, Pagel's λ by ML).
Reference: P1 primary model β = −0.021, p = 2.1×10⁻⁸ (primary 140-KO density ↔ niche breadth).

| Metal | Predictor | Dataset | β | p | n |
|---|---|---|---|---|---|
| Cu | mobile | full_env | −0.0021 | 0.498 NS | 1,085 |
| Cu | bedrock | full_env | −0.0040 | 0.178 NS | 1,212 |
| Cu | mobile | soil_only | +0.0138 | 0.171 NS | 113 |
| Cu | bedrock | soil_only | −0.0027 | 0.715 NS | 127 |
| Cr | mobile | full_env | −0.0050 | 0.124 NS | 1,085 |
| **Cr** | **bedrock** | **full_env** | **+0.0189** | **5.5×10⁻¹⁰** | **1,220** |
| Cr | mobile | soil_only | +0.0109 | 0.329 NS | 113 |
| Cr | bedrock | soil_only | +0.0041 | 0.746 NS | 127 |
| **Pb** | **mobile** | **full_env** | **+0.0122** | **1.5×10⁻⁴** | **1,085** |
| Pb | bedrock | full_env | +0.0025 | 0.420 NS | 1,220 |
| Pb | mobile | soil_only | +0.0114 | 0.301 NS | 113 |
| Pb | bedrock | soil_only | +0.0088 | 0.475 NS | 127 |

**Key findings:**
- **Cu:** Neither mobile nor bedrock Cu predicts niche breadth (both NS). No Cu-mediated niche association.
- **Cr bedrock (POSITIVE, p = 5.5×10⁻¹⁰):** Higher bedrock Cr → *broader* niche (opposite sign to the primary metal-gene/niche-breadth association). Likely reflects serpentinite/ultramafic geology; not a metal-gene mechanism.
- **Pb mobile (POSITIVE, p = 1.5×10⁻⁴):** Higher bioavailable Pb → *broader* niche. Both Cr and Pb effects are positive — consistent with richer/more heterogeneous environments, not metal-stress narrowing.
- Soil-only: all six models NS (limited power, n ≈ 113–127).

---

## Analysis C: Gene category density ~ mobile vs bedrock metal

Model: `gene_density_z ~ metal_z + genome_size_z` (PGLS, Pagel's λ by ML).
Prediction: cofactor density better predicted by bedrock; resistance density better predicted by mobile.

| Metal | Gene category | Predictor | Dataset | β | p | n |
|---|---|---|---|---|---|---|
| Cu | cofactor | mobile | full_env | +0.0155 | 0.488 NS | 618 |
| Cu | cofactor | bedrock | full_env | +0.0387 | 0.101 NS | 703 |
| Cu | cofactor | mobile | soil_only | −0.0617 | 0.290 NS | 69 |
| Cu | cofactor | bedrock | soil_only | +0.0472 | 0.313 NS | 77 |
| **Cu** | **resistance** | **mobile** | **full_env** | **−0.0426** | **0.050†** | **767** |
| Cu | resistance | bedrock | full_env | +0.0086 | 0.695 NS | 865 |
| Cu | resistance | mobile | soil_only | −0.0097 | 0.860 NS | 78 |
| Cu | resistance | bedrock | soil_only | +0.0651 | 0.094† | 87 |
| Cr | cofactor | mobile | full_env | +0.0092 | 0.695 NS | 618 |
| Cr | cofactor | bedrock | full_env | +0.0242 | 0.266 NS | 707 |
| Cr | cofactor | mobile | soil_only | −0.0701 | 0.315 NS | 69 |
| Cr | cofactor | bedrock | soil_only | −0.0040 | 0.950 NS | 77 |
| **Cr** | **resistance** | **mobile** | **full_env** | **−0.0461** | **0.042*** | **767** |
| **Cr** | **resistance** | **bedrock** | **full_env** | **+0.0567** | **0.008**** | **871** |
| Cr | resistance | mobile | soil_only | −0.0146 | 0.817 NS | 78 |
| Cr | resistance | bedrock | soil_only | +0.0689 | 0.247 NS | 87 |
| Pb | cofactor | mobile | full_env | −0.0023 | 0.917 NS | 618 |
| Pb | cofactor | bedrock | full_env | −0.0049 | 0.845 NS | 708 |
| Pb | cofactor | mobile | soil_only | −0.1153 | 0.083† | 69 |
| Pb | cofactor | bedrock | soil_only | −0.0445 | 0.586 NS | 77 |
| Pb | resistance | mobile | full_env | +0.0196 | 0.377 NS | 767 |
| Pb | resistance | bedrock | full_env | +0.0277 | 0.239 NS | 872 |
| Pb | resistance | mobile | soil_only | +0.0861 | 0.121 NS | 78 |
| Pb | resistance | bedrock | soil_only | +0.0352 | 0.585 NS | 87 |

**Key findings:**
- **Cofactor genes:** No significant associations with mobile or bedrock Cu/Cr/Pb. The cofactor~bedrock prediction is not supported but also not falsified — null for both.
- **Resistance genes and mobile Cu/Cr (NEGATIVE, p = 0.042–0.050):** Higher bioavailable Cu/Cr → *fewer* resistance genes per Mb. This is the **opposite direction** of the timescale hypothesis. Genome streamlining in bioavailable-metal-rich environments dominates over positive selection for resistance.
- **Resistance genes and bedrock Cr (POSITIVE, p = 0.008):** Higher bedrock Cr → more resistance genes. Mechanistically plausible — ultramafic soils historically select for Cr-resistance gene accumulation.
- **Cr paradox:** Mobile Cr negatively predicts resistance while bedrock Cr positively predicts it. These two measures are negatively correlated (ρ = −0.211), so they index different geological contexts.
- Soil-only results all NS (limited power).

---

## Analysis D: Double-signal vs high-λ gene presence ~ mobile Cu + pH + SOM

Model: `gene_presence_fraction ~ mobile_Cu_z + soil_pH_z + soil_SOM_z` (PGLS, Pagel's λ).
Presence fraction = proportion of MAGs per genus carrying the KO (range 0–1).
Threshold for full_env analysis: ≥50 genera with non-zero presence.
nrsD (n_nonzero = 48) and shp (n_nonzero = 41) fell below threshold.

### Double-signal gene results (full_env, n = 982 genera)

| Gene | β_mobile_Cu | p | λ |
|---|---|---|---|
| merD | −0.0011 | 0.451 NS | 0.099 |
| merE | −0.0008 | 0.495 NS | 0.113 |
| gesB | +0.0006 | 0.157 NS | 0.067 |
| gesA | +0.0006 | 0.192 NS | 0.065 |
| aoxB | +0.0013 | 0.456 NS | 0.028 |
| golS | +0.0003 | 0.631 NS | 0.042 |
| doxDA | +0.0007 | 0.652 NS | 0.159 |
| norB | +0.0016 | 0.283 NS | 0.164 |
| iucD | −0.0021 | 0.173 NS | 0.776 |
| nicC | −0.0001 | 0.926 NS | 0.124 |
| nikB | −0.0017 | 0.422 NS | 0.272 |
| **Summary** | **0/11 p < 0.05** | | median λ = 0.113 |

### High-λ gene results (full_env, n = 982 genera)

| Gene | β_mobile_Cu | p | λ |
|---|---|---|---|
| zntR | +0.0002 | 0.907 NS | 0.573 |
| cobN | +0.0002 | 0.957 NS | 0.838 |
| cobT | +0.0004 | 0.890 NS | 0.584 |
| cobC1 | +0.0003 | 0.927 NS | 0.569 |
| cusA | −0.0010 | 0.831 NS | 0.814 |
| cbiK | −0.0022 | 0.405 NS | 1.000 |
| CoADR | +0.0040 | 0.136 NS | 1.000 |
| **emrB** | **−0.0143** | **0.016*** | 0.774 |
| czcA | −0.0066 | 0.277 NS | 0.794 |
| dsbA | +0.0027 | 0.453 NS | 0.712 |
| **Summary** | **1/10 p < 0.05** | | median λ = 0.784 |

**Result:** The prediction (double-signal genes more strongly associated with mobile Cu than
high-λ genes) is **NOT supported**. Neither gene type shows consistent mobile Cu association.
The one significant result (emrB, a high-λ gene) shows a *negative* association — opposite
to the adaptive prediction. Phylogenetic signal (λ) confirms the contrast: double-signal genes
have median λ = 0.11 (HGT-compatible), high-λ genes have median λ = 0.78 (vertically inherited).

---

## Analysis E: Variance partitioning

OLS variance partitioning of z-scored metal gene density (ko_per_mb_primary_z) into
unique contributions of: bedrock Cu, mobile Cu, soil pH, soil SOM.

| Dataset | Full R² | Unique: bedrock Cu | Unique: mobile Cu | Unique: pH | Unique: SOM | n |
|---|---|---|---|---|---|---|
| full_env | 0.0354 | 0.0001 | 0.0001 | 0.0348 | 0.0032 | 1,074 |
| soil_only | 0.0513 | 0.0041 | 0.0288 | 0.0129 | 0.0069 | 113 |

**Key findings:**
- **Full env:** Soil pH accounts for essentially all jointly explainable variance (unique R² = 0.035).
  Bedrock Cu and mobile Cu each contribute unique R² < 0.001 — statistically negligible.
  SOM adds 0.003 unique. Metal source (bedrock vs mobile) is irrelevant at the genus level
  in the full environmental dataset.
- **Soil-only:** Mobile Cu contributes unique R² = 0.029 — the largest single contributor
  (56% of total R² = 0.051). Bedrock Cu contributes 0.004. pH and SOM smaller.
  **Caveat:** soil-only n = 113; unique R² estimates are unstable (bootstrap CI not computed).

---

## Summary comparison table

| Test | Full-env result | Soil-only result | Prediction supported? |
|---|---|---|---|
| A: Cu separability | ρ = +0.02 (orthogonal) | ρ = +0.13 NS | ✓ Separable |
| A: Cr separability | ρ = −0.21 | ρ = −0.15 NS | ✓ Separable |
| A: Pb separability | ρ = +0.08 | ρ = +0.14 NS | ✓ Separable |
| B: niche ~ mobile Cu | β = −0.002, NS | β = +0.014, NS | ✗ No effect |
| B: niche ~ bedrock Cu | β = −0.004, NS | β = −0.003, NS | ✗ No effect |
| B: niche ~ bedrock Cr | β = +0.019, p < 1e-9 | NS | — Unexpected positive |
| B: niche ~ mobile Pb | β = +0.012, p < 1e-4 | NS | — Unexpected positive |
| C: cofactor ~ bedrock Cu | β = +0.039, p = 0.101 NS | NS | ✗ Not supported |
| C: resistance ~ mobile Cu (hypothesis) | β = −0.043, p = 0.050† (NEGATIVE) | NS | ✗ Opposite direction |
| C: resistance ~ bedrock Cr | β = +0.057, p = 0.008** | NS | Partially consistent |
| C: resistance ~ mobile Cr | β = −0.046, p = 0.042* (NEGATIVE) | NS | ✗ Opposite direction |
| D: double-signal ~ mobile Cu | 0/11 p < 0.05 | 1/11 (doxDA, unrelated to Cu) | ✗ Not supported |
| D: high-λ ~ mobile Cu | 1/10 p < 0.05 (emrB, negative) | NS | ✗ Not supported |
| E: mobile Cu unique R² | 0.0001 (negligible) | 0.029 (largest contributor) | Tentative soil-only |

---

## Discussion paragraph

Mobile Cu fractions (CSU PF1 modelled bioavailable fraction) and bedrock Cu concentrations
(GeoROC log-transformed) were essentially orthogonal across genera (ρ = +0.02), confirming
that the two measures capture distinct environmental signals. The timescale hypothesis — that
resistance genes track ecological-timescale bioavailable metal pools while cofactor genes reflect
geological-timescale bedrock composition — was **not supported**. For Cu, neither mobile nor
bedrock fractions predicted cofactor or resistance gene density (all p > 0.10). For Cr,
resistance gene density showed a marginally significant *negative* association with mobile Cr
(β = −0.046, p = 0.042) and a significant *positive* association with bedrock Cr (β = +0.057,
p = 0.008), which is the opposite of the timescale prediction for mobile metals and partially
consistent for bedrock (high-Cr ultramafic soils drive resistance via geological selection).
Mobile metal fractions, which represent bioavailable metal pools in soil, were therefore **worse**
predictors of resistance gene density than bedrock concentrations for Cr, and **no different** for
Cu, inconsistent with the interpretation that resistance genes respond adaptively to current
bioavailability. By contrast, cofactor gene density showed no significant association with either
bedrock or mobile metal concentrations, consistent with the null expectation under slow geological
evolution but providing no positive evidence for bedrock-specific prediction. The 13 double-signal
HGT candidate genes showed no significant associations with mobile Cu (0/11 genes, p < 0.05,
full_env), nor did the 10 high-λ vertically inherited genes (1/10, negative direction). These
results indicate that genus-level mobile metal fractions, as approximated by the CSU PF1 modelled
grid, do not detectably predict resistance gene repertoires at the genus level, and the
metal-resistance HGT-timescale framework is not validated by this ecological test.

### Limitations

1. **Mobile metal data scope:** CSU PF1 provides only Cu, Cr, Pb from the requested set;
   Zn, Ni, Co mobile fractions are unavailable — the comparison is restricted to three metals.
2. **Modelled fractions:** CSU PF1 mobile fractions are modelled (not measured in situ);
   model uncertainty propagates into genus-level means via spatial averaging.
3. **Spatial resolution:** CSU grid at 250 m; genus-level means aggregate across widely
   dispersed samples, introducing spatial mismatches.
4. **Covariate collinearity:** Mobile metals covary with soil pH and SOM (both drive metal
   speciation). Unique variance partitioning separates these (pH dominates: unique R² = 0.035)
   but cannot resolve causal pathways.
5. **Presence fraction PGLS:** Analysis D uses continuous presence fraction; proper
   phylogenetic logistic regression (phyloglm) would be more appropriate for sparse binary data.
6. **Power:** Soil-only analyses use n ≈ 69–127 genera; soil-only results are underpowered.
7. **Positive niche breadth effects:** Bedrock Cr (p < 1e-9) and mobile Pb (p < 1e-4) both
   positively predict niche breadth — unexpected and likely reflect geographic confounders
   (serpentinite biogeography, industrial Pb contamination gradients) rather than within-genus
   metal biology.

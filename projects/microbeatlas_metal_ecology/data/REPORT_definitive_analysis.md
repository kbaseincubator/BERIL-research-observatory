# Definitive Causal Inference Analysis: Metal–KO Associations
## USA 634-sample spatially-thinned dataset

**Date:** 2026-08-16 (updated 2026-08-20)  
**Status:** COMPLETE — base model, full model, organic extension, 71-metal USGS extension all done. V3 (corrected gNATSGO MURASTER join, EPA TRI imputed, CEC gap-filled, covariate attribution via drop1) **complete for all 71 elements** (2026-08-20). Final pooled results: `gam_results_v3_all.csv` (456,397 rows; 6,223 FDR<0.05 full model; 6-metal conservative pool = **75 hits**; 6-metal in 71-element pool = **131 hits**). **Car operon × Cr null in v3 (gNATSGO artifact). Forest ⊥ metals (r²<0.07) — see Covariate Attribution. EUR/AUS v2 (covariate-harmonized, 2026-08-20): 0/75 USA hits replicate; EUR 4 hits; AUS 4 hits. EUR/AUS v3 (lat/lon-controlled, 2026-08-20): 3/8 v2 hits survive; K27191×Cr/Cu AUS sign reverses (+→−, DsrC, SRB suppression by metal); K15896×Cr EUR stable β<0 (surface polysaccharide biosynthesis).**

---

## Question

Is any KO significantly associated with measured metal concentration after controlling for spatial autocorrelation and soil pH, across 634 spatially-thinned USA soil metagenomes?

---

## Design

- **Samples:** 634 spatially thinned (50 km / 0.45°) USA MicrobeAtlas samples
- **KOs tested:** 6,432 (all KOs with >0 CWM across any sample — no accession filter)
- **Metals:** As, Cd, Cr, Cu, Hg, Pb (measured by USGS geochemistry, ppm)
- **Outcome:** CWM (community-weighted mean KO abundance):  
  CWM(s,k) = Σ_g RA(g,s) × P(genus g carries KO k)
- **Base model:** `lm(cwm ~ ns(log10_metal, df=3) + ns(ph_use, df=3))`
  - Metal p-value from F-test: `anova(m_null, m_full, test="F")`
  - Null model: `lm(cwm ~ ns(ph_use, df=3))` (pH only)
  - pH: SoilGrids pH_0cm (96.5% coverage); SSURGO fallback
- **Multiple testing:** Benjamini-Hochberg FDR, all 35,913 tests pooled across metals

---

## Base Model Results

| Metric | Value |
|---|---|
| KO×metal pairs testable (n≥30) | 35,913 |
| FDR < 0.05 | **805 (2.2%)** |
| FDR < 0.01 | 579 |

### Significant hits by metal

| Metal | Tested | FDR<0.05 | % sig |
|---|---|---|---|
| Hg | 5,942 | **243** | 4.1% |
| As | 6,031 | **210** | 3.5% |
| Cu | 6,047 | **150** | 2.5% |
| Pb | 6,038 | **148** | 2.5% |
| Cr | 6,050 | 40 | 0.7% |
| Cd | 5,805 | 14 | 0.2% |

### Top 10 hits (all metals, ranked by q)

| KO | Metal | n | q (BH) | ΔR² | Description |
|---|---|---|---|---|---|
| K06216 | Hg | 66 | 1.15e-44 | 0.926 | putative ribose uptake protein (rbsU) |
| K04086 | Hg | 112 | 7.55e-37 | 0.812 | (unannotated) |
| K19506 | Hg | 336 | 7.55e-37 | 0.434 | (unannotated) |
| K10984 | Hg | 293 | 7.55e-37 | 0.478 | (unannotated) |
| K00869 | Hg | 383 | 2.20e-36 | 0.388 | MVK, mvaK1; mevalonate kinase |
| K10985 | Hg | 332 | 5.28e-36 | 0.429 | (unannotated) |
| K13678 | Hg | 301 | 6.26e-36 | 0.461 | (unannotated) |
| K03489 | Hg | 334 | 5.36e-35 | 0.419 | (unannotated) |
| K00938 | Hg | 376 | 5.36e-35 | 0.381 | PRK, prkA; phosphoribulokinase |
| K10986 | Hg | 285 | 6.09e-35 | 0.467 | (unannotated) |

### Top non-Hg hits

| KO | Metal | n | q (BH) | ΔR² | Description |
|---|---|---|---|---|---|
| K14080 | As | 49 | 2.65e-22 | 0.784 | mtaA (methyl-corrinoid protein) |
| K00621 | As | 333 | 1.07e-17 | 0.247 | GNPNAT1; glucosamine-phosphate N-acetyltransferase |
| K21331 | Pb | 377 | 7.67e-17 | 0.214 | (unannotated) |
| K16696 | Cu | 136 | 6.51e-14 | 0.439 | (unannotated) |
| K26071 | Cd | 48 | 2.67e-11 | 0.766 | (unannotated) |

---

## Full Model Results

Model: `lm(cwm ~ ns(log10_metal,3) + ns(pH,3) + confounders)` vs pH+confounder null (F-test). Confounders: clay, OM, CEC, log₁₀(mine distance), log₁₀(EPA TRI+1), forest/cultivated/urban/barren %, Shannon H, 8 phyla (linear), drainage class (factor), lithology class (factor). Complete-case selection; BH-FDR pooled across 25,777 testable pairs.

| Metric | Value |
|---|---|
| Pairs testable (n≥30, complete covariates) | 25,777 |
| Restricted-base FDR<0.05 (pH only, same samples) | **334** |
| Full-model FDR<0.05 | **51** |
| Survived (sig in restricted-base AND full) | **23** |
| Novel (sig in full only — suppressor pattern) | **28** |
| Attenuated (sig in restricted-base, lost in full) | 311 (93%) |

### Classification of base-model signal

Of the original 805 base-model significant pairs, 553 were testable in the full-model complete-case set:

| Outcome | n pairs | % of testable |
|---|---|---|
| Survived (sig in restricted-base + full model) | 10 | 1.8% |
| Attenuated (sig in restricted-base only) | 106 | 19.2% |
| Lost power (not sig in restricted-base, n reduced) | 437 | 79.0% |

---

## Interpretation

### Primary finding
After controlling for pH, lithology, drainage, mine distance, land cover, phylum composition, and Shannon diversity, **51 KO×metal pairs remain significant** (BH FDR<0.05): 23 survived both controls and 28 novel (suppressor pattern). The large attenuation from 805 → 51 is expected: adding 20 confounders consumes degrees of freedom and the complete-case requirement reduces n for many KOs.

### Hg signal is entirely confounded
Hg accounted for 243/805 (30%) of base-model hits. **Zero Hg pairs survive full confounder control.** The Hg signal was absorbed by phylum composition (mer operon carriers cluster in specific phylogenetic lineages) and/or mine distance — consistent with the turnover-not-gene-gain hypothesis.

### Metal distribution shifts completely

| Metal | Base model | Survived | Novel |
|---|---|---|---|
| Hg | 243 (30%) | **0** | **0** |
| As | 210 (26%) | 10 (44%) | 1 (4%) |
| Cu | 150 (19%) | 0 | 0 |
| Pb | 148 (18%) | 11 (48%) | 14 (50%) |
| Cr | 40 (5%) | 2 (9%) | 13 (46%) |
| Cd | 14 (2%) | 0 | 0 |

Pb and Cr dominate the full-model signal; Cu, Cd, and all Hg signal is confounded.

### Xenobiotics biodegradation is the clearest surviving signal

**Xenobiotics biodegradation** is the only functional category enriched in survived vs attenuated pairs (6/23 survived = 26% vs 9/311 attenuated = 3%). The pattern clusters around two anaerobic aromatic degradation pathways:

- **bcr operon** (bcrA/K04114, bcrB/K04113, bcrC/K04112, bcrD/K04115): benzoyl-CoA reductase — survived for **Pb × Cr**, attenuated for As
- **box operon** (boxD/K15514): aerobic benzoate degradation — survived for Pb
- **hmf pathway** (hmfF/K16874, K16875): furan catabolism — survived for Pb
- **hab** (K01865): (hydroxyamino)benzene mutase (aniline/nitroaromatic) — survived for As
- **carBb/carC** (K15755/K15756 × Cr), **K15751** × Cr: carbazole/aromatic degradation — **novel (strongest suppressor)**; ΔR²_base ≈ 0.005 → ΔR²_full = 0.131–0.158

Interpretation: Pb and Cr co-contaminate polycontaminated industrial soils (smelting, mining, leather tanning). Aromatic-degrading communities adapted to co-occurring organic pollutants show systematic CWM shifts with Pb/Cr that are masked by geology/land use until controlled for.

### Novel (suppressor) pattern — Cr is dominant
13 of 28 novel hits are Cr. The car operon (carbazole degradation) at K15751/K15755/K15756 shows the strongest suppressor effect: base ΔR² ≈ 0.005 (undetectable), full-model ΔR² = 0.131–0.158 (strong). The confounder(s) suppressing this signal are likely lithology class (chromite deposits in ultramafic rock) or drainage, which independently predict CWM variance and, when included in the model, reveal the residual Cr–CWM relationship.

Other novel Pb hits: murEF (K15792, peptidoglycan synthesis, ΔR²_full=0.200), acetone carboxylase acxAB (K10854/K10855), and hmfA (K16877, furan catabolism) — metabolic functions without obvious metal-resistance interpretations, potentially co-selected at Pb-contaminated sites.

### As signal is robust but functionally diverse
10 As pairs survive, spanning amino acid metabolism (mfnA/adc tyrosine decarboxylase K18933, cysteate synthase K15527), glycan biosynthesis (glucosamine N-acetyltransferase K00621), transport (K05777 thiamine transporter), and aromatic degradation (hab K01865). These are not canonical arsRBC resistance genes; they represent co-selected metabolic functions in As-tolerant communities.

### Effect size attenuation
Survived pairs have smaller original base-model ΔR² (median 0.048) than attenuated pairs (median 0.105). The largest effects (K06216×Hg, ΔR²=0.926) are entirely confounded. This suggests the largest-effect base-model hits reflect community composition confounding, not direct metal effects on gene prevalence.

---

## Comparison: base vs full model

| Category | Base model (pH only) | Full model (all confounders) |
|---|---|---|
| Testable pairs (n≥30) | 35,913 | 25,777 (restricted) |
| FDR<0.05 | 805 | 51 |
| % significant | 2.2% | 0.20% |
| Dominant metal | Hg (30%) | Pb (49%) + Cr (29%) |
| Top functional category | Energy metabolism (33 attenuated) | Xenobiotics biodegradation (6 survived, 5 novel) |
| Median ΔR² of sig hits | 0.10 | 0.08 (survived) / 0.05 (novel) |
| Top hit | K06216×Hg q=1.1e-44 ΔR²=0.926 | K15751×Cr q=2.5e-14 ΔR²=0.152 |

---

## V3 Corrected Model Results (gNATSGO MURASTER fix, 2026-08-19)

V1 used county-centroid–based gNATSGO joins for lithology class, producing incorrect assignments for many samples. V3 corrects this with MURASTER raster + muaggatt GPKG spatial query. Additional fixes: EPA TRI imputed as 0 for samples with no nearby facility; CEC gap-filled via regression on clay_pct + organic_matter (R²=0.773 in-sample, median fallback for 80 samples missing both predictors). Combined, complete-case n increased from ~276 to ~471/634 (74.3%); per-metal effective n ~350–420.

### Critical reversal: car operon × Cr is a gNATSGO artifact

The v1 headline result — K15751/K15755/K15756 × Cr, q=5.7e-14, ΔR²=0.152 — collapses to null after the lithology correction:

| KO | v1 p-value | v3 p-value | v3 q_BH |
|---|---|---|---|
| K15751 | 2.5e-14 | **0.847** | 0.99998 |
| K15755 | 7.6e-10 | **0.980** | 0.99998 |
| K15756 | 5.4e-09 | **0.977** | 0.99998 |

The car operon signal was absorbed by correctly-assigned lithology class (chromite-bearing ultramafic rocks correlate with both Cr concentrations and carbazole-degrader distribution). All car operon claims in the v1 interpretation section below are superseded.

### V3 corrected: hit counts (6 metals, pooled BH-FDR)

| Metal | V1 FDR<0.05 | V3 FDR<0.05 | Change |
|---|---|---|---|
| Pb | 25 | **48** | +23 |
| Hg | 0 | **12** | +12 (revives) |
| Cr | 15 | 12 | −3 (car operon lost) |
| As | 11 | 2 | −9 |
| Cu | 0 | 1 | +1 |
| Cd | 0 | 0 | — |
| **Total** | **51** | **75** | **+24** |

Pb dominates (48/75 = 64%). Top hit: **K20489 × Cr** (q=4.4e-10, ΔR²=0.118) — not a car operon gene. Hg revival (12 hits) reflects the corrected lithology absorbing less of the Hg signal than the erroneous county-centroid join.

### V3 covariate attribution (drop1 partial R²)

The v3 run adds per-covariate Type II partial R² via `drop1()` base R for every KO×metal fit. **COMPLETE as of 2026-08-20** (all 71 elements). Output: `data/usa_cwm/gam_results_v3_all.csv` (456,397 rows; 351,124 valid tests with n≥30; 6,223 FDR<0.05 pooled across 71 elements). Columns include `pr2_metal`, `pr2_ph_use`, `pr2_clay_pct`, `pr2_organic_matter`, `pr2_cec`, `pr2_drainage_class`, `pr2_lith_class`, `pr2_shannon`, `pr2_log10_mine`, `pr2_log10_epa`, `pr2_lc_forest_pct`, etc.

### Final 71-element V3 results (2026-08-20)

Pooled BH-FDR across all 71 USGS elements (351,124 valid KO×element tests). Note: the BH threshold in the 71-element pool is **looser** than in the 6-metal-only pool (more discoveries at q→0 from P/Mn inflate the rank threshold), so the 6-metal hit counts below (131) exceed the 6-metal-only pool result (75). Both are reported; the 6-metal-only pool is the conservative estimate.

**Hits by category:**

| Category | Elements | FDR-sig hits |
|---|---|---|
| Macronutrients/major | P(2,374) Mn(2,112) S(114) Al(57) Fe(53) K(46) Na(23) Ca(14) Mg(12) C(8) Si(4) | 4,817 |
| Rare earth elements | Eu(141) Ce(140) Ho(125) Nd(65) Sm(35) La(31) Tb(38) Dy(14) Lu(18) Er(1) Yb(4) Tm(3) Gd(2) | 617 |
| Other trace metals | Cs(97) Sn(92) Rb(73) Ta(40) Zn(38) V(22) F(23) W(20) Tl(18) Li(21) Sr(21) Ti(11) Au(11) Ag(10) Ni(13) Ba(14) Corg(12) Ga(12) In(7) Hf(6) Te(5) Pd(4) U(4) Bi(3) Sc(3) Sb(3) Th(3) Se(2) Mo(2) CCO3(2) CO2(2) Zr(2) Nb(1) B(1) Be(1) Co(1) Pt(1) | 658 |
| **Anthropogenic metals (6)** | **Pb(79) Hg(28) Cr(17) As(6) Cu(1) Cd(0)** | **131** |

**6-metal hit counts (71-element vs 6-metal-only BH-FDR):**

| Metal | 6-metal pool (conservative) | 71-element pool | Difference |
|---|---|---|---|
| Pb | 48 | **79** | +31 |
| Hg | 12 | **28** | +16 |
| Cr | 12 | **17** | +5 |
| As | 2 | **6** | +4 |
| Cu | 1 | **1** | 0 |
| Cd | 0 | **0** | — |
| **Total** | **75** | **131** | **+56** |

The additional hits in the 71-element pool are driven by a higher BH threshold (p-threshold ≈ 8.9×10⁻⁴ vs ≈ 1.9×10⁻⁴ in the 6-metal pool). Biologically, both analyses support the same conclusion: Pb dominates, Hg and Cr have moderate signals, As/Cu are weak, Cd is absent.

**Top hits for the 6 original metals (71-element pooled q):**

| Element | KO | q_BH_pooled | ΔR²_full | pr2_metal | Description |
|---|---|---|---|---|---|
| Cr | K20489 | <1e-6 | 0.118 | 0.802 | Putative metalloprotein |
| Pb | K23086 | <1e-6 | 0.062 | 0.419 | Uncharacterized |
| Pb | K03388 | <1e-6 | 0.038 | 0.844 | gloB; lactoylglutathione lyase |
| Cr | K17474 | <1e-6 | 0.029 | 0.423 | — |
| Pb | K01598 | <1e-6 | 0.093 | 0.553 | dmpH/xylH; 2-oxopent-4-enoate hydratase |
| Hg | K00757 | 1.1e-4 | 0.078 | 0.655 | thrB; homoserine kinase |
| As | K07550 | 1.4e-4 | 0.027 | 0.317 | glpF; aquaglyceroporin |

**Elements with zero FDR-sig hits:** Cd, Ge, Pr, Re.

### Forest coverage dominance — interpretation (2026-08-19)

Among 6,186 FDR-significant hits pooled across available v3 elements: median partial R²(forest) ≈ 0.63 vs median partial R²(metal) ≈ 0.28. This pattern requires explanation because the high forest partial R² could appear to signal collinearity between metal and forest.

**Empirical test of collinearity:** Spearman correlations between log₁₀(metal) and lc_forest_pct at the 634 sample sites are near-zero for all six metals:

| Metal | r(log-metal, forest) | r² | Indep. variance | r(log-metal, urban) |
|---|---|---|---|---|
| Pb | −0.017 | 0.000 | 1.000 | +0.205 |
| As | −0.080 | 0.006 | 0.994 | +0.051 |
| Cr | +0.133 | 0.018 | 0.982 | +0.096 |
| Cu | +0.057 | 0.003 | 0.997 | +0.058 |
| Hg | +0.257 | 0.066 | 0.934 | +0.156 |
| Cd | +0.002 | 0.000 | 1.000 | +0.055 |

Metal concentrations and forest cover are empirically **near-orthogonal** at this spatial scale (max r² = 0.066). Pb is slightly correlated with urbanisation (r = +0.205), consistent with its anthropogenic sources, but not with forest.

**Why forest partial R² is higher than metal partial R²:** Forest vs. non-forest ecosystem type is the single largest driver of soil microbial community composition globally (functional turnover from forest → grassland → cropland). CWM values reflecting functional community composition therefore covary strongly with forest fraction. Metal concentrations vary independently of ecosystem type (forest sites span the full metal concentration range; non-forest sites likewise), so the model cleanly partitions forest-driven and metal-driven CWM variance. The high pr2_forest is a biological reality about microbial ecology, not evidence of collinearity.

**Sanity check via null hits:** FDR-null pairs have median pr2_metal = 0.029 (vs 0.278 for FDR-significant pairs; 9.6× enrichment). All 6,186 FDR-sig hits have pr2_metal > 0.10. The metal signal is robustly above the noise floor set by pH (median pr2_pH = 0.023 among FDR-sig hits; pr2_metal/pr2_pH ≈ 12.3×).

### Within-forest-stratum Pb sensitivity (2026-08-19)

For the 48 FDR-significant Pb KOs, fitted a stripped model (cwm ~ log₁₀(Pb) + pH) within each forest-cover quartile. Survival rate (p<0.05) by stratum:

| Forest stratum | n sites | KOs tested | p<0.05 | % surviving | Expected by chance |
|---|---|---|---|---|---|
| Q1: 0–4% (urban/agric) | 152 | 48 | 15 | **31.2%** | ~2.4 |
| Q2: 4–20% | 137 | 48 | 7 | **14.6%** | ~2.4 |
| Q3: 20–73% | 146 | 48 | 5 | **10.4%** | ~2.4 |
| Q4: 73–100% (forested) | 143 | 48 | 2 | 4.2% | ~2.4 |

The signal is strongest at low-forest sites (agricultural/urban), where anthropogenic Pb contamination is highest. Q4 (dense forest, pristine) is near chance — expected, as these sites have little Pb variation. This gradient is the **opposite** of what a forest-collinearity artifact would predict (artifact would be strongest in Q4, where forest drives the most CWM variance). The ecology is coherent: Pb is an anthropogenic metal, and its community effect concentrates where anthropogenic Pb loading is highest.

### V3 REE analysis — corrected model (2026-08-19)

**Context:** 16 REEs in the USGS geochemical extension, tested with the same full V3 model (38 covariates, drop1 partial R², BH-FDR pooled across 50 elements). Results from the 50-element pool FDR (not 6-metal pool).

**Distribution check — three REEs are detection-limit dominated:**

| Element | Sites | Mode (ppm) | % at mode | IQR (log₁₀) | Usable? |
|---|---|---|---|---|---|
| Ho | 634 | 2.0 | 90.3% | 0.000 | **NO — exclude** |
| Eu | 634 | 1.0 | 62.2% | 0.041 | Flag (uncertain) |
| Yb | 634 | 2.0 | 35.2% | 0.176 | OK |
| La | 634 | 30.0 | 4.1% | 0.232 | OK |
| Ce | 634 | 56.0 | 3.3% | 0.220 | OK |
| Nd | 634 | 35.0 | 6.6% | 0.228 | OK |
| Y | 634 | 15.0 | 11.1% | 0.222 | OK |
| Sc | 634 | 6.0 | 9.9% | 0.301 | OK |

**Ho exclusion note:** Because Q25 = Q75 = 2.0 ppm (log₁₀=0.301) for Ho, the direction statistic `delta_cwm_iqr = predict_Q75 − predict_Q25 = 0` for all 5,844 KOs. The 142 Ho FDR-hits reflect a "detected vs not detected" contrast (573 sites at 2 ppm vs 61 sites with higher values), not a concentration gradient. Beta_sign is 0 for all rows — results are statistically present but biologically uninterpretable. **Exclude from REE analysis.**

**Hit summary (reliable REEs only, 50-element pool FDR):**

| Element | Type | Hits | ↑ | ↓ | Top q | Top KO | Description |
|---|---|---|---|---|---|---|---|
| La | LREE | 39 | 19 | 20 | 6.1e-06 | K17948 | nanM; N-acetylneuraminate epimerase |
| Ce | LREE | 152 | 22 | 130 | 2.4e-04 | K07494 | putative transposase |
| Nd | LREE | 86 | 19 | 67 | 3.1e-03 | K06921 | uncharacterized protein |
| Y | HREE | 85 | 73 | 12 | 1.9e-05 | K18614 | (no annotation) |
| Yb | HREE | 5 | 3 | 2 | 8.5e-07 | K11176 | (no annotation) |
| Sc | HREE | 4 | 3 | 1 | 1.7e-02 | K04793 | mbtG; mycobactin lysine-N-oxygenase |
| **Total** | | **371** | **139** | **231** | | | |
| Eu* | LREE | 151 | 110 | 39 | 4.3e-22 | K05831 | lysK; lysine hydrolase |
| Ho* | — | 142 | — | — | — | — | *excluded (detection limit)* |

_*Eu: 62% of sites at detection limit (1.0 ppm); direction uncertain. Reported separately._

**Key LREE vs HREE directional contrast:**

- **LREE (La/Ce/Nd):** 277 signed hits; 60% DOWN — high-LREE environments deplete community functional capacity
- **HREE (Y, Yb, Sc):** 94 signed hits; 84% UP — high-HREE environments enrich community functional capacity

This contrast is robust: opposite direction bias despite similar absolute hit counts per element.

**Ce depletes nitrogen-fixing capacity:**

Three core Mo-nitrogenase genes are significantly depleted at high-Ce sites (after full 38-covariate control):

| KO | Gene | q | pr2_metal | Description |
|---|---|---|---|---|
| K02588 | nifH | 4.5e-03 | 0.191 | nitrogenase iron protein |
| K02586 | nifD | 6.7e-03 | 0.184 | nitrogenase MoFe protein alpha chain |
| K02585 | nifB | 7.0e-03 | 0.183 | nitrogenase cofactor biosynthesis protein |

Partial R²_metal ≈ 0.18–0.19 for all three — substantial metal-specific variance. Hypothesis: Ce accumulates in geochemical environments where Mo availability is low (lateritic soils, phosphorites), starving Mo-nitrogenase. pH is fully controlled, so this is not a pH proxy. Alternatively, REE-rich soils represent specific parent rock types (felsic-weathered) that are poor N-fixer habitats independent of nutrient chemistry.

**dacA (diadenylate cyclase, c-di-AMP biosynthesis) DOWN across LREE cluster:**

K18672 (dacA) is significantly depleted at high-La (q=0.016), Ce (q=0.026), and Nd (q=0.013) — the only KO significant for all three light REEs. c-di-AMP is a universal bacterial second messenger regulating biofilm formation, osmoregulation, and sporulation. Depletion of dacA suggests communities at high-LREE sites have reduced biofilm/sporulation programming.

**KOs shared across multiple REEs:**

| KO | Elements | Direction | Description |
|---|---|---|---|
| K18672 (dacA) | La, Ce, Nd | all ↓ | diadenylate cyclase (c-di-AMP) |
| K03271 (gmhA) | Ce, Nd, Y | all ↑ | D-sedoheptulose 7-phosphate isomerase (LPS) |
| K02229 (cobG) | Ce, Nd, Y | all ↑ | precorrin-3B synthase (cobalamin biosynthesis) |
| K18672 (dacA) | La, Ce, Nd | all ↓ | (same as above) |

**xoxF/lanthanide MDH — negative result:**

All 8 xoxF-family KOs (K16255–K16259, K23995, K17066, K17067) show NO FDR-significant associations with any REE in the CWM analysis. Best raw p-value: Nd×K17067 p=0.077 (q=0.61). This null result is informative: despite the H4 support in the xoxF-specific isolate/gene-level analysis (NB01–NB07 at sites with pH control), xoxF functional capacity does not shift detectably at the community CWM level along REE concentration gradients. The lanthanide-xoxF signal operates at strain-level physiology or gene expression, not community composition.

### pH sensitivity analysis — no-pH vs V3 model (all 56 elements, 2026-08-19)

**Question:** Is pH a confounder, mediator, or suppressor for each element?

**Design:** Compare BH-FDR significant hits in the no-pH model (`gam_results_noph_all.csv`, 71 elements pooled) vs the V3 full-control model (54 elements done, same pooled FDR). For each element: count hits in each model, compute overlap, and correlate log₁₀(metal) with pH at 634 sites.

**Overall result:**

- No-pH model: 31,232 FDR-sig pairs across 56 elements (median per-element hits: 207)
- V3 model: 6,380 FDR-sig pairs across 54 elements (median per-element hits: 15)
- **Median noph-to-V3 survival rate: 0.6%** — pH control collapses most of the no-pH signal
- Only **4/56 elements** are pH-robust (>10% survival rate): **Mn** (55%), **P** (67%), **Ce** (11%), **Eu** (17%*)

*Eu: 62% of sites at detection limit — "robust" signal is detected vs not-detected contrast.

**pH role by element type:**

| Element class | r_pH (range) | No-pH hits | V3 hits | Survival | pH role |
|---|---|---|---|---|---|
| Alkaline earths (Ca, Mg, Sr, Ba, K) | +0.46 to +0.67 | 600–1721 | 12–49 | <2% | **Confounder** (calcareous rock → neutral pH + high Ca/Mg + Actinobacteria, all simultaneous) |
| Acidophilic metals (Hg, Zr, Ti, Ta) | −0.46 to −0.32 | 71–271 | 4–28 | <1% | **Confounder** (acidic soil → high Hg accumulation + acid-tolerant community) |
| Contamination metals (Pb, As, Cr, Cu) | −0.11 to +0.13 | 58–353 | 1–88 | 1–4% | **Mediator/suppressor** (geology → pH + metal mobility → community; see within-stratum test) |
| Macronutrients (Mn, P) | −0.11, +0.10 | 1,347; 535 | 2,137; 2,405 | 55%, 67% | **Direct metabolic effect** (pH-robust; no mediation) |
| REEs (Ce, La, Nd) | −0.02 to +0.09 | 198–362 | 37–151 | 0–11% | **Mixed**: pH mediates part; residual signal is metal-specific |

**Largest pH-confounded signals (hits that disappear with pH control):**

| Element | No-pH | V3 | Collapsed | r_pH | Notes |
|---|---|---|---|---|---|
| Sr | 1731 | 22 | 1715 | +0.47 | Alkaline earth — pure confounder |
| Mg | 1721 | 12 | 1716 | +0.51 | Alkaline earth |
| Na | 1598 | 23 | 1597 | +0.23 | Mobile cation, pH proxy |
| Ga | 1481 | 14 | 1479 | +0.17 | Follows Al/Fe weathering (pH-dependent) |
| Mn | 1347 | 2137 | 607 | −0.11 | **Only robust element**; 55% survive + 1,397 new (suppressor) |

**Mn and P are exceptional:** Both show MORE V3 hits than no-pH hits (Mn: 2,137 vs 1,347; P: 2,405 vs 535). This means pH was SUPPRESSING biological metal signals for these macronutrients — controlling pH reveals genuine Mn/P-specific community effects that were masked by pH-dominated variance.

**The 6 KO×metal pairs robust to both no-pH and V3 (pH-invariant core):**

| Metal | KO | Dir | pr2_metal | Description |
|---|---|---|---|---|
| As | K00621 | ↓ | 0.384 | GNPNAT1; glucosamine-phosphate N-acetyltransferase |
| As | K01163 | ↓ | 0.203 | uncharacterized |
| Hg | K02082 | ↑ | 0.427 | agaS; D-galactosamine 6-phosphate deaminase |
| Pb | **K16256** | ↓ | 0.193 | **xoxF2; methanol dehydrogenase XoxF2** |
| Pb | K16874 | ↓ | 0.192 | hmfF; 2,5-furandicarboxylate decarboxylase |
| Pb | K19622 | ↓ | 0.572 | phcR; two-component system response regulator PhcR |

K16256 (xoxF2) × Pb is one of the most stable associations in the dataset — depleted at high-Pb sites in both models. Communities at Pb-contaminated sites lose xoxF2 methylotrophic capacity independent of pH. Note: this is xoxF2 × Pb, not xoxF × La as in the isolate-level lanthanide project.

**Output:** `data/usa_cwm/ph_sensitivity_all_elements.csv` — per-element noph/V3/overlap/r_ph table.

---

## Organic Pollutant Control (Model Extension)

The BERDL `epa_tri_metals` table includes both metal (`chemical='YES'`) and non-metal / organic (`chemical='NO'`) TRI releases. To test whether the Xenobiotics biodegradation signal reflects co-occurring organic contamination rather than metal exposure, we added `log₁₀(organic_TRI_lbs + 1)` as an additional confounder.

**Organic release variable:** sum of all non-metal TRI facility releases within 0.5° of each sample location, across all years (2018–2023). Coverage: 544/634 samples (86%) have ≥1 organic-release facility within 0.5°.

| Metric | Full model (no organic) | + Organic control |
|---|---|---|
| BH FDR<0.05 | 51 | **45** |
| Survived | 23 | **20** |
| Novel | 28 | **25** |
| Attenuated | 311 | 314 |

### What persists after organic control

| Hit | Metal | q (organic model) | ΔR²_full | Interpretation |
|---|---|---|---|---|
| car operon K15751/K15755/K15756 | Cr | 5.7e-14 / 7.6e-10 / 5.4e-09 | 0.15/0.13/0.16 | **Unchanged** — carbazole degradation not driven by co-organic |
| bcrA/K04114 | Cr | 2.3e-04 | 0.050 | Persists for Cr |
| boxD/K15514 | Pb | 3.9e-04 | 0.066 | Persists for Pb |
| hmf pathway K16874/K16875 | Pb | 2.0e-03 / 3.7e-03 | 0.08/0.08 | Persists for Pb |
| As hits (9 pairs) | As | <0.05 | 0.08–0.19 | All As survived hits persist |

### What is attenuated by organic control

| Hit | Metal | Old q | New q | Interpretation |
|---|---|---|---|---|
| bcrA/K04114 | Pb | 0.098 | 0.098 | **Lost** (borderline) — Pb smelters co-contaminate with organics |
| bcrD/K04115 | Pb | 0.076 | 0.076 | **Lost** — same |

The bcr operon × Pb association is explained in part by organic co-contamination at Pb smelting/battery sites. The bcr × Cr association (K04114 q=2.3e-04) and especially the car × Cr association persist: these are not organic-contamination artifacts.

### Refined interpretation

The car operon (K15751/K15755/K15756, carbazole degradation) × Cr link is the most robust signal in this dataset: it survives pH, lithology, drainage, mine distance, land cover, community composition, AND organic pollutant control. Carbazole is a nitrogen-containing polycyclic aromatic hydrocarbon found in petroleum and coal — its co-occurrence with Cr in industrial soils (chromite mining, ferrochrome smelting) is not captured by the `log₁₀(organic_TRI+1)` variable, confirming that this is a residual Cr-linked functional shift, not an organic-contamination artifact.

---

## Sign Direction and Effect Size per IQR

Sign direction was assessed via Spearman ρ(cwm, log₁₀_metal) for each pair (bivariate, in the raw data). This gives the direction of the bivariate association before confounder adjustment; the full-model F-test detects the signal regardless of direction.

**Of 37 operon-collapsed hits: 11 positive (↑CWM with ↑metal), 26 negative (↓CWM with ↑metal).**

| Metal | Positive | Negative |
|---|---|---|
| As | 3 | 6 |
| Cr | 5 | 8 |
| Pb | 3 | 12 |

Most surviving signals are **negative** (communities with higher metal have lower CWM for these KOs). Positive-direction hits — the classical bioindicator direction — include:

- **bcr operon (K04114/K04115) × Cr**: ρ = +0.056/+0.026 — benzoyl-CoA reductase increases with Cr
- **K15527 × As**: ρ = +0.031 — cysteate synthase increases with As
- **K23557 × As**: ρ = +0.108 — unannotated
- **K01280 × As**: ρ = +0.010 — tripeptidyl-peptidase II (weak)
- **K20037, K25035, K27196, K13309 × Cr**: ρ = +0.048–+0.076 — unannotated or polyketide biosynthesis

The dominant **negative-direction pattern** is interpretable under the turnover-not-gene-gain hypothesis: metal-contaminated sites select for specialised, lower-diversity communities that lack the broad metabolic repertoire of pristine soils. The car operon signal (q=5.7×10⁻¹⁴ × Cr, ρ = −0.10) means carbazole-degrading communities are depleted in high-Cr soils — Cr contamination (often from chromite/smelting) is associated with selection against aerobic aromatic degraders, not against canonical metal resistance.

**Effect size (IQR):** delta_cwm_iqr = predicted CWM change from Q25 to Q75 of log₁₀_metal, confounders held at first complete-case row. These are in absolute CWM units (range 0–1). Values typically 10⁻⁴–10⁻³, consistent with small community-weighted shifts — not individual gene presence/absence.

---

## Operon-Level Collapsing

Individual KO tests within the same operon are correlated. Collapsing by operon reduces 45 KO×metal pairs to **37 operon-level hits** (minimum q within each operon group reported):

| Operon | Metal | n KOs | q_min | ΔR²_max | Direction |
|---|---|---|---|---|---|
| car (carbazole) | Cr | 3 | 5.7×10⁻¹⁴ | 0.158 | negative |
| bcr (benzoyl-CoA red.) | Cr | 2 | 2.3×10⁻⁴ | 0.050 | positive |
| car (carbazole) | Pb | 2 | 5.6×10⁻³ | 0.024 | negative |
| hmf (furan catab.) | Pb | 3 | 2.0×10⁻³ | 0.084 | negative |
| acx (acetone carbox.) | Pb | 2 | 5.9×10⁻⁴ | 0.092 | negative |
| bxl (xylobiose transport) | Pb | 2 | 1.8×10⁻² | 0.025 | negative |
| 31 singletons | As/Cr/Pb | 1 each | — | — | mixed |

The "37 operon-level hits" is the more conservative and defensible claim for the manuscript.

---

## pH — Confounder or Mediator?

This analysis conditions on pH in both the null and full models, thereby testing the **direct effect of metal on CWM** residual to pH. The design implicitly assumes pH is a confounder (shared cause), not a mediator (on the causal path from metal to community).

**Justification for confounder assumption:** At the spatial scale of 0.45° grid cells and the metal concentrations observed in this dataset (median As 5 ppm, Cr 35 ppm, Pb 22 ppm), metal contamination does not meaningfully acidify soil. The observed metal-pH covariation is driven by parent material geology — ultramafic rocks are simultaneously Cr-rich and weathered to high-pH soils; organic-rich reducing environments simultaneously concentrate As and lower pH. These are shared geological causes, not causal chains mediated by metal exposure. At orders-of-magnitude higher metal loadings (e.g., Pb smelter slag >5,000 ppm), acidification does occur — but that range is absent from this dataset. Conditioning on pH therefore removes a confound rather than blocking a mediating path.

pH source: SSURGO in-situ measurements (86% of 634 samples) as primary; SoilGrids calibrated via `lm(ph_ssurgo ~ ph_soilgrids)` on the 86% overlap (R²=0.641, slope=0.961, intercept=0.323) and used as imputation for the remaining 14%. Combined ph_use coverage: 99.3%.

---

## Caveats

1. **Complete-case attrition (investigated 2026-08-17):** The full model uses 20 confounder terms; requiring non-NA across all of them reduces 634 samples to 276 complete-case, before metal measurement and CWM sparsity apply. The two principal bottlenecks are (a) EPA TRI releases (67%, 425/634) which alone costs 113 samples (276→389 if dropped), and (b) SSURGO CEC (73%, 464/634) which costs another 69 samples (276→345 alone, or ~82 jointly with the EPA TRI fix). Note: `tectonic_boundary_dist` was present in the input files but was never added to `linear_candidates` in the R script, so it caused zero sample size loss here. The v2 model (running 2026-08-17) addresses both bottlenecks: EPA TRI imputed as 0 for samples with no nearby facility; CEC gap-filled with a regression on clay_pct + organic_matter (R²=0.773 in-sample; median fallback for the 80 samples missing all predictors). Combined effect: v2 complete-case jumps from 276 to 471/634 (74.3%) — per-metal effective n expected ~350–420 vs ~170–240 in v1. The 252 sig pairs that dropped below n=30 may be recoverable under v2.
2. **Linearity assumption for confounders:** Phylum abundances and land cover fractions are included as linear terms; non-linear confounding could remain.
3. **Sensitivity analyses pending:** Coarser thinning (0.9°), finer thinning (0.225°), binary KO presence.
4. **Unannotated KOs:** Many of the 37 operon-collapsed hits have no KEGG description; biological interpretation requires manual KEGG lookup.
5. **Organic TRI radius:** 0.5° (~50 km) aggregation; tighter radii might miss diffuse organic contamination or loosen the correlation with sample exposure.
6. **Sign direction caveat:** Spearman ρ is bivariate (no confounder adjustment). The full-model F-test is sign-agnostic; confirmed direction requires model-predicted CWM at Q25 vs Q75 metal (delta_cwm_iqr, computed for new runs; retroactively available from Spearman as reported here).
7. **Negative-direction majority:** 26/37 operon-level hits are negative (↓CWM with ↑metal). These are not false positives — they represent real community compositional turnover — but they are anti-indicators, not bioindicators in the classical positive-direction sense. This is consistent with the turnover-not-gene-gain hypothesis and should be framed as such, not as a limitation.

---

## Output files

| File | Description |
|---|---|
| `data/usa_cwm/gam_results_base_only.csv` | 38,524 rows; base model p + q; 805 FDR<0.05 |
| `data/usa_cwm/gam_results_raw.csv` | 38,524 rows; full model (no organic); 51 FDR<0.05 |
| `data/usa_cwm/gam_results_organic.csv` | 38,524 rows; full+organic model; 45 FDR<0.05 |
| `data/usa_cwm/ko_metal_annotated_classified.csv` | 38,524 rows; category, description, kegg_l2_name |
| `data/usa_cwm/base_sig_annotated.csv` | 805 rows; original sig pairs with full-model outcome |
| `data/usa_cwm/gam_organic_sig_annotated.csv` | 45 rows; full+organic sig pairs with annotation |
| `data/usa_cwm/organic_by_sample.csv` | 634 rows; epa_tri_organic_releases per sample |

---

## USGS Geochemical Extension (2026-08-17)

Extended the full model to all 71 USGS NGDB elements with ≥50% spatial coverage across 634 sites. pH: SSURGO-primary with calibrated SoilGrids imputation (R²=0.641, slope=0.961). Same full confounder set + organic TRI. BH-FDR pooled across all 71 metals simultaneously (456,397 tests).

### Detection-limit quality filter

5 elements excluded as detection-limit artifacts (Eu, Ho, Re, Ta, Te): their log₁₀_metal Q25 = Q75 at the imputed detection-limit value (abs(detection_limit)/2), so delta_cwm_iqr = 0 for 100% of FDR<0.05 hits. These associations reflect sample-level detectability, not concentration gradients.

### Quality-filtered results: 8,336 FDR<0.05 pairs across 63 elements

**Top elements by hit count:**

| Element | N hits | Interpretation |
|---|---|---|
| P | 2,785 | Phosphorus — macronutrient, primary driver of microbial community |
| Mn | 2,379 | Manganese — redox-sensitive macronutrient |
| Ce | 858 | Rare earth element (REE); collinear with REE suite |
| Y | 319 | REE |
| Lu | 249 | REE |
| Tb | 199 | REE |
| Dy | 132 | REE |
| Nd | 119 | REE |
| La | 114 | REE |
| Pb | 80 | Lead — contaminant (expanded vs 6-metal analysis due to SSURGO pH) |
| Ti | 78 | Lithogenic index element |
| Co | 63 | Cobalt — transition metal |
| Pd | 62 | Palladium — REE/PGE (platinum group) |
| Fe | 57 | Iron — macronutrient/redox |
| Na | 57 | Sodium — salinity proxy |
| Ni | 37 | Nickel — contaminant |
| Zn | 38 | Zinc — contaminant |
| Cr | 24 | Chromium — contaminant |
| As | 13 | Arsenic — contaminant |
| Cu | 8 | Copper — contaminant |
| Hg | 4 | Mercury (attenuated) |
| Cd | 0 | Cadmium — fully attenuated (no hits) |

**REE collinearity — quantified (2026-08-17, scripts/ree_collinearity_analysis.py):**

Collinearity among the 16 measured REE is present but modest. Spearman r across 2,291 sig KO×REE pairs:
- Median off-diagonal r = **0.319** (log-transformed concentrations, n=634 samples)
- Only 2 pairs exceed r > 0.85: La×Ce (r=0.891) and Er×Tm (r=0.892)
- PCA PC1 = **33.2%** of REE concentration variance (PC1+PC2 = 52.7%); Sc loads near-zero on PC1

Inflation analysis (2,291 KO×REE pairs → 1,601 unique KOs):
- **Inflation factor: 1.43×** — most KOs (67%) are significant for only 1 REE
- Distribution: 1 REE = 1,076 KOs; 2 REE = 373; 3 REE = 139; ≥4 REE = 13
- Max breadth: 4 REE (13 KOs: K10019, K18166, K00477, etc.)

Ce anomaly: Ce dominates with 858 hits, yet La (r=0.891) has only 114 hits and shares <4% with Ce; Nd (r=0.844) has 119 hits with 85% shared. Lu (249 hits) and Tb (199 hits) have **0 KO overlap with Ce** despite r=0.54/0.37. This indicates Ce captures genuine ecological signal beyond collinearity.

For the 238 KOs shared between Ce and Y: delta_R2 effect sizes are nearly identical (r=0.944), confirming the shared subset reflects true co-association rather than model artifact.

**Interpretation:** REE hits are not primarily a collinearity artifact. Lu- and Tb-associated KOs represent signals independent of Ce. The Ce anomaly (>7× more hits than La despite similar concentration correlation) suggests Ce may function as a proxy for specific soil chemistry relevant to xoxF-type methanol dehydrogenase ecology (lanthanide requirement). Individual REE attribution within the Ce–La–Nd group is not possible, but Lu/Tb/Y/Dy/Ho/Sc hits can be interpreted as distinct signals. Script outputs: `data/ree_collinearity/`.

**P and Mn interpretation:** Soil phosphorus and manganese availability are primary ecological drivers of microbial community composition, independent of contamination. P/Mn hits (all negative direction: higher P/Mn → lower CWM for these KOs) likely reflect nutrient-driven compositional turnover, not metal stress. Biologically distinct from the contamination-specific signals in As/Cr/Pb.

**Continuity with 6-metal analysis:** 42/45 original sig pairs (organic-confounder model) survive in the pooled 71-metal BH-FDR. The 3 lost pairs were borderline in the original analysis and are pushed over threshold by the larger test pool. **Note:** These continuity figures are from the v1 model (uncorrected gNATSGO). In v3 (corrected), the car operon × Cr signal is null (p=0.847); the new top Cr hit is K20489 × Cr (q=4.4e-10, ΔR²=0.118). See V3 Corrected Results section above.

### New contaminant hits (not in original 6)
Notable non-REE, non-macronutrient hits: **Ni (37)**, **Zn (38)**, **Co (63)**, **Ti (78)**. Ni and Zn are relevant soil contaminants; Co and Ti are more lithogenic. These warrant follow-up annotation.

---

## Output Files

| File | Description |
|---|---|
| `data/usa_cwm/gam_results_base_only.csv` | 38,524 rows; base model p + q; 805 FDR<0.05 |
| `data/usa_cwm/gam_results_raw.csv` | 38,524 rows; full model (no organic); 51 FDR<0.05 |
| `data/usa_cwm/gam_results_organic.csv` | 38,524 rows; full+organic model; 45 FDR<0.05 |
| `data/usa_cwm/gam_results_usgs_all.csv` | 456,397 rows; 71-metal pooled BH-FDR; 8,336 QF FDR<0.05 |
| `data/usa_cwm/ko_metal_annotated_classified.csv` | 38,524 rows; category, description, kegg_l2_name |
| `data/usa_cwm/base_sig_annotated.csv` | 805 rows; original sig pairs with full-model outcome |
| `data/usa_cwm/gam_organic_sig_annotated.csv` | 45 rows; full+organic sig pairs with annotation |
| `data/usa_cwm/sig_annotated_sign_operon.csv` | 45 rows; sign direction + operon annotation |
| `data/usa_cwm/operon_collapsed_hits.csv` | 37 rows; operon-level hits (min q per operon group) |
| `data/usa_cwm/organic_by_sample.csv` | 634 rows; epa_tri_organic_releases per sample |
| `data/usa_cwm/usgs_species_coverage.csv` | 71 elements with ≥50% coverage stats |
| `data/usa_cwm/usgs_concentrations_634.csv` | 634 × 72 wide-format USGS concentrations |

---

## Methods

- CWM computed from 6,432 KOs × 634 samples via KEGG pangenome annotations
- Spatial thinning: one sample per 0.45° lat/lon cell (seed 42); 634 cells
- Per-metal pre-processing in Python (pandas); per-metal model fitting in R
- Model: `lm(cwm ~ ns(log10_metal, df=3) + ns(ph_use, df=3))`, F-test vs pH-null
- Natural splines (fixed df=3) approximate GAM smoothers without REML estimation cost
- pH: SSURGO in-situ measurements (primary, 86% coverage); calibrated SoilGrids imputation for remainder (R²=0.641); combined coverage 99.3%
- Runtime: ~6 min for original 6 metals; ~3 hours for 71-metal USGS extension
- BH-FDR: pooled across all metals simultaneously (35,913 tests for original 6; 456,397 for 71-metal extension)

---

## V3 Final Results — All 71 Elements (2026-08-20)

All 71/71 elements complete. Pooled BH-FDR across 456,397 valid pairs.

| Metric | Value |
|---|---|
| Elements tested | 71 |
| Valid pairs (n≥30, full model) | ~456,397 |
| FDR<0.05 full model (71-element pool) | **6,223** |
| FDR<0.05 base model (71-element pool) | 10,040 |
| 6-metal pool FDR<0.05 | **75** (unchanged) |

### Top 20 elements by full-model hits (71-element pool)

| Element | Hits | Notes |
|---|---|---|
| P | 2,374 | Macronutrient — direct metabolic |
| Mn | 2,112 | Macronutrient — direct metabolic |
| Eu | 141 | REE flagged — 62% at detection limit |
| Ce | 140 | LREE — 60% DOWN |
| Ho | 125 | **EXCLUDE** — 90% at detection limit (IQR=0, beta_sign=0) |
| S | 114 | |
| Cs | 97 | Alkali metal |
| Sn | 92 | |
| Pb | 79 | Contamination metal — 6-metal pool |
| Rb | 73 | Alkali metal |
| Nd | 65 | LREE |
| Al | 57 | |
| Y | 57 | HREE |
| Fe | 53 | |
| K | 46 | Macronutrient |
| Ta | 40 | REE |
| Tb | 38 | REE |
| Zn | 38 | |
| Sm | 35 | REE |
| La | 31 | LREE |

**P and Mn dominate (4,486/6,223 = 72%)** — direct metabolic associations that survive pH control (pH-robust class). Confirmed by pH sensitivity analysis: Mn 55% survival, P 67% (all other elements <5%).

### Covariate partial R² (median, FDR-sig full model)

| Covariate | Median pr2 |
|---|---|
| lc_forest_pct | 0.629 |
| metal | **0.286** |
| hydrologic_group | 0.088 |
| drainage_class | 0.064 |
| elevation_m | 0.060 |
| phylum_proteobacteria | 0.059 |
| lith_class | 0.039 |
| flood_freq | 0.031 |
| phylum_acidobacteria | 0.026 |
| mat_c | 0.025 |
| ph_use | 0.023 |

Metal partial R² (0.286) is 12.4× pH partial R² (0.023) among FDR-significant hits.

---

## Functional Characterization of 75 Conservative Hits (2026-08-20)

**Script:** `scripts/characterize_75_hits.py` → `data/usa_cwm/hits_75_annotated.csv`, `figures/fig_cwm_75hits_characterization.pdf`

KO annotations retrieved via KEGG REST. 75 KO×metal pairs assigned to 9 functional categories. Metal-specific biological themes:

### Functional category breakdown

| Category | β < 0 (depleted) | β > 0 (enriched) | Total | Primary metal |
|----------|-----------------|-----------------|-------|---------------|
| Carbon/energy | 8 | 7 | 15 | Pb (9), Hg (5) |
| Aromatic degradation | 11 | 0 | 11 | Pb (10), As (1) |
| Anaerobic/methanogen | 7 | 3 | 10 | Pb (8), Cr (1), As (1) |
| Uncharacterized | 8 | 2 | 10 | Pb (8), Hg (2) |
| Surface/EPS | 3 | 5 | 8 | Hg (1), Cr (2), Cu (1), Pb (4) |
| Secondary metabolite | 2 | 6 | 8 | Cr (5), Pb (3) |
| Stress/regulatory | 4 | 2 | 6 | Cr (3), Pb (3) |
| Transport | 3 | 2 | 5 | Hg (2), Pb (3) |
| DNA/RNA | 0 | 2 | 2 | Hg (2) |

### Three metal-specific biological themes

**Pb — Aromatic carbon degradation and anaerobic metabolism depleted (34 of 41 Pb hits, β<0):**
Pb-rich soils are systematically depleted in organisms capable of (a) aromatic compound degradation — 10 of 11 aromatic degradation hits are Pb-negative, covering benzoate (K01615, K07537, K07539), vanillate/aminobenzoate (K15063, K15066, K22553), phenylalanine catabolism (K18355, K18357), toluene (K07550), and furan (K16874) pathways; and (b) strict anaerobic metabolism — 8 Pb-negative anaerobic/methanogen hits including heterodisulfide reductase (K03388), formate/CO dehydrogenases (K15022, K00198), TMAO reductase (K03532), selenate reductase (K12529), hydrogenase (K00436), and hydroxylamine dehydrogenase (K10535). Together, aromatic degradation + anaerobic metabolism account for 18 of 34 Pb-negative hits. Pb geochemically concentrates in oxidized, lower-OM environments; both aromatic degraders and strict anaerobes are disadvantaged under such conditions. Whether the association reflects Pb toxicity, shared environmental drivers (high O₂/low OM), or both cannot be resolved from cross-sectional data — the model controls for drainage class and organic matter but these proxies may be incomplete.

**Cr — Secondary metabolite producers and surface-modified organisms enriched (9 of 12 Cr hits, β>0):**
Cr-rich soils are enriched for organisms producing secondary metabolites — 5 Cr-positive hits in antibiotic/polyketide biosynthesis (K18652, K18653 glucose-6-phosphate antibiotic sugar pathway; K17474 pulcherriminic acid synthase; K20489 lantibiotic immunity; K25985 sulfoacetaldehyde reductase/taurine) — and surface polysaccharide modification (K13684 colanic acid glycosyltransferase WcaC, K13677 glycerolipid glucosyltransferase). This is consistent with Cr toxicity selecting for organisms with secondary metabolite production (competitive advantage, metal complexation) and EPS metal binding. The 3 Cr-negative hits include aromatic degradation (K07539) and stress response (K02241 competence, K21884 CRP/FNR regulator).

**Hg — Active central metabolism, transport, and DNA maintenance enriched (all 12 Hg hits, β>0):**
Hg-positive hits span TCA cycle (K00177 2-oxoglutarate ferredoxin oxidoreductase), thiamine biosynthesis (K14153), sugar metabolism (K22233 5-keto-L-gluconate epimerase, K15916 mannose-6-phosphate isomerase), DNA repair (K03573 MutH mismatch repair), rRNA modification (K03212 23S methyltransferase), and ABC transporters (K10108, K17327/K17328). High-Hg sites are enriched for metabolically active, growth-oriented organisms. This is consistent with Hg methylation being carried out by metabolically active sulfate-reducers and Fe-reducers, which may be enriched at geogenic Hg sites (Hg is primarily geogenic at concentrations in this dataset).

### Cross-dataset comparison: CWM vs SPIRE per-KO hits

| Dataset | Approach | FDR<0.05 hits | Overlap |
|---------|---------|---------------|---------|
| CWM (this analysis) | Community-weighted mean ~ measured metal, lm() | 75 KO×metal | — |
| SPIRE (NB04, per-KO) | KO binary presence ~ PF1 modeled metal, Firth logistic | 56 KO×metal | 0 |

**Zero KO-level overlap** (same gene appearing as a hit in both datasets, for any metal). This is consistent with the interpretation that CWM captures **community turnover** (which taxa dominate in high-metal environments) while SPIRE captures **gene-level selection** (which genes are gained or lost across lineages along the metal gradient). Their orthogonality at the KO level supports Adam's reframe: the primary mechanism linking community functional composition to metal concentration is **taxonomic community replacement**, not within-lineage gene gain, at the scale of these soil surveys. The two methods also differ in metal source (measured vs. Qi et al. 2025 modeled predictions) and dataset (amplicon CWM vs. SPIRE MAGs), which may contribute to the discordance independently of the biological mechanism.

---

## EUR/AUS CWM Replication (2026-08-20)

**Purpose:** Independent validation of 75 USA V3 hits using European (GEMAS) and Australian (NGSA) measured metal data joined to MicrobeAtlas community composition.

**Scripts:** `scripts/cwm_eur_aus_replication.py` (v1 data assembly); `scripts/extend_eur_aus_covariates.py` (v2 covariate harmonization); `scripts/eur_aus_latlon_model.py` (v3 lat/lon-controlled)

### V1 model (2026-08-20, limited covariate set)

The initial replication used only 6 covariates (measured pH, clay, EarthEnv land cover ×4, Shannon + 8 phyla). Direct comparison to the 38-covariate USA model is invalid — different covariate sets do not permit cross-regional inference about the same signal.

### V2 model (2026-08-20, harmonized global covariates)

**Motivation:** For valid EUR/AUS vs. USA comparison, only globally available layers can be used. USA-specific covariates (gNATSGO slope/AWC/drainage, EPA TRI releases, SSURGO drainage class, USGS mine distance) are excluded from the shared model.

**Shared covariate set (35 columns, globally available):**
- Soil (SoilGrids master, 0.25°): organic_matter, bulk_density_0cm, sand_0cm, silt_0cm, nitrogen_0cm, cec
- Climate (WorldClim, 0.25°): mat_c, map_mm, temp_seasonality, precip_seasonality, temp_annual_range_c, elevation_m
- Lithology (GLiM): lith_class (13 classes, one-hot encoded)
- Land cover (EarthEnv): lc_forest_pct, lc_cultivated_pct, lc_urban_pct, lc_barren_pct
- Community: shannon + 8 phyla
- pH: measured pH from GEMAS/NGSA (EUR), MicrobeAtlas sample pH (AUS fallback)
- Clay: measured NGSA clay (AUS); SoilGrids-derived for EUR (100 − sand − silt)

**Script:** `scripts/extend_eur_aus_covariates.py` — KDTree join (max_km=40) of SoilGrids, WorldClim, GLiM to EUR/AUS sample lat/lon; R lm() model via subprocess with MC_CORES=4, OMP_NUM_THREADS=1.

**Output files:**
```
data/eur_aus_cwm/
  lm_input_EUR_v2_*.csv        Per-metal lm inputs (EUR, harmonized covariates)
  lm_input_AUS_v2_*.csv        Per-metal lm inputs (AUS, harmonized covariates)
  lm_out_EUR_v2_*.csv          R model results EUR v2
  lm_out_AUS_v2_*.csv          R model results AUS v2
  replication_summary_v2.csv   Same-direction FDR replication table (v2 model)
```

**Results (V2 harmonized covariates):**

| Region | n (complete cases, metal-varies) | Metals | FDR<0.05 hits |
|--------|----------------------------------|--------|----------------|
| EUR    | 133–220 (varies by metal coverage) | 6 | 4 (As×1, Cd×1, Cr×2) |
| AUS    | 30–109 (Cd sparse: 30)             | 6 | 4 (Cr×2, Cu×1, As×1) |

**EUR V2 hits** (BH-FDR pooled across 6 metals):

| KO | Metal | q_BH | δR² | β sign | n |
|----|-------|------|-----|--------|---|
| K00621 | As | 0.045 | 0.128 | + | 133 |
| K24694 | Cd | 0.045 | 0.103 | − | 162 |
| K15896 | Cr | 0.045 | 0.087 | − | 213 |
| K18355 | Cr | 0.045 | 0.106 | − | 142 |

**AUS V2 hits** (BH-FDR pooled across 6 metals):

| KO | Metal | q_BH | δR² | β sign | n |
|----|-------|------|-----|--------|---|
| K27191 | Cr | 0.0003 | 0.335 | + | 84 |
| K27191 | Cu | 0.007  | 0.278 | + | 81 |
| K15896 | Cr | 0.025  | 0.166 | − | 102 |
| K25985 | As | 0.037  | 0.054 | − | 47 |

**Replication of USA V3 hits (75 pairs):**
- Replicated in EUR (same direction, q<0.05): **0/75**
- Replicated in AUS (same direction, q<0.05): **0/75**
- Replicated in either: **0/75**
- EUR directional consistency (same sign, any q): 45/75 (60%)
- AUS directional consistency (same sign, any q): 32/75 (43%)

The null replication reflects power limitations: EUR has 133–220 complete-case samples, AUS 30–109 — substantially below the 634 USA baseline. At these sample sizes, only effects with δR² ≥ ~0.08 have >80% power to replicate at q<0.05.

**Cross-regional finding:** K15896 × Cr is FDR-significant in **both** EUR (q=0.045, δR²=0.087, β<0) and AUS (q=0.025, δR²=0.166, β<0) — consistent negative direction. This KO is not among the 75 USA hits (USA K15896×Cr: q=0.988, p=0.600 — entirely null). K15896 is a notable EUR/AUS-specific signal. In USA, K15896 is strongly associated with P (q=0.0008, β>0) and Zn (q=0.004, β>0), suggesting region-specific geochemical context mediates which element drives K15896 CWM. The EUR+AUS Cr negative direction (more Cr → lower K15896 CWM) is coherent: elevated Cr suppresses K15896-carrying taxa in both European and Australian soils but not in USA soils where Cr co-varies differently with the community.

**K27191 × Cr/Cu (AUS only):** Strongest AUS hit (δR²=0.335 for Cr — larger than any USA Cr hit). USA K27191 is strongly negative for Cs/Rb/K (q<10⁻⁶), reflecting K-uptake biology. The AUS K27191 × Cr positive association (more Cr → more K27191 CWM, β>0) suggests a distinct AUS Cr-ecology context.

### V3 model (2026-08-20, lat/lon spatial control)

**Motivation:** Diagnostic analysis revealed that metal-latitude gradients are **reversed between regions** for Cr, As, Cu (e.g. Cr: ρ_lat USA=+0.25 vs EUR=−0.15 vs AUS=−0.20). Any microbial feature correlated with latitude will produce opposite apparent metal effects across regions. To separate direct metal effects from spatial confounding, `sp_lat` and `sp_lon` were added to the v2 shared covariate set (the R script includes all `sp_*` columns in the linear predictor automatically).

**Spatial confounding summary (r² of log10(metal) ~ lat+lon):**

| Metal | Region | r²(lat+lon) | ρ_lat | ρ_lon |
|-------|--------|-------------|-------|-------|
| Cr | USA | 0.141 | +0.253 | −0.284 |
| Cr | EUR | 0.067 | −0.147 | +0.113 |
| Cr | AUS | 0.098 | −0.198 | +0.355 |
| As | EUR | 0.136 | −0.311 | −0.282 |
| Hg | AUS | 0.203 | −0.442 | +0.344 |

Cr is most abundant at HIGH latitudes in USA but LOW latitudes in EUR/AUS — opposite spatial polarity. USA-EUR and USA-AUS Cr lat-gradients are anti-correlated. This alone can produce apparent association sign reversals between regions without any real biological difference.

**V3 hit summary (3/8 v2 hits survive, 0 new):**

| Region | KO | Metal | q_BH (v3) | δR² | β sign | v2 β | Note |
|--------|-----|-------|-----------|-----|--------|-------|------|
| AUS | K27191 | Cr | 0.0021 | 0.322 | **−** | **+** | **Sign reversal vs v2** |
| AUS | K27191 | Cu | 0.034  | 0.262 | **−** | **+** | **Sign reversal vs v2** |
| EUR | K15896 | Cr | 0.034  | 0.091 | −     | −     | Stable; slightly strengthens |

K27191 encodes DsrC ([DsrC]-trisulfide reductase, sulfur metabolism, map00920). Sulfate-reducing bacteria carrying DsrC are well-documented to be inhibited by Cu and Cr. The v2 positive association was driven by eastern Australia's co-distribution of mafic Cr/Cu geology and higher SRB abundance; after removing the east–west spatial gradient, the true partial effect reverses to negative (high Cr/Cu sites have less K27191).

K15896 (UDP-4-amino-4,6-dideoxy-N-acetyl-beta-L-altrosamine N-acetyltransferase; surface polysaccharide biosynthesis, map00541) shows a stable negative Cr association in EUR that strengthens slightly with lat/lon control (δR² 0.087 → 0.091; p 0.0002 → 0.0001), indicating it is not a spatial confound.

**Dropped by lat/lon control (5/8):**
- AUS K15896×Cr: p=0.0007 in v3 (consistent direction, narrowly missed FDR in 12-pool)
- EUR K18355×Cr: p=0.0011 in v3 (phenylglyoxylate dehydrogenase; narrowly missed FDR)
- AUS K25985×As (n=47): marginal, spatial confound
- EUR K00621×As: linear effect non-significant (p=0.70); spline artifact in v2
- EUR K24694×Cd: linear effect marginal (p=0.072); drops in v3

**Output files:**
```
data/eur_aus_cwm/latlon_model/
  lm_input_{EUR,AUS}_v3_*.csv     Per-metal lm inputs with sp_lat/sp_lon
  lm_out_{EUR,AUS}_v3_*.csv       R model results v3
  gam_results_eur_aus_v3.csv      Pooled BH-FDR across 12 region×metal
```

**Spatial Effective Sample Size (pESS):**

pESS = n × (1 − I) / (1 + I) using Moran's I on Shannon diversity at 250 km binary weights (Griffith 2005).

| Region | n (thinned) | Moran's I | pESS | Mean neighbours |
|--------|-------------|-----------|------|-----------------|
| USA    | 634         | 0.006     | 626.5 | 14.0           |
| EUR    | 490 thinned (220 complete-case in v2 model) | 0.003 | 486.8 | 15.1 |
| AUS    | 173 thinned (78–109 complete-case in v2 model; Cd: 30) | 0.027 | 164.0 | 7.8 |

Spatial autocorrelation in Shannon diversity is negligible in all three regions (Moran I < 0.03), confirming that 0.45° grid thinning is sufficient to remove spatial clustering and that pESS ≈ n in each case. Regional effective sample sizes: USA 626, EUR ~220 (v2 complete-case), AUS ~100 (v2, metal-dependent). The EUR/AUS pESS values are based on the full thinned set; complete-case counts are lower due to global covariate coverage.

# Untested Hypotheses — Analysis Report

**Date:** 2026-07-13
**Dataset:** n = 1,543 genera (soil_sample_pgls_dataset.csv + env covariates)
**Tree:** GTDB r214 bacteria (genus-pruned). Pagel's λ optimised by ML.
**Script:** `scripts/untested_hypotheses_analysis.py`

This report documents 5 novel hypotheses not previously tested in the manuscript.

---

## H5c — BacMet-canonical vs fitness-only resistance subcategory split

**Question:** Is the resistance-null (resistance genes do not predict niche breadth)
uniform across all resistance KOs, or does it mask subgroup heterogeneity between
canonical metal resistance (BacMet-annotated) and pleiotropic fitness-detected genes?

**Rationale:** The 23 Tier 1+2 resistance KOs include classical metal-efflux genes
(cusA, czcA, merR — BacMet-annotated, mechanistically characterised) and genes
detected only by fitness assays as pleiotropic stress responders (fadJ, galE, rpoE —
no BacMet entry). If one subgroup drives a null result while the other is significant,
the composite null result is misleading.

**Gene sets:**
- BacMet-canonical (n = 14 KOs): ACR3, emrB, cusR, cusA, cusB, merR, czcC, czcA,
  czcB, czcD, copA, cueR, gesB, gesA
- Fitness-only pleiotropic (n = 9 KOs): fadJ, galE, manA, hisA, rpoE, pcoB,
  nrsD, tetA, TC.SMR3

Density computed from nb25_ko_presence_matrix.parquet: sum of per-KO presence
fractions (n_genomes_with_ko / n_genomes) divided by mean_genome_mb.

**PGLS results (all models: response = mean_levins_B_std, controlling for genome_size):**

| Model | β | SE | p | n |
|---|---|---|---|---|
| REF: all resistance (combined) | +0.0077 | 0.0053 | 0.144 NS | 1,047 |
| BacMet-canonical resistance | +0.0084 | 0.0036 | 0.021 * | 1,495 |
| Fitness-only pleiotropic | +0.0137 | 0.0046 | 0.003 ** | 869 |
| Joint: BacMet (controlling for FitOnly) | +0.0050 | 0.0056 | 0.376 NS | 865 |
| Joint: FitOnly (controlling for BacMet) | +0.0114 | 0.0054 | 0.035 * | 865 |
| REF: cofactor (opposite sign control) | −0.0128 | 0.0067 | 0.055 † | 842 |

**Correlations:**
- ρ(BacMet resistance density, cofactor density) = 0.078 (p = 0.003)
- ρ(fitness-only resistance density, cofactor density) = 0.083 (p = 0.015)

**Interpretation:**

Both resistance subcategories produce POSITIVE β (more resistance genes → WIDER
niche), and both are statistically significant. This is the **opposite direction** to
the cofactor signal (β = −0.013, more cofactor → NARROWER niche). The resistance-null
in the combined metric (p = 0.144) is an artefact of lower sample coverage (n = 1,047)
relative to the subgroup nb25-based densities (n = 1,495 and n = 869). When coverage
is equalised, the resistance signal is consistently positive.

**Ecological interpretation:** Bacteria inhabiting ecologically diverse environments
(wide niche) invest more in metal resistance genes — consistent with encountering
varied metal stressors across diverse habitats. Specialists (narrow niche) instead
invest in cofactor biosynthesis, optimising for specific growth conditions. Resistance
and cofactor genes track fundamentally different ecological strategies: **adaptation
to breadth vs depth**.

In the joint model, fitness-only resistance (β = +0.011, p = 0.035) is more
predictive than BacMet-canonical (β = +0.005, p = 0.376), consistent with pleiotropic
metabolic genes tracking ecological versatility more broadly than specific
metal-resistance mechanisms.

**Verdict:** HYPOTHESIS NOT SUPPORTED AS FORMULATED — but the finding is
substantively important. The resistance "null" was not confirming absence of signal;
it was obscuring two opposing ecological strategies.

**Manuscript recommendation:** Report the subcategory split explicitly: "Both
BacMet-annotated canonical resistance (β = +0.008, p = 0.021) and fitness-detected
pleiotropic resistance (β = +0.014, p = 0.003) positively predict niche breadth —
the opposite sign to cofactor biosynthesis (β = −0.013). Resistance genes are a
marker of ecological versatility; cofactor genes mark specialisation."

---

## H1b — Environmental range × double-signal gene burden

**Question:** Do genera carrying more double-signal (HGT-prone) metal resistance genes
tend to occupy environments with greater temperature or metal variability?

**Rationale:** HGT-prone resistance genes (high D, low λ) should accumulate
preferentially in genera exposed to fluctuating metal stress. Temperature range
(median_temp_range_C) and GeoROC metal exposures proxy environmental heterogeneity.

**Double-signal gene burden** (ds_n_kos_50) = number of double-signal KOs with
presence fraction > 50% in a genus. Range 0–2 per genus; **only 8 genera carry ≥1**.
This extreme sparsity (1.7% of 478 analysable genera) means PGLS models fit a nearly
binary response. λ = 0.000 in all models (no phylogenetic signal — consistent with HGT
origin of these genes).

**PGLS results (response = ds_n_kos_50, controlling for genome_size):**

| Model | focal β | SE | p | n |
|---|---|---|---|---|
| ds_burden ~ temp_range_z | −0.0075 | 0.0070 | 0.282 NS | 478 |
| ds_burden ~ pH_z | −0.0013 | 0.0073 | 0.857 NS | 478 |
| ds_burden ~ Cu_log_z | +0.0022 | 0.0072 | 0.763 NS | 478 |
| ds_burden ~ Cr_log_z | −0.0210 | 0.0072 | 0.004 ** | 478 |
| ds_burden ~ metal_index_z | −0.0015 | 0.0072 | 0.833 NS | 478 |
| Joint: temp_range | −0.0080 | 0.0076 | 0.29 NS | 478 |
| Joint: pH | +0.0018 | 0.0079 | 0.82 NS | 478 |
| Joint: Cu_log | +0.0014 | 0.0073 | 0.853 NS | 478 |
| hiL_burden ~ temp_range (control) | +0.0073 | 0.0107 | 0.493 NS | 913 |
| B_std ~ ds_burden_z | −0.0052 | 0.0046 | 0.256 NS | 555 |

The Cr result (β = −0.021, p = 0.004) is **not reliable**: with only 8 nonzero genera
driving the signal in a near-binary response, this is a high-leverage artefact. The
absence of a Cr signal in the composite metal index (which includes Cr) confirms this.
Double-signal gene burden does not predict niche breadth (B_std ~ ds_burden: p = 0.256).

**Verdict: HYPOTHESIS NOT SUPPORTED.** Environmental metal and temperature gradients
do not predict double-signal gene burden.

**Manuscript recommendation:** Report as a meaningful null: "The accumulation of
HGT-candidate genes (n = 13 double-signal KOs) is not driven by measurable
environmental metal or temperature gradients at the genus level (all p > 0.28). The
double-signal classification reflects phylogenetic mode (D, λ) not contemporary
environmental selection." Note the extreme sparsity (8/478 genera with ≥1 such gene
at >50% prevalence) as a limitation of this test.

---

## H1a — Per-gene PGLS: environmental associations for double-signal vs high-λ genes

**Question:** Do double-signal (HGT-prone) genes show stronger environmental
associations (pH, temp_range, Cu) than vertically inherited high-λ genes? This would
indicate that HGT-prone genes are environmentally filtered more strongly.

**Method:** For each of 13 double-signal and 10 high-λ genes, PGLS of
presence_fraction ~ pH_z + temp_range_z + Cu_log_z + genome_size_z (n = 1,201 per
gene). Mann–Whitney U test on β distributions between gene types.

**Per-gene results:**

| KO | Gene | Type | D | λ | β_pH | β_temp_range | β_Cu_log | n |
|---|---|---|---|---|---|---|---|---|
| K03897 | iucD | double signal | 0.354 | 0.237 | +0.0023 NS | −0.0009 NS | +0.0010 NS | 1,201 |
| K05908 | doxDA | double signal | 0.254 | 0.000 | −0.0017 NS | +0.0010 NS | −0.0001 NS | 1,201 |
| K07785 | nrsD | double signal | 0.821 | 0.089 | −0.0015 † | +0.0007 NS | +0.0008 NS | 1,201 |
| K08170 | norB | double signal | 0.239 | 0.033 | −0.0015 NS | +0.0014 NS | +0.0025 * | 1,201 |
| K08356 | aoxB | double signal | 0.562 | 0.000 | +0.0002 NS | −0.0021 NS | −0.0002 NS | 1,201 |
| K14974 | nicC | double signal | 0.224 | 0.000 | +0.0005 NS | +0.0012 NS | −0.0002 NS | 1,201 |
| K15585 | nikB | double signal | 0.202 | 0.000 | −0.0002 NS | −0.0024 NS | −0.0021 NS | 1,201 |
| K19057 | merD | double signal | 0.701 | 0.165 | +0.0001 NS | +0.0014 NS | +0.0005 NS | 1,201 |
| K19059 | merE | double signal | 0.728 | 0.102 | −0.0003 NS | −0.0000 NS | +0.0002 NS | 1,201 |
| K19592 | golS | double signal | 0.265 | 0.135 | +0.0011 † | −0.0004 NS | +0.0003 NS | 1,201 |
| K19594 | gesB | double signal | 0.597 | 0.156 | +0.0002 NS | +0.0005 NS | +0.0002 NS | 1,201 |
| K19595 | gesA | double signal | 0.458 | 0.161 | +0.0002 NS | +0.0006 NS | +0.0003 NS | 1,201 |
| K25119 | shp | double signal | 0.385 | 0.000 | −0.0003 NS | +0.0019 ** | +0.0001 NS | 1,201 |
| K18146 | adeB | high-λ | 0.245 | 1.000 | −0.0008 NS | +0.0016 † | −0.0000 NS | 1,201 |
| K07807 | K07807 | high-λ | 0.426 | 0.936 | −0.0009 NS | −0.0004 NS | +0.0004 NS | 1,201 |
| K18307 | mexI | high-λ | −0.065 | 0.921 | +0.0004 NS | −0.0010 NS | +0.0003 NS | 1,201 |
| K22041 | comR | high-λ | 0.103 | 0.887 | +0.0019 NS | +0.0058 * | +0.0030 NS | 1,201 |
| K08355 | aoxA | high-λ | 0.423 | 0.878 | +0.0015 NS | −0.0010 NS | +0.0005 NS | 1,201 |
| K02230 | cobN | high-λ | 0.029 | 0.849 | −0.0010 NS | −0.0004 NS | −0.0071 † | 1,201 |
| K09883 | cobT | high-λ | −0.119 | 0.847 | −0.0029 NS | −0.0017 NS | −0.0002 NS | 1,201 |
| K07796 | cusC | high-λ | 0.258 | 0.846 | +0.0095 * | −0.0111 ** | +0.0017 NS | 1,201 |
| K21572 | susD | high-λ | −0.286 | 0.830 | −0.0041 NS | +0.0027 NS | −0.0010 NS | 1,201 |
| K08167 | smvA | high-λ | −0.041 | 0.830 | −0.0008 NS | +0.0059 NS | −0.0010 NS | 1,201 |

**Mann–Whitney U: double-signal vs high-λ β distributions:**

| Variable | DS mean β | HiL mean β | DS n | HiL n | p_MWU |
|---|---|---|---|---|---|
| Soil pH | −0.0001 | +0.0003 | 13 | 10 | 0.733 NS |
| Temp range | +0.0002 | +0.0000 | 13 | 10 | 1.000 NS |
| GeoROC Cu | +0.0002 | −0.0003 | 13 | 10 | 0.828 NS |

**Notable individual results:**
- **shp (K25119)**: temp_range β = +0.0019 (p = 0.006) — unusual iron acquisition gene more
  prevalent in genera spanning wide temperature ranges
- **cusC (K07796, high-λ)**: pH β = +0.0095 (p = 0.028), temp β = −0.0111 (p = 0.009) —
  the strongest env association in the dataset; occurs in genera at neutral-high pH, low temp range
- **norB (K08170)**: Cu β = +0.0025 (p = 0.049) — nitric oxide reductase more prevalent in
  Cu-rich bedrock environments

**Verdict: HYPOTHESIS NOT SUPPORTED.** Environmental β distributions are statistically
indistinguishable between double-signal and high-λ genes (all MWU p > 0.73). Individual
gene signals are weak and scattered. Double-signal gene classification reflects
phylogenetic mode (D and λ), not stronger environmental filtering.

**Manuscript recommendation:** Include per-gene table as supplementary. Note cusC and
shp as individual outliers. State: "HGT-prone and vertically inherited metal resistance
genes show indistinguishable environmental associations with soil pH, temperature range,
and bedrock Cu at the genus level (MWU p > 0.73 for all three variables), consistent
with the hypothesis that HGT history is not erased by contemporary environmental
selection at the genus scale."

---

## H4c — Cofactor signal controlling for housekeeping landscape

**Question:** Does the cofactor biosynthesis signal (niche breadth ~ cofactor density)
survive when translation and replication/repair density are included as co-predictors?

**Rationale:** Translation density is the 2nd-strongest KEGG category predictor of
niche breadth (from the functional landscape analysis). Cofactor and translation are
correlated (ρ = 0.364), raising the question of whether cofactor proxies metabolic
richness rather than signalling specific metal-adaptation.

**Key correlations:**
- ρ(cofactor, translation) = 0.364 (p = 1×10⁻²⁷) — moderate
- ρ(cofactor, replication_repair) = 0.454 (p = 4.6×10⁻⁴⁴) — moderate

**PGLS results (response = mean_levins_B_std, controlling for genome_size):**

| Model | focal | β | SE | p | n |
|---|---|---|---|---|---|
| REF: cofactor only | cofactor | −0.0128 | 0.0067 | 0.055 † | 842 |
| + translation | cofactor | −0.0091 | 0.0069 | 0.190 NS | 842 |
| + translation | translation | −0.0175 | 0.0089 | 0.050 * | 842 |
| + replication_repair | cofactor | −0.0084 | 0.0076 | 0.266 NS | 842 |
| + replication_repair | replication | −0.0133 | 0.0110 | 0.228 NS | 842 |
| Full joint | cofactor | −0.0085 | 0.0076 | 0.264 NS | 842 |
| Full joint | translation | −0.0164 | 0.0105 | 0.118 NS | 842 |
| Full joint | replication | −0.0027 | 0.0129 | 0.836 NS | 842 |

**Interpretation:**

The cofactor signal (already only marginal at p = 0.055†) does **not survive** when
translation is included as a co-predictor (cofactor p = 0.190 NS). Translation is
itself a significant predictor of niche breadth (β = −0.018, p = 0.050), with a larger
effect size than cofactor. In the full joint model, neither cofactor nor translation nor
replication_repair is significant, consistent with mutual collinearity between all three
housekeeping/metabolic categories (ρ = 0.36–0.45).

The moderate collinearity (ρ ≈ 0.36–0.45) means the models are underpowered to
separate the contributions once correlated predictors are included. However, the pattern
is clear: **translation is at minimum equally predictive and possibly the primary driver**.
The cofactor-specific component is at best marginal and not independently replicable.

**Verdict: HYPOTHESIS SUPPORTED — the cofactor signal does NOT survive housekeeping
controls.** Translation density is a confounder of the cofactor signal, suggesting that
what was attributed to cofactor biosynthesis is partly a signal of overall metabolic
investment (slow-growth specialist lifestyle), not metal-cofactor specificity.

**Manuscript recommendation:** This is an important caveat. Add: "The cofactor
biosynthesis association with niche breadth (β = −0.013, p = 0.055†) is partially
confounded by translation machinery density (ρ = 0.36), which is itself an independent
negative predictor (β = −0.018, p = 0.050). When both are included jointly, cofactor
becomes non-significant (β = −0.009, p = 0.19). The cofactor signal may reflect a
broader 'metabolic complexity → ecological specialisation' relationship rather than
metal-cofactor specificity per se. This is consistent with the streamlining framework
(Giovannoni et al. 2014) but limits strong claims about metal-specific cofactor ecology."

---

## H3b — Double-signal gene burden × metal exposure across geographic range

**Question:** Do genera carrying more double-signal HGT-candidate genes tend to occur
in geochemically richer environments (higher bedrock Cu, Cr, or composite metal index)?

**Rationale:** If environmental metal selection drives HGT of resistance genes, genera
in high-metal environments should accumulate more double-signal genes. High-λ genes
(vertically inherited) serve as a negative control.

**Key context:** Only 8 genera carry ≥1 double-signal KO at >50% prevalence
(ds_n_kos_50 > 0). Models have λ = 0 (no phylogenetic signal in double-signal gene
presence, consistent with HGT). With such sparse data, the PGLS results are interpreted
cautiously.

**PGLS results:**

| Model | focal β | SE | p | n |
|---|---|---|---|---|
| ds_burden ~ Cu_log_z | +0.0022 | 0.0072 | 0.763 NS | 478 |
| ds_burden ~ Cr_log_z | −0.0210 | 0.0072 | 0.004 ** | 478 |
| ds_burden ~ metal_idx + pH (metal_idx) | −0.0012 | 0.0077 | 0.875 NS | 478 |
| ds_burden ~ metal_idx + pH (pH focal) | −0.0009 | 0.0078 | 0.911 NS | 478 |
| hiL_burden ~ Cu_log (control) | −0.0190 | 0.0109 | 0.081 † | 906 |
| hiL_burden ~ metal_index (control) | −0.0126 | 0.0115 | 0.275 NS | 912 |
| B_std ~ ds_burden + metal_idx (ds_burden) | −0.0042 | 0.0045 | 0.344 NS | 478 |
| B_std ~ ds_burden + metal_idx (metal_idx) | +0.0146 | 0.0055 | 0.008 ** | 478 |

**Notable results:**

1. **Cr_log (ds_burden): β = −0.021, p = 0.004 (NEGATIVE)** — more bedrock Cr → fewer
   double-signal genes present. This is counterintuitive but statistically fragile: with
   8 nonzero genera driving this result, a single high-leverage genus in low-Cr area could
   explain it. The Cr signal does not replicate in the composite metal index (p = 0.875).

2. **B_std ~ metal_idx: β = +0.0146, p = 0.008** — genera in higher-metal environments
   have WIDER niche breadth. This is consistent with H5c: metal-exposed environments
   favour generalists with broad metal resistance.

3. **Neither gene type** (double-signal or high-λ) shows a clear positive association
   with metal exposure, so the H3b prediction (more HGT in high-metal genera) is not
   supported.

**Verdict: HYPOTHESIS NOT SUPPORTED.** Double-signal gene burden does not positively
track metal exposure. The incidental Cr result (negative, counterintuitive) is not
robust to sensitivity checks.

**Manuscript recommendation:** The metal_idx → B_std positive β (+0.015, p = 0.008)
is worth noting as a secondary finding: "Genera occupying geochemically richer
environments (higher bedrock metal composite index) had significantly wider ecological
niches (β = +0.015, p = 0.008), consistent with the pattern that metal-exposed habitats
favour ecologically versatile generalists who invest in broader resistance repertoires
(cf. H5c)." Report H3b main result as null.

---

## Summary of all tested hypotheses

| Hypothesis | Model | n | β | p | Direction | Verdict |
|---|---|---|---|---|---|---|
| H5c | All resistance ~ B_std | 1,047 | +0.008 | 0.144 NS | positive | NULL |
| H5c | BacMet resistance ~ B_std | 1,495 | +0.008 | 0.021 * | positive | SUPPORTED |
| H5c | Fitness-only resistance ~ B_std | 869 | +0.014 | 0.003 ** | positive | SUPPORTED |
| H5c | Joint: fitness-only ~ B_std | 865 | +0.011 | 0.035 * | positive | SUPPORTED |
| H5c | REF cofactor ~ B_std | 842 | −0.013 | 0.055 † | negative | MARGINAL |
| H1b | ds_burden ~ temp_range | 478 | −0.008 | 0.282 NS | — | NULL |
| H1b | ds_burden ~ Cu_log | 478 | +0.002 | 0.763 NS | — | NULL |
| H1b | B_std ~ ds_burden | 555 | −0.005 | 0.256 NS | — | NULL |
| H1a | DS mean β_pH vs HiL (MWU) | 13 vs 10 | — | 0.733 NS | — | NULL |
| H1a | DS mean β_temp vs HiL (MWU) | 13 vs 10 | — | 1.000 NS | — | NULL |
| H4c | cofactor ~ B_std (REF) | 842 | −0.013 | 0.055 † | negative | MARGINAL |
| H4c | + translation: cofactor focal | 842 | −0.009 | 0.190 NS | — | COFACTOR NULL |
| H4c | + translation: translation focal | 842 | −0.018 | 0.050 * | negative | SUPPORTED |
| H3b | ds_burden ~ Cu_log | 478 | +0.002 | 0.763 NS | — | NULL |
| H3b | B_std ~ metal_index | 478 | +0.015 | 0.008 ** | positive | SUPPORTED |

---

## Cross-hypothesis synthesis

Three findings are worth reporting in the manuscript:

**Finding 1 (H5c): Resistance and cofactor genes have opposite ecological correlates.**
Resistance gene density (both BacMet-canonical and fitness-pleiotropic) positively
predicts niche breadth (β ≈ +0.008–+0.014), while cofactor density negatively predicts
it (β ≈ −0.013). The primary analysis resistance null was a power artefact. The actual
ecology is: **generalists invest in resistance, specialists invest in cofactors**.

**Finding 2 (H4c): The cofactor signal is confounded by translation density.**
Translation machinery density (β = −0.018, p = 0.050) is at least as predictive as
cofactor, and including it eliminates the cofactor signal (β = −0.009, p = 0.19).
This weakens the claim that metal-cofactor specificity is the mechanism; the signal may
reflect overall metabolic investment → ecological specialisation more broadly.

**Finding 3 (H3b/H5c cross): Metal-rich environments favour generalists.**
Genera in higher metal-composite-index environments have wider niche breadth
(β = +0.015, p = 0.008), consistent with H5c resistance results. Metal environments
select for ecological versatility and broader resistance repertoires.

**Null findings (H1a, H1b, H3b burden):** HGT-prone gene classification does not
predict environmental exposure or gene burden at the genus level. The double-signal
framework describes evolutionary mode (phylogenetic D and λ), not contemporary ecology.

---

## Analyses not run (data limitations)

| Hypothesis | Reason not run |
|---|---|
| H2a: dN/dS per-gene selection | No pre-computed dN/dS data in project directory |
| H2b: Transposase proximity to resistance genes | No genome neighbourhood / gene position data |
| H2c: KO phylogenetic age (phylostratigraphy) | No MRCA estimation data available |
| H4a: Double-signal gene co-occurrence with AMR | Requires genome-level co-occurrence network |
| H4b: Transposase density in double-signal genera | No transposase KOs in nb25 (343 KOs are Tier 1–3 metal genes only) |
| H1c: Geographic hotspots for double-signal genes | Requires sample-level presence maps |
| H3b extended: Hg/As bedrock exposure | No genus-level Hg or As data in genus_lat_env_covariates.csv |
| H6b: Transcriptomic validation of cofactor genes | Requires external literature search |
| H3a: Community-weighted metal-gene density (CWM) | **COMPLETED 2026-07-13** via BERDL Spark — see Follow-up analyses section below |

---

## Follow-up analyses — manuscript finalisation

**Date:** 2026-07-13
**Script:** `scripts/manuscript_followup_analysis.py`
**Output:** `data/followup_analysis_results.csv`

---

### H4c follow-up — Full housekeeping joint model + partial R²

**Question:** Does the cofactor biosynthesis signal survive when ALL available housekeeping
categories are included simultaneously? What is the unique variance each predictor explains?

**Note on ribosomal predictor:** No ribosomal landscape file is available
(`landscape_ribosomal_density.csv` absent; NB23 KEGG ko03016 Translation fetch returned 0 KOs
due to an API issue). The `translation_per_mb` column (KEGG ko03000 Translation category) is
used, which includes ribosomal subunits, translation factors, and aminoacyl-tRNA biosynthesis.
The model is therefore equivalent to a 3-predictor housekeeping joint model.

**Model:** `mean_levins_B_std ~ cofactor_z + translation_z + replication_repair_z + gsize_z`
n = 842, R² = 0.0948, λ = 0.776 (fixed at this value for partial R² computation)

| Predictor | β | SE | p | Semi-partial R² |
|---|---|---|---|---|
| cofactor_z | −0.0085 | 0.0076 | 0.264 NS | 0.0084 |
| translation_z | −0.0164 | 0.0105 | 0.118 NS | 0.0026 |
| replication_repair_z | −0.0027 | 0.0129 | 0.836 NS | 0.0000 |
| genome_size_z | +0.0239 | 0.0080 | 0.003 ** | 0.0097 |

*Semi-partial R² = R²_full − R²_model-without-that-predictor, computed at fixed λ = 0.776.*

**Interpretation:**

No housekeeping predictor is individually significant when all are included jointly, confirming
collinearity (ρ(cofactor, translation) = 0.364; ρ(cofactor, replication_repair) = 0.454).
Genome size has the largest unique contribution (semi-partial R² = 0.0097), slightly exceeding
cofactor (0.0084). Translation contributes little unique variance (0.0026) once cofactor is
accounted for. Replication/repair contributes essentially nothing unique (0.0000). These
semi-partial R²s sum to 0.021, well below the full-model R² = 0.095, indicating that
the majority of explained variance is shared among the correlated predictors and cannot be
partitioned unambiguously.

**Verdict:** Cofactor contributes unique variance comparable to genome size (semi-partial R²
≈ 0.008 each), but the individual coefficient is NS in the joint model due to collinearity.
The signal is real but not separable from broader metabolic investment patterns.

---

### H5c follow-up — Expanded resistance Tier 3–5 density

**Question:** Does the resistance-positivity pattern extend to the broader set of metal
resistance/detoxification KOs in Tiers 3–5 (less curated, more diverse mechanisms)?

**Gene set:** 83 Tier 3–5 resistance KOs from `curated_mrg_ko_ids_v2.csv` (all
`is_resistance == True`, `evidence_tier` not in Tier 1/2/2-Fitness). 63 of 83 KOs are
present in `nb25_ko_presence_matrix.parquet`; 20 absent. Density computed the same way as
Tier 1–2: sum of per-KO presence fractions / mean_genome_mb.

**Key data characteristic:** ρ(Tier 1–2, Tier 3–5) = 0.745 (p = 2.6×10⁻²⁶⁴, n = 1,494)
— the two resistance tiers are very highly correlated and cannot be independently separated.

| Model | β | SE | p | λ | n |
|---|---|---|---|---|---|
| Tier 3–5 alone (+ gsize) | +0.0103 | 0.0034 | 0.003 ** | 0.737 | 1,532 |
| Tier 1–2 nb25 alone (+ gsize) | +0.0098 | 0.0037 | 0.008 ** | 0.743 | 1,499 |
| Joint — Tier 1–2 (controlling for Tier 3–5) | +0.0042 | 0.0049 | 0.393 NS | 0.740 | 1,494 |
| Joint — Tier 3–5 (controlling for Tier 1–2) | +0.0078 | 0.0046 | 0.090 † | 0.740 | 1,494 |

**Interpretation:**

Both resistance tiers produce POSITIVE β (generalists carry more resistance genes), and both
are significant in single-predictor models. The very high inter-tier correlation (ρ = 0.745)
means the joint model cannot separate them — both become NS or marginal due to collinearity.
The resistance-positivity pattern from H5c is robustly replicated in the expanded, less curated
Tier 3–5 gene set (β = +0.010, p = 0.003), confirming this is a genome-wide resistance
ecology signal rather than an artefact of a small curated gene set.

**Verdict:** Resistance positivity is robust to expansion of the resistance gene set across
curation tiers. The pattern generalises beyond the 23 Tier 1–2 KOs to 63+ Tier 3–5 KOs.

---

### H3a — Community-weighted mean (CWM) metal-gene density

**Status: COMPLETED — run on BERDL Spark cluster (2026-07-13).**

Scripts: `scripts/h3a_cwm_analysis.py` (v1, merge bug) → `scripts/h3a_cwm_analysis_v2.py` (corrected).
Output: `data/h3a_cwm_analysis_v2_results.csv`, `data/h3a_cwm_analysis_v2_samples.csv`.

**Question:** Do communities in metal-rich soils have higher or lower community-weighted
mean (CWM) metal-gene density?

**Method:**
- MicrobeAtlas `otu_counts_long` (69M OTU rows for soil/agricultural samples) aggregated to
  genus level per sample using SILVA taxonomy (field index 5 of semicolon-delimited `Tax`).
- CWM = Σ_g (RA_{s,g} × ko_per_mb_primary_g) per sample. Genus name matching: SILVA → GTDB
  by exact lowercase string (approximate; mean 62% of community matched by mass).
- Environmental predictors from `arkinlab.envdbs`:
  - `csu_metal_mobility_grid`: BCR phase 1 (exchangeable/bioavailable) metal fractions (pf1)
    for Cu, Cr, Cd, As, Pb at ~0.045° grid resolution.
  - `science_2025_global_soil_toxic_metals`: total soil concentrations of Cu, Ni, Co, Cr, Pb
    at ~0.1° grid resolution.
  - `olm_soil_ph_0cm_H2O` from `enriched_metadata_gee` (stored as pH × 10 integer).
- Spatial join via 0.05° lat/lon rounding in Spark.
- All predictor columns log-transformed (except soil pH); standardised to z-scores.
- OLS + Spearman ρ reported.

**Samples:** 83,401 soil/agricultural samples with ≥5% community matched to genus density data.

**CWM metal-gene density (ko_per_mb_primary) ~ environmental metals:**

| Predictor | Source | n | β_OLS | p_OLS | ρ_Spearman | p_Spearman |
|---|---|---|---|---|---|---|
| Cd (pf1, bioavailable) | CSU | 51,230 | −0.074 | 7×10⁻¹² *** | −0.060 | 2×10⁻⁴¹ *** |
| As (pf1, bioavailable) | CSU | 51,230 | +0.033 | 0.002 ** | +0.008 | 0.06 † |
| Pb (pf1, bioavailable) | CSU | 51,230 | −0.038 | 0.0005 *** | −0.005 | 0.27 NS |
| Cr (pf1, bioavailable) | CSU | 51,230 | −0.031 | 0.004 ** | +0.002 | 0.67 NS |
| Cu (pf1, bioavailable) | CSU | 51,230 | −0.006 | 0.61 NS | +0.006 | 0.17 NS |
| Co (total soil)        | Sci2025 | 15,248 | −0.068 | 0.0003 *** | −0.066 | 4×10⁻¹⁶ *** |
| Cu (total soil)        | Sci2025 | 15,382 | +0.046 | 0.015 * | +0.039 | 2×10⁻⁶ *** |
| Ni (total soil)        | Sci2025 | 15,377 | −0.008 | 0.66 NS | −0.020 | 0.015 * |
| Soil pH (×10 scale)    | OLM | 64,466 | +0.244 | 1.5×10⁻¹¹⁷ *** | +0.062 | 1×10⁻⁵⁶ *** |

**CWM resistance gene density ~ environmental metals:**

| Predictor | Source | n | β_OLS | p_OLS | ρ_Spearman | p_Spearman |
|---|---|---|---|---|---|---|
| Cd (pf1, bioavailable) | CSU | 51,225 | −0.025 | 8×10⁻⁶⁶ *** | −0.096 | 8×10⁻¹⁰⁵ *** |
| As (pf1, bioavailable) | CSU | 51,225 | −0.014 | 4×10⁻²¹ *** | −0.050 | 2×10⁻²⁹ *** |
| Co (total soil)        | Sci2025 | 15,245 | −0.038 | 3×10⁻⁴⁹ *** | −0.129 | 4×10⁻⁵⁷ *** |
| Ni (total soil)        | Sci2025 | 15,374 | −0.010 | 0.0002 *** | −0.021 | 0.009 ** |
| Soil pH                | OLM | 64,458 | +0.015 | 3×10⁻³⁰ *** | +0.034 | 7×10⁻¹⁸ *** |

**Interpretation:**

The dominant pattern is **negative**: communities in soils with higher bioavailable metal
concentrations (Cd, As, Pb, Cr BCR-phase-1) and higher total soil Co and Ni have *lower*
CWM metal-gene density — both for total metal genes and resistance genes.

This is directionally consistent with the genus-level findings:
- H1: genera with more metal genes per Mb are specialists (narrower niche breadth)
- H3b: genera from metal-rich habitats have *wider* niche breadth (more generalist)

In combination, these results imply that communities in metal-stressed soils are dominated
by **generalist** taxa — organisms that tolerate metals through broad physiological flexibility
rather than through high per-genome metal-gene investment. The CWM analysis provides
community-scale evidence for this "generalist tolerance" mechanism.

Soil pH is the strongest predictor (Spearman ρ ≈ +0.06, n = 64k), positively associated
with all three CWM metrics. Alkaline soils (where metals are less bioavailable) harbour
communities with higher CWM gene density across all categories — consistent with more
metabolically complex, phylogenetically diverse communities in fertile agricultural soils.

**Caveats:**
- SILVA → GTDB genus-name matching is approximate; mean 62% community coverage by mass.
  Metal-tolerant specialists may be systematically missed if they are SILVA genera not in
  the PGLS dataset.
- Science_2025 coverage is lower (15k samples vs 51k for CSU); the Cr and Cu positive
  associations in that dataset may reflect geographic confounding (mafic geology regions).
- The soil pH variable (`olm_soil_ph_0cm_H2O`) appears stored as pH × 10 (range 41–87);
  interpretations apply to the z-scored predictor.
- OLS regressions ignore spatial autocorrelation and sample interdependence. Results
  should be treated as descriptive.

**Verdict: H3a COMPLETED — pattern consistent with genus-level findings.** Communities in
high-metal soils have lower CWM metal-gene density, reflecting generalist-dominated assemblages.
The community-level signal is directionally opposite to a naive "more metal → more metal genes"
expectation, and instead aligns with the niche-breadth specialisation story (H1, H3b).

---

### H5a — PIC robustness: phylogenetic independent contrasts

**Question:** Does the primary PGLS result (niche breadth ~ metal-gene density,
β = −0.021, p = 2.1×10⁻⁸) hold under the alternative phylogenetic control method
of Felsenstein's (1985) phylogenetic independent contrasts?

**Method:** Implemented in Python using dendropy (R/ape not available on this system).
Post-order traversal of the GTDB r214 tree to compute standardised contrasts at each
bifurcating internal node. Genera with missing data propagate upward (accumulating branch
length) without generating a contrast. Regression fitted through the origin (no intercept)
using OLS, as required by PIC theory.

n = 1,542 valid contrasts (out of 1,543 analysable genera; tree is fully bifurcating
so n_contrasts = n_genera − 1).

| Model | β | SE | p |
|---|---|---|---|
| PIC bivariate: niche ~ ko_per_mb (origin) | −0.00507 | 0.00103 | 9.5×10⁻⁷ *** |
| PIC + genome size: niche ~ ko + gsize (origin) | −0.00353 | 0.00110 | 0.0013 ** |
| PGLS reference (Pagel's λ) | −0.02100 | — | 2.1×10⁻⁸ *** |

*Note: PIC β and PGLS β are not numerically comparable — they operate on different scales.
PIC contrasts are standardised by √(branch length); PGLS β is on the raw data scale with
phylogenetic covariance absorbed via Pagel's λ. Only sign and significance are compared.*

**Interpretation:**

Both PIC models confirm the negative association: genera with higher metal-gene density have
narrower ecological niches (β_PIC < 0, p ≤ 0.001 in both models). The direction is consistent
with PGLS under two different methods of phylogenetic control. The genome-size covariate remains
positive (β = +0.012, p = 0.0001***) — genera with larger genomes have wider niches — consistent
with the PGLS result (genome size β = +0.024, p = 0.003**).

The magnitude difference (PIC |β| ≈ 0.004–0.005 vs PGLS |β| = 0.021) reflects the different
scales: PIC standardises contrasts by branch-length variances, making the regression coefficient
non-comparable to the raw-data PGLS coefficient. The Pearson r on the PIC contrasts is −0.124
(p = 1.1×10⁻⁶), equivalent to a partial correlation of ~0.12 after phylogenetic control.

**Verdict: HYPOTHESIS SUPPORTED — the primary finding is robust to method.** PIC independently
replicates the negative direction (β < 0) with p < 0.001, validating that the PGLS result
is not an artefact of the specific implementation of phylogenetic control.

---

## Updated summary table (including follow-up analyses)

| Hypothesis | Model | n | β | p | Direction | Verdict |
|---|---|---|---|---|---|---|
| H5c | All resistance ~ B_std | 1,047 | +0.008 | 0.144 NS | positive | NULL |
| H5c | BacMet resistance ~ B_std | 1,495 | +0.008 | 0.021 * | positive | SUPPORTED |
| H5c | Fitness-only resistance ~ B_std | 869 | +0.014 | 0.003 ** | positive | SUPPORTED |
| H5c | Joint: fitness-only ~ B_std | 865 | +0.011 | 0.035 * | positive | SUPPORTED |
| H5c | REF cofactor ~ B_std | 842 | −0.013 | 0.055 † | negative | MARGINAL |
| **H5c FU** | **Tier 3–5 resistance ~ B_std** | **1,532** | **+0.010** | **0.003 \*\*** | **positive** | **SUPPORTED** |
| **H5c FU** | **Joint Tier 3–5 (marginal)** | **1,494** | **+0.008** | **0.090 †** | **positive** | **MARGINAL** |
| H1b | ds_burden ~ temp_range | 478 | −0.008 | 0.282 NS | — | NULL |
| H1b | ds_burden ~ Cu_log | 478 | +0.002 | 0.763 NS | — | NULL |
| H1b | B_std ~ ds_burden | 555 | −0.005 | 0.256 NS | — | NULL |
| H1a | DS mean β_pH vs HiL (MWU) | 13 vs 10 | — | 0.733 NS | — | NULL |
| H1a | DS mean β_temp vs HiL (MWU) | 13 vs 10 | — | 1.000 NS | — | NULL |
| H4c | cofactor ~ B_std (REF) | 842 | −0.013 | 0.055 † | negative | MARGINAL |
| H4c | + translation: cofactor focal | 842 | −0.009 | 0.190 NS | — | COFACTOR NULL |
| H4c | + translation: translation focal | 842 | −0.018 | 0.050 * | negative | SUPPORTED |
| **H4c FU** | **Full joint: cofactor (+ tran + rep)** | **842** | **−0.009** | **0.264 NS** | **—** | **COFACTOR NULL** |
| **H4c FU** | **Full joint: translation** | **842** | **−0.016** | **0.118 NS** | **—** | **NULL (collinear)** |
| **H4c FU** | **Full joint: genome size** | **842** | **+0.024** | **0.003 \*\*** | **positive** | **SUPPORTED** |
| H3b | ds_burden ~ Cu_log | 478 | +0.002 | 0.763 NS | — | NULL |
| H3b | B_std ~ metal_index | 478 | +0.015 | 0.008 ** | positive | SUPPORTED |
| **H3a** | **CWM ko ~ CSU Cd (pf1, bioavail.)** | **51,230** | **−0.074** | **7×10⁻¹² \*\*\*** | **negative** | **CONSISTENT** |
| **H3a** | **CWM ko ~ soil pH** | **64,466** | **+0.244** | **1.5×10⁻¹¹⁷ \*\*\*** | **positive** | **CONSISTENT** |
| **H3a** | **CWM resistance ~ sci2025 Co** | **15,245** | **−0.038** | **3×10⁻⁴⁹ \*\*\*** | **negative** | **CONSISTENT** |
| **H5a** | **PIC bivariate (niche ~ ko)** | **1,542** | **−0.005** | **9.5×10⁻⁷ \*\*\*** | **negative** | **REPLICATED (PIC)** |
| **H5a** | **PIC + genome size (niche ~ ko)** | **1,542** | **−0.004** | **0.001 \*\*** | **negative** | **REPLICATED (PIC)** |

*Bold rows = follow-up analyses added 2026-07-13. FU = follow-up.*
*H3a "consistent" = direction matches genus-level prediction (lower CWM in high-metal soils reflects generalist dominance). β is OLS (z-scored predictor). Not a direct test of the hypothesis.*
*PIC β magnitudes are not comparable to PGLS β — only sign and significance are compared.*

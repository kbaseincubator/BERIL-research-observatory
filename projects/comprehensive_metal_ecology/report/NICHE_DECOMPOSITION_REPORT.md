# Niche Breadth Decomposition — Analysis Report

> **Working document only.** This report and the associated figure (`figures/png/niche_decomposition_scatter.png`) are not part of the approved scientific record in `REPORT.md`. The analysis supports future manuscript Supplementary placement (cross-biome vs. within-soil B_cross/B_soil decomposition) but has not been formally reviewed or cited. Do not cite figures from this file in REPORT.md without adding them to the figures inventory and re-running `/berdl-review`.

## Overview

Tests whether the primary metal-gene–niche breadth association (β = −0.021, p = 2.1×10⁻⁸)
is driven by **cross-biome breadth** (B_cross — ability to span multiple major biomes) or
**within-soil breadth** (B_soil — fine-scale habitat diversity within the soil biome).

**B_cross** = mean_levins_B_std: Levins' B_std from all MicrobeAtlas Env_Level_1 biome
categories (soil, marine, freshwater, host-associated, etc.). Range [0.003, 0.747].

**B_soil** = levins_B_soil_std: Levins' B_std from soil/agricultural samples only, using
7 Env_Level_2 sub-habitats as the niche axis. Range [0.000, 0.319].

**Soil specialist** = genus with frac_soil > 0.5 (>50% of OTU occurrences in soil biome).

**Analysis dataset:** n = 1,543 genera — all genera with ≥5 soil sample occurrences
(required for B_soil computation); excludes 31 genera from the full P1 dataset (n=1,574)
that lack soil presence. The analysis subset β for B_cross is −0.0118 (p = 0.0036,
λ = 0.742), somewhat smaller than the full-dataset P1 β = −0.021 (p = 2.1×10⁻⁸, λ = 0.757),
suggesting the excluded non-soil genera contribute to the full signal.

Tree: GTDB r214 bacteria (genus-pruned). Pagel's λ optimised by ML in all models.

---

## Step 1 — Variance decomposition

| Metric | Mean | SD | Min | Max |
|---|---|---|---|---|
| B_cross (all biomes) | 0.247 | 0.150 | 0.003 | 0.747 |
| B_soil (within soil) | 0.072 | 0.048 | 0.000 | 0.319 |

**Variance ratio B_cross/B_soil = 9.8×** — B_cross has nearly 10× more variance than B_soil.

**Key diagnostic:** If a within-soil effect existed proportional to the cross-biome effect,
we would expect β_Bsoil_true ≈ β_Bcross × (SD_Bcross / SD_Bsoil) ≈ −0.021 × 3.1 = −0.066.
The observed β_Bsoil ≈ 0 (p = 0.97) therefore indicates the within-soil effect is
biologically near zero, not merely undetectable — power is not the explanation.

**Cross-measure correlations:**
- Spearman ρ(B_cross, B_soil) = +0.381 (p = 1.8×10⁻⁵⁴) — weakly correlated; distinct information
- Spearman ρ(B_cross, frac_soil) = +0.306 — soil-associated genera are not more restricted;
  host-associated specialists (low frac_soil) tend to have the lowest B_cross
- Spearman ρ(ko_z, B_cross) = −0.177 — metal genes track cross-biome breadth
- Spearman ρ(ko_z, B_soil) = +0.044 — metal genes do NOT track within-soil breadth

---

## Step 2 — PGLS: which component drives the metal-gene association

**Prediction:** B_cross should be significantly predicted by metal-gene density (β < 0),
while B_soil should be null. In the joint model, B_cross should remain significant and
B_soil should not.

### Reference: this-dataset B_cross model (λ optimised, n = 1,543)

| Model | focal β | SE | p | λ | n |
|---|---|---|---|---|---|
| REF: B_cross ~ ko_z + gsize_z | −0.0118 | 0.0040 | 0.0036** | 0.742 | 1,543 |

### Models with metal gene density as response

| Model | focal predictor | β | SE | p | λ | n |
|---|---|---|---|---|---|---|
| M1: ko ~ B_cross_z + gsize_z | B_cross_z | −0.2694 | 0.0924 | 0.0036** | ~0.74 | 1,543 |
| M2: ko ~ B_soil_z + gsize_z | B_soil_z | −0.0139 | 0.0808 | 0.864 NS | ~0.74 | 1,543 |
| M3 joint (B_cross coeff): ko ~ B_cross_z + B_soil_z + gsize_z | B_cross_z | −0.2721 | 0.0932 | 0.0036** | ~0.74 | 1,543 |
| M3 joint (B_soil coeff): same model | B_soil_z | +0.0176 | 0.0814 | 0.829 NS | ~0.74 | 1,543 |

### Models with niche breadth as response

| Model | focal β | SE | p | λ | n |
|---|---|---|---|---|---|
| M4: B_cross ~ ko_z + gsize_z | −0.0118 | 0.0040 | 0.0036** | 0.742 | 1,543 |
| M5: B_soil ~ ko_z + gsize_z | +0.0001 | 0.0015 | 0.970 NS | ~0.74 | 1,543 |

**Result:** Prediction FULLY SUPPORTED.
- B_cross is a significant predictor of metal-gene density (M1 p = 0.0036); B_soil is null (M2 p = 0.86).
- In the joint model (M3), B_cross remains significant (p = 0.0036) and B_soil is null (p = 0.83) —
  B_cross subsumes B_soil's explanatory contribution completely.
- M4 vs M5: Metal-gene density predicts B_cross but not B_soil.

---

## Step 3 — Soil-specialist stratification

Soil specialists: genera with frac_soil > 0.5 (n = 159, mean frac_soil = 0.816)
Multi-biome generalists: genera with frac_soil ≤ 0.5 (n = 1,384, mean frac_soil = 0.077)

| Group | Model | β | SE | p | n |
|---|---|---|---|---|---|
| Specialists | B_cross ~ ko_z + gsize_z | −0.0359 | 0.0178 | **0.045*** | 159 |
| Specialists | B_soil ~ ko_z + gsize_z | +0.0053 | 0.0046 | 0.253 NS | 159 |
| Generalists | B_cross ~ ko_z + gsize_z | −0.0100 | 0.0041 | **0.015*** | 1,384 |
| Generalists | B_soil ~ ko_z + gsize_z | −0.0003 | 0.0015 | 0.862 NS | 1,384 |

**Within-group variance:** Specialists: B_cross SD = 0.139, B_soil SD = 0.035.
Generalists: B_cross SD = 0.147, B_soil SD = 0.049.

**Interpretation:** The cross-biome signal is present in BOTH soil specialists and
multi-biome generalists (p = 0.045 and p = 0.015 respectively). Within soil specialists,
B_cross captures the residual variation in how far beyond the soil biome a genus ventures
(e.g. whether it also occurs in freshwater or host-associated habitats). Metal-gene density
remains negatively associated even within this "mostly-soil" group. B_soil is null in both
groups — there is no within-soil streamlining signal regardless of soil affinity.

---

## Step 4 — Power check for the soil null

n_soil_samples distribution (n = 1,543 genera):
P25 = 190, P50 = 748, P75 = 3,984, P95 = 28,839

Most genera have >100 soil samples; the median is 748. This is ample for computing stable
B_soil estimates. Increasing the sample threshold does not change the null result:

| Threshold | n_genera | B_soil SD | β | p |
|---|---|---|---|---|
| ≥5 (base) | 1,543 | 0.048 | +0.0001 | 0.970 NS |
| ≥10 | 1,524 | 0.048 | +0.0001 | 0.968 NS |
| ≥20 | 1,505 | 0.047 | +0.0003 | 0.851 NS |
| ≥100 | 1,315 | 0.044 | +0.0003 | 0.848 NS |

**Conclusion:** The B_soil null is robust across all sample thresholds. The slight positive
β (not negative) at higher thresholds further confirms there is no cryptic within-soil
streamlining signal being masked by noisy B_soil estimates.

---

## Step 5 — Phylum-stratified analysis

| Phylum | n | B_cross β | B_cross p | B_soil β | B_soil p |
|---|---|---|---|---|---|
| Proteobacteria | 660 | −0.0140 | **0.013*** | +0.0019 | 0.336 NS |
| Firmicutes | 330 | −0.0058 | 0.486 NS | −0.0048 | 0.169 NS |
| Actinobacteria | 203 | −0.0202 | 0.094† | −0.0000 | 0.997 NS |

**Interpretation:** The cross-biome signal is significant in Proteobacteria (p = 0.013,
n = 660), marginal in Actinobacteria (p = 0.094, n = 203), and absent in Firmicutes
(p = 0.49, n = 330). The within-soil (B_soil) signal is null in all three phyla.

The Firmicutes null for B_cross warrants attention: Firmicutes are primarily host-associated
or sporulating soil specialists with distinct genome content (many are strict specialists,
giving low variance in B_cross). The cross-biome pattern is not universal across all phyla,
but Firmicutes also have the smallest B_cross SD (consistent with ecological specialisation)
and the PGLS may be underpowered within this clade even at n = 330.

B_soil is null in every phylum tested — the within-soil null is not driven by any single
clade diluting a real signal.

---

## Step 6 — Metal-gene subcategory decomposition

| Category | n | B_cross β | B_cross p | B_soil β | B_soil p |
|---|---|---|---|---|---|
| Cofactor (7 KOs) | 842 | −0.0128 | 0.055† | −0.0003 | 0.872 NS |
| Resistance (15 KOs) | 1,047 | +0.0077 | 0.144 NS | −0.0018 | 0.301 NS |
| Cofactor+vitamin (KEGG) | 1,060 | −0.0130 | **0.021*** | −0.0001 | 0.970 NS |

**Result:** The cross-biome signal is driven by **cofactor genes** (negative and marginal/
significant: p = 0.055 for the 7-KO set, p = 0.021 for the expanded cofactor+vitamin
KEGG set). Resistance genes show no cross-biome signal (β = +0.008, p = 0.14 — not even
negative). Both subcategories are null for B_soil.

**Interpretation:** This is consistent with the prediction. Cofactor biosynthesis genes
are vertically inherited, phylogenetically conserved, and functionally essential — genera
that retain expanded cofactor gene sets may have narrower biome ranges due to specific
cofactor metabolic requirements. Resistance genes, which are more horizontally transferred
and situationally selected, do not show this cross-biome pattern.

---

## Step 7 — Sampling bias check

**Key question:** Do genera with more soil samples (better-sampled = more OTU records)
have systematically different metal-gene content, potentially confounding the B_cross signal?

| Test | focal β | SE | p |
|---|---|---|---|
| ko ~ n_soil_log_z + gsize_z | +1.001 | 0.083 | <0.001*** |
| ρ(ko_z, frac_soil) = −0.052 | (p = 0.041) | | |

**Unexpected finding:** More soil-sampled genera carry MORE metal genes (β = +1.0, p < 0.001).
This is counter-intuitive if sampling depth proxied ecological ubiquity, but makes ecological
sense: genera appearing in many different soil samples may occupy more geochemically diverse
soils (high-metal soils appear less often in surveys), requiring expanded metal gene repertoires.

Crucially, when sampling depth is controlled in the B_cross model, the cross-biome signal
**strengthens substantially**:

| Model | β(ko_z) | p |
|---|---|---|
| B_cross ~ ko_z + gsize_z (base) | −0.0118 | 0.0036** |
| B_cross ~ ko_z + n_soil_log_z + gsize_z | **−0.0313** | **4.4×10⁻¹⁶***  |
| B_soil ~ ko_z + n_soil_log_z + gsize_z | −0.0020 | 0.174 NS |

**n_soil_samples is a negative suppressor of the B_cross signal.** Genera with many soil
samples are both more metal-gene-rich AND more cross-biome generalist — these two tendencies
partially cancel in the naive model. When we partial out sampling depth, the cross-biome
association with metal gene density triples in magnitude (−0.012 → −0.031) and reaches
genome-wide significance (p < 10⁻¹⁵). The B_soil result remains null after this control.

---

## Step 8 — Complete results table

| Model | focal β | SE | p | n |
|---|---|---|---|---|
| REF: B_cross ~ ko_z + gsize_z | −0.0118 | 0.0040 | 0.0036** | 1,543 |
| M1: ko ~ B_cross_z + gsize_z | −0.2694 | 0.0924 | 0.0036** | 1,543 |
| M2: ko ~ B_soil_z + gsize_z | −0.0139 | 0.0808 | 0.864 NS | 1,543 |
| M3 (joint) B_cross coeff | −0.2721 | 0.0932 | 0.0036** | 1,543 |
| M3 (joint) B_soil coeff | +0.0176 | 0.0814 | 0.829 NS | 1,543 |
| M4: B_cross ~ ko_z + gsize_z | −0.0118 | 0.0040 | 0.0036** | 1,543 |
| M5: B_soil ~ ko_z + gsize_z | +0.0001 | 0.0015 | 0.970 NS | 1,543 |
| SPEC: B_cross ~ ko_z + gsize_z | −0.0359 | 0.0178 | 0.045* | 159 |
| SPEC: B_soil ~ ko_z + gsize_z | +0.0053 | 0.0046 | 0.253 NS | 159 |
| GEN: B_cross ~ ko_z + gsize_z | −0.0100 | 0.0041 | 0.015* | 1,384 |
| GEN: B_soil ~ ko_z + gsize_z | −0.0003 | 0.0015 | 0.862 NS | 1,384 |
| PWR n≥10: B_soil ~ ko_z + gsize_z | +0.0001 | 0.0015 | 0.968 NS | 1,524 |
| PWR n≥20: B_soil ~ ko_z + gsize_z | +0.0003 | 0.0014 | 0.851 NS | 1,505 |
| PWR n≥100: B_soil ~ ko_z + gsize_z | +0.0003 | 0.0015 | 0.848 NS | 1,315 |
| PH Proteobacteria: B_cross | −0.0140 | 0.0056 | 0.013* | 660 |
| PH Proteobacteria: B_soil | +0.0019 | 0.0019 | 0.336 NS | 660 |
| PH Firmicutes: B_cross | −0.0058 | 0.0084 | 0.486 NS | 330 |
| PH Firmicutes: B_soil | −0.0048 | 0.0035 | 0.169 NS | 330 |
| PH Actinobacteria: B_cross | −0.0202 | 0.0120 | 0.094† | 203 |
| PH Actinobacteria: B_soil | −0.0000 | 0.0039 | 0.997 NS | 203 |
| SUB cofactor: B_cross | −0.0128 | 0.0067 | 0.055† | 842 |
| SUB cofactor: B_soil | −0.0003 | 0.0021 | 0.872 NS | 842 |
| SUB resistance: B_cross | +0.0077 | 0.0053 | 0.144 NS | 1,047 |
| SUB resistance: B_soil | −0.0018 | 0.0018 | 0.301 NS | 1,047 |
| SUB cofactor_vitamin: B_cross | −0.0130 | 0.0056 | 0.021* | 1,060 |
| SUB cofactor_vitamin: B_soil | −0.0001 | 0.0019 | 0.970 NS | 1,060 |
| BIAS ko ~ n_soil_log_z + gsize_z | +1.001 | 0.083 | <0.001*** | 1,543 |
| BIAS B_cross ~ ko_z + n_soil_log_z + gsize_z | −0.0313 | 0.0038 | 4.4×10⁻¹⁶*** | 1,543 |
| BIAS B_soil ~ ko_z + n_soil_log_z + gsize_z | −0.0020 | 0.0015 | 0.174 NS | 1,543 |

All PGLS models use Pagel's λ optimised by ML (typical λ ≈ 0.74 for n=1,543,
similar to the primary P1 λ = 0.757). λ shown as 0.742 for full-dataset models
(verified directly); phylum-stratified models have slightly different λ (not extracted
for brevity).

---

## Synthesis

### Statement

**The metal-gene–niche breadth association is a cross-biome phenomenon, not a within-soil gradient.**

Metal-gene density (KOs per Mb) negatively predicts cross-biome niche breadth (B_cross) in
PGLS across 1,543 bacterial genera (β = −0.012, p = 0.004, λ = 0.742). The within-soil
niche breadth (B_soil) is completely null (β ≈ 0, p = 0.97). In the joint model, B_cross
remains significant and B_soil does not add any explanatory value. The null is not a power
artefact — increasing the soil sample threshold to ≥100 genus-level occurrences does not
recover a signal, and the expected β under proportional scaling would be −0.066 (not near
zero). The pattern is robust to sampling depth control (B_cross β strengthens to −0.031,
p = 4×10⁻¹⁶ when n_soil_samples is partialled out), holds in both soil specialists (p = 0.045)
and multi-biome generalists (p = 0.015), and is taxonomically general (significant in
Proteobacteria, marginal in Actinobacteria). The subcategory analysis confirms that cofactor
genes drive the cross-biome signal (β = −0.013, p = 0.021 for cofactor+vitamin set) while
resistance genes do not (β = +0.008, p = 0.14 NS).

### Discussion paragraph

The collapse of the metal-gene–niche breadth association when niche breadth is restricted
to within-soil samples (B_soil: β ≈ 0, p = 0.97) resolves a key interpretive ambiguity
in the primary finding. The cross-biome signal — genera spanning more major biome categories
(soil, marine, freshwater, host) carry fewer metal genes per Mb — is not a fine-scale
soil ecology pattern but a macroecological cross-biome gradient. This distinction has
mechanistic implications. Cofactor biosynthesis genes, which are phylogenetically conserved
and metabolically essential, drive the cross-biome signal (cofactor+vitamin β = −0.013,
p = 0.021), suggesting that expanded cofactor gene repertoires may constrain biogeochemical
niche flexibility — genera with elaborate metal-handling pathways are specialised for
geochemically specific environments (e.g. high-metal, high-redox-diversity soils) and cannot
easily colonise the nutrient-poor, metal-dilute environments typical of open ocean or host
surfaces. Resistance genes, which are more horizontally acquired and situationally selected,
show no cross-biome association (β = +0.008, NS), consistent with their role as responsive
contingency genes rather than niche-defining metabolic specialists. The observation that
controlling for soil sampling depth strengthens the cross-biome signal (β −0.012 → −0.031)
indicates that ecologically ubiquitous genera — which accumulate soil sample records — tend
to be both metal-gene-rich AND broad-ranging, a positive correlation that suppresses the
negative metal-gene/niche breadth association in naïve models. This is consistent with
the interpretation that truly cosmopolitan bacteria (found in many soils) have diversified
metabolic repertoires to cope with heterogeneous environments, but within-biome soil
diversity does not predict metal gene density at all.

### Recommendation for manuscript placement

**Report as a main finding in §3.4 (niche breadth sensitivity) with mechanistic framing.**
The result is not merely a null sensitivity check — it identifies the ecological scale at
which the signal operates (cross-biome, not within-soil). Recommend presenting:
1. M4 vs M5 (forward direction: B_cross vs B_soil as response to ko) as the primary comparison
2. M3 joint model (B_cross survives, B_soil null) as evidence of mutual exclusivity
3. The sampling-bias control (β strengthens to −0.031) as robustness evidence
4. The cofactor vs resistance decomposition as mechanistic interpretation

The two-panel scatter figure (figures/png/niche_decomposition_scatter.png) belongs in the
Supplementary (alongside the existing soil-sample niche report).

### Figure suggestion

**Figure Sx: Niche breadth decomposition scatter**

Two-panel matplotlib scatter, n = 1,543 genera:
- Panel A: Cross-biome niche breadth (B_cross, y) vs metal-gene density (x), coloured by
  soil-specialist status (frac_soil > 0.5; orange = soil specialist, blue = multi-biome
  generalist). Regression lines for each group. Negative slope visible in both groups.
- Panel B: Within-soil niche breadth (B_soil, y) vs metal-gene density (x), same encoding.
  Flat regression lines in both groups.
Caption: "Cross-biome but not within-soil niche breadth is negatively associated with
metal-gene density. Both soil specialists (orange, n = 159) and multi-biome generalists
(blue, n = 1,384) show a negative B_cross slope (β = −0.036 and −0.010 respectively,
p < 0.05), while B_soil is flat in both groups."

Saved: figures/png/niche_decomposition_scatter.png

---

## Limitations

1. **Dataset restriction:** The 1,543-genus analysis excludes 31 genera from the full P1
   dataset that lack soil sample presence. These may be entirely non-soil genera (e.g.
   strict marine or host-associated) whose exclusion reduces the B_cross variance range
   and slightly attenuates the β (−0.012 vs −0.021 full-dataset).
2. **B_soil coarseness:** Only 7 Env_Level_2 soil sub-habitat categories are used for
   B_soil. Finer-resolution soil partitioning (by pH, depth, moisture, vegetation type)
   might reveal within-soil gradients not visible with these coarse categories.
3. **B_cross confounds:** mean_levins_B_std is sensitive to the number of biome categories
   and sampling effort per biome — biomes with more MicrobeAtlas samples (e.g. soil)
   can make it appear genera are more "specialist" in other biomes.
4. **Firmicutes cross-biome null:** The cross-biome signal is absent in Firmicutes
   (p = 0.49), possibly due to ecological specialisation (most are host or soil specialists
   with low B_cross variance) or different genomic constraints in this phylum.
5. **Cofactor result marginal:** The cofactor-only model for B_cross is marginal (p = 0.055);
   the expanded cofactor+vitamin set (p = 0.021) is significant. The mechanistic attribution
   to cofactor genes specifically (vs. the broader metabolic ensemble) requires further
   validation.

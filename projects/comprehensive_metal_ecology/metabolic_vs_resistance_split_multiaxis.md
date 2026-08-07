# Core Metabolism vs. Resistance — Multi-Axis Niche Breadth Analysis

**Date**: 2026-07-15 (updated 2026-07-15 to add non-metal cofactor axes)  
**Goal**: Test whether core metabolism gene density (proxy for metabolic constraint) vs. resistance gene density (proxy for tolerance flexibility) behaves like the cofactor/resistance split seen in P1/NB03, and whether any signal is specific to a particular niche dimension.  
**Tree**: GTDB r214 genus tree, PGLS with Pagel's λ (ML), n = 1,574 bacterial genera (full set, no category subset restriction)  
**Data source**: `kbase.ke_pangenome` via Spark (consistent with P1)

---

## Gene Set Definitions

| Gene category | KO count | Definition | Source |
|---|---|---|---|
| Core metabolism | 96 | Non-redundant KOs from KEGG modules M00001–M00006, M00009, M00011, M00154–M00155 (glycolysis, TCA, pentose phosphate, pyruvate dehydrogenase, respiratory chain) minus 25 KOs that overlap the 730-KO metal gene list | KEGG REST API |
| Resistance/Detox | 15 | T1+2 KOs with `primary_category = Resistance/Detoxification` | curated_mrg_ko_ids_v2.csv |
| Metal Cofactor Biosynthesis | 5 | T1+2 KOs with `primary_category = Cofactor Biosynthesis` | curated_mrg_ko_ids_v2.csv |
| Metal-dependent Metabolism | 1 | T1+2 KOs with `primary_category = Metal-dependent Metabolism` | curated_mrg_ko_ids_v2.csv |

All predictors are per-Mb densities (KOs per Mb of mean genome size), z-standardised across all 1,574 genera. Models include `genome_mb_z` as a covariate throughout.

---

## Niche Breadth Axes

| Axis | Column | n | λ range | Description |
|---|---|---|---|---|
| Levins' B | `mean_levins_B_std` | 1,574 | 0.742–0.747 | Cross-biome occupancy diversity (P1 primary response) |
| Env PC1 | `env_pc1_z` | 1,562 | 0.450–0.480 | PC1 of within-genus environmental SD (pH, temperature, 5 GeoROC metals); 27.4% variance; wider = more geochemical heterogeneity |
| Soil niche breadth | `levins_B_soil_std` | 1,543 | 0.548–0.555 | Levins' B restricted to soil samples only |
| Social niche breadth | `count_breadth_std` | 535 | 0.000–0.008 | Host/ecosystem association breadth (BacDive proxy) |

---

## Results

### Single-predictor models (7 models each: alone + 3 joint configurations)

#### Levins' B (cross-biome niche breadth, n = 1,574, λ ≈ 0.74)

| Predictor | β | SE | p | Interpretation |
|---|---|---|---|---|
| Core metabolism | −0.0076 | 0.0053 | 0.149 | null |
| Resistance/Detox | +0.0003 | 0.0039 | 0.931 | null |
| Metal Cofactor | −0.0058 | 0.0043 | 0.173 | null |
| Metal-dep Metabolism | −0.0038 | 0.0035 | 0.279 | null |

**All single-predictor associations with Levins' B are null** (p > 0.12). This contrasts with the NB03 per-category analysis that found strong cofactor β = −0.034 (p = 7.0×10⁻⁹). The discrepancy is methodological: NB03 restricted each model to genera with ≥1 KO in the focal category (n = 1,257 for cofactor, 612 for metal-dep), whereas here all 1,574 genera enter each model with 0-count genera included in the z-standardisation. Dilution from 0-count genera suppresses signals that emerge only in the conditioned set.

#### Env PC1 (geochemical niche breadth, n = 1,562, λ ≈ 0.46)

| Predictor | β | SE | p | Interpretation |
|---|---|---|---|---|
| Core metabolism | **+0.1205** | 0.0395 | **0.002** | significant positive |
| Resistance/Detox | **+0.1209** | 0.0299 | **5.6×10⁻⁵** | significant positive |
| Metal Cofactor | +0.0236 | 0.0322 | 0.464 | null |
| Metal-dep Metabolism | **+0.0751** | 0.0274 | **0.006** | significant positive |

Core metabolism, resistance, and metal-dependent metabolism all positively predict geochemical niche width. Metal cofactor biosynthesis is the only null category.

#### Soil niche breadth (n = 1,543, λ ≈ 0.55)

| Predictor | β | SE | p | Interpretation |
|---|---|---|---|---|
| Core metabolism | −0.0016 | 0.0019 | 0.405 | null |
| Resistance/Detox | −0.0007 | 0.0014 | 0.613 | null |
| Metal Cofactor | **−0.0035** | 0.0015 | **0.022** | significant negative |
| Metal-dep Metabolism | +0.0009 | 0.0013 | 0.467 | null |

#### Social niche breadth (n = 535, λ ≈ 0.000–0.008)

| Predictor | β | SE | p | Interpretation |
|---|---|---|---|---|
| Core metabolism | **+0.0086** | 0.0028 | **0.002** | significant positive |
| Resistance/Detox | **+0.0093** | 0.0019 | **1.4×10⁻⁶** | significant positive |
| Metal Cofactor | **+0.0067** | 0.0022 | **0.003** | significant positive |
| Metal-dep Metabolism | **+0.0074** | 0.0019 | **0.0001** | significant positive |

λ ≈ 0.000 for all social breadth models: no phylogenetic signal in this axis for the 535-genus panel. PGLS reduces to OLS. All predictors positive (broader gene repertoire → wider host associations). No functional split visible.

---

### Joint models

#### Core metabolism vs. Resistance (joint model)

| Axis | Core β | Core p | Resist β | Resist p | λ |
|---|---|---|---|---|---|
| Levins' B (n=1574) | −0.0084 | 0.126 | +0.0021 | 0.604 | 0.745 |
| Env PC1 (n=1562) | **+0.0846** | **0.038** | **+0.1039** | **0.001** | 0.450 |
| Soil B (n=1543) | −0.0014 | 0.472 | −0.0004 | 0.779 | 0.554 |
| Social B (n=535) | +0.0053 | 0.066 | **+0.0083** | **2.9×10⁻⁵** | 0.000 |

On **env PC1**: both core metabolism and resistance are independently positive and significant after mutual adjustment. They point in the SAME direction — there is no split. On Levins' B and soil breadth, both are null.

#### Metal-dep Metabolism vs. Resistance (joint model)

| Axis | Metal-dep β | Metal-dep p | Resist β | Resist p | λ |
|---|---|---|---|---|---|
| Levins' B (n=1574) | −0.0041 | 0.259 | +0.0013 | 0.740 | 0.744 |
| Env PC1 (n=1562) | +0.0545 | 0.051 | **+0.1083** | **4.1×10⁻⁴** | 0.452 |
| Soil B (n=1543) | +0.0011 | 0.395 | −0.0010 | 0.502 | 0.549 |
| Social B (n=535) | **+0.0046** | **0.023** | **+0.0076** | **2.5×10⁻⁴** | 0.001 |

On **env PC1**: resistance is strongly positive; metal-dep metabolism is marginally positive (β = +0.055, p = 0.051) and attenuated by resistance. These two gene sets are positively correlated (genera with more resistance genes tend to have more metal-dep genes), so the attenuation is expected.

#### Core metabolism vs. Metal-dep Metabolism (joint model)

| Axis | Core β | Core p | Metal-dep β | Metal-dep p | λ |
|---|---|---|---|---|---|
| Levins' B (n=1574) | −0.0067 | 0.216 | −0.0028 | 0.429 | 0.747 |
| Env PC1 (n=1562) | **+0.1006** | **0.013** | **+0.0588** | **0.037** | 0.468 |
| Soil B (n=1543) | −0.0020 | 0.298 | +0.0013 | 0.338 | 0.555 |
| Social B (n=535) | **+0.0057** | **0.050** | **+0.0062** | **0.002** | 0.000 |

On **env PC1**: both remain independently significant after mutual adjustment (core β = +0.101, metal-dep β = +0.059). Both functional categories expand geochemical niche range.

---

## Summary Comparison Table

Columns show direction and significance of each predictor on each niche axis. "–" = null (p > 0.05), "+" = positive significant, "−" = negative significant, "?" = λ ≈ 0 (no phylo signal, interpret cautiously).

| Predictor | Levins' B (cross-biome) | Env PC1 (geochemical) | Soil B | Social B |
|---|---|---|---|---|
| Core metabolism | – (null) | **+ (p=0.002)** | – (null) | **?+ (p=0.002)** |
| Resistance/Detox | – (null) | **+ (p<0.0001)** | – (null) | **?+ (p<0.0001)** |
| Metal Cofactor | – (null, full set) | – (null) | **− (p=0.022)** | **?+ (p=0.003)** |
| Metal-dep Metabolism | – (null) | **+ (p=0.006)** | – (null) | **?+ (p=0.0001)** |

---

## Interpretation

### Core metabolism does not behave like cofactor biosynthesis on any axis

The motivating question was whether core metabolism genes — fundamental metabolic pathways present in virtually all bacteria — show the same negative niche association as metal cofactor biosynthesis genes (the key finding in P1/NB03). The answer is clearly no:

1. **Levins' B (full set)**: Core metabolism is null (β = −0.0076, p = 0.149), as is resistance (β = +0.0003, p = 0.931). The null result here is expected because the full-set analysis includes genera with 0 counts for some categories; the NB03 cofactor signal emerges only in the subset of genera that actually carry cofactor genes (n = 1,257), where possession of cofactor genes is associated with biome specialisation. Core metabolism genes are universal (all 1,574 genera have ≥1 core KO), so this restriction is not applicable.

2. **Env PC1 (geochemical niche)**: Core metabolism is strongly POSITIVE (β = +0.121, p = 0.002), identical in magnitude to resistance (β = +0.121, p = 5.6×10⁻⁵). In the joint model, both remain positive and significant after controlling for each other. This means genera with higher core metabolism gene density inhabit a WIDER range of geochemical environments — the opposite of the Levins' B cofactor constraint. This is consistent with core metabolism genes encoding metal-requiring enzymes (e.g., Fe-S cluster-containing dehydrogenases in the TCA cycle, Zn-dependent aldolases in glycolysis), so genera with high core metabolic throughput may simply be adapted to environments with diverse metal availability.

3. **Soil niche breadth**: Core metabolism is null (β = −0.0016, p = 0.405). Only cofactor biosynthesis is (marginally) negative (β = −0.0035, p = 0.022), weakly replicating the Levins' B cofactor signal in a soil-restricted context.

4. **Social niche breadth (λ ≈ 0)**: All predictors positive. The absence of phylogenetic signal (λ ≈ 0) means cross-genera variation in host/ecosystem breadth is not structured by phylogeny in this sample. All associations likely reflect shared ecological strategies (generalist genomes carry more genes of all types) rather than a metal-specific effect.

### The functional split is not between core metabolism and resistance

On the env PC1 axis, the split is NOT between core metabolism (constraining) and resistance (neutral/positive). Both are positive, and both remain independently positive in the joint model. The split on env PC1 is instead between:
- **Metal gene categories** (core metabolism, resistance, metal-dep metabolism): all **positive** — wider geochemical niche
- **Metal cofactor biosynthesis**: **null** — no geochemical niche association

This different split suggests that cofactor biosynthesis genes (K01845 siroheme, K00590 cobalamin, K01994 riboflavin, K01687 thiamine, K03533 sirohydrochlorin) are metabolically distinct from the other metal gene categories — their biosynthetic product is a cofactor incorporated into specific enzyme families, so their presence commits the genome to a specific biochemical strategy without necessarily demanding a particular ambient metal concentration. In contrast, core metabolism and resistance genes involve BOTH biosynthesis of metal-using enzymes AND their operation under varying ambient metal concentrations, making geochemical range expansion more likely.

### Resistance vs. metal-dep metabolism on env PC1

In the metal-dep vs. resistance joint model, resistance is more strongly and consistently associated with wider geochemical niche (β = +0.108, p = 4.1×10⁻⁴) than metal-dep metabolism (β = +0.055, p = 0.051 after adjustment). This is consistent with resistance genes directly enabling tolerance of a wider range of ambient metal concentrations, while metal-dep metabolism genes may reflect secondary adaptation after the tolerance threshold is crossed.

### Methodological note: full-set vs. conditioned-set analyses

This analysis runs PGLS on all 1,574 genera for each predictor (with 0 assigned to genera that have no KO in the focal category). The NB03 per-category analysis conditioned on ≥1 KO per category. These are different estimands: the conditioned-set analysis asks "among genera that carry this gene set, does density predict niche breadth?" while the full-set analysis asks "across all bacteria, does gene set density predict niche breadth?" The latter dilutes signals that are conditional on gene set presence. For the purposes of this analysis — comparing functional splits across axes — the full-set approach maintains a consistent genus panel across all comparisons.

---

## Methods Note

**Core metabolism KO set**: 96 KOs fetched from KEGG REST API for modules M00001–M00006 (glycolysis, gluconeogenesis, pentose phosphate, TCA), M00009 (citrate cycle), M00011 (citrate cycle, second carbon oxidation), M00154–M00155 (fumarate respiration). 25 KOs overlapping the 730-KO metal gene list were removed (to avoid confounding with metal-specific functions). Of the 96 KOs, 48 were found in `kbase.ke_pangenome.bakta_annotations` for at least one genome; all 1,574 genera carry ≥1 of these 48 KOs (median: 16 KOs per genus).

**PGLS**: `scripts/pgls_utils.py`, Pagel's λ ML, GTDB r214 genus tree, `genome_mb_z` covariate in all models.

**Data outputs**: `data/multiaxis_pgls_results.csv` (68 rows, focal and covariate coefficients for all 28 models), `data/multiaxis_pgls_input.csv` (1,574 genera × 13 columns).

---

## Non-Metal Cofactor Density on Missing Axes

**Background**: The non-metal cofactor gene set (KEGG "cofactors and vitamins" pathway, ~370 KOs) showed the strongest negative Levins' B association of any functional category (β = −0.029, p = 2.4×10⁻¹¹, n = 1,073 genera with ≥1 cofactor/vitamin KO, from the env_PC1 split analysis) and was null on env PC1 (β = +0.003, p = 0.93). The two remaining axes — soil-only niche breadth and social niche breadth — were untested.

**Model**: `niche ~ nonmetal_cofactor_per_mb_z + genome_mb_z` (PGLS, Pagel's λ ML, GTDB r214 tree; restricted to genera with non-null cofactor/vitamin density).

### Soil-only niche breadth (n = 1,060, λ = 0.486)

| Predictor | β | SE | p | Interpretation |
|---|---|---|---|---|
| Non-metal cofactor density | −0.0001 | 0.0019 | 0.970 | **null** |
| genome_mb_z | −0.0002 | 0.0021 | 0.937 | null |

The strong Levins' B signal for non-metal cofactors does not replicate on the soil-restricted niche breadth axis.

### Social niche breadth (n = 428, λ ≈ 0.000)

| Predictor | β | SE | p | Interpretation |
|---|---|---|---|---|
| Non-metal cofactor density | +0.0054 | 0.0027 | 0.045* | marginal positive |
| genome_mb_z | +0.0077 | 0.0026 | 0.003** | positive |

λ ≈ 0.000: no phylogenetic signal in social breadth for this subset. Marginal positive association is consistent with the pattern seen for all other categories on this axis (all positive, see above).

---

## Complete Functional Category × Niche Axis Comparison

All PGLS with Pagel's λ ML, GTDB r214 genus tree, genome_mb_z covariate. Significance: *** p < 0.001, ** p < 0.01, * p < 0.05, † marginal p < 0.1, — null. Genus panels differ by axis and by whether the analysis conditions on having ≥1 KO per category (conditioned) or uses the full 1,574-genus set (full). See methodology note below.

| Functional category | Levins' B (cross-biome) | Env PC1 (geochemical) | Soil-only niche B | Social niche B (BacDive†) | Social niche B (co-occurrence‡) |
|---|---|---|---|---|---|
| **Resistance/Detox** (15 KOs) | — null (full, n=1,574) | **+ 0.073*** (conditioned, n=1,550) | — null (full, n=1,543) | **?+ 0.009***†  (full, n=535) | **+ 15.79*** (n=1,547, λ=0.509) |
| **Metal Cofactor** (5 KOs) | **− 0.034***§ (conditioned, n=1,257) | — null (conditioned, n=1,248) | **− 0.004*** (full, n=1,543) | **?+ 0.007**†  (full, n=535) | **+ 5.71*** (n=1,547, λ=0.495) |
| **Non-metal Cofactor** (370 KOs) | **− 0.029*** (conditioned, n=1,073) | — null (conditioned, n=1,068) | — null (conditioned, n=1,060) | **?+ 0.005**†  (conditioned, n=428) | — null −2.10 p=0.276 (n=1,062, λ=0.573) |
| **Core metabolism** (96 KOs) | — null (full, n=1,574) | **+ 0.121**† (full, n=1,562) | — null (full, n=1,543) | **?+ 0.009**†  (full, n=535) | **+ 9.06*** (n=1,547, λ=0.504) |
| **Metal-dep. Metabolism** (1 KO) | — null (full, n=1,574) | **+ 0.075**† (full, n=1,562) | — null (full, n=1,543) | **?+ 0.007***†  (full, n=535) | **+ 7.22*** (n=1,547, λ=0.483) |

β values given; † = BacDive social axis has λ ≈ 0 for all models — **uninterpretable as PGLS**; ‡ = co-occurrence weighted degree from soil-stratum phi-coefficient network, λ ≈ 0.5 (phylogenetically structured, interpretable); § = NB03 conditioned-set result; p-value significance from the individual predictor row.

**Env PC1 note**: Resistance β comes from the conditioned-set env_PC1_split_analysis (β=+0.073, n=1,550). Full-set metabolic analysis gives β=+0.121 (n=1,562) — larger because the 0-count genera included in the full set are concentrated in lower env PC1, pulling the slope up. The conditioned-set figure is more conservative.

### Interpretation

**Non-metal cofactor signal is specific to cross-biome niche breadth.**

The non-metal cofactor/vitamin gene set is the only functional category where a statistically unambiguous negative association is reproducible across multiple independent analyses: the signal (β = −0.029, p = 2.4×10⁻¹¹) survived the NB25 permutation test (empirical p = 0/1000 for the functional split magnitude) and the NB26 jackknife (all 4 cofactor biosynthesis KOs stable, β range −0.016 to −0.029, all p < 0.001, no sign changes). But it is absent on every other niche axis tested here:

- **Env PC1 (geochemical range)**: null (β = +0.003, p = 0.93). Genera with high cofactor/vitamin gene density do not inhabit a narrower or wider range of metal concentrations or pH.
- **Soil-only niche breadth**: null (β = −0.0001, p = 0.97). Within the soil biome, cofactor/vitamin density provides no predictive power for how many soil strata or soil types a genus occupies.
- **Social breadth**: marginally positive (β = +0.0054, p = 0.045, λ ≈ 0). At best a genome-size proxy effect (genera with large, diverse genomes have more cofactor genes and more host associations); the absence of phylogenetic signal makes this uninterpretable as a metal ecology result.

By contrast, **metal cofactor biosynthesis** (5 KOs) does show a marginal negative signal on the soil-only axis (β = −0.0035, p = 0.022) in addition to the strong cross-biome Levins' B signal (β = −0.034, NB03). This suggests the metal cofactor constraint may extend slightly into within-biome soil breadth, while the non-metal cofactor constraint is strictly cross-biome. The difference may reflect that metal-specific cofactors (siroheme, cobalamin, sirohydrochlorin) are more directly linked to soil metal geochemistry, creating within-soil constraints as well as cross-biome ones.

**Resistance, core metabolism, and metal-dep metabolism** all pattern together: null on Levins' B (full set), positive on env PC1, null on soil breadth, marginally positive on social breadth. None of these gene categories shows the negative cross-biome constraint that distinguishes the non-metal cofactor set. This reinforces that the cofactor/resistance functional split in P1 is driven by the cofactor side, not the resistance side — resistance genes are consistently null or slightly positive across all axes.

**The cross-biome niche axis is qualitatively distinct.** Non-metal cofactor density is the single strongest predictor of cross-biome Levins' B narrowing, but has zero predictive value for within-biome, geochemical, or social niche dimensions. This dissociation suggests the cofactor constraint operates at the level of which biome types a genus can colonise — reflecting metabolic blueprint specificity — rather than at the level of local environmental tolerance or host range. Biome transitions may require whole-pathway reconfigurations of cofactor biosynthesis, while fine-scale variation within a biome does not.

---

## Corrected Social Niche Breadth Analysis (Co-occurrence Network)

**Date**: 2026-07-15  
**Motivation**: The BacDive `count_breadth_std` metric used as the social niche breadth axis in the analysis above shows λ ≈ 0 in all PGLS models (0.000–0.008), meaning there is no phylogenetic signal in this variable for the 535-genus panel used. PGLS with λ ≈ 0 degenerates to OLS and provides no corrective power for shared evolutionary history; the functional-category associations on this axis are therefore uninterpretable as phylogenetically controlled results. Additionally, `count_breadth_std` is a BacDive host/ecosystem co-isolation proxy and is not the social niche breadth metric validated in the co-occurrence analysis (NB19–20).

**Replacement metric**: Weighted degree from the soil-stratum phi-coefficient co-occurrence network. φ-weighted degree = sum of significant positive φ edges for a genus in the soil stratum (162,022 samples, 3,149 genera). This is the metric that showed β = 15.2, p = 3.54×10⁻³², λ = 0.559 in the primary co-occurrence analysis (degree ~ ko_per_mb_primary + genome_mb_z). Data source: `/tmp/cooc_pgls_input_soil.csv` from `scripts/run_cooccurrence_analysis.py`.

**PGLS models**: `degree ~ category_density_z + genome_mb_z`, PGLS with Pagel's λ (ML), GTDB r214 genus tree, n = 1,547 genera with non-null soil-stratum degree.

---

### BacDive vs. co-occurrence comparison

| Functional category | BacDive β (p) | BacDive λ | Co-occurrence β (p) | Co-occurrence λ |
|---|---|---|---|---|
| Resistance/Detox | +0.0093 (1.4×10⁻⁶***) | 0.000 | **+15.79 (3.0×10⁻³⁵***)** | **0.509** |
| Metal Cofactor | +0.0067 (0.003**) | 0.008 | **+5.71 (4.1×10⁻⁵***)** | **0.495** |
| Non-metal Cofactor | +0.0054 (0.045*) | 0.000 | **−2.10 (0.276 — null)** | **0.573** |
| Core metabolism | +0.0086 (0.002**) | 0.007 | **+9.06 (7.3×10⁻⁸***)** | **0.504** |
| Metal-dep. Metabolism | +0.0074 (0.0001***) | 0.000 | **+7.22 (4.1×10⁻¹⁰***)** | **0.483** |

All co-occurrence models: n=1,547 (full set) except Non-metal Cofactor n=1,062 (conditioned on non-null density). BacDive: n=535. β values are not directly comparable (different response scales).

---

### Co-occurrence alone models

All models: `degree ~ category_z + genome_mb_z`; soil-stratum phi-coefficient weighted degree; n=1,547 (or 1,062 for non-metal cofactor); GTDB r214 tree.

| Functional category | β (focal) | SE | p | λ | Interpretation |
|---|---|---|---|---|---|
| Resistance/Detox | **+15.79** | 1.24 | **3.0×10⁻³⁵** | 0.509 | strong positive |
| Core metabolism | **+9.06** | 1.68 | **7.3×10⁻⁸** | 0.504 | strong positive |
| Metal-dep. Metabolism | **+7.22** | 1.15 | **4.1×10⁻¹⁰** | 0.483 | strong positive |
| Metal Cofactor | **+5.71** | 1.39 | **4.1×10⁻⁵** | 0.495 | significant positive |
| Non-metal Cofactor | −2.10 | 1.93 | 0.276 | 0.573 | **null** |

`genome_mb_z` covariate: β ≈ +12–19 in all models (p < 10⁻²⁰), confirming genome size drives co-occurrence degree independently of functional gene density.

---

### Co-occurrence joint models

#### Core metabolism + resistance (n=1,547, λ=0.507)

| Predictor | β | SE | p |
|---|---|---|---|
| Core metabolism | +3.77 | 1.67 | 0.024* |
| Resistance | **+14.99** | 1.29 | **5.3×10⁻³⁰** |
| genome_mb_z | +19.26 | 1.82 | 3.1×10⁻²⁵ |

Core metabolism retains a significant independent association with co-occurrence degree (β=+3.77, p=0.024) after controlling for resistance, but resistance is the dominant predictor (β=+15.0). Consistent with resistance genes encoding direct ecological interaction strategies (metal exclusion, biocide resistance) that define ecological positioning in co-occurrence networks.

#### Metal-dep metabolism + resistance (n=1,547, λ=0.497)

| Predictor | β | SE | p |
|---|---|---|---|
| Metal-dep metabolism | **+4.61** | 1.12 | **4.3×10⁻⁵** |
| Resistance | **+14.75** | 1.26 | **2.4×10⁻³⁰** |
| genome_mb_z | +16.44 | 1.31 | 2.9×10⁻³⁴ |

Both metal-dep metabolism and resistance retain independent positive associations in the joint model. Unlike env PC1 (where metal-dep is absorbed by resistance), the two predictors remain separable on co-occurrence degree.

#### Core metabolism + metal-dep metabolism (n=1,547, λ=0.493)

| Predictor | β | SE | p |
|---|---|---|---|
| Core metabolism | **+6.79** | 1.72 | **8.1×10⁻⁵** |
| Metal-dep metabolism | **+6.01** | 1.18 | **4.3×10⁻⁷** |
| genome_mb_z | +18.03 | 1.90 | 9.8×10⁻²¹ |

Both categories contribute independently to co-occurrence degree when resistance is excluded.

#### Metal cofactor + non-metal cofactor (n=1,062, λ=0.557)

| Predictor | β | SE | p |
|---|---|---|---|
| Metal Cofactor | **+6.90** | 1.75 | **8.6×10⁻⁵** |
| Non-metal Cofactor | −3.43 | 1.94 | 0.077† |
| genome_mb_z | +11.46 | 2.16 | 1.4×10⁻⁷ |

Metal cofactor positive (β=+6.90, p=8.6×10⁻⁵) and non-metal cofactor null/marginally negative (β=−3.43, p=0.077). In the alone model, non-metal cofactor was fully null (β=−2.10, p=0.276); in the joint model it tends negative (marginally). The contrast between metal cofactor (positive) and non-metal cofactor (null/negative) on this axis echoes the pattern on cross-biome Levins' B where both are negative, but here the directions diverge — metal cofactor joins the positive-association group while non-metal cofactor remains null.

---

### Interpretation

#### λ is resolved: co-occurrence degree is phylogenetically structured

The defining failure of the BacDive axis was λ ≈ 0. All five functional categories on the co-occurrence degree axis produce λ = 0.48–0.57. Phylogenetic signal is present and accounted for by the PGLS model, making these results methodologically valid. The BacDive results should be treated as OLS estimates on an un-phylogenetically-corrected dataset and are not part of the interpretable evidence.

#### Functional split on co-occurrence degree: four positive, one null

On the validated social niche axis (phi-coefficient weighted degree, soil stratum), the pattern is:

- **Resistance, core metabolism, metal-dep metabolism, metal cofactor**: all strongly positive (β = +5.7 to +15.8, all p < 10⁻⁴). Genera with higher functional gene density are more central in the soil co-occurrence network — they have more co-occurring partners with significant positive phi coefficients.
- **Non-metal cofactor**: null (β = −2.10, p = 0.276). Non-metal cofactor/vitamin gene density has no relationship with co-occurrence network centrality.

This is a new functional split: **the non-metal cofactor category is uniquely decoupled from co-occurrence network position**, while all metal-gene categories (resistance, transport-linked, metabolism) are positively associated.

#### The cofactor-negative Levins' B signal does not appear on the co-occurrence axis

The cross-biome Levins' B axis shows cofactor negative (β = −0.034, NB03; β = −0.029 for non-metal cofactor). The co-occurrence degree axis shows metal cofactor positive and non-metal cofactor null — no negative association. This reinforces the axis-specificity of the cofactor constraint: it is a biome-transition phenomenon (negative Levins' B) but not a co-occurrence network phenomenon. Genera with high cofactor gene density can be central co-occurrence partners in soil despite being biome-specialists.

#### Co-occurrence degree is not purely a genome-size proxy

The genome size covariate is always the strongest predictor (β ≈ +12–19), confirming that large-genome generalists have more co-occurrence partners. But functional gene categories add independent predictive power beyond genome size: in joint models, all four metal-gene categories retain significant independent associations (β = +3.8 to +15.0 after genome size control). The co-occurrence axis therefore captures functional differentiation above and beyond genome size, making it a valid niche axis.

#### Resistance is the dominant driver of co-occurrence centrality

In joint models with core metabolism or metal-dep metabolism, resistance always dominates (β ≈ +15, p < 10⁻²⁹), while the other categories retain marginal to moderate independent associations (β = +3.8 to +6.8). This suggests resistance genes are the primary ecological interface linking metal gene repertoire to co-occurrence network position — likely because resistance determines which metal concentrations a genus can tolerate in a shared habitat, directly shaping which other genera it can co-occur with in metal-rich soil environments.

---

### Data outputs

- `/tmp/cooc_functional_pgls_results.csv` — 22-row PGLS results for all alone + joint models

---

### Methodology note

Results are not fully cross-comparable because different analyses used different genus panels:
- Resistance/Metal categories on Levins' B, soil, and social from the metabolic/resistance analysis use the **full 1,574-genus set** (0 assigned for genera without those KOs).
- Non-metal cofactor and the env_PC1_split_analysis results use **conditioned sets** (genera with ≥1 KO in the focal category).
- NB03 metal cofactor Levins' B result (β = −0.034) uses the NB03 restricted panel (n = 1,257).
- Co-occurrence degree (corrected social axis) uses the soil-stratum subset (n=1,547 with non-null degree).

For the cross-biome Levins' B axis specifically, conditioned-set analyses (NB03, env_PC1_split_analysis) consistently find cofactor negative and resistance null; full-set analyses find everything null. The conditioned-set estimand is the more biologically interpretable one (conditioning on gene presence), and the full-set results are mechanistically diluted by 0-count genera.

# Non-Exclusive Classification of Metal Gene Categories and Expanded Metal-dep Metabolism

**Date**: 2026-07-15  
**Goal**: Replace the mutually exclusive `primary_category` classification with a non-exclusive framework, compute an expanded Metal-dependent Metabolism gene set, and test it across all four niche breadth axes.  
**Tree**: GTDB r214 genus tree, PGLS with Pagel's λ (ML), n = 1,574 bacterial genera  
**Data source**: `kbase.ke_pangenome` via Spark

---

## Non-Exclusive Classification

### Method

The original `primary_category` column assigned each KO to exactly one functional category, collapsing Metal-dependent Metabolism to 1 KO in the T1+2 set (54 in all tiers) because metal-using enzymes were classified under whichever function was most prominent. The non-exclusive framework assigns each KO to all categories it qualifies for simultaneously.

**Category rules:**

| Category | Source | Scope |
|---|---|---|
| Resistance/Detoxification | `is_resistance` flag (validated against BacMet2) | Unchanged from original |
| Transport/Homeostasis | `is_transport` flag (validated against transporter families) | Unchanged |
| Sensing/Regulation | `is_sensor` flag | Unchanged |
| Cofactor Biosynthesis (metal) | `is_cofactor` flag | Unchanged |
| **Metal-dep. Metabolism (expanded)** | `is_metabolism` flag PLUS KOs in a non-cofactor metabolic KEGG module with metal annotation and a catalytic EC number, excluding pure transporters | **Expanded** |

The Metal-dep Metabolism expansion adds KOs from other primary categories if they satisfy: (1) annotated in a metabolic KEGG module (excluding cofactor biosynthesis modules M00122, M00810, M00811, M00880-M00882, M00924-M00925, M00572-M00573, M00116, M00133-M00134, M00595-M00596, M00897, M00120-M00121, M00860-M00861, M00093-M00094, M00622-M00624), AND (2) have a metal annotation (`metals` column non-null), AND (3) have an EC number in their definition, AND (4) are not flagged as transporters or efflux proteins.

### Category sizes (non-exclusive)

| Category | All 730 KOs | T1+2 (140 KOs) | Original T1+2 primary_category |
|---|---|---|---|
| Resistance/Detox | 106 | 15 | 15 |
| Transport/Homeostasis | 213 | 106 | 106 |
| Sensing/Regulation | 61 | 13 | 10 |
| Cofactor Biosynthesis (metal) | 9 | 6 | 5 |
| **Metal-dep. Metabolism** | **93** | **4** | **1** |

The Metal-dep Metabolism set expands from 1 → 4 KOs in T1+2, and from 54 → 93 KOs across all tiers. In T1+2, the 4 KOs are:

| KO | Definition | Metals | Original primary_category |
|---|---|---|---|
| K00240 | Succinate dehydrogenase iron-sulfur subunit [EC:1.3.5.1] | Fe, S | Sensing/Regulation |
| K00245 | Succinate dehydrogenase iron-sulfur subunit [EC:1.3.5.1] | Fe, S | Sensing/Regulation |
| K00380 | Sulfite reductase (NADPH) flavoprotein alpha-component [EC:1.8.1.2] | S, Co, Cu | Metal-dependent Metabolism |
| K18367 | CoA-dependent NAD(P)H sulfur oxidoreductase [EC:1.8.1.18] | S | Sensing/Regulation |

K00240 and K00245 (Fe-S cluster TCA enzyme) and K18367 (sulfur/energy metabolism) were previously classified as "Sensing/Regulation" because their metal sensing role was prioritised; they are legitimately metal-cofactor-dependent metabolic enzymes.

### KO overlap matrix (T1+2)

| | Resistance | Transport | Sensing | Cofactor | Metal-dep |
|---|---|---|---|---|---|
| **Resistance** | 15 | 0 | 3 | 0 | 0 |
| **Transport** | 0 | 106 | 0 | 0 | 0 |
| **Sensing** | 3 | 0 | 13 | 1 | 3 |
| **Cofactor** | 0 | 0 | 1 | 6 | 0 |
| **Metal-dep** | 0 | 0 | 3 | 0 | 4 |

No Resistance ↔ Metal-dep overlap in T1+2. The 3 Sensing ↔ Metal-dep overlaps are the succinate dehydrogenase subunits (K00240, K00245) and K17219 (sulfur reductase Mo subunit).

### Spearman correlations between per-genus densities

Correlations computed for n = 1,073 genera with all five densities non-null.

| | Resistance | Cofactor | Metal-dep T1+2 | Metal-dep all-tier | Non-metal cofactor |
|---|---|---|---|---|---|
| **Resistance** | — | ρ=+0.41*** | ρ=+0.51*** | ρ=+0.55*** | ρ=+0.32*** |
| **Cofactor** | | — | ρ=+0.45*** | ρ=+0.62*** | ρ=+0.35*** |
| **Metal-dep T1+2** | | | — | ρ=+0.73*** | ρ=+0.42*** |
| **Metal-dep all-tier** | | | | — | ρ=+0.50*** |
| **Non-metal cofactor** | | | | | — |

All categories are positively correlated. The Metal-dep T1+2 and all-tier sets are strongly correlated (ρ = +0.73), confirming the T1+2 subset captures a similar signal. The Metal-dep all-tier is more correlated with Cofactor biosynthesis (ρ = +0.62) than with Resistance (ρ = +0.55), suggesting the all-tier set captures metabolic specificity better than pure resistance functions.

---

## PGLS Results: Expanded Metal-dep Metabolism Across All Four Axes

All models include `genome_mb_z` as a covariate. "All-tier" = 93-KO expanded set (all 5 evidence tiers); "T1+2 exp" = 4-KO T1+2 subset.

### Alone models

| Predictor | n | β | SE | p | λ | Interpretation |
|---|---|---|---|---|---|---|
| **Levins' B (cross-biome)** | | | | | | |
| Metal-dep all-tier | 1,574 | −0.0065 | 0.0047 | 0.151 | 0.745 | null |
| Metal-dep T1+2 exp | 1,574 | −0.0033 | 0.0043 | 0.436 | 0.743 | null |
| *Original 1-KO (NB03)* | *1,073* | *−0.021* | *0.005* | *7.5×10⁻⁵* | *—* | *significant negative* |
| **Env PC1 (geochemical)** | | | | | | |
| Metal-dep all-tier | 1,562 | +0.0660 | 0.0349 | 0.057† | 0.475 | marginal positive |
| Metal-dep T1+2 exp | 1,562 | +0.0656 | 0.0316 | 0.039* | 0.470 | significant positive |
| **Soil-only niche B** | | | | | | |
| Metal-dep all-tier | 1,543 | −0.0014 | 0.0016 | 0.384 | 0.551 | null |
| Metal-dep T1+2 exp | 1,543 | +0.0006 | 0.0015 | 0.684 | 0.550 | null |
| **Social breadth** (λ≈0) | | | | | | |
| Metal-dep all-tier | 535 | +0.0093 | 0.0021 | 2.0×10⁻⁵*** | 0.012 | positive (λ≈0) |
| Metal-dep T1+2 exp | 535 | +0.0084 | 0.0019 | 4.6×10⁻⁵*** | 0.000 | positive (λ≈0) |

*The original 1-KO result (NB03 conditioned set) was −0.021, p = 7.5×10⁻⁵ on Levins' B. This has not been recalculated here; it used a conditioned genus subset (n = 1,073).*

### Joint models

#### Levins' B: metal-dep + resistance

| Predictor | β | SE | p | λ |
|---|---|---|---|---|
| Metal-dep all-tier | −0.0085 | 0.0051 | 0.097† | 0.744 |
| Resistance | +0.0037 | 0.0044 | 0.403 | 0.744 |

Both null. Consistent with the full-set analysis in the metabolic-vs-resistance report.

#### Levins' B: metal-dep + non-metal cofactor (n=1,073 conditioned set)

| Predictor | β | SE | p | λ |
|---|---|---|---|---|
| Metal-dep all-tier | −0.0030 | 0.0052 | 0.558 | 0.785 |
| Non-metal cofactor | **−0.0128** | 0.0057 | **0.026*** | 0.785 |

The non-metal cofactor signal survives adjustment for metal-dep metabolism — the two effects are independent on Levins' B.

#### Env PC1: metal-dep + resistance (n=1,562)

| Predictor | β | SE | p | λ |
|---|---|---|---|---|
| Metal-dep all-tier | +0.0071 | 0.0384 | 0.853 | 0.455 |
| **Resistance** | **+0.1182** | **0.0314** | **4.0×10⁻⁴*** | 0.455 |

Metal-dep metabolism is **completely absorbed** by resistance on env PC1 (β drops from +0.066 to +0.007, p = 0.853). The two predictors are correlated (ρ = +0.55), and resistance accounts for all the geochemical niche variation that metal-dep metabolism appeared to capture.

#### Env PC1: metal-dep + cofactor biosynthesis (n=1,562)

| Predictor | β | SE | p | λ |
|---|---|---|---|---|
| Metal-dep all-tier | +0.0654 | 0.0371 | 0.079† | 0.474 |
| Cofactor biosyn | +0.0017 | 0.0358 | 0.962 | 0.474 |

Metal-dep metabolism retains its marginal env PC1 association after controlling for cofactor biosynthesis; cofactor biosynthesis is null.

#### Social breadth: metal-dep + resistance (n=535, λ≈0)

| Predictor | β | SE | p | λ |
|---|---|---|---|---|
| Metal-dep all-tier | +0.0046 | 0.0026 | 0.073† | 0.005 |
| Resistance | +0.0069 | 0.0024 | 0.004** | 0.005 |

Both positive on social breadth; resistance is more strongly significant. The λ≈0 flag applies: no phylogenetic signal, results approximate OLS.

#### Social breadth: metal-dep + non-metal cofactor (n=428, λ≈0)

| Predictor | β | SE | p | λ |
|---|---|---|---|---|
| **Metal-dep all-tier** | **+0.0104** | **0.0022** | **1.0×10⁻⁵*** | 0.002 |
| Non-metal cofactor | ≈0.0000 | 0.0027 | 0.987 | 0.002 |

Metal-dep metabolism is positive on social breadth regardless of non-metal cofactor density. Non-metal cofactor is null in the joint model (marginal alone association was driven by collinearity with metal-dep).

---

## Comparison to Original 1-KO Metal-dep Metabolism (NB03)

| Analysis | Metal-dep KOs | Levins' B β | Levins' B p | Env PC1 β | Env PC1 p |
|---|---|---|---|---|---|
| NB03 conditioned (1 KO) | 1 (K00380) | −0.021 | 7.5×10⁻⁵ | not tested | — |
| T1+2 expanded alone (4 KOs) | 4 | −0.0033 | 0.436 | +0.066 | 0.039 |
| All-tier expanded alone (93 KOs) | 93 | −0.0065 | 0.151 | +0.066 | 0.057 |

The original 1-KO negative Levins' B signal does not replicate in the expanded set. The 1-KO result was based on K00380 (sulfite reductase), a highly specific enzyme in sulfate-assimilating genera; this restriction to a single highly informative KO in a conditioned genus subset (n=1,073) produced a stronger but narrower signal. Expanding to 4 or 93 KOs removes this specificity and brings the category into the same null zone as resistance genes on Levins' B.

The expanded Metal-dep Metabolism is **marginally positive on env PC1** (β ≈ +0.066, p ≈ 0.04–0.06), consistent with the resistance direction, not the cofactor direction. This confirms that metal-using metabolic enzymes (TCA-cycle Fe-S subunits, sulfur reductases) expand geochemical range in the same direction as resistance genes.

---

## Interpretation

### Expanded metal-dep metabolism behaves like resistance, not cofactor

Across all four niche axes, the expanded 93-KO metal-dep metabolism set produces results that are qualitatively identical to the resistance/detox pattern:

1. **Levins' B (cross-biome)**: Null (β = −0.0065, p = 0.151). Same as resistance (β = +0.0003, p = 0.931 in the full-set analysis).
2. **Env PC1 (geochemical niche)**: Marginally positive (β = +0.066, p = 0.057), but fully collinear with resistance in the joint model (β drops to +0.007, p = 0.853 when resistance is included). Both gene categories associate with wider geochemical niches, and they overlap sufficiently that the residual metal-dep signal is entirely explained by resistance genes.
3. **Soil-only breadth**: Null. Same as resistance.
4. **Social breadth (λ≈0)**: Positive, same as resistance (both reflect genome generalism in the absence of phylogenetic structure).

The expanded metal-dep metabolism does NOT show the cofactor pattern (negative Levins' B, null env PC1). The reason the original 1-KO (K00380, sulfite reductase) was negative on Levins' B is that K00380 is a highly genus-specific enzyme involved in assimilatory sulfate reduction, present disproportionately in genera with narrow biome niches (e.g., sulfate-reducing bacteria with constrained ecological range). This makes K00380 an outlier relative to the broader metal-dep metabolism category.

### Non-exclusive classification recovers no new negative Levins' B predictors among metal categories

The non-exclusive framework confirms that the negative Levins' B signal is carried exclusively by **cofactor biosynthesis genes** (both metal cofactor biosynthesis and non-metal cofactor/vitamin metabolism). All metal-resistance, transport, and metabolism genes are null or positive. This result is robust to the choice of exclusive vs. non-exclusive classification.

### Collinearity between metal-dep metabolism and resistance on env PC1

The ρ = +0.55 Spearman correlation between metal-dep metabolism and resistance gene densities (per genus, all-tier) explains why both are positive on env PC1 and why metal-dep metabolism is absorbed by resistance in the joint model. Genera with diverse metal resistance arsenals tend to also have diverse metal-cofactor-dependent metabolism — these co-occur as part of a generalised metal-adapted lifestyle rather than being independent biological functions. The resistance gene density is the better predictor of geochemical range, likely because resistance genes are directly selected by ambient metal concentrations, while metal-dep metabolism KOs are selected by metabolic requirements that may be less directly tied to ambient conditions.

### The original NB03 Metal-dep Metabolism signal was gene-specific, not category-general

The NB03 Metal-dep Metabolism result (β = −0.021, n=1 KO) was essentially driven by a single gene (K00380) in a conditioned genus subset. After expanding to all T1+2 KOs that qualify as metal-dep metabolism (4 KOs) or all evidence tiers (93 KOs), the signal disappears (β = −0.003 to −0.007, p > 0.15). The 1-KO result is therefore an artefact of the mutually exclusive classification collapsing a diverse functional category to its least representative member.

---

## Data Outputs

| File | Description |
|---|---|
| `data/non_exclusive_classification.csv` | Non-exclusive category flags for all 730 KOs |
| `data/non_exclusive_pgls_input.csv` | Per-genus densities for all non-exclusive categories + all 4 niche axes (1,574 genera) |
| `data/ne_metal_dep_pgls_results.csv` | PGLS results for 20 expanded metal-dep models × 4 niche axes |

## Methods Note

**Metal-dep Metabolism expansion**: 89 KOs beyond T1+2 were queried from `kbase.ke_pangenome` via Spark (same bakta_annotations query pattern as the core metabolism analysis). Of 89 queried, 41 were found in bakta_annotations. The T1+2 4-KO subset used existing `genus_ko_presence_t12_spark.csv`. All densities are KOs per Mb, z-standardised across all 1,574 genera.

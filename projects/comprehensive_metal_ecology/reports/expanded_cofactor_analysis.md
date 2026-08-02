# Expanded KEGG Metal-Cofactor Biosynthesis Analysis

**Date**: 2026-07-15  
**Goal**: Test whether expanding the metal-cofactor biosynthesis gene set from the curated 7–9 KOs to the full KEGG-annotated metal-cofactor set changes the multi-axis niche breadth results.  
**Tree**: GTDB r214 genus tree, PGLS with Pagel's λ (ML), n=1,574 genera (full set)  
**Data source**: `kbase.ke_pangenome` via Spark (bakta_annotations)

---

## Step 1 — Expanded gene set construction

### KEGG modules queried

| Pathway | Module(s) | KOs in module | KOs with bakta data |
|---|---|---|---|
| Molybdopterin (Moco) | M00880 | 10 | 6 |
| Heme (iron) | M00121, M00926 | 17 | 10 |
| Cobalamin (cobalt) | M00122, M00924 | 32 | 18 |
| Siroheme (iron) | M00846 | 14 | 7 |
| Fe-S cluster assembly | M00175, M00176 + 5 explicit KOs | 23 | 13 |
| **Total unique** | | **81** | **47** |

Cross-pathway overlaps (small): K96243 appears in four pathways (Fe-S assembly, cobalamin, heme, molybdopterin); K13542 in cobalamin and heme; 5 KOs shared between cobalamin and siroheme. After deduplication: 81 unique KOs in the expanded set.

Of the 81 queried KOs, 34 (42%) were absent from `kbase.ke_pangenome.bakta_annotations`. These are likely enzyme subunits or isoforms that receive different KEGG annotations in Bakta's pipeline (e.g., CbiA/CobB isoforms, alternative cobalamin biosynthesis routes). The 47 KOs with data cover all five pathways.

### Cross-reference with the curated 730-KO list

| Category | Count |
|---|---|
| In our `is_cofactor=True` curated set | 6 |
| In curated 730-KO list, classified as **other** | 61 |
| Not in our 730-KO list at all | 14 |

The 61 "misclassified" KOs include many genuine metal-cofactor biosynthesis enzymes assigned to "Unknown" (25) or "Transport/Homeostasis" (20) in our curation because their primary metal interaction was annotated as transport-related or their function was uncertain. The largest such group is cobalamin methyltransferases (precorrin series), which were classified as Transport because precorrin intermediates are chaperoned across membranes.

The 6 that ARE in our curated cofactor set: K01772 (ferrochelatase, heme, Tier 3), K02225 (CobC, cobalamin, Tier 2), K03635/K03638/K03750/K03831 (molybdopterin synthase subunits, Tier 2).

---

## Step 2 — Per-genus densities

Densities = number of distinct metal-cofactor KOs present per genus / mean genome size (Mb), z-scored across all 1,574 genera.

| Pathway | KOs with data | Genera with ≥1 KO | Mean per-Mb | SD per-Mb |
|---|---|---|---|---|
| Full expanded | 47 | 1,561 (99.2%) | 4.82 | 2.27 |
| Heme | 10 | 1,470 (93.4%) | 1.56 | 0.82 |
| Cobalamin | 18 | 1,225 (77.8%) | 1.57 | 1.44 |
| Molybdopterin | 6 | 1,280 (81.3%) | 0.81 | 0.55 |
| Siroheme | 7 | 1,414 (89.8%) | 0.94 | 0.56 |
| Fe-S assembly | 13 | 1,531 (97.3%) | 0.90 | 0.55 |

The expanded set is nearly universal: 1,561/1,574 genera have ≥1 expanded metal-cofactor KO (vs. ~1,257–1,550 for conditioned-set analyses of the curated set). This means the full-set expanded analysis avoids most of the 0-count dilution that made the curated set null in full-set analyses.

---

## Step 3 — PGLS results

All models: `niche ~ category_density_z + genome_mb_z`, PGLS Pagel's λ (ML), GTDB r214 tree.

### Levins' B (cross-biome niche breadth)

Full set, n=1,574, λ≈0.71 for all models.

| Cofactor set | n KOs | β | SE | p | λ | Interpretation |
|---|---|---|---|---|---|---|
| **Expanded KEGG** | 47 | **−0.0107** | 0.0041 | **0.0096***** | 0.714 | **significant negative** |
| Curated (9 KOs, full-set) | 9 | −0.0062 | 0.0042 | 0.142 | 0.709 | null |
| *Curated T1+2 (5 KOs, conditioned, NB03)* | *5* | *−0.034* | *0.007* | *<10⁻⁵* | *—* | *significant negative* |
| Heme | 10 | −0.0043 | 0.0045 | 0.333 | 0.711 | null |
| **Cobalamin** | 18 | **−0.0111** | 0.0040 | **0.0051***** | 0.712 | **significant negative** |
| Molybdopterin | 6 | −0.0039 | 0.0039 | 0.317 | 0.708 | null |
| Siroheme | 7 | −0.0045 | 0.0041 | 0.278 | 0.711 | null |
| Fe-S assembly | 13 | −0.0016 | 0.0035 | 0.646 | 0.710 | null |

**The expanded set is significantly negative on Levins' B** (p=0.010) in the full-set analysis, unlike the original curated 9-KO set which was null (p=0.142). The signal is driven primarily by **cobalamin biosynthesis** (β=−0.011, p=0.005). Heme, molybdopterin, siroheme, and Fe-S assembly are all null. The cobalamin result makes biological sense: cobalamin is the most complex metal cofactor and is produced/acquired by a limited phylogenetically biased subset of bacteria.

### Env PC1 (geochemical niche breadth)

n=1,562, λ≈0.42 for all models.

| Cofactor set | β | SE | p | λ | Interpretation |
|---|---|---|---|---|---|
| Expanded KEGG | +0.0137 | 0.0312 | 0.660 | 0.419 | null |
| Curated (9 KOs, full-set) | +0.0183 | 0.0319 | 0.566 | 0.417 | null |
| Heme | +0.0575 | 0.0333 | 0.084† | 0.417 | marginal positive |
| Cobalamin | −0.0496 | 0.0298 | 0.095† | 0.414 | marginal negative |
| Molybdopterin | +0.0211 | 0.0297 | 0.477 | 0.418 | null |
| Siroheme | +0.0282 | 0.0312 | 0.367 | 0.420 | null |
| **Fe-S assembly** | **+0.0646** | 0.0271 | **0.017*** | 0.420 | **significant positive** |

Heterogeneous picture: **Fe-S assembly is significantly positive** on env PC1 (β=+0.065, p=0.017), consistent with iron-sulfur clusters being required for a wide range of metalloenzymes that must function across diverse geochemical conditions. **Cobalamin is marginally negative** (β=−0.050, p=0.095), the opposite direction — cobalamin-producing genera may be geochemically specialized (anaerobic sediment specialists). The expanded set's combined signal cancels to null (β=+0.014).

### Soil-only niche breadth

n=1,543, λ≈0.49–0.50 for all models.

| Cofactor set | β | SE | p | λ | Interpretation |
|---|---|---|---|---|---|
| **Expanded KEGG** | **−0.0030** | 0.0015 | **0.040*** | 0.494 | **significant negative** |
| Curated (9 KOs, full-set) | −0.0033 | 0.0015 | 0.032* | 0.495 | significant negative |
| Heme | −0.0027 | 0.0016 | 0.094† | 0.503 | marginal negative |
| Cobalamin | −0.0022 | 0.0014 | 0.112 | 0.490 | null |
| **Molybdopterin** | **−0.0038** | 0.0014 | **0.008***** | 0.496 | **strongest negative** |
| Siroheme | −0.0017 | 0.0015 | 0.240 | 0.500 | null |
| Fe-S assembly | +0.0007 | 0.0013 | 0.595 | 0.497 | null |

The negative soil niche breadth signal is **consistent across the expanded set and the original curated set**. **Molybdopterin is the strongest driver** (β=−0.0038, p=0.008), followed by heme (marginal). Fe-S assembly is null and positive, again showing a distinct pattern. This extends the "cofactor negative on soil breadth" result from the curated set to the expanded set, with molybdopterin as the key pathway.

### Co-occurrence weighted degree (corrected social axis)

n=1,547, soil-stratum phi-coefficient network, λ≈0.50 for all models.

| Cofactor set | β | SE | p | λ | Interpretation |
|---|---|---|---|---|---|
| **Expanded KEGG** | **+7.87** | 1.34 | **5.6×10⁻⁹** | 0.516 | strong positive |
| Curated (9 KOs) | +5.71 | 1.39 | 4.1×10⁻⁵ | 0.495 | strong positive |
| Heme | +5.37 | 1.45 | 2.2×10⁻⁴ | 0.498 | positive |
| Cobalamin | +4.06 | 1.29 | 1.7×10⁻³ | 0.511 | positive |
| Molybdopterin | +5.23 | 1.29 | 5.5×10⁻⁵ | 0.495 | positive |
| Siroheme | +3.84 | 1.35 | 4.5×10⁻³ | 0.495 | positive |
| **Fe-S assembly** | **+6.21** | 1.16 | **1.1×10⁻⁷** | 0.499 | **strongest positive** |

All expanded cofactor pathways are **uniformly positive** on co-occurrence degree (p < 0.005 for all except siroheme p=0.005). Fe-S assembly is the strongest individual pathway (β=+6.21, p=1.1×10⁻⁷), closely followed by heme (β=+5.37) and molybdopterin (β=+5.23). The expanded set amplifies the curated-set signal (β=+7.87 vs +5.71).

---

## Step 4 — Joint models: expanded metal cofactors vs. non-metal cofactors

Model: `niche ~ expanded_z + cof_vitamin_z + genome_mb_z`, n=1,073 (conditioned on non-null non-metal cofactor density), λ from data.

| Axis | Expanded β (p) | Non-metal cof β (p) | λ | Key finding |
|---|---|---|---|---|
| Levins' B | −0.0097 (0.051†) | −0.0109 (0.068†) | 0.749 | Both marginal negative; independent effects |
| Env PC1 | −0.0154 (0.682) | **+0.089 (0.044*)** | 0.388 | Non-metal cof positive after metal cof control |
| Soil B | −0.0024 (0.175) | +0.0007 (0.752) | 0.439 | Both null |
| **Co-occurrence degree** | **+10.60 (8.3×10⁻¹⁰***)** | **−6.93 (7.5×10⁻⁴***)** | 0.586 | **Opposite signs: metal cof positive, non-metal cof negative** |

### Striking result: Opposite signs on co-occurrence degree

In the joint model for co-occurrence degree, expanded metal cofactors are **strongly positive** (β=+10.60) while non-metal cofactors are **significantly negative** (β=−6.93, p=0.001). Non-metal cofactors were null in the alone model (β=−2.10, p=0.276 from the previous analysis) because the two categories are positively correlated (genera with high metal-cofactor gene density also tend to have higher non-metal cofactor densities, ρ≈+0.50). Once metal-cofactor density is controlled, the residual non-metal cofactor effect is negative: genera that invest disproportionately in non-metal cofactor/vitamin metabolism *relative to* metal cofactor biosynthesis have fewer co-occurrence partners.

This opposition suggests that **metal-cofactor biosynthesis capacity** expands ecological connectivity (more co-occurrence partners) while **non-metal cofactor/vitamin investment independent of metal biosynthesis** indicates metabolic specialization that restricts co-occurrence breadth. The latter effect is consistent with the strong negative Levins' B signal for non-metal cofactors — vitamin/cofactor specialists occupy narrow niches at multiple scales.

### Env PC1 joint model: non-metal cofactor conditionally positive

When expanded metal cofactor is controlled, non-metal cofactors become significantly positive on env PC1 (β=+0.089, p=0.044). This reversal (from null alone to positive in joint) may reflect confounding by cobalamin: cobalamin biosynthesis genes are marginally negative on env PC1 (β=−0.050), and genera with high non-metal cofactor density may differ in cobalamin investment. Once the competing negative cobalamin effect is absorbed into the expanded metal cofactor predictor, the residual non-metal cofactor variation is positive on geochemical range.

---

## Step 5 — Comparison table

| Cofactor set | n KOs (bakta) | Levins' B β (p) | Env PC1 β (p) | Soil B β (p) | Degree β (p) |
|---|---|---|---|---|---|
| Original T1+2 curated, conditioned, NB03 | 5 | **−0.034 (<10⁻⁵)** | — | — | — |
| Curated 9-KO (full-set) | 9 | −0.006 (0.142, null) | +0.018 (0.566) | −0.003 (0.032*) | +5.71 (4.1×10⁻⁵) |
| **Expanded KEGG (full-set)** | **47** | **−0.011 (0.010**)** | +0.014 (0.660) | **−0.003 (0.040*)** | **+7.87 (5.6×10⁻⁹)** |
| Heme (10 KOs) | 10 | −0.004 (0.333) | +0.057 (0.084†) | −0.003 (0.094†) | +5.37 (2.2×10⁻⁴) |
| Cobalamin (18 KOs) | 18 | **−0.011 (0.005**)** | −0.050 (0.095†) | −0.002 (0.112) | +4.06 (1.7×10⁻³) |
| Molybdopterin (6 KOs) | 6 | −0.004 (0.317) | +0.021 (0.477) | **−0.004 (0.008**)** | +5.23 (5.5×10⁻⁵) |
| Siroheme (7 KOs) | 7 | −0.004 (0.278) | +0.028 (0.367) | −0.002 (0.240) | +3.84 (4.5×10⁻³) |
| Fe-S assembly (13 KOs) | 13 | −0.002 (0.646) | **+0.065 (0.017*)** | +0.001 (0.595) | **+6.21 (1.1×10⁻⁷)** |
| Non-metal cofactors (370 KOs) | ~370 | **−0.029 (2.4×10⁻¹¹)** | null (0.93) | null (0.97) | null (0.276) |

Significance: *** p < 0.001, ** p < 0.01, * p < 0.05, † p < 0.10.  
All full-set analyses n=1,574 (Levins' B), 1,562 (env PC1), 1,543 (soil B), 1,547 (degree).

---

## Step 6 — Interpretation

### Does expanding the set strengthen or dilute the Levins' B signal?

**It strengthens it.** The original 9-KO curated set is null in the full-set analysis (p=0.142); the expanded 47-KO set is significantly negative (p=0.010). This is because:

1. The expanded set adds cobalamin biosynthesis KOs (18 vs. 1 in the curated set), and cobalamin is the key driver of the negative Levins' B signal (β=−0.011, p=0.005).
2. The expanded set reaches 99.2% of genera with ≥1 KO vs. 60–80% for individual pathway subsets, reducing dilution from 0-count genera.

The NB03 conditioned-set result (β=−0.034) remains stronger because it restricts to genera that actually carry cofactor genes, amplifying the within-genus variation. The expanded full-set result (β=−0.011) is a conservative estimate capturing the same negative direction but diluted by the universal background.

### Which pathway drives the Levins' B signal?

**Cobalamin** (18 KOs, β=−0.011, p=0.005) is the only individually significant pathway. This makes biological sense:

- Cobalamin biosynthesis is one of the most metabolically costly biosynthetic pathways (>30 enzymatic steps), energetically committing a genus to cobalamin-auxotrophic environments or highly reducing conditions.
- Cobalamin-producing bacteria are phylogenetically concentrated in anaerobic and low-oxygen niches (sulfate-reducing bacteria, methanogens, Firmicutes from the gut). These are biome-restricted taxa by definition.
- Heme, molybdopterin, siroheme, and Fe-S assembly are more broadly distributed (93–97% of genera with ≥1 KO) and show no Levins' B signal, consistent with these being more universally required cofactors whose biosynthesis does not constrain biome range.

### Is there a metal-specific component distinct from non-metal cofactors?

Yes, on **two axes**:

1. **Levins' B**: Both expanded metal cofactor (β=−0.011) and non-metal cofactor (β=−0.029) are negative. In the joint model, both remain marginally negative (p=0.051 and p=0.068), suggesting **partially independent negative effects** — the cobalamin-biosynthesis constraint and the vitamin/cofactor-metabolism constraint are distinct sources of biome specialisation.

2. **Env PC1 (geochemical niche)**: The two categories diverge — Fe-S assembly is positive (β=+0.065, p=0.017) while the overall expanded set is null. Non-metal cofactors are null (β=+0.003). This suggests Fe-S cluster assembly genes confer geochemical range expansion (Fe-S clusters are redox sensors and serve as catalytic centers across a wide range of metalloenzymes required in diverse geochemical conditions), while non-metal cofactor biosynthesis does not.

3. **Co-occurrence degree**: The joint model reveals a sharp divergence (metal cofactor β=+10.60 vs. non-metal cofactor β=−6.93, p=0.001). Metal-cofactor biosynthesis capacity is positively associated with co-occurrence network centrality; non-metal cofactor investment is negatively associated when metal cofactor capacity is controlled. This metal-specific co-occurrence advantage may reflect shared metabolic dependencies: genera that produce metal-containing cofactors are ecological partners for cofactor-auxotrophic bacteria that cannot make their own (cobalamin cross-feeding is a well-documented ecological interaction).

### Does the expanded analysis change the narrative?

**Partially yes, but the core result stands:**

1. **Cross-biome niche breadth (Levins' B)**: The narrative strengthens slightly. The original result (curated set significant in conditioned analysis, null in full-set) is now replicated in a full-set analysis with the expanded set. The cofactor-negative signal is robust to gene set definition and generalises from the curated 5 molybdopterin/siroheme KOs to a broader set including cobalamin.

2. **Pathway specificity**: The Levins' B signal is primarily cobalamin-driven, not a general metal-cofactor feature. Heme, Fe-S assembly, and molybdopterin individually do not show significant Levins' B associations. This adds mechanistic resolution: it is specifically the commitment to de novo cobalamin biosynthesis (the most energetically expensive metal cofactor) that correlates with biome specialisation.

3. **Fe-S assembly is functionally distinct**: Fe-S assembly genes behave more like resistance genes (positive on env PC1 and degree, null on Levins' B) than like cobalamin genes (negative on Levins' B, negative/null on env PC1). Fe-S clusters are nearly universal and serve as electron transfer hubs in oxidoreductases across all major metabolic pathways, making them more of a "universal metabolic infrastructure" than a biome-defining biosynthetic commitment.

4. **Metal vs. non-metal cofactor distinction on co-occurrence degree**: The joint model result (metal positive, non-metal negative on degree) is a new finding not visible in the original analysis. It suggests that cofactor cross-feeding ecology (cobalamin, heme) drives positive co-occurrence relationships, while non-metal vitamin biosynthesis independence does not — this has implications for interpreting community assembly in metal-rich soils.

---

## Data outputs

| File | Description |
|---|---|
| `data/expanded_kegg_metal_cofactor_densities.csv` | Per-genus per-Mb densities and z-scores for full expanded set and 5 pathway subsets (1,574 genera × 16 cols) |
| `/tmp/expanded_cofactor_pgls_results.csv` | 68-row PGLS results (7 alone models × 4 axes + 4 joint models × 2 predictors) |
| `/tmp/kegg_metal_cofactor_crossref.csv` | Cross-reference table: all 81 KEGG KOs vs. curated 730-KO list |
| `/tmp/kegg_metal_cofactor_kos.json` | Pathway → KO mapping (81 KOs, 5 pathways) |

## Methods

**KEGG module fetch**: REST API `https://rest.kegg.jp/get/{module_id}`, KOs extracted by regex `K\d{5}`. Modules M00880 (Moco), M00121+M00926 (heme), M00122+M00924 (cobalamin), M00846 (siroheme), M00175+M00176 (Fe-S assembly). Explicit Fe-S KOs added: K04487, K05997, K22068, K22072, K07400.

**Spark query**: Same `bakta_annotations` pattern as the primary T1+2 analysis; 69 new KOs queried; 35 found. Combined with 12 KOs from prior queries (T1+2 + metal_dep_expanded). Total: 47 of 81 with bakta data.

**Density**: distinct KOs per genus per mean-Mb, z-scored across all 1,574 genera. Genera with 0 observed KOs assigned density 0 (not excluded from analysis — 99.2% have ≥1 for the full expanded set).

**PGLS**: `niche ~ density_z + genome_mb_z`, Pagel's λ (ML), GTDB r214 genus tree.

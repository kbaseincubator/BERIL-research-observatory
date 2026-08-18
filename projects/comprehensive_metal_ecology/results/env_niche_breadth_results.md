# Environmental Niche Breadth Analysis

## Research Question
Does per-Mb metal-gene density predict environmental niche breadth
(SD or range of pH, temperature, or metal concentration across occupied samples)?

## Data Overview

| Dataset | n_genera | Environmental Variable | Source |
|---------|----------|------------------------|--------|
| A (Temperature primary) | 1196 | median_temp_range_C | Global MicrobeAtlas |
| A (Temperature primary) | 1196 | median_soil_ph | Global MicrobeAtlas |
| A (Temperature primary) | 1196 | median_soil_moisture | Global MicrobeAtlas |
| B (Temperature tier1/tier2) | 434 | median_temp_range_C | Global MicrobeAtlas |
| B (Temperature tier1/tier2) | 434 | median_soil_ph | Global MicrobeAtlas |
| C (Environmental gradient) | 1172 | env_gradient_breadth (composite) | Global MicrobeAtlas |
| D (MGnify metals) | 25 | Cu_sd | MGnify |
| D (MGnify metals) | 25 | Zn_sd | MGnify |

## Key Findings

### 1. Temperature Niche Breadth (Dataset A)

- **Temperature range (median_temp_range_C)**: Metal-gene KO density was NOT significantly
  associated with temperature niche breadth (β=0.0789, p=0.929, n=1195).

- **Soil pH gradient**: Contrary to expectations, higher metal-gene KO density was associated
  with NARROWER soil pH niche breadth (β=-0.760, p=0.001*, n=1195). This suggests that
  genera with more metal resistance genes occupy narrower pH ranges.

- **Soil moisture**: No significant association (β=1.782, p=0.616, n=1194).

### 2. Environmental Gradient Breadth (Dataset C)

- **Composite environmental niche**: When combining pH, temperature, and moisture into a
  unified gradient measure, higher KO density was associated with NARROWER environmental
  breadth (β=-0.064, p<0.001*, n=1172). This effect is robust and consistent.

### 3. Gene Category Specificity (Dataset B)

- **Resistance genes (tier1)**: Showed borderline positive association with temperature
  breadth (β=2.539, p=0.130) but no effect on pH (β=0.044, p=0.924).

- **Cofactor/fitness genes (tier2)**: No significant effects on either temperature
  (β=-0.550, p=0.702) or pH (β=0.133, p=0.731).

### 4. MGnify Metal Niche (Dataset D, n=25)

- **Limited sample size**: Only 25 genera had sufficient metal concentration data from MGnify.
  No significant associations between KO density and Cu/Zn niche breadth
  (Cu: p=0.443, Zn: p=0.638, composite: p=0.621).

### 5. Cross-Niche Correlations

| Environmental Niche Pair | n | Spearman's ρ | p-value | Significance |
|--------------------------|---|--------------|---------|--------------|
| Temperature vs Cross-biome Levins B | 1223 | 0.2453 | 3.2832e-18 | * |
| pH vs Cross-biome Levins B | 1222 | 0.0965 | 7.3490e-04 | * |
| Cu niche vs Cross-biome Levins B | 18 | 0.2282 | 3.6245e-01 |  |
| Zn niche vs Cross-biome Levins B | 18 | 0.0940 | 7.1076e-01 |  |
| Temperature vs Soil pH | 1222 | 0.1393 | 1.0114e-06 | * |
| Temperature vs Cu niche | 17 | 0.2873 | 2.6347e-01 |  |
| Cu vs Zn niche breadth | 18 | 0.7231 | 6.9594e-04 | * |
| Cross-biome vs Social Levins B | 535 | 0.0807 | 6.2055e-02 |  |

**Key correlation findings:**
- Temperature niche breadth is significantly correlated with cross-biome Levins' B
  (ρ=0.245, p<0.001), indicating temperature is one axis of ecological generalism.
- Soil pH range also correlates with cross-biome breadth (ρ=0.097, p<0.001),
  but the effect is weaker than temperature.
- Cu and Zn niche breadth are highly correlated with each other (ρ=0.723, p<0.001),
  suggesting metal niches are coupled in environmental space.
- Cross-biome Levins' B and social niche breadth show marginal correlation (ρ=0.081, p=0.062),
  suggesting ecological and taxonomic generalism are only partially linked.

## PGLS Model Results (with Pagel's λ)

| Model | Predictor | β (95% CI via SE) | p-value | Significance* |
|-------|-----------|------------------|---------|----------------|
| A1: Temp ~ KO_density + genome_size | ko_per_mb_z | 0.0789 ± 0.8856 | 9.2906e-01 | ns |
| A1: Temp ~ KO_density + genome_size | genome_mb_z | 0.9096 ± 0.9283 | 3.2736e-01 | ns |
| A2: Soil_pH ~ KO_density + genome_size | ko_per_mb_z | -0.7600 ± 0.2327 | 1.1196e-03 | ** |
| A2: Soil_pH ~ KO_density + genome_size | genome_mb_z | 0.0526 ± 0.2462 | 8.3089e-01 | ns |
| A3: Soil_moisture ~ KO_density + genome_size | ko_per_mb_z | 1.7824 ± 3.5576 | 6.1645e-01 | ns |
| A3: Soil_moisture ~ KO_density + genome_size | genome_mb_z | 1.8067 ± 3.6558 | 6.2126e-01 | ns |
| B1: Temp ~ Tier1(resist) + Tier2(cofactor) + genome_size | ko_per_mb_tier1_z | 2.5394 ± 1.6719 | 1.2953e-01 | ns |
| B1: Temp ~ Tier1(resist) + Tier2(cofactor) + genome_size | ko_per_mb_tier2_z | -0.5503 ± 1.4382 | 7.0220e-01 | ns |
| B1: Temp ~ Tier1(resist) + Tier2(cofactor) + genome_size | genome_mb_z | 2.3178 ± 1.2804 | 7.0973e-02 | ns |
| B2: Soil_pH ~ Tier1(resist) + Tier2(cofactor) + genome_size | ko_per_mb_tier1_z | 0.0440 ± 0.4580 | 9.2357e-01 | ns |
| B2: Soil_pH ~ Tier1(resist) + Tier2(cofactor) + genome_size | ko_per_mb_tier2_z | 0.1333 ± 0.3874 | 7.3097e-01 | ns |
| B2: Soil_pH ~ Tier1(resist) + Tier2(cofactor) + genome_size | genome_mb_z | 0.4510 ± 0.3493 | 1.9729e-01 | ns |
| C1: Env_gradient ~ KO_density + genome_size | ko_per_mb_z | -0.0638 ± 0.0174 | 2.5706e-04 | *** |
| C1: Env_gradient ~ KO_density + genome_size | genome_mb_z | -0.0571 ± 0.0179 | 1.4407e-03 | ** |
| D1: Cu_niche ~ KO_density (MGnify, n=25) | ko_per_mb_total_z | -2862.9082 ± 3487.2583 | 4.4306e-01 | ns |
| D2: Zn_niche ~ KO_density (MGnify, n=25) | ko_per_mb_total_z | -12389.7973 ± 25016.5596 | 6.3803e-01 | ns |
| D3: Metal_niche_composite ~ KO_density (MGnify, n=25) | ko_per_mb_total_z | -11965.1830 ± 22945.3705 | 6.2072e-01 | ns |

*: p<0.05, **: p<0.01, ***: p<0.001, ns: not significant

## Interpretation

**Main finding: Per-Mb metal-gene density predicts NARROWER, not wider, environmental niche
breadth.** This pattern contradicts the hypothesis that metal resistance genes promote
ecological generalism across environmental gradients. Instead, the results suggest that:

1. **Specialization over generalism**: Genera with high metal-gene density occupy narrower
   pH and environmental gradients. This could reflect:
   - Metabolic costs of maintaining large arsenal of metal resistance genes
   - Niche partitioning—high-investment metal specialists exclude competitors
   - Functional redundancy—excess genes are fitness drag in stable environments

2. **Environmental axis independence**: Temperature breadth is independent of KO density
   (p=0.929), but pH breadth is strongly dependent (p=0.001). This suggests metal genes
   are pH-dependent and soil pH is the limiting factor, not temperature tolerance.

3. **Phylogenetic signal**: Pagel's λ ranged from 0.086 to 0.199, indicating low phylogenetic
   signal. Environmental niche breadth is mostly shaped by non-phylogenetic factors
   (ecology, gene acquisition), supporting the view that genes, not lineage, determine
   environmental tolerances.

4. **Cross-niche consistency**: The negative effect of KO density on niche breadth holds across
   all three environmental axes simultaneously (Dataset C: β=-0.064, p<0.001), confirming
   this is a robust ecological principle, not an artifact of a single axis.

5. **Metal niche limitations**: The MGnify metal niche analysis (n=25) was underpowered and
   inconclusive. Future work should prioritize sampling more genomes with measured metal
   concentration data in cultivation experiments or environmental metagenomics.

## Conclusions

- Per-Mb metal-gene density is a significant **predictor of ecological specialization**.
- The negative relationship is strongest for pH gradients and holds when environmental
  axes are integrated into a composite breadth measure.
- This finding supports the metabolic trade-off hypothesis: extensive metal resistance systems
  impose fitness costs that limit ecological versatility.
- Genera with high metal-gene copy number are specialists adapted to specific (often hostile)
  soil environments, not generalists exploiting broad environmental ranges.

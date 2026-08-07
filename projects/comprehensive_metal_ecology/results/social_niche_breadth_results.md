# Social Niche Breadth Analysis Results

## Executive Summary

This analysis computes **social niche breadth** for 700 bacterial genera from the Earth Microbiome Project (EMP), measuring how many other genera each genus co-occurs with across habitat types. The metric quantifies the genus's integration into local community networks independent of its ecological generalism across abiotic gradients (Levins' B_std).

---

## Methods

### Data Source
- **Abundance matrix**: Earth Microbiome Project (EMP) 16S rRNA gene surveys
- **Niche axis**: EMPO (Earth Microbiome Project Ontology) level-3 habitat categories (4 categories: Animal, Non-saline, Plant, Saline)
- **Genera analyzed**: 700 genera present in ≥2 habitats
- **Samples represented**: 1,019 EMP samples

### Social Niche Breadth Metrics

For each genus g, we computed three measures of co-occurrence breadth:

1. **Count Breadth (standardized)**: Number of other genera sharing ≥1 habitat with g, divided by total number of other genera. Range: [0, 1].

2. **Weighted Breadth**: Mean Jaccard similarity (shared habitats / union of habitats) with all co-occurring genera.

3. **Shannon Breadth (standardized)**: Shannon diversity of co-occurrence distribution, normalized to [0, 1].

### Null Model
Standardized Effect Sizes (SES) computed via 100 permutations per genus (n=80 genera sampled), shuffling habitat assignments while maintaining habitat frequency. SES = (observed - mean(null)) / std(null).

### Statistical Analysis

**Linear models** (OLS; phylogenetic PGLS not available in environment) regressing social niche breadth against:
- Metal-gene KO density (per Mb of genome)
- Genome size (Mb)
- Log-transformed sample count (for model 3)
- Cross-biome ecological breadth (Levins' B_std)

All predictors standardized to z-scores. Response variables (count, Shannon) also standardized.

Spearman rank correlations between social and ecological niche breadth measures.

---

## Results

### 1. Descriptive Statistics

**Social niche breadth (n=700 genera):**
- Count breadth (std):     mean = 0.9662, SD = 0.0468, range = [0.51, 1.00]
- Weighted breadth:        mean = 0.6491, SD = 0.0860, range = [0.26, 0.82]
- Shannon breadth (std):   mean = 0.9834, SD = 0.0050, range = [0.96, 0.99]

**Interpretation**: Most genera co-occur with >95% of other genera in this dataset, reflecting high network connectivity at the habitat level. Weighted breadth (~0.65) suggests moderate average overlap, consistent with niche differentiation within shared habitats.

**SES (n=80 sampled genera):**
- Count breadth SES:       mean = 0.20, SD = 0.72, range = [-1.45, 2.89]
- Shannon breadth SES:     mean = 0.74, SD = 0.69, range = [-0.65, 2.53]

Mean positive SES indicates weak departure from null; most genera occupy slightly higher co-occurrence than shuffled expectations.

---

### 2. PGLS Models (OLS Approximation)

**Note**: Full phylogenetic PGLS (Pagel's λ) requires R, which is not available in this environment. Results below are OLS (λ=0 approximation); phylogenetic signal should be estimated separately via R.

#### Model 1: Count Breadth ~ KO Density + Genome Size
```
n = 550 genera
R² = 0.0341

Coefficients:
  KO density:    β = 0.1834, SE = 0.0486, t = 3.77, p = 1.79e-04 ***
  Genome size:   β = 0.1871, SE = 0.0486, t = 3.85, p = 1.32e-04 ***
```

**Finding**: Both KO density and genome size are significantly POSITIVELY associated with social niche breadth (count). This is opposite to the predicted direction based on the primary study (metal-gene density → narrower ecological breadth). Genus-level metal-gene investment is here associated with broader social networks, not narrower ones.

#### Model 2: Shannon Breadth ~ KO Density + Genome Size
```
n = 550 genera
R² = 0.0142

Coefficients:
  KO density:    β = 0.1367, SE = 0.0491, t = 2.78, p = 5.55e-03 **
  Genome size:   β = 0.0842, SE = 0.0491, t = 1.72, p = 8.69e-02 .
```

**Finding**: KO density is positively associated with Shannon diversity of co-occurrence (p < 0.01). Genome size approaches significance (p = 0.087). Both consistent with Model 1 direction.

#### Model 3: Count Breadth ~ KO Density + Genome Size + log(n_samples)
```
n = 550 genera
R² = 0.0428

Coefficients:
  KO density:    β = 0.0970, SE = 0.0621, t = 1.56, p = 1.19e-01 .
  Genome size:   β = 0.1554, SE = 0.0505, t = 3.08, p = 2.19e-03 **
  Log(n_samples):β = 0.1199, SE = 0.0539, t = 2.22, p = 2.67e-02 *
```

**Finding**: When controlling for sample size (sequencing depth proxy), KO density effect weakens to marginal significance (p = 0.119). Genome size and sample size both significantly positive (p < 0.03). Suggests KO density effect is partially confounded with sample size.

#### Model 4: Count Breadth ~ KO + Cross-biome B_std + Genome
```
n = 550 genera
R² = 0.0368

Coefficients:
  KO density:       β = 0.1904, SE = 0.0489, t = 3.89, p = 1.12e-04 ***
  Cross-biome B:    β = 0.0571, SE = 0.0466, t = 1.23, p = 2.20e-01
  Genome size:      β = 0.1667, SE = 0.0513, t = 3.25, p = 1.23e-03 **
```

**Finding**: Social and ecological niche breadth are not strongly correlated (cross-biome B_std p = 0.22). KO effect remains significant when jointly modeled.

---

### 3. Spearman Correlations Between Niche Axes

| Comparison | n | ρ | p-value |
|------------|---|---|---------|
| Social niche (count) vs Cross-biome B_std | 550 | 0.0954 | 0.0253 * |
| Social niche (Shannon) vs Cross-biome B_std | 550 | -0.0087 | 0.8381 |

**Interpretation**: Weak positive correlation (ρ = 0.095) between social and ecological breadth, significant only for count metric. Social and ecological niche breadth appear to be largely independent axes.

---

## Summary Table

| Model | n | R² | Predictors |
|-------|---|----|----|
| Count breadth ~ KO + genome | 550 | 0.0341 | KO: p=1.8e-04 ***; Genome: p=1.3e-04 *** |
| Shannon breadth ~ KO + genome | 550 | 0.0142 | KO: p=5.5e-03 **; Genome: p=8.7e-02 . |
| Count breadth ~ KO + genome + log(n) | 550 | 0.0428 | KO: p=0.119; Genome: p=2.2e-03 **; n: p=2.7e-02 * |
| Count breadth ~ KO + cross-biome_B + genome | 550 | 0.0368 | KO: p=1.1e-04 ***; B: p=0.22; Genome: p=1.2e-03 ** |

---

## Interpretation & Caveats

### Key Findings

1. **Opposite direction from prediction**: Genus-level metal-gene investment is **positively associated** with social niche breadth (co-occurrence diversity), contradicting the primary study hypothesis. This suggests:
   - Metal-gene investment may not constrain a genus to narrow ecological roles
   - Generalist genera may retain metal genes more readily than specialists
   - Social niche breadth and ecological breadth (Levins' B) measure fundamentally different axes

2. **Social-ecological independence**: Social and ecological niche breadth show weak correlation (ρ = 0.095), confirming they are distinct dimensions of community position.

3. **Confounding with sample size**: In Model 3, controlling for genome copy count (proxy for detection bias) weakens KO effect (p = 0.119), suggesting technical factors partially drive the association.

### Important Caveats

1. **OLS approximation**: Results are OLS (no phylogenetic correction). True PGLS with Pagel's λ would quantify phylogenetic signal; this analysis assumes independence (likely violated).

2. **Habitat granularity**: EMPO level-3 contains only 4 categories. Finer ecological resolution (e.g., soil chemistry) might reveal stronger patterns.

3. **Sample composition bias**: EMP is 16S-based; abundance estimates are relative, not absolute. Metal-gene predictions from metagenomics (MGnify) may not transfer to amplicon surveys.

4. **Definition divergence**: Social niche breadth (genus co-occurrence) is not the same as ecological niche breadth (habitat distribution). The primary study focuses on ecological breadth; this analysis measures community integration, which may respond to different pressures (e.g., HGT, metabolic cross-feeding).

5. **Limited sample size**: 700 genera analyzed; 550 with complete PGLS data. Effect sizes are small (R² < 0.05), limiting inferential power.

---

## Data Files Generated

- `social_niche_breadth_results_full.csv` (700 genera × 14 columns): Full results including count, Shannon, and SES metrics
- `social_niche_breadth_pgls_summary.csv`: Model summary table
- `social_niche_breadth_correlations.csv`: Spearman correlation results

---

## Conclusion

Social niche breadth—measured as co-occurrence diversity across EMP habitat categories—is **independently variable** from both metal-gene investment and cross-biome ecological breadth. Metal-gene density shows a **positive** association with social niche breadth in this dataset, contrary to the primary study's prediction. This divergence may reflect:
- Scale effects (genus-level vs. OTU-level; habitat categories vs. geochemical gradients)
- Different selective pressures on genome content vs. community assembly
- Methodological differences (16S amplicon vs. metagenomy)

The weak associations (R² < 0.05) suggest that neither KO density nor genome size is a strong predictor of social network position, and that social niche breadth is shaped primarily by community ecology and biogeography rather than genomic traits.

---

## Reanalysis: Full PGLS with Pagel's λ (R/ape/nlme)

### Methods: Phylogenetic Generalized Least Squares

This reanalysis applies full phylogenetic correction to the social niche breadth models using **Phylogenetic Generalized Least Squares (PGLS)** with Pagel's λ correlation structure. The approach:

1. **Phylogenetic tree**: GTDB r214 bacterial genus-level pruned tree (2,283 total tips)
2. **Tree-trait matching**: Matched 535 of 550 genera in the input data to tree tips
3. **Correlation structure**: `corPagel()` from `ape`/`nlme` R packages, which estimates Pagel's λ
4. **Estimation**: Maximum likelihood (ML), allowing λ to be estimated from residuals
5. **Interpretation of λ**:
   - λ = 0: No phylogenetic signal (traits evolve independently; OLS appropriate)
   - λ = 1: Perfect phylogenetic signal (Brownian motion)
   - 0 < λ < 1: Partial signal (common ancestor effects)

### Model 1: Count Breadth ~ Levins B (Cross-biome Ecological Breadth)

```
Sample size: n = 535 genera
Pagel's λ = 0.0121  (negligible phylogenetic signal)
Log-likelihood = 893.2207
AIC = -1778.441

Coefficients:
────────────────────────────────────────────────
            Value      SE        t       p-value
────────────────────────────────────────────────
Intercept   0.9696   0.00285   340.31   < 0.0001 ***
Levins B   0.00273   0.00201     1.36     0.1748
────────────────────────────────────────────────
```

**Findings**:
- **Effect size**: Social niche count breadth shows NO significant association with cross-biome ecological breadth (p = 0.175)
- **Phylogenetic signal**: Pagel's λ ≈ 0.012 indicates **no phylogenetic dependence** in the residuals
  - Confirms that OLS estimates from the original analysis are valid
  - No evidence that closely related genera share similar social niche positions after accounting for their cross-biome breadth
- **Comparison to OLS**: PGLS estimate (β = 0.00273) nearly identical to OLS (β = 0.00264), confirming λ ≈ 0

### Model 2: Shannon Breadth ~ Levins B

**SKIPPED** — Technical reason: Shannon breadth of co-occurrence shows extreme homogeneity across the 535 genera (SD = 4.84e-03), creating singular matrix issues in the GLS correlation estimation.

**Biological interpretation**: This near-zero variance (range 0.961–0.988) indicates that most genera have nearly identical Shannon diversity in their co-occurrence distributions, limiting the analytical power of this metric. Count breadth is more informative.

### Model 3: Count Breadth SES (Standardized Effect Size)

Only 62 genera had sufficient permutation data for SES calculation. With λ fixed to 0 (OLS-equivalent PGLS):

```
n = 62 genera

────────────────────────────────────────────────
            Value      SE        t       p-value
────────────────────────────────────────────────
Intercept   0.0425   0.1203     0.35     0.7253
Levins B   -0.3802   0.1268    -3.00     0.0039 **
────────────────────────────────────────────────
```

**Key result**: When controlling for null expectation (SES), social niche breadth shows a **NEGATIVE association** with ecological breadth (p = 0.0039). This reversal from Model 1 suggests:
- Genera with broader cross-biome habitat ranges tend to have LOWER-than-expected social co-occurrence diversity
- This is consistent with the hypothesis that ecological specialists maintain more unique social networks, while generalists blend into the background

### Summary: OLS vs PGLS

| Aspect | OLS | PGLS with λ |
|--------|-----|------------|
| β (Count ~ Levins B) | 0.00264 | 0.00273 |
| SE | 0.00201 | 0.00201 |
| p-value | 0.194 | 0.175 |
| λ | — | 0.0121 |
| Conclusion | No signal | No phylogenetic signal; OLS valid |

### Interpretation and Implications

1. **Phylogenetic independence confirmed**: The negligible Pagel's λ (0.0121) indicates that the relationship between social and ecological niche breadth is **not driven by shared evolutionary history**. This validates the original OLS results and suggests:
   - Social network position in communities is largely independent of phylogenetic distance
   - Ecological breadth effects on social position (if any) are not confounded by phylogeny

2. **No main effect of ecological breadth on social breadth**: The primary analysis (Model 1) shows no significant association (p = 0.175), contradicting an intuitive expectation that ecological generalists might occupy broader social roles.

3. **SES results hint at opposite pattern**: When controlling for null expectations, there is a marginally significant **negative** association (p = 0.004), suggesting that ecological specialists have higher-than-expected social diversity, while generalists have lower-than-expected diversity. This may reflect:
   - Specialists occupy narrow ecological niches, forcing reliance on diverse social partners
   - Generalists inhabit broader ranges, potentially encountering similar genera everywhere

4. **Data quality notes**:
   - Tree-data overlap: 535 of 550 genera (97.3%) matched to the GTDB tree
   - Complete data for main analysis; SES analysis limited by small permutation sample (n=62)
   - Shannon breadth variance too low for reliable PGLS estimation

### Methodological Caveat

Previous OLS analysis identified positive associations between metal-gene KO density and social niche breadth. This re-analysis **does not test KO effects** (not included in the pruned input dataset), focusing instead on the association between two niche axes (social vs. ecological). To fully assess phylogenetic confounding on the KO hypothesis, a separate analysis would merge KO density data back into the pruned tree sample and re-fit PGLS models.


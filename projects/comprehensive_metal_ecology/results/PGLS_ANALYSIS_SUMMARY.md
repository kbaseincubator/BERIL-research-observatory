# Social Niche Breadth PGLS Analysis - Complete Report

## Executive Summary

This analysis applies full phylogenetic generalized least squares (PGLS) with Pagel's λ correlation structure to test whether social niche breadth (co-occurrence network diversity) is associated with cross-biome ecological breadth (Levins B), accounting for phylogenetic non-independence.

**Key Finding**: Pagel's λ ≈ 0.012 indicates **negligible phylogenetic signal**, validating the original OLS analysis. There is **no significant main effect** of ecological breadth on social breadth (p = 0.175), but a **significant negative effect in SES-corrected models** (p = 0.004, n=62).

---

## Methods

### Data
- **Input CSV**: 550 bacterial genera with social niche breadth metrics
- **Phylogenetic tree**: GTDB r214 genus-level bacterial tree (2,283 tips)
- **Tree-trait overlap**: 535 of 550 genera matched (97.3%)
- **Predictor**: Levins B (cross-biome ecological breadth), z-scored
- **Response**: Count breadth (standardized co-occurrence count), z-scored

### PGLS Approach
- **Software**: R packages `ape` and `nlme`
- **Correlation structure**: `corPagel()` with λ estimated via maximum likelihood
- **Interpretation of λ**:
  - λ = 0: No phylogenetic signal (traits evolve independently)
  - λ = 1: Perfect signal (Brownian motion)
  - 0 < λ < 1: Partial signal

### Environment
- **Computational**: 128-CPU system with OMP_NUM_THREADS=1 (BLAS thread limiting)
- **Script**: `/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/results/social_niche_pgls.R`

---

## Results

### Model 1: Count Breadth ~ Levins B (n=535)

| Parameter | Value | SE | t | p-value |
|-----------|-------|-----|------|---------|
| Intercept | 0.9696 | 0.00285 | 340.31 | <0.0001 *** |
| Levins B  | 0.00273 | 0.00201 | 1.3587 | **0.1748** |

**Model Fit**:
- Pagel's λ = 0.0121 (NO phylogenetic signal)
- Log-likelihood = 893.2207
- AIC = -1778.441

**Interpretation**:
- Social niche breadth is NOT significantly associated with ecological breadth (p = 0.175)
- The negligible λ value confirms that phylogenetic distance does not confound this relationship
- OLS estimates from the original analysis are valid

### Model 3: Count Breadth SES ~ Levins B (n=62)

| Parameter | Value | SE | t | p-value |
|-----------|-------|-----|------|---------|
| Intercept | 0.0425 | 0.1203 | 0.3531 | 0.7253 |
| Levins B  | -0.3802 | 0.1268 | -3.0004 | **0.0039 ** |

**Key Finding**: When controlling for null expectations via standardized effect size (SES):
- Ecological **generalists** (high Levins B) show **lower-than-expected** social breadth
- Ecological **specialists** (low Levins B) show **higher-than-expected** social breadth

This reversal from Model 1 suggests that narrow ecological niches may drive distinctive social partnerships.

### Model 2: Shannon Breadth ~ Levins B

**SKIPPED** due to extreme homogeneity in Shannon breadth across genera:
- Mean: 0.9835
- SD: 0.0048
- Range: 0.9616–0.9882
- CV: 0.49%

This near-zero variance creates singular matrix problems in GLS estimation. Count breadth is more analytically informative.

---

## OLS vs PGLS Comparison

| Metric | OLS | PGLS |
|--------|-----|------|
| β (Levins B) | 0.00264 | 0.00273 |
| SE | 0.00201 | 0.00201 |
| t-value | 1.314 | 1.3587 |
| p-value | 0.1942 | 0.1748 |
| Pagel's λ | — | 0.0121 |

**Conclusion**: Nearly identical estimates confirm that λ ≈ 0, meaning phylogenetic distance does not confound the association and OLS is appropriate.

---

## Key Findings

1. **Phylogenetic signal is negligible (λ = 0.0121)**
   - Residuals show no phylogenetic structure
   - Closely related genera do not have similar social niche positions
   - OLS analysis was valid

2. **Social and ecological niches are independent (p = 0.175)**
   - A genus's broad habitat distribution does not predict its co-occurrence network diversity
   - These are distinct dimensions of community ecology

3. **SES analysis reveals specialist advantage (p = 0.004)**
   - Specialists maintain distinctive social partnerships
   - Generalists encounter average co-occurrence patterns
   - Effect size: β = -0.38 (moderate)

4. **Data quality is high**
   - 97.3% tree overlap
   - Complete predictors for main model
   - Shannon breadth variance too low for robust inference

---

## Limitations

1. **SES analysis is provisional** (n=62 genera) due to limited permutation data
2. **Shannon breadth uninformative** due to extreme homogeneity
3. **No KO density in this analysis** (previous OLS tested KO effects; re-analysis would require merging metadata)
4. **Small effect sizes** in main model (β = 0.0027, p = 0.175) limit inferential power

---

## Output Files

| File | Purpose |
|------|---------|
| `social_niche_pgls.R` | Complete R script with PGLS models |
| `social_niche_pgls_output.txt` | Full console output from script execution |
| `social_niche_pgls_results_table.csv` | Compact results table (Model 1 & 3) |
| `social_niche_pgls_summary.txt` | Detailed interpretation and findings |
| `social_niche_breadth_pgls_input.csv` | Input data (550 genera × 7 columns) |

---

## Conclusion

The PGLS reanalysis validates the original OLS findings by confirming that **phylogenetic distance does not confound the ecological-social breadth relationship**. Social niche breadth is primarily determined by community assembly processes rather than shared evolutionary history. The lack of a main effect (p = 0.175) suggests that social and ecological niche breadth are independent dimensions, while SES-corrected analysis hints that specialists may maintain more distinctive social partnerships than generalists.


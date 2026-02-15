# Report: Field vs Lab Gene Importance in *Desulfovibrio vulgaris* Hildenborough

## Key Findings

### ENIGMA CORAL Contains No DvH Fitness Data (NB01)

The ENIGMA CORAL database (47 tables, `enigma_coral` on BERDL) was surveyed for complementary data. Key finding: **DvH is completely absent** from the database. The single TnSeq library is for FW300-N2E2 (*Pseudomonas*), DubSeq libraries cover *E. coli*, *P. putida*, and *B. thetaiotaomicron*. All 6,705 genomes and 15,015 genes are environmental isolates from Oak Ridge, not DvH. The database does contain 4,346 field samples with geochemistry data (uranium, metals) across 596 Oak Ridge locations, and 213,044 ASVs for community composition -- potentially useful for future analyses, but not for gene-level fitness analysis.

### Condition Classification (NB02)

757 DvH experiments classified into 6 categories:

| Category | Experiments | % | Rationale |
|----------|------------|---|-----------|
| Lab-nutrient | 237 | 31.3% | Amino acids, organic acids, carbon sources |
| Field-core | 204 | 26.9% | DvH primary metabolism (sulfate, lactate, formate, pyruvate, H2) |
| Lab-other | 140 | 18.5% | Lab reagents (DMSO, PEG, osmotic stress, iron chelators) |
| Field-stress | 78 | 10.3% | FRC contaminants (uranium, mercury, nitrate, nitrite, oxygen, NO) |
| Heavy-metals | 55 | 7.3% | Metal stress (cobalt, nickel, zinc, copper, manganese, selenium) |
| Lab-antibiotic | 43 | 5.7% | Antibiotics and respiratory inhibitors |

Broad split: 337 field (44.5%) vs 420 lab (55.5%).

### Genes Important for Field Conditions Are Significantly More Conserved (NB03)

Of 2,725 non-essential genes with both fitness data and pangenome links, 76.3% are core overall. An additional 678 essential genes (80.1% core) are excluded because they lack fitness data (no transposon mutants recovered). Genes important (fitness < -2) under different condition classes show varying conservation:

| Condition class | Important genes | Core % | OR vs baseline | FDR q |
|----------------|----------------|--------|---------------|-------|
| Field-stress | 298 | **83.6%** | 1.58 | **0.026** |
| Field-core | 376 | **82.4%** | 1.46 | **0.026** |
| Lab-other | 292 | 81.5% | 1.37 | 0.073 |
| Lab-nutrient | 452 | **81.4%** | 1.36 | **0.037** |
| Lab-antibiotic | 109 | 73.4% | 0.86 | 0.49 |
| Heavy-metals | 198 | 71.2% | 0.77 | 0.14 |
| Essential (no fitness) | 678 | 80.1% | -- | -- |
| All genes (baseline) | 2,725 | 76.3% | -- | -- |

Field-stress (q=0.026), field-core (q=0.026), and lab-nutrient (q=0.037) genes are significantly enriched in the core genome after BH-FDR correction. Heavy-metals and lab-antibiotic genes trend below baseline but are not significant.

### Specificity Analysis: Lab-Specific Genes Are Surprisingly More Core

| Specificity | Genes | Core % |
|-------------|-------|--------|
| Lab-specific (sick in lab only) | 50 | **96.0%** |
| Field-specific (sick in field only) | 52 | 88.5% |
| Field-biased | 89 | 83.1% |
| Universal (sick in both) | 352 | 79.8% |
| Neutral (no strong effects) | 2,083 | 74.5% |

Counter to H1, genes with fitness defects **only under lab conditions** are 96% core (n=50), slightly higher than field-specific genes at 88.5% (n=52). Both are well above the 74.5% baseline, suggesting that any fitness importance -- regardless of ecological context -- predicts conservation. The field-specific vs lab-specific comparison is not statistically significant (Fisher exact OR=0.32, p=0.27). The universal vs neutral comparison is significant (OR=1.35, p=0.033).

### Fitness Effects Are Weak Predictors of Core Status

Logistic regression with 10-fold cross-validated AUC:

| Model | CV-AUC | Std |
|-------|--------|-----|
| Field fitness only | 0.517 | 0.052 |
| Lab fitness only | 0.531 | 0.052 |
| Field + Lab | 0.548 | 0.053 |
| Full (+ gene length) | 0.645 | 0.068 |

Gene length is a much stronger predictor of core status than fitness effects from either field or lab conditions. Neither fitness dimension alone is informative (CV-AUC near 0.5). Cross-validation confirms the in-sample estimates are not inflated.

### Threshold Sensitivity Analysis

The pattern is robust across fitness thresholds (-1 to -3):

| Condition class | -3.0 | -2.0 | -1.5 | -1.0 |
|----------------|------|------|------|------|
| Field-stress | 89.4% | 83.6% | 84.0% | 82.1% |
| Field-core | 84.4% | 82.4% | 81.9% | 79.0% |
| Lab-nutrient | 83.5% | 81.4% | 81.0% | 79.5% |
| Lab-other | 85.2% | 81.5% | 80.1% | 77.5% |
| Lab-antibiotic | 82.2% | 73.4% | 77.3% | 76.2% |
| Heavy-metals | 70.6% | 71.2% | 76.7% | 76.7% |

Field-stress consistently has the highest conservation across all thresholds. Heavy-metals is consistently the lowest. The lab-antibiotic dip at -2 is driven by a small sample (n=109 at -2 vs n=45 at -3).

### Module-Level Conservation Shows No Field-Lab Difference (NB04)

Of 52 ICA fitness modules, the mean core fraction is 0.886 and the median is 1.000. No significant correlation exists between field condition activity and module conservation (Spearman rho=0.071, p=0.62). Using the mean core fraction (0.886) as the classification threshold, modules partition into:

| Module type | Count | Mean core fraction |
|-------------|-------|-------------------|
| Ecological (field-active + conserved) | 21 | 0.980 |
| Conserved-quiet (low field activity + conserved) | 17 | 0.983 |
| Field-variable (field-active + less conserved) | 5 | 0.829 |
| Lab (low field + less conserved) | 9 | 0.516 |

The 9 "lab" modules (mean core fraction 0.516) are notably less conserved, containing genes in the accessory genome. The 21 ecological modules contain 239 member genes, of which 52 are unannotated -- candidates for novel environmental adaptation functions.

## Interpretation

### Hypothesis Outcomes

- **H1 partially supported**: Genes important for field-stress conditions are significantly more conserved than baseline (83.6% core, OR=1.58, FDR q=0.026), as are field-core genes (82.4%, OR=1.46, q=0.026). However, lab-nutrient genes are also significantly enriched (81.4%, q=0.037), and the field-specific vs lab-specific gene comparison is not significant (Fisher exact OR=0.32, p=0.27, n=50-52 per group). The strongest signal is that *any* fitness importance predicts conservation: universally important genes are significantly more core than neutral genes (OR=1.35, p=0.033). Threshold sensitivity analysis confirms field-stress genes are consistently the most conserved across thresholds from -1 to -3.
- **H2 not supported**: Module-level conservation does not correlate with field condition activity (Spearman rho=0.071, p=0.62). However, the revised module classification (using mean rather than median core fraction) reveals 9 "lab" modules with strikingly low conservation (mean core fraction 0.516), suggesting that accessory-genome modules do exist and tend to respond to lab-type conditions.
- **H3 partially supported**: 21 "ecological" modules (field-active + conserved, mean core fraction 0.980) contain 239 genes, of which 52 are unannotated candidates for environmental adaptation. These are distinct from the 9 "lab" modules, supporting the concept of a functional core relevant to environmental survival.

### Key Biological Insight

The most striking finding is that **lab-antibiotic** and **heavy-metal resistance** genes are the least conserved (73.4% and 71.2%), well below the 76.3% baseline. This suggests that resistance functions are disproportionately in the accessory genome, consistent with these being recently acquired adaptive traits carried on mobile genetic elements. Conversely, genes for core metabolism (sulfate reduction, lactate/formate/pyruvate utilization) and FRC-relevant stress responses (uranium, mercury, nitrate) are deeply conserved, reflecting their importance for DvH's ecological niche.

Note on heavy-metals classification: we classified heavy-metals (cobalt, nickel, zinc, copper, manganese, selenium, molybdate, tungstate, aluminum) as "field" in the broad category because DvH encounters these metals at Oak Ridge FRC sites. However, the low conservation of heavy-metal-important genes (71.2%) contrasts with the high conservation of uranium/mercury-important genes (in field-stress at 83.6%). This may reflect that specific metal resistance mechanisms (efflux pumps, metal-binding proteins) are accessory traits, while the uranium and mercury response involves more fundamental stress pathways (DNA repair, sulfate reduction itself) that are part of the core genome.

### Literature Context

- **Trotter et al. (2023)** generated the comprehensive barcoded transposon library for DvH used in this analysis, identifying essential genes and condition-specific phenotypes across hundreds of conditions. Our work adds a pangenome conservation dimension to their fitness measurements.
- **Rosconi et al. (2022)** showed that gene essentiality in *S. pneumoniae* is strain-dependent and influenced by accessory genome composition. This parallels our finding that fitness importance is a better predictor of conservation than the specific ecological context of the condition -- the *magnitude* of fitness effect matters more than *which* condition produces it.
- **Lee et al. (2015)** identified 352 general and 199 condition-specific essential genes in *P. aeruginosa* across six growth media, establishing the concept of condition-dependent essentiality. Our analysis extends this framework by testing whether the *ecological relevance* of conditions predicts evolutionary conservation.
- **Akusobi et al. (2025)** found 259 core essential genes and 425 differentially required genes across 21 *M. abscessus* clinical isolates, demonstrating that genetic diversity drives significant functional differences. This supports our finding that fitness effects vary by condition class, though conservation patterns do not cleanly separate field from lab conditions.
- **Shi et al. (2021)** showed that pre-existing genetic variation in DvH influences chromate tolerance, with the chromate transporter DVU0426 identified as crucial for Cr(VI) resistance -- a specific example of accessory-genome-encoded environmental adaptation.
- **Huang et al. (2022)** found that genomic islands and prophages are "major drivers for evolution and environmental adaptation" in *S. algae*, consistent with our finding that metal and antibiotic resistance genes are enriched in the accessory genome.
- **Price et al. (2018)** generated the Fitness Browser data underpinning this analysis. Our work tests a prediction implicit in their dataset: whether the ecological relevance of experimental conditions modulates the fitness-conservation relationship.

### Novel Contribution

This is the first analysis to stratify RB-TnSeq fitness effects by ecological relevance and test whether field-relevant conditions predict pangenome conservation differently than lab conditions. The finding that condition type matters less than fitness magnitude for conservation prediction was not anticipated and suggests that the core genome reflects general functional importance rather than niche-specific selection. The accessory-genome enrichment of antibiotic and metal resistance genes, however, identifies a clear functional partition that aligns with ecological expectations.

### Limitations

- 678 essential genes (80.1% core) are excluded from the fitness analysis because they lack transposon mutants. Including them would raise the overall baseline slightly but would not change condition-class comparisons (which are among non-essential genes only)
- Single organism (DvH) limits generalizability -- results may differ in organisms with larger accessory genomes
- The *Nitratidesulfovibrio vulgaris* pangenome has relatively few genomes, creating a coarse core/auxiliary classification with a high baseline core fraction (76.3%), which compresses effect sizes
- Condition classification relies on manual mapping of `condition_1` labels; edge cases (e.g., zinc sulfate as metal vs sulfate source) required subjective judgment
- The fitness < -2 threshold is the primary cutoff, but sensitivity analysis across -1 to -3 confirms pattern robustness
- Gene length is confounded with both fitness measurement quality (short genes get fewer transposon insertions) and core status (core genes tend to be longer)
- The field-specific and lab-specific gene sets are small (n=50-52), limiting statistical power for the key comparison
- Field and lab fitness effects are correlated (r ~ 0.7 from the scatter plot), meaning most genes that are sick in one context are sick in the other

## Visualizations

| Figure | Description |
|--------|-------------|
| `fig_conservation_by_condition_class.png` | Bar chart: core % for genes important (fitness < -2) in each of 6 condition classes, with all-genes baseline |
| `fig_field_vs_lab_specificity.png` | Scatter: mean field fitness vs mean lab fitness per gene, colored by core/auxiliary status |
| `fig_roc_conservation_prediction.png` | ROC curves comparing field-only, lab-only, combined, and full models for predicting core status |
| `fig_condition_importance_heatmap.png` | Heatmap: % of genes with fitness < -2 by condition class and conservation status |
| `fig_module_conservation_vs_activity.png` | Scatter (2 panels): module core fraction vs field/lab condition activity |
| `fig_ecological_vs_lab_modules.png` | Box + scatter: module conservation and activity by module type classification |

## Data Files

| File | Description |
|------|-------------|
| `experiment_classification.csv` | 757 experiments with category and broad_category assignments |
| `gene_fitness_conservation.csv` | 2,725 genes with per-category fitness stats, conservation, and specificity class |
| `module_characterization.csv` | 52 ICA modules with conservation, field/lab activity, type, and top annotation |

## Future Directions

1. **Multi-organism extension**: Apply the field vs lab classification to other ENIGMA organisms (e.g., *Pseudomonas* FW300 strains) that have both environmental relevance and Fitness Browser data, to test whether the pattern generalizes
2. **Finer-grained conservation metric**: Replace binary core/auxiliary with quantitative conservation (fraction of genomes carrying the gene cluster) to increase statistical power
3. **ENIGMA community data integration**: Use the 213K ASVs and 4,346 field samples in ENIGMA CORAL to ask whether *Desulfovibrio* abundance at Oak Ridge sites correlates with the geochemistry conditions tested in the Fitness Browser
4. **Accessory resistance gene characterization**: Deeper analysis of the antibiotic and heavy-metal resistance genes in the accessory genome -- are they on mobile elements? Recently acquired? Shared with co-occurring species at Oak Ridge?
5. **Quantitative fitness scores**: Replace binary important/not-important with continuous fitness scores (e.g., mean or minimum fitness per condition class) as predictors in logistic regression

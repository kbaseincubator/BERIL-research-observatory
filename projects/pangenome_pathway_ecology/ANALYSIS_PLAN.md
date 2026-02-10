# Analysis Plan: Pangenome Openness, GapMind Pathways & AlphaEarth Distances

## Overview

This project investigates how pangenome characteristics (open vs. closed) correlate with:
1. **Metabolic pathway completeness** via GapMind predictions
2. **Structural similarity** via AlphaEarth protein embeddings
3. **Phylogenetic distances** from the phylogenetic tree

## Five-Phase Analysis Framework

### Phase 1: Data Exploration & Characterization ✓ COMPLETE
**Notebook**: `notebooks/01_data_exploration.ipynb`

**Objectives**:
- Profile pangenome statistics across all 27,690 species
- Calculate pangenome openness index (auxiliary + singleton / total genes)
- Assess GapMind pathway data availability and coverage
- Evaluate AlphaEarth embedding availability (~28% coverage)
- Identify target species for detailed analysis

**Key Outputs**:
- `data/species_pangenome_openness.csv` - Openness scores for all species
- `data/target_species_for_analysis.csv` - Selected species with good data coverage
- `figures/01_pangenome_openness_overview.png` - Openness distribution visualization

**Key Findings**:
- Pangenome openness varies widely across species (0-1 range)
- GapMind pathways available for most genomes
- AlphaEarth embeddings cover ~28% of genomes
- Identified target species with complete data coverage

---

### Phase 2: Pathway Correlation Analysis (IN PROGRESS)
**Notebook**: `notebooks/02_pathway_analysis.ipynb`

**Objectives**:
- Aggregate GapMind pathway scores to species level
- Calculate species-level pathway metrics:
  - Mean pathway completion score
  - Pathway diversity (unique pathways/categories)
  - Coverage across metabolic categories
- Correlate pathway metrics with pangenome openness
- Analyze pathway category distributions

**Expected Correlations to Test**:
- `openness_score` ↔ `avg_pathway_score` (Do open genomes have less complete pathways?)
- `openness_score` ↔ `pathway_diversity` (Do open genomes have diverse pathways?)
- `openness_score` ↔ `unique_categories` (Do open genomes span more categories?)

**Key Outputs**:
- `data/species_pathway_openness_merged.csv` - Combined dataset
- `data/pathway_openness_correlations.csv` - Correlation statistics
- `data/pathway_categories_summary.csv` - Category-level summaries
- `figures/02_pathway_openness_correlations.png` - Scatter plots with trend lines

---

### Phase 3: Structural Distance Analysis (PLANNED)
**Notebook**: `notebooks/03_structural_distances.ipynb` (to be created)

**Objectives**:
- Extract AlphaEarth protein embeddings for target species
- Compute within-species pairwise structural distances
- Analyze distance distributions by species openness
- Test: Do open pangenomes show greater structural diversity?

**Analysis Approach**:
1. For each target species:
   - Collect all genomes with AlphaEarth embeddings
   - Compute pairwise Euclidean distances between embeddings
   - Calculate distance statistics (mean, std, quartiles)
2. Correlate distance metrics with pangenome openness

**Expected Metrics**:
- Mean within-species structural distance
- Structural diversity coefficient (std / mean)
- Distance quantiles (Q1, median, Q3)

**Key Outputs**:
- `data/species_structural_distances.csv` - Within-species distance metrics
- `data/structural_openness_correlations.csv` - Correlation results
- `figures/03_structural_distances_by_openness.png` - Distance distribution plots
- `figures/03_pca_embeddings.png` - PCA projection of embeddings

---

### Phase 4: Phylogenetic Signal Control (PLANNED)
**Notebook**: `notebooks/04_phylogenetic_analysis.ipynb` (to be created)

**Objectives**:
- Control for phylogenetic non-independence
- Use phylogenetic independent contrasts (PIC) or PGLS regression
- Determine if observed correlations are:
  - Independent of phylogeny (true signal)
  - Driven by evolutionary relationships (phylogenetic signal)

**Analysis Approach**:
1. Extract phylogenetic distances from `phylogenetic_tree_distance_pairs`
2. Build phylogenetic distance matrix for species
3. Implement PGLS regression for each correlation
4. Compare partial vs. phylogenetic-corrected correlations

**Key Outputs**:
- `data/phylogenetic_corrected_correlations.csv` - PGLS results
- `figures/04_phylogenetic_tree_with_traits.png` - Tree colored by openness
- Summary statistics on phylogenetic signal strength

---

### Phase 5: Ecological Context Integration (PLANNED)
**Notebook**: `notebooks/05_ecological_analysis.ipynb` (to be created)

**Objectives**:
- Link pangenome characteristics to environmental metadata
- Test ecological hypotheses:
  - Generalists (open pangenomes) in variable environments?
  - Specialists (closed pangenomes) in stable niches?
- Visualize patterns across environmental categories

**Analysis Approach**:
1. Join species data with `ncbi_env` environmental metadata
2. Categorize environments (aquatic, soil, human-associated, etc.)
3. Compare openness distributions by environment
4. Test interaction: environment + phylogeny → openness

**Expected Findings**:
- Environmental filtering effects on pangenome structure
- Niche specialization patterns
- Ecotype-specific pathway completeness profiles

**Key Outputs**:
- `data/species_environmental_profiles.csv` - Species-environment linkages
- `figures/05_openness_by_environment.png` - Box plots and distributions
- `figures/05_environmental_filtering_analysis.png` - Bivariate analysis

---

## Data Dependencies

| Phase | Input Tables | Key Join Keys |
|-------|--------------|---------------|
| 1 | `pangenome`, `gtdb_species_clade` | `gtdb_species_clade_id` |
| 2 | Phase 1 outputs + `gapmind_pathways`, `genome` | `genome_id`, `gtdb_species_clade_id` |
| 3 | Phase 2 outputs + `alphaearth_embeddings_all_years` | `genome_id` |
| 4 | Phase 3 outputs + `phylogenetic_tree_distance_pairs` | `gtdb_species_clade_id` |
| 5 | Phase 4 outputs + `ncbi_env`, `sample` | `genome_id`, `sample_id` |

## Timeline & Milestones

- **Checkpoint 1** (After Phase 1): Identify data gaps and target species
- **Checkpoint 2** (After Phase 2): Confirm pathway-openness relationship direction
- **Checkpoint 3** (After Phase 3): Validate structural diversity hypothesis
- **Checkpoint 4** (After Phase 4): Assess phylogenetic signal strength
- **Final**: Integrate findings into ecological framework

## Hypotheses to Test

### H1: Pathway Completeness vs. Openness
- **Hypothesis**: Open pangenomes have LESS complete metabolic pathways (more variable gene content)
- **Prediction**: Negative correlation between openness and average pathway score
- **Alternative**: Openness indicates SPECIALIZED pathways in variable niches

### H2: Structural Diversity vs. Openness
- **Hypothesis**: Open pangenomes have greater structural diversity among genomes
- **Prediction**: Positive correlation between openness and within-species structural distance variance
- **Alternative**: Closed pangenomes show more structural conservation

### H3: Phylogenetic Signal
- **Hypothesis**: Pangenome openness is primarily driven by phylogenetic relationships
- **Prediction**: Correlations weaken after phylogenetic correction
- **Alternative**: Openness varies independently of phylogeny (ecological signal)

### H4: Ecological Specialization
- **Hypothesis**: Environment shapes pangenome structure
- **Prediction**: Stable environments → closed pangenomes; Variable environments → open pangenomes
- **Alternative**: Within-environment niche diversity drives pangenome openness

## Success Criteria

✓ **Phase 1**:
- All 27,690 species have openness scores
- GapMind and AlphaEarth coverage assessed
- At least 100 target species identified

✓ **Phase 2**:
- Pathway metrics calculated for 80%+ of species
- Correlation analysis complete with p-values
- Visualizations showing relationship strength

✓ **Phase 3**:
- Structural distances computed for target species
- Within-species diversity metrics calculated
- Correlation analysis with openness complete

✓ **Phase 4**:
- Phylogenetic distances extracted and formatted
- PGLS regression models fitted
- Phylogenetic signal strength quantified

✓ **Phase 5**:
- Environmental metadata linked to species
- Categorical analysis by environment
- Multivariate integration complete

## Common BERDL Queries

### Species with high pathway coverage
```sql
SELECT
  s.GTDB_species,
  COUNT(DISTINCT gp.genome_id) as genomes_with_pathways,
  COUNT(DISTINCT g.genome_id) as total_genomes,
  ROUND(100.0 * COUNT(DISTINCT gp.genome_id) / COUNT(DISTINCT g.genome_id), 1) as coverage_pct
FROM kbase_ke_pangenome.gtdb_species_clade s
JOIN kbase_ke_pangenome.genome g ON s.gtdb_species_clade_id = g.gtdb_species_clade_id
LEFT JOIN kbase_ke_pangenome.gapmind_pathways gp ON g.genome_id = gp.genome_id
GROUP BY s.GTDB_species
HAVING COUNT(DISTINCT g.genome_id) >= 10
ORDER BY coverage_pct DESC
```

### Species with AlphaEarth embeddings
```sql
SELECT
  s.GTDB_species,
  COUNT(DISTINCT g.genome_id) as total_genomes,
  COUNT(DISTINCT ae.genome_id) as genomes_with_embeddings
FROM kbase_ke_pangenome.gtdb_species_clade s
JOIN kbase_ke_pangenome.genome g ON s.gtdb_species_clade_id = g.gtdb_species_clade_id
LEFT JOIN kbase_ke_pangenome.alphaearth_embeddings_all_years ae ON g.genome_id = ae.genome_id
GROUP BY s.GTDB_species
ORDER BY genomes_with_embeddings DESC
```

## Important Reminders

1. **Species IDs**: Always use exact match with backticks: `` = 's__Species_name--RS_GCF_123' ``
2. **Large table filters**: Filter `genome` (293K rows) before expensive joins
3. **AlphaEarth slowness**: This table is large; use with WHERE clauses
4. **Gene clusters**: Species-specific, cannot compare across species
5. **Update documentation**: Tag discoveries with `[pangenome_pathway_ecology]` in `../../docs/`

## Related Work

- `../pangenome_openness/` - Existing open/closed pangenome classification
- `../ecotype_analysis/` - Environment and phylogeny effects
- `../cog_analysis/` - Functional category distributions

## Status Tracking

- [x] Phase 1: Data Exploration - COMPLETE
- [ ] Phase 2: Pathway Analysis - IN PROGRESS
- [ ] Phase 3: Structural Distances - PLANNED
- [ ] Phase 4: Phylogenetic Control - PLANNED
- [ ] Phase 5: Ecological Context - PLANNED

---

**Project Start**: 2026-02-05
**Last Updated**: 2026-02-05
**Status**: Actively developing

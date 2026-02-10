# Pangenome Openness, Metabolic Pathways, and Biogeography

## Research Question

**Do pangenome characteristics (open vs. closed) correlate with metabolic pathway diversity and biogeographic distribution patterns?**

### Hypotheses (REVISED)

1. **Pangenome-Pathway Hypothesis**: Species with open pangenomes (higher accessory/core ratio) have MORE VARIABLE pathway completeness across genomes (intra-species heterogeneity), enabling niche-specific metabolic strategies.

2. **Niche Breadth-Pathway Hypothesis**: Species with broader ecological niches (larger AlphaEarth embedding diversity) have higher mean pathway completeness, reflecting metabolic versatility needed for diverse environments.

3. **Pangenome-Niche Hypothesis**: Open pangenome species exhibit broader ecological niche breadth (measured via AlphaEarth embedding distances), not just geographic distribution.

## Data Sources

### 1. Pangenome Statistics (`kbase_ke_pangenome.pangenome`)
- **Scale**: 27,690 species
- **Key Metrics**:
  - `no_core`: Number of core genes (present in ≥90% of genomes)
  - `no_aux_genome`: Number of accessory genes
  - `no_singleton_gene_clusters`: Number of unique genes
  - `no_genomes`: Number of genomes in species

### 2. Metabolic Pathways (`kbase_ke_pangenome.gapmind_pathways`)
- **Scale**: 305M rows (genome-level pathway predictions)
- **Important**: GapMind has exactly **80 pathways** total; each genome-pathway pair has MULTIPLE rows (different steps)
- **Key Fields**:
  - `genome_id`: Genome identifier
  - `pathway`: Metabolic pathway name (80 distinct pathways)
  - `metabolic_category`: Functional category (aa, cofactor, etc.)
  - `score_category`: `complete`, `likely_complete`, `steps_missing_low`, `steps_missing_medium`, `not_present`
  - `clade_name`: Species identifier (links to pangenome table)
- **Analysis Strategy**: Take BEST score for each genome-pathway pair, then aggregate to species

### 3. AlphaEarth Embeddings (`kbase_ke_pangenome.alphaearth_embeddings_all_years`)
- **Scale**: 83,287 genomes (28% coverage of total 293K genomes)
- **Key Concept**: AlphaEarth embeddings capture **ECOLOGICAL** context, not just geography
- **Key Fields**:
  - `genome_id`: Genome identifier
  - `cleaned_lat`, `cleaned_lon`: Geographic coordinates (supplementary)
  - `A00` - `A63`: 64-dimensional embedding vectors (PRIMARY METRIC)
  - `species`: Species identifier
- **Niche Breadth Metrics**:
  - Mean embedding distance (pairwise Euclidean)
  - Embedding variance across dimensions
  - Niche breadth score: `mean_distance × (1 + variance)`

## Analysis Pipeline

### Phase 1: Data Integration
1. **Join pangenome stats with species metadata**
   - Calculate pangenome openness metrics:
     - Accessory/Core ratio: `no_aux_genome / no_core`
     - Singleton ratio: `no_singleton_gene_clusters / no_gene_clusters`
     - Pangenome size: `no_gene_clusters`

2. **Aggregate pathway data to species level**
   - Count distinct pathways per species
   - Calculate pathway diversity (Shannon entropy)
   - Identify core vs. variable pathways per species

3. **Calculate biogeographic metrics**
   - For species with AlphaEarth coverage:
     - Compute intra-species embedding distances (geographic spread)
     - Calculate geodesic distances from lat/lon
     - Estimate geographic range

### Phase 2: Comparative Analysis
1. **Pangenome vs. Pathway Diversity**
   - Correlation: Pangenome openness ~ Pathway count
   - Regression: Pathway diversity ~ Core/Accessory ratio
   - Control for genome count per species

2. **Geography vs. Pathways**
   - Correlation: Geographic range ~ Pathway diversity
   - Analysis: Do widespread species have more pathways?

3. **Pangenome vs. Geography**
   - Correlation: Pangenome openness ~ Geographic range
   - Test: Are open pangenomes more geographically dispersed?

### Phase 3: Stratified Analysis
- **By Phylum/Class**: Do patterns differ across major clades?
- **By Environment**: Marine vs. terrestrial vs. host-associated
- **By Genome Count**: Control for sampling bias

## Key Challenges

### Data Sparsity
- **AlphaEarth coverage**: Only 28% of genomes (83K/293K) have embeddings
- **Solution**: Focus analysis on species with sufficient AlphaEarth coverage (e.g., ≥5 genomes with embeddings)

### Table Sizes
- **gapmind_pathways**: 305M rows - requires filtering and aggregation
- **Solution**: Aggregate to species level first, use Spark SQL on JupyterHub

### Species Heterogeneity
- Genome counts per species vary widely (some species have >14K genomes)
- **Solution**: Include genome count as covariate, use stratified sampling

## Expected Outputs

### Data Products
- `data/pangenome_openness_metrics.csv` - Species-level pangenome statistics
- `data/pathway_diversity_by_species.csv` - Aggregated pathway counts and diversity
- `data/biogeography_metrics.csv` - AlphaEarth distances and geographic ranges
- `data/integrated_dataset.csv` - Combined dataset for analysis

### Visualizations
- Scatter plots: Pangenome openness vs. pathway diversity
- Geographic maps: Species distribution patterns colored by pangenome openness
- Heatmaps: Pathway presence/absence across species
- Phylogenetic trees: Mapping pangenome and pathway traits

### Notebooks
- `01_data_extraction_REVISED.ipynb` - Query BERDL with CORRECTED pathway aggregation
- `02_comparative_analysis_REVISED.ipynb` - Statistical analysis with REVISED hypotheses
- `CORRECTIONS.md` - Documentation of issues and fixes

**Note**: Original notebooks deprecated due to incorrect pathway counting (see CORRECTIONS.md)

## Related Work

This project builds on:
- `projects/ecotype_analysis/` - Environment vs. phylogeny effects
- `projects/pangenome_openness/` - Open vs. closed pangenome patterns
- `projects/cog_analysis/` - Functional category distributions

## Next Steps

1. Extract pangenome statistics for all 27K species
2. Aggregate pathway data to species level
3. Calculate biogeographic metrics for species with AlphaEarth coverage
4. Identify species subset with sufficient data across all three dimensions
5. Perform correlation and regression analyses
6. Generate visualizations and interpret patterns

## Notes

- Use Spark SQL on BERDL JupyterHub for all queries (better performance than REST API)
- AlphaEarth embeddings are 64-dimensional; use Euclidean or cosine distance
- Gapmind pathways use `clade_name` (not `genome_id`) to link to species
- Remember: gene clusters are species-specific, cannot compare across species

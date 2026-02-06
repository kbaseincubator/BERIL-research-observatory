# Pangenome Openness, Metabolic Pathways, and Biogeography

## Research Question

**Do pangenome characteristics (open vs. closed) correlate with metabolic pathway diversity and biogeographic distribution patterns?**

### Hypotheses

1. **Pangenome-Pathway Hypothesis**: Species with open pangenomes (higher accessory/core ratio) have greater metabolic pathway diversity, reflecting adaptation to varied ecological niches.

2. **Geography-Pathway Hypothesis**: Species with broader biogeographic distributions (larger AlphaEarth embedding distances) have more diverse metabolic capabilities.

3. **Pangenome-Geography Hypothesis**: Open pangenome species are more widely distributed geographically due to greater metabolic flexibility.

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
- **Key Fields**:
  - `genome_id`: Genome identifier
  - `pathway`: Metabolic pathway name
  - `metabolic_category`: Functional category (aa, cofactor, etc.)
  - `score_category`: present / partial / not_present
  - `clade_name`: Species identifier (links to pangenome table)

### 3. AlphaEarth Embeddings (`kbase_ke_pangenome.alphaearth_embeddings_all_years`)
- **Scale**: 83,287 genomes (28% coverage of total 293K genomes)
- **Key Fields**:
  - `genome_id`: Genome identifier
  - `cleaned_lat`, `cleaned_lon`: Geographic coordinates
  - `A00` - `A63`: 64-dimensional embedding vectors
  - `species`: Species identifier

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
- `01_data_extraction.ipynb` - Query BERDL and extract data
- `02_pangenome_metrics.ipynb` - Calculate pangenome openness metrics
- `03_pathway_diversity.ipynb` - Aggregate pathway data
- `04_biogeography_analysis.ipynb` - AlphaEarth distance calculations
- `05_integrated_analysis.ipynb` - Combined statistical analysis and visualization

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

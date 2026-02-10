# Pangenome Openness, Metabolic Pathways, and Phylogenetic Distances

## Research Question

How do pangenome characteristics (open vs. closed) correlate with:
1. **Metabolic pathway completeness** (GapMind pathways)
2. **Phylogenetic distances** (AlphaEarth structural similarity and phylogenetic distances)
3. **Species ecology and niche specialization**

## Hypothesis

- **Open pangenomes** (high auxiliary/singleton gene ratios) may indicate:
  - Generalist species with broader niche adaptation
  - Greater horizontal gene transfer within ecological niches
  - Increased metabolic pathway diversity/flexibility

- **Closed pangenomes** (low auxiliary/singleton ratios) may indicate:
  - Specialist species with narrow niche adaptation
  - Reduced gene acquisition rates
  - Core metabolic pathway conservation

## Data Sources

### From `kbase_ke_pangenome` Database

**Pangenome Metrics** (`pangenome` table):
- `no_genomes`: Number of genomes in the pangenome
- `no_core`: Core genes present in all/most genomes
- `no_aux_genome`: Auxiliary genes (present in some genomes)
- `no_singleton_gene_clusters`: Singleton genes (unique to individual genomes)
- `no_gene_clusters`: Total gene families
- `no_CDSes`: Total coding sequences

**Pangenome Openness Index**:
```
openness = (aux_genes + singleton_genes) / total_genes
closedness = 1 - openness
```

**Metabolic Pathways** (`gapmind_pathways` table):
- `pathway`: Pathway name
- `score`: Completion score (0-1)
- `score_simplified`: Simplified category (likely/unlikely/unknown)
- `metabolic_category`: Functional category
- `sequence_scope`: Completeness scope

**Phylogenetic/Structural Distance** (`alphaearth_embeddings_all_years` table):
- High-dimensional structural embeddings derived from AlphaEarth models
- Can compute pairwise distances between genomes

**Additional Distance Data** (`phylogenetic_tree_distance_pairs` table):
- Phylogenetic distances between species

### Derived Metrics

1. **Pangenome Openness Score**
   - Ratio of variable (auxiliary + singleton) to total genes
   - Normalized to 0-1 scale

2. **Pathway Completeness Profile**
   - Per-species: Average pathway completion across all metabolic categories
   - Can analyze distributions across openness spectrum

3. **Structural Distance Correlations**
   - Compute AlphaEarth embedding distances for genomes within each species
   - Correlate with pangenome openness

4. **Phylogenetic Distance Relationships**
   - Relate pangenome openness to evolutionary distances
   - Control for phylogenetic signal

## Methodology

### Phase 1: Data Exploration & Characterization
1. Query pangenome statistics across all 27,690 species
2. Calculate pangenome openness distribution
3. Identify species with diverse openness profiles
4. Query GapMind pathway coverage and completeness

### Phase 2: Correlation Analysis
1. Species-level aggregation of pathway completion
2. Compute correlations between:
   - Pangenome openness ↔ pathway completeness
   - Pangenome openness ↔ pathway diversity
   - Pangenome openness ↔ metabolic category coverage

### Phase 3: Structural Distance Analysis
1. Extract AlphaEarth embeddings for target species
2. Compute within-species structural distances
3. Relate structural distances to pangenome openness
4. Test: Do open pangenomes show greater structural diversity?

### Phase 4: Phylogenetic Signal Control
1. Compute phylogenetic distances between species
2. Use phylogenetic independent contrasts (PIC) or PGLS
3. Determine if associations are independent of phylogeny

### Phase 5: Ecological Context
1. Link to environmental metadata (`ncbi_env` table)
2. Test environmental filtering vs. ecological opportunity
3. Visualize patterns across major environmental categories

## Expected Outputs

- **Data files**:
  - `species_pangenome_openness.csv` - Openness scores for all species
  - `species_pathway_profiles.csv` - Pathway completion by species
  - `pathway_openness_correlations.csv` - Correlation matrix
  - `alphaearth_distances_by_species.csv` - Structural distance matrices (large!)

- **Figures**:
  - Pangenome openness distribution across species
  - Scatter: openness vs. pathway completeness
  - Heatmap: Pathway categories vs. openness groups
  - PCA: Reduced AlphaEarth embeddings colored by openness
  - Phylogenetic tree with openness as trait

- **Notebooks**:
  - `01_data_exploration.ipynb` - Initial data profiling
  - `02_pangenome_openness.ipynb` - Calculate openness metrics
  - `03_pathway_analysis.ipynb` - GapMind pathway correlations
  - `04_structural_distances.ipynb` - AlphaEarth embedding analysis
  - `05_phylogenetic_analysis.ipynb` - Phylogenetic context

## Key Considerations

### Performance
- `genome` table has 293K rows - use filters
- `gapmind_pathways` is moderate size - can aggregate
- `alphaearth_embeddings_all_years` may be large - consider sampling strategy
- `genome_ani` table is very large - use carefully

### Gotchas
- AlphaEarth embeddings only cover ~28% of genomes (from previous work)
- Gene cluster IDs are species-specific - cannot compare across species
- Use exact equality for species IDs: `WHERE id = 's__Species--RS_GCF_123'`
- Some species may have incomplete pathway data - handle gracefully

### Data Limitations
- GapMind predictions vary in confidence (score categories)
- AlphaEarth coverage is incomplete
- Pathway predictions are probabilistic, not experimental

## References

- **GapMind**: Metabolic pathway completion scoring system
- **AlphaEarth**: Protein structural embedding model
- **BERDL**: KBase BER Data Lakehouse - Delta Lakehouse implementation
- **GTDB r214**: Genome Taxonomy Database version used for pangenome species

## Related Projects

- `pangenome_openness/` - Existing analysis of open vs. closed pangenome patterns
- `ecotype_analysis/` - Environment vs. phylogeny effects on gene content
- `cog_analysis/` - COG functional category distributions

## Project Status

- [ ] Data exploration and profiling
- [ ] Pangenome openness metric calculation
- [ ] Pathway correlation analysis
- [ ] Structural distance analysis
- [ ] Phylogenetic signal control
- [ ] Ecological context integration
- [ ] Manuscript/findings documentation

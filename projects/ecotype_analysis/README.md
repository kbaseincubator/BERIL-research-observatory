# Ecotype Correlation Analysis

## Research Question

What drives gene content similarity between bacterial genomes: **environmental similarity** or **phylogenetic relatedness**? When genomes from similar environments share similar gene content, is it because they adapted to the same niche, or because they inherited genes from a common ancestor?

## Hypothesis

Environmental similarity should predict gene content similarity even after controlling for phylogenetic distance. If bacteria adapt their gene repertoires to their ecological niches, genomes from similar environments should share more genes than expected from their evolutionary relationships alone.

## Approach

1. **Select target species**: Identify species with sufficient genome count (50-500) and environmental embedding coverage from AlphaEarth
2. **Extract distance matrices** for each species:
   - **Environment distance**: Cosine distance between AlphaEarth 64-dimensional embeddings
   - **Phylogenetic distance**: 100 - ANI (Average Nucleotide Identity)
   - **Gene content distance**: Jaccard distance between gene cluster presence/absence profiles
3. **Compute correlations**:
   - Raw correlation: environment vs gene content
   - Partial correlation: environment vs gene content, controlling for phylogeny
   - Partial correlation: phylogeny vs gene content, controlling for environment
4. **Compare across ecological categories**: Stratify by pathogen/commensal/environmental lifestyle

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `alphaearth_embeddings_all_years` - Environmental embeddings (64-dim vectors)
  - `genome_ani` - Pairwise ANI between genomes
  - `gene_genecluster_junction` - Gene-to-cluster memberships
  - `gtdb_species_clade` - Species taxonomy

## Key Findings

Analysis of **172 species** with sufficient environmental and phylogenetic data reveals:

### Phylogeny Usually Dominates

- **Median partial correlation for environment**: 0.0025
- **Median partial correlation for phylogeny**: 0.0143
- Phylogeny dominates in **60.5%** of species
- Environment dominates in **39.5%** of species

### No Difference by Lifestyle

Tested whether "environmental" bacteria (free-living, where lat/lon is meaningful) show stronger environment effects than host-associated bacteria. **No significant difference found** (p=0.66).

### Statistical Summary

- Significant positive environment effect (p<0.05): 12 species (7.0%)
- Significant negative environment effect: 4 species (2.3%)
- Not significant: 156 species (90.7%)

### Interpretation

For most bacterial species, phylogenetic history is a stronger predictor of gene content than environmental similarity. This suggests that:
1. Vertical inheritance dominates the gene content signal
2. Environmental adaptation may act on specific gene subsets rather than the whole genome
3. The AlphaEarth embeddings may not fully capture ecologically relevant environmental variation

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_data_extraction.ipynb` | Extract embeddings, ANI, and gene clusters for 224 target species |
| `02_ecotype_correlation_analysis.ipynb` | Compute correlations and generate visualizations |

## Visualizations

| Figure | Description |
|--------|-------------|
| `ecotype_correlation_summary.png` | 4-panel summary: correlation distributions, env vs phylo effects, sample size effect, raw vs partial |
| `ecotype_by_category.png` | Box plots comparing environment and phylogeny effects by ecological category |
| `ecotype_scatter_by_category.png` | Scatter plot of environment vs phylogeny effects, colored by category |
| `embedding_diversity_distribution.png` | Distribution of environmental embedding diversity across species |
| `environmental_vs_host_comparison.png` | Comparison of effects between environmental and host-associated bacteria |

## Data Files

| File | Description |
|------|-------------|
| `target_genomes_expanded.csv` | 13,381 genomes across 224 species with metadata |
| `species_selection_stats.csv` | Per-species statistics for species selection |
| `species_embedding_diversity.csv` | Environmental diversity metrics per species |
| `ecotype_correlation_results.csv` | Correlation results for all 172 species |
| `species_ecological_categories.csv` | Ecological categorization of species |

## Authors
- **Paramvir S. Dehal** (Lawrence Berkeley National Lab) | ORCID: 0000-0001-5810-2497 | Author

## Future Directions

1. **Subset by gene function**: Test whether specific COG categories (e.g., V-Defense, L-Mobile) show stronger environment effects
2. **Alternative distance metrics**: Try different embedding distances or environmental metadata directly
3. **Within-ecotype comparison**: For species with identified ecotypes, compare gene content between ecotype clusters

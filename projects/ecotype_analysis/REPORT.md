# Report: Ecotype Correlation Analysis

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

## Future Directions

1. **Subset by gene function**: Test whether specific COG categories (e.g., V-Defense, L-Mobile) show stronger environment effects
2. **Alternative distance metrics**: Try different embedding distances or environmental metadata directly
3. **Within-ecotype comparison**: For species with identified ecotypes, compare gene content between ecotype clusters

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_data_extraction.ipynb` | Extract embeddings, ANI, and gene clusters for 224 target species |
| `02_ecotype_correlation_analysis.ipynb` | Compute correlations and generate visualizations |

### Visualizations

| Figure | Description |
|--------|-------------|
| `ecotype_correlation_summary.png` | 4-panel summary: correlation distributions, env vs phylo effects, sample size effect, raw vs partial |
| `ecotype_by_category.png` | Box plots comparing environment and phylogeny effects by ecological category |
| `ecotype_scatter_by_category.png` | Scatter plot of environment vs phylogeny effects, colored by category |
| `embedding_diversity_distribution.png` | Distribution of environmental embedding diversity across species |
| `environmental_vs_host_comparison.png` | Comparison of effects between environmental and host-associated bacteria |

### Data Files

| File | Description |
|------|-------------|
| `target_genomes_expanded.csv` | 13,381 genomes across 224 species with metadata |
| `species_selection_stats.csv` | Per-species statistics for species selection |
| `species_embedding_diversity.csv` | Environmental diversity metrics per species |
| `ecotype_correlation_results.csv` | Correlation results for all 172 species |
| `species_ecological_categories.csv` | Ecological categorization of species |

## Revision History
- **v1** (2026-02): Migrated from README.md

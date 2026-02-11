# Pangenome Openness Analysis

## Research Question

Do **open pangenomes** (species with high gene content variability) show different patterns of environmental vs phylogenetic effects compared to **closed pangenomes**?

Open pangenomes have a low fraction of core genes and high fraction of singleton/accessory genes, suggesting frequent horizontal gene transfer. Closed pangenomes have mostly conserved gene content across all genomes.

## Hypothesis

**Open pangenomes should show stronger environment effects** because:
- High gene turnover suggests ecological adaptation pressure
- Species with more HGT may acquire niche-specific genes from the environment
- Closed pangenomes may be more constrained by phylogenetic inertia

## Approach

1. **Calculate openness metrics** using pre-computed pangenome statistics:
   - Core fraction: `no_core / no_gene_clusters`
   - Singleton fraction: `no_singleton_gene_clusters / no_gene_clusters`
   - Openness = 1 - core_fraction (higher = more open)

2. **Correlate with ecotype effects** from the ecotype_analysis project:
   - Environment partial correlation (controlling for phylogeny)
   - Phylogeny partial correlation (controlling for environment)

3. **Statistical test**: Spearman correlation between openness and effect sizes

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `pangenome` - Pre-computed pangenome statistics including:
    - `no_core` - Number of core gene clusters
    - `no_aux_genome` - Number of auxiliary gene clusters
    - `no_singleton_gene_clusters` - Number of singleton clusters
    - `no_gene_clusters` - Total gene clusters

**Key Discovery**: The `pangenome` table already has pre-computed statistics - no need to compute from the `gene_cluster` table!

## Key Findings

### No Correlation Found

Analysis of pangenome openness vs environment/phylogeny effects revealed **no significant relationship**:

| Metric | Spearman rho | p-value |
|--------|--------------|---------|
| Openness vs Environment effect | -0.05 | 0.54 |
| Openness vs Phylogeny effect | 0.03 | 0.73 |

### Interpretation

Whether a species has an open or closed pangenome does **not predict** whether environment or phylogeny dominates its gene content. This suggests:

1. **Pangenome structure is independent of eco-phylo dynamics**: Open pangenomes don't necessarily mean environment-driven adaptation
2. **HGT may not track environmental similarity**: Gene acquisition might be opportunistic rather than niche-specific
3. **Core/accessory classification may not capture functional adaptation**: The genes that vary may not be the ones responding to environment

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_explore_gene_data.ipynb` | Understand gene table structure and pangenome statistics |

## Visualizations

| Figure | Description |
|--------|-------------|
| `pangenome_vs_effects.png` | Scatter plots of pangenome openness vs environment and phylogeny effect sizes |

## Data Files

| File | Description |
|------|-------------|
| `pangenome_stats.csv` | Pre-computed pangenome statistics for target species |

## Related Projects

This project builds on:
- **ecotype_analysis**: Uses the environment vs phylogeny effect sizes computed there
- **cog_analysis**: The functional partitioning findings may explain why openness alone doesn't predict adaptation patterns

## Authors
- **Paramvir S. Dehal** (Lawrence Berkeley National Lab) | ORCID: 0000-0001-5810-2497 | Author

## Future Directions

1. **Stratify by gene function**: Do open pangenomes show environment effects specifically in L (mobile) or V (defense) categories?
2. **Test alternative openness metrics**: Try auxiliary fraction, Heap's law alpha, or pangenome fluidity
3. **Lifestyle interaction**: Test openness × lifestyle interaction (e.g., open pathogens vs open environmental species)

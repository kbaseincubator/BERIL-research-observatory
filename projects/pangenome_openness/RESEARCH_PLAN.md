# Research Plan: Pangenome Openness Analysis

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

## Related Projects

This project builds on:
- **ecotype_analysis**: Uses the environment vs phylogeny effect sizes computed there
- **cog_analysis**: The functional partitioning findings may explain why openness alone doesn't predict adaptation patterns

## Revision History
- **v1** (2026-02): Migrated from README.md

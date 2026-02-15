# Report: Pangenome Openness Analysis

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

## Future Directions

1. **Stratify by gene function**: Do open pangenomes show environment effects specifically in L (mobile) or V (defense) categories?
2. **Test alternative openness metrics**: Try auxiliary fraction, Heap's law alpha, or pangenome fluidity
3. **Lifestyle interaction**: Test openness x lifestyle interaction (e.g., open pathogens vs open environmental species)

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_explore_gene_data.ipynb` | Understand gene table structure and pangenome statistics |

### Visualizations

| Figure | Description |
|--------|-------------|
| `pangenome_vs_effects.png` | Scatter plots of pangenome openness vs environment and phylogeny effect sizes |

### Data Files

| File | Description |
|------|-------------|
| `pangenome_stats.csv` | Pre-computed pangenome statistics for target species |

## Revision History
- **v1** (2026-02): Migrated from README.md

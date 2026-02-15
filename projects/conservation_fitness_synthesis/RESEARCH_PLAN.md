# Research Plan: Gene Conservation, Fitness, and the Architecture of Bacterial Genomes

## Research Question

How does a gene's importance for bacterial survival relate to its evolutionary conservation? If a gene is essential -- or important under many conditions -- is it conserved across all strains of a species? And what happens when we look at genes that are costly to carry?

This synthesis connects two large-scale datasets: the **Fitness Browser** (RB-TnSeq mutant fitness data for ~194,000 genes across 43 bacteria) and the **KBase pangenome** (gene cluster conservation across 27,690 microbial species). Together, they let us ask whether "important" means "conserved" -- and reveal surprises about what the conserved genome actually is.

## Hypothesis

A naive model predicts that core genes are "boring" housekeeping genes -- always needed, never costly. We hypothesize that the conserved genome is instead the most functionally active part of the genome, and that lab conditions are an impoverished proxy for natural selection pressures.

## Approach

This is a synthesis project that draws on four upstream analysis projects:

| Project | What it does | Key result |
|---------|-------------|------------|
| [conservation_vs_fitness](../conservation_vs_fitness/) | Link table + essential gene analysis | Essential genes 86% core (OR=1.56) |
| [fitness_effects_conservation](../fitness_effects_conservation/) | Quantitative fitness spectrum | 16pp gradient, core = more burdensome |
| [module_conservation](../module_conservation/) | ICA modules vs pangenome | Module genes 86% core (OR=1.46) |
| [core_gene_tradeoffs](../core_gene_tradeoffs/) | Anatomy of the burden paradox | Trade-offs drive the paradox (OR=1.29) |

### Analysis Strategy

1. **The Gradient**: Quantify the fitness-conservation gradient from essential genes (82% core) to always-neutral genes (66% core) across 194,216 protein-coding genes and 43 diverse bacteria
2. **The Paradox**: Test whether core genes are more or less likely to be burdens, have condition-specific effects, and show trade-off behavior
3. **The Resolution**: Construct a selection-signature matrix crossing lab fitness cost with pangenome conservation to identify genes under purifying selection in natural environments
4. **The Architecture**: Use ICA decomposition to identify co-regulated fitness modules and test their enrichment in core genes; dissect the burden paradox by functional category

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `conservation_vs_fitness/data/` | Link table, essential genes | FB gene-to-cluster links, conservation status |
| `fitness_effects_conservation/data/` | Fitness statistics | Per-gene fitness profiles and summaries |
| `fitness_modules/data/modules/` | ICA modules | Module membership and module family data |

**Data pipeline**: DIAMOND blastp at >=90% identity mapped 177,863 FB genes to pangenome clusters. Essential genes identified as protein-coding genes with no entries in `genefitness` (no viable transposon mutants). Fitness profiles computed from ~7,500 experiments across 48 organisms.

**Note on % core**: Throughout this synthesis, % core is computed as the fraction of ALL protein-coding genes (including unmapped genes with unknown conservation) that are core. This treats unmapped genes as "not confirmed core." When restricted to mapped genes only, the percentages are higher (e.g., essential genes: 82% of all vs 86% of mapped). Individual project READMEs may use either denominator -- see each project for details.

**Statistical methods**: Fisher's exact test with BH-FDR correction, Spearman correlations, paired Wilcoxon signed-rank tests.

**Scale**: 194,216 protein-coding genes, 43 organisms, 27,690 pangenome species, 132.5M gene clusters, 1,116 ICA fitness modules.

## Revision History

- **v1** (2026-02): Migrated from README.md

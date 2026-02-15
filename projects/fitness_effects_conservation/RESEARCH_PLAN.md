# Research Plan: Fitness Effects vs Conservation -- Quantitative Analysis

## Research Question

Do genes with stronger or broader fitness effects tend to be more conserved in the pangenome? Is there a continuous gradient from essential genes (core) to dispensable genes (accessory), and what does the fitness landscape of novel/singleton genes look like?

## Hypothesis

The companion project (`conservation_vs_fitness`) showed that essential genes are modestly enriched in core clusters (OR=1.56). But essentiality is binary. This project asks the quantitative question: across the full spectrum from essential to neutral to burden, how does fitness importance relate to gene conservation? We expect a continuous gradient, but the shape and magnitude are unknown.

## Approach

1. **Extract per-gene fitness statistics** from 194,216 protein-coding genes across 43 organisms, including both fitness scores (from `genefitness`) and essential gene status (genes with no transposon insertions)
2. **Fitness magnitude vs conservation** -- bin genes from essential through strong/moderate/weak effects to neutral, compare % core across the spectrum
3. **Positive fitness effects** -- test whether auxiliary/singleton genes are more likely to be burdens (mutant grows better = gene is costly)
4. **Fitness breadth vs conservation** -- are genes important in many conditions more likely core?
5. **Condition type analysis** -- do stress, carbon source, and nitrogen source conditions reveal different conservation patterns?
6. **Novel gene fitness landscape** -- are singleton genes generally detrimental, neutral, or ephemeral (neutral except in one condition)?

## Key Methods

- **Essential gene inclusion**: Genes with no fitness data (no viable transposon mutants) are included as the most extreme fitness category, representing ~14.3% of protein-coding genes. Without them, the analysis misses the most functionally important genes.
- **Fitness profiles**: Genes classified as essential -> often_sick -> mixed -> sometimes_sick -> always_neutral -> sometimes_beneficial
- **Ephemeral niche genes**: Defined as |mean_fit| < 0.3 but min_fit < -2 and n_sick <= 3 -- neutral overall but critical in one condition
- **Shared link table**: Uses `fb_pangenome_link.tsv` from `conservation_vs_fitness` project (177,863 gene-cluster links, 33 organisms after Dyella79 exclusion)

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kescience_fitnessbrowser` | `genefitness` | Per-gene per-experiment fitness scores |
| `kescience_fitnessbrowser` | `experiment` | Experiment metadata, `expGroup` condition categories |
| `kescience_fitnessbrowser` | `specificphenotype` | Genes with strong condition-specific effects |
| Shared | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Gene-to-cluster links with conservation |
| Shared | `conservation_vs_fitness/data/essential_genes.tsv` | Essential gene classification |

## Project Structure

```
projects/fitness_effects_conservation/
├── README.md
├── notebooks/
│   ├── 02_fitness_vs_conservation.ipynb   # Magnitude + novel gene landscape
│   └── 03_breadth_vs_conservation.ipynb   # Breadth + condition type
├── src/
│   └── extract_fitness_stats.py           # Spark data extraction
├── data/
│   ├── fitness_stats.tsv                  # Per-gene fitness summary
│   ├── fitness_stats_by_condition.tsv     # Per-gene per-condition-type stats
│   └── specific_phenotypes.tsv            # Specific phenotype counts
└── figures/
```

## Revision History

- **v1** (2026-02): Migrated from README.md

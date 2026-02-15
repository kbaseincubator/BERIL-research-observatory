# Report: Fitness Effects vs Conservation -- Quantitative Analysis

## Key Findings

### Conservation Increases with Fitness Importance

A clear gradient from essential to neutral genes:

| Fitness category | n genes | % Core |
|-----------------|--------:|-------:|
| Essential (no viable mutants) | 27,693 | **82%** |
| Often sick (>10% experiments) | 15,989 | 78% |
| Mixed (sick + beneficial) | 20,739 | 70% |
| Sometimes sick | 25,201 | 72% |
| Always neutral | 94,889 | **66%** |
| Sometimes beneficial | 9,705 | 70% |

The same gradient holds when binning by strongest fitness effect: essential -> 82.2% core, min_fit < -3 -> 77.7%, min_fit -1 to 0 -> 66.4%.

### Breadth of Fitness Effects Predicts Conservation

Genes important in more conditions are more likely core (Spearman rho=0.086, p=8.1e-230):

| Breadth | % Core |
|---------|-------:|
| Essential | 82% |
| 20+ experiments | 79% |
| 6-20 experiments | 73% |
| 1-5 experiments | 71% |
| 0 experiments | 66% |

### Core Genes Are Not Burdens -- They're More Likely Beneficial

Counter to the expectation that accessory genes might be costly to carry, **core genes are MORE likely to show positive fitness effects** when deleted (24.4% ever beneficial vs 19.9% for auxiliary, OR=0.77 for auxiliary vs core). This may reflect that core genes are more likely to participate in trade-off situations -- they help in some conditions but cost in others.

### Specific-Phenotype Genes Are More Likely Core

Genes with strong condition-specific effects (tagged in `specificphenotype`) are 77.3% core vs 70.3% for genes without specific phenotypes (OR=1.78, p=1.8e-97). This contradicts the naive expectation that condition-specific genes would be accessory. Instead, it suggests that core genes are more likely to have measurable condition-specific effects -- perhaps because they participate in well-characterized pathways.

### Ephemeral Niche Genes

4,450 genes (2.7%) fit the "ephemeral niche gene" pattern: neutral overall but critical in one condition. Surprisingly, these are MORE common in core genes (3.0%) than auxiliary (1.7%) or singleton (1.6%). Core genes may simply have more detectable conditional effects because they participate in more pathways.

## Interpretation

The results paint a consistent picture: **gene fitness importance and pangenome conservation are positively correlated across the full spectrum**. Essential genes are 82% core; always-neutral genes are 66% core. This 16-percentage-point gradient spans ~194,000 genes across 43 diverse bacteria.

However, several findings challenge simple models:
- Core genes are more likely to be both detrimental (essential) AND beneficial (burden) when deleted -- they're more extreme, not more neutral
- Condition-specific fitness genes are more core, not more accessory
- Novel/singleton genes are NOT systematically detrimental -- their mean fitness is near zero, similar to auxiliary genes

These patterns suggest that core genes are the most functionally active genes -- they have the largest fitness effects in both directions because they're embedded in critical pathways. Accessory genes, by contrast, tend to be functionally quieter under lab conditions.

## Supporting Evidence

| Type | Path | Description |
|------|------|-------------|
| Notebook | `notebooks/02_fitness_vs_conservation.ipynb` | Magnitude + novel gene landscape |
| Notebook | `notebooks/03_breadth_vs_conservation.ipynb` | Breadth + condition type analysis |
| Data | `data/fitness_stats.tsv` | Per-gene fitness summary |
| Data | `data/fitness_stats_by_condition.tsv` | Per-gene per-condition-type stats |
| Data | `data/specific_phenotypes.tsv` | Specific phenotype counts |

## Revision History

- **v1** (2026-02): Migrated from README.md

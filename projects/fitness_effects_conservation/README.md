# Fitness Effects vs Conservation — Quantitative Analysis

## Research Question

Do genes with stronger or broader fitness effects tend to be more conserved in the pangenome? Is there a continuous gradient from essential genes (core) to dispensable genes (accessory), and what does the fitness landscape of novel/singleton genes look like?

## Motivation

The companion project (`conservation_vs_fitness`) showed that essential genes are modestly enriched in core clusters (OR=1.56). But essentiality is binary. This project asks the quantitative question: across the full spectrum from essential to neutral to burden, how does fitness importance relate to gene conservation?

## Approach

1. **Extract per-gene fitness statistics** from 194,216 protein-coding genes across 43 organisms, including both fitness scores (from `genefitness`) and essential gene status (genes with no transposon insertions)
2. **Fitness magnitude vs conservation** — bin genes from essential through strong/moderate/weak effects to neutral, compare % core across the spectrum
3. **Positive fitness effects** — test whether auxiliary/singleton genes are more likely to be burdens (mutant grows better = gene is costly)
4. **Fitness breadth vs conservation** — are genes important in many conditions more likely core?
5. **Condition type analysis** — do stress, carbon source, and nitrogen source conditions reveal different conservation patterns?
6. **Novel gene fitness landscape** — are singleton genes generally detrimental, neutral, or ephemeral (neutral except in one condition)?

## Key Methods

- **Essential gene inclusion**: Genes with no fitness data (no viable transposon mutants) are included as the most extreme fitness category, representing ~14.3% of protein-coding genes. Without them, the analysis misses the most functionally important genes.
- **Fitness profiles**: Genes classified as essential → often_sick → mixed → sometimes_sick → always_neutral → sometimes_beneficial
- **Ephemeral niche genes**: Defined as |mean_fit| < 0.3 but min_fit < -2 and n_sick ≤ 3 — neutral overall but critical in one condition
- **Shared link table**: Uses `fb_pangenome_link.tsv` from `conservation_vs_fitness` project (177,863 gene-cluster links, 33 organisms after Dyella79 exclusion)

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kescience_fitnessbrowser` | `genefitness` | Per-gene per-experiment fitness scores |
| `kescience_fitnessbrowser` | `experiment` | Experiment metadata, `expGroup` condition categories |
| `kescience_fitnessbrowser` | `specificphenotype` | Genes with strong condition-specific effects |
| Shared | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Gene-to-cluster links with conservation |
| Shared | `conservation_vs_fitness/data/essential_genes.tsv` | Essential gene classification |

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

The same gradient holds when binning by strongest fitness effect: essential → 82.2% core, min_fit < -3 → 77.7%, min_fit -1 to 0 → 66.4%.

### Breadth of Fitness Effects Predicts Conservation

Genes important in more conditions are more likely core (Spearman rho=0.086, p=8.1e-230):

| Breadth | % Core |
|---------|-------:|
| Essential | 82% |
| 20+ experiments | 79% |
| 6-20 experiments | 73% |
| 1-5 experiments | 71% |
| 0 experiments | 66% |

### Core Genes Are Not Burdens — They're More Likely Beneficial

Counter to the expectation that accessory genes might be costly to carry, **core genes are MORE likely to show positive fitness effects** when deleted (24.4% ever beneficial vs 19.9% for auxiliary, OR=0.77 for auxiliary vs core). This may reflect that core genes are more likely to participate in trade-off situations — they help in some conditions but cost in others.

### Specific-Phenotype Genes Are More Likely Core

Genes with strong condition-specific effects (tagged in `specificphenotype`) are 77.3% core vs 70.3% for genes without specific phenotypes (OR=1.78, p=1.8e-97). This contradicts the naive expectation that condition-specific genes would be accessory. Instead, it suggests that core genes are more likely to have measurable condition-specific effects — perhaps because they participate in well-characterized pathways.

### Ephemeral Niche Genes

4,450 genes (2.7%) fit the "ephemeral niche gene" pattern: neutral overall but critical in one condition. Surprisingly, these are MORE common in core genes (3.0%) than auxiliary (1.7%) or singleton (1.6%). Core genes may simply have more detectable conditional effects because they participate in more pathways.

## Interpretation

The results paint a consistent picture: **gene fitness importance and pangenome conservation are positively correlated across the full spectrum**. Essential genes are 82% core; always-neutral genes are 66% core. This 16-percentage-point gradient spans ~194,000 genes across 43 diverse bacteria.

However, several findings challenge simple models:
- Core genes are more likely to be both detrimental (essential) AND beneficial (burden) when deleted — they're more extreme, not more neutral
- Condition-specific fitness genes are more core, not more accessory
- Novel/singleton genes are NOT systematically detrimental — their mean fitness is near zero, similar to auxiliary genes

These patterns suggest that core genes are the most functionally active genes — they have the largest fitness effects in both directions because they're embedded in critical pathways. Accessory genes, by contrast, tend to be functionally quieter under lab conditions.

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

## Reproduction

**Prerequisites**: Python 3.10+, pandas, numpy, matplotlib, scipy. BERDL Spark Connect for data extraction.

1. **Extract fitness stats** (Spark): `python3 src/extract_fitness_stats.py`
2. **Run NB02** (local): `jupyter nbconvert --execute notebooks/02_fitness_vs_conservation.ipynb`
3. **Run NB03** (local): `jupyter nbconvert --execute notebooks/03_breadth_vs_conservation.ipynb`

Requires `conservation_vs_fitness` project data (link table, essential genes) at `../conservation_vs_fitness/data/`.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

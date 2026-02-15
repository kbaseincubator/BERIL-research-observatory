# Research Plan: Fitness Modules x Pangenome Conservation

## Research Question

Are ICA fitness modules enriched in core or accessory pangenome genes, and do cross-organism module families map to the core genome?

## Hypothesis

The `fitness_modules` project identified 1,116 co-regulated gene modules across 32 bacteria via ICA decomposition of RB-TnSeq data, then aligned them into 156 cross-organism module families. The `conservation_vs_fitness` project linked FB genes to pangenome clusters with conservation status. We hypothesize that functionally coherent gene groups (modules) preferentially reside in the conserved core genome, and that module families spanning more organisms will have higher core fractions.

## Approach

1. Merge module membership data with pangenome conservation status across 29 overlapping organisms
2. Compute per-module conservation composition (% core / auxiliary / singleton)
3. Classify modules as core (>90% core genes), mixed (50-90%), or accessory (<50%)
4. Test whether module families spanning more organisms have higher core fractions
5. Check whether essential genes appear in modules (they shouldn't -- ICA requires fitness data)

## Data Sources

| Source | Use |
|--------|-----|
| `fitness_modules/data/modules/` | ICA module membership (32 organisms) |
| `fitness_modules/data/module_families/` | Module family mapping and annotations |
| `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Gene-to-cluster links with conservation status |
| `conservation_vs_fitness/data/essential_genes.tsv` | Essential gene classification |

## Project Structure

```
projects/module_conservation/
├── README.md
├── notebooks/
│   ├── 01_module_conservation.ipynb   # Per-module conservation profiles
│   └── 02_family_conservation.ipynb   # Family breadth vs conservation
├── data/
│   ├── module_conservation.tsv        # Per-module conservation composition
│   └── family_conservation.tsv        # Per-family conservation summary
└── figures/
```

## Revision History

- **v1** (2026-02): Migrated from README.md

# Fitness Modules × Pangenome Conservation

## Research Question

Are ICA fitness modules enriched in core or accessory pangenome genes, and do cross-organism module families map to the core genome?

## Motivation

The `fitness_modules` project identified 1,116 co-regulated gene modules across 32 bacteria via ICA decomposition of RB-TnSeq data, then aligned them into 156 cross-organism module families. The `conservation_vs_fitness` project linked FB genes to pangenome clusters with conservation status. This project connects them to ask: do functionally coherent gene groups (modules) preferentially reside in the conserved core genome?

## Approach

1. Merge module membership data with pangenome conservation status across 29 overlapping organisms
2. Compute per-module conservation composition (% core / auxiliary / singleton)
3. Classify modules as core (>90% core genes), mixed (50-90%), or accessory (<50%)
4. Test whether module families spanning more organisms have higher core fractions
5. Check whether essential genes appear in modules (they shouldn't — ICA requires fitness data)

## Key Findings

### Module Genes Are More Core Than Average

- **Module genes: 86.0% core** vs all genes: 81.5% (+4.5 percentage points)
- Genes assigned to ICA modules are co-regulated functional units, and they skew toward the conserved core genome

### Most Modules Are Core

Of 974 modules with ≥3 mapped genes:
- **577 (59%) are core modules** (>90% core genes)
- 349 (36%) are mixed modules (50-90% core)
- **48 (5%) are accessory modules** (<50% core)

The median module is 93.4% core. Most co-regulated fitness response units are embedded in the conserved genome.

### Family Breadth Does NOT Predict Conservation

Surprisingly, module families spanning more organisms do NOT have higher core fractions (Spearman rho=-0.01, p=0.914). Families are nearly all core regardless of how many organisms they span. The core genome baseline is so high (~82%) that there's little room for a gradient.

### Accessory Module Families Exist

38 families have <50% core genes — these are co-regulated accessory gene modules conserved across organisms. They may represent horizontally transferred functional units or niche-specific operons.

### Essential Genes Are Absent from Modules

0 essential genes appear in any module, confirming that ICA modules only capture genes with measurable fitness variation (non-essential genes with transposon insertions). Essential genes are invisible to ICA because they have no fitness data.

## Limitations

- **Ceiling effect**: The baseline core rate is already ~81.5%, limiting the maximum observable enrichment. The +4.5pp difference to 86% is statistically significant but represents a modest absolute effect.
- **29/32 organism subset**: 3 module organisms (Cola, Kang, SB2B) lack pangenome links because their species had too few genomes in GTDB for pangenome construction.
- **Module membership threshold**: The upstream ICA module membership uses |Pearson r| ≥ 0.3 with max 50 genes per module. This threshold affects which genes are "in" a module and could influence conservation composition.
- **Classification thresholds are arbitrary**: The 90% and 50% cutoffs for core/mixed/accessory module classification are convenient but not biologically motivated.
- **Essential genes excluded**: ICA requires fitness data, so essential genes (no transposon insertions) are absent from all modules. This means modules only capture the non-essential portion of the genome.

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

## Reproduction

All analysis runs locally — no Spark needed.

Requires data from:
- `projects/fitness_modules/data/modules/` and `data/module_families/`
- `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` and `essential_genes.tsv`

```bash
cd projects/module_conservation
jupyter nbconvert --execute notebooks/01_module_conservation.ipynb
jupyter nbconvert --execute notebooks/02_family_conservation.ipynb
```

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

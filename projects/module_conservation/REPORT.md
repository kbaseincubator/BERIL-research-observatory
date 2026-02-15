# Report: Fitness Modules x Pangenome Conservation

## Key Findings

### Module Genes Are More Core Than Average

- **Module genes: 86.0% core** vs all genes: 81.5% (+4.5 percentage points)
- Genes assigned to ICA modules are co-regulated functional units, and they skew toward the conserved core genome

### Most Modules Are Core

Of 974 modules with >=3 mapped genes:
- **577 (59%) are core modules** (>90% core genes)
- 349 (36%) are mixed modules (50-90% core)
- **48 (5%) are accessory modules** (<50% core)

The median module is 93.4% core. Most co-regulated fitness response units are embedded in the conserved genome.

### Family Breadth Does NOT Predict Conservation

Surprisingly, module families spanning more organisms do NOT have higher core fractions (Spearman rho=-0.01, p=0.914). Families are nearly all core regardless of how many organisms they span. The core genome baseline is so high (~82%) that there's little room for a gradient.

### Accessory Module Families Exist

38 families have <50% core genes -- these are co-regulated accessory gene modules conserved across organisms. They may represent horizontally transferred functional units or niche-specific operons.

### Essential Genes Are Absent from Modules

0 essential genes appear in any module, confirming that ICA modules only capture genes with measurable fitness variation (non-essential genes with transposon insertions). Essential genes are invisible to ICA because they have no fitness data.

## Interpretation

ICA fitness modules are enriched in core genes (86% vs 81.5% baseline, OR=1.46, p=1.6e-87), confirming that co-regulated functional units preferentially reside in the conserved genome. However, the enrichment is modest due to a ceiling effect -- the baseline core rate is already very high. The surprising null result for family breadth vs conservation (rho=-0.01) suggests that conservation is a property of individual genes, not of the cross-organism scope of their regulatory module.

## Limitations

- **Ceiling effect**: The baseline core rate is already ~81.5%, limiting the maximum observable enrichment. The +4.5pp difference to 86% is statistically significant but represents a modest absolute effect.
- **29/32 organism subset**: 3 module organisms (Cola, Kang, SB2B) lack pangenome links because their species had too few genomes in GTDB for pangenome construction.
- **Module membership threshold**: The upstream ICA module membership uses |Pearson r| >= 0.3 with max 50 genes per module. This threshold affects which genes are "in" a module and could influence conservation composition.
- **Classification thresholds are arbitrary**: The 90% and 50% cutoffs for core/mixed/accessory module classification are convenient but not biologically motivated.
- **Essential genes excluded**: ICA requires fitness data, so essential genes (no transposon insertions) are absent from all modules. This means modules only capture the non-essential portion of the genome.

## Supporting Evidence

| Type | Path | Description |
|------|------|-------------|
| Notebook | `notebooks/01_module_conservation.ipynb` | Per-module conservation profiles |
| Notebook | `notebooks/02_family_conservation.ipynb` | Family breadth vs conservation |
| Data | `data/module_conservation.tsv` | Per-module conservation composition |
| Data | `data/family_conservation.tsv` | Per-family conservation summary |

## Revision History

- **v1** (2026-02): Migrated from README.md

# Research Plan: Core Gene Paradox -- Why Are Core Genes More Burdensome?

## Research Question

Why are core genome genes MORE likely to show positive fitness effects when deleted (burdensome) than accessory genes? What functions and conditions drive this, and what does it tell us about natural selection?

## Hypothesis

The `fitness_effects_conservation` project found that core genes are 1.3x more likely to be burdens than auxiliary genes (OR=0.77 for auxiliary vs core, p=5.5e-48) and that condition-specific fitness genes are more core (OR=1.78). This contradicts the "streamlining" model where accessory genes are metabolic burdens.

**Key framing**: Lab conditions are an impoverished proxy for nature. A gene burdensome in LB may be essential in soil or biofilm. Genes that are simultaneously costly (lab) AND conserved (pangenome) are the strongest evidence for purifying selection -- nature maintains them despite their cost.

## Approach

1. Dissect the burden paradox by functional category (SEED top-level categories) to determine which functions drive the core-burden excess
2. Identify trade-off genes -- genes that are important (fit < -1) in some conditions and burdensome (fit > 1) in others -- and test their enrichment in core
3. Construct a selection-signature matrix crossing lab fitness cost with pangenome conservation
4. Analyze burden patterns by condition type (stress, carbon source, nitrogen source, etc.)
5. Case studies of specific functional categories (motility, cell wall)

## Data Sources

| Source | Use |
|--------|-----|
| `fitness_effects_conservation/data/` | Per-gene fitness statistics |
| `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Gene-to-cluster links with conservation status |
| `conservation_vs_fitness/data/seed_annotations.tsv` | SEED functional annotations |
| `conservation_vs_fitness/data/seed_hierarchy.tsv` | SEED functional category hierarchy |

## Project Structure

```
projects/core_gene_tradeoffs/
├── README.md
├── notebooks/
│   └── 01_burden_anatomy.ipynb   # Full analysis (6 sections)
└── figures/
    ├── burden_by_function.png
    ├── burden_by_condition.png
    ├── tradeoff_genes_conservation.png
    ├── specific_phenotype_conditions.png
    ├── motility_case_study.png
    └── selection_signature_matrix.png
```

## Revision History

- **v1** (2026-02): Migrated from README.md

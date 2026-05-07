# Macro-Micro Nutrient Gene Co-cycling in Bacterial Pangenomes

## Research Question

Do bacterial pangenomes encoding macro-nutrient acquisition (P, N) and phenazine biosynthesis genes disproportionately co-encode trace-metal handling genes, reflecting the biogeochemical coupling of nutrient and metal cycles through enzyme cofactor requirements and Fe-oxyhydroxide mineral dissolution?

## Status

**Analysis complete** — Substrate A (pangenome co-occurrence) executed across all four analysis steps. Substrates B (ecological co-occurrence) and C (gene-fitness correlation) are named future directions.

## Overview

Across 27,682 GTDB species pangenomes from `kbase_ke_pangenome`, we find significant co-occurrence of P-acquisition and metal-handling genes (phi=0.110, OR=2.3, p=1.3×10⁻⁶⁵), N-fixation and metal-handling genes (phi=0.107, OR=4.0, p=1.5×10⁻⁸⁷), and complete overlap of phenazine operon carriers with metal-handling genes (63/63 species, 100%). The 63 phenazine operon carriers are concentrated in soil Actinomycetota and rhizosphere Pseudomonadota, consistent with the McRose-Newman model of phenazine-mediated Fe(III)-oxyhydroxide dissolution as a joint P and trace-metal mobilization strategy.

## Quick Links

- [RESEARCH_PLAN.md](RESEARCH_PLAN.md) — Hypothesis, approach, revision history
- [REPORT.md](REPORT.md) — Full findings and interpretation
- [figures/figure1_cooccurrence.png](figures/figure1_cooccurrence.png) — Multi-panel figure

## Reproduction

```bash
# Step 1: Extract gene families (requires on-cluster Spark access)
python src/01_extract_gene_families.py

# Step 2: Co-occurrence statistics
python src/02_cooccurrence_stats.py

# Step 3: Core vs. accessory enrichment
python src/03_core_accessory_enrichment.py

# Step 4: Phylogenetic stratification
python src/04_phylogenetic_stratification.py

# Figure
python src/05_figure.py
```

Step 1 requires access to the `kbase_ke_pangenome` tenant on BERDL. Steps 2–5 run on the CSV outputs in `data/`.

## Authors

- Jing Tao (jingtao-lbl), Lawrence Berkeley National Laboratory

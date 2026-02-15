# The 5,526 Costly + Dispensable Genes

## Research Question

What characterizes genes that are simultaneously burdensome (fitness improves when deleted) and not conserved in the pangenome? Are they mobile elements, recent acquisitions, degraded pathways, or something else?

## Status

Completed -- costly+dispensable genes are predominantly mobile genetic element debris (7.45x keyword enrichment, 11.7x Phage/Transposon SEED enrichment). They are poorly annotated (51% vs 75% SEED), taxonomically restricted (median OG breadth 15 vs 31), and shorter (615 vs 765 bp). See [REPORT.md](REPORT.md) for full findings.

## Overview

The `core_gene_tradeoffs` project identified a 2x2 selection signature matrix of 142,190 genes: 28,017 are "costly + conserved" (maintained by natural selection despite lab-measured burden), while 5,526 are "costly + dispensable" (burdensome AND not in the core genome). This project characterizes the 5,526 costly+dispensable genes to determine whether they represent recent horizontal acquisitions, degrading ancestral functions, or mobile genetic elements. The analysis uses functional annotation enrichment (SEED, KEGG), ortholog breadth across 48 organisms, gene length distributions, and per-organism variation. See [REPORT.md](REPORT.md) for full findings and interpretation.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Hypothesis, approach, analysis plan
- [Report](REPORT.md) -- Findings, interpretation, literature context

## Data Sources

| Asset | Source Project | What it provides |
|-------|--------------|-----------------|
| Fitness stats | `fitness_effects_conservation` | Per-gene fitness summary for ~142K genes |
| FB-pangenome link | `conservation_vs_fitness` | 177K gene-to-cluster links with core/aux/singleton |
| Essential genes | `conservation_vs_fitness` | Essentiality, gene length, descriptions |
| SEED annotations | `conservation_vs_fitness` | 125K functional descriptions |
| SEED hierarchy | `conservation_vs_fitness` | Functional category hierarchy |
| KEGG annotations | `conservation_vs_fitness` | 73K KEGG group annotations |
| Ortholog groups | `essential_genome` | 179K gene-to-OG mappings across 48 organisms |
| Specific phenotypes | `fitness_effects_conservation` | Condition-specific phenotype counts |

## Project Structure

```
projects/costly_dispensable_genes/
├── README.md
├── RESEARCH_PLAN.md
├── REPORT.md
├── notebooks/
│   ├── 01_define_quadrants.ipynb            # Reconstruct 2x2 matrix, export gene lists
│   ├── 02_functional_characterization.ipynb # SEED/KEGG enrichment analysis
│   └── 03_evolutionary_context.ipynb        # Ortholog breadth, gene length, singletons
├── data/
├── figures/
└── requirements.txt
```

## Reproduction

**Prerequisites:** Python 3.10+, pandas, numpy, matplotlib, seaborn, scipy, statsmodels. All data pre-cached from upstream projects -- no Spark needed.

```bash
cd projects/costly_dispensable_genes
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/01_define_quadrants.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_functional_characterization.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_evolutionary_context.ipynb
```

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory

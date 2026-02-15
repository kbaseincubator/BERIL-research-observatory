# Gene Conservation, Fitness, and the Architecture of Bacterial Genomes

## Research Question

How does a gene's importance for bacterial survival relate to its evolutionary conservation, and what does the conserved genome actually look like?

## Status

Completed -- Synthesis of four analysis projects reveals a 16pp fitness-conservation gradient, a burden paradox where core genes are MORE costly, and a selection-signature matrix identifying 28,017 genes under purifying selection.

## Overview

This synthesis connects two large-scale datasets -- the Fitness Browser (RB-TnSeq mutant fitness data for ~194,000 genes across 43 bacteria) and the KBase pangenome (gene cluster conservation across 27,690 microbial species) -- to ask whether "important" means "conserved." It draws on four upstream analysis projects (conservation_vs_fitness, fitness_effects_conservation, module_conservation, core_gene_tradeoffs) to reveal that the conserved genome is the most functionally active part of the genome, not the most inert, and that lab conditions are an impoverished proxy for natural selection.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) -- Findings, interpretation, supporting evidence

## Reproduction

All figures are generated locally from cached upstream data:

```bash
cd projects/conservation_fitness_synthesis
jupyter nbconvert --execute notebooks/01_summary_figures.ipynb
```

Requires data from `conservation_vs_fitness/data/`, `fitness_effects_conservation/data/`, and `fitness_modules/data/modules/`.

**Scale**: 194,216 protein-coding genes, 43 organisms, 27,690 pangenome species, 132.5M gene clusters, 1,116 ICA fitness modules.

**Statistical methods**: Fisher's exact test with BH-FDR correction, Spearman correlations, paired Wilcoxon signed-rank tests.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory

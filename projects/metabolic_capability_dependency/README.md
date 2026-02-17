# Metabolic Capability vs Dependency

## Research Question

Can we distinguish metabolic *capability* (genome predicts a complete pathway) from metabolic *dependency* (fitness data shows the pathway genes actually matter)? Do "latent capabilities" — pathways that are genomically present but experimentally dispensable — predict pangenome openness and evolutionary gene loss?

## Status
In Progress — research plan created, awaiting analysis.

## Overview

This project bridges two major BERDL resources: **GapMind pathway predictions** (80 amino acid and carbon source pathways across 293K genomes) and **Fitness Browser RB-TnSeq data** (27M fitness scores across 48 organisms). Using the FB-pangenome link table from `conservation_vs_fitness`, we classify each organism-pathway pair as an **active dependency** (complete + fitness-important), a **latent capability** (complete + fitness-neutral), or **absent**. We then test whether latent capabilities correlate with pangenome openness (Black Queen Hypothesis) and whether within-species pathway variation defines metabolic ecotypes.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Data Sources
- `kbase_ke_pangenome.gapmind_pathways` — 305M rows, 80 pathways
- `kescience_fitnessbrowser.genefitness` — 27M fitness scores, 48 organisms
- Existing: `conservation_vs_fitness/data/fb_pangenome_link.tsv` (177,863 gene-cluster links)
- Existing: `conservation_vs_fitness/data/organism_mapping.tsv` (44 FB → GTDB mappings)

## Structure
```
notebooks/          — Analysis notebooks (01-05)
data/               — Extracted and processed data
figures/            — Key visualizations
requirements.txt    — Python dependencies
```

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Sierra Moxon (ORCID: 0000-0002-8719-7760), Lawrence Berkeley National Laboratory / KBase

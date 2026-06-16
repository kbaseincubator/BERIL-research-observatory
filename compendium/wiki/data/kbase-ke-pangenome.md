# KBase KE Pangenome

## Overview

The KBase KE Pangenome collection is the shared pangenome backbone in this demo.
It supplies species and clade-level gene-content context: which genes are core,
which are accessory, which gene clusters recur across species, and how genomes
can be compared within or across bacterial lineages.

Both demo topics depend on this collection. The metal-resistance projects use it
to ask whether metal-important genes are core or accessory and to score metal
gene signatures across species. The ecotype projects use it to compare
within-species gene-content profiles and COG functional categories.

## Projects Using This Collection

In [Metal Resistance & Critical Minerals](../topics/metal-resistance.md), the
pangenome is the evidence layer that turns raw fitness defects into an
evolutionary claim. The metal atlas reports that metal-important genes are
strongly core-enriched, while the cross-resistance and specificity projects
refine that into a gradient from general stress to metal-shared and
metal-specific genes.

In [Microbial Ecotypes & Niche Differentiation](../topics/microbial-ecotypes.md),
the pangenome is the matrix being compared. The ecotype correlation analysis uses
gene-cluster profiles to ask whether environment or phylogeny better predicts
gene-content similarity. The functional differentiation project then asks which
COG categories separate gene-content ecotypes.

## Connections

This collection is the best single entry point for the demo because it touches
both topics and all five projects. The [home page](../index.md) gives the full
map, while the two topic pages explain how the same pangenome layer supports
different biological questions.

## Sources

- [stmt:metal-atlas-core-robustness-finding; metal_fitness_atlas]
- [stmt:metal-atlas-conserved-families-finding; metal_fitness_atlas]
- [stmt:metal-cross-tier-architecture-finding; metal_cross_resistance]
- [stmt:ecotype-phylogeny-dominance-finding; ecotype_analysis]
- [stmt:ecotype-functional-differentiation-finding; ecotype_functional_differentiation]

# Microbial Ecotypes & Niche Differentiation

## Overview

This page synthesizes two projects on microbial ecotypes. Here, an ecotype is a
within-species bacterial subpopulation with distinct gene-content, functional, or
ecological tendencies. The demo deliberately pairs a broad correlation analysis
with a more targeted functional analysis: first asking whether environment
explains whole-genome gene-content similarity, then asking whether gene-content
clusters differ in the functions they carry.

The synthesis is cautious. Whole-genome gene-content similarity is usually more
strongly predicted by phylogeny than by environment. That does not mean ecology
is absent. It means the environmental signal may be concentrated in particular
gene subsets and functional categories rather than spread evenly across the whole
pangenome.

## What the Corpus Shows

The ecotype correlation analysis tested 172 species with sufficient
environmental and phylogenetic data. Phylogeny dominated gene-content similarity
in most species, and splitting environmental from host-associated bacteria did
not reveal a stronger environment effect. This makes the broadest claim a
negative one: whole-genome gene-content correlation is a blunt instrument for
detecting niche effects.

The functional differentiation project makes the same story more specific.
Gene-content ecotypes were detected in 12 of 15 sampled species, and COG
functional categories differed significantly across ecotypes in every valid
species. Adaptive categories such as defense, transport, carbohydrate
metabolism, and cell-wall functions showed larger effect sizes than housekeeping
categories, although housekeeping categories also varied.

Taken together, the projects suggest a two-step view of ecotype signal. First,
phylogenetic history dominates the genome-wide background. Second, within that
background, accessory-gene functions can still differ systematically between
ecotypes. That makes functional stratification more useful than treating all
gene clusters as one undifferentiated distance matrix.

## Projects and Evidence

**Ecotype Correlation Analysis** asks whether environmental similarity predicts
gene-content similarity after controlling for phylogenetic distance. Its result
is mostly negative: phylogeny dominates in 60.5% of species, and 90.7% of tested
species lack a significant positive environment effect.

**Ecotype Functional Differentiation** asks whether gene-content ecotypes differ
in COG functional profiles. It finds valid ecotypes in 12 of 15 sampled species
and significant functional differentiation in 170 of 257 species-by-COG tests.
This gives the earlier "specific gene subsets" interpretation a concrete form.

## Connections

This topic connects to [Metal Resistance & Critical Minerals](metal-resistance.md)
because both pages are about structure inside bacterial pangenomes. The metal
page separates broad core stress response from metal-specific response. This
page separates phylogenetic background from functional differentiation between
ecotypes.

The shared data anchor is [KBase KE Pangenome](../data/kbase-ke-pangenome.md),
which provides pangenome, genome, gene-cluster, and annotation tables. The author
pages for [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md) and
[Justin Reese](../authors/0000-0002-2170-2250.md) show how the ecotype work is
split across the two projects.

## Caveats and Open Directions

The broad environmental analysis is limited by missing or noisy geographic
metadata and by AlphaEarth embedding coverage. The functional analysis is limited
by sample size, clustering assumptions, and COG annotation coverage. The most
important open direction is to connect these layers: test whether the functional
categories that differ between ecotypes also show stronger environmental
association after controlling for within-species phylogeny.

## Sources

- [stmt:ecotype-phylogeny-dominance-finding; ecotype_analysis]
- [stmt:ecotype-lifestyle-null-caveat; ecotype_analysis]
- [stmt:ecotype-gene-subset-claim; ecotype_analysis]
- [stmt:ecotype-functional-widespread-finding; ecotype_functional_differentiation]
- [stmt:ecotype-functional-differentiation-finding; ecotype_functional_differentiation]
- [stmt:ecotype-adaptive-effect-claim; ecotype_functional_differentiation]
- [stmt:ecotype-unknown-mobile-caveat; ecotype_functional_differentiation]

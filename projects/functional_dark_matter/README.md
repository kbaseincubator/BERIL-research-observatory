# Functional Dark Matter — Experimentally Prioritized Novel Genetic Systems

## Research Question

Which genes of unknown function across 48 bacteria have strong fitness phenotypes, and can cross-organism conservation, co-regulation modules, pangenome distribution, and biogeographic patterns characterize their likely functions and prioritize them for experimental follow-up?

## Status

In Progress — research plan created, awaiting analysis.

## Overview

Nearly one in four bacterial genes lacks functional annotation ("hypothetical protein"), yet many of these have experimentally measured fitness effects in the Fitness Browser's 27M measurements across 7,552 conditions. This project systematically catalogs ~3,700 "dark matter" genes with strong fitness phenotypes, applies five layers of computational inference (module membership, co-fitness, domain structure, conservation patterns, biogeographic distribution), and produces a prioritized candidate list for experimental characterization.

The approach integrates data across five BERDL collections: pangenome (293K genomes), Fitness Browser (48 organisms), NMDC multi-omics (6,365 environmental samples), ENIGMA CORAL (Oak Ridge ecology), and KBase Genomes (protein sequences). Environmental analysis uses AlphaEarth satellite embeddings and NMDC abiotic measurements to test whether dark gene carriers come from environments matching the lab conditions where the genes show fitness effects.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources

This project builds on several completed projects:
- [`conservation_vs_fitness`](../conservation_vs_fitness/) — FB-pangenome link table (177,863 gene-cluster mappings)
- [`fitness_modules`](../fitness_modules/) — ICA fitness modules (1,116 modules, 32 organisms)
- [`essential_genome`](../essential_genome/) — Essential gene families (17,222 ortholog groups)

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory

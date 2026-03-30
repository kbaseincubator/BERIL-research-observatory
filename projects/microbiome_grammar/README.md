# Microbiome Grammar -- Environmental Rules for Microbial Community Design

## Research Question

Can we extract quantitative association rules linking environmental parameters (geochemistry, pH, nutrients) to microbial community composition and functional potential across BERDL databases, and use those rules to design fit-for-purpose microbial assemblages for target applications like rare earth metal recovery or complete denitrification?

## Status

In Progress -- research plan created, beginning data inventory phase.

## Overview

This project systematically inventories and integrates all environmental-microbe linkage data across BERDL's 35+ databases to build a predictive "microbiome grammar" -- a set of quantitative rules mapping environmental conditions to expected microbial taxa and their functional capabilities.

The project spans four phases:
1. **Data Inventory**: Census all metagenomic, isolate, and environmental sample data with measured environmental parameters (ENIGMA geochemistry, NMDC abiotic features, pangenome metadata)
2. **Association Mining**: Extract statistically significant taxon-environment associations and train predictive models
3. **Assemblage Design**: Build an optimization framework that recommends multi-organism assemblages for user-specified conditions and target functions
4. **Validation**: Test predictions against held-out data and experimental results from the Fitness Browser

Two driving use cases guide the framework:
- **Rare earth metal recovery**: "Recommend microbial assemblages for REE biorecovery from industrial waste at pH 6.5 & 5 mM nitrate"
- **Denitrification pathway completion**: "Which microbes in my metagenome interact to complete denitrification and prevent N2 loss?"

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- hypotheses, data sources, analysis plan
- [Report](REPORT.md) -- findings, interpretation, supporting evidence

## Data Sources

- **ENIGMA CORAL** (`enigma_coral`): 596 locations, 4,346 samples, 213K ASVs, 6,705 genomes, 52,884 geochemistry records (48 chemical species incl. 13 rare earth elements)
- **NMDC Multi-omics** (`nmdc_arkin`): 48 studies with pH, temperature, nutrients + 3M metabolomics records
- **Pangenome** (`kbase_ke_pangenome`): 293K genomes, GapMind pathway predictions, eggNOG functional annotations, AlphaEarth environmental embeddings
- **Fitness Browser** (`kescience_fitnessbrowser`): 559 metal experiments, 48 organisms with genome-wide fitness data
- **BacDive** (`kescience_bacdive`): 97K strains with growth conditions and metabolite utilization
- **Web of Microbes** (`kescience_webofmicrobes`): 37 organisms with exometabolomics profiles
- **Prior projects**: `metal_fitness_atlas`, `cf_formulation_design`, `nmdc_community_metabolic_ecology`, `enigma_contamination_functional_potential`

## Reproduction

*TBD -- add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)) -- U.C. Berkeley / Lawrence Berkeley National Laboratory

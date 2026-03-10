# BacDive Phenotype Signatures of Metal Tolerance

## Research Question
Can BacDive-measured bacterial phenotypes (Gram stain, oxygen tolerance, metabolite utilization, enzyme activities) predict metal tolerance as measured by Fitness Browser experiments and the Metal Fitness Atlas?

## Status
In Progress — research plan created, awaiting analysis.

## Overview
The Metal Fitness Atlas scored 27,702 pangenome species for metal tolerance using gene functional signatures validated against RB-TnSeq fitness data. BacDive provides standardized phenotypic measurements (Gram stain, oxygen tolerance, metabolite utilization, enzyme activities) for 97K bacterial strains. This project tests whether these readily measurable phenotypes predict metal tolerance, connecting classical microbiology (culture-based phenotyping) to genomic metal tolerance predictions. A two-scale design validates associations both directly (12 FB organisms matching BacDive) and at pangenome scale (~3,000-5,000 species linked via genome accessions).

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources
- `kescience_bacdive` — 97K strains with phenotype data (local: `data/bacdive_ingest/`)
- `projects/metal_fitness_atlas/data/species_metal_scores.csv` — metal tolerance scores for 27,702 species
- `projects/conservation_vs_fitness/data/organism_mapping.tsv` — FB organism-to-pangenome mapping
- `projects/counter_ion_effects/data/` — metal experiment classifications and counter ion data

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy

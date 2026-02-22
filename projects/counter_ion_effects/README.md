# Counter Ion Effects on Metal Fitness Measurements

## Research Question
When bacteria are exposed to metal salts (CoCl₂, NiCl₂, CuCl₂), how much of the observed fitness effect is caused by the metal cation versus the counter anion (chloride)? Does correcting for chloride confounding change the conclusions of the Pan-Bacterial Metal Fitness Atlas?

## Status
In Progress — research plan created, awaiting analysis.

## Overview
The Fitness Browser's 559 metal experiments predominantly use chloride salts. At high concentrations (e.g., 250 mM CoCl₂ delivers 500 mM Cl⁻), the counter ion itself may cause significant fitness effects. This project leverages NaCl stress experiments available for most metal-tested organisms to decompose the metal fitness signal into a chloride component and a metal-specific component, then re-evaluates the Metal Fitness Atlas conclusions after correction.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources
- `kescience_fitnessbrowser` — NaCl stress experiments (17+ organisms with both NaCl and metal data)
- `projects/metal_fitness_atlas/data/` — metal experiment classifications, fitness scores, conservation stats
- `projects/fitness_modules/data/matrices/` — cached full fitness matrices
- `projects/fitness_modules/data/annotations/` — experiment metadata
- `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` — FB-to-pangenome gene mapping

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy

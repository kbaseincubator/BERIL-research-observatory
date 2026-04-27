# Gene-Resolution Metal Cross-Resistance Across Diverse Bacteria

## Research Question
Is the genetic architecture of metal cross-resistance conserved across phylogenetically diverse bacteria, or is it rewired species by species?

## Status
In Progress — research plan created, awaiting analysis.

## Overview
The literature treats metal cross-resistance as a binary property of strains (e.g., "Co-Ni cross-resistant"), inferred from MIC assays on a handful of model organisms. We have genome-wide RB-TnSeq fitness data across 30 organisms and up to 13 metals — enabling the first gene-resolution cross-resistance analysis. For each organism, we correlate gene fitness profiles between all metal pairs to build a metal × metal cross-resistance matrix, then test whether these matrices are conserved across organisms (universal chemistry) or rewired per species (organism-specific). We decompose genes into a three-tier architecture (general stress > metal-shared > metal-specific) and predict that shared genes are more core in the pangenome. Finally, we use conserved cross-resistance signatures to predict multi-metal tolerance across 27K species and validate against BacDive isolation environments.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources
- **Fitness Browser**: 422 metal experiments, 37 organisms, 13 metals (Al, Cd, Co, Cr, Cu, Fe, Hg, Mn, Mo, Ni, Se, U, W, Zn)
- **Metal Fitness Atlas** (this observatory): metal-important gene lists, conserved metal families
- **Metal Specificity** (this observatory): metal-specific vs pleiotropic gene classification
- **Counter Ion Effects** (this observatory): DvH metal-NaCl correlation hierarchy
- **Essential Genome** (this observatory): ortholog groups, pangenome conservation
- **BacDive**: isolation environment metadata for validation

## Reproduction
*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors
- Paramvir S. Dehal (https://orcid.org/0000-0001-5810-2497), Lawrence Berkeley National Laboratory

# Prophage-AMR Co-mobilization Atlas

## Research Question

At pangenome scale (293K genomes, 27K species), are antibiotic resistance genes preferentially located within or adjacent to prophage regions, and does this co-localization predict AMR gene mobility and accessory-genome status?

## Status

In Progress — research plan created, awaiting analysis.

## Overview

Five completed AMR projects characterized resistance gene distribution, conservation, fitness costs, and environmental patterns. Separately, the prophage_ecology project mapped prophage distribution across phylogeny. This project connects the two: testing whether AMR genes near prophage markers are more likely to be accessory (mobile) and whether prophage-rich species have broader AMR repertoires. Uses `bakta_amr` for curated AMR hits, `bakta_annotations` product-field keywords for prophage marker detection, and gene coordinate proximity for co-localization scoring.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Data Sources

- `kbase_ke_pangenome.bakta_amr` — 83K AMR gene clusters (AMRFinderPlus via Bakta)
- `kbase_ke_pangenome.bakta_annotations` — 132M gene cluster annotations (product-field prophage keywords)
- `kbase_ke_pangenome.gene_cluster` — core/accessory status, species membership
- `kbase_ke_pangenome.gene` — gene coordinates for neighborhood analysis
- `kbase_ke_pangenome.pangenome` — species-level summary statistics
- `kescience_fitnessbrowser` — fitness costs for ~30 organisms (cross-validation)
- Completed project data: `amr_pangenome_atlas`, `amr_strain_variation`, `prophage_ecology`

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

- Justin Reese, Lawrence Berkeley National Laboratory (ORCID: 0000-0002-2170-2250)
- Claude (AI co-scientist, Anthropic)

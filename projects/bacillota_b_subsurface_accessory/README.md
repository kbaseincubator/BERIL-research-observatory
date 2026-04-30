# Subsurface Bacillota_B Specialization

## Research Question

Within the Bacillota_B phylum (Desulfosporosinus, BRH-c8a Peptococcaceae, BRH-c4a Desulfotomaculales, and other obligate-anaerobe deep-subsurface Firmicutes), what accessory gene content distinguishes deep-clay-isolated genomes from phylum-matched soil-baseline genomes? Beyond the curated marker dictionary used in `clay_confined_subsurface` (which mostly tested Wood–Ljungdahl, [NiFe]-hydrogenase, dsr-apr-sat — and whose IR-side markers turned out to be wrong genes), what does the BERDL pangenome gene-cluster–level signal say about subsurface adaptation in this phylum?

## Status

In Progress — research plan written; cohort assembly (NB01) is the next step.

## Overview

The companion `clay_confined_subsurface` project (PR #227, merged) found that within Bacillota_B (after phylum control), 5/5 deep-clay isolates carry sulfate reduction vs 4/19 soil-baseline (p_BH=0.04) — the only result that survived phylum-stratified testing. Bacillota_B is exactly Bagnoud 2016's recurrent indigenous Mont Terri lineage. The natural follow-up is gene-cluster–level: what *else* distinguishes these subsurface specialists from their soil congeners? We extend the clay project's framework from a curated 18-marker dictionary to the full BERDL pangenome accessory-genome of Bacillota_B, using eggNOG OGs as the cross-species orthology surrogate. We also use this as the venue for **correcting the clay project's H3 IR-side analysis**, which used three KO numbers (K07811, K17324, K17323) that turn out to be TMAO reductase, glycerol ABC, and glycerol permease — not iron-reduction markers. The correction (Phase 1) replaces those with PFAM PF14537 multi-heme cytochrome detection + heme-binding motif counting and re-runs the clay H3 test.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses (H1 accessory operons, H2 compactness, H3 corrected iron-reduction), cohort definition, query strategy, analysis plan
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)
- [References](references.md) — annotated bibliography (TBD)
- Predecessors: [`clay_confined_subsurface`](../clay_confined_subsurface/) (PR #231 framework + IR correction target), [`oak_ridge_cultivation_gap`](../oak_ridge_cultivation_gap/) (annotation pipeline)

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase

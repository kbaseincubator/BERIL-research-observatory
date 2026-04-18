# Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

## Research Question

Can we predict bacterial growth phenotype — at multiple resolutions from binary growth through continuous kinetics to complex dynamics — from genome content and growth condition, in a way where the predictive features are biologically interpretable, validated against independent fitness data, and actionable for rational experimental design at a contaminated field site?

## Status

**In Progress** — Act I complete (NB00-NB04). Act I synthesis in [Report](REPORT.md). Starting Act II (feature engineering, variance partitioning, modeling).

## Context

This project sits within the **ENIGMA SFA**, which studies microbial community assembly and function in the contaminated subsurface at the **Oak Ridge Y-12 field site**. Legacy uranium extraction created contamination plumes high in uranium, heavy metals, and nitrate (which lowers pH) in fractured shale aquifers. Carbon availability is low — simple substrates are consumed rapidly from flowing necromass, leaving complex carbon for specialists. Understanding which strains grow on which substrates, how quickly, and what they produce is directly relevant to predicting field-scale community dynamics.

## Overview

The project sits at a unique convergence of five datasets for the same Oak Ridge field isolates:

| Dataset | Scale | What it provides |
|---|---|---|
| **ENIGMA growth curves** | 303 plates, 27,632 curves, 123 strains, 195 molecules | Continuous growth phenotype (lag, µmax, max OD, AUC, diauxy) |
| **ENIGMA Genome Depot** | 3,110 genomes, 3.7M KO, 6.4M COG, 29.4M OG annotations | Pre-computed genome features for all 123 growth strains |
| **Fitness Browser** | 7 matching strains, 27M fitness scores | Independent gene-level validation of predictor features |
| **Web of Microbes** | 6 matching strains, 105 metabolites each | Exometabolomic ground truth |
| **Carbon source phenotypes** | 795 genomes × 379 conditions = ~53K binary labels | Broad pretraining corpus (Dileep et al., preprint) |

The project is structured in three acts:

**Act I — Know the Collection (NB01-NB04)**:
- NB01 [done]: Growth curve fitting (27,632 curves, modified Gompertz, QC flags)
- NB02: Condition canonicalization and cross-dataset alignment (ChEBI-based)
- NB03: Functional diversity census (phylogeny, metabolic guilds, resistance/motility/mobile elements, pangenome outliers)
- NB04: Environmental context and biogeography (pangenome species-level via `ncbi_env`, microbeatlas global 16S, CORAL local Oak Ridge, SparCC co-occurrence)

**Act II — Predict and Explain (NB05-NB08)**:
- NB05 [done]: Feature engineering (4,305 prevalence-filtered KOs, 4 feature levels, no PCA)
- NB06: GBDT variance partitioning + SHAP + FB concordance (nested M0→M3, the central analytical notebook)
- NB07: CSP transfer learning (pretrain on 795-genome corpus, fine-tune on ENIGMA)
- NB08: WoM exometabolomic prediction (pilot, 6 strains)

**Act III — Diagnose and Propose (NB10-NB11)**:
- NB10: Conflict detection and counterfactuals
- NB11: Active learning proposal (next 200 experiments for ENIGMA)

## Six Hypotheses

1. **H1**: Feature resolution must match phenotype resolution (pathways for binary growth, KOs for kinetics, regulatory proxies for complex dynamics)
2. **H2**: GapMind, CUB/gRodon, and GBDT are complementary by condition class
3. **H3**: FB concordance is measurable and independent of held-out accuracy
4. **H4**: CSP pretraining transfers to ENIGMA continuous targets
5. **H5**: Growth-predictive features also predict exometabolomic output
6. **H6**: Active learning outperforms random experimental design

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, data sources, references
- [Report](REPORT.md) — Act I findings (6 key results, 22 figures)

## Anchor Strains (Tier 1)

| ENIGMA strain | FB orgId | WoM? | Curves | Species |
|---|---|---|---|---|
| FW300-N2E3 | `pseudo3_N2E3` | Yes | 454 | *P. fluorescens* |
| FW300-N2E2 | `pseudo6_N2E2` | — | 456 | *P. fluorescens* |
| FW300-N1B4 | `pseudo1_N1B4` | — | 360 | *P. fluorescens* |
| GW456-L13 | `pseudo13_GW456_L13` | Yes | 360 | *P. fluorescens* |
| GW460-11-11-14-LB5 | `Pedo557` | — | 362 | *Pedobacter sp.* |
| GW101-3H11 | `acidovorax_3H11` | — | 192 | *Acidovorax sp.* |
| FW507-4G11 | `Cup4G11` | — | 192 | *Cupriavidus basilensis* |

All 123 growth-curve strains have genome depot annotations (KO, COG, OG, EC, GO). 32 also have BERDL pangenome features (GapMind, UniRef, Pfam, ANI).

## Data Collections

This project integrates data from the following BERDL collections:

- `enigma_coral` — ENIGMA CORAL: growth curve bricks, strain metadata, ASV communities, GTDB-Tk taxonomy, isolation locations, geochemistry
- `enigma_genome_depot_enigma` — ENIGMA Genome Depot: 3,110 genomes with KO, COG, OG, EC, GO annotations
- `kescience_fitnessbrowser` — Fitness Browser: RB-TnSeq gene fitness for 7 anchor strains
- `kescience_webofmicrobes` — Web of Microbes: exometabolomics for 6 strains
- `globalusers_carbon_source_phenotypes` — Carbon source phenotypes: 795 genomes x 379 binary growth labels (Dileep et al.)
- `kbase_ke_pangenome` — KBase pangenome: species-level biogeography via ncbi_env, GapMind pathways
- `arkinlab_microbeatlas` — Microbial Atlas: 464K global 16S samples for genus-level biogeography and co-occurrence

## Reproduction

*TBD — prerequisites and step-by-step instructions will be added after Act II is complete.*

## Authors

- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory

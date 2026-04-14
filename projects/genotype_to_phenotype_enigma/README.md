# Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

## Research Question

Given a bacterial strain's genome and a defined growth condition (carbon source, metal, antibiotic, pH, ...), can we predict its quantitative growth phenotype in a way that is biologically interpretable, mechanistically grounded, and validated against independent fitness data?

## Status

**In Progress** — research plan written (2026-04-14), awaiting growth curve parsing and fitting (NB01).

## Overview

The ENIGMA SFA recently uploaded ~303 plates of high-throughput growth curves to the BERDL lakehouse (`enigma_coral.ddt_brick*`, bricks 928–1230), covering 88 Oak Ridge field isolates under diverse media, carbon sources, metals, and antibiotics. Five of these strains have direct matches in the Fitness Browser RB-TnSeq dataset (*P. fluorescens* FW300-N1B4, FW300-N2E2, FW300-N2E3, GW456-L13; *Pedobacter* GW460-11-11-14-LB5), yielding a unique ground-truth cohort where strain genome, measured gene fitness under defined conditions, and measured growth parameters are all simultaneously available.

This project uses that ground-truth anchor set to compare three predictor paradigms — **GapMind pathway completeness** (rule-based), **FBA-lite** (mechanistic), and **gradient-boosted trees on genome features** (data-driven) — on multiple phenotype targets (growth y/n, lag, µmax, max OD, yield). A central contribution is defining *biological meaningfulness* as a measurable, separable property of a predictor: the fraction of its top-weighted features whose FB orthologs are fitness-significant under matched conditions. This lets us distinguish mechanistically grounded predictors from phylogeny-riding ones even when held-out accuracy is similar.

The project is structured in four phases:

1. **Foundation** (NB01–03): Growth curve parsing and fitting, condition canonicalization, coverage atlas.
2. **Baselines** (NB04–07): GapMind rule-based predictor, FBA-lite mechanistic predictor, GBDT data-driven predictor, feature engineering across multiple genome representations (UniRef, COG, KO, Pfam, GapMind, ModelSEED reactions, GC content, ribosomal/translational, regulatory proxies, defense/mobile load), phylogenetic controls via adversarial validation and mixed-effects models.
3. **Diagnosis** (NB08–10): Counterfactual and conflict detection, feature attribution via SHAP / flux variability / pathway weights, biological meaningfulness scoring via FB concordance.
4. **Active learning** (NB11, stretch): Ranked experimental proposal for ENIGMA's next round, scored by model disagreement × genotype-space novelty × meaningfulness-weighted coverage gain.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, query strategy, references
- [Report](REPORT.md) — findings, interpretation, supporting evidence *(pending)*

## Reproduction

*TBD — prerequisites and step-by-step instructions will be added after Phase 1 is complete.*

## Key Data Sources

- `enigma_coral.ddt_brick0000928`–`ddt_brick0001230` — 303 growth curve plates (~5M timepoint rows)
- `enigma_coral.sdt_strain`, `sdt_genome`, `sdt_condition` — strain and condition metadata
- `kescience_fitnessbrowser.*` — RB-TnSeq fitness data for 48 organisms, 27M scores
- `kbase_ke_pangenome.gapmind_pathways` — pathway completeness predictions
- `kbase_ke_pangenome.eggnog_mapper_annotations`, `bakta_annotations`, `bakta_pfam_domains`, `genomad_mobile_elements` — genome feature sources
- `kbase_msd_biochemistry.reaction`, `compound` — ModelSEED biochemistry for FBA-lite
- `kbase_ke_pangenome.gtdb_metadata`, `gtdb_taxonomy_r214v1`, `genome_ani` — phylogenetic controls

## Anchor Strains (ENIGMA × Fitness Browser direct matches)

| ENIGMA strain | FB orgId | Species |
|---|---|---|
| FW300-N1B4 | `pseudo1_N1B4` | *P. fluorescens* |
| FW300-N2E2 | `pseudo6_N2E2` | *P. fluorescens* |
| FW300-N2E3 | `pseudo3_N2E3` | *P. fluorescens* (previously characterized in `fw300_metabolic_consistency`) |
| GW456-L13 | `pseudo13_GW456_L13` | *P. fluorescens* |
| GW460-11-11-14-LB5 | `Pedo557` | *Pedobacter sp.* |

Additional strains with shared GTDB species (but distinct FB orgId) extend the effective training set.

## Authors

- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory

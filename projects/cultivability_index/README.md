# Metabolic Self-Sufficiency Index — Predicting Cultivability from Pangenome Pathway Completeness

## Research Question
Can metabolic self-sufficiency, measured as the completeness of GapMind-annotated amino acid biosynthesis and carbon utilization pathways across a genome, predict which uncultured species in the BERDL `kbase_ke_pangenome` are most likely to be cultivable in pure culture?

## Status
Reviewed — REVIEW_1.md drafted; awaiting /submit.

## Overview
The cultured fraction of the bacterial pangenome is small (<1% of GTDB families have any isolate) and ecologically biased — `clay_confined_subsurface` and `oak_ridge_cultivation_gap` demonstrated that cultured isolates misrepresent native community composition. A practical question for experimentalists is which uncultured genomes are tractable targets for cultivation.

Across 235,671 HQ-filtered BERDL genomes (CheckM ≥ 95%, contam ≤ 5%; 208K isolates, 27.6K MAGs/SAGs/env), we tested whether per-genome GapMind pathway completeness predicts isolate-vs-MAG status with family-stratified leave-out validation across 183 dual-labeled GTDB families. 71 of 80 pathways show significant family-controlled differential completeness; a held-out-family L1-LR classifier reaches AUC = 0.748 on pathway features alone, AUC = 0.897 with `checkm + size + gc + n50` covariates. Independent validation on 25 phyla and on subsurface-tagged genomes (a proxy for the Mont Terri / Oak Ridge / Rifle cohorts) recapitulates the cultivation gap.

A striking biological reversal emerges: **carbon utilization pathways are isolate-predictive (positive coefficients) but most amino-acid biosynthesis pathways are MAG-predictive (negative coefficients)**. Lab cultivation media supplement amino acids, so auxotrophic isolates survive cultivation, while MAGs from oligotrophic environments retain AA biosynthesis. The deliverable is a 256-MAG strict candidate list of uncultured GTDB genera in cultivated families, ranked by P(isolate), with the Bacteroidota family Saprospiraceae as the dominant S-tier source.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence
- [Candidate list (strict)](data/cultivability_candidates_strict.tsv) — 256 uncultured-genus MAGs ranked by P(isolate)

## Reproduction
1. **Environment**: BERDL on-cluster JupyterHub or off-cluster via the standard BERIL bootstrap (`scripts/bootstrap_client.sh` + SSH tunnels). `KBASE_AUTH_TOKEN` must be set.
2. **Install**: `pip install -r requirements.txt`. Reuses `berdl_notebook_utils`.
3. **Build the feature matrix**: `python src/build_features.py` writes `data/features.parquet` (~40s on-cluster).
4. **Univariate signal**: `python src/univariate_signal.py` produces `data/per_pathway_or.tsv`.
5. **Train classifier**: `python src/train_model.py` produces `data/model_metrics.tsv`, `data/model_coefficients.tsv`, `data/scored_genomes.parquet`.
6. **Rank candidates**: `python src/rank_candidates.py` produces both candidate lists.
7. **Validate**: `python src/validate_anchored.py` produces per-phylum validation tables and figures.
8. **Figures**: `python src/make_nb02_figures.py` and `src/make_nb03_figures.py` (also called inside step 7).

The notebooks (`notebooks/0[0-5]_*.ipynb`) provide narrative wrappers around the scripts; the scripts are the canonical execution path for reproducibility.

## Data Collections

This project queries the `kbase_ke_pangenome` collection — see the [Data Collections](https://berdl.kbase.us/collections/kbase_ke_pangenome) page for citation and attribution. Tables: `gapmind_pathways`, `gtdb_metadata`, `gtdb_taxonomy_r214v1`, `genome`.

## Authors
- Justin Reese (LBL) — ORCID: 0000-0002-2170-2250

# Subsurface Bacillota_B Specialization

## Research Question

Within the Bacillota_B phylum (Desulfosporosinus, BRH-c8a Peptococcaceae, BRH-c4a Desulfotomaculales, and other obligate-anaerobe deep-subsurface Firmicutes), what accessory gene content distinguishes deep-clay-isolated genomes from phylum-matched soil-baseline genomes? Beyond the curated marker dictionary used in `clay_confined_subsurface` (which mostly tested Wood–Ljungdahl, [NiFe]-hydrogenase, dsr-apr-sat — and whose IR-side markers turned out to be wrong genes), what does the BERDL pangenome gene-cluster–level signal say about subsurface adaptation in this phylum?

## Status

Complete — see [Report](REPORT.md) for findings.

**Headline**: H1 strongly supported (547 anchor-enriched eggNOG OGs falling into all 5 pre-registered functional categories). H2 not supported — opposite direction (anchor 35% LARGER, not smaller; +1.4 SD on genome size, p≤0.025), consistent with Beaver & Neufeld 2024 self-sufficiency. Phase 1 clay correction shows the original H3 IR-side analysis was artefactual (mismatched KOs) — corrected multi-heme cytochrome detection finds no significant cohort difference; clay project's SR-side H3 stands but IR-side narrative needs withdrawal.

## Overview

The companion `clay_confined_subsurface` project (PR #227, merged) found that within Bacillota_B (after phylum control), 5/5 deep-clay isolates carry sulfate reduction vs 4/19 soil-baseline (p_BH=0.04) — the only result that survived phylum-stratified testing. Bacillota_B is exactly Bagnoud 2016's recurrent indigenous Mont Terri lineage. The natural follow-up is gene-cluster–level: what *else* distinguishes these subsurface specialists from their soil congeners? We extend the clay project's framework from a curated 18-marker dictionary to the full BERDL pangenome accessory-genome of Bacillota_B, using eggNOG OGs as the cross-species orthology surrogate. We also use this as the venue for **correcting the clay project's H3 IR-side analysis**, which used three KO numbers (K07811, K17324, K17323) that turn out to be TMAO reductase, glycerol ABC, and glycerol permease — not iron-reduction markers. The correction (Phase 1) replaces those with PFAM PF14537 multi-heme cytochrome detection + heme-binding motif counting and re-runs the clay H3 test.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses (H1 accessory operons, H2 compactness, H3 corrected iron-reduction), cohort definition, query strategy, analysis plan
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)
- [References](references.md) — annotated bibliography (TBD)
- Predecessors: [`clay_confined_subsurface`](../clay_confined_subsurface/) (PR #231 framework + IR correction target), [`oak_ridge_cultivation_gap`](../oak_ridge_cultivation_gap/) (annotation pipeline)

## Reproduction

### Prerequisites
- Python 3.10+ with `pandas`, `numpy`, `pyarrow`, `scipy`, `statsmodels`, `matplotlib`
- BERDL JupyterHub access (`berdl_notebook_utils.setup_spark_session.get_spark_session`) for NB01–04, NB06 (Spark queries against `kbase_ke_pangenome`)
- `KBASE_AUTH_TOKEN` set in repo `.env`
- Companion data from `clay_confined_subsurface/data/` (genome_features.parquet, baseline_features.parquet) for NB06 IR correction

### Steps
```bash
cd projects/bacillota_b_subsurface_accessory

# Spark-dependent (run on BERDL JupyterHub)
jupyter nbconvert --to notebook --execute --inplace notebooks/01_cohort_assembly.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_og_presence.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/04_og_annotation.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/06_clay_h3_correction.ipynb

# Local pandas/scipy
jupyter nbconvert --to notebook --execute --inplace notebooks/03_og_enrichment.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/05_h2_compactness.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/07_synthesis.ipynb
```
NB01 ≈ 5 min, NB02 ≈ 10–15 min (1B-row gene/junction join), NB03 ≈ 1 min, NB04 ≈ 5 min, NB05 ≈ 30 sec, NB06 ≈ 10–15 min (CXXCH motif scan on ~190-genome cluster faa_sequences in Spark), NB07 ≈ 30 sec.

### Data Collections

This project draws from `kbase_ke_pangenome` (gene clusters, eggNOG annotations, bakta annotations + PFAM domains, protein sequences) and `kescience_bacdive` (clay-strain expansion). Companion project: [`clay_confined_subsurface`](../clay_confined_subsurface/).

## Authors

David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase

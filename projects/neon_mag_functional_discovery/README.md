# NEON Metagenome Lineage Novelty and Functional Ecology

## Research Question

Across the three NEON metagenome studies in NMDC (soil, surface water, benthic sediment), (1) where does lineage novelty (GTDB-uncalled or genus-only MAGs) concentrate along habitat and soil-chemistry gradients, (2) which KOs and Pfams discriminate habitats or track measured soil chemistry (pH, C:N, organic carbon, horizon), and (3) for the subset of NEON MAG genera that overlap the KBase KE pangenome, do environmental MAG accessory genomes carry KOs absent from cultured representatives of the same genus?

## Status

**Planning** — discovery queries complete, scope locked, scaffold ready. Next: NB01 sample-design extraction.

## Overview

Uses BERDL's `nmdc_metadata`, `nmdc_results`, and `kbase_ke_pangenome` collections to do three linked analyses anchored on three NMDC studies that re-host NEON metagenomic data:

| Study | Habitat | NEON product | Biosamples | MAGs (MQ+HQ) | Annotation workflows |
|---|---|---|---|---|---|
| `nmdc:sty-11-34xj1150` | Soil | DP1.10107.001 | 6,489 | 1,177 | 1,895 |
| `nmdc:sty-11-hht5sb92` | Surface water | DP1.20281.001 | 234 | 110 | 102 |
| `nmdc:sty-11-pzmd0x14` | Benthic sediment | DP1.20279.001 | 736 | 322 | 645 |

Per-sample functional content comes from `nmdc_metadata.functional_annotation_agg` (KO/COG/Pfam counts per metagenome workflow, ~27M annotation rows for NEON). MAG taxonomy comes from `nmdc_metadata.workflow_execution_set_mags_list` (GTDB-Tk classifications at all ranks plus completeness/contamination). Pangenome contrast uses genus-level joins to `kbase_ke_pangenome.gtdb_species_clade` and downstream gene-cluster tables.

## Data

Discovery-phase facts that bound the analysis (see `data/discovery_summary.md`):

- **Metagenomics-only**: no metaT/metaP/metabolomics/lipidomics/NOM for any NEON study in NMDC. Multi-omics framing is not viable.
- **Soil chemistry is rich**: pH (97%), temp (97%), water_content (84%), soil_horizon (100%), C:N/org_carb/NH4-N (21–32%). Water has temp/conductivity/dissolved-oxygen. Benthic has only coordinates and env-scale terms.
- **MAGs are dominated by novel lineages**: ~75% of soil MAGs are LQ; among MQ+HQ, soil has 40 archaea and 1,137 bacteria. Eukaryotic MAGs (14 credible total) too few for a cross-domain claim. Project focuses on bacteria (workhorse) with archaea as a soil sub-question.
- **Pangenome linkage at genus level**: 249 of 412 NEON MAG genera (60%) have at least one KE pangenome representative, including environmental groups (Palsa-295, Bog-1198, Sulfotelmatobacter), not only clinical genera.

## Data Collections

- `nmdc_metadata` (NMDC tenant) — biosamples, data generation, workflow executions, MAG lists, functional annotation aggregate
- `nmdc_results` (NMDC tenant) — gtdbtk_bacterial_summary, checkm_statistics (per-gene annotation tables exist but are billion-row scale; used only for targeted gene hunts)
- `kbase_ke_pangenome` (KBase tenant) — gtdb_species_clade, gene_cluster, eggnog_mapper_annotations for accessory-genome comparison

Explicitly **not used**: `nmdc_arkin` _gold tables (no NEON coverage); external NEON portal data (climate stations, eddy covariance, vegetation surveys).

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, query strategy, pitfalls
- [Discovery Summary](data/discovery_summary.md) — what the probe queries returned

## Reproduction

**Prerequisites**:
- BERDL JupyterHub access with `nmdc` and `kbase` tenant read permissions
- Python 3.10+, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`

**Steps** (planned):
1. `01_discovery_and_sample_design.ipynb` — reproduce the discovery queries from the planning session; emit `data/biosample_field_coverage.tsv`, `data/sample_inventory.tsv`, `data/mag_inventory.tsv`.
2. `02_lineage_novelty_map.ipynb` — MAG taxonomic-rank-of-classification × habitat × (soil chemistry bin where applicable).
3. `03_sample_functional_profiles.ipynb` — sample × KO matrix from `functional_annotation_agg`; habitat- and chemistry-discriminating functions.
4. `04_pangenome_accessory_contrast.ipynb` — for overlapping genera, NEON-MAG vs KE-pangenome accessory KO sets.
5. `05_synthesis.ipynb` — figures and discovery candidate table.

**Note**: `data/*.tsv*` files (except `discovery_summary.md`) are gitignored; only notebooks, plan, figures, and small summary artifacts are committed.

## Authors

- Chris Mungall, LBNL, ORCID [0000-0002-6601-2165](https://orcid.org/0000-0002-6601-2165)

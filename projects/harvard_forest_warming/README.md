# Harvard Forest Long-Term Warming — DNA vs RNA Functional Response

## Research Question

After ~25 years of +5°C experimental soil warming at the Harvard Forest Barre Woods plot, does the functional transcript pool (metatranscriptome KO/Pfam composition) diverge from the genome pool (metagenome KO/Pfam composition) more strongly than expected from neutral community turnover, and which functional categories drive any divergence?

## Status

**Complete** — see [REPORT.md](REPORT.md) for findings. Pending automated review via `/submit`.

## Overview

Tests three linked hypotheses on NMDC study `nmdc:sty-11-8ws97026` (Blanchard lab, Barre Woods, Harvard Forest, USA): (H1) the transcript-pool functional profile diverges more between heated and control than the genome-pool profile; (H2) carbon-degradation KOs are enriched in heated metatranscriptomes consistent with published respiration-acceleration findings; (H3) organic and mineral horizons respond differently to warming. Uses 42 biosamples × 5 omics layers from the `nmdc_metadata` and `nmdc_results` tables in BERDL.

## Data

- **Source**: NMDC study `nmdc:sty-11-8ws97026` ("Molecular mechanisms underlying changes in the temperature sensitive respiration response of forest soils to long-term experimental warming")
- **PI**: Jeffrey Blanchard, U. Massachusetts Amherst
- **Site**: Barre Woods, Petersham, MA, USA (42.481 °N, −72.178 °W)
- **Treatment**: Heated (+5°C, ~25 years) vs Control
- **Horizons**: Organic (0–0.02 m) vs Mineral (0.02–0.10 m)
- **Sample count**: 42 biosamples
- **Layers used**: metagenome KO/Pfam, metatranscriptome KO, kraken2 read taxonomy, GTDB MAG taxonomy, ChEBI metabolite identifications

All data accessed via Spark SQL against the BERDL Lakehouse `nmdc` tenant. **Excluded**: `nmdc_arkin` tables.

## Data Collections

- `nmdc` — NMDC `nmdc_metadata` and `nmdc_results` tables in the BERDL Lakehouse

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (after analysis)

## Reproduction

**Prerequisites**:
- BERDL JupyterHub access with `nmdc` tenant read permissions
- Python 3.10+, `pandas`, `numpy`, `scipy`, `matplotlib` (all in default JupyterHub kernel)
- The curated `user_data/c_cycling_kos.tsv` is committed to the repo

**Steps**:
1. Open this project on the BERDL JupyterHub.
2. Run notebooks in order:
   - `01_sample_design.ipynb` — produces `data/sample_design.tsv` and `data/workflow_runs.tsv`.
   - `02_extract_features.ipynb` — heavy Spark extraction (~5-10 min). Produces 5 feature TSVs in `data/`.
   - `03_community_composition.ipynb` — kraken2 PERMANOVA + per-phylum tests.
   - `04_dna_vs_rna_divergence.ipynb` — paired DNA∩RNA PERMANOVA (H1).
   - `05_c_cycling_enrichment.ipynb` — H2 + H1 sensitivity check (no incubation confound).
   - `06_horizon_interaction.ipynb` — H3 horizon × warming interaction.
   - `07_metabolite_view.ipynb` — bonus ChEBI Fisher tests.
   - `08_synthesis.ipynb` — final summary figure.
3. Total runtime: ~15-20 min on JupyterHub.

**Note**: All `data/*.tsv*` files are gitignored (regenerable). The committed inputs are the notebooks, the synthesis figure, the curated `c_cycling_kos.tsv`, and `RESEARCH_PLAN.md` / `REPORT.md`.

## Authors

- Chris Mungall, LBNL, ORCID [0000-0002-6601-2165](https://orcid.org/0000-0002-6601-2165)

# Self-Sufficiency, Anaerobic Toolkit, and Cultivation Bias in Clay-Confined Cultured Bacterial Genomes

## Research Question

Do BERDL's cultured bacterial genomes from clay-confined deep-subsurface environments recapitulate the genomic signatures the recent literature has identified — biosynthetic self-sufficiency (Beaver & Neufeld 2024; Becraft 2021), the H₂-driven anaerobic chemolithoautotrophy toolkit (Wood–Ljungdahl + group 1 [NiFe]-hydrogenase + dissimilatory sulfate reduction, per Bagnoud 2016), and a cultivation-driven porewater-vs-rock-attached signature dichotomy (Bagnoud 2016 vs Mitzscherling 2023) — relative to surface soil microbes?

## Status

Complete — see [Report](REPORT.md) for findings.

**Headline**: H3 (porewater-bias) strongly supported (SR enrichment vs Mitzscherling rock-attached null p=4×10⁻¹²); H2 (anaerobic toolkit) partially supported — only sulfate reduction survives phylogenetic control (within-Bacillota_B p_BH=0.04); H1 (self-sufficiency) not supported — cultivation bias means BERDL's cohort omits the *Ca.* Desulforudis audaxviator-type extreme self-sufficient lineages the Beaver & Neufeld (2024) synthesis describes.

## Overview

Recent literature on the deep terrestrial subsurface (Beaver & Neufeld 2024 review; Bagnoud 2016 Mont Terri Opalinus; Mitzscherling 2023 Opalinus rock-attached communities; Engel 2019 Grimsel bentonite) generates testable predictions for what cultured bacterial genomes from clay-confined sites should encode: greater biosynthetic completeness ("self-sufficiency"), a recurring anaerobic-respiration toolkit, and — because cultivable porewater organisms differ qualitatively from rock-attached *Geobacter*/*Geothrix* lineages — a cultivation-driven porewater bias in any genome-resolved cohort. We test these predictions on the ~25–40 BERDL cultured genomes traceable to clay-confined origins (Mont Terri Opalinus boreholes, bentonite formations, kaolin lenses, BacDive deep-clay strains) versus a phylogenetically matched soil/sediment baseline drawn from the 5,151 species linked to soil biosamples in `kbase_ke_pangenome.ncbi_env`.

This project is the **genome-resolved** complement to [`enigma_sso_asv_ecology`](../enigma_sso_asv_ecology/), which characterized in-situ subsurface community structure via 16S ASVs at Oak Ridge.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, cohort definition, query strategy, analysis plan
- [References](references.md) — annotated bibliography (32 papers, 6 read in full)
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Reproduction

### Prerequisites

- Python 3.10+ with `pandas`, `numpy`, `pyarrow`, `scipy`, `statsmodels`, `seaborn`, `matplotlib`
- BERDL JupyterHub access (`berdl_notebook_utils.setup_spark_session.get_spark_session`) for NB01–03 (Spark queries)
- `KBASE_AUTH_TOKEN` set in repo `.env`

### Steps

```bash
cd projects/clay_confined_subsurface

# Spark-dependent (run on BERDL JupyterHub or with proxy chain)
jupyter nbconvert --to notebook --execute --inplace notebooks/01_cohort_assembly.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_genome_features.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_soil_baseline.ipynb

# Local-only (read parquet outputs from above)
jupyter nbconvert --to notebook --execute --inplace notebooks/04_h1_self_sufficiency.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/05_h2_anaerobic_toolkit.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/06_h3_porewater_bias.ipynb
```

NB01 takes ~2 min; NB02–03 take ~5–15 min each (1B-row gene/junction joins filtered to cohort genomes); NB04–06 are local pandas/scipy and run in seconds. Outputs land in `data/` (.tsv, .parquet) and `figures/` (.png).

### Data Collections

This project draws from `kbase_ke_pangenome` (NCBI env metadata, genome/taxonomy, gene clusters, eggNOG annotations, GapMind pathways).

## Authors

David Lyon (ORCID: [0000-0002-1927-3565](https://orcid.org/0000-0002-1927-3565)) — KBase

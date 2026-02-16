# Contamination Gradient vs Functional Potential in ENIGMA Communities

## Research Question

Do high-contamination Oak Ridge groundwater communities show enrichment for taxa with higher inferred stress-related functional potential compared with low-contamination communities?

## Status

Complete -- see [Report](REPORT.md) for synthesized findings from 108 overlap samples, strict-vs-relaxed mapping sensitivity, and model statistics.

## Overview

This project uses ENIGMA CORAL field data to test whether contamination gradients (uranium and co-occurring metals) are associated with shifts in inferred community functional potential. Functional potential is estimated by linking ENIGMA taxa to BERDL pangenome annotations and aggregating stress-relevant functional signals (COG defense/mobilome and related categories) at the site level. The analysis targets community-level ecological filtering rather than gene-level causality.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- hypothesis, query strategy, and analysis design
- [Report](REPORT.md) -- findings, interpretation, and limitations
- [Review](REVIEW.md) -- automated review feedback and prioritized improvements
- [References](references.md) -- key context for ENIGMA + BERIL analyses

## Reproduction

### Prerequisites
- BERDL JupyterHub environment with built-in `get_spark_session()`
- Python dependencies from `requirements.txt`

### Notebook execution order

```bash
cd projects/enigma_contamination_functional_potential

# Spark extraction and feature build (run on BERDL JupyterHub)
jupyter nbconvert --to notebook --execute --inplace notebooks/01_enigma_extraction_qc.ipynb --ExecutePreprocessor.timeout=7200
jupyter nbconvert --to notebook --execute --inplace notebooks/02_taxonomy_bridge_functional_features.ipynb --ExecutePreprocessor.timeout=7200

# Modeling/plotting (can run where the extracted TSV files are available)
jupyter nbconvert --to notebook --execute --inplace notebooks/03_contamination_functional_models.ipynb --ExecutePreprocessor.timeout=7200
```

### Expected outputs
- `data/geochemistry_sample_matrix.tsv`
- `data/community_taxon_counts.tsv`
- `data/sample_location_metadata.tsv`
- `data/taxon_bridge.tsv`
- `data/taxon_functional_features.tsv`
- `data/site_functional_scores.tsv`
- `data/model_results.tsv`
- `figures/contamination_vs_functional_score.png`
- `figures/contamination_index_distribution.png`
- `figures/mapping_coverage_by_mode.png`

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory

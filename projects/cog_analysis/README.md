# COG Functional Category Analysis

## Research Question

How do COG functional category distributions differ across core, auxiliary, and novel genes in bacterial pangenomes?

## Status

Completed — Universal functional partitioning discovered across 32 species and 9 phyla: novel genes enriched in mobile elements (+10.88%) and defense (+2.83%), core genes enriched in translation and metabolism.

## Overview

This project analyzes COG (Clusters of Orthologous Groups) functional category distributions across core, auxiliary, and singleton gene classes in bacterial pangenomes. Using annotations from the `eggnog_mapper_annotations` table and gene classifications from the `gene_cluster` table in BERDL, it reveals a remarkably consistent "two-speed genome" pattern that holds universally across bacterial phyla.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — Detailed hypothesis, approach, query strategy
- [Report](REPORT.md) — Findings, interpretation, supporting evidence

## Reproduction

**Prerequisites**: Run notebooks on the BERDL JupyterHub where Spark is available.

```bash
cd projects/cog_analysis/notebooks
jupyter notebook cog_analysis.ipynb
```

**Important**: All notebooks require Spark session initialization. Add this at the top of each notebook:
```python
from get_spark_session import get_spark_session
spark = get_spark_session()
```

Execute all cells. The notebook will:
- Query BERDL database directly using Spark SQL
- Save results to `../data/cog_distributions.csv`
- Generate visualizations in `../data/`

## Authors
- **Paramvir S. Dehal** (Lawrence Berkeley National Lab) | ORCID: 0000-0001-5810-2497 | Author

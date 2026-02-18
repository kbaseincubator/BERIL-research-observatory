# The Pan-Bacterial Essential Metabolome

## Research Question

Which biochemical reactions are universally essential across bacteria, and what does the essential metabolome reveal about the minimal core metabolism required for microbial life?

## Status

In Progress — research plan created, awaiting data extraction.

## Overview

This project links experimental gene essentiality data (from RB-TnSeq experiments across 48 bacterial organisms) to biochemical reactions in the ModelSEED database. By mapping universally essential gene families (identified in the `essential_genome` project) to their catalyzed reactions, we identify the core set of metabolic reactions required for bacterial life. This represents the first pan-bacterial experimental characterization of essential metabolism, bridging the gap between genetic essentiality and biochemical function.

**Key innovation**: Uses the new local BERDL workflow to test:
- MinIO data access (download existing essential gene data, upload results)
- Spark Connect queries from local machine (EC annotations, biochemistry reactions)
- Cross-database integration (Fitness Browser → Pangenome → Biochemistry)

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Data Sources

| Source | Purpose | Scale |
|--------|---------|-------|
| `projects/essential_genome/data/` | Universally essential gene families (859 families, 48 organisms) | Precomputed |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | EC numbers for gene clusters | 93M annotations |
| `kbase_msd_biochemistry.reaction` | Biochemical reactions | 56K reactions |
| `kbase_msd_biochemistry.reaction_ec` | EC → reaction mappings | Small |

## Project Structure

```
essential_metabolome/
├── README.md                    — This file
├── RESEARCH_PLAN.md             — Detailed research plan and hypotheses
├── REPORT.md                    — Findings and interpretation (TBD)
├── notebooks/
│   ├── 01_data_extraction.ipynb      — Map essential genes → EC → reactions (Spark Connect)
│   └── 02_metabolic_analysis.ipynb   — Pathway enrichment, network analysis, visualization
├── data/
│   ├── essential_gene_clusters.tsv   — Gene clusters in universal essential families
│   ├── essential_ec_numbers.tsv      — EC numbers from essential genes
│   ├── essential_reactions.tsv       — Reactions catalyzed by essential genes
│   ├── universal_essential_reactions.tsv — Reactions essential in all 48 organisms
│   ├── pathway_enrichment.tsv        — Statistical test results
│   └── reaction_properties.tsv       — Properties of essential vs non-essential reactions
├── figures/
│   ├── reaction_coverage.png         — Histogram of reaction prevalence
│   ├── pathway_enrichment.png        — Enriched pathways in essential reactions
│   ├── cofactor_dependency.png       — Cofactor usage patterns
│   └── network_centrality.png        — Network centrality distributions
└── requirements.txt             — Python dependencies
```

## Workflow Testing Goals

This project serves as a validation of the new local BERDL workflow:

**MinIO Operations**:
- ✅ Download essential gene data from lakehouse: `mc cp --recursive berdl-minio/.../essential_genome/data/ ./data/`
- ⏳ Upload project results: `python tools/lakehouse_upload.py essential_metabolome`

**Spark Connect Queries**:
- ⏳ Query eggNOG annotations for essential gene clusters
- ⏳ Join EC numbers to ModelSEED reactions
- ⏳ Extract reaction properties (reversibility, pathways, cofactors)

**Local Analysis**:
- ⏳ Pathway enrichment (Fisher's exact test, FDR correction)
- ⏳ Metabolic network analysis (betweenness centrality)
- ⏳ Visualization (matplotlib, seaborn)

## Reproduction

*Prerequisites and step-by-step instructions will be added after analysis is complete.*

**Requirements**:
- Python 3.10+
- `.venv-berdl` environment (see `scripts/bootstrap_client.sh`)
- `KBASE_AUTH_TOKEN` in `.env`
- BERDL proxy chain running (for Spark Connect queries)
- MinIO credentials (for data download/upload)

## Dependencies

See `requirements.txt` for full Python dependencies. Key packages:
- `pyspark` — Spark Connect client
- `pandas` — Data manipulation
- `scipy` — Statistical tests
- `matplotlib`, `seaborn` — Visualization
- `networkx` or `igraph` — Metabolic network analysis

## Authors

Paramvir Dehal (ORCID: 0000-0001-5810-2497, Lawrence Berkeley National Lab)

# The Pan-Bacterial Essential Metabolome

## Research Question

Which biochemical reactions are universally essential across bacteria, and what does the essential metabolome reveal about the minimal core metabolism required for microbial life?

## Status

Complete — pilot study analyzing 7 organisms with GapMind pathway data. See [Report](REPORT.md) for findings on amino acid biosynthesis conservation and *Desulfovibrio vulgaris* serine auxotrophy.

## Overview

This pilot study analyzes metabolic pathway completeness across 7 bacterial organisms with essential gene data using GapMind predictions from `kbase_ke_pangenome`. The analysis reveals **high conservation of amino acid biosynthesis pathways** (17/18 pathways present in all organisms) with one notable exception: *Desulfovibrio vulgaris* lacks serine biosynthesis, representing a potential metabolic auxotrophy.

**Key finding**: Near-universal amino acid prototrophy among free-living bacteria, with organism-specific gaps reflecting ecological adaptation.

**Limitation**: E. coli genomes are absent from the pangenome GapMind dataset (too many genomes for species-level analysis), limiting this to a 7-organism pilot study rather than the intended pan-bacterial survey.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (TBD)

## Data Sources

| Source | Purpose | Scale | Attribution |
|--------|---------|-------|-------------|
| `projects/essential_genome/` (lakehouse) | Universally essential gene families (859 families, 48 organisms) | 17K ortholog groups | Dehal (2026) |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | EC numbers for gene clusters | 93M annotations | BERDL |
| `kbase_msd_biochemistry.reaction` | Biochemical reactions | 56K reactions | ModelSEED |
| `kbase_msd_biochemistry.reaction_ec` | EC → reaction mappings | Small | ModelSEED |

**Note**: Essential gene family data is referenced from the lakehouse (`berdl-minio/.../microbialdiscoveryforge/projects/essential_genome/data/`) rather than copied locally. See `projects/essential_genome/` for the original analysis.

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

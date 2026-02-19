# Gene-Environment Association Across Pangenome Species

## Research Question

For species with strains isolated from diverse environments, do specific accessory gene clusters show significant over- or under-representation in particular environments? This provides generic infrastructure for linking pangenome gene content to NCBI biosample metadata via within-tenant (`ncbi_env`) and cross-tenant (`nmdc_ncbi_biosamples`) joins.

## Approach

1. **Environmental metadata pivot** (notebook 02): Transform the `ncbi_env` EAV table into per-genome environment categories (human_clinical, host_associated, soil, aquatic, plant_associated, food, engineered, sediment, air). Cross-tenant join with NMDC harmonized ontology labels.
2. **Gene-environment association** (notebook 03): For species with >=10 genomes in >=2 environment categories, test each accessory gene cluster for differential prevalence (Fisher's exact / chi-squared, BH FDR correction). Functional enrichment via COG categories.
3. **Methylobacterium descriptive analysis** (notebook 03, section 10): Genome-level MDH profile and B vitamin pathway completeness by environment. Descriptive only (sample sizes too small for formal testing).

## Data Sources

| Source | Database | Table(s) |
|--------|----------|----------|
| Genomes | `kbase_ke_pangenome` | `genome` |
| Environment (EAV) | `kbase_ke_pangenome` | `ncbi_env` |
| NCBI biosamples | `nmdc_ncbi_biosamples` | `biosamples_flattened`, `env_triads_flattened` |
| Gene clusters | `kbase_ke_pangenome` | `gene_cluster`, `gene`, `gene_genecluster_junction` |
| Annotations | `kbase_ke_pangenome` | `eggnog_mapper_annotations` |

## Notebooks

| Notebook | Purpose | Runtime |
|----------|---------|---------|
| `02_env_metadata_exploration.ipynb` | EAV pivot, cross-tenant NMDC join, environment categorization | ~10 min |
| `03_gene_environment_association.ipynb` | Species selection, statistical tests, COG enrichment, Methylobacterium descriptive analysis | ~3 hours (10 species) |

## Known Issues

- **Spark Connect auth timeout**: Sessions expire after ~40 minutes (KBaseAuthServerInterceptor). Notebook 03 includes `refresh_spark()` to restart the session between species.
- **Environment categorization gap**: "leaves" and "tree leaf surface" in `isolation_source` don't map to `plant_associated`; they fall into `other`.

## Intermediate Data

- `data/genome_env_metadata.csv` — per-genome environment metadata (292,913 genomes), produced by notebook 02 and consumed by notebook 03

## Reproduction

1. Upload notebooks to BERDL JupyterHub
2. Run in order: 02 -> 03 (notebook 03 depends on `data/genome_env_metadata.csv` from 02)
3. Both notebooks require Spark Connect

## Related Projects

- `mextorquens_pangenome_case/` — *M. extorquens* B vitamin auxotrophy and xoxF/mxaF case study (uses same annotation tables but no data dependency)
- `temporal_core_dynamics/` — Uses same `ncbi_env` EAV pivot pattern

## Authors

- **Mark A. Miller** (Lawrence Berkeley National Lab)

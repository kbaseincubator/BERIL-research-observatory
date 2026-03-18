# Within-Species AMR Strain Variation

Strain-level analysis of AMR gene variation across 1,305 bacterial species and 180,025 genomes.
Extends the AMR Pangenome Atlas (species-level) to within-species resolution.

## Status

Complete — see [Report](REPORT.md) for findings.

## Research Question

Within a species, how does the AMR repertoire vary between strains, and what drives that variation?

## Questions

1. How does the AMR repertoire vary between strains within a species?
2. Do AMR genes co-occur in resistance islands?
3. Does phylogeny or ecology better predict AMR profile?
4. Are there distinct AMR ecotypes within clinically important species?
5. Are AMR repertoires expanding over time?

## Key Findings

- **51% of AMR genes are rare** within any given species; median Jaccard diversity = 0.435
- **1,517 resistance islands** in 54% of species (mean phi = 0.827, 88% multi-mechanism)
- **56% of species** show significant phylogenetic signal in AMR (Mantel test, FDR < 0.05)
- **Acquired AMR tracks phylogeny more than intrinsic** (r=0.222 vs 0.117, p=7e-16)
- **20% of species** form distinct AMR ecotypes (silhouette 0.620)
- **Host-associated species** carry more AMR genes than environmental species

## Data Collections

- `kbase_ke_pangenome` — KBase pangenome resource (gene, genome, genome_ani, ncbi_env)

## Notebooks

| # | Name | Compute | Time | Description |
|---|------|---------|------|-------------|
| 01 | Data Extraction | Spark | 12.4h | Genome x AMR presence/absence matrices + metadata |
| 02 | Variation Metrics | Local | 5m | Fixed/variable/rare classification, diversity indices |
| 03 | Co-occurrence | Local | 20m | Phi coefficients, resistance island detection |
| 04 | Phylogenetic Signal | Spark+Local | 1.6h | ANI extraction, Mantel tests |
| 05 | AMR Ecotypes | Local | 30m | UMAP + DBSCAN clustering by AMR profile |
| 06 | Temporal + Environment | Local | 5m | Collection date trends, rule-based environment classification |
| 07 | Synthesis | Local | 1m | Publication figures, summary table |

## Data Dependencies

- `amr_pangenome_atlas/data/amr_census.csv` — AMR cluster x species mapping
- `amr_pangenome_atlas/data/amr_species_summary.csv` — species selection criteria
- BERDL tables: `kbase_ke_pangenome.gene`, `gene_genecluster_junction`, `genome`, `genome_ani`, `ncbi_env`

## Execution Order

```
NB01 (Spark) → NB02, NB03, NB05, NB06 (parallel, local)
NB04 (Spark) → NB04 Mantel (local)
All → NB07 (synthesis)
```

## Reproduction

**Requirements**: Install dependencies with `pip install -r requirements.txt`. For Spark notebooks, the BERDL environment also requires `spark_connect_remote` and `berdl_remote` (pre-installed on NERSC/BERDL).

**Sibling project dependency**: NB01 and NB02 require data from the `amr_pangenome_atlas` project at `../amr_pangenome_atlas/data/` (specifically `amr_census.csv` and `amr_species_summary.csv`). Ensure that project is present on the `projects/amr_pangenome_atlas` branch before running.

**Spark notebooks** (NB01, NB04): Require a live BERDL Spark session via `get_spark_session()` from the repository `scripts/` directory. These are long-running (12h and 1.6h respectively) and can be run headless via `scripts/run_nb01_extraction.py` and `scripts/run_nb04_phylogenetic.py`. NB04 caps ANI extraction at species with <=500 genomes for computational feasibility.

**Local notebooks** (NB02, NB03, NB05, NB06, NB07): Run from cached data in `data/` without Spark. Total runtime ~1h.

**Execution order**: NB01 first (produces `data/genome_amr_matrices/` and `data/genome_metadata.csv`), then NB02-NB06 in parallel, then NB04 (Spark ANI extraction + local Mantel tests), then NB07 (synthesis). Figures can be regenerated with `python scripts/generate_figures.py`.

## Authors

- Paramvir Dehal (LBNL)

# Lifestyle-Based COG Stratification

## Research Question

How does bacterial lifestyle (free-living vs host-associated) affect pangenome functional composition at the COG category level?

## Hypothesis

- **H0**: COG enrichment patterns in core vs accessory genes are independent of bacterial lifestyle
- **H1**: Host-associated bacteria show higher defense (V) enrichment in accessory genes; free-living bacteria show greater metabolic (E, G, C, P, I) diversity in accessory genes; host-associated bacteria have smaller core genome fractions

## Approach

1. Classify genomes by lifestyle using NCBI BioSample environmental metadata (`ncbi_env` table)
2. Aggregate to species-level lifestyle assignments
3. Compare COG functional enrichment patterns (core vs accessory) between lifestyle groups
4. Control for phylogeny by stratifying within phyla
5. Statistical testing with multiple comparison correction

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `ncbi_env` — Environmental metadata (EAV format, 4.1M rows)
  - `genome` — Genome metadata (293K rows)
  - `gene_cluster` — Core/accessory classification (132M rows)
  - `eggnog_mapper_annotations` — COG functional annotations (93M rows)
  - `pangenome` — Per-species pangenome statistics (27K rows)
  - `gtdb_species_clade` — Taxonomy (27K rows)

## Key Findings

*TBD -- run notebooks and use `/synthesize` to complete this section.*

## Notebooks

| Notebook | Purpose |
|----------|---------|
| [`01_data_exploration.ipynb`](notebooks/01_data_exploration.ipynb) | Assess ncbi_env coverage, build lifestyle classifier, identify target species |
| [`02_cog_enrichment.ipynb`](notebooks/02_cog_enrichment.ipynb) | COG enrichment analysis (core vs accessory) by lifestyle group, hypothesis tests |
| [`03_phylogenetic_controls.ipynb`](notebooks/03_phylogenetic_controls.ipynb) | Phylum-stratified controls, confounder analysis, publication figures |

## Visualizations

| Figure | Description |
|--------|-------------|
| *TBD* | |

## Data Files

| File | Description |
|------|-------------|
| `data/species_lifestyle_classification.csv` | Species-level lifestyle assignments |
| `data/cog_enrichment_by_lifestyle.csv` | COG enrichment scores by lifestyle group |

## Related Projects

- `projects/cog_analysis/` — COG functional category analysis (core vs accessory)
- `projects/pangenome_pathway_geography/` — Pangenome openness and biogeography

## Reproduction

1. Upload notebooks to BERDL JupyterHub
2. Run notebooks 01-03 in order
3. Outputs saved to `data/` and `figures/`

## Authors

*TBD*

## Future Directions

*TBD -- use `/synthesize` to complete this section.*

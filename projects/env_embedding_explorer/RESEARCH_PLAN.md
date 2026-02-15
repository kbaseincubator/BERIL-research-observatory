# Research Plan: AlphaEarth Embeddings, Geography & Environment Explorer

## Research Question

What do AlphaEarth environmental embeddings capture, and how do they relate to geographic coordinates and NCBI environment labels?

## Hypothesis

This is an exploratory/characterization project rather than a hypothesis-driven study. The guiding expectations are:
- **E1**: The 64-dim embedding space contains interpretable structure corresponding to major environment types (soil, marine, freshwater, host-associated)
- **E2**: A nontrivial fraction of lat/lon coordinates refer to institutional addresses rather than sampling sites
- **E3**: Geographic proximity correlates with embedding similarity, but environment type is a stronger predictor
- **E4**: Free-text NCBI environment labels are noisy but can be harmonized into ~15-20 meaningful categories

## Literature Context

AlphaEarth embeddings are derived from satellite imagery at genome sampling locations. They have been used in the `ecotype_analysis` project to test environment vs phylogeny effects on gene content (result: phylogeny usually dominates, median partial correlation 0.0025 for environment vs 0.0143 for phylogeny). However, the embedding space itself has not been characterized -- we don't know what the 64 dimensions represent, whether they cluster meaningfully, or how they relate to traditional environment metadata.

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `alphaearth_embeddings_all_years` | Embeddings + lat/lon + taxonomy | 83,287 | Full scan (small) |
| `ncbi_env` | Environment labels (EAV format) | 4,124,801 | Filter by accession IN (AlphaEarth biosample IDs) |
| `gtdb_metadata` | Assembly quality, isolation source | 293,059 | Filter by accession IN (AlphaEarth genome IDs) |

### Key Queries

1. **Full AlphaEarth extraction**:
```sql
SELECT * FROM kbase_ke_pangenome.alphaearth_embeddings_all_years
```

2. **NCBI env pivot for AlphaEarth genomes**:
```sql
SELECT accession,
       MAX(CASE WHEN harmonized_name = 'isolation_source' THEN content END) as isolation_source,
       MAX(CASE WHEN harmonized_name = 'geo_loc_name' THEN content END) as geo_loc_name,
       MAX(CASE WHEN harmonized_name = 'env_broad_scale' THEN content END) as env_broad_scale,
       MAX(CASE WHEN harmonized_name = 'env_local_scale' THEN content END) as env_local_scale,
       MAX(CASE WHEN harmonized_name = 'env_medium' THEN content END) as env_medium,
       MAX(CASE WHEN harmonized_name = 'host' THEN content END) as host
FROM kbase_ke_pangenome.ncbi_env
WHERE accession IN ({biosample_ids})
GROUP BY accession
```

3. **Attribute inventory**:
```sql
SELECT harmonized_name, COUNT(DISTINCT accession) as n_genomes
FROM kbase_ke_pangenome.ncbi_env
GROUP BY harmonized_name
ORDER BY n_genomes DESC
```

### Performance Plan
- **Tier**: JupyterHub (Spark) for extraction, local for visualization
- **Estimated complexity**: Simple -- all target tables are small (83K-293K rows)
- **Known pitfalls**: ncbi_env is EAV format (must pivot); string-typed columns may need CAST

## Analysis Plan

### Notebook 1: Data Extraction (JupyterHub)
- **Goal**: Extract and join AlphaEarth embeddings with NCBI environment labels
- **Expected output**: `data/alphaearth_with_env.csv`, `data/coverage_stats.csv`, `data/ncbi_env_attribute_counts.csv`, `data/isolation_source_raw_counts.csv`

### Notebook 2: Interactive Exploration (local or JupyterHub)
- **Goal**: Characterize embedding space, QC coordinates, harmonize labels, create interactive visualizations
- **Expected output**: Interactive plotly figures (UMAP scatter, geographic map, heatmaps), saved PNGs in `figures/`
- **Sections**:
  1. Coverage overview (UpSet plot)
  2. Coordinate QC (flag institutional addresses, integer-degree rounding, ocean non-marine)
  3. Environment label harmonization (keyword-based grouping of free-text to ~15-20 categories)
  4. UMAP of 64-dim embeddings colored by environment, phylum, coord quality
  5. Geographic map (plotly scattergeo)
  6. Embedding vs geography distance analysis
  7. Environment label vs embedding cluster cross-tabulation

## Expected Outcomes

- A characterized AlphaEarth embedding space with interpretable clusters
- A coordinate quality flag usable by downstream projects
- A harmonized environment category mapping reusable across the observatory
- Interactive visualizations for ongoing data exploration

## Revision History
- **v1** (2026-02-15): Initial plan

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory

# Research Plan: Gene-Environment Association Across Pangenome Species

## Research Question

For species with strains isolated from diverse environments, do specific accessory gene clusters show significant over- or under-representation in particular environments? This provides generic infrastructure for linking pangenome gene content to NCBI biosample metadata via within-tenant (`ncbi_env`) and cross-tenant (`nmdc_ncbi_biosamples`) joins.

## Hypothesis

- **H1 (Gene-environment associations exist)**: Accessory gene clusters are non-randomly distributed across environments -- specific genes are enriched in specific niches, reflecting ecological adaptation.
- **H2 (Mobilome drives niche adaptation)**: Environment-associated genes are enriched for mobile genetic element functions (COG category X), consistent with horizontal gene transfer as a driver of niche adaptation (Ochman et al., 2000; Brockhurst et al., 2019).
## Approach

### 1. Environmental Metadata Pivot (Notebook 02)
- Transform the `ncbi_env` EAV table into per-genome environment categories using keyword matching on `isolation_source`
- Categories: human_clinical, host_associated, soil, aquatic, plant_associated, food, engineered, sediment, air
- Cross-tenant join with `nmdc_ncbi_biosamples` for NMDC harmonized ontology labels
- Output: `genome_env_metadata.csv`

### 2. Gene-Environment Association (Notebook 03)
- Species selection: >=10 genomes in >=2 environment categories
- For each qualifying species, build presence/absence matrix of accessory gene clusters per genome
- Per-cluster statistical test: chi-squared (>2 categories) or Fisher's exact (2 categories)
- Multiple testing correction: Benjamini-Hochberg FDR, q < 0.05
- Functional enrichment: compare COG category distribution in significant vs background (sampled) clusters
- Proof of concept: *S. aureus* (12,906 genomes, 133,007 accessory clusters, 5 environment categories)

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `genome` - Genome metadata
  - `ncbi_env` - Environment metadata (EAV format with `isolation_source`)
  - `gene_cluster` - Gene cluster classifications
  - `gene` - Individual gene records
  - `gene_genecluster_junction` - Gene-to-cluster memberships
  - `eggnog_mapper_annotations` - Functional annotations (COG categories, EC, KEGG)
  - `gtdb_species_clade` - Species taxonomy
- **Cross-tenant**: `nmdc_ncbi_biosamples.biosamples_flattened`, `nmdc_ncbi_biosamples.env_triads_flattened`

## Expected Outputs

### Figures
- `env_metadata_coverage.png` - Environment category distribution across genomes
- `volcano_gene_env.png` - Prevalence difference vs q-value for S. aureus accessory clusters
- `cog_enrichment.png` - COG category enrichment in environment-associated vs background genes

### Data
- `genome_env_metadata.csv` - Per-genome environment metadata (292,913 genomes)
- `gene_env_summary.csv` - Cross-species summary of qualifying species
- `gene_env_Staphylococcus_aureus.csv` - Per-cluster association results for S. aureus

### Notebooks
- `02_env_metadata_exploration.ipynb` - EAV pivot, cross-tenant NMDC join (~10 min)
- `03_gene_environment_association.ipynb` - Species selection, statistical tests, COG enrichment (~30 min)

## Related Projects

- **listeria_pangenome_case** - *L. monocytogenes* pathway completeness case study using GapMind predictions
- **temporal_core_dynamics** - Uses same `ncbi_env` EAV pivot pattern

## Revision History
- **v1** (2026-02): Created from README.md content

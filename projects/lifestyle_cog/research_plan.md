# Research Plan: Lifestyle-Based COG Stratification

## Research Question

How does bacterial lifestyle (free-living vs host-associated) affect pangenome functional composition at the COG category level?

Dewar et al. (2024) showed that lifestyle is the primary driver of pangenome *structural* variation (fluidity, openness). We extend this by asking whether lifestyle also shapes the *functional* composition of core vs accessory genomes — specifically, whether the COG enrichment patterns in accessory genes differ systematically between free-living and host-associated species.

## Hypotheses

- **H1**: Host-associated bacteria have higher defense gene (COG category V) enrichment in their accessory genomes than free-living bacteria
  - *Rationale*: Constant immune and phage pressure in host environments selects for diverse, rapidly-evolving defense systems
  - *H0*: V-category enrichment in accessory genes is independent of lifestyle

- **H2**: Free-living bacteria have greater metabolic diversity in their accessory genomes (COG categories E, G, C, P, I)
  - *Rationale*: Variable nutrient availability in open environments favors flexible, diverse metabolic capabilities
  - *H0*: Metabolic COG enrichment in accessory genes is independent of lifestyle

- **H3**: Host-associated bacteria have smaller core genomes as a fraction of total gene clusters
  - *Rationale*: Stable host environments allow genome streamlining of core functions; consistent with Dewar et al.'s finding of lower pangenome fluidity in host-associated species
  - *H0*: Core genome fraction is independent of lifestyle

## Literature Context

### Key References

1. **Dewar et al. (2024)** "Bacterial lifestyle shapes pangenomes" — *PNAS*. Studied 126 species. Lifestyle is the most important driver of pangenome variation. Host-associated species have lower fluidity. Did NOT examine COG functional composition — structural analysis only. **Our study fills this gap.**

2. **McInerney et al. (2017)** "The bacterial pangenome as a new tool for analysing pathogenic bacteria" — *Current Opinion in Microbiology*. Framework for core/accessory functional partitioning. Core enriched in housekeeping (J, F, H), accessory in defense/mobilome (V, X, L).

3. **Moldovan & Gelfand (2018)** "Evidence for selection in abundant accessory gene content" — *MBE*. Accessory genes are under selection, not neutral drift. Supports the idea that functional differences between lifestyles reflect adaptation, not noise.

4. **Bobay & Ochman (2018)** "Structure and Dynamics of Bacterial Populations: Pangenome Ecology" — *The Pangenome* (Springer). Ecological theory predicting that sympatric (free-living) bacteria have wider, more open pangenomes with more defense mechanisms.

### Gap

No study has systematically compared COG functional enrichment patterns (core vs accessory) across lifestyle categories at the scale BERDL enables (27K species, 293K genomes). Dewar et al. covered structure; we cover function.

Full references: `projects/lifestyle_cog/references.md`

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `ncbi_env` | Lifestyle classification | 4.1M (EAV) | Filter by `harmonized_name IN ('host', 'isolation_source', 'env_broad_scale')` |
| `genome` | Link biosample to species | 293K | Join on `ncbi_biosample_id` |
| `sample` | Biosample accessions (backup join) | 293K | Join on `genome_id` |
| `pangenome` | Core/accessory/singleton counts | 27K | Full scan OK |
| `gtdb_species_clade` | Taxonomy for phylogenetic control | 27K | Full scan OK |
| `gene_cluster` | Core/accessory classification per gene cluster | 132M | **Filter by `gtdb_species_clade_id`** |
| `eggnog_mapper_annotations` | COG categories per gene cluster | 93M | **Filter by `query_name` (gene_cluster_id)** |

### Key Queries

1. **Assess ncbi_env coverage** (Notebook 01):
```sql
-- What harmonized_name values exist and how many genomes have them?
SELECT harmonized_name, COUNT(DISTINCT accession) as n_biosamples
FROM kbase_ke_pangenome.ncbi_env
GROUP BY harmonized_name
ORDER BY n_biosamples DESC
LIMIT 30
```

2. **Extract lifestyle metadata** (Notebook 01):
```sql
-- Get host/isolation_source/env_broad_scale per genome
SELECT g.genome_id, g.gtdb_species_clade_id, ne.harmonized_name, ne.content
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.ncbi_env ne
  ON g.ncbi_biosample_id = ne.accession
WHERE ne.harmonized_name IN ('host', 'isolation_source', 'env_broad_scale', 'env_local_scale', 'env_medium')
```

3. **COG enrichment by lifestyle** (Notebook 02-03):
```sql
-- For a given species, get COG distribution by core/accessory
SELECT
  gc.is_core,
  ann.COG_category,
  COUNT(*) as cluster_count
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '{species_id}'
GROUP BY gc.is_core, ann.COG_category
```

### Performance Plan

- **Tier**: JupyterHub (large joins across gene_cluster + eggnog)
- **Estimated complexity**: Moderate — the ncbi_env exploration is small, but scaling COG analysis across many species requires Spark
- **Known pitfalls**:
  - `ncbi_env` is EAV format — must pivot, not scan blindly
  - `gene_cluster` and `eggnog_mapper_annotations` are LARGE — always filter by species
  - Species IDs contain `--` — use exact equality in quoted strings
  - COG_category can be multi-character (e.g., "LV") — decide whether to split or treat as composite
  - String-typed numeric columns — CAST before comparisons
  - Avoid `.toPandas()` on intermediate results

## Analysis Plan

### Notebook 01: Data Exploration & Lifestyle Classification
- **Goal**: Assess `ncbi_env` coverage, build lifestyle classifier, identify target species
- **Steps**:
  1. Query `ncbi_env` to find which `harmonized_name` values are populated and how densely
  2. For attributes like `host`, `isolation_source`, `env_broad_scale`: examine content values, build classification rules
  3. Classify genomes as: free-living, host-associated, or ambiguous/unknown
  4. Aggregate to species level: assign species lifestyle by majority vote of constituent genomes
  5. Filter to species with >= 10 genomes AND clear lifestyle assignment
  6. Report: how many species per lifestyle category, phylogenetic distribution
- **Expected output**: `data/species_lifestyle_classification.csv`

### Notebook 02: COG Enrichment Analysis
- **Goal**: Compare COG enrichment (core vs accessory) between lifestyle groups
- **Steps**:
  1. For each target species, query gene_cluster + eggnog_mapper_annotations
  2. Calculate COG proportions in core vs accessory genes
  3. Compute enrichment scores: `(proportion_in_accessory - proportion_in_core) / proportion_in_core`
  4. Group species by lifestyle, compare enrichment distributions per COG category
  5. Statistical tests: Wilcoxon rank-sum for each COG category between lifestyles
  6. Multiple testing correction (Benjamini-Hochberg)
- **Expected output**: `data/cog_enrichment_by_lifestyle.csv`, `figures/enrichment_heatmap.png`

### Notebook 03: Phylogenetic Controls & Visualization
- **Goal**: Control for phylogeny, test robustness, generate publication figures
- **Steps**:
  1. Stratify by phylum — do patterns hold within Proteobacteria? Firmicutes? Actinomycetota?
  2. PGLS or phylogenetic ANOVA if tree data available (330 species have trees)
  3. Test confounders: genome count, genome size, annotation completeness
  4. Generate figures: heatmaps, box plots, phylogenetic context plots
  5. Core fraction analysis (H3): compare core_fraction = no_core / no_gene_clusters between lifestyles
- **Expected output**: `figures/lifestyle_cog_heatmap.png`, `figures/core_fraction_comparison.png`, `figures/phylum_stratified.png`

## Expected Outcomes

- **If H1 supported**: Host-associated bacteria have higher V (defense) enrichment in accessory genes — consistent with arms-race dynamics in host environments. Novel because Dewar et al. only showed structural differences, not functional ones.

- **If H2 supported**: Free-living bacteria have more diverse metabolic accessory genes — supports the ecological generalist hypothesis. Could explain WHY free-living species have more open pangenomes (metabolic flexibility drives gene gain).

- **If H3 supported**: Host-associated species have smaller core fractions — consistent with genome streamlining in stable environments. Extends Dewar et al.'s fluidity finding to functional architecture.

- **If H0 not rejected**: COG enrichment patterns are universal regardless of lifestyle — the core/accessory functional partitioning is driven by gene-level constraints (essentiality, expression level) rather than ecology. This would also be a significant finding.

## Potential Confounders

1. **Phylogenetic non-independence**: Host-associated bacteria cluster in certain phyla — must stratify by phylum
2. **Sampling bias**: Pathogens massively over-sampled vs environmental bacteria
3. **Genome count effects**: Species with more genomes have better-resolved pangenomes
4. **Annotation completeness**: ~40% of genes lack COG annotations; may differ by lifestyle
5. **ncbi_env coverage**: Unknown fraction of genomes have usable lifestyle metadata
6. **Lifestyle classification ambiguity**: Many bacteria are facultatively host-associated
7. **COG category granularity**: Single-letter categories may be too coarse for some signals

## Authors

*To be filled in*

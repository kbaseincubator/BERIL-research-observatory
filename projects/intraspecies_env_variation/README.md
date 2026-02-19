# Lanthanide Methylotrophy, B Vitamin Auxotrophy, and Intraspecies Environmental Variation

## Research Question

*Methylobacterium extorquens* AM1 carries two methanol dehydrogenases: the lanthanide-dependent XoxF and the calcium-dependent MxaF. These represent fundamentally different C1 metabolic modes with distinct metal cofactor requirements. We ask:

1. **B vitamin biosynthesis**: Is *M. extorquens* auxotrophic for any B vitamins? Which biosynthesis pathways are complete vs incomplete in the pangenome, and what does that imply for optimal growth medium design?
2. **xoxF/mxaF and B vitamins**: Across *Methylobacterium* species, do strains carrying xoxF show different B vitamin biosynthesis profiles than mxaF-only strains?
3. **Broader pattern**: Across the pangenome database, do strains of the same species isolated from different environments carry different accessory genes? Can we link environmental metadata from NCBI biosamples to gene content variation?

The first two questions are organism-specific and mechanistically focused. The third provides cross-database infrastructure (pangenome + NMDC biosample joins) that contextualizes the case study.

## Hypothesis

*M. extorquens* likely has B vitamin auxotrophies that constrain growth medium composition. If the xoxF lanthanide-dependent pathway is co-regulated with or genetically linked to specific B vitamin requirements, this would connect rare earth element biology to vitamin metabolism — a testable prediction for laboratory validation. More broadly, accessory gene content should correlate with isolation environment across species.

## Approach

1. **M. extorquens B vitamin survey**: Query eggNOG annotations for B1 (thiamine), B2 (riboflavin), B6 (pyridoxine), B7 (biotin), B9 (folate), and B12 (cobalamin) biosynthesis genes across *M. extorquens* pangenome gene clusters
2. **xoxF/mxaF annotation audit**: Characterize all PQQ methanol dehydrogenase annotations, including the known eggNOG misannotation of xoxF as mxaF (EC 1.1.2.8 / K00114)
3. **Cross-species MDH + B vitamin correlation**: Test whether xoxF-carrying *Methylobacterium* species have different B vitamin profiles than mxaF-only species
4. **Environmental metadata pivot**: Transform the `ncbi_env` EAV table and cross-tenant NMDC biosample data into per-genome environment categories
5. **Gene-environment association**: For species with sufficient environmental diversity, test accessory gene cluster associations with environment (Fisher's exact / chi-squared, FDR-corrected)

## Data Sources

| Source | Database | Table(s) | Purpose |
|--------|----------|----------|---------|
| Pangenome genomes | `kbase_ke_pangenome` | `genome`, `sample` | Genome metadata, biosample accession links |
| Species stats | `kbase_ke_pangenome` | `gtdb_species_clade`, `pangenome` | Species-level pangenome statistics |
| Gene clusters | `kbase_ke_pangenome` | `gene_cluster`, `gene`, `gene_genecluster_junction` | Gene content per genome |
| Annotations | `kbase_ke_pangenome` | `eggnog_mapper_annotations` | COG, KEGG, EC for gene clusters |
| Environment (EAV) | `kbase_ke_pangenome` | `ncbi_env` | Isolation source, host, location, env_broad_scale |
| NCBI biosamples | `nmdc_ncbi_biosamples` | `biosamples_flattened` | Cross-tenant environmental metadata |
| Env triads | `nmdc_ncbi_biosamples` | `env_triads_flattened` | Curated env ontology labels (broad/local/medium) |

### Key Join Paths

```
Pangenome <-> Environment:
  kbase_ke_pangenome.genome.ncbi_biosample_id
    --> kbase_ke_pangenome.ncbi_env.accession         (within-tenant, EAV pivot)
    --> nmdc_ncbi_biosamples.biosamples_flattened      (cross-tenant)

Annotations <-> Gene clusters:
  kbase_ke_pangenome.eggnog_mapper_annotations.query_name
    --> kbase_ke_pangenome.gene_cluster.gene_cluster_id
```

## Notebooks

| Notebook | Purpose | Estimated Runtime |
|----------|---------|-------------------|
| `01_mextorquens_bvitamin_case.ipynb` | M. extorquens B vitamin biosynthesis survey, xoxF/mxaF analysis, growth medium implications | ~15 min |
| `02_env_metadata_exploration.ipynb` | Explore ncbi_env, cross-tenant NMDC biosample join, derive environment categories | ~10 min |
| `03_gene_environment_association.ipynb` | Species selection, statistical tests, functional enrichment, visualization | ~30-60 min |

## Key Findings

_To be filled in after running the analysis on BERDL JupyterHub._

## Reproduction

### Prerequisites
- BERDL JupyterHub access (for Spark SQL against Delta Lakehouse)
- Python 3.11+ with packages in `requirements.txt`

### Steps
1. Upload notebooks to BERDL JupyterHub
2. Run notebooks in order: 01 -> 02 -> 03
3. Notebook 02 exports `data/genome_env_metadata.csv` used by notebook 03
4. All three notebooks require Spark Connect

### Portability: BERDL JupyterHub vs Workstation

- **BERDL JupyterHub** (primary): Full Spark Connect access, large query results, direct access to all tenant databases. Use `get_spark_session()` and Spark SQL.
- **Workstation** (alternative): Use the KBase MCP REST API (see `cmungall/lakehouse-skills/kbase-query`). Works for exploration and moderate queries but has result size limits and requires a KBase auth token that expires weekly. The EAV pivot and cross-tenant joins in notebook 02 are best done on Spark.

## Related Projects

- `ecotype_analysis/` — Environment vs phylogeny effects on gene content using AlphaEarth embeddings (complementary continuous approach)
- `cog_analysis/` — COG functional category distributions across core/auxiliary/novel genes
- `temporal_core_dynamics/` — Core genome dynamics over collection time (uses same ncbi_env EAV pivot pattern)

## Authors

- **Mark A. Miller** (Lawrence Berkeley National Lab)

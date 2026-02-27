# Research Plan: Openness vs Functional Composition

## Research Question

Does pangenome openness predict the magnitude of COG functional enrichment in novel vs core genes?

## Hypothesis

- **H0**: COG enrichment patterns are independent of pangenome openness
- **H1**: Open pangenomes show HIGHER L (mobile element) and V (defense) enrichment in novel genes
- **H2**: Closed pangenomes show HIGHER metabolic diversity in core (E, C, G categories)
- **H3**: The universal "two-speed genome" pattern intensifies with openness

## Literature Context

- **Tettelin et al. (2005)** introduced the open/closed pangenome framework. Open pangenomes have large accessory genomes, suggesting frequent HGT.
- **McInerney et al. (2017)** argued pangenome structure reflects selection, drift, and HGT balance.
- **cog_analysis project** (this repo) found universal L/V enrichment in novel genes across 32 species/9 phyla, but did not test whether this scales with openness.
- **pangenome_openness project** (this repo) found no correlation between openness and eco-phylo dynamics, but suggested stratifying by gene function as a next step.

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `pangenome` | Openness metrics per species | 27K | Filter to >= 50 genomes |
| `gtdb_species_clade` | Taxonomy for phylogenetic controls | 27K | Join on species ID |
| `gene_cluster` | Core/auxiliary/singleton classification | 132M | Filter by species IN list |
| `gene_genecluster_junction` | Link clusters to annotations | 1B+ | Join only for selected species |
| `eggnog_mapper_annotations` | COG categories | 93M | Join on query_name = gene_cluster_id |

### Key Queries

1. **Pangenome stats extraction** (lightweight):
```sql
SELECT p.*, sc.GTDB_taxonomy, sc.GTDB_species
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade sc
    ON p.gtdb_species_clade_id = sc.gtdb_species_clade_id
WHERE CAST(p.no_genomes AS INT) >= 50
```

2. **COG distributions for selected species** (heavy, ~6 min for 40 species):
```sql
SELECT gc.gtdb_species_clade_id, gc.is_core, gc.is_auxiliary, gc.is_singleton,
       ann.COG_category, COUNT(*) as gene_count
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.gene_genecluster_junction j
    ON gc.gene_cluster_id = j.gene_cluster_id
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
    ON j.gene_id = ann.query_name
WHERE gc.gtdb_species_clade_id IN (<40 species>)
    AND ann.COG_category IS NOT NULL
    AND ann.COG_category != '-'
GROUP BY gc.gtdb_species_clade_id, gc.is_core, gc.is_auxiliary, gc.is_singleton, ann.COG_category
```

### Performance Plan

- **Tier**: JupyterHub (3-way join on billion-row tables)
- **Estimated complexity**: Moderate (~6 min based on cog_analysis precedent for 32 species)
- **Known pitfalls**: String-typed numeric columns in pangenome table (CAST needed); multi-letter COG categories (split into individual letters)

## Analysis Plan

### Notebook 1: Openness Stratification
- **Goal**: Extract pangenome stats, compute openness, select target species
- **Expected output**: `data/species_openness_quartiles.csv`

### Notebook 2: COG Enrichment by Openness
- **Goal**: Query COG distributions for ~40 species across openness quartiles
- **Expected output**: `data/cog_enrichment_by_openness.csv`

### Notebook 3: Statistical Analysis
- **Goal**: Statistical tests, phylogenetic controls, figures
- **Expected output**: `figures/enrichment_by_quartile_heatmap.png`, `figures/openness_vs_lv_enrichment.png`, `figures/core_metabolic_by_openness.png`

## Expected Outcomes

- **If H1 supported**: Open pangenomes have stronger L/V enrichment -- HGT introduces more mobile/defense cargo in open genomes. This extends the "two-speed genome" to show it's not just universal but scales with genome fluidity.
- **If H0 not rejected**: The two-speed pattern is truly universal and independent of openness -- even closed pangenomes have the same L/V enrichment magnitude. This would suggest the pattern is driven by the nature of HGT events, not their frequency.
- **Potential confounders**: Genome count (more genomes = better pangenome estimates), phylum effects, genome size

## Revision History

- **v1** (2026-02-19): Initial plan

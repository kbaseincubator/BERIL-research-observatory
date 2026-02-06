# Pangenome Module

## Overview

Pangenome data for 293,059 genomes across 27,690 microbial species from GTDB.

**Database**: `kbase_ke_pangenome`

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `genome` | 293,059 | Genome metadata and file paths |
| `pangenome` | 27,690 | Per-species pangenome statistics |
| `gtdb_species_clade` | 27,690 | Species taxonomy and ANI statistics |
| `gene_cluster` | varies | Gene family classifications (core/accessory/singleton) |
| `gene_genecluster_junction` | varies | Gene-to-cluster memberships |
| `gene` | varies | Individual gene records |
| `eggnog_mapper_annotations` | varies | Functional annotations (COG, GO, KEGG, EC, PFAM) |
| `gapmind_pathways` | varies | Metabolic pathway predictions |
| `genome_ani` | varies | Pairwise ANI values between genomes |
| `gtdb_metadata` | varies | CheckM quality, assembly stats, GC% |
| `gtdb_taxonomy_r214v1` | varies | GTDB taxonomy |
| `sample` | varies | Sample metadata |
| `ncbi_env` | varies | Environment metadata |

## Key Table Schemas

### genome
| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | Primary key (e.g., RS_GCF_000005845.2) |
| `gtdb_species_clade_id` | string | FK to gtdb_species_clade |
| `gtdb_taxonomy_id` | string | FK to gtdb_taxonomy_r214v1 |
| `ncbi_biosample_id` | string | NCBI BioSample ID |
| `has_sample` | boolean | Whether environmental sample data exists |

### pangenome
| Column | Type | Description |
|--------|------|-------------|
| `gtdb_species_clade_id` | string | FK to gtdb_species_clade |
| `no_genomes` | int | Number of genomes in species |
| `no_core` | int | Number of core gene clusters |
| `no_aux_genome` | int | Number of accessory gene clusters |
| `no_singleton_gene_clusters` | int | Number of singleton clusters |
| `no_gene_clusters` | int | Total gene clusters |

### gtdb_species_clade
| Column | Type | Description |
|--------|------|-------------|
| `gtdb_species_clade_id` | string | Primary key (e.g., s__Escherichia_coli--RS_GCF_000005845.2) |
| `GTDB_species` | string | Species name |
| `GTDB_taxonomy` | string | Full taxonomy string |
| `mean_intra_species_ANI` | float | Average ANI within species |
| `ANI_circumscription_radius` | float | ANI radius for species boundary |

### gtdb_metadata
| Column | Type | Description |
|--------|------|-------------|
| `accession` | string | Genome ID (matches genome.genome_id) |
| `checkm_completeness` | float | CheckM completeness score |
| `checkm_contamination` | float | CheckM contamination score |
| `genome_size` | int | Assembly size in bp |
| `gc_percentage` | float | GC content |

### gene_cluster
| Column | Type | Description |
|--------|------|-------------|
| `gene_cluster_id` | string | Primary key |
| `gtdb_species_clade_id` | string | FK to gtdb_species_clade |
| `is_core` | boolean | True if core gene |

### eggnog_mapper_annotations
| Column | Type | Description |
|--------|------|-------------|
| `query_name` | string | Gene cluster ID |
| `EC` | string | Enzyme Commission numbers |
| `KEGG_ko` | string | KEGG ortholog IDs |
| `KEGG_Reaction` | string | KEGG reaction IDs |
| `KEGG_Pathway` | string | Pathway identifiers |
| `BiGG_Reaction` | string | BiGG reaction IDs |
| `COG_category` | string | COG functional category |
| `Description` | string | Functional description |

## Table Relationships

```
genome.gtdb_species_clade_id -> gtdb_species_clade.gtdb_species_clade_id
genome.gtdb_taxonomy_id -> gtdb_taxonomy_r214v1.gtdb_taxonomy_id
genome.genome_id -> gtdb_metadata.accession
pangenome.gtdb_species_clade_id -> gtdb_species_clade.gtdb_species_clade_id
gene_cluster.gtdb_species_clade_id -> gtdb_species_clade.gtdb_species_clade_id
gene_genecluster_junction.gene_cluster_id -> gene_cluster.gene_cluster_id
gene_genecluster_junction.gene_id -> gene.gene_id
genome_ani.genome1_id -> genome.genome_id
genome_ani.genome2_id -> genome.genome_id
```

## Common Query Patterns

### Get Species Information
```sql
SELECT
  s.GTDB_species,
  s.GTDB_taxonomy,
  p.no_genomes,
  p.no_core,
  p.no_aux_genome,
  p.no_singleton_gene_clusters,
  s.mean_intra_species_ANI,
  s.ANI_circumscription_radius
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
WHERE s.GTDB_species LIKE '%Escherichia_coli%'
```

### Get Genomes for a Species
```sql
SELECT
  g.genome_id,
  g.ncbi_biosample_id,
  m.checkm_completeness,
  m.checkm_contamination,
  m.genome_size,
  m.gc_percentage
FROM kbase_ke_pangenome.genome g
LEFT JOIN kbase_ke_pangenome.gtdb_metadata m
  ON g.genome_id = m.accession
WHERE g.gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
LIMIT 100
```

### Find Species with Most Genomes
```sql
SELECT
  s.GTDB_species,
  p.no_genomes,
  p.no_core,
  p.no_aux_genome,
  s.mean_intra_species_ANI
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
ORDER BY p.no_genomes DESC
LIMIT 20
```

### Pangenome Statistics
```sql
SELECT
  COUNT(*) as total_species,
  AVG(no_genomes) as avg_genomes_per_species,
  AVG(no_core) as avg_core_genes,
  AVG(no_singleton_gene_clusters) as avg_singletons
FROM kbase_ke_pangenome.pangenome
```

### Pangenome Openness (Core Fraction)
```sql
SELECT
  s.GTDB_species,
  p.no_genomes,
  p.no_core,
  p.no_gene_clusters,
  CAST(p.no_core AS FLOAT) / p.no_gene_clusters as core_fraction
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
WHERE p.no_genomes >= 50
ORDER BY core_fraction ASC
LIMIT 20
```

### Species with Open Pangenomes (High Singleton Ratio)
```sql
SELECT
  s.GTDB_species,
  p.no_genomes,
  p.no_singleton_gene_clusters,
  p.no_gene_clusters,
  CAST(p.no_singleton_gene_clusters AS FLOAT) / p.no_gene_clusters as singleton_fraction
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
WHERE p.no_genomes >= 20
ORDER BY singleton_fraction DESC
LIMIT 20
```

### COG Category Distribution by Gene Class
```sql
SELECT
  gc.is_core,
  ann.COG_category,
  COUNT(*) as gene_count
FROM kbase_ke_pangenome.gene_cluster gc
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = 's__Neisseria_gonorrhoeae--RS_GCF_013030075.1'
GROUP BY gc.is_core, ann.COG_category
ORDER BY gc.is_core, gene_count DESC
```

### KEGG Pathway Enrichment in Core vs Accessory
```sql
SELECT
  gc.is_core,
  ann.KEGG_Pathway,
  COUNT(*) as gene_count
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = 's__Escherichia_coli--RS_GCF_000005845.2'
  AND ann.KEGG_Pathway != '-'
GROUP BY gc.is_core, ann.KEGG_Pathway
ORDER BY gene_count DESC
LIMIT 30
```

### Find Genes with EC Numbers
```sql
SELECT query_name, EC, Description, KEGG_ko, KEGG_Reaction
FROM kbase_ke_pangenome.eggnog_mapper_annotations
WHERE EC != '-' AND EC IS NOT NULL
LIMIT 20
```

### High-Quality Genomes Only
```sql
SELECT
  g.genome_id,
  g.gtdb_species_clade_id,
  m.checkm_completeness,
  m.checkm_contamination
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.gtdb_metadata m
  ON g.genome_id = m.accession
WHERE m.checkm_completeness > 95
  AND m.checkm_contamination < 2
LIMIT 100
```

### Phylum-level Statistics
```sql
SELECT
  t.phylum,
  COUNT(DISTINCT g.genome_id) as n_genomes,
  COUNT(DISTINCT g.gtdb_species_clade_id) as n_species
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t
  ON g.genome_id = t.genome_id
GROUP BY t.phylum
ORDER BY n_genomes DESC
```

### Database-Wide Statistics
```sql
SELECT 'genomes' as metric, COUNT(*) as value FROM kbase_ke_pangenome.genome
UNION ALL
SELECT 'species' as metric, COUNT(*) as value FROM kbase_ke_pangenome.gtdb_species_clade
UNION ALL
SELECT 'pangenomes' as metric, COUNT(*) as value FROM kbase_ke_pangenome.pangenome
```

### Species with Environmental Data
```sql
SELECT COUNT(DISTINCT g.gtdb_species_clade_id) as species_with_env
FROM kbase_ke_pangenome.genome g
WHERE g.has_sample = true
```

## Pitfalls

- **Large tables**: `gene`, `gene_genecluster_junction`, and `eggnog_mapper_annotations` can be very large. Always filter by `gtdb_species_clade_id`.
- **Species ID format**: Species clade IDs follow the pattern `s__{species}--{reference_genome}` (e.g., `s__Escherichia_coli--RS_GCF_000005845.2`)
- **Pagination required**: Use `ORDER BY` with `LIMIT`/`OFFSET` for deterministic pagination through large result sets
- **NULL annotations**: Many genes have `-` or NULL for annotation columns like EC, KEGG_ko - filter with `!= '-' AND IS NOT NULL`

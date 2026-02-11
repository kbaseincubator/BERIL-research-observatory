# KBase KE Pangenome Database Schema Documentation

**Database**: `kbase_ke_pangenome`
**Location**: On-prem Delta Lakehouse (BERDL - KBase BER Data Lakehouse)
**Access**: Spark SQL via REST API at `https://hub.berdl.kbase.us/apis/mcp/`
**Tenant**: KBase
**Last Updated**: 2026-02-11
**Verified**: Direct Spark SQL queries on cluster (2026-01-07)

---

## Overview

This database contains pangenome data for **293,059 genomes** across **27,690 microbial species** derived from GTDB r214. The data includes:
- Species-level pangenomes computed with motupan (90% AAI clustering)
- Pairwise ANI between genomes (~421M pairs)
- Functional annotations via eggNOG v6
- Metabolic pathway predictions via GapMind
- Environmental embeddings from AlphaEarth

---

## Table Summary

| Table | Row Count | Description |
|-------|-----------|-------------|
| `genome` | 293,059 | Genome metadata and file paths |
| `gtdb_species_clade` | 27,690 | Species taxonomy and ANI statistics |
| `pangenome` | 27,702 | Per-species pangenome statistics |
| `gtdb_metadata` | 293,059 | CheckM quality, assembly stats, GC% |
| `gtdb_taxonomy_r214v1` | 293,059 | GTDB taxonomy hierarchy |
| `gene` | 1,011,650,903 | Individual gene records |
| `gene_cluster` | 132,531,501 | Gene family classifications |
| `gene_genecluster_junction` | 1,011,650,762 | Gene-to-cluster memberships |
| `eggnog_mapper_annotations` | 93,558,330 | Functional annotations (COG, GO, KEGG, EC, PFAM) |
| `genome_ani` | 421,218,641 | Pairwise ANI values between genomes |
| `sample` | 293,059 | Biosample/Bioproject accessions |
| `ncbi_env` | 4,124,801 | NCBI environment metadata (key-value format) |
| `alphaearth_embeddings_all_years` | 83,287 | Environmental embeddings (64-dim) |
| `gapmind_pathways` | 305,471,280 | Metabolic pathway predictions |

---

## Table Schemas

### 1. `genome`

Central genome table linking to species clades and taxonomy.

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | **Primary Key**. Format: `RS_GCF_XXXXXXXXX.X` or `GB_GCA_XXXXXXXXX.X` |
| `gtdb_species_clade_id` | string | FK → `gtdb_species_clade` |
| `gtdb_taxonomy_id` | string | FK → `gtdb_taxonomy_r214v1` |
| `ncbi_biosample_id` | string | NCBI BioSample accession |
| `fna_file_path_nersc` | string | Path to nucleotide FASTA at NERSC |
| `faa_file_path_nersc` | string | Path to protein FASTA at NERSC |

**Sample Row**:
```
genome_id: RS_GCF_002752865.1
gtdb_species_clade_id: s__Klebsiella_pneumoniae--RS_GCF_000742135.1
```

---

### 2. `gtdb_species_clade`

Species-level taxonomy and ANI statistics.

| Column | Type | Description |
|--------|------|-------------|
| `gtdb_species_clade_id` | string | **Primary Key**. Format: `s__Genus_species--RS_GCF_XXXXXXXXX.X` |
| `representative_genome_id` | string | Type strain / representative genome |
| `GTDB_species` | string | Species name (e.g., "s__Escherichia coli") |
| `GTDB_taxonomy` | string | Full taxonomy string (d__;p__;c__;o__;f__;g__;s__) |
| `ANI_circumscription_radius` | float | ANI threshold for species boundary |
| `mean_intra_species_ANI` | float | Average ANI within species |
| `min_intra_species_ANI` | float | Minimum ANI within species |
| `mean_intra_species_AF` | float | Mean alignment fraction |
| `min_intra_species_AF` | float | Minimum alignment fraction |
| `no_clustered_genomes_unfiltered` | int | Raw genome count before QC |
| `no_clustered_genomes_filtered` | int | Genome count after QC filtering |

**ID Format Notes**:
- The `--` in species IDs can cause SQL parsing issues when used in `IN` clauses
- Use `LIKE 'prefix%'` patterns instead of exact matches to avoid SQL comment interpretation

---

### 3. `pangenome`

Pre-computed pangenome statistics per species.

| Column | Type | Description |
|--------|------|-------------|
| `gtdb_species_clade_id` | string | **Primary Key**. FK → `gtdb_species_clade` |
| `protocol_id` | string | Build protocol reference (e.g., "PGNKE_MMS90_V01_DEC2024") |
| `number_of_iterations` | int | motupan iteration count |
| `mean_initial_completeness` | float | Initial genome completeness (%) |
| `total_sum_of_loglikelihood_ratios` | float | Model fit statistic |
| `corrected_mean_completness` | float | Adjusted completeness after filtering |
| `estimate_mean_traits_per_genome_count` | float | Estimated genes per genome |
| `no_aux_genome` | int | Number of accessory gene clusters |
| `no_core` | int | Number of core gene clusters (present in ≥95% genomes) |
| `no_singleton_gene_clusters` | int | Number of singleton clusters (1 genome only) |
| `likelies` | float | Likelihood statistic |
| `no_CDSes` | int | Total CDS count |
| `no_gene_clusters` | int | Total gene cluster count |
| `no_genomes` | int | Number of genomes in this pangenome |

**Derived Metrics** (computed locally):
```python
core_fraction = no_core / no_gene_clusters
aux_fraction = no_aux_genome / no_gene_clusters  # Note: aux + core = gene_clusters
singleton_fraction = no_singleton_gene_clusters / no_gene_clusters
```

**Sample Row**:
```csv
gtdb_species_clade_id,no_genomes,no_core,no_aux_genome,no_singleton_gene_clusters,no_gene_clusters
s__Clostridium_AQ_innocuum--RS_GCF_012317185.1,81,3035,16743,8460,19778
```

---

### 4. `gtdb_metadata`

Comprehensive genome quality and assembly metadata from GTDB.

| Column | Type | Description |
|--------|------|-------------|
| `accession` | string | **Primary Key**. FK → `genome.genome_id` |
| `checkm_completeness` | float | CheckM completeness (%) |
| `checkm_contamination` | float | CheckM contamination (%) |
| `checkm_strain_heterogeneity` | float | Strain heterogeneity (%) |
| `genome_size` | int | Total genome size (bp) |
| `gc_percentage` | float | GC content (%) |
| `contig_count` | int | Number of contigs |
| `n50_contigs` | int | N50 contig length |
| `longest_contig` | int | Longest contig length |
| `coding_density` | float | Coding density (%) |
| `protein_count` | int | Number of proteins |
| `ncbi_assembly_level` | string | Assembly level (Complete, Chromosome, Scaffold, Contig) |
| `ncbi_genome_category` | string | MAG, SAG, or isolate |
| `ncbi_isolation_source` | string | Isolation source from NCBI |
| `ncbi_country` | string | Country of origin |
| `ncbi_lat_lon` | string | Latitude/longitude if available |
| `gtdb_taxonomy` | string | GTDB taxonomy string |
| ... | ... | (100+ columns total - see GTDB metadata specification) |

---

### 5. `gtdb_taxonomy_r214v1`

Parsed GTDB taxonomy for easy hierarchical queries.

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | FK → `genome.genome_id` |
| `gtdb_taxonomy_id` | string | **Primary Key**. Taxonomy identifier |
| `domain` | string | Domain (d__Bacteria or d__Archaea) |
| `phylum` | string | Phylum (p__*) |
| `class` | string | Class (c__*) |
| `order` | string | Order (o__*) |
| `family` | string | Family (f__*) |
| `genus` | string | Genus (g__*) |
| `species` | string | Species (s__*) |

---

### 6. `gene`

Individual gene records linking genes to genomes.

| Column | Type | Description |
|--------|------|-------------|
| `gene_id` | string | **Primary Key**. Unique gene identifier |
| `genome_id` | string | FK → `genome.genome_id` |

**Note**: This table has ~1 billion rows. Use targeted queries with genome_id filters.

---

### 7. `gene_cluster`

Gene family classifications with core/accessory/singleton status.

| Column | Type | Description |
|--------|------|-------------|
| `gene_cluster_id` | string | **Primary Key**. Cluster identifier (e.g., "AAAIZCND_mmseqsCluster_01682") |
| `gtdb_species_clade_id` | string | FK → `gtdb_species_clade`. Clusters are species-specific |
| `is_core` | boolean | True if present in ≥95% of genomes |
| `is_auxiliary` | boolean | True if present in <95% and >1 genome |
| `is_singleton` | boolean | True if present in exactly 1 genome |
| `likelihood` | float | Assignment confidence from motupan |

**Important**: Core, auxiliary, and singleton are mutually exclusive categories.

---

### 8. `gene_genecluster_junction`

Many-to-many junction table linking genes to gene clusters.

| Column | Type | Description |
|--------|------|-------------|
| `gene_id` | string | FK → `gene.gene_id` |
| `gene_cluster_id` | string | FK → `gene_cluster.gene_cluster_id` |

**Note**: ~1 billion rows. One gene maps to one cluster within a species pangenome.

---

### 9. `eggnog_mapper_annotations`

Functional annotations from eggNOG v6, computed on cluster representatives.

| Column | Type | Description |
|--------|------|-------------|
| `query_name` | string | **Primary Key**. FK → `gene_cluster.gene_cluster_id` |
| `seed_ortholog` | string | Best eggNOG ortholog hit |
| `evalue` | float | E-value of best hit |
| `score` | float | Alignment score |
| `eggNOG_OGs` | string | Hierarchical orthologous groups (pipe-separated) |
| `max_annot_lvl` | string | Taxonomic level of annotation |
| `COG_category` | string | COG functional category (single letter codes) |
| `Description` | string | Functional description |
| `Preferred_name` | string | Gene name if known |
| `GOs` | string | GO terms (comma-separated) |
| `EC` | string | EC numbers (comma-separated) |
| `KEGG_ko` | string | KEGG orthology IDs |
| `KEGG_Pathway` | string | KEGG pathway IDs |
| `KEGG_Module` | string | KEGG module IDs |
| `KEGG_Reaction` | string | KEGG reaction IDs |
| `KEGG_rclass` | string | KEGG reaction class |
| `BRITE` | string | KEGG BRITE hierarchies |
| `KEGG_TC` | string | Transporter classification |
| `CAZy` | string | Carbohydrate-active enzyme annotations |
| `BiGG_Reaction` | string | BiGG reaction IDs |
| `PFAMs` | string | PFAM domain annotations |

**Sample Row**:
```csv
query_name,eggNOG_OGs,COG_category
AAAIZCND_mmseqsCluster_01682,"COG1073@1|root,COG1073@2|Bacteria,2GVYQ@201174|Actinobacteria",S
```

---

### 10. `genome_ani`

Pairwise Average Nucleotide Identity between genomes.

| Column | Type | Description |
|--------|------|-------------|
| `genome1_id` | string | FK → `genome.genome_id` |
| `genome2_id` | string | FK → `genome.genome_id` |
| `protocol_id` | string | ANI computation protocol |
| `ANI` | float | Average Nucleotide Identity (0-100) |
| `AF` | float | Alignment fraction |
| `AFMapped` | float | Alignment fraction of mapped regions |
| `AFTotal` | float | Total alignment fraction |

**Note**: ~421 million rows. Only contains within-species comparisons. Query by species to avoid timeouts.

---

### 11. `sample`

Biosample and Bioproject accession mapping.

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | **Primary Key**. FK → `genome.genome_id` |
| `ncbi_bioproject_accession_id` | string | NCBI BioProject accession |
| `ncbi_biosample_accession_id` | string | NCBI BioSample accession |

---

### 12. `ncbi_env`

NCBI environment metadata in key-value format.

| Column | Type | Description |
|--------|------|-------------|
| `accession` | string | BioSample accession |
| `id` | string | Row identifier |
| `attribute_name` | string | Metadata field name |
| `display_name` | string | Human-readable attribute name |
| `harmonized_name` | string | Standardized attribute name |
| `content` | string | Attribute value |
| `package_content` | string | BioSample package information |

**Note**: This is an EAV (Entity-Attribute-Value) table. Pivot or filter by `harmonized_name` for specific attributes.

---

### 13. `alphaearth_embeddings_all_years`

Environmental embeddings from AlphaEarth satellite imagery.

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | FK → `genome.genome_id` |
| `ncbi_biosample_accession_id` | string | BioSample accession |
| `ncbi_bioproject` | string | BioProject accession |
| `domain` | string | GTDB domain |
| `phylum` | string | GTDB phylum |
| `class` | string | GTDB class |
| `order` | string | GTDB order |
| `family` | string | GTDB family |
| `genus` | string | GTDB genus |
| `species` | string | GTDB species |
| `cleaned_lat` | float | Cleaned latitude |
| `cleaned_lon` | float | Cleaned longitude |
| `cleaned_year` | int | Sample collection year |
| `A00` - `A63` | float | 64-dimensional AlphaEarth embedding |

**Coverage**: Only 83,287 genomes (28.4%) have environmental embeddings due to sparse lat/lon metadata.

---

### 14. `gapmind_pathways`

GapMind metabolic pathway predictions per genome.

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | FK → `genome.genome_id` |
| `pathway` | string | Pathway name (e.g., "glucosamine", "arginine") |
| `clade_name` | string | Species clade (same as `gtdb_species_clade_id`) |
| `metabolic_category` | string | Category: "carbon" or "amino_acid" |
| `sequence_scope` | string | Gene set used: "core" or other |
| `nHi` | int | Number of high-confidence step matches |
| `nMed` | int | Number of medium-confidence step matches |
| `nLo` | int | Number of low-confidence step matches |
| `score` | float | Overall pathway score |
| `score_category` | string | Category: "likely_complete", "steps_missing_low", "not_present" |
| `score_simplified` | int | Binary score (1=likely complete, 0=incomplete) |

**Row Count**: 305,471,280

**Sample Row**:
```
genome_id: GCF_003947565.1
pathway: glucosamine
clade_name: s__Spirillospora_rifamycini--RS_GCF_000425065.1
metabolic_category: carbon
sequence_scope: core
nHi: 2, nMed: 1, nLo: 0
score: 1.9
score_category: likely_complete
score_simplified: 1
```

---

## Key Relationships (Entity-Relationship)

```
gtdb_species_clade (27,690)
    │
    ├── 1:1 → pangenome (27,702)
    │            └── protocol_id → pangenome_build_protocol
    │
    ├── 1:N → genome (293,059)
    │            │
    │            ├── 1:1 → gtdb_metadata (accession)
    │            ├── 1:1 → gtdb_taxonomy_r214v1 (genome_id)
    │            ├── 1:1 → sample (genome_id)
    │            ├── 0:1 → alphaearth_embeddings_all_years (genome_id)
    │            │
    │            ├── 1:N → gene (genome_id)
    │            │            └── N:1 → gene_genecluster_junction (gene_id)
    │            │                          └── N:1 → gene_cluster
    │            │
    │            └── N:N → genome_ani (genome1_id, genome2_id)
    │
    └── 1:N → gene_cluster (gtdb_species_clade_id)
                 └── 1:1 → eggnog_mapper_annotations (query_name)
```

---

## Data Integrity Observations

*Verified via direct Spark SQL on cluster (2026-01-07)*

### Verified Alignments (1:1 Expected)

| Table A | Table B | Count A | Count B | Status |
|---------|---------|---------|---------|--------|
| `genome` | `gtdb_metadata` | 293,059 | 293,059 | **ALIGNED** |
| `genome` | `sample` | 293,059 | 293,059 | **ALIGNED** |
| `genome` | `gtdb_taxonomy_r214v1` | 293,059 | 293,059 | **ALIGNED** |
| `genome` | `gtdb_species_clade` | 293,059 | (all matched) | **ALIGNED** (0 orphan genomes) |
| `gene` | `gene_genecluster_junction` | 1,011,650,903 | 1,011,650,762 | **~ALIGNED** (141 orphan genes) |

### Gene Cluster Category Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| **Core** (≥95% genomes) | 62,062,686 | 46.83% |
| **Auxiliary** (<95%, >1 genome) | 70,468,815 | 53.17% |
| **Singleton** (1 genome only) | 50,203,195 | 37.88% |
| Uncategorized | 0 | 0.00% |

**Note**: Singletons are a subset of auxiliary clusters. Core + Auxiliary = Total clusters.

### Genes Per Genome Statistics

| Statistic | Value |
|-----------|-------|
| Min | 198 |
| Q1 (25th percentile) | 2,138 |
| **Median** | **3,099** |
| Q3 (75th percentile) | 4,608 |
| Max | 12,729 |
| Mean | 3,452 |

### Known Discrepancies

1. **pangenome vs gtdb_species_clade**: 27,702 vs 27,690 (**12 orphan pangenomes**)

   These 12 pangenomes reference species clades not in `gtdb_species_clade`:
   ```
   s__Portiera_aleyrodidarum--RS_GCF_000300075.1
   s__C7867-002_sp001822575--GB_GCA_001822575.1
   s__AG-339-G14_sp902525735--GB_GCA_902525735.1
   s__UBA2103_sp002376865--GB_GCA_002376865.1
   s__UBA1020_sp002316545--GB_GCA_002316545.1
   s__Nanosynbacter_sp022828325--RS_GCF_022828325.1
   s__2-01-FULL-33-17_sp001786995--GB_GCA_001786995.1
   s__TMED112_sp003213455--GB_GCA_003213455.1
   s__SCGC-AAA076-P13_sp905182885--GB_GCA_905182885.1
   s__Profftella_armatura--RS_GCF_000441555.1
   (+ 2 more)
   ```
   These appear to be single-genome species or symbionts that were included in pangenome builds but filtered from the species clade table.

2. **alphaearth_embeddings coverage**: Only **83,227/293,059 = 28.4%** of genomes have embeddings
   - Environmental metadata (lat/lon) is sparsely populated in NCBI
   - More complete for environmental samples vs clinical isolates

3. **ncbi_env table structure**: 4.1M rows in EAV format
   - Multiple rows per BioSample for different attributes
   - Sparse and inconsistent field population across samples

---

## SQL Query Patterns

### Authentication
```bash
AUTH_TOKEN=$(grep "KB_AUTH_TOKEN" .env | cut -d'"' -f2)
```

### Basic Query via API
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM kbase_ke_pangenome.genome LIMIT 10", "limit": 1000}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/query
```

### Get Species with Pangenome Stats
```sql
SELECT
  s.GTDB_species,
  p.no_genomes,
  p.no_core,
  p.no_aux_genome,
  p.no_singleton_gene_clusters,
  p.no_gene_clusters,
  s.mean_intra_species_ANI
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
ORDER BY p.no_genomes DESC
LIMIT 20
```

### Get Genomes for a Species (avoid -- in IN clause)
```sql
-- WRONG: This fails because -- is interpreted as SQL comment
SELECT * FROM genome WHERE gtdb_species_clade_id IN ('s__E_coli--RS_GCF_000005845.2')

-- CORRECT: Use LIKE pattern
SELECT * FROM kbase_ke_pangenome.genome
WHERE gtdb_species_clade_id LIKE 's__Escherichia_coli%'
LIMIT 100
```

### Get ANI for a Species (iterate by species to avoid timeout)
```python
# Query ANI for one species at a time
genome_ids = get_genomes_for_species(species_id)
genome_list = ','.join([f"'{g}'" for g in genome_ids])

query = f"""
SELECT genome1_id, genome2_id, ANI
FROM kbase_ke_pangenome.genome_ani
WHERE genome1_id IN ({genome_list})
  AND genome2_id IN ({genome_list})
"""
```

### Get Gene Clusters with Annotations
```sql
SELECT
  gc.gene_cluster_id,
  gc.is_core,
  gc.is_auxiliary,
  gc.is_singleton,
  e.COG_category,
  e.Description,
  e.GOs
FROM kbase_ke_pangenome.gene_cluster gc
LEFT JOIN kbase_ke_pangenome.eggnog_mapper_annotations e
  ON gc.gene_cluster_id = e.query_name
WHERE gc.gtdb_species_clade_id LIKE 's__Escherichia_coli%'
LIMIT 100
```

### Get Environmental Embeddings for Species
```sql
SELECT
  ae.genome_id,
  ae.cleaned_lat,
  ae.cleaned_lon,
  ae.A00, ae.A01, ae.A02, ae.A03  -- First 4 embedding dimensions
FROM kbase_ke_pangenome.alphaearth_embeddings_all_years ae
JOIN kbase_ke_pangenome.genome g ON ae.genome_id = g.genome_id
WHERE g.gtdb_species_clade_id LIKE 's__Prochlorococcus%'
```

---

## Performance Notes

1. **Use ORDER BY for pagination**: Queries without ORDER BY may return inconsistent results when paginating with LIMIT/OFFSET.

2. **Avoid large IN clauses**: The `--` in species IDs can break queries. Use LIKE patterns instead.

3. **Query large tables by partition**: Filter by `gtdb_species_clade_id` or `genome_id` to reduce scan size.

4. **API timeouts**: Large queries may timeout (504 Gateway Timeout). Break into smaller batches.

5. **Retry on 503 errors**: The "cannot schedule new futures after shutdown" error is transient. Retry after a few seconds.

---

## Recently Added Tables

*Confirmed present as of 2026-02-11 (previously listed as missing)*

| Table Name | Description | Status |
|------------|-------------|--------|
| `phylogenetic_tree` | Species phylogenies from single-copy core genes | **NOW AVAILABLE** |
| `phylogenetic_tree_distance_pairs` | Pairwise phylogenetic distances | **NOW AVAILABLE** |

These tables were not present in the January 2026 verification but are now accessible. Schema details are pending verification.

## Missing Tables (Mentioned in Project Docs but Not Present)

*Last checked 2026-02-11*

| Table Name | Mentioned For | Status |
|------------|---------------|--------|
| `pangenome_build_protocol` | Parameter settings for reproducibility | **NOT FOUND** |
| `genomad_mobile_elements` | Plasmid/virus/prophage annotations | **NOT FOUND** |
| `IMG_env` | IMG environment metadata | **NOT FOUND** |

The `protocol_id` column in `pangenome` and `genome_ani` tables references `pangenome_build_protocol`, but the protocol table itself is not available.

---

## API Availability Note

The REST API at `https://hub.berdl.kbase.us/apis/mcp/` can experience 504 Gateway Timeout errors for complex queries. If you encounter issues:

1. **Use direct Spark SQL** on the cluster instead of REST API for complex queries
2. Wait a few minutes and retry (transient "cannot schedule new futures" errors)
3. Use the `/count` endpoint (faster) instead of `/query` for counts
4. Query by species rather than across the entire database
5. Add `LIMIT` clauses and paginate with `OFFSET`

---

## Changelog

- **2026-01-07**: Full verification via direct Spark SQL on cluster. Added gapmind_pathways schema, gene cluster category distribution, genes per genome statistics, identified 12 specific orphan pangenomes.
- **2026-01-06**: Initial documentation based on REST API queries and local data extracts.

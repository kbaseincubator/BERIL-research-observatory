# KBase Genomes Database Schema Documentation

**Database**: `kbase_genomes`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: KBase
**Last Updated**: 2026-02-11
**Verified**: REST API schema introspection

---

## Overview

The KBase Genomes database stores **structural genomics data** in a normalized relational schema following the KBase Common Data Model (CDM). It contains contigs, features (genes), encoded features (CDS), and protein sequences for the same 293,059 genomes in the pangenome collection, plus extensive cross-reference (junction) tables linking these entities.

Key data:
- 293,059 contig collections (one per genome)
- 34,582,336 contigs
- 1,011,650,903 features (genes)
- 253,173,194 unique protein sequences
- Full protein amino acid sequences available

**Important**: This database uses UUID-based identifiers internally. The `name` table provides mappings between human-readable gene IDs and CDM UUIDs.

---

## Table Summary

### Entity Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `contig_collection` | 293,059 | Genome-level contig sets (one per genome) |
| `contig` | 34,582,336 | Individual contigs with GC content and length |
| `feature` | 1,011,650,903 | Gene/feature records with coordinates |
| `encoded_feature` | 1,011,650,903 | CDS-level records (1:1 with features) |
| `protein` | 253,173,194 | Unique protein sequences |
| `name` | 1,046,526,298 | ID mappings between systems |

### Junction Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `contig_x_contig_collection` | 34,582,336 | Contig-to-genome membership |
| `contig_x_feature` | 1,011,650,903 | Feature location on contigs |
| `contig_x_encoded_feature` | ~1B | Encoded feature location on contigs |
| `contig_collection_x_feature` | ~1B | Features per genome |
| `contig_collection_x_encoded_feature` | 1,011,650,903 | Encoded features per genome |
| `contig_collection_x_protein` | 1,011,650,903 | Proteins per genome |
| `contig_x_protein` | ~1B | Protein location on contigs |
| `feature_x_protein` | 1,011,650,903 | Feature-to-protein mappings |
| `encoded_feature_x_feature` | ~1B | Encoded feature to feature mappings |
| `encoded_feature_x_protein` | 1,011,650,903 | Encoded feature to protein mappings |

---

## Table Schemas

### `contig_collection`

One record per genome, linking to taxonomy.

| Column | Type | Description |
|--------|------|-------------|
| `contig_collection_id` | string | **Primary Key**. CDM UUID |
| `hash` | string | Content hash |
| `contig_bp` | string | Total base pairs |
| `ncbi_taxon_id` | string | NCBI taxonomy ID |
| `gtdb_taxon_id` | string | GTDB taxonomy ID |

---

### `contig`

Individual contigs/scaffolds.

| Column | Type | Description |
|--------|------|-------------|
| `contig_id` | string | **Primary Key**. CDM UUID |
| `hash` | string | Content hash |
| `gc_content` | string | GC content fraction |
| `length` | string | Contig length in bp |

---

### `feature`

Gene/feature records with genomic coordinates.

| Column | Type | Description |
|--------|------|-------------|
| `feature_id` | string | **Primary Key**. CDM UUID |
| `hash` | string | Content hash |
| `cds_phase` | string | CDS reading frame phase |
| `e_value` | string | Prediction e-value |
| `p_value` | string | Prediction p-value |
| `start` | string | Start coordinate |
| `end` | string | End coordinate |
| `strand` | string | Strand (+/-) |
| `source_database` | string | Source annotation database |
| `protocol_id` | string | Annotation protocol |
| `type` | string | Feature type (CDS, rRNA, tRNA, etc.) |

---

### `encoded_feature`

CDS-level records (coding sequences).

| Column | Type | Description |
|--------|------|-------------|
| `encoded_feature_id` | string | **Primary Key**. CDM UUID |
| `hash` | string | Content hash |
| `has_stop_codon` | string | Whether CDS has stop codon |
| `type` | string | Feature type |

---

### `protein`

Unique protein sequences.

| Column | Type | Description |
|--------|------|-------------|
| `protein_id` | string | **Primary Key**. CDM UUID |
| `hash` | string | Content hash (MD5 of sequence) |
| `description` | string | Protein description |
| `evidence_for_existence` | string | Evidence type |
| `length` | string | Protein length (amino acids) |
| `sequence` | string | **Full amino acid sequence** |

---

### `name`

Cross-reference table mapping between identifier systems. This is essential for linking gene IDs from other databases (e.g., pangenome `gene_id`) to CDM UUIDs used in this database.

| Column | Type | Description |
|--------|------|-------------|
| `entity_id` | string | CDM UUID (FK to feature, protein, etc.) |
| `name` | string | External identifier (e.g., gene locus tag) |
| `description` | string | Name description |
| `source` | string | Source system for this name |

---

## Key Relationships

```
contig_collection (293K genomes)
    │
    ├── 1:N → contig (34.5M)
    │            │
    │            ├── 1:N → feature (1B) via contig_x_feature
    │            │            │
    │            │            ├── 1:1 → encoded_feature via encoded_feature_x_feature
    │            │            │
    │            │            └── N:1 → protein (253M) via feature_x_protein
    │            │
    │            └── 1:N → protein via contig_x_protein
    │
    └── 1:N → feature via contig_collection_x_feature
```

**Cross-database link to pangenome**: The `name` table maps between `kbase_genomes` CDM UUIDs and the `gene_id` values used in `kbase_ke_pangenome.gene`.

---

## Common Query Patterns

### Get Protein Sequence for a Gene
```sql
SELECT p.protein_id, p.description, p.length, p.sequence
FROM kbase_genomes.protein p
JOIN kbase_genomes.feature_x_protein fp ON p.protein_id = fp.protein_id
JOIN kbase_genomes.name n ON fp.feature_id = n.entity_id
WHERE n.name = 'YOUR_GENE_ID'
LIMIT 1
```

### Get All Proteins for a Genome
```sql
SELECT p.protein_id, p.length, p.sequence
FROM kbase_genomes.protein p
JOIN kbase_genomes.contig_collection_x_protein cp
  ON p.protein_id = cp.protein_id
WHERE cp.contig_collection_id = 'GENOME_UUID'
```

### Map Gene IDs to CDM UUIDs
```sql
SELECT entity_id, name, source
FROM kbase_genomes.name
WHERE name = 'NZ_CP095497.1_1766'
```

---

## Pitfalls

- **UUID-based IDs**: All primary keys are CDM UUIDs, not human-readable IDs. Use the `name` table for cross-referencing.
- **Billion-row tables**: `feature`, `encoded_feature`, and all junction tables have ~1 billion rows. Always filter.
- **String types**: Numeric columns (length, coordinates) are stored as strings. Cast as needed.
- **No direct genome_id column**: Unlike the pangenome database, genomes here are identified by `contig_collection_id`. Cross-reference via `name` table or through the `gtdb_taxon_id` column.
- **Protein deduplication**: The `protein` table has 253M unique sequences vs 1B features, meaning many features share identical proteins.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.

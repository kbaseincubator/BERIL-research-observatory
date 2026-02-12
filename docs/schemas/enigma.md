# ENIGMA CORAL Database Schema Documentation

**Database**: `enigma_coral`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: ENIGMA
**Last Updated**: 2026-02-11

---

## Overview

The ENIGMA (Ecosystems and Networks Integrated with Genes and Molecular Assemblies) CORAL database stores environmental microbiology data including samples, taxa, genomes, genes, strains, communities, and experimental conditions. Part of the DOE ENIGMA Scientific Focus Area studying microbial community function.

Key data:
- 596 sampling locations with geographic coordinates
- 3,365 taxa with NCBI taxonomy IDs
- 6,705 genomes
- 15,015 genes
- Experimental strains and conditions

---

## Table Summary

### Scientific Data Tables (sdt_*)

| Table | Row Count | Description |
|-------|-----------|-------------|
| `sdt_enigma` | 1 | Root entity |
| `sdt_location` | 596 | Sampling locations with coordinates |
| `sdt_taxon` | 3,365 | Taxonomic entities with NCBI IDs |
| `sdt_genome` | 6,705 | Genome records |
| `sdt_gene` | 15,015 | Gene records |
| `sdt_sample` | varies | Environmental samples |
| `sdt_community` | varies | Microbial community data |
| `sdt_strain` | varies | Laboratory strains |
| `sdt_condition` | varies | Experimental conditions |
| `sdt_protocol` | varies | Experimental protocols |
| `sdt_assembly` | varies | Genome assemblies |
| `sdt_reads` | varies | Sequencing reads |
| `sdt_bin` | varies | Metagenomic bins |
| `sdt_tnseq_library` | varies | TnSeq mutant libraries |
| `sdt_dubseq_library` | varies | DubSeq libraries |
| `sdt_image` | varies | Microscopy images |

### Data/Process Tables (ddt_*, sys_*)

| Table | Description |
|-------|-------------|
| `ddt_brick*` | Data brick tables (numerical data arrays) |
| `ddt_ndarray` | N-dimensional array data |
| `sys_oterm` | Ontology terms |
| `sys_process` | Computational processes |
| `sys_process_input/output` | Process I/O tracking |
| `sys_typedef` | Type definitions |

---

## Key Table Schemas

### `sdt_location`

| Column | Type | Description |
|--------|------|-------------|
| `sdt_location_id` | string | **Primary Key** |
| `sdt_location_name` | string | Location name |
| `latitude_degree` | string | Latitude |
| `longitude_degree` | string | Longitude |
| `continent_sys_oterm_id` | string | Continent ontology term ID |
| `continent_sys_oterm_name` | string | Continent name |
| `country_sys_oterm_id` | string | Country ontology term ID |
| `country_sys_oterm_name` | string | Country name |
| `region` | string | Region name |
| `biome_sys_oterm_id` | string | Biome ontology term ID |
| `biome_sys_oterm_name` | string | Biome name |
| `feature_sys_oterm_id` | string | Feature ontology term ID |
| `feature_sys_oterm_name` | string | Feature name |

### `sdt_taxon`

| Column | Type | Description |
|--------|------|-------------|
| `sdt_taxon_id` | string | **Primary Key** |
| `sdt_taxon_name` | string | Taxon name |
| `ncbi_taxid` | string | NCBI taxonomy ID |

### `sdt_strain`

| Column | Type | Description |
|--------|------|-------------|
| `sdt_strain_id` | string | **Primary Key** |
| `sdt_strain_name` | string | Strain name |
| `sdt_strain_description` | string | Description |
| `sdt_genome_name` | string | Associated genome |
| `derived_from_sdt_strain_name` | string | Parent strain |
| `sdt_gene_names_changed` | string | Modified genes |

### `sdt_condition`

| Column | Type | Description |
|--------|------|-------------|
| `sdt_condition_id` | string | **Primary Key** |
| `sdt_condition_name` | string | Condition name |

---

## Pitfalls

- Many tables had schema timeouts during API introspection; schemas above are partial.
- Data brick tables (`ddt_brick*`) contain numerical arrays and may have non-standard schemas.
- The `sys_*` tables are system/metadata tables, not primary scientific data.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.

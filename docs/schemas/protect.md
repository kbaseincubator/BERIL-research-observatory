# PROTECT GenomeDepot Database Schema Documentation

**Database**: `protect_genomedepot`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: PROTECT
**Last Updated**: 2026-02-11

---

## Overview

Pathogen genome browser database using the GenomeDepot format. Contains genome, gene, annotation, strain, sample, and taxon data for pathogen surveillance.

---

## Table Summary

| Table | Row Count | Description |
|-------|-----------|-------------|
| `browser_genome` | varies | Genome records |
| `browser_gene_sampled` | varies | Sampled gene records |
| `browser_annotation_sampled` | varies | Sampled annotations |
| `browser_strain` | varies | Strain information |
| `browser_sample` | varies | Sample metadata |
| `browser_taxon` | varies | Taxonomic information |

---

## Key Table Schemas

### `browser_genome`

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | **Primary Key** |
| `name` | string | Genome name |
| `description` | string | Description |
| `contigs` | string | Number of contigs |
| `size` | string | Genome size |
| `genes` | string | Number of genes |
| `json_url` | string | JSON metadata URL |
| `pub_date` | string | Publication date |
| `external_url` | string | External link |
| `external_id` | string | External identifier |
| `gbk_filepath` | string | GenBank file path |
| `sample_id` | string | FK -> `browser_sample` |
| `strain_id` | string | FK -> `browser_strain` |
| `taxon_id` | string | FK -> `browser_taxon` |

### `browser_gene_sampled`

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | **Primary Key** |
| `name` | string | Gene name |
| `locus_tag` | string | Locus tag |
| `type` | string | Feature type |
| `start` | string | Start position |
| `end` | string | End position |
| `strand` | string | Strand |
| `function` | string | Gene function |
| `contig_id` | string | FK -> contig |
| `genome_id` | string | FK -> `browser_genome` |
| `operon_id` | string | Operon identifier |
| `protein_id` | string | Protein identifier |

---

## Pitfalls

- Most schema introspection calls timed out for this database.
- Uses "sampled" table variants (`browser_gene_sampled`) rather than full tables.
- Smaller schema compared to the PhageFoundry genome browsers.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.

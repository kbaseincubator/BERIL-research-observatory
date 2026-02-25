# BacDive Module

## Overview
BacDive (Bacterial Diversity Metadatabase) is the world's largest standardized database for bacterial and archaeal strain-level phenotypic information. It provides structured data on growth conditions, isolation source, metabolite utilization, enzyme activities, oxygen tolerance, morphology, and genome accessions for ~97K strains.

**Database**: `kescience_bacdive`
**Generated**: 2026-02-23
**Source**: [BacDive](https://bacdive.dsmz.de/) (DSMZ, Leibniz Institute)
**API**: REST API v2 at `api.bacdive.dsmz.de`, Python client `bacdive` v2.0.0

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `strain` | 97,334 | Core strain info: BacDive ID, NCBI taxid, species, type strain status, DSM number |
| `taxonomy` | 97,334 | Full LPSN taxonomy: domain through species with full scientific name |
| `culture_condition` | 186,962 | Growth media names and temperatures with growth results |
| `isolation` | 57,970 | Isolation source, country, continent, hierarchical source categories |
| `physiology` | 97,334 | Gram stain, cell shape, motility, oxygen tolerance, murein type, AI predictions |
| `metabolite_utilization` | 988,259 | Per-compound utilization results (+/-/produced) with ChEBI IDs |
| `sequence_info` | 81,294 | Genome (GCA) and 16S accessions, GC content |
| `enzyme` | 642,947 | Enzyme activities with EC numbers |

## Key Table Schemas

### strain
Core strain metadata.
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | BacDive strain ID (primary key) |
| `dsm_number` | string | DSM culture collection number |
| `description` | string | Strain description |
| `ncbi_taxid` | string | NCBI taxonomy ID |
| `ncbi_taxid_match_level` | string | Taxonomy match level (species, genus, etc.) |
| `species_name` | string | Species name |
| `strain_designation` | string | Strain designation |
| `type_strain` | string | Whether this is a type strain ("yes"/"no") |
| `keywords` | string | Semicolon-separated keywords |
| `doi` | string | BacDive DOI for this strain entry |

### taxonomy
Full taxonomic classification (LPSN preferred).
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | FK to strain table |
| `domain` | string | Bacteria or Archaea |
| `phylum` | string | Phylum |
| `tax_class` | string | Class (column renamed from `class` to avoid SQL reserved word) |
| `tax_order` | string | Order (column renamed from `order` to avoid SQL reserved word) |
| `family` | string | Family |
| `genus` | string | Genus |
| `species` | string | Binomial species name |
| `full_name` | string | Full scientific name with authority |

### metabolite_utilization
Per-compound utilization test results. Largest table (~1M rows).
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | FK to strain table |
| `compound_name` | string | Metabolite/compound name |
| `chebi_id` | string | ChEBI chemical identifier |
| `utilization` | string | Result: positive, negative, produced, variable, weak, etc. |

### isolation
Isolation source with hierarchical categorization.
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | FK to strain table |
| `sample_type` | string | Free-text sample type description |
| `country` | string | Country of isolation |
| `continent` | string | Continent |
| `geographic_location` | string | Specific geographic location |
| `cat1` | string | Top-level source category (#Host, #Environmental, #Engineered) |
| `cat2` | string | Mid-level category (#Mammals, #Soil, #Built environment, etc.) |
| `cat3` | string | Fine-level category (#Human, #Clean room, etc.) |

### physiology
Morphological and physiological characteristics.
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | FK to strain table |
| `gram_stain` | string | Gram stain result (positive, negative, variable) |
| `cell_shape` | string | Cell morphology (rod, coccus, etc.) |
| `motility` | string | Motility (yes, no) |
| `oxygen_tolerance` | string | Oxygen requirement (aerobe, anaerobe, facultative, microaerophile, etc.) |
| `murein_type` | string | Cell wall murein chemotype |
| `predicted_gram` | string | AI-predicted Gram stain (deepG model, ≥90% confidence) |
| `predicted_motility` | string | AI-predicted motility |
| `predicted_oxygen` | string | AI-predicted oxygen tolerance |

### enzyme
Enzyme activity test results.
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | FK to strain table |
| `enzyme_name` | string | Enzyme name |
| `ec_number` | string | EC number |
| `activity` | string | Activity result (positive, negative, variable, etc.) |

### sequence_info
Genome and 16S rRNA sequence accessions.
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | FK to strain table |
| `accession_type` | string | Type: genome, 16S, gc_content |
| `accession` | string | Accession number (GCA_* for genomes, GenBank for 16S) |
| `database` | string | Source database (INSDC, etc.) |
| `assembly_level` | string | Genome assembly level (complete, scaffold, contig) |
| `description` | string | Sequence description |

### culture_condition
Growth media and temperature test results.
| Column | Type | Description |
|--------|------|-------------|
| `bacdive_id` | int | FK to strain table |
| `medium_name` | string | Growth medium name with composition |
| `growth` | string | Growth result (yes, positive, negative, etc.) |
| `medium_link` | string | Link to MediaDive medium definition |
| `temperature` | string | Growth temperature tested |
| `record_type` | string | Record type: medium or temperature |

## Data Richness Summary

| Dimension | Values |
|-----------|--------|
| Isolation: Host-associated | 17,580 strains |
| Isolation: Environmental | 15,815 strains |
| Isolation: Engineered | 6,737 strains |
| Gram-negative | 9,105 strains |
| Gram-positive | 6,089 strains |
| Aerobe | 8,559 strains |
| Anaerobe | 4,583 strains |
| Unique metabolites tested | 1,366 |
| Unique enzymes | 191 |
| Unique EC numbers | 103 |
| Genome accessions (GCA) | 27,502 |
| 16S sequences | 43,391 |

## Cross-Collection Links

| Target Collection | Join Key | Coverage |
|-------------------|----------|----------|
| `kescience_fitnessbrowser` | `strain.ncbi_taxid` → `organism.taxonomyId` | 12/48 FB organisms match (637 BacDive strains) |
| `kbase_ke_pangenome` | `sequence_info.accession` (GCA) → `genome.genome_id` | 27,502 genome accessions available for matching |
| `kescience_webofmicrobes` | `metabolite_utilization.compound_name` → `compound.compound_name` | 63 WoM metabolites have BacDive utilization data |
| `kbase_msd_biochemistry` | `enzyme.ec_number` → reaction EC annotations | 103 unique EC numbers |

## Known Limitations
- `tax_class` and `tax_order` columns renamed from `class`/`order` to avoid SQL reserved words
- Many physiology fields are sparsely populated (Gram stain: 15K/97K, oxygen: 23K/97K)
- Metabolite utilization data is heavily biased toward common test panel compounds (trehalose, arginine, glucose dominate)
- Genome accession format (GCA_*) needs prefix matching to pangenome genome IDs (which use GB_GCA_* or RS_GCF_*)
- NCBI taxid matching to FB organisms is at species level, not strain level

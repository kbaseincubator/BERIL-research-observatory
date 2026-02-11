# PlanetMicrobe Database Schema Documentation

**Databases**: `planetmicrobe_planetmicrobe`, `planetmicrobe_planetmicrobe_raw`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: PlanetMicrobe
**Last Updated**: 2026-02-11

---

## Overview

PlanetMicrobe is a platform for marine microbial ecology data. The database stores oceanographic sampling campaigns, environmental samples, sequencing experiments, and taxonomic/functional profiles from metagenomic and amplicon studies.

Two versions exist:
- `planetmicrobe_planetmicrobe`: Processed/curated data
- `planetmicrobe_planetmicrobe_raw`: Raw data

---

## Table Summary

| Table | Row Count | Description |
|-------|-----------|-------------|
| `campaign` | varies | Oceanographic campaigns/cruises |
| `sampling_event` | 1,151 | Sampling events with coordinates |
| `sample` | 2,371 | Environmental samples |
| `experiment` | 5,946 | Sequencing experiments |
| `library` | 0* | Sequencing libraries |
| `run` | varies | Sequencing runs |
| `project` | 0* | Research projects |
| `project_type` | varies | Project type definitions |
| `taxonomy` | varies | Taxonomic profiles |
| `go` | varies | GO term profiles |
| `pfam` | varies | PFAM domain profiles |
| `schema` | varies | Data schema definitions |
| `file_format` | varies | File format definitions |
| `file_type` | varies | File type definitions |
| `file` | varies | Data file records |
| `app` | varies | Application definitions |
| `user` | varies | User accounts |

*\*Zero counts may indicate empty or newly initialized tables.*

### Junction Tables

| Table | Description |
|-------|-------------|
| `project_to_file` | Project-file associations |
| `project_to_sample` | Project-sample associations |
| `run_to_file` | Run-file associations |
| `run_to_go` | Run-GO term associations |
| `run_to_pfam` | Run-PFAM associations |
| `run_to_taxonomy` | Run-taxonomy associations |
| `sample_to_sampling_event` | Sample-event associations |

---

## Key Table Schemas

### `sample`

| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | string | **Primary Key** |
| `schema_id` | string | Data schema reference |
| `accn` | string | Accession number |
| `locations` | string | Geographic locations |
| `number_vals` | string | Numeric metadata values |
| `string_vals` | string | String metadata values |
| `datetime_vals` | string | Temporal metadata values |

### `sampling_event`

| Column | Type | Description |
|--------|------|-------------|
| `sampling_event_id` | string | **Primary Key** |
| `sampling_event_type` | string | Event type |
| `campaign_id` | string | FK -> `campaign` |
| `name` | string | Event name |
| `locations` | string | Geographic coordinates |
| `start_time` | string | Start timestamp |
| `end_time` | string | End timestamp |

### `experiment`

| Column | Type | Description |
|--------|------|-------------|
| `experiment_id` | string | **Primary Key** |
| `sample_id` | string | FK -> `sample` |
| `name` | string | Experiment name |
| `accn` | string | Accession number |

### `library`

| Column | Type | Description |
|--------|------|-------------|
| `library_id` | string | **Primary Key** |
| `experiment_id` | string | FK -> `experiment` |
| `name` | string | Library name |
| `strategy` | string | Sequencing strategy |
| `source` | string | Source material |
| `selection` | string | Selection method |
| `protocol` | string | Protocol description |
| `layout` | string | Library layout |
| `length` | string | Fragment length |

---

## Pitfalls

- Several table schemas and counts timed out during introspection.
- `project` and `library` tables appear empty (count=0).
- Data appears to be relatively small-scale compared to other BERDL collections.
- The `_raw` database appears to mirror the processed database structure.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.

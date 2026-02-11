# KBase Phenotype Database Schema Documentation

**Database**: `kbase_phenotype`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: KBase
**Last Updated**: 2026-02-11

---

## Overview

Phenotype data from growth experiments, storing experimental conditions and measurements. Currently contains a small number of experiments (4) with 182,376 condition sets and 28,260 measurements.

---

## Table Summary

| Table | Row Count | Description |
|-------|-----------|-------------|
| `experiment` | 4 | Experiment definitions |
| `experimental_variable` | 17 | Variables measured in experiments |
| `experimental_context` | varies | Variable values per experiment |
| `condition_set` | 182,376 | Experimental condition combinations |
| `measurement` | 28,260 | Measured values |
| `experiment_x_measurement` | varies | Experiment-measurement junction |
| `protocol` | varies | Experimental protocols |

---

## Table Schemas

### `experiment`

| Column | Type | Description |
|--------|------|-------------|
| `experiment_id` | string | **Primary Key** |
| `name` | string | Experiment name |
| `description` | string | Experiment description |
| `protocol_id` | string | FK -> `protocol` |
| `created_at` | string | Creation timestamp |
| `contributor` | string | Data contributor |

### `experimental_context`

| Column | Type | Description |
|--------|------|-------------|
| `experiment_context_id` | string | **Primary Key** |
| `experiment_id` | string | FK -> `experiment` |
| `variable_id` | string | FK -> `experimental_variable` |
| `value` | string | Variable value |

---

## Pitfalls

- Small dataset (4 experiments). May be a pilot or in-progress collection.
- Some table schemas timed out during introspection.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.

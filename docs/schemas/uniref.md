# UniRef Protein Cluster Databases Schema Documentation

**Databases**: `kbase_uniref50`, `kbase_uniref90`, `kbase_uniref100`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: KBase
**Last Updated**: 2026-02-11

---

## Overview

Three UniRef protein cluster databases at different identity thresholds. UniRef provides clustered sets of protein sequences from UniProt to reduce redundancy and speed up searches.

- **UniRef100**: Identical sequences + subfragments (260K clusters, 950K members)
- **UniRef90**: 90% identity clusters (100K clusters)
- **UniRef50**: 50% identity clusters (100K clusters)

**Note**: These appear to be subset/sample datasets, not the full UniRef databases (which have hundreds of millions of clusters).

---

## Table Summary (per database)

| Table | UniRef50 | UniRef90 | UniRef100 | Description |
|-------|----------|----------|-----------|-------------|
| `cluster` | 100,000 | 100,000 | 260,000 | Cluster definitions |
| `clustermember` | varies | varies | 949,823 | Cluster membership |
| `crossreference` | varies | 203,452 | 1,339,674 | External DB cross-references |
| `entity` | varies | 100,000 | varies | Entity records |

---

## Table Schemas

### `clustermember`

| Column | Type | Description |
|--------|------|-------------|
| `cluster_id` | string | FK -> `cluster` |
| `entity_id` | string | FK -> `entity` |
| `is_representative` | string | Whether this is the cluster representative |
| `is_seed` | string | Whether this is the seed sequence |
| `score` | string | Membership score |

---

## Pitfalls

- These appear to be **partial datasets** (sample/pilot), not full UniRef.
- Schema introspection timed out for several tables.

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.

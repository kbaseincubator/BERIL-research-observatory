# UniProt Database Schema Documentation

**Database**: `kbase_uniprot`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: KBase
**Last Updated**: 2026-02-11

---

## Overview

UniProt cross-reference identifiers linking UniProt protein IDs to external databases.

---

## Table Summary

| Table | Row Count | Description |
|-------|-----------|-------------|
| `uniprot_identifier` | varies | UniProt ID cross-references |

---

## Table Schema

### `uniprot_identifier`

| Column | Type | Description |
|--------|------|-------------|
| `uniprot_id` | string | UniProt accession |
| `db` | string | External database name |
| `xref` | string | Cross-reference identifier |
| `description` | string | Description |
| `source` | string | Data source |
| `relationship` | string | Relationship type |

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.

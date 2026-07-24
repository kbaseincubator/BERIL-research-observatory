---
name: nmdc-naming-aliases-and-cruft
description: Dual dotted/underscore aliases, test databases, phantom and broken NMDC-named databases
metadata:
  type: reference
  provenance: audit finding
  tenant: nmdc, kbase, globalusers, user
  databases: [nmdc.metadata, kbase.nmdc_neon, globalusers.nmdc_core_test3, mamillerpa.nmdc_flattened_biosamples]
  currency: "2026-07-10"
  authority: nmdc_context_audit project (live catalog)
related: [nmdc-label-is-overloaded, nmdc-data-outside-nmdc-tenant]
---

# Naming aliases and cruft

`get_databases()` returns **20** entries containing "nmdc". Most are duplicates or
non-data. Knowing which to ignore saves confusion during discovery.

## Dual aliases (dotted vs underscore) — the same data, twice
Every tenant database is exposed under **two names**:
- Dotted `nmdc.metadata` — the Iceberg `catalog.namespace` form (use this in SQL).
- Underscore `nmdc_metadata` — the underlying Hive table
  (table property `berdl.source-hive-table=nmdc_metadata.biosample_set` confirms the link).

They resolve to the **same tables**. The inventory tooling surfaces only the dotted form;
`get_databases()` returns both. Prefer the dotted form and don't treat the two as distinct
datasets. This applies to `nmdc.results`/`nmdc_results`,
`nmdc.ncbi_biosamples`/`nmdc_ncbi_biosamples`, `nmdc.ref_data`/`nmdc_ref_data`.

## Test databases (not real data)
- `globalusers.nmdc_core_test3`, `globalusers.nmdc_core_test4` — one table each
  (`covstats_gold`); scratch/test artifacts.
- `globalusers_nmdc_core_test`, `_test2` — 0 tables.
- These are in a `globalusers` tenant that does not even appear in the standard inventory
  summary. Ignore for analysis.

## Phantom alias
- `kbase_nmdc_neon` (underscore form) resolves to **0 tables**, while `kbase.nmdc_neon`
  (dotted) has 8. Use the dotted form; the underscore alias is empty here.

## Broken user copies (do not use)
- `mamillerpa.nmdc_flattened_biosamples` and `my.nmdc_flattened_biosamples` — attempting to
  list tables raises `BadRequestException: Location does not exist:
  s3a://cdm-lake/users-sql-warehouse/mamillerpa/iceberg/nmdc_flattened_biosamples/.../metadata/...`.
  The Iceberg metadata pointer is dangling (data moved/deleted). These are personal
  scratch copies, not a maintained resource; either repair or drop them, but don't cite them.

## Takeaway
Of 20 "nmdc" database names, only **7** are real, maintained resources
([[nmdc-completeness-and-currency]]); the rest are aliases, tests, phantoms, or broken.

# Export Path Conventions

Use explicit, deterministic prefixes for export outputs.

## Recommended User Export Prefix

`s3a://cdm-lake/users-general-warehouse/<username>/exports/<project>/<run_id>/`

Example:

`s3a://cdm-lake/users-general-warehouse/jdoe/exports/pangenome-core/2026-02-17T1530Z/`

## Recommended Tenant Export Prefix

`s3a://cdm-lake/tenant-general-warehouse/<tenant>/exports/<project>/<run_id>/`

## Format Guidance

- `parquet`: best default for interoperability and efficient reads.
- `iceberg`: best when output will be registered in the Polaris catalog and queried repeatedly.
- `delta`: for scratch file output not registered in a catalog (legacy; new tables should use Iceberg).
- `json/csv`: only for smaller extracts and human-readable handoff.

## Naming Guidance

- Include date-time in UTC in path suffix.
- Include project or analysis label.
- Avoid overwriting previous runs unless rerun semantics are intentional.

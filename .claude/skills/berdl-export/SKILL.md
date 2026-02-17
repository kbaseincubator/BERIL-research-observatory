---
name: berdl-export
description: Export large BERDL query results from remote Spark to MinIO paths instead of returning bulky inline payloads. Use when query output is too large for interactive display, when a durable artifact is needed for downstream analysis, or when transfer should happen through object storage.
---

# BERDL Export Skill

## Overview

Use this skill when the result set is too large to return directly.
Run the query remotely, write to MinIO, then hand off retrieval to `/berdl-minio`.

## Preconditions

1. Ensure local dependencies are installed via `/berdl-query/scripts/bootstrap_client.sh`.
2. Ensure `KBASE_AUTH_TOKEN` is available locally.
3. Ensure BERDL JupyterHub session is active (open notebook).
4. Choose an export path in `s3a://cdm-lake/...`.

## Workflow

1. Validate query logic with a small `LIMIT` first.
2. Pick format and path:
   - Parquet for general data exchange.
   - Delta for queryable table-like outputs.
3. Run export:
   - `python scripts/export_sql.py --query "SELECT ..." --path "s3a://cdm-lake/users-general-warehouse/<user>/exports/run_20260217" --format parquet --mode overwrite`
   - Proxy mode: `python scripts/export_sql.py --berdl-proxy --query "SELECT ..." --path "s3a://cdm-lake/users-general-warehouse/<user>/exports/run_20260217" --format parquet --mode overwrite`
4. Capture generated manifest JSON for path and options used.
5. Use `/berdl-minio` to inspect/download artifacts.

## Where Results Go

- Results are written explicitly to the MinIO path passed to `--path`.
- Nothing is copied locally unless a follow-up download is performed.
- Exports are not automatic for normal query calls.

## Scripts

- `scripts/export_sql.py`: execute SQL and write output to MinIO path.
  - Supports `--berdl-proxy`, `--grpc-proxy`, `--https-proxy`, `--host-template`, `--port`.

## References

- `references/export-paths.md`: format choices and path conventions.

## Safety Rules

1. Do not export to root-level bucket paths; use user- or tenant-scoped prefixes.
2. Use deterministic file naming with date/time suffixes.
3. Prefer overwrite only for intentional reruns; otherwise use unique path per run.

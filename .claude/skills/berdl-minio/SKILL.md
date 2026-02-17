---
name: berdl-minio
description: Retrieve and use BERDL MinIO credentials and transfer result artifacts between BERDL object storage and the local machine. Use when exported query results need to be listed, downloaded, shared, or when only KBASE_AUTH_TOKEN is available and MinIO keys must be acquired.
---

# BERDL MinIO Skill

## Overview

Use this skill to work with BERDL MinIO from local tools.
It handles credential sourcing, MinIO client setup, and object retrieval operations.

## Credential Strategy

Use credentials in this order:
1. Existing `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` in environment or `.env`.
2. Derive credentials from BERDL remote environment using `berdl-remote` (authenticated by `KBASE_AUTH_TOKEN`).

## Workflow

1. Resolve credentials:
   - `python scripts/get_minio_creds.py --shell`
   - If remote bootstrap is needed: `python scripts/get_minio_creds.py --bootstrap-remote --shell`
2. Configure `mc`:
   - `bash scripts/configure_mc.sh berdl-minio https://minio.berdl.kbase.us`
3. List/download exported files:
   - `mc ls berdl-minio/cdm-lake/users-general-warehouse/<user>/exports/`
   - `mc cp --recursive berdl-minio/cdm-lake/users-general-warehouse/<user>/exports/run_20260217 ./exports/run_20260217`

## Scripts

- `scripts/get_minio_creds.py`: resolve MinIO keys locally or via BERDL remote context.
- `scripts/configure_mc.sh`: configure MinIO CLI alias and test connectivity.

## References

- `references/minio-endpoints.md`: environment endpoints and path patterns.

## Safety Rules

1. Never print full secrets in final user-facing summaries unless explicitly requested.
2. Do not commit credentials into repository files.
3. Prefer short-lived retrieval and local shell export for active sessions.

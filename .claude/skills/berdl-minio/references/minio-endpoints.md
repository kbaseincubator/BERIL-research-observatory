# BERDL MinIO Endpoints and Paths

## Endpoints

- Development UI: `https://minio-ui.dev.berdl.kbase.us`
- Staging UI: `https://minio-ui.stage.berdl.kbase.us`
- Production UI: `https://minio-ui.berdl.kbase.us`
- Production API endpoint (common default): `https://minio.berdl.kbase.us`

## Common Bucket/Prefix Patterns

- Personal files:
  - `s3://cdm-lake/users-general-warehouse/<username>/`
- Personal SQL warehouse:
  - `s3://cdm-lake/users-sql-warehouse/<username>/`
- Tenant files:
  - `s3://cdm-lake/tenant-general-warehouse/<tenant>/`
- Tenant SQL warehouse:
  - `s3://cdm-lake/tenant-sql-warehouse/<tenant>/`

## Practical Retrieval Pattern

1. Resolve credentials.
2. Configure `mc` alias.
3. List prefix before download.
4. Copy only required run folder(s) locally.

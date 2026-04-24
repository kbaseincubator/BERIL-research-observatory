# BERDL Ingest Session Report: On-Cluster Execution

**Date:** 2026-04-03
**Operator:** Mark Andrew Miller (mamillerpa)
**Environment:** `jupyter-mamillerpa` on BERDL notebook server (hub.berdl.kbase.us)
**Namespace:** `nmdc_flattened_biosamples` (existing, 6 tables -> 10 tables)

## Summary

Four new Parquet tables were ingested into the existing `nmdc_flattened_biosamples`
Delta Lake namespace to support OBI ontology coverage analysis. The `/berdl-ingest`
skill was designed for off-cluster use and required manual adaptation to run
on the notebook server directly.

## What was ingested

| Table | Rows | Source size |
|-------|------|-------------|
| `flattened_data_generation` | 10,423 | 363 KB |
| `flattened_data_object` | 226,864 | 7.6 MB |
| `flattened_workflow_execution` | 24,698 | 5.5 MB |
| `flattened_workflow_execution_mags` | 40,580 | 49 MB |

All row counts verified against source and via the handoff verification query
(11 `nmdc_type` values totaling 24,698 rows in `flattened_workflow_execution`).

## On-cluster vs. off-cluster: what we changed

### 1. Skipped the entire proxy/tunnel chain

The `/berdl-ingest` skill and its `ingest_lib.py` `initialize()` function assume
off-cluster execution with:

- SSH SOCKS tunnels on ports 1337 and 1338
- pproxy on port 8123 bridging SOCKS to HTTP
- `spark_connect_remote` library for authenticated Spark Connect over the proxy
- `berdl-remote login/spawn` to start the JupyterHub server remotely
- MinIO access via `~/.mc/config.json` credentials routed through pproxy

**On-cluster, none of this is needed.** The notebook server has:

- `SPARK_CONNECT_URL` env var pointing directly at the sidecar (`sc://jupyter-mamillerpa.jupyterhub-prod:15002`)
- `MINIO_ENDPOINT_URL`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` in the environment
- `berdl_notebook_utils.setup_spark_session.get_spark_session()` handling Spark auth natively
- Direct HTTPS access to MinIO at `minio.berdl.kbase.us`

### 2. Used `berdl_notebook_utils` instead of `spark_connect_remote`

Off-cluster, the skill uses `scripts/get_spark_session.py` which imports
`spark_connect_remote.create_spark_session()`. This package is not installed
on the notebook server (and doesn't need to be).

On-cluster, `berdl_notebook_utils.setup_spark_session.get_spark_session()` is
pre-installed and handles KBase token authentication via gRPC headers automatically.

### 3. Built MinIO client from environment variables

Off-cluster, the skill reads `~/.mc/config.json` (alias `berdl-minio`) and routes
through the pproxy. On-cluster, we constructed the `minio.Minio` client directly
from environment variables:

```python
from minio import Minio
client = Minio(
    endpoint=os.environ["MINIO_ENDPOINT_URL"].replace("https://", ""),
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=True,
)
```

No proxy manager needed. We did also run `mc alias set berdl-minio` using these
env vars, but that was only necessary for `mc` CLI usage, not the Python ingest.

### 4. Did not use the notebook template

The reference notebook (`ingest.ipynb`) imports `ingest_lib.initialize()` which
calls `_check_ssh_tunnels()` and fails immediately on-cluster. Rather than patching
the template, we ran the ingest as a direct Python script:

1. Upload Parquet files to MinIO bronze via `minio.fput_object()`
2. `spark.read.parquet()` from bronze path
3. `sdf.write.format("delta").mode("overwrite").save()` to silver path
4. `CREATE TABLE IF NOT EXISTS ... USING DELTA LOCATION` to register in catalog
5. `REFRESH TABLE` and `SELECT COUNT(*)` to verify

## Data issue: Parquet UUID type incompatibility

`flattened_data_object.parquet` contained an `md5_checksum` column stored as
`fixed_size_binary[16]`. Spark's Parquet reader interprets 16-byte fixed binary
as a UUID logical type and raises:

```
AnalysisException: [PARQUET_TYPE_ILLEGAL] Illegal Parquet type: FIXED_LEN_BYTE_ARRAY (UUID)
```

**Fix:** Re-exported the file via pandas, converting the raw bytes to hex strings:

```python
df["md5_checksum"] = df["md5_checksum"].apply(
    lambda x: x.hex() if isinstance(x, bytes) else str(x) if x is not None else None
)
```

**Root cause:** The upstream `flatten_nmdc_collections.py` pipeline (DuckDB -> Parquet
with ZSTD) stores MD5 hashes as `fixed_size_binary[16]`, which is semantically correct
but incompatible with Spark 4.x Parquet reader. The upstream script should cast these
to `VARCHAR` before Parquet export, or the ingest skill should detect and handle this
type during the schema inspection step.

## Recommendations for repo maintainers

### 1. Add on-cluster mode to `ingest_lib.py`

`initialize()` should detect when it's running on the notebook server (e.g. check for
`SPARK_CONNECT_URL` or `MINIO_ACCESS_KEY` in the environment) and skip the tunnel/proxy
chain. Suggested approach:

```python
def initialize():
    if os.environ.get("SPARK_CONNECT_MODE_ENABLED"):
        # On-cluster path
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()
        minio_client = _build_minio_client_from_env()
    else:
        # Off-cluster path (existing code)
        _check_ssh_tunnels()
        _start_pproxy_if_needed()
        ...
```

### 2. Add `fixed_size_binary` handling to the Parquet ingest path

The notebook template's Parquet path reads files directly with `spark.read.parquet()`.
When Spark encounters `fixed_size_binary` columns it fails. The skill should either:

- Pre-screen Parquet schemas with PyArrow before uploading to bronze
- Convert incompatible types (fixed binary -> string) during the detect/schema step
- Document this as a known limitation with a workaround

### 3. `_build_minio_client()` should support env var credentials

Currently it only reads from `~/.mc/config.json`. On-cluster, credentials are in
`MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` / `MINIO_ENDPOINT_URL`. A fallback to
env vars would make the library work in both contexts without configuration.

### 4. The `already_ingested/` convention is undocumented

The source directory had a subdirectory `already_ingested/` containing 6 Parquet files
from a prior ingest. This convention (separating already-loaded files) is not part of
the skill's workflow. Consider either documenting it or having the skill track ingested
files via the progress log so users don't need to manually segregate them.

## Paths

- **Bronze:** `s3a://cdm-lake/tenant-general-warehouse/nmdc/datasets/nmdc_flattened_biosamples/`
- **Silver:** `s3a://cdm-lake/tenant-sql-warehouse/nmdc/nmdc_flattened_biosamples.db/`
- **Source handoff:** `projects/obi_ontology_coverage/INGEST_HANDOFF.md`
- **Flattening instructions:** `projects/obi_ontology_coverage/flatten-nmdc-workflow-collections-instructions-2026-04-03.md`

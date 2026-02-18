---
name: berdl-query
description: Run SQL queries from a local machine against a provisioned BERDL Spark cluster using spark_connect_remote. Use when the user wants remote Spark compute with local control, needs clarity on connection and timeout behavior, or wants to return small/medium results directly before exporting large outputs.
---

# BERDL Query Skill

## Overview

Use this skill to run BERDL Spark queries locally while computation runs on the remote BERDL cluster.
Use this as the default query path for interactive analysis and API-like result retrieval.

## Preconditions

1. `KBASE_AUTH_TOKEN` set in environment or `.env`.
2. `.venv-berdl` created: `bash scripts/bootstrap_client.sh` (one-time setup).
3. JupyterHub session active: log in at `https://hub.berdl.kbase.us` and open a notebook so your Spark Connect service is running.
4. **Proxy running**: BERDL services are not directly reachable from external networks. Read `references/proxy-setup.md` for the full setup. The short version:
   - SSH SOCKS tunnels on ports 1337 and 1338 (requires user credentials — ask the user to start these)
   - pproxy HTTP bridge on port 8123 (Claude can start this from `.venv-berdl`)
   - Verify with: `lsof -i :1337 -i :1338 -i :8123 | grep LISTEN`

## Workflow

1. Activate the local Python environment:
   - `source .venv-berdl/bin/activate`
2. Verify proxy is running (check ports 1337, 1338, 8123). Start pproxy if needed.
3. Execute a probe query:
   - `python scripts/run_sql.py --berdl-proxy --query "SHOW DATABASES"`
4. Run the target SQL query with bounded result size:
   - `python scripts/run_sql.py --berdl-proxy --query "SELECT * FROM db.table ORDER BY id" --limit 500 --output /tmp/query_result.json`
5. If result size is large, use export mode in this same skill:
   - `python scripts/export_sql.py --berdl-proxy --query "SELECT ..." --path "s3a://cdm-lake/users-general-warehouse/<user>/exports/<run_id>" --format parquet --mode overwrite`

## Connection and Timeout Behavior

- The connection is maintained by the local process, the proxy chain, and the BERDL JupyterHub session.
- If your JupyterHub session idles out, reconnect by re-opening a notebook and rerunning the query.
- If an SSH tunnel drops, queries will fail with "Connect call failed" or "authentication service timed out". Check tunnels and restart dead ones.
- Long queries can fail if network/session state changes; retry after reconnecting.
- Keep a JupyterHub tab open during long operations for better reliability.

## Monitoring Running Queries

- Check Spark/JupyterHub monitoring while queries are running.
- For local polling, issue lightweight probe queries between large operations.
- If the client is blocked on a long action, assume the remote job is active unless an error is returned.

## Where Results Go

- Query actions return data to local client memory by default.
- Results are not automatically persisted to MinIO.
- For large outputs, explicitly export to MinIO with `scripts/export_sql.py` and retrieve with `/berdl-minio`.

## Result Size Guidance

- Small/medium interactive results: return inline with explicit `limit`.
- Large results: export to object storage.
- Read `references/query-limits.md` for decision thresholds.

## Running Notebooks Locally

Existing BERDL notebooks use `spark = get_spark_session()` to create a Spark session.
A local drop-in replacement is provided in `scripts/get_spark_session.py`. When the
`.venv-berdl` environment is active, it is importable with no path changes:

```python
from get_spark_session import get_spark_session
spark = get_spark_session()
# spark.sql(...), df.toPandas(), etc. work identically to JupyterHub
```

This uses `spark_connect_remote` with proxy settings under the hood.
The proxy chain (SSH tunnels + pproxy) must be running.

## Scripts

- `scripts/bootstrap_client.sh`: install required local packages into `.venv-berdl`. Also makes `scripts/` importable from the venv via a `.pth` file.
- `scripts/get_spark_session.py`: drop-in replacement for the BERDL JupyterHub `get_spark_session()`. Uses `spark_connect_remote` with proxy settings.
- `scripts/run_sql.py`: run bounded SQL query and emit JSON output.
  - Supports `--berdl-proxy`, `--grpc-proxy`, `--https-proxy`, `--host-template`, `--port`.
- `scripts/export_sql.py`: run SQL and write output to MinIO/object storage.
  - Supports `--berdl-proxy`, `--grpc-proxy`, `--https-proxy`, `--host-template`, `--port`.
  - Supports format/mode/partition controls for large-result workflows.

## References

- `references/proxy-setup.md`: how to set up SSH tunnels and pproxy for local access.
- `references/query-limits.md`: query tiering and fallback guidance.
- `references/export-paths.md`: recommended MinIO path conventions and format choices.

## Safety Rules

1. Always apply a limit for inline returns unless explicitly asked otherwise.
2. Prefer `ORDER BY` in paginated queries.
3. Use `scripts/export_sql.py` when response volume is large.

---
name: berdl-query
description: Run SQL queries from a local machine against a provisioned BERDL Spark cluster using spark_connect_remote. Use when the user wants remote Spark compute with local control, needs clarity on connection and timeout behavior, or wants to return small/medium results directly before exporting large outputs.
---

# BERDL Query Skill

## Overview

Use this skill to run BERDL Spark queries locally while computation runs on the remote BERDL cluster.
Use this as the default query path for interactive analysis and API-like result retrieval.

## Preconditions

1. Ensure `KBASE_AUTH_TOKEN` is set in environment or stored in `.env`.
2. Log in to BERDL JupyterHub and open at least one notebook so your personal Spark Connect service is active.
3. Install local client dependencies with `scripts/bootstrap_client.sh` on new machines.

## Workflow

1. Activate the local Python environment.
2. Execute a probe query:
   - `python scripts/run_sql.py --query "SHOW DATABASES"`
   - Proxy mode: `python scripts/run_sql.py --berdl-proxy --query "SHOW DATABASES"`
3. Run the target SQL query with bounded result size:
   - `python scripts/run_sql.py --query "SELECT * FROM db.table ORDER BY id" --limit 500 --output /tmp/query_result.json`
4. If result size is large, switch to `/berdl-export` instead of returning rows inline.

## Connection and Timeout Behavior

- The connection is maintained by the local process and BERDL JupyterHub session.
- If your JupyterHub session idles out, reconnect by re-opening a notebook and rerunning the query.
- Long queries can fail if network/session state changes; retry after reconnecting.
- Keep a JupyterHub tab open during long operations for better reliability.

## Monitoring Running Queries

- Check Spark/JupyterHub monitoring while queries are running.
- For local polling, issue lightweight probe queries between large operations.
- If the client is blocked on a long action, assume the remote job is active unless an error is returned.

## Where Results Go

- Query actions return data to local client memory by default.
- Results are not automatically persisted to MinIO.
- For large outputs, explicitly export to MinIO with `/berdl-export` and retrieve with `/berdl-minio`.

## Result Size Guidance

- Small/medium interactive results: return inline with explicit `limit`.
- Large results: export to object storage.
- Read `references/query-limits.md` for decision thresholds.

## Scripts

- `scripts/bootstrap_client.sh`: install required local packages.
- `scripts/run_sql.py`: run bounded SQL query and emit JSON output.
  - Supports `--berdl-proxy`, `--grpc-proxy`, `--https-proxy`, `--host-template`, `--port`.

## References

- `references/query-limits.md`: query tiering and fallback guidance.

## Safety Rules

1. Always apply a limit for inline returns unless explicitly asked otherwise.
2. Prefer `ORDER BY` in paginated queries.
3. Move to `/berdl-export` when response volume is large.

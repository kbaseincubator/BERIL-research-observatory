---
name: berdl
description: Query the KBase BERDL (BER Data Lakehouse) databases. Use when the user asks to explore pangenome data, query species information, get genome statistics, analyze gene clusters, access functional annotations, or query biochemistry data.
allowed-tools: Bash, Read
---

# BERDL Data Lakehouse Query Skill

Query the KBase BERDL Data Lakehouse containing pangenome and biochemistry data.

## Step 0: Environment Check

Run before anything else:

```bash
python scripts/berdl_env.py --check
```

If it exits non-zero, follow the printed next steps exactly. Do not proceed with any query until this passes. The location reported (`on-cluster` vs `off-cluster`) selects the execution path for every subsequent step.

## Discovery (live)

Run the canonical discovery flow before any query. The set of accessible databases depends on the authenticated user; do not assume from prose.

```python
import berdl_notebook_utils

databases = berdl_notebook_utils.get_databases(return_json=False)            # → list[str]
tables    = berdl_notebook_utils.get_tables("DATABASE", return_json=False)   # → list[str]
schema    = berdl_notebook_utils.get_table_schema("DATABASE", "TABLE", detailed=True, return_json=False)  # → list[dict] with name, dataType, description, isPartition, ...

# For table-level COMMENT and TBLPROPERTIES:
spark.sql("DESCRIBE EXTENDED DATABASE.TABLE").toPandas()
```

> **Discovery returns JSON by default.** Always pass `return_json=False`. Without it you get a JSON *string*, and `in`, iteration, and `display()` will silently misbehave.

For pattern guidance, read [`modules/query-patterns.md`](modules/query-patterns.md) (universal SQL safety/perf rules) and [`modules/cross-database.md`](modules/cross-database.md) (cross-DB join recipes).

For curated database-specific gotchas (NULL conventions, ID formats, missing-column workarounds, JOIN-key surprises, large-table guards), grep `docs/pitfalls.md` for the database name. Example: `grep -A 20 "^## kbase_ke_pangenome$" docs/pitfalls.md`.

**Read the appropriate module** for database-specific tables, schemas, and query patterns.
**Read [query-patterns.md](modules/query-patterns.md)** before writing any SQL — it contains mandatory safety rules and performance guidance.

## Query Execution

Choose the query path from the environment detected by `scripts/detect_berdl_environment.py`:

- **On-cluster / BERDL JupyterHub**: use the active Spark session directly. Do not add `--berdl-proxy`.
- **Off-cluster / local machine**: use `/berdl-query` or the local `scripts/run_sql.py --berdl-proxy` wrapper.

On-cluster, execute actual SQL with native Spark SQL:

```python
df = spark.sql("SELECT * FROM database.table LIMIT 10")
```

Off-cluster, use the bounded wrapper when appropriate:

```bash
python scripts/run_sql.py --berdl-proxy --query "SELECT * FROM database.table ORDER BY id" --limit 500 --output /tmp/query_result.json
```

Use SQL for counts and samples:

```sql
SELECT COUNT(*) AS n FROM database.table;
SELECT * FROM database.table LIMIT 5;
```

Avoid BERDL MCP query operations for SQL execution, including `mcp_query_table`, `mcp_select_table`, `mcp_count_table`, `mcp_sample_table`, and REST `/delta/tables/query`.

## Common Patterns

### Pagination
```sql
SELECT * FROM database.table
ORDER BY id
LIMIT 1000 OFFSET 0  -- First page

SELECT * FROM database.table
ORDER BY id
LIMIT 1000 OFFSET 1000  -- Second page
```

**Always use ORDER BY** for deterministic pagination.

### Output Formatting
```bash
... | python3 -m json.tool
```

## Instructions for Claude

1. **Read auth token** from `.env` first
2. **Read [query-patterns.md](modules/query-patterns.md)** — contains mandatory validation checklist and performance tiers
3. **Read the appropriate module** for the target database (pangenome, biochemistry, etc.)
4. **Read [cross-database.md](modules/cross-database.md)** if the query spans multiple databases
5. **Start with helper discovery** if unfamiliar with available databases, tables, or schemas
6. **Check row counts** with bounded Spark SQL before querying large tables
7. **Use Spark SQL** through `spark.sql(query)` or `scripts/run_sql.py`
8. **Run the validation checklist** from query-patterns.md before executing any SQL query
9. **Handle pagination** for large result sets
10. **Include ORDER BY** in queries for consistent pagination

### Query Validation (mandatory)

Before executing any query, verify against the checklist in [query-patterns.md](modules/query-patterns.md):
- Partitioned column filter present?
- Large tables guarded?
- Results bounded?
- Types cast correctly?
- Species IDs quoted?
- Annotation NULLs filtered?
- ORDER BY for pagination?
- Correct JOIN keys?

### Performance Tiers

| Expected Result Size | Strategy |
|---|---|
| < 100K rows | Bounded Spark SQL, `.toPandas()` OK |
| 100K – 10M rows | Filter + aggregate in SQL first |
| > 10M rows | PySpark on JupyterHub only |

## Error Handling

| Error | Meaning | Solution |
|---|---|---|
| 504 Gateway Timeout | Query took too long | Simplify query, add filters, switch to JupyterHub |
| 524 Origin Timeout | Server didn't respond | Retry after a few seconds |
| 503 "cannot schedule new futures" | Spark executor restarting | Wait 30s, retry |
| Empty response | Query failed silently | Check query syntax, verify table exists |
| Auth errors | Invalid or expired token | Validate `KBASE_AUTH_TOKEN` in `.env` |

**Rule of thumb**: Use `spark.sql()` directly in JupyterHub for complex, long-running, or large-result queries.

## Adding New Databases

Use the `/berdl-discover` skill to introspect new databases and generate module files.

## Scripts

The following scripts exist and are referenced by skills. **Do not invent script names** — only the paths below exist. If you need behavior not covered here, ask the user.

| Script | Purpose |
|---|---|
| `scripts/berdl_env.py` | Canonical environment check (Step 0 of every BERDL skill) |
| `scripts/berdl_inventory.py` | Pretty-printed inventory (tenant / database / table count / sample tables) |
| `scripts/detect_berdl_environment.py` | Underlying detector (called by `berdl_env.py`) |
| `scripts/run_sql.py` | Bounded SQL via Spark Connect (`--berdl-proxy` for off-cluster) |
| `scripts/export_sql.py` | SQL → MinIO export (`--berdl-proxy` for off-cluster) |
| `scripts/get_minio_creds.py` | MinIO credential resolver |
| `scripts/configure_mc.sh` | MinIO CLI alias setup |
| `scripts/get_spark_session.py` | Local drop-in for the BERDL `get_spark_session()` |
| `scripts/bootstrap_client.sh` | Create `.venv-berdl` and install query packages |
| `scripts/bootstrap_ingest.sh` | Install ingest packages on top of `.venv-berdl` |
| `scripts/ingest_lib.py` | JH-side ingest helpers |
| `scripts/ingest_preflight.py` | Pre-flight ingest plan printer |
| `scripts/start_pproxy.sh` | pproxy startup |
| `scripts/discover_berdl_collections.py` | UI snapshot builder |
| `scripts/build_data_cache.py` | UI data cache builder |

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

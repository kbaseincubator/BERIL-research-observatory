---
name: berdl
description: Query the KBase BERDL (BER Data Lakehouse) databases. Use when the user asks to explore pangenome data, query species information, get genome statistics, analyze gene clusters, access functional annotations, or query biochemistry data.
allowed-tools: Bash, Read
---

# BERDL Data Lakehouse Query Skill

Query the KBase BERDL Data Lakehouse containing pangenome and biochemistry data.

## Available Databases

| Database | Module | Description |
|----------|--------|-------------|
| `kbase_ke_pangenome` | [pangenome.md](modules/pangenome.md) | 293K genomes, 27K species pangenomes |
| `kbase_msd_biochemistry` | [biochemistry.md](modules/biochemistry.md) | ModelSEED reactions and compounds |
| `kescience_fitnessbrowser` | See [docs/schemas/fitnessbrowser.md](../../../docs/schemas/fitnessbrowser.md) | 48 organisms, 27M fitness measurements |
| `kbase_genomes` | See [docs/schemas/genomes.md](../../../docs/schemas/genomes.md) | 293K genomes, 253M protein sequences |
| `microbialdiscoveryforge` (MinIO) | Use live discovery; see relevant docs in [docs/schemas/](../../../docs/schemas/) when available | Observatory project data on MinIO object storage |

**Cross-database patterns**: [cross-database.md](modules/cross-database.md) — joining pangenome ↔ biochemistry ↔ fitness ↔ NCBI

Use live access-aware discovery for the current database inventory.

**Read the appropriate module** for database-specific tables, schemas, and query patterns.
**Read [query-patterns.md](modules/query-patterns.md)** before writing any SQL — it contains mandatory safety rules and performance guidance.

## Access-Aware Discovery

Use `berdl_notebook_utils` helper functions to discover only what the current user can access:

```python
import berdl_notebook_utils

databases = berdl_notebook_utils.get_databases()
tables = berdl_notebook_utils.get_tables("DATABASE_NAME")
schema = berdl_notebook_utils.get_table_schema("DATABASE_NAME", "TABLE_NAME")
```

Use `docs/schemas/` only as supporting table/column documentation. Do not treat static docs as the source of truth for current access or inventory.

Avoid using raw discovery SQL such as `spark.sql("SHOW DATABASES")` or `spark.sql("SHOW TABLES ...")`; those commands do not apply BERDL access-aware filtering.

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

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

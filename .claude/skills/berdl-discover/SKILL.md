---
name: berdl-discover
description: Discover and document BERDL databases. Use when the user wants to explore a new database, generate documentation for a database, or create a module file for the berdl skill.
allowed-tools: Bash, Read, Write
---

# BERDL Database Discovery Skill

This skill performs live discovery of BERDL databases using `berdl_notebook_utils` helpers and `DESCRIBE EXTENDED`. It does NOT generate module files. Curated database-specific gotchas live in `docs/pitfalls.md` (per-database H2 sections); structural facts come from the live system.

## Step 0: Environment Check

```bash
python scripts/berdl_env.py --check
```

Do not proceed if not ready.

## Discovery Workflow

### Step 1: List accessible databases

```python
import berdl_notebook_utils
databases = berdl_notebook_utils.get_databases(return_json=False)  # → list[str]
print(databases)
```

> Always pass `return_json=False`. The default returns a JSON *string*.

### Step 2: List tables in the target database

```python
tables = berdl_notebook_utils.get_tables("DATABASE_NAME", return_json=False)  # → list[str]
print(tables)
```

### Step 3: Per-column schema

```python
schema = berdl_notebook_utils.get_table_schema("DATABASE_NAME", "TABLE_NAME", detailed=True, return_json=False)
# schema is list[dict] with keys: name, dataType, nullable, description, isPartition
for col in schema:
    print(col)
```

The `description` field is the column COMMENT set at ingest. Legacy tables may have empty descriptions — that’s fine; do not fabricate.

### Step 4: Table-level metadata via DESCRIBE EXTENDED

On-cluster:
```python
spark.sql("DESCRIBE EXTENDED DATABASE_NAME.TABLE_NAME").toPandas()
```

Off-cluster:
```bash
uv run scripts/run_sql.py --berdl-proxy \
  --query "DESCRIBE EXTENDED DATABASE_NAME.TABLE_NAME" \
  --output /tmp/desc.json
```

This returns table COMMENT, TBLPROPERTIES, storage location, format, owner, created date.

### Step 5: Row counts (optional, on user request)

```python
spark.sql("SELECT COUNT(*) AS n FROM DATABASE_NAME.TABLE_NAME")
```

Skip for tables flagged as large in `docs/pitfalls.md` (e.g. `gene`, `genome_ani`, `reaction_similarity`). The agent should ask before running `COUNT(*)` on any table without an existing pitfall entry.

### Step 6: Identify cross-table relationships

Inspect column names ending in `_id` and match against other tables’ primary keys. Sample 2–5 rows when needed:

```python
spark.sql("SELECT * FROM DATABASE_NAME.TABLE_NAME LIMIT 5")
```

### Step 7: Propose pitfall additions

If discovery surfaces non-derivable knowledge (NULL convention, ID format, missing-column workaround, JOIN-key gotcha, large-table guard), propose appending it to `docs/pitfalls.md` under the matching `## DATABASE_NAME` H2 section. Do not write a separate module file.

## Output

Present discovery results inline to the user: a compact summary of tables, schemas, and any new pitfalls proposed. Keep the output focused on what the user asked about — full structural snapshots are derivable on demand and need not be persisted.

## Error Handling

- **`berdl_env.py --check` fails:** stop. Surface the error.
- **`get_databases(return_json=False)` returns empty list:** the user has no DB access. Tell them; do not pretend.
- **`DESCRIBE EXTENDED` fails:** surface the error verbatim. Common cause: typo in database/table name, or table dropped between `get_tables()` and `DESCRIBE`.
- **Schema retrieval prints `Error retrieving schema for table ...`:** the underlying S3 files are missing for that table. Note in the user-facing output, do not crash.

Avoid raw `SHOW DATABASES` or `SHOW TABLES` for routine discovery — those bypass access-aware filtering. SHOW is allowed only for the off-cluster `/berdl_start` Phase 1.6 fallback when `berdl_notebook_utils` isn’t installed locally.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

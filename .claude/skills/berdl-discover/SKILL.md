---
name: berdl-discover
description: Discover and document BERDL databases. Use when the user wants to explore a new database, generate documentation for a database, or create a module file for the berdl skill.
allowed-tools: Bash, Read, Write
---

# BERDL Database Discovery Skill

This skill introspects BERDL databases with access-aware notebook helpers and generates documentation modules for use with the `berdl` skill.

## Discovery Workflow

When discovering a new database, follow these steps in order:

### Step 1: Start Spark

Use the correct Spark session pattern for the environment, then import helpers:

```python
import berdl_notebook_utils
```

### Step 2: List Accessible Databases

```python
databases = berdl_notebook_utils.get_databases()
display(databases)
```

### Step 3: List Tables in Target Database

```python
tables = berdl_notebook_utils.get_tables("DATABASE_NAME")
display(tables)
```

### Step 4: Get Schema for Each Table

```python
schema = berdl_notebook_utils.get_table_schema("DATABASE_NAME", "TABLE_NAME")
display(schema)
```

### Step 5: Get Row Counts

```python
spark.sql("SELECT COUNT(*) AS n FROM DATABASE_NAME.TABLE_NAME")
```

### Step 6: Sample Data

```python
spark.sql("SELECT * FROM DATABASE_NAME.TABLE_NAME LIMIT 5")
```

### Step 7: Identify Relationships

Look for foreign key patterns:
- Columns ending in `_id` that match other table names
- Columns with consistent naming across tables
- Sample data to confirm relationship patterns

## Output: Module File Template

After discovery, generate a module file at `.claude/skills/berdl/modules/{database_short_name}.md`:

```markdown
# {Database Name} Module

## Overview
{Brief description of what this database contains}

**Database**: `{database_name}`
**Generated**: {YYYY-MM-DD}

## Tables

| Table | Rows | Description |
|-------|------|-------------|
| `table_name` | {count} | {description inferred from columns/data} |

## Key Table Schemas

### {table_name}
| Column | Type | Description |
|--------|------|-------------|
| `column_name` | {type} | {description} |

## Table Relationships

{Describe foreign key relationships discovered}

- `table1.column` -> `table2.column`

## Common Query Patterns

### {Pattern Name}
{Brief description of what this query does}

```sql
SELECT ...
FROM {database}.{table}
...
```

## Pitfalls

{Any gotchas, NULL handling, performance notes discovered during exploration}
```

## Output: collections.yaml Entry Template

If the user wants to add the database to the UI, offer to update `ui/config/collections.yaml`:

```yaml
{database_short_name}:
  name: "{Human Readable Name}"
  description: "{Description}"
  database: "{database_name}"
  tables:
    - name: "{table_name}"
      description: "{description}"
```

## Instructions for Claude

When the user invokes `/berdl-discover`:

1. **Ask which database** to discover (or list available databases if unknown)
2. **Execute discovery workflow** steps 1-7, collecting:
   - Table list
   - Schema for each table
   - Row counts for key tables
   - Sample data (2-5 rows per table)
3. **Analyze relationships** by:
   - Identifying `*_id` columns
   - Matching column names across tables
   - Confirming with sample data
4. **Generate module file** using the template above
5. **Write the file** to `.claude/skills/berdl/modules/{name}.md`
6. **Offer to update** `ui/config/collections.yaml` if applicable

## Example Session

```
User: "Discover the kescience_fitnessbrowser database"

Claude:
1. Lists tables in kescience_fitnessbrowser -> finds: experiments, genes, fitness_scores, conditions
2. Gets schema for each table
3. Gets row counts: experiments(500), genes(50000), fitness_scores(2M), conditions(1000)
4. Samples data to understand structure
5. Identifies relationships: fitness_scores.gene_id -> genes.id, fitness_scores.experiment_id -> experiments.id
6. Generates .claude/skills/berdl/modules/fitness.md with:
   - Table overview
   - Schema details
   - Query patterns for fitness analysis
   - Pitfalls (e.g., "fitness_scores table is large, always filter by experiment_id")
7. Asks: "Would you like me to add this to ui/config/collections.yaml?"
```

## Error Handling

- **Authentication failure**: Check `.env` file exists and contains valid `KBASE_AUTH_TOKEN`
- **Database not found**: List accessible databases with `berdl_notebook_utils.get_databases()` and confirm spelling
- **Timeout on large tables**: Skip row counts for tables > 100M rows, note in pitfalls
- **Schema unavailable**: Mark table as "schema pending" and note in output

Avoid raw `SHOW DATABASES` or `SHOW TABLES` SQL for discovery, and avoid MCP query operations such as `mcp_query_table`, `mcp_select_table`, `mcp_count_table`, `mcp_sample_table`, or REST `/delta/tables/query` for BERDL SQL execution.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

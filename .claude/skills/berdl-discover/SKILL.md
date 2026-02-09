---
name: berdl-discover
description: Discover and document BERDL databases. Use when the user wants to explore a new database, generate documentation for a database, or create a module file for the berdl skill.
allowed-tools: Bash, Read, Write
---

# BERDL Database Discovery Skill

This skill introspects BERDL databases via API and generates documentation modules for use with the `berdl` skill.

## Discovery Workflow

When discovering a new database, follow these steps in order:

### Step 1: Authenticate

```bash
AUTH_TOKEN=$(grep "KB_AUTH_TOKEN" .env | cut -d'"' -f2)
```

### Step 2: List All Databases

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"use_hms": true, "filter_by_namespace": true}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/databases/list | python3 -m json.tool
```

### Step 3: List Tables in Target Database

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "use_hms": true}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/databases/tables/list | python3 -m json.tool
```

### Step 4: Get Schema for Each Table

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "table": "TABLE_NAME"}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/databases/tables/schema | python3 -m json.tool
```

### Step 5: Get Row Counts

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "table": "TABLE_NAME"}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/count | python3 -m json.tool
```

### Step 6: Sample Data

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "table": "TABLE_NAME", "limit": 5}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/sample | python3 -m json.tool
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

- **Authentication failure**: Check `.env` file exists and contains valid `KB_AUTH_TOKEN`
- **Database not found**: List available databases and confirm spelling
- **Timeout on large tables**: Skip row counts for tables > 100M rows, note in pitfalls
- **Schema unavailable**: Mark table as "schema pending" and note in output

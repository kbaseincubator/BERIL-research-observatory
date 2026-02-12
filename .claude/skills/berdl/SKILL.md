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

For the full inventory of 35 databases across 9 tenants, see [docs/collections.md](../../../docs/collections.md).

**Read the appropriate module** for database-specific tables, schemas, and query patterns.

## Authentication

All API requests require the token from `.env`:

```bash
AUTH_TOKEN=$(grep "KB_AUTH_TOKEN" .env | cut -d'"' -f2)
```

## API Endpoints

**Base URL**: `https://hub.berdl.kbase.us/apis/mcp/`

### List Databases
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"use_hms": true, "filter_by_namespace": true}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/databases/list
```

### List Tables
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "use_hms": true}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/databases/tables/list
```

### Get Schema
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "table": "TABLE_NAME"}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/databases/tables/schema
```

### Count Rows
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "table": "TABLE_NAME"}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/count
```

### Sample Data
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"database": "DATABASE_NAME", "table": "TABLE_NAME", "limit": 5}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/sample
```

### Execute SQL Query
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM database.table LIMIT 10", "limit": 1000, "offset": 0}' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/query
```

### Structured SELECT (SQL-injection safe)
```bash
curl -s -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "database": "DATABASE_NAME",
    "table": "TABLE_NAME",
    "columns": [{"column": "col1"}, {"column": "col2"}],
    "order_by": [{"column": "col1", "direction": "DESC"}],
    "limit": 20
  }' \
  https://hub.berdl.kbase.us/apis/mcp/delta/tables/select
```

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
2. **Read the appropriate module** for the target database
3. **Start with schema exploration** if unfamiliar with table structure
4. **Use appropriate endpoint**: `/sample` for inspection, `/count` for counts, `/query` for SQL
5. **Handle pagination** for large result sets
6. **Include ORDER BY** in queries for consistent pagination

## Error Handling

- **"cannot schedule new futures after shutdown"**: Retry the query
- **Timeout**: Use pagination with smaller limits
- **Auth errors**: Validate token exists in `.env`

## Adding New Databases

Use the `/berdl-discover` skill to introspect new databases and generate module files.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

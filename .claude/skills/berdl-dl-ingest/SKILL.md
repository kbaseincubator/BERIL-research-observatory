---
name: berdl-dl-ingest
description: Upload local dataset files to a user-provided MinIO location, generate or refine a config JSON for the data_lakehouse_ingest pipeline, and run ingest() to load Delta tables into the BERDL Lakehouse. Use when a user wants to load SQLite, TSV, CSV, Parquet, JSON, XML, or similar tabular data into a Lakehouse namespace.
allowed-tools: Bash, Read, Write, Edit, Task
---

# BERDL Local Ingest Skill

## Overview

This skill helps ingest a local dataset into the BERDL Lakehouse from a local machine.

The skill is intentionally minimal and centers on three tasks:

1. Inspect the local source data directory
2. Upload the source files to a MinIO path provided by the user
3. Build a config JSON for `data_lakehouse_ingest.ingest()` and run the ingest function

Use this skill when the user already has local source files and wants them uploaded to MinIO and then loaded into Delta tables through the ingest framework.

## What This Skill Does

- Examines a local directory and identifies the input files
- Supports source data such as:
  - `.db` / `.sqlite`
  - `.csv`
  - `.tsv`
  - `.parquet`
  - `.json`
  - `.xml`
- Uploads the files to a MinIO destination explicitly provided by the user
- Generates a config JSON that can be passed to `ingest()`
- If a ready config is not available, uses reference markdowns or examples in the skills folder to construct one
- Runs `ingest()` with the generated config

## What This Skill Does Not Do

This skill does not own complex ingest execution logic that already belongs in the ingest library itself.

Avoid re-implementing workflow features here if they are already handled by the ingest function or related utilities, such as:

- chunk planning
- custom resume logging
- notebook-driven pre-flight execution
- custom multi-phase ingest orchestration beyond file upload + config generation + `ingest()`

## Preconditions

1. `KBASE_AUTH_TOKEN` is set in the environment or `.env`, if required by the BERDL environment.
2. Required local environment and BERDL tooling are installed.
3. Any required BERDL proxy or remote access setup is available if needed by downstream commands.
4. MinIO access is available.
5. The agent can use the MinIO upload skill or related helper workflow if that functionality lives in another skills folder.

## Questions to Ask

Only ask what the user has not already provided. At most three questions:

1. **Where are the data files located locally?**
2. **What is the dataset name?**
3. **Where in MinIO should the files go?**
   - If the user has no preference, default to the personal warehouse:
     `s3://cdm-lake/users-general-warehouse/<username>/datasets/<dataset>/`
   - Only use a tenant path if the user explicitly provides a tenant name.

Do not ask about tenant, namespace, or write mode unless the user raises them.

---

## Workflow

### Step 1: Inspect the source directory

Inspect the directory and report what was found:

```bash
ls -lh <DATA_DIR>
find <DATA_DIR> -maxdepth 2 -type f | sort
```

Identify likely source files and classify them by format:

* SQLite database: `.db`, `.sqlite`
* Tabular text files: `.csv`, `.tsv`
* Other supported structured files: `.parquet`, `.json`, `.xml`
* Optional schema/reference files: `.sql`, `.md`, `.json`

### Step 2: Determine the MinIO destination

Use the path the user provided, or default to:

```text
s3://cdm-lake/users-general-warehouse/<username>/datasets/<dataset>/
```

Resolve `<username>` from `~/.mc/config.json` (`aliases.berdl-minio.accessKey`).

### Step 3: Upload files to MinIO

Upload the source files from the local directory to the user-provided MinIO path.

If another BERDL skill already handles MinIO uploads, use that skill rather than duplicating the upload logic here.

After upload, report:

* local files uploaded
* MinIO destination path
* any files skipped
* any upload failures

### Step 4: Ask the user for config inputs

Before generating or assuming a config, always ask the user:

> "Do you have a config JSON, SQL schema file, or any other reference (e.g. column descriptions, data dictionary) that should be used to generate the ingest config?"

Wait for the response. Then proceed based on what they provide:

| User provides | Action |
|---|---|
| A config JSON | Review it, update paths/dataset name as needed, use it directly |
| A SQL schema file (`.sql`) | Parse `CREATE TABLE` statements to extract column names and types; use `schema_sql` in config |
| Column descriptions / data dictionary | Use structured `schema` array with `"comment"` per column |
| Nothing | Infer column names from TSV headers; use `schema_sql` with all columns as `STRING` |

Do not auto-generate or infer column comments. Only add comments when the user has explicitly supplied them.

### Step 5: Build the config JSON

Create a config JSON suitable for passing to `ingest()`.

At minimum, the config should define:

* dataset name
* source/base paths
* defaults by format when useful
* one or more table entries
* target schema information if available
* load mode if the user specifies overwrite or append

Use the uploaded MinIO location in the config wherever the Bronze path is required.

Example shape (personal namespace — no tenant field):

```json
{
  "dataset": "<dataset>",
  "paths": {
    "bronze_base": "s3a://cdm-lake/users-general-warehouse/<username>/datasets/<dataset>"
  },
  "defaults": {
    "tsv": {
      "header": true,
      "delimiter": "\t",
      "inferSchema": false
    }
  },
  "tables": [
    {
      "name": "<table_name>",
      "enabled": true,
      "schema_sql": "<col1> STRING NOT NULL, <col2> STRING",
      "bronze_path": "${bronze_base}/<file_name>.tsv"
    }
  ]
}
```

Only add `"tenant": "<name>"` when the user explicitly provides a tenant name. Never infer or hardcode it.

### `schema` vs `schema_sql`

Use `schema_sql` (a DDL string) by default when generating configs. Only switch to the structured `schema` array when the user explicitly provides per-column comments/descriptions — the array's only advantage over `schema_sql` is storing those comments as Delta table metadata (visible in `DESCRIBE TABLE`).

Do not invent or infer column comments. If the user has not provided them, use `schema_sql`.

### Step 6: Review config with the user

Show the generated or updated config JSON to the user before running ingest.

Call out:

* dataset name
* MinIO bronze path
* tables to be loaded
* inferred or provided schemas
* overwrite vs append behavior, if relevant

Do not use overwrite behavior for an existing target unless the user explicitly agrees.

### Pre-flight: verify proxy before any upload or ingest

Run this checklist **before** any `mc cp` upload or `berdl-remote python` call. Do not skip steps.

```bash
# 1. Load token (tr -d '\r' strips Windows CRLF)
export KBASE_AUTH_TOKEN=$(grep KBASE_AUTH_TOKEN .env | cut -d= -f2 | tr -d '\r')

# 2. Login — validates token and refreshes JupyterHub cookie
berdl-remote login --hub-url https://hub.berdl.kbase.us

# 3. Spawn kernel
berdl-remote spawn --timeout 120

# 4. Verify SSH SOCKS tunnels (required for proxy; Claude cannot start these)
lsof -i :1337 -i :1338 | grep LISTEN

# 5. Start pproxy if not running
lsof -i :8123 | grep LISTEN || (
  source .venv-berdl/bin/activate &&
  python -c "
import sys, asyncio
sys.argv = ['pproxy', '-l', 'http://:8123', '-r', 'socks5://127.0.0.1:1338']
asyncio.set_event_loop(asyncio.new_event_loop())
from pproxy.server import main
main()
" &
  sleep 2
)

# 6. Confirm kernel ready
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1
berdl-remote status
```

**If login fails** (invalid token): ask the user to generate a new token at narrative.kbase.us → Account → Developer Tokens, update `.env`, then retry from step 1.

**If SSH tunnels are missing** (step 4 returns nothing): ask the user to open them — Claude cannot authenticate the SSH session:
```bash
ssh -f -N -o ServerAliveInterval=60 -D 1338 ac.<username>@login1.berkeley.kbase.us
ssh -f -N -o ServerAliveInterval=60 -D 1337 ac.<username>@login1.berkeley.kbase.us
```

### Step 7: Run ingest() via berdl-remote

Once the pre-flight passes, run ingest:

Once the kernel is confirmed ready, run ingest:

```bash
berdl-remote python "
from data_lakehouse_ingest import ingest
report = ingest('s3a://cdm-lake/users-general-warehouse/<username>/datasets/<dataset>/<dataset>.json')
print(report)
"
```

Pass the MinIO path of the uploaded config JSON directly to `ingest()`. Do not implement namespace creation, Spark session setup, or MinIO client initialization — the cluster handles all of that automatically.

If you need a Spark session on the remote kernel for ad-hoc queries (e.g. verifying row counts after ingest), use:

```python
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
spark.sql('SHOW TABLES IN <namespace>').show()
spark.stop()
```

Note: `from get_spark_session import get_spark_session` is the local notebook path and will fail on the remote kernel. Always use `berdl_notebook_utils.setup_spark_session` when running via `berdl-remote python`.

### Step 8: Report results

Report back to the user:

* uploaded file count
* MinIO upload location
* config file used or generated
* dataset / namespace loaded
* tables processed
* success or failure summary
* any next-step recommendations

## Config Generation Rules

1. Prefer an existing valid config if one is already available.
2. If no config exists, generate one from discovered files.
3. If additional guidance is needed, use reference markdowns placed in the skills folder.
4. Keep the config focused on what `ingest()` needs.
5. Do not embed unrelated notebook execution logic into the config generation flow.

## Safety Rules

1. Never print or log MinIO `secretKey` values.
2. Never overwrite an existing target dataset without explicit user confirmation.
3. Always show the config JSON before running ingest when the config was newly generated or materially changed.
4. Do not fabricate schema details when reliable schema inputs are available from files or references.
5. Do not duplicate upload logic if a dedicated MinIO upload skill already exists.

## Error Handling

* **No supported files found**: tell the user what was found and why it could not be used.
* **MinIO upload failure**: report the file(s) that failed and stop before ingest.
* **Missing config**: generate one from the source files and available references.
* **Invalid config**: explain which part is incomplete or malformed and correct it before calling `ingest()`.
* **Schema uncertainty**: fall back to a conservative config and clearly tell the user what was inferred.
* **Ingest failure**: report the error from the ingest function and identify whether the issue is upload, config, schema, or target-path related.

## References

Use these when available:

* reference markdowns in the skills folder for config construction
* MinIO upload skill in another skills folder, if upload logic is already implemented there
* BERDL ingest library documentation and examples

```

A couple of design notes behind this rewrite:
- I removed the notebook-centric flow, pre-flight confirmation cell, chunking, progress-log format, and resume logic because your current markdown is doing work that should live in the ingest implementation instead of the agent skill. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}
- I kept MinIO upload explicitly in scope, since you said the agent should still connect to MinIO and upload files, even if that is delegated to another skill. :contentReference[oaicite:4]{index=4}

If you want, I can also give you a second version that is even shorter and more “agent-instruction style,” with fewer explanations and more direct action rules.
```

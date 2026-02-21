---
name: berdl-ingest
description: Ingest a local dataset into the BERDL Lakehouse from a local (off-cluster) machine. Handles data format detection and preparation, MinIO upload, and Delta table creation via the data_lakehouse_ingest pipeline. Use when a user wants to load a new dataset — SQLite, TSV, CSV, Parquet, or other tabular formats — into a Lakehouse namespace.
allowed-tools: Bash, Read, Write, Edit, Task
---

# BERDL Local Ingest Skill

## Overview

Ingests a local dataset into the BERDL Lakehouse as a new tenant namespace, running entirely
from a local machine via the off-cluster proxy chain. Detects source format, parses schema,
exports data if needed, uploads to MinIO bronze, and writes Delta tables to the silver layer.

## Preconditions

1. `KBASE_AUTH_TOKEN` set in environment or `.env`.
2. **Ingest packages installed**: run `bash scripts/bootstrap_ingest.sh` (requires `.venv-berdl` from `bootstrap_client.sh`).
3. **Proxy running**: SSH tunnels on 1337/1338, pproxy on 8123, JupyterHub session active. See `berdl-query/references/proxy-setup.md`.
4. **`mc` configured**: `~/.mc/config.json` must have a `berdl-minio` alias. Run `bash scripts/configure_mc.sh --berdl-proxy` if not set.

## Workflow

### Step 1: Ask for source directory

Ask the user for the path to their source data directory. The directory should contain:

- A `.db` / `.sqlite` file — SQLite database (tables exported to TSV automatically), **or**
- One `.tsv` or `.csv` file per table — used directly, no conversion needed
- Optionally a `.sql` file with `CREATE TABLE` statements — used to map column types to Spark SQL types; all columns default to `STRING` without it

Inspect the directory and report what was found before continuing:

```bash
ls -lh <DATA_DIR>
```

**SQL dump only:** If the user has a `.sql` dump with INSERT statements but no `.db`, restore it first:
```bash
sqlite3 /tmp/<dataset>.db < <dump>.sql
# then move the .db into the source directory
```

### Step 2: Choose tenant

List existing tenants:

```bash
source .venv-berdl/bin/activate
python scripts/run_sql.py --berdl-proxy --query "SHOW DATABASES"
```

Present the results. Tenants are the unique prefixes before the first `_` in each database name (e.g. `kescience`, `nmdc`, `gtdb`). Ask the user to pick an existing tenant or provide a new name.

### Step 3: Choose dataset name and write mode

Ask for the dataset name. Suggest `DATA_DIR.name` (the directory's basename) as a default.
Check whether the namespace already exists:

```bash
python scripts/run_sql.py --berdl-proxy --query "SHOW DATABASES LIKE '<tenant>_<dataset>'"
```

The final namespace will be `{tenant}_{dataset}`.

**If the namespace already exists**, list its current tables and row counts, then ask the user:

- **Overwrite** — existing Delta tables are replaced. Use `MODE = "overwrite"`.
- **Append** — new rows are added to existing tables. Use `MODE = "append"`.

If the user chooses append, also confirm which tables they want to append to — it may not
be all of them. For any table the user wants to skip, set `"enabled": false` in the config
(the notebook generates all tables as enabled by default; edit the config cell or the
upload/ingest cells to exclude specific tables if needed).

### Step 4: Generate, configure, and run the ingest notebook

Copy the reference template into the source directory, named after the dataset:

```bash
cp .claude/skills/berdl-ingest/references/ingest.ipynb <DATA_DIR>/<dataset>_ingest.ipynb
```

Edit the configuration cell (cell id `b0000003`) in the copied notebook, replacing the
`{PLACEHOLDER}` values. Use the **absolute path** for `DATA_DIR` — relative paths will
not resolve correctly when `nbconvert` executes the notebook:

```python
DATA_DIR = Path("/absolute/path/to/<source directory>")
TENANT   = "<chosen tenant>"
DATASET  = "<chosen dataset>"   # or None to use DATA_DIR.name
BUCKET   = "cdm-lake"
MODE     = "overwrite"          # "overwrite" or "append" — determined in Step 3
```

Execute the notebook:

```bash
source .venv-berdl/bin/activate
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=600 \
    <DATA_DIR>/<dataset>_ingest.ipynb
```

The notebook auto-detects format, parses schema from the `.sql` file, exports SQLite to TSV
if needed (sanitizing embedded tabs/newlines), builds and uploads the ingest config and data
files to MinIO, runs `ingest()`, and prints a verification table with row counts.

### Step 5: Confirm results

Report to the user:
- Namespace created: `{tenant}_{dataset}`
- Tables ingested and row counts (from notebook output)
- Bronze path: `s3a://cdm-lake/tenant-general-warehouse/{tenant}/datasets/{dataset}/`
- Silver path: `s3a://cdm-lake/tenant-sql-warehouse/{tenant}/{tenant}_{dataset}.db`

Confirm row counts match the source. Mismatches indicate a schema or TSV parsing issue —
check the quarantine path in the ingest report.

## Scripts

- `scripts/bootstrap_client.sh`: create `.venv-berdl` and install base query packages.
- `scripts/bootstrap_ingest.sh`: install ingest-specific packages on top of `.venv-berdl`.

## References

- `references/ingest.ipynb`: notebook template — copied into `<DATA_DIR>/` and configured for each ingest job.
- `berdl-query/references/proxy-setup.md`: SSH tunnel and pproxy setup for off-cluster access.

## Error Handling

- **Ingest packages missing**: run `bash scripts/bootstrap_ingest.sh`.
- **Proxy not running**: check ports 1337, 1338, 8123 with `lsof -i :1337 -i :1338 -i :8123 | grep LISTEN`.
- **Namespace already exists**: confirm with user before re-ingesting; existing Delta tables will be overwritten.
- **Row count mismatch**: inspect the quarantine directory at `s3a://cdm-lake/tenant-sql-warehouse/{tenant}/{tenant}_{dataset}.db/quarantine/` for rejected rows.
- **Schema type errors**: recheck `.sql` parsing output and adjust column types manually in the config cell before re-running the upload and ingest cells.

## Safety Rules

1. Never print or log MinIO `secretKey` values.
2. Do not set `MODE = "overwrite"` for an existing namespace without explicit user confirmation. Default to asking overwrite vs append whenever the namespace already exists.
3. Do not commit the notebook with credentials visible in cell outputs.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

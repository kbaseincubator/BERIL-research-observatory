---
name: berdl-ingest
description: Ingest a local dataset into the BERDL Lakehouse from a local (off-cluster) machine. Handles data format detection and preparation, MinIO upload, and Delta table creation via the data_lakehouse_ingest pipeline. Use when a user wants to load a new dataset — SQLite, TSV, CSV, Parquet, or other tabular formats — into a Lakehouse namespace.
allowed-tools: Bash, Read, Write, Edit, Task
---

# BERDL Local Ingest Skill

## Overview

Ingests a local dataset into the BERDL Lakehouse as a new tenant namespace, running entirely
from a local machine via the off-cluster proxy chain. Detects source format, parses schema,
exports data if needed, then executes a **two-phase ingest**:

1. **Upload** — all source files uploaded to MinIO bronze in full before any ingest begins.
2. **Ingest** — Delta tables written to silver. Tables larger than `CHUNK_TARGET_GB` (default 20 GB)
   are streamed from the local file in line-count chunks to avoid Spark session timeouts.
   A JSONL progress log is written to MinIO after every chunk so interrupted jobs can resume.

## Preconditions

1. `KBASE_AUTH_TOKEN` set in environment or `.env`.
2. **Ingest packages installed**: run `bash scripts/bootstrap_ingest.sh` (requires `.venv-berdl` from `bootstrap_client.sh`).
3. **SSH tunnels on ports 1337 and 1338 must be running** (user must start these —
   Claude cannot run interactive SSH commands). pproxy (:8123) is started automatically.
   JupyterHub server is spawned in Step 0 before ingest begins. If tunnels are not running,
   tell the user to run these two commands in a terminal:
   ```bash
   ssh -f -N -o ServerAliveInterval=60 -D 1338 ac.<username>@login1.berkeley.kbase.us
   ssh -f -N -o ServerAliveInterval=60 -D 1337 ac.<username>@login1.berkeley.kbase.us
   ```
4. **`mc` configured**: `~/.mc/config.json` must have a `berdl-minio` alias. Run `bash scripts/configure_mc.sh --berdl-proxy` if not set.

## Workflow

### Step 0: Ensure JupyterHub server is running

Do this before anything else. The Spark Connect sidecar lives inside the JupyterHub pod —
without it there is nothing to connect to.

```bash
source .venv-berdl/bin/activate
berdl-remote status
```

If the output contains "Kernel available", the server is up — proceed to Step 1.

If not (server stopped, not spawned, or config missing), spawn it now:

```bash
berdl-remote login --hub-url https://hub.berdl.kbase.us
berdl-remote spawn --timeout 120
```

`berdl-remote login` authenticates non-interactively using `KBASE_AUTH_TOKEN` — do not ask
the user to log into JupyterHub in a browser. After spawn completes, wait 40 seconds for the
Spark Connect sidecar to start before proceeding:

```bash
sleep 40
```

Do not skip this step or defer it to the notebook. The ingest must never prompt the user for
JupyterHub credentials or ask them to visit the hub URL.

### Step 0b: Verify MinIO credentials

Before proceeding, confirm `~/.mc/config.json` exists and has a `berdl-minio` alias:

```bash
python3 -c "
import json, pathlib
cfg = json.load(open(pathlib.Path.home() / '.mc/config.json'))
alias = cfg['aliases']['berdl-minio']
print('berdl-minio URL:', alias['url'])
"
```

If this fails with `FileNotFoundError` or `KeyError`, the alias is not configured.
Tell the user to run:

```bash
bash scripts/configure_mc.sh --berdl-proxy
```

Do not proceed to Step 1 until this check passes. Connectivity (whether the credentials
are valid against the live cluster) is verified automatically when `initialize()` runs
in the notebook — any auth failure there will surface with a clear error message.

### Step 1: Ask for source directory

Ask the user for the path to their source data directory. The directory should contain:

- One `.parquet` file per table — Parquet files are read natively by Spark with embedded schema (preferred format), **or**
- A `.db` / `.sqlite` file — SQLite database (tables exported to TSV automatically), **or**
- One `.tsv` or `.csv` file per table — used directly, no conversion needed
- Optionally a `.sql` file with `CREATE TABLE` statements — used to map column types to Spark SQL types for CSV/TSV; all columns default to `STRING` without it (not needed for Parquet)

Inspect the directory and report what was found before continuing:

```bash
ls -lh <DATA_DIR>
```

**SQL dump only:** If the user has a `.sql` dump with INSERT statements but no `.db`, restore it first:
```bash
sqlite3 /tmp/<dataset>.db < <dump>.sql
# then move the .db into the source directory
```

### Step 1b: Resolve schema

**If the source is Parquet:** schema is embedded in the file metadata — skip this step
entirely and proceed to Step 2.

After inspecting the directory, check whether a `.sql` file with `CREATE TABLE` statements is present.

**If a `.sql` file exists:** use it directly — no further action needed. Skip to Step 2.

**If no `.sql` file exists:** attempt to infer column types from the data source:

- **SQLite (`.db`):** run `PRAGMA table_info(<table>)` for each table to get column names and SQLite-declared types. Map to Spark SQL types:

  | SQLite type | Spark SQL type |
  |-------------|----------------|
  | `INTEGER`   | `BIGINT`       |
  | `REAL`      | `DOUBLE`       |
  | `TEXT`      | `STRING`       |
  | `BLOB`      | `BINARY`       |
  | `NUMERIC`   | `DOUBLE`       |
  | (empty/unknown) | `STRING`   |

  ```bash
  sqlite3 <DATA_DIR>/<file>.db ".tables"
  sqlite3 <DATA_DIR>/<file>.db "PRAGMA table_info(<table>);"
  ```

- **TSV/CSV:** read the header row and sample ~5 rows. Infer types by inspecting values — integers, floats, and strings. When in doubt, use `STRING`.

  ```bash
  head -6 <DATA_DIR>/<file>.tsv
  ```

After inference, **present the proposed schema to the user** as a draft `.sql` file (one `CREATE TABLE` block per table). Ask the user to review and confirm or correct it. Example format:

```sql
CREATE TABLE my_table (
    id       BIGINT,
    name     STRING,
    score    DOUBLE,
    active   STRING
);
```

- If the inferred schema looks complete and unambiguous, propose writing it as `<DATA_DIR>/schema.sql` and proceed once the user confirms.
- If there are ambiguous columns (e.g. a column that looks like dates, mixed numeric/text, or unclear nullability), flag them specifically and ask the user what type to use before writing the file.
- If the data cannot be sampled (e.g. files are too large to inspect headers, or PRAGMA returns no type info), tell the user what's missing and ask them to provide a schema or decide to proceed with all columns as `STRING`.

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

If the user chooses append, confirm which tables they want to append to. For any table to skip,
note it now — the user can set `"enabled": false` in the per-table config or skip the relevant
ingest step in the notebook.

### Step 4: Generate, configure, and run the ingest notebook

Copy the reference template into the source directory, named after the dataset:

```bash
cp .claude/skills/berdl-ingest/references/ingest.ipynb <DATA_DIR>/<dataset>_ingest.ipynb
```

Edit the configuration cell (cell id `b0000003`) in the copied notebook, replacing the
`{PLACEHOLDER}` values. Use the **absolute path** for `DATA_DIR`:

```python
DATA_DIR        = Path("/absolute/path/to/<source directory>")
TENANT          = "<chosen tenant>"
DATASET         = "<chosen dataset>"    # or None to use DATA_DIR.name
BUCKET          = "cdm-lake"
MODE            = "overwrite"           # "overwrite" or "append" — determined in Step 3
CHUNK_TARGET_GB = 20                    # tables above this are ingested in chunks
CHUNKED_INGEST  = True                  # False = force single-batch (not recommended for large tables)
CONFIRMED       = False                 # set True after reviewing the pre-flight plan
```

**Run the notebook through the Pre-flight plan cell** (do not execute the full notebook yet):

```bash
source .venv-berdl/bin/activate
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=120 \
    --ExecutePreprocessor.raise_on_iopub_timeout=False \
    <DATA_DIR>/<dataset>_ingest.ipynb 2>&1 | tail -5
```

The Pre-flight cell will raise a `RuntimeError` (intentionally) when `CONFIRMED = False`,
halting execution after printing the plan.

**Extract the plan output and present it to the user in chat.** Do not ask the user to
open the notebook or edit it manually — the agent handles all notebook edits.

Extract all cell text output from the notebook:

```bash
python3 -c "
import json
nb = json.load(open('<DATA_DIR>/<dataset>_ingest.ipynb'))
for cell in nb.get('cells', []):
    for o in cell.get('outputs', []):
        if 'text' in o: print(''.join(o['text']))
"
```

Format the plan as a clear markdown summary in chat, showing:

- **Upload**: each table name, file size (GB), and total upload size
- **Ingest**: for each table — single ingest or number of chunks × lines per chunk

**Do not run the full notebook until the user explicitly confirms.** Ask the user:

> "Here is the ingest plan. Would you like to (a) request any changes, or (b) confirm
> and proceed?"

**(a) Suggest changes** — Make the requested edits to cell
`b0000003-0000-0000-0000-000000000003` in the notebook (e.g. lower `CHUNK_TARGET_GB`,
change `MODE`, disable a table), re-run the pre-flight `nbconvert` command, extract the
updated output, and re-present the revised plan. Repeat until the user is satisfied.

**(b) Confirm and proceed** — Edit cell `b0000003-0000-0000-0000-000000000003` to set
`CONFIRMED = True`, then execute the full notebook:

```bash
source .venv-berdl/bin/activate
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=-1 \
    <DATA_DIR>/<dataset>_ingest.ipynb
```

**What the notebook does:**

1. Counts lines in each source file and calculates per-table chunk sizes
2. Prints the pre-flight plan and blocks until `CONFIRMED = True`
3. Uploads all files to MinIO bronze (full files, no chunking at this stage)
4. Loads any existing progress log from MinIO (enables resume on restart)
5. For each table:
   - **≤ CHUNK_TARGET_GB**: ingests via `ingest()` in one shot
   - **> CHUNK_TARGET_GB**: streams the local file with `pandas.read_csv(chunksize=N)`,
     writes each chunk to Delta via `spark.createDataFrame()`, logs progress to MinIO after each chunk
6. Verifies final row counts against expected line counts

**Resuming an interrupted ingest:** If the notebook fails mid-ingest (e.g. Spark session timeout),
simply re-run the ingest cell. The progress log is loaded at startup — already-completed chunks
and tables are skipped automatically.

**Disabling chunked ingest:** Set `CHUNKED_INGEST = False` to force all tables through the
single-batch `ingest()` pipeline regardless of size. Only use this for datasets where all
tables are small enough to ingest without timeout risk.

### Step 5: Confirm results

Report to the user:
- Namespace created: `{tenant}_{dataset}`
- Tables ingested and row counts (from notebook verification cell output)
- Bronze path: `s3a://cdm-lake/tenant-general-warehouse/{tenant}/datasets/{dataset}/`
- Silver path: `s3a://cdm-lake/tenant-sql-warehouse/{tenant}/{tenant}_{dataset}.db`
- Progress log: `s3a://cdm-lake/tenant-general-warehouse/{tenant}/datasets/{dataset}/_ingest_progress.jsonl`

Confirm row counts match expected line counts. If there is a mismatch, the progress log
records `start_line`, `end_line`, and `rows_written` per chunk — the user can query the last
ingested row in Delta and compare against the logged line range to locate the gap.

## Scripts

- `scripts/bootstrap_client.sh`: create `.venv-berdl` and install base query packages.
- `scripts/bootstrap_ingest.sh`: install ingest-specific packages on top of `.venv-berdl`.

## References

- `references/ingest.ipynb`: notebook template — copied into `<DATA_DIR>/` and configured for each ingest job.
- `berdl-query/references/proxy-setup.md`: SSH tunnel and pproxy setup for off-cluster access.

## Progress Log Format

The progress log is a JSONL file at `s3a://cdm-lake/{BRONZE_PREFIX}/_ingest_progress.jsonl`.
Each line is one JSON object. There are two entry types:

**Chunk entry** (written after each chunk or single-table ingest):
```json
{"table": "my_table", "chunk": 2, "start_line": 4000001, "end_line": 6000000,
 "rows_written": 2000000, "rows_cumulative": 6000000,
 "status": "ingested", "timestamp": "2026-02-23T14:32:00Z"}
```

**Completion entry** (written when all chunks for a table are done):
```json
{"table": "my_table", "status": "complete",
 "total_rows": 6000000, "total_chunks": 3, "timestamp": "2026-02-23T15:10:00Z"}
```

`start_line` and `end_line` are 1-indexed data line numbers (header excluded). If a row
count mismatch is found, use these to cross-check against the Delta table's last row.

## Error Handling

- **Ingest packages missing**: run `bash scripts/bootstrap_ingest.sh`.
- **MinIO config missing or alias not found** (`FileNotFoundError` or `KeyError` on
  `berdl-minio`): run `bash scripts/configure_mc.sh --berdl-proxy`, then re-run Step 0b.
- **MinIO connection failed** (credentials invalid or expired): re-run
  `bash scripts/configure_mc.sh --berdl-proxy` to refresh the alias, confirm pproxy is
  running on :8123, then retry. Never print `accessKey` or `secretKey` when diagnosing.
- **SSH tunnels down (ports 1337/1338)**: tell the user to run the missing tunnel command(s)
  in a terminal (replace `<username>` with their LBNL username), then re-run the
  initialization cell:
  ```bash
  ssh -f -N -o ServerAliveInterval=60 -D 1338 ac.<username>@login1.berkeley.kbase.us
  ssh -f -N -o ServerAliveInterval=60 -D 1337 ac.<username>@login1.berkeley.kbase.us
  ```
- **pproxy not running (:8123)**: started automatically by the notebook.
- **JupyterHub server not running**: this should have been caught in Step 0. Re-run Step 0
  (`berdl-remote login` then `berdl-remote spawn --timeout 120`, then `sleep 40`) before
  retrying. Do not ask the user to log into JupyterHub manually.
- **Spark session timeout mid-table**: a health check runs once per table before ingest
  begins. If Spark dies mid-table during a chunked ingest, the chunk write raises and
  the ingest cell fails. Re-run the cell to resume automatically from the last completed
  chunk — no data is lost because the progress log records every completed chunk.
- **Spark session timeout limit (1 hour)**: cluster admin task — request BERDL
  administrators to increase Spark Connect session timeout to 10 hours.
- **Namespace already exists**: confirm with user before re-ingesting; `MODE = "overwrite"` on
  the first chunk will replace the existing Delta table.
- **Row count mismatch**: inspect the progress log for `start_line`/`end_line` of the last
  chunk, and check the quarantine path at `{SILVER_BASE}/quarantine/` for rejected rows.
- **Schema type errors**: recheck `.sql` parsing output in the schema cell and adjust column
  types in the config cell before re-running the ingest cell.
- **`createDataFrame` size errors over Spark Connect**: if a chunk is too large for the gRPC
  channel, reduce `CHUNK_TARGET_GB` (e.g. to 10 or 5) and re-run. The progress log will
  resume from the last completed chunk.

## Safety Rules

1. Never print, log, or echo any MinIO credential fields (`accessKey`, `secretKey`).
   When inspecting `~/.mc/config.json` for diagnostics, only print the `url` field.
2. Never print, log, or write `KBASE_AUTH_TOKEN` in any notebook, script, or file. Always
   access it exclusively through `os.getenv("KBASE_AUTH_TOKEN")` or the `.env` file loader —
   never hardcode or echo the value.
3. Do not set `MODE = "overwrite"` for an existing namespace without explicit user confirmation.
4. Do not set `CONFIRMED = True` on behalf of the user — always present the pre-flight plan
   and wait for explicit confirmation before proceeding.
5. Do not commit the notebook with credentials visible in cell outputs.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

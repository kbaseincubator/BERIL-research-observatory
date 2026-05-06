---
name: berdl-ingest-remote
description: Ingest a local dataset into the BERDL Lakehouse from a local (off-cluster) machine via SSH tunnels and pproxy. Handles data format detection and preparation, MinIO upload, and Delta table creation via the data_lakehouse_ingest pipeline. Use when a user wants to load a new dataset — SQLite, TSV, CSV, Parquet, or other tabular formats — into a Lakehouse namespace from their local machine (not from within JupyterHub). For in-cluster ingestion from within JupyterHub, use berdl-ingest instead.
allowed-tools: Bash, Read, Write, Edit, Task
---

# BERDL Remote (Off-Cluster) Ingest Skill

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

### Step 0a: Environment Check

```bash
python scripts/berdl_env.py --check
```

This skill is **off-cluster only**. If `--check` reports on-cluster, switch to `/berdl-ingest`. If off-cluster and not ready, follow printed next steps; the existing Step 0 (JH server spawn) cannot succeed without tunnels and pproxy in place.

### Step 0c: Ensure JupyterHub server is running

Do this before anything else. The Spark Connect sidecar lives inside the JupyterHub pod —
without it there is nothing to connect to.

**First, load `.env` into the shell environment.** `berdl-remote` reads `KBASE_AUTH_TOKEN`
from the shell environment only — unlike the Python scripts in this repo, it does not parse
`.env` itself. Always source `.env` before calling any `berdl-remote` command:

```bash
set -a && source .env 2>/dev/null; set +a
```

Then verify the token is present:

```bash
[ -n "$KBASE_AUTH_TOKEN" ] && echo "KBASE_AUTH_TOKEN: set" || echo "KBASE_AUTH_TOKEN: MISSING"
```

If the token is missing after sourcing `.env`, do not proceed — see
**Error Handling: KBASE_AUTH_TOKEN missing** for the correct safe response.

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

List accessible databases with the access-aware helper:

```python
import berdl_notebook_utils

databases = berdl_notebook_utils.get_databases(return_json=False)  # → list[str]
```

Present the results. Tenants are the unique prefixes before the first `_` in each database name (e.g. `kescience`, `nmdc`, `gtdb`). Ask the user to choose one of the following options:

1. **An existing tenant** — pick from the list above
2. **A new tenant name** — provide a new name (a new tenant namespace will be created)
3. **My user-tenant space (private)** — data is stored in the authenticated user's personal
   space, not under a shared tenant. **This is private to the user's account.** When this
   option is chosen, set `USER_TENANT = True` in the notebook config (Step 4) and **do not**
   set `TENANT` to the user's name — the `tenant` and `is_tenant` fields are omitted from
   the config JSON entirely, so the pipeline routes correctly to the user's personal space
   instead of creating a new tenant with the user's name.

### Step 3: Choose dataset name and write mode

Ask for the dataset name. Suggest `DATA_DIR.name` (the directory's basename) as a default.
Check whether the namespace already exists:

```python
namespace = "<tenant>_<dataset>"
namespace_exists = namespace in berdl_notebook_utils.get_databases(return_json=False)
```

The final namespace will be `{tenant}_{dataset}`.

**If the namespace already exists**, list its current tables and row counts, then ask the user:

- **Overwrite** — existing Delta tables are replaced. Use `MODE = "overwrite"`.
- **Append** — new rows are added to existing tables. Use `MODE = "append"`.

If the user chooses append, confirm which tables they want to append to. For any table to skip,
note it now — the user can set `"enabled": false` in the per-table config or skip the relevant
ingest step in the notebook.

### Step 3b: Collect dataset metadata

One YAML metadata file is created per table, stored locally at `<DATA_DIR>/metadata/{table}.yaml`
and uploaded to MinIO at `{BRONZE_PREFIX}/metadata/{table}.yaml`. The file is uploaded twice:
before ingest (`status: in_progress`) and after (`status: completed` or `failed`).

**Infer `ingested_by`:**

```bash
git config user.name
```

If this returns a name, use it as the default. If git is unavailable or returns empty, prompt
the user for their name.

**Check for existing metadata files (re-ingest warning):**

```bash
https_proxy=http://127.0.0.1:8123 mc ls "berdl-minio/cdm-lake/{BRONZE_PREFIX}/metadata/" 2>/dev/null | head -5
```

If any files are listed, warn the user:
> "Metadata files already exist for this dataset and will be overwritten."

**Ask about source:**

> "Are all tables from the same source (e.g., the same URL or download location), or do some
> tables come from different sources?"

**(a) Same source for all tables — ask once:**

> "What is the source URL or download location for this dataset?"

Use that value for all table metadata files.

**(b) Mixed sources — generate a temp fill-in file:**

Create `<DATA_DIR>/metadata/_source_input.yaml`. List every table with blank fields, ordered
by priority so the user fills in the most important ones first:

```yaml
# Ingest metadata input for {NAMESPACE}
# 'shared' fields apply to all tables. Per-table fields override the shared value.
# Fields left blank will not be set in the metadata.
# Save and close when done, then let the agent know.

shared:
  ingested_by: "{inferred name or blank}"
  ingest_contributors: []

tables:
  {table1}:
    source: ""
    description: ""
    ingested_by: ""      # leave blank to use shared value above
    ingest_contributors: []
    version: ""
  {table2}:
    source: ""
    description: ""
    ingested_by: ""
    ingest_contributors: []
    version: ""
  # ... one entry per table
```

Tell the user the file path and ask them to fill it in and confirm when done. After
confirmation, read the file, extract values, and **delete the temp file**:

```bash
rm "<DATA_DIR>/metadata/_source_input.yaml"
```

**Generate local metadata files:**

Create `<DATA_DIR>/metadata/` if it does not exist. Run the following script, substituting
actual values for all `<PLACEHOLDER>` entries:

```bash
source .venv-berdl/bin/activate
python3 - <<'PYEOF'
import uuid, yaml
from datetime import date, datetime, timezone
from pathlib import Path

DATA_DIR      = Path("<DATA_DIR>")
TENANT        = "<TENANT>"
DATASET       = "<DATASET>"
BUCKET        = "cdm-lake"
BRONZE_PREFIX = f"tenant-general-warehouse/{TENANT}/datasets/{DATASET}"

tables        = [<list of table names as Python strings>]
ingested_by   = "<inferred or provided name>"
source_shared = "<source if same for all, else None>"
source_map    = {<table: source pairs from temp file, else empty dict {}>}

sql_files  = sorted(DATA_DIR.glob("*.sql"))
sql_bronze = (f"s3a://{BUCKET}/{BRONZE_PREFIX}/config/{sql_files[0].name}"
              if sql_files else None)

now   = datetime.now(timezone.utc).isoformat()
today = date.today().isoformat()

metadata_dir = DATA_DIR / "metadata"
metadata_dir.mkdir(exist_ok=True)

for table in tables:
    source = source_map.get(table) or source_shared or ""
    meta = {
        "schema_version":      "0.2.0",
        "identifier":          str(uuid.uuid4()),
        "tenant":              TENANT,
        "dataset":             DATASET,
        "namespace":           f"{TENANT}_{DATASET}",
        "table":               table,
        "title":               table,
        "source":              source,
        "date_accessed":       today,
        "status":              "in_progress",
        "ingested_by":         ingested_by,
        "ingest_started_at":   now,
        "data_schema_location": sql_bronze,
        "version":             None,
        "description":         None,
        "ingest_contributors": [],
        "ingest_completed_at": None,
    }
    out = metadata_dir / f"{table}.yaml"
    with open(out, "w") as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"  wrote {out.name}")
PYEOF
```

**Present required non-auto fields for user confirmation — REQUIRED STOPPING POINT:**

Display the values that need confirmation. For same-source ingests this is one set of values;
for mixed-source, show a compact per-table table:

```
Required fields — please confirm or correct:
  title         : {table}  (one per table — defaults to table name)
  source        : {source value(s)}
  ingested_by   : {name}
  date_accessed : {today}
```

Ask: **(a) Confirm these values and proceed, or (b) correct specific values.**

If (b): ask which field and table to correct, update the relevant local `.yaml` file, and
re-present the summary. Repeat until the user explicitly confirms. Do not proceed until
confirmation is received.

**Optional fields step — REQUIRED STOPPING POINT:**

After confirmation, strongly suggest completing the optional fields:

> "Consider filling in: `description`, `version`, `ingest_contributors`. These improve
> discoverability and traceability. How would you like to proceed?
> (a) Let me help you fill them in now
> (b) Edit the files manually — they are at `<DATA_DIR>/metadata/`
> (c) Skip for now (you can update them later)"

Wait for the user's explicit choice before continuing.

- **(a)** Prompt for each optional field. For `description` and `version`: ask once if same
  for all tables, otherwise per-table. For `ingest_contributors`: always shared. Update
  local `.yaml` files after each answer.
- **(b)** List all file paths clearly and wait for the user to confirm they are done editing.
- **(c)** Warn: "Metadata will be uploaded with optional fields blank. You should return to
  fill these in before the dataset is used in analyses."

**Upload to MinIO (first push — in_progress):**

```bash
source .venv-berdl/bin/activate
# NOTE: mc interprets relative paths as MinIO URLs — always use an absolute path here.
https_proxy=http://127.0.0.1:8123 mc cp --recursive "$(realpath <DATA_DIR>)/metadata/" \
    "berdl-minio/cdm-lake/{BRONZE_PREFIX}/metadata/"
```

Confirm to the user:
> "Metadata uploaded (first push — **in_progress**) for {N} tables →
> `s3a://cdm-lake/{BRONZE_PREFIX}/metadata/`"

### Step 4: Generate, configure, and run the ingest notebook

Copy the reference template into the source directory, named after the dataset:

```bash
cp .claude/skills/berdl-ingest/references/ingest.ipynb <DATA_DIR>/<dataset>_ingest.ipynb
```

Edit the configuration cell (cell id `b0000003`) in the copied notebook, replacing the
`{PLACEHOLDER}` values. Use the **absolute path** for `DATA_DIR`:

```python
DATA_DIR        = Path("/absolute/path/to/<source directory>")
TENANT          = "<chosen tenant>"     # ignored when USER_TENANT=True
DATASET         = "<chosen dataset>"    # or None to use DATA_DIR.name
BUCKET          = "cdm-lake"
MODE            = "overwrite"           # "overwrite" or "append" — determined in Step 3
CHUNK_TARGET_GB = 20                    # tables above this are ingested in chunks
CHUNKED_INGEST  = True                  # False = force single-batch (not recommended for large tables)
USER_TENANT     = False                 # True = user-tenant space; omits 'tenant'/'is_tenant' from config JSON
```

If the user chose **user-tenant space** in Step 2: set `USER_TENANT = True`. Do **not** set
`TENANT` to the user's name — leave it as a placeholder or empty string. The `tenant` and
`is_tenant` keys will be absent from the config JSON, routing the ingest to the user's
personal space.

**Run the pre-flight script** to compute and display the ingest plan. This requires no
Spark or JupyterHub — only tunnels and MinIO:

```bash
source .venv-berdl/bin/activate
python scripts/ingest_preflight.py \
    --data-dir "/absolute/path/to/<source directory>" \
    --tenant "<chosen tenant>" \
    --dataset "<chosen dataset>" \
    --mode overwrite \
    --chunk-target-gb 20
    # add --user-tenant if the user chose user-tenant space in Step 2
```

When `--user-tenant` is passed, the script resolves the KBase username from
`~/.mc/config.json` (the MinIO access key equals the KBase username) and displays the
exact destination namespace: `u_<username>__<dataset>`. This line appears at the top of
the plan output — include it verbatim in the chat summary so the user sees precisely where
their data will land.

**Present the plan output to the user in chat**, formatted as a clear markdown summary:

- **Destination**: namespace name — `u_<username>__<dataset>` for user-tenant space,
  `<tenant>_<dataset>` for shared tenants. Always show this prominently.
- **Upload**: each table name, file size (GB), and total upload size
- **Ingest**: for each table — single ingest or number of chunks × lines per chunk

**Do not run the full notebook until the user explicitly confirms.** Ask the user:

> "Here is the ingest plan. Would you like to (a) request any changes, or (b) confirm
> and proceed?"

**(a) Suggest changes** — Make the requested edits to cell
`b0000003-0000-0000-0000-000000000003` in the notebook (e.g. lower `CHUNK_TARGET_GB`,
change `MODE`), re-run the pre-flight script with the updated values, and re-present the
revised plan. Repeat until the user is satisfied.

**(b) Confirm and proceed** — Before launching the notebook, warn the user about the
silent startup period. The notebook runs as a background process and produces no visible
output until each cell completes, so the user will see nothing in chat during this time.
Send this message (base the estimate on total source size at ~1 min per 30 GB, minimum
1 minute, and frame it as a rough expectation not a precise figure):

> "Starting the ingest notebook now — running it in the background. You might expect
> roughly **{N} minutes** of silence while the notebook initialises Spark and counts
> lines in the source file(s) before any upload begins. I'll let you know as soon as
> the first chunk starts ingesting so you know setup is done — after that you can ask
> me for status updates at any time."

Then execute the full notebook in the background:

```bash
source .venv-berdl/bin/activate
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=-1 \
    <DATA_DIR>/<dataset>_ingest.ipynb
```

After launching, poll the MinIO progress log every 5 minutes until the first entry
appears, then notify the user:

```bash
https_proxy=http://127.0.0.1:8123 mc cat \
  "berdl-minio/cdm-lake/{BRONZE_PREFIX}/_ingest_progress.jsonl" 2>/dev/null | head -1
```

When the first entry appears, send the user a message such as:

> "Setup complete — chunk 1 is now ingesting. You can ask me for status updates at
> any time."

Do not continue polling after the first entry is confirmed — the user will ask for
updates as needed.

**What the notebook does:**

1. Counts lines in each source file and calculates per-table chunk sizes
2. Uploads non-chunked files to MinIO bronze. Chunked tables are skipped here —
   their chunk files are uploaded one-by-one during ingest (step 4b below)
3. Loads any existing progress log from MinIO (enables resume on restart)
4. For each table:
   - **≤ CHUNK_TARGET_GB** (non-chunked): builds a merged config JSON, uploads it to
     MinIO, and calls `ingest()` once for all non-chunked tables
   - **> CHUNK_TARGET_GB** (chunked): splits the local file into ~`CHUNK_TARGET_GB`
     pieces at newline boundaries (streaming, ~128 MB memory), then for each chunk:
     uploads the chunk file to MinIO, verifies the upload size, calls `ingest()` on
     that chunk with `append` mode (overwrite for chunk 0), deletes the chunk file
     from MinIO after success, and logs an `uploaded` + `ingested` entry per chunk
5. Verifies final row counts against expected line counts

**Resuming an interrupted ingest:** If the notebook fails mid-ingest (e.g. Spark session
timeout), simply re-run the ingest cell. The progress log tracks upload and ingest status
per chunk — already-completed chunks are skipped, and uploaded-but-not-ingested chunks are
verified in MinIO before ingest resumes. No data is lost.

**Disabling chunked ingest:** Set `CHUNKED_INGEST = False` to force all tables through the
single-batch `ingest()` pipeline regardless of size. Only use this for datasets where all
tables are small enough to ingest without timeout risk.

### Step 5: Confirm results

Report to the user:
- Namespace created: `{tenant}_{dataset}` for shared tenants, or `u_{username}__{dataset}`
  for user-tenant space — use the value resolved during Step 4 (printed by the config cell
  and the pre-flight script). Always show the full namespace name explicitly.
- Tables ingested and row counts (from notebook verification cell output)

For **shared tenant** ingests:
- Bronze: `s3a://cdm-lake/tenant-general-warehouse/{tenant}/datasets/{dataset}/`
- Silver: `s3a://cdm-lake/tenant-sql-warehouse/{tenant}/{tenant}_{dataset}.db`
- Progress log: `s3a://cdm-lake/tenant-general-warehouse/{tenant}/datasets/{dataset}/_ingest_progress.jsonl`

For **user-tenant space** ingests (use `username` and `u_{username}__{dataset}` from Step 4):
- Bronze: `s3a://cdm-lake/users-general-warehouse/{username}/data/{dataset}/`
- Silver: `s3a://cdm-lake/users-sql-warehouse/{username}/u_{username}__{dataset}.db`
- Progress log: `s3a://cdm-lake/users-general-warehouse/{username}/data/{dataset}/_ingest_progress.jsonl`

Confirm row counts match expected line counts. If there is a mismatch, the progress log
records `start_line`, `end_line`, and `rows_written` per chunk — the user can query the last
ingested row in Delta and compare against the logged line range to locate the gap.

The notebook's final cell performs the **metadata second push**: it updates each table's
local `.yaml` with `ingest_completed_at` and `status: completed` (or `failed`), then
batch-uploads all files to MinIO. Look for the confirmation line in the notebook output:

```
Metadata second push complete → s3a://cdm-lake/{BRONZE_PREFIX}/metadata/
```

If any table shows `status: failed` in the output, that table's metadata was updated
accordingly — re-run the ingest cell for that table, then re-run the metadata cell to
push a corrected `completed` record.

## Scripts

- `scripts/bootstrap_client.sh`: create `.venv-berdl` and install base query packages.
- `scripts/bootstrap_ingest.sh`: install ingest-specific packages on top of `.venv-berdl`.
- `scripts/ingest_preflight.py`: print the pre-flight ingest plan (no Spark required). Run before executing the ingest notebook to review upload sizes and chunk counts.

## References

- `references/ingest.ipynb`: notebook template — copied into `<DATA_DIR>/` and configured for each ingest job.
- `berdl-query/references/proxy-setup.md`: SSH tunnel and pproxy setup for off-cluster access.

## Progress Log Format

The progress log is a JSONL file at `s3a://cdm-lake/{BRONZE_PREFIX}/_ingest_progress.jsonl`.
Each line is one JSON object. There are three entry types:

**Upload entry** (written immediately after a chunk file lands in MinIO — chunked tables only):
```json
{"table": "my_table", "chunk": 2, "status": "uploaded",
 "minio_path": "s3a://cdm-lake/.../my_table_chunk_002.tsv",
 "size_bytes": 21474836480, "timestamp": "2026-02-23T14:30:00Z"}
```

**Ingested entry** (written after `ingest()` confirms success for a chunk or single-batch table):
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

On restart, resume logic uses all three entry types: an `uploaded`-only chunk triggers a
MinIO size verification before re-ingesting; an `ingested` chunk is skipped entirely.

## Error Handling

- **KBASE_AUTH_TOKEN missing** (not in environment and not found in `.env`): Send the user
  this exact message — do not improvise wording, and **never ask them to paste or type their
  token into this chat**:

  > "Your `KBASE_AUTH_TOKEN` isn't set. You have two options — you can do one or both:
  >
  > **Option A — export it for this terminal session:**
  > In a **separate terminal window** (not here), run:
  > ```
  > export KBASE_AUTH_TOKEN=<your_token>
  > ```
  > Then type `! export KBASE_AUTH_TOKEN=<your_token>` in this chat to make it available
  > to the agent — replacing `<your_token>` with your actual token.
  >
  > **Option B (also recommended) — add it to your `.env` file for persistence:**
  > Open `.env` in a text editor and add or update the line:
  > ```
  > KBASE_AUTH_TOKEN=<your_token>
  > ```
  > Save the file, then let me know and I'll continue.
  >
  > Doing both means you won't need to set it again next session.
  >
  > **Security reminder:** Never paste your token directly into this chat as plain text.
  > Tokens pasted here may be visible in logs or chat history. Always use a terminal or
  > your `.env` file."

  After the user confirms they have set the token, re-run the `.env` source and token check
  before continuing.

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
- **Spark session timeout mid-chunk**: a health check runs before each chunk ingest. If
  Spark dies mid-chunk, the `ingest()` call raises and the ingest cell fails. Re-run the
  cell — the progress log will skip already-ingested chunks and re-verify uploaded ones
  before resuming. No data is lost.
- **Spark session timeout limit (1 hour)**: cluster admin task — request BERDL
  administrators to increase Spark Connect session timeout to 10 hours.
- **Chunk upload verification failure**: if a chunk file is present in the progress log as
  `uploaded` but MinIO shows a size mismatch or the file is missing, `_ingest_chunked()`
  automatically re-uploads the chunk from the local temp file before ingesting.
- **Namespace already exists**: confirm with user before re-ingesting; `MODE = "overwrite"`
  on chunk 0 will replace the existing Delta table; subsequent chunks use `append`.
- **Row count mismatch**: inspect the progress log for `start_line`/`end_line` of the last
  ingested chunk and check the quarantine path at `{SILVER_BASE}/quarantine/` for rejected rows.
- **Schema type errors**: recheck `.sql` parsing output in the schema cell and adjust column
  types in the config cell before re-running the ingest cell.

## Safety Rules

1. Never print, log, or echo any MinIO credential fields (`accessKey`, `secretKey`).
   When inspecting `~/.mc/config.json` for diagnostics, only print the `url` field.
2. Never print, log, or write `KBASE_AUTH_TOKEN` in any notebook, script, or file. Always
   access it exclusively through `os.getenv("KBASE_AUTH_TOKEN")` or the `.env` file loader —
   never hardcode or echo the value.
3. Do not set `MODE = "overwrite"` for an existing namespace without explicit user confirmation.
4. Always present the pre-flight plan output from `ingest_preflight.py` and wait for
   explicit user confirmation before executing the ingest notebook.
5. Do not commit the notebook with credentials visible in cell outputs.
6. **If a token appears in the conversation context** (i.e. a raw credential string was pasted
   into chat by the user): immediately stop all work and send this message — do not proceed
   with any task until the user has acted:

   > "**Security alert:** It looks like a credential was pasted directly into this chat.
   > Chat messages may be stored in logs or history. Please take these steps immediately:
   >
   > 1. **Revoke this token now** — generate a new one from the KBase token management page.
   > 2. **Do not use the pasted token** — treat it as compromised.
   > 3. Add your new token to `.env` or export it in a separate terminal as described above.
   >
   > Let me know once you have a new token and I'll continue."

   Do not repeat, quote, or reference the token value in any response.
7. **Never auto-resume a prior ingest.** When the skill is invoked, do not automatically
   check on, investigate, or resume any previously in-progress ingest found in memory or
   context. At the start of Step 1, if memory contains an in-progress ingest, mention it
   briefly as one option: "I see a previous ingest was in progress — would you like to
   resume it, or start a new one?" Then wait for explicit user choice before taking any
   action related to the prior ingest.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.

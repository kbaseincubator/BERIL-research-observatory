---
name: berdl-ingest
description: Ingest a dataset into the BERDL Lakehouse from within JupyterHub (in-cluster). Data may live on the JH filesystem or a global shared filesystem. Handles schema detection, MinIO upload via Python client, and Delta table creation via the data_lakehouse_ingest pipeline. Use when a user is already working inside JupyterHub and wants to load a new dataset — SQLite, TSV, CSV, Parquet, or other tabular formats — into a Lakehouse namespace. For off-cluster ingestion from a local machine, use berdl-ingest-remote instead.
allowed-tools: Bash, Read, Write, Edit, Task
---

# BERDL In-Cluster Ingest Skill

## Overview

Ingests a dataset into the BERDL Lakehouse from within JupyterHub. Because Spark and
MinIO are directly accessible inside the cluster, no SSH tunnels, pproxy, or
`berdl-remote` are needed. The workflow is:

1. Verify the JH environment (Spark + MinIO connect directly).
2. Detect source format and parse schema.
3. Collect dataset metadata.
4. Upload source files to MinIO bronze via `minio_client.fput_object()`.
5. Call `ingest()` per table — Spark reads from bronze and writes Delta to silver.
6. Verify row counts.
7. Report the bronze and silver paths to the user.

## Preconditions

1. `KBASE_AUTH_TOKEN` set in environment or `.env`. Source it first:
   ```bash
   set -a && source .env 2>/dev/null; set +a
   [ -n "$KBASE_AUTH_TOKEN" ] && echo "token: set" || echo "token: MISSING"
   ```
2. `data_lakehouse_ingest` installed in the active Python environment:
   ```bash
   python3 -c "import data_lakehouse_ingest; print('ok')"
   ```
   If this fails, the package is not installed. Ask the user to install it via the
   appropriate environment setup for their JH server.
3. Source data is accessible on the JH filesystem — either in the user's home directory
   or on a globally mounted share (e.g. `/global/cfs/`, `/clusterfs/`).

## Workflow

### Step 0: Verify environment

`get_spark_session()` and `get_minio_client()` come from `scripts/ingest_lib.py` in
the BERIL repo (not from `data_lakehouse_ingest` directly). The notebook bootstraps
`ingest_lib` by walking up from the notebook's location to find `scripts/` and adding
it to `sys.path` — the same approach as the remote skill.

`ingest()` is imported directly from `data_lakehouse_ingest` (its only public export).

Verify the environment is ready:

```python
import sys
from pathlib import Path

_found = False
for _p in [Path.cwd()] + list(Path.cwd().parents):
    if (_p / "scripts" / "ingest_lib.py").exists():
        sys.path.insert(0, str(_p / "scripts"))
        _found = True
        break
if not _found:
    raise RuntimeError("Could not find scripts/ingest_lib.py — run from within the BERIL repo.")

from ingest_lib import get_spark_session, get_minio_client
from data_lakehouse_ingest import ingest

spark        = get_spark_session()
minio_client = get_minio_client()
print("Spark and MinIO ready.")
```

If either `get_spark_session()` or `get_minio_client()` raises, the JH environment is
misconfigured — this is not a tunnel issue. Report the error verbatim and stop.

### Step 1: Ask for source directory

Ask the user for the path to their source data directory on the JH filesystem.
The directory should contain:

- One `.parquet` file per table — schema is embedded (preferred), **or**
- A `.db` / `.sqlite` file — tables are exported to TSV automatically, **or**
- One `.tsv` or `.csv` file per table — used directly
- Optionally a `.sql` file with `CREATE TABLE` statements — used to map column types

Inspect and report what was found:

```bash
ls -lh <DATA_DIR>
```

**SQL dump only:** If the user has a `.sql` dump with INSERT statements but no `.db`,
restore it first:
```bash
sqlite3 /tmp/<dataset>.db < <dump>.sql
```

### Step 1b: Resolve schema

**Parquet:** schema embedded — skip this step.

**If a `.sql` file exists:** use it directly — skip to Step 2.

**If no `.sql` file:** infer types from the source:

- **SQLite:** run `PRAGMA table_info(<table>)` for each table.

  | SQLite type     | Spark SQL type |
  |-----------------|----------------|
  | `INTEGER`       | `BIGINT`       |
  | `REAL`          | `DOUBLE`       |
  | `TEXT`          | `STRING`       |
  | `BLOB`          | `BINARY`       |
  | `NUMERIC`       | `DOUBLE`       |
  | (empty/unknown) | `STRING`       |

  ```bash
  sqlite3 <DATA_DIR>/<file>.db ".tables"
  sqlite3 <DATA_DIR>/<file>.db "PRAGMA table_info(<table>);"
  ```

- **TSV/CSV:** sample header + 5 rows:
  ```bash
  head -6 <DATA_DIR>/<file>.tsv
  ```

Present the proposed schema as a draft `.sql` file and ask the user to confirm or
correct it before writing `<DATA_DIR>/schema.sql`. Flag any ambiguous columns.

### Step 2: Choose tenant

```python
import berdl_notebook_utils
databases = berdl_notebook_utils.get_databases()
```

Present results. Tenants are the unique prefixes before the first `_`. Ask the user:

1. **Existing tenant** — choose from the list
2. **New tenant name** — a new namespace will be created
3. **User-tenant space (private)** — set `USER_TENANT = True` in the notebook config;
   namespace becomes `u_<JUPYTERHUB_USER>__<dataset>`.

### Step 3: Choose dataset name and write mode

Suggest `DATA_DIR.name` as the dataset name default. Check whether the namespace
already exists:

```python
namespace        = f"{tenant}_{dataset}"
namespace_exists = namespace in berdl_notebook_utils.get_databases()
```

If it exists, list tables and row counts, then ask:
- **Overwrite** — `MODE = "overwrite"` (replaces existing Delta tables)
- **Append** — `MODE = "append"` (adds rows to existing tables)

### Step 3b: Collect dataset metadata

One YAML metadata file per table, stored at `<DATA_DIR>/metadata/{table}.yaml` and
uploaded to `s3a://cdm-lake/{BRONZE_PREFIX}/metadata/{table}.yaml` twice: before
ingest (`status: in_progress`) and after (`status: completed` or `failed`).

**Infer `ingested_by`:**

```bash
git config user.name
```

**Check for existing metadata (re-ingest warning):** Use the Python MinIO client —
there is no `mc` CLI in the JH terminal environment:

```python
objects = list(minio_client.list_objects(
    "cdm-lake", prefix=f"{BRONZE_PREFIX}/metadata/", recursive=True))
if objects:
    print(f"WARNING: {len(objects)} metadata file(s) already exist and will be overwritten.")
```

**Ask about source:** Same-source or mixed? Follow the same prompting logic as
`berdl-ingest-remote` Step 3b (create `_source_input.yaml` for mixed sources).

**Generate local metadata files:**

Use the `BRONZE_PREFIX`, `NAMESPACE`, `TENANT`, `DATASET`, `BUCKET`, and `USER_TENANT`
variables already set by the notebook config cell — do not recompute them here.
Both shared-tenant and user-tenant paths are handled correctly by those variables.

```python
import uuid, yaml
from datetime import date, datetime, timezone

# BRONZE_PREFIX, NAMESPACE, TENANT, DATASET, BUCKET, USER_TENANT already set by config cell

tables        = [<list of table names>]
ingested_by   = "<name>"
source_shared = "<source url or None>"
source_map    = {}  # {table: source} for mixed-source ingests

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
        "schema_version":       "0.2.0",
        "identifier":           str(uuid.uuid4()),
        "tenant":               None if USER_TENANT else TENANT,
        "dataset":              DATASET,
        "namespace":            NAMESPACE,
        "table":                table,
        "title":                table,
        "source":               source,
        "date_accessed":        today,
        "status":               "in_progress",
        "ingested_by":          ingested_by,
        "ingest_started_at":    now,
        "data_schema_location": sql_bronze,
        "version":              None,
        "description":          None,
        "ingest_contributors":  [],
        "ingest_completed_at":  None,
    }
    out = metadata_dir / f"{table}.yaml"
    with open(out, "w") as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"  wrote {out.name}")
```

**Present required fields for user confirmation — REQUIRED STOPPING POINT.**
Same flow as `berdl-ingest-remote` Step 3b: confirm `title`, `source`, `ingested_by`,
`date_accessed`. Then offer optional fields (`description`, `version`,
`ingest_contributors`).

**Upload metadata (first push — in_progress):**

```python
for table in tables:
    meta_path = metadata_dir / f"{table}.yaml"
    meta_key  = f"{BRONZE_PREFIX}/metadata/{table}.yaml"
    minio_client.fput_object("cdm-lake", meta_key, str(meta_path))
print(f"Metadata uploaded (first push — in_progress) for {len(tables)} table(s)")
print(f"  → s3a://cdm-lake/{BRONZE_PREFIX}/metadata/")
```

### Step 4: Generate, configure, and run the ingest notebook

Copy the in-cluster template into the source directory:

```bash
cp .claude/skills/berdl-ingest/references/ingest_jh.ipynb <DATA_DIR>/<dataset>_ingest.ipynb
```

Edit the configuration cell (`jh0003`) with the absolute `DATA_DIR`, `TENANT`,
`DATASET`, `MODE`, and `USER_TENANT` values.

**Present the ingest plan to the user before running** — list each table, its file
size, and source path. Ask:

> "Here is the ingest plan. Would you like to (a) request any changes, or (b) confirm
> and proceed?"

Do not run the notebook until the user explicitly confirms.

After confirmation, the user runs the notebook interactively in JupyterHub (cell by
cell, or Run All). Unlike the remote skill, there is no `jupyter nbconvert` subprocess
— execution happens directly in the JH kernel.

**What the notebook does:**

1. Connects to Spark and MinIO directly (no tunnels).
2. Detects source format and parses schema.
3. Uploads source files to MinIO bronze via `minio_client.fput_object()` — skips files
   already present at the correct size.
4. For each table: builds a config JSON, uploads it to MinIO, calls `ingest()`, checks
   `success: true`, logs completion to the progress JSONL in MinIO.
5. Verifies row counts via `spark.sql(COUNT(*))`.
6. Performs the metadata second push.

**Resuming an interrupted ingest:** Re-run the Ingest cell. The progress log in MinIO
is read at the start of the cell — completed tables are skipped automatically.

### Step 5: Confirm results and report paths

After the notebook completes, report:

- **Namespace:** `{NAMESPACE}`
- **Tables ingested** and row counts
- **Bronze path:** `s3a://cdm-lake/{BRONZE_PREFIX}/`
- **Silver path:** `{SILVER_BASE}`
- **Progress log:** `s3a://cdm-lake/{PROGRESS_KEY}`
- **Metadata:** `s3a://cdm-lake/{METADATA_PREFIX}/`

These paths can be used to query the data via the `berdl` skill, or to verify the
upload in the MinIO browser (`https://minio.berdl.kbase.us`).

## References

- `references/ingest_jh.ipynb`: notebook template for in-cluster ingest.
- `berdl-ingest-remote/SKILL.md`: off-cluster variant (requires SSH tunnels + pproxy).

## Progress Log Format

Same format as `berdl-ingest-remote`. JSONL at
`s3a://cdm-lake/{BRONZE_PREFIX}/_ingest_progress.jsonl`. Entry types:

**Completion entry** (one per table, written by the ingest cell):
```json
{"table": "my_table", "status": "complete",
 "rows_written": 228709, "timestamp": "2026-05-05T14:30:00Z"}
```

On re-run, the ingest cell reads the log and skips any table with `"status": "complete"`.

## Error Handling

- **`KBASE_AUTH_TOKEN` missing:** Same message as `berdl-ingest-remote` — never ask
  the user to paste their token into chat.
- **`data_lakehouse_ingest` not importable:** Package not installed in this JH
  environment. Ask the user to check their environment setup — do not attempt to pip
  install without confirmation.
- **`get_spark_session()` fails:** The JH environment or Spark sidecar is not
  configured correctly. Report the error verbatim and stop — this is not a tunnel
  issue and cannot be fixed by the agent.
- **`get_minio_client()` fails:** MinIO credentials are not configured in this JH
  environment. Report the error and ask the user to check with a BERDL admin.
- **`ingest()` returns `success: false`:** Raise immediately — do not silently continue
  to the next table. Show the `errors` list from the report.
- **Row count mismatch:** Check `s3a://cdm-lake/{BRONZE_PREFIX}/_ingest_progress.jsonl`
  and the quarantine path at `{SILVER_BASE}/quarantine/`.
- **Source file not found:** Verify `DATA_DIR` is accessible from the JH pod. Global
  share paths (e.g. `/clusterfs/`) may require the server to be spawned with the
  correct mount options.
- **Namespace already exists:** Confirm with user before `MODE = "overwrite"`.

## Safety Rules

1. Never print, log, or echo any MinIO credential fields. When diagnosing MinIO issues,
   never show `accessKey` or `secretKey`.
2. Never print, log, or write `KBASE_AUTH_TOKEN`. Always access via
   `os.getenv("KBASE_AUTH_TOKEN")` or the `.env` file loader.
3. Do not set `MODE = "overwrite"` for an existing namespace without explicit user
   confirmation.
4. Always present the ingest plan and wait for explicit user confirmation before
   executing the notebook.
5. **If a token appears in the conversation:** stop immediately and send the security
   alert message from `berdl-ingest-remote` (revoke token, do not use, add to `.env`).
6. **Never auto-resume a prior ingest.** At Step 1, if memory contains an in-progress
   ingest, mention it once as an option and wait for explicit user choice.

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, or data surprises during
this task, follow the pitfall-capture protocol. Read
`.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine
whether the issue should be added to `docs/pitfalls.md`.

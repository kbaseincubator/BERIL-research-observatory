---
name: berdl-ingest
description: Ingest a local dataset into the BERDL Lakehouse from a local (off-cluster) machine. Handles data format detection and preparation, MinIO upload, and Delta table creation via the data_lakehouse_ingest pipeline. Use when a user wants to load a new dataset — SQLite, TSV, CSV, Parquet, or other tabular formats — into a Lakehouse namespace.
allowed-tools: Bash, Read, Write, Edit
---

# BERDL Local Ingest Skill

Ingests a local dataset into the BERDL Lakehouse as a new tenant namespace, running entirely from a local machine via the off-cluster proxy chain.

---

## Preconditions

Before starting, verify:

1. **Standard BERDL proxy chain is active** — SSH tunnels on 1337/1338, pproxy on 8123, active JupyterHub session. See `berdl-query/references/proxy-setup.md`.
2. **`.venv-berdl` bootstrapped** — run `bash scripts/bootstrap_client.sh` if not present.
3. **Ingest packages installed** — check and install if missing (see Phase 0 below).
4. **`~/.mc/config.json` has a `berdl-minio` alias** — run `bash scripts/configure_mc.sh --berdl-proxy` if not configured.

---

## Inputs to gather from the user

Before running, confirm:

| Input | Example | Notes |
|-------|---------|-------|
| Data source path | `local/litsearch.db` | File or directory |
| Tenant name | `kescience` | Existing Lakehouse tenant |
| Dataset name | `litsearch` | New name for this dataset |

Target namespace will be `{tenant}_{dataset}` (e.g. `kescience_litsearch`).

---

## Phase 0: Bootstrap — install ingest packages

Check whether `data_lakehouse_ingest` is already installed. If not:

```bash
# First time setup — run both scripts in order
bash scripts/bootstrap_client.sh   # creates .venv-berdl and installs query packages
bash scripts/bootstrap_ingest.sh   # adds ingest-specific packages on top
```

If `.venv-berdl` already exists (bootstrap_client.sh was run previously):

```bash
bash scripts/bootstrap_ingest.sh
```

This installs: `jupyter`, `nbconvert`, the three BERDL internal packages (`spark_notebook_base`, `spark_notebook` utils, `data_lakehouse_ingest`) with `--no-deps`, and the standard PyPI dependencies (`minio`, `linkml`, etc.).

The BERDL packages must use `--no-deps` because their transitive dependencies are JupyterHub-only packages unavailable outside the cluster. See `local/README.md` for the full dependency chain explanation.

---

## Phase 1: Detect data format

Inspect the source path to determine what preparation (if any) is needed before ingestion.

**Supported formats (ready to ingest directly):**
- `.tsv` / `.tsv.gz` — tab-separated, one file per table
- `.csv` — comma-separated; set `"delimiter": ","` in the config (see Phase 4)
- `.parquet` / directory of `.parquet` files — one file or partition directory per table

**Formats that require preparation (export to TSV or CSV first):**
- `.db` / `.sqlite` / `.sqlite3` — SQLite database
- `.sql` — SQL dump (restore to SQLite, then export)
- `.json` / `.jsonl` — normalise and export as TSV or CSV
- Any other format — assess and determine approach

Detection heuristic:
```bash
file <path>
# and/or
python3 -c "
from pathlib import Path
p = Path('<path>')
if p.is_dir():
    exts = {f.suffix for f in p.rglob('*') if f.is_file()}
    print('Directory extensions:', exts)
else:
    print('Extension:', p.suffix, '| Magic:', p.read_bytes()[:8].hex())
"
```

---

## Phase 2: Prepare data (if needed)

### SQLite database → TSV

Use Python's `sqlite3` + `csv` modules. Sanitize embedded tabs and newlines in text fields
(these corrupt TSV format and are common in biological text like literature snippets).

```python
import sqlite3, csv
from pathlib import Path

SQLITE_DB = Path("<path>")
TSV_DIR = Path("/tmp/<dataset>_tsv")
TSV_DIR.mkdir(exist_ok=True)

def _clean(v):
    if v is None: return ""
    if isinstance(v, str):
        return v.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    return v

conn = sqlite3.connect(SQLITE_DB)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]

for table in tables:
    out = TSV_DIR / f"{table}.tsv"
    cur.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cur.description]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        w.writerow(cols)
        for row in cur:
            w.writerow([_clean(v) for v in row])
    print(f"{table}: {out.stat().st_size/1e6:.1f} MB")

conn.close()
```

### SQL dump → TSV

Restore the dump to a temporary SQLite DB first, then follow the SQLite → TSV path above:

```bash
sqlite3 /tmp/<dataset>.db < <dump_file>.sql
```

### Parquet → (no conversion needed)

Parquet files can be read directly by Spark. Skip Phase 2 and set `format: parquet` in
the config (see Phase 3). Point `bronze_path` at the `.parquet` file or partition directory.

---

## Phase 3: Inspect data and map schema

Before writing the config, inspect the prepared data to determine column names and types.

**For TSV or CSV files** — infer from headers and sample rows:
```python
import csv
from pathlib import Path

DELIMITERS = {".tsv": "\t", ".csv": ","}

for f in Path("/tmp/<dataset>_files").iterdir():
    delim = DELIMITERS.get(f.suffix, "\t")
    with open(f, newline="") as fh:
        reader = csv.reader(fh, delimiter=delim)
        headers = next(reader)
        sample = next(reader, None)
    print(f"\n{f.name}: {headers}")
    if sample: print("  Sample:", sample[:5])
```

**For SQLite** — use `.schema` and sample queries directly.

**Type mapping** (SQLite/CSV → Spark SQL):

| Source type | Spark SQL type | Notes |
|-------------|---------------|-------|
| TEXT / VARCHAR | STRING | Default for all text |
| INTEGER / INT | INT | Use BIGINT if values > 2^31 |
| REAL / FLOAT | DOUBLE | |
| NUMERIC | DOUBLE | Verify no string-encoded values first |
| BLOB | BINARY | Rare; check if base64-encoded text |
| (empty / ambiguous) | STRING | Safe default; cast later if needed |

**Key pitfall**: Many biological databases store numeric values as strings (e.g. scores, coordinates). Inspect sample rows before assigning numeric types. If in doubt, use STRING and cast in queries.

---

## Phase 4: Generate ingestion config

Build a config dict following the `data_lakehouse_ingest` schema:

```python
import json

TENANT  = "<tenant>"       # e.g. "kescience"
DATASET = "<dataset>"      # e.g. "litsearch"
BUCKET  = "cdm-lake"
BRONZE_PREFIX = f"tenant-general-warehouse/{TENANT}/datasets/{DATASET}"
CONFIG_KEY    = f"{BRONZE_PREFIX}/{DATASET}.json"

# One entry per table — schema_sql is a comma-separated "col TYPE" string
TABLE_SCHEMAS = {
    "TableName": "col1 STRING, col2 INT, col3 DOUBLE",
    # ...
}

config = {
    "tenant": TENANT,
    "dataset": DATASET,
    "is_tenant": True,
    "paths": {
        "data_plane":   f"s3a://{BUCKET}/tenant-general-warehouse/{TENANT}/",
        "bronze_base":  f"s3a://{BUCKET}/{BRONZE_PREFIX}/",
        "silver_base":  f"s3a://{BUCKET}/tenant-sql-warehouse/{TENANT}/{DATASET}.db",
    },
    "defaults": {
        # Set delimiter to match the actual file format:
        #   "\t"  for TSV files
        #   ","   for CSV files
        "csv": {"header": True, "delimiter": "\t", "inferSchema": False}
    },
    "tables": [
        {
            "name":       table,
            "enabled":    True,
            "schema_sql": schema,
            "partition_by": None,
            # Extension must match the actual uploaded files (.tsv or .csv)
            "bronze_path": f"s3a://{BUCKET}/{BRONZE_PREFIX}/{table}.tsv",
        }
        for table, schema in TABLE_SCHEMAS.items()
    ],
}
```

For CSV files, set `"delimiter": ","` and use `.csv` extensions in `bronze_path`.
For Parquet tables, set `"bronze_path"` to the `.parquet` file or partition directory path
on MinIO and omit `schema_sql` (Parquet carries its own schema).

The pipeline derives the target namespace as `{tenant}_{dataset}` (e.g. `kescience_litsearch`).

---

## Phase 5: Upload to MinIO

Upload the config JSON and all data files to the bronze path. Use `mc` with the proxy:

```bash
export https_proxy=http://127.0.0.1:8123
export no_proxy=localhost,127.0.0.1

# Upload config
mc cp /tmp/<dataset>_config.json \
    berdl-minio/cdm-lake/tenant-general-warehouse/<tenant>/datasets/<dataset>/<dataset>.json

# Upload TSVs
mc cp /tmp/<dataset>_tsv/ \
    berdl-minio/cdm-lake/tenant-general-warehouse/<tenant>/datasets/<dataset>/ \
    --recursive

# Verify
mc ls berdl-minio/cdm-lake/tenant-general-warehouse/<tenant>/datasets/<dataset>/
```

---

## Phase 6: Run the ingestion pipeline

Create and execute a notebook following the `litsearch_ingest.ipynb` pattern.
Save it to `local/<dataset>_ingest.ipynb`.

The notebook has four critical elements not present in the JupyterHub version:

### 6a. sys.modules stubs (MUST run before importing data_lakehouse_ingest)

`berdl_notebook_utils.__init__` imports JupyterHub-only packages at module load time.
Stub out the entire package in `sys.modules` before any import of `data_lakehouse_ingest`:

```python
import sys
from types import ModuleType

_STUB_MODULES = [
    "berdl_notebook_utils",
    "berdl_notebook_utils.berdl_settings",
    "berdl_notebook_utils.clients",
    "berdl_notebook_utils.setup_spark_session",
    "berdl_notebook_utils.spark",
    "berdl_notebook_utils.spark.database",
    "berdl_notebook_utils.spark.cluster",
    "berdl_notebook_utils.spark.dataframe",
    "berdl_notebook_utils.minio_governance",
]
for _name in _STUB_MODULES:
    sys.modules[_name] = ModuleType(_name)

# Stub create_namespace_if_not_exists — the only berdl_notebook_utils function
# actually called by the ingest pipeline (in orchestrator/init_utils.py).
def _create_namespace_if_not_exists(spark, namespace=None, append_target=True, tenant_name=None):
    ns = f"{tenant_name}_{namespace}" if tenant_name else namespace
    location = f"s3a://cdm-lake/tenant-sql-warehouse/{tenant_name}/{ns}.db"
    spark.sql(f"CREATE DATABASE IF NOT EXISTS `{ns}` LOCATION '{location}'")
    print(f"Namespace {ns} ready at {location}")
    return ns

sys.modules["berdl_notebook_utils.spark.database"].create_namespace_if_not_exists = (
    _create_namespace_if_not_exists
)
sys.modules["berdl_notebook_utils.setup_spark_session"].get_spark_session = None
sys.modules["berdl_notebook_utils.clients"].get_minio_client = None

from minio import Minio
from data_lakehouse_ingest import ingest
from get_spark_session import get_spark_session
```

### 6b. Build clients with proxy

The Python `minio` library does not honour system proxy env vars — a `urllib3.ProxyManager`
must be passed explicitly. Credentials are read from `~/.mc/config.json`.

```python
import json, urllib3
from pathlib import Path

_mc  = json.loads(Path.home().joinpath(".mc/config.json").read_text())
_b   = _mc["aliases"]["berdl-minio"]

minio_client = Minio(
    endpoint   = _b["url"].replace("https://", "").replace("http://", ""),
    access_key = _b["accessKey"],
    secret_key = _b["secretKey"],
    secure     = _b["url"].startswith("https"),
    http_client= urllib3.ProxyManager("http://127.0.0.1:8123"),
)

spark = get_spark_session()   # sets grpc_proxy + https_proxy env vars automatically

# Wire real clients into stubs for any internal code paths
sys.modules["berdl_notebook_utils.setup_spark_session"].get_spark_session = lambda **kw: spark
sys.modules["berdl_notebook_utils.clients"].get_minio_client              = lambda **kw: minio_client
```

### 6c. Call ingest() with explicit clients

```python
cfg_path = f"s3a://cdm-lake/{CONFIG_KEY}"
report   = ingest(cfg_path, spark=spark, minio_client=minio_client)
report
```

Passing `spark` and `minio_client` explicitly prevents `core.py` from calling the stubbed
`get_spark_session()` / `get_minio_client()` — only `create_namespace_if_not_exists` is
reached through the stub layer.

### 6d. Path resolution

When run via `jupyter nbconvert`, the kernel's working directory is the notebook's
directory, not the repo root. Use a fallback for relative paths:

```python
_candidates = [Path("<dataset>.db"), Path("local/<dataset>.db")]
SOURCE = next((p for p in _candidates if p.exists()), None)
```

### Execute

```bash
source .venv-berdl/bin/activate
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=600 \
    local/<dataset>_ingest.ipynb
```

---

## Phase 7: Verify

```python
spark.sql("SHOW TABLES IN <tenant>_<dataset>").show()

for tbl in TABLE_SCHEMAS:
    count = spark.sql(f"SELECT count(*) FROM <tenant>_<dataset>.{tbl}").collect()[0][0]
    print(f"  {tbl:30s}: {count:>10,}")

spark.stop()
```

Row counts must match the source exactly. Any mismatch indicates a schema type mismatch
or TSV parsing issue — check the quarantine path in the ingest report:
`s3a://cdm-lake/tenant-sql-warehouse/<tenant>/<tenant>_<dataset>.db/quarantine/`.

---

## Commit the notebook

Once verified, commit the notebook with outputs saved:

```bash
git add local/<dataset>_ingest.ipynb local/README.md
git commit -m "Add <dataset> ingest notebook for kescience_<dataset>"
```

Update `local/README.md` with the new dataset row.

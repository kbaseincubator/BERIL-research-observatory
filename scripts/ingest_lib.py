"""BERDL ingest infrastructure library.

Provides all plumbing used by the ingest notebook template. Import from here
instead of duplicating this code in notebooks:

    from ingest_lib import (
        initialize, detect_source_files, parse_sql_schema,
        build_table_stats, print_preflight_plan,
        upload_files, run_ingest, verify_ingest,
    )

Public API
----------
initialize()
    Start Spark and MinIO. Returns (spark, minio_client).

detect_source_files(data_dir)
    Scan a directory for SQLite / TSV / CSV files. Returns source details.

parse_sql_schema(sql_path)
    Parse CREATE TABLE statements. Returns (schemas, schema_defs).

export_sqlite(source_db, dataset, schemas)
    Export a SQLite database to TSV files. Returns list of Paths.

build_table_stats(source_files, schemas, chunk_target_gb, chunked_ingest)
    Count lines and plan chunks. Returns TABLE_STATS dict.

print_preflight_plan(table_stats, namespace, mode, bucket, bronze_prefix,
                     progress_key, confirmed)
    Print upload/ingest plan. Raises if confirmed=False.

upload_files(minio_client, bucket, config_key, table_stats, tenant, dataset,
             bronze_prefix, silver_base, schemas, schema_defs, mode, file_ext,
             delimiter)
    Upload dataset config JSON and data files to MinIO bronze.

run_ingest(spark, minio_client, table_stats, schemas, schema_defs, namespace,
           tenant, dataset, bucket, bronze_prefix, silver_base, mode, file_ext,
           delimiter, progress_key)
    Ingest all tables into Delta silver. Returns the (possibly reconnected) spark.

verify_ingest(spark, namespace, table_stats, minio_client, bucket,
              progress_key, silver_base)
    Query row counts and compare against expected. Prints results.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

logging.basicConfig(level=logging.INFO)


# ── Stub injection ─────────────────────────────────────────────────────────────
# data_lakehouse_ingest imports berdl_notebook_utils submodules that only exist
# on JupyterHub. Inject lightweight stubs so the package loads off-cluster.

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
    if _name not in sys.modules:
        sys.modules[_name] = ModuleType(_name)


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

from data_lakehouse_ingest import ingest as _lakehouse_ingest  # noqa: E402
from get_spark_session import get_spark_session  # noqa: E402


# ── Infrastructure ─────────────────────────────────────────────────────────────

def _port_listening(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _check_ssh_tunnels() -> None:
    """Raise with full ssh commands if tunnels on 1337/1338 are not running."""
    missing = [p for p in [1337, 1338] if not _port_listening(p)]
    if missing:
        raise RuntimeError(
            f"\n[setup] SSH tunnel(s) not detected on port(s): {missing}\n"
            "Please start the missing tunnel(s) in a terminal, then re-run this cell:\n"
            + "\n".join(
                f"  ssh -f -N -o ServerAliveInterval=60 -D {p} "
                "ac.<username>@login1.berkeley.kbase.us"
                for p in missing
            )
        )
    print("[setup] SSH tunnels OK (ports 1337, 1338)")


def _start_pproxy_if_needed() -> None:
    """Start pproxy on :8123 as a background process if not already running."""
    if _port_listening(8123):
        print("[setup] pproxy OK (port 8123)")
        return
    print("[setup] pproxy not running — starting automatically...")
    subprocess.Popen(
        [sys.executable, "-c",
         "import sys, asyncio; "
         "sys.argv = ['pproxy', '-l', 'http://:8123', '-r', 'socks5://127.0.0.1:1338']; "
         "asyncio.set_event_loop(asyncio.new_event_loop()); "
         "from pproxy.server import main; main()"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    if _port_listening(8123):
        print("[setup] pproxy started on :8123")
    else:
        print("[setup] WARNING: pproxy may not have started — check port 8123 manually")


def _ensure_jupyterhub_server() -> None:
    """Auto-login and spawn JupyterHub server via berdl-remote if not running."""
    config_path = Path.home() / ".berdl" / "remote-config.yaml"
    if not config_path.exists():
        print("[setup] No berdl-remote config — logging in with KBASE_AUTH_TOKEN...")
        r = subprocess.run(
            ["berdl-remote", "login", "--hub-url", "https://hub.berdl.kbase.us"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"[setup] WARNING: berdl-remote login failed:\n{r.stderr.strip()}")
            return
        print(f"[setup] {r.stdout.strip()}")

    r = subprocess.run(["berdl-remote", "status"], capture_output=True, text=True)
    if r.returncode == 0 and "Kernel available" in r.stdout:
        print("[setup] JupyterHub server and kernel OK")
        return

    print("[setup] JupyterHub server not ready — spawning...")
    r = subprocess.run(
        ["berdl-remote", "spawn", "--timeout", "120"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"[setup] WARNING: berdl-remote spawn failed:\n{r.stderr.strip()}")
        return
    print(f"[setup] {r.stdout.strip()}")
    print("[setup] Waiting 40s for Spark Connect sidecar to start...")
    time.sleep(40)


def _check_spark_health(spark) -> bool:
    """Return True if the Spark session responds to a trivial query."""
    try:
        spark.sql("SELECT 1").collect()
        return True
    except Exception:
        return False


def _build_minio_client():
    import urllib3
    from minio import Minio

    mc_cfg_path = Path.home() / ".mc" / "config.json"
    if not mc_cfg_path.exists():
        raise RuntimeError(
            "[minio] ~/.mc/config.json not found.\n"
            "Run: bash scripts/configure_mc.sh --berdl-proxy"
        )
    mc_cfg = json.loads(mc_cfg_path.read_text())
    if "berdl-minio" not in mc_cfg.get("aliases", {}):
        raise RuntimeError(
            "[minio] No 'berdl-minio' alias found in ~/.mc/config.json.\n"
            "Run: bash scripts/configure_mc.sh --berdl-proxy"
        )
    berdl = mc_cfg["aliases"]["berdl-minio"]
    client = Minio(
        endpoint=berdl["url"].replace("https://", "").replace("http://", ""),
        access_key=berdl["accessKey"],
        secret_key=berdl["secretKey"],
        secure=berdl["url"].startswith("https"),
        http_client=urllib3.ProxyManager("http://127.0.0.1:8123"),
    )
    try:
        buckets = [b.name for b in client.list_buckets()]
        if "cdm-lake" not in buckets:
            raise RuntimeError("cdm-lake bucket not found in MinIO listing")
        print("[minio] MinIO connection OK")
    except Exception as e:
        raise RuntimeError(
            f"[minio] MinIO connection failed: {e}\n"
            "Check that pproxy is running (:8123) and that credentials in "
            "~/.mc/config.json are valid.\n"
            "Re-run: bash scripts/configure_mc.sh --berdl-proxy"
        ) from e
    return client


def _connect_spark(retries: int = 3):
    """Connect to Spark with retries. Updates berdl_notebook_utils stub on success."""
    last_error = None
    for attempt in range(retries):
        try:
            spark = get_spark_session()
            sys.modules["berdl_notebook_utils.setup_spark_session"].get_spark_session = (
                lambda **kw: spark
            )
            print("[spark] Spark session connected.")
            return spark
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                wait = 20 * (attempt + 1)
                print(f"[spark] Attempt {attempt + 1}/{retries} failed — retrying in {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"[spark] Failed to connect after {retries} attempts: {last_error}")


def initialize():
    """Set up Spark and MinIO, returning (spark, minio_client).

    Checks SSH tunnels (raises if missing), auto-starts pproxy, auto-spawns
    the JupyterHub server, then connects. All steps except SSH tunnels are
    fully automatic — no browser login or user interaction required.
    """
    _check_ssh_tunnels()
    _start_pproxy_if_needed()
    _ensure_jupyterhub_server()
    print("[spark] Initializing Spark session...")
    spark = _connect_spark()
    minio_client = _build_minio_client()
    sys.modules["berdl_notebook_utils.clients"].get_minio_client = lambda **kw: minio_client
    print("Spark and MinIO clients ready.")
    return spark, minio_client


def reconnect_spark(old_spark):
    """Stop a dead Spark session and return a new one.

    Use when a session times out mid-ingest:

        spark = reconnect_spark(spark)
    """
    try:
        old_spark.stop()
    except Exception:
        pass
    _check_ssh_tunnels()
    _start_pproxy_if_needed()
    _ensure_jupyterhub_server()
    print("[spark] Reconnecting...")
    return _connect_spark()


# ── Format detection ───────────────────────────────────────────────────────────

def detect_source_files(data_dir: Path):
    """Scan data_dir and return (source_mode, source_db, sql_schema, data_files,
    file_ext, delimiter).

    source_mode  -- 'sqlite', 'parquet', 'tsv', or 'csv'
    source_db    -- Path to the .db file, or None
    sql_schema   -- Path to the .sql schema file, or None (always None for parquet)
    data_files   -- list of Paths to the files to ingest (empty for sqlite mode;
                    populated by export_sqlite)
    file_ext     -- '.parquet', '.tsv', or '.csv'
    delimiter    -- '\\t' or ',' (ignored for parquet)
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"DATA_DIR not found: {data_dir}")

    db_files      = (sorted(data_dir.glob("*.db"))
                     + sorted(data_dir.glob("*.sqlite"))
                     + sorted(data_dir.glob("*.sqlite3")))
    sql_files     = sorted(data_dir.glob("*.sql"))
    tsv_files     = sorted(data_dir.glob("*.tsv"))
    csv_files     = sorted(data_dir.glob("*.csv"))
    parquet_files = sorted(data_dir.glob("*.parquet"))

    print(f"SQLite databases : {[f.name for f in db_files]}")
    print(f"SQL schema files : {[f.name for f in sql_files]}")
    print(f"TSV files        : {[f.name for f in tsv_files]}")
    print(f"CSV files        : {[f.name for f in csv_files]}")
    print(f"Parquet files    : {[f.name for f in parquet_files]}")

    sql_schema = sql_files[0] if sql_files else None
    if not parquet_files:
        print(f"Schema file      : "
              f"{sql_schema.name if sql_schema else 'none — all columns default to STRING'}")

    if db_files:
        print(f"\nMode: SQLite -> TSV  (source: {db_files[0].name})")
        return "sqlite", db_files[0], sql_schema, [], ".tsv", "\t"
    elif parquet_files:
        print(f"\nMode: Parquet files ({len(parquet_files)} found)")
        print("Schema           : embedded in Parquet metadata")
        return "parquet", None, None, parquet_files, ".parquet", "\t"
    elif tsv_files:
        print(f"\nMode: TSV files ({len(tsv_files)} found)")
        return "tsv", None, sql_schema, tsv_files, ".tsv", "\t"
    elif csv_files:
        print(f"\nMode: CSV files ({len(csv_files)} found)")
        return "csv", None, sql_schema, csv_files, ".csv", ","
    else:
        raise ValueError(f"No recognised source files found in {data_dir}")


# ── Schema parsing ─────────────────────────────────────────────────────────────

_TYPE_MAP = {
    "TEXT": "STRING",    "VARCHAR": "STRING",  "CHAR": "STRING",   "CLOB": "STRING",
    "INTEGER": "INT",    "INT": "INT",          "SMALLINT": "INT",  "TINYINT": "INT",
    "MEDIUMINT": "INT",  "BIGINT": "BIGINT",
    "REAL": "DOUBLE",    "FLOAT": "DOUBLE",     "DOUBLE": "DOUBLE",
    "NUMERIC": "DOUBLE", "DECIMAL": "DOUBLE",   "NUMBER": "DOUBLE",
    "BLOB": "BINARY",    "BOOLEAN": "BOOLEAN",  "BOOL": "BOOLEAN",
}


def parse_sql_schema(sql_path: Path):
    """Parse CREATE TABLE statements from a .sql file.

    Returns:
        schemas     -- {table: 'col TYPE, col TYPE, ...'} DDL strings for Spark
        schema_defs -- {table: [{'column', 'type', 'nullable', 'comment'}, ...]}
    """
    text = sql_path.read_text(encoding="utf-8", errors="replace")
    schemas: dict[str, str] = {}
    schema_defs: dict[str, list] = {}
    pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
        r'[`"\[]?(\w+)[`"\]]?\s*\(([^;]+?)\)\s*;',
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(text):
        table_name = m.group(1)
        cols: list[str] = []
        col_defs: list[dict] = []
        for line in m.group(2).splitlines():
            line = re.sub(r"/\*.*?\*/", "", line).strip()
            line = re.sub(r"--.*$", "", line).strip()
            line = line.rstrip(",")
            if not line:
                continue
            if re.match(
                r"(PRIMARY\s+KEY|UNIQUE|INDEX|FOREIGN\s+KEY|CHECK|CONSTRAINT)\b",
                line, re.I,
            ):
                continue
            tokens = re.split(r"\s+", line, maxsplit=2)
            if len(tokens) < 2:
                continue
            col_name   = re.sub(r'[`"\[\]]', "", tokens[0])
            raw_type   = re.sub(r"\(.*", "", tokens[1]).upper()
            spark_type = _TYPE_MAP.get(raw_type, "STRING")
            rest       = tokens[2] if len(tokens) > 2 else ""
            nullable   = not bool(re.search(r"\bNOT\s+NULL\b", rest, re.I))
            comment_m  = re.search(r"COMMENT\s+'([^']*)'", rest, re.I)
            cols.append(f"{col_name} {spark_type}")
            col_def = {
                "column":   col_name,
                "type":     spark_type.lower(),
                "nullable": nullable,
            }
            if comment_m:
                col_def["comment"] = comment_m.group(1)
            col_defs.append(col_def)
        if cols:
            schemas[table_name]     = ", ".join(cols)
            schema_defs[table_name] = col_defs

    print(f"Parsed {len(schemas)} tables from {sql_path.name}:")
    for name, defs in schema_defs.items():
        print(f"  {name}:")
        for col in defs:
            nullable_tag = "" if col["nullable"] else "  NOT NULL"
            comment_tag  = f"  # {col['comment']}" if col.get("comment") else ""
            print(f"    {col['column']}: {col['type']}{nullable_tag}{comment_tag}")

    return schemas, schema_defs


# ── Data preparation ───────────────────────────────────────────────────────────

def _count_lines(filepath: Path) -> int:
    """Count newlines in a file efficiently. Result includes the header line."""
    n = 0
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            n += block.count(b"\n")
    return n


def _clean(v: Any) -> str:
    """Sanitize a SQLite value for TSV output."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    return v


def export_sqlite(source_db: Path, dataset: str, schemas: dict) -> list:
    """Export all tables from a SQLite database to TSV files.

    Writes files to /tmp/<dataset>_tsv/. Fills in missing entries in schemas
    from column names found in the database. Returns sorted list of TSV Paths.
    """
    work_dir = Path(f"/tmp/{dataset}_tsv")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    conn = sqlite3.connect(source_db)
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]

    for table in tables:
        out = work_dir / f"{table}.tsv"
        cur.execute(f'SELECT * FROM "{table}"')
        cols = [d[0] for d in cur.description]
        if table not in schemas:
            schemas[table] = ", ".join(f"{c} STRING" for c in cols)
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            w.writerow(cols)
            for row in cur:
                w.writerow([_clean(v) for v in row])
        rows = cur.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        print(f"  {table:30s}: {rows:>9,} rows  {out.stat().st_size / 1e6:.1f} MB")

    conn.close()
    return sorted(work_dir.glob("*.tsv"))


def build_table_stats(
    source_files: list,
    schemas: dict,
    chunk_target_gb: float,
    chunked_ingest: bool,
    delimiter: str = "\t",
) -> dict:
    """Count lines and calculate chunk plan for each source file.

    For any table not already in schemas, reads the header row and defaults
    all columns to STRING. Pass delimiter matching your source files ('\t' for
    TSV, ',' for CSV).

    Returns TABLE_STATS dict:
        {table: {path, size_bytes, data_lines, chunk_size, n_chunks, chunked}}
    """
    chunk_target_bytes = chunk_target_gb * 1e9
    table_stats: dict = {}

    # Infer STRING schema from headers for any TSV/CSV table not covered by a .sql file.
    # Parquet files carry embedded schema — skip them.
    for f in source_files:
        if f.suffix == ".parquet":
            continue
        table = f.stem
        if table not in schemas:
            with open(f, newline="", encoding="utf-8") as fh:
                cols = next(csv.reader(fh, delimiter=delimiter))
            schemas[table] = ", ".join(f"{c} STRING" for c in cols)
            print(f"  {table}: no schema found — defaulting all {len(cols)} columns to STRING")

    print(f"Analyzing {len(source_files)} table(s) — counting lines...")
    for f in source_files:
        table      = f.stem
        size_bytes = f.stat().st_size
        print(f"  {f.name}: {size_bytes / 1e9:.1f} GB", end=" ", flush=True)
        total_lines = _count_lines(f)
        data_lines  = max(total_lines - 1, 0)   # exclude header

        # Parquet uses Spark's native reader — pandas chunking is not supported.
        if f.suffix == ".parquet":
            chunk_size, n_chunks = data_lines, 1
        elif chunked_ingest and size_bytes > chunk_target_bytes and data_lines > 0:
            chunk_size = max(1, round(data_lines * chunk_target_bytes / size_bytes))
            n_chunks   = math.ceil(data_lines / chunk_size)
        else:
            chunk_size = data_lines
            n_chunks   = 1

        table_stats[table] = {
            "path":       f,
            "size_bytes": size_bytes,
            "data_lines": data_lines,
            "chunk_size": chunk_size,
            "n_chunks":   n_chunks,
            "chunked":    n_chunks > 1,
        }
        note = (f"{n_chunks} chunks x ~{chunk_size:,} lines"
                if n_chunks > 1 else "single ingest")
        print(f"-> {data_lines:,} data lines  [{note}]")

    return table_stats


# ── Pre-flight ─────────────────────────────────────────────────────────────────

def print_preflight_plan(
    table_stats: dict,
    namespace: str,
    mode: str,
    bucket: str,
    bronze_prefix: str,
    progress_key: str,
    confirmed: bool,
) -> None:
    """Print the upload and ingest plan.

    Raises RuntimeError if confirmed=False so the notebook halts after display.
    Set CONFIRMED = True in the configuration cell and re-run to proceed.
    """
    W = 72
    print("=" * W)
    print("PRE-FLIGHT PLAN")
    print("=" * W)

    total_gb = sum(s["size_bytes"] for s in table_stats.values()) / 1e9
    print("\nSTEP 1 -- MinIO Upload  (all tables uploaded before any ingest begins)")
    for table, s in table_stats.items():
        print(f"  {table:<45s}  {s['size_bytes'] / 1e9:>7.1f} GB")
    print(f"  {'TOTAL':<45s}  {total_gb:>7.1f} GB")

    print(f"\nSTEP 2 -- Spark Ingest into Delta  (namespace: {namespace})")
    for table, s in table_stats.items():
        if s["chunked"]:
            chunk_gb = s["size_bytes"] / s["n_chunks"] / 1e9
            print(f"  {table:<45s}  {s['n_chunks']} chunks x ~{s['chunk_size']:,} lines"
                  f"  (~{chunk_gb:.1f} GB each)  [CHUNKED]")
        else:
            print(f"  {table:<45s}  {s['data_lines']:,} lines  [single ingest]")

    print(f"\nProgress log : s3a://{bucket}/{progress_key}")
    print(f"Ingest mode  : {mode}")
    print("=" * W)

    if not confirmed:
        raise RuntimeError(
            "\nReview the plan above.\n"
            "If it looks correct, set CONFIRMED = True in the Configuration cell "
            "and re-run from this cell onward."
        )
    print("CONFIRMED — proceeding.")


# ── Upload ─────────────────────────────────────────────────────────────────────

def _minio_object_size(minio_client, bucket: str, key: str) -> int:
    """Return remote object size in bytes, or -1 if it does not exist."""
    try:
        return minio_client.stat_object(bucket, key).size
    except Exception as e:
        if any(tag in str(e) for tag in ("NoSuchKey", "does not exist", "404")):
            return -1
        raise


def _build_dataset_config(
    tenant, dataset, bucket, bronze_prefix, silver_base,
    table_stats, schemas, schema_defs, mode, file_ext, delimiter,
) -> dict:
    is_parquet = file_ext == ".parquet"
    defaults = (
        {"parquet": {"inferSchema": True}}
        if is_parquet
        else {"csv": {"header": True, "delimiter": delimiter, "inferSchema": False}}
    )
    return {
        "tenant": tenant, "dataset": dataset, "is_tenant": True,
        "paths": {
            "data_plane":  f"s3a://{bucket}/tenant-general-warehouse/{tenant}/",
            "bronze_base": f"s3a://{bucket}/{bronze_prefix}/",
            "silver_base": silver_base,
        },
        "defaults": defaults,
        "tables": [
            {
                "name": table, "enabled": True,
                "schema": schema_defs.get(table, []),
                "partition_by": None, "mode": mode,
                "bronze_path": f"s3a://{bucket}/{bronze_prefix}/{table}{file_ext}",
            }
            for table in table_stats
        ],
    }


def upload_files(
    minio_client,
    bucket: str,
    config_key: str,
    table_stats: dict,
    tenant: str,
    dataset: str,
    bronze_prefix: str,
    silver_base: str,
    schemas: dict,
    schema_defs: dict,
    mode: str,
    file_ext: str,
    delimiter: str,
) -> None:
    """Upload dataset config JSON and all data files to MinIO bronze.

    Skips any file whose size already matches the remote object, so re-running
    after a partial upload only uploads what is missing.
    """
    config = _build_dataset_config(
        tenant, dataset, bucket, bronze_prefix, silver_base,
        table_stats, schemas, schema_defs, mode, file_ext, delimiter,
    )
    config_bytes = json.dumps(config, indent=2).encode("utf-8")
    minio_client.put_object(
        bucket, config_key, io.BytesIO(config_bytes), len(config_bytes),
        content_type="application/json",
    )
    print(f"Config -> s3a://{bucket}/{config_key}")

    print("\nChecking / uploading data files...")
    for table, s in table_stats.items():
        key         = f"{bronze_prefix}/{table}{file_ext}"
        local_size  = s["size_bytes"]
        remote_size = _minio_object_size(minio_client, bucket, key)

        if remote_size == local_size:
            print(f"  {table}: {local_size / 1e9:.1f} GB — already in MinIO, skipping")
            continue
        if remote_size != -1:
            print(f"  {table}: size mismatch "
                  f"(local {local_size:,} B vs MinIO {remote_size:,} B) — re-uploading")
        else:
            print(f"  {table}: {local_size / 1e9:.1f} GB — uploading...", end=" ", flush=True)

        minio_client.fput_object(bucket, key, str(s["path"]))
        print(f"done  -> s3a://{bucket}/{key}")

    print("\nUpload complete.")


# ── Progress log ───────────────────────────────────────────────────────────────

def _load_progress_log(minio_client, bucket: str, progress_key: str) -> list:
    """Load JSONL progress log from MinIO. Returns [] if not found."""
    try:
        resp = minio_client.get_object(bucket, progress_key)
        entries = []
        for line in resp.read().decode().splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
        return entries
    except Exception as e:
        if any(tag in str(e) for tag in ("NoSuchKey", "does not exist", "404")):
            return []
        raise


def _append_progress(minio_client, bucket: str, progress_key: str, entry: dict) -> None:
    """Append one entry to the MinIO progress log (read-modify-write)."""
    entries = _load_progress_log(minio_client, bucket, progress_key)
    entries.append(entry)
    data = ("\n".join(json.dumps(e) for e in entries) + "\n").encode()
    minio_client.put_object(
        bucket, progress_key, io.BytesIO(data), len(data),
        content_type="application/x-ndjson",
    )


# ── Ingest engine ──────────────────────────────────────────────────────────────

def _spark_type(type_name: str):
    from pyspark.sql import types as T
    return {
        "STRING":  T.StringType(),
        "INT":     T.IntegerType(),
        "BIGINT":  T.LongType(),
        "DOUBLE":  T.DoubleType(),
        "BOOLEAN": T.BooleanType(),
        "BINARY":  T.BinaryType(),
    }.get(type_name, T.StringType())


def _spark_schema(schema_ddl: str):
    from pyspark.sql import types as T
    fields = []
    for part in schema_ddl.split(","):
        tokens = part.strip().split()
        if len(tokens) >= 2:
            fields.append(T.StructField(tokens[0], _spark_type(tokens[1]), True))
    return T.StructType(fields)


def _ingest_chunked(
    spark, minio_client, bucket, progress_key,
    namespace, table, stats, schema_ddl, delta_path, mode, delimiter, progress_log,
):
    """Stream a large source file into Delta in line-count chunks."""
    import pandas as pd
    from pyspark.sql import functions as F
    from pyspark.sql import types as T

    target_schema    = _spark_schema(schema_ddl) if schema_ddl else None
    done_chunks      = {e["chunk"] for e in progress_log
                        if e["table"] == table and e.get("status") == "ingested"}
    rows_done        = sum(e["rows_written"] for e in progress_log
                          if e["table"] == table and e.get("status") == "ingested")
    table_registered = bool(done_chunks)

    reader = pd.read_csv(
        stats["path"], sep=delimiter, chunksize=stats["chunk_size"],
        dtype=str, keep_default_na=False, na_values=[],
    )
    for chunk_num, chunk_df in enumerate(reader):
        if chunk_num in done_chunks:
            print(f"  Chunk {chunk_num + 1}/{stats['n_chunks']}: already ingested — skipping")
            continue

        start_line = chunk_num * stats["chunk_size"] + 1
        end_line   = start_line + len(chunk_df) - 1

        if target_schema:
            str_schema = T.StructType([
                T.StructField(f.name, T.StringType(), True) for f in target_schema.fields
            ])
            sdf = spark.createDataFrame(chunk_df, schema=str_schema)
            for field in target_schema.fields:
                if not isinstance(field.dataType, T.StringType):
                    sdf = sdf.withColumn(field.name, F.col(field.name).cast(field.dataType))
        else:
            sdf = spark.createDataFrame(chunk_df)

        write_mode = mode if (chunk_num == 0 and not done_chunks) else "append"
        sdf.write.format("delta").mode(write_mode).save(delta_path)

        if not table_registered:
            spark.sql(
                f"CREATE TABLE IF NOT EXISTS `{namespace}`.`{table}` "
                f"USING DELTA LOCATION '{delta_path}'"
            )
            table_registered = True

        rows_done += len(chunk_df)
        _append_progress(minio_client, bucket, progress_key, {
            "table": table, "chunk": chunk_num,
            "start_line": start_line, "end_line": end_line,
            "rows_written": len(chunk_df), "rows_cumulative": rows_done,
            "status": "ingested",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        print(f"  Chunk {chunk_num + 1}/{stats['n_chunks']}: "
              f"lines {start_line:,}-{end_line:,}  "
              f"({len(chunk_df):,} rows written, {rows_done:,} cumulative)")

    return rows_done


def run_ingest(
    spark,
    minio_client,
    table_stats: dict,
    schemas: dict,
    schema_defs: dict,
    namespace: str,
    tenant: str,
    dataset: str,
    bucket: str,
    bronze_prefix: str,
    silver_base: str,
    mode: str,
    file_ext: str,
    delimiter: str,
    progress_key: str,
):
    """Ingest all tables into Delta silver.

    Loads the progress log first — completed tables and chunks are skipped
    automatically so an interrupted ingest can be resumed by re-running this call.

    Returns the spark session (which may be a new session if reconnection occurred).
    """
    progress_log    = _load_progress_log(minio_client, bucket, progress_key)
    complete_tables = {e["table"] for e in progress_log if e.get("status") == "complete"}

    if progress_log:
        print(f"Loaded {len(progress_log)} progress log entries.")
        if complete_tables:
            print(f"  Already complete: {', '.join(sorted(complete_tables))}")
    else:
        print("No prior progress — ingesting all tables from scratch.")

    spark.sql(f"CREATE DATABASE IF NOT EXISTS `{namespace}` LOCATION '{silver_base}'")
    print(f"Namespace {namespace} ready.\n")

    for table, stats in table_stats.items():
        if table in complete_tables:
            print(f"{table}: already complete — skipping\n")
            continue

        print("=" * 60)
        print(f"Ingesting: {table}")
        print(f"  {stats['data_lines']:,} rows | {stats['n_chunks']} chunk(s) "
              f"| {stats['size_bytes'] / 1e9:.1f} GB")

        if not _check_spark_health(spark):
            print("[spark] Session unhealthy — reconnecting...")
            spark = reconnect_spark(spark)

        if not stats["chunked"]:
            # Small table: single ingest via data_lakehouse_ingest pipeline
            tbl_cfg = _build_dataset_config(
                tenant, dataset, bucket, bronze_prefix, silver_base,
                {table: stats}, schemas, schema_defs, mode, file_ext, delimiter,
            )
            tbl_cfg_key   = f"{bronze_prefix}/{table}_config.json"
            tbl_cfg_bytes = json.dumps(tbl_cfg, indent=2).encode()
            minio_client.put_object(
                bucket, tbl_cfg_key, io.BytesIO(tbl_cfg_bytes), len(tbl_cfg_bytes),
                content_type="application/json",
            )
            result = _lakehouse_ingest(
                f"s3a://{bucket}/{tbl_cfg_key}",
                spark=spark, minio_client=minio_client,
            )
            if result and not result.get("success", True):
                raise RuntimeError(f"ingest() returned failure for {table}: {result}")
            rows_done = stats["data_lines"]
            _append_progress(minio_client, bucket, progress_key, {
                "table": table, "chunk": 0,
                "start_line": 1, "end_line": rows_done,
                "rows_written": rows_done, "rows_cumulative": rows_done,
                "status": "ingested",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        else:
            # Large table: chunked streaming ingest
            delta_path = f"{silver_base}/{table}"
            rows_done  = _ingest_chunked(
                spark, minio_client, bucket, progress_key,
                namespace, table, stats, schemas.get(table, ""),
                delta_path, mode, delimiter, progress_log,
            )

        _append_progress(minio_client, bucket, progress_key, {
            "table": table, "status": "complete",
            "total_rows": rows_done, "total_chunks": stats["n_chunks"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        print(f"  {table}: {rows_done:,} rows — COMPLETE\n")

    print("All tables ingested.")
    return spark


# ── Verification ───────────────────────────────────────────────────────────────

def verify_ingest(
    spark,
    namespace: str,
    table_stats: dict,
    minio_client,
    bucket: str,
    progress_key: str,
    silver_base: str,
) -> None:
    """Query row counts from Delta and compare against expected line counts.

    Prints a pass/fail summary for each table and flags any mismatches.
    """
    print("=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    spark.sql(f"SHOW TABLES IN `{namespace}`").show()

    progress_log = _load_progress_log(minio_client, bucket, progress_key)
    all_match    = True

    print("Row counts (Delta vs expected):")
    for table, stats in table_stats.items():
        count    = spark.sql(
            f"SELECT COUNT(*) FROM `{namespace}`.`{table}`"
        ).collect()[0][0]
        expected = stats["data_lines"]
        match    = "OK" if count == expected else "MISMATCH"
        if count != expected:
            all_match = False
        print(f"  {table:<45s}  {count:>12,}  expected {expected:>12,}  [{match}]")

    print("\nProgress log summary:")
    for e in progress_log:
        if e.get("status") == "complete":
            print(f"  {e['table']}: {e['total_rows']:,} rows, "
                  f"{e['total_chunks']} chunk(s) — COMPLETE")

    print()
    if all_match:
        print("All row counts match. Ingest successful.")
        print(f"Namespace : {namespace}")
        print(f"Silver    : {silver_base}")
    else:
        print("Row count mismatch detected.")
        print(f"  Progress log : s3a://{bucket}/{progress_key}")
        print(f"  Quarantine   : {silver_base}/quarantine/")

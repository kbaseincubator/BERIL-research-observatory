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

get_minio_username()
    Read the KBase username from the berdl-minio alias in ~/.mc/config.json.

print_preflight_plan(table_stats, namespace, mode, bucket, bronze_prefix,
                     progress_key, confirmed, user_namespace=None)
    Print upload/ingest plan. Shows user_namespace when provided. Raises if confirmed=False.

upload_files(minio_client, bucket, table_stats, bronze_prefix, file_ext)
    Upload data files to MinIO bronze. Chunked tables are skipped here —
    their chunk files are uploaded one-by-one during ingest.

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


def get_minio_username() -> str:
    """Return the KBase username from the berdl-minio alias in ~/.mc/config.json.

    The MinIO access key equals the KBase username in this deployment.
    Raises RuntimeError if the alias is missing or the config is unreadable.
    """
    mc_cfg_path = Path.home() / ".mc" / "config.json"
    if not mc_cfg_path.exists():
        raise RuntimeError(
            "[minio] ~/.mc/config.json not found.\n"
            "Run: bash scripts/configure_mc.sh --berdl-proxy"
        )
    mc_cfg = json.loads(mc_cfg_path.read_text())
    try:
        return mc_cfg["aliases"]["berdl-minio"]["accessKey"]
    except KeyError as e:
        raise RuntimeError(
            "[minio] Could not read accessKey from berdl-minio alias.\n"
            "Run: bash scripts/configure_mc.sh --berdl-proxy"
        ) from e


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


def initialize_minio():
    """Set up MinIO only (no Spark, no JupyterHub), returning minio_client.

    Checks SSH tunnels (raises if missing), auto-starts pproxy, then connects
    to MinIO. Used by ingest_preflight.py for the pre-flight plan step.
    """
    _check_ssh_tunnels()
    _start_pproxy_if_needed()
    minio_client = _build_minio_client()
    return minio_client


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
        size_gb    = size_bytes / 1e9
        wait_note  = "  (large file — may take several minutes)" if size_gb > 10 else ""
        print(f"  {f.name}: {size_gb:.1f} GB{wait_note}", end=" ", flush=True)
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


# ── Chunked file splitting ─────────────────────────────────────────────────────

_CHUNK_BLOCK_SIZE = 64 * 1024 * 1024  # 64 MB read blocks


def _chunk_file_binary(source_path: Path, chunk_target_bytes: float, file_ext: str):
    """Split a TSV/CSV file into ~chunk_target_bytes chunks at newline boundaries.

    Streams the source file sequentially in 64 MB blocks, writing directly to
    temp files so memory usage stays at ~128 MB regardless of chunk size.
    Each chunk file is a complete valid TSV/CSV including the original header row.

    Yields (chunk_index, temp_path, start_line, end_line, size_bytes) for each chunk.
      - start_line / end_line are 1-indexed data line numbers (header excluded).
      - temp_path is in /tmp; caller must delete it after use.

    The final chunk may be smaller than chunk_target_bytes.
    """
    stem = source_path.stem
    chunk_index = 0
    line_cursor = 0   # cumulative data lines completed across all previous chunks
    leftover    = b"" # bytes from the last block that belong to the next chunk
    eof         = False

    with open(source_path, "rb") as src:
        header_bytes = src.readline()  # includes trailing \n

        while not eof:
            tmp = Path(f"/tmp/{stem}_chunk_{chunk_index:03d}{file_ext}")
            bytes_data  = 0   # data bytes written (excluding header)
            n_data_lines = 0
            last_block   = b""

            with open(tmp, "wb") as dst:
                dst.write(header_bytes)

                # Seed with any bytes carried over from the previous chunk
                if leftover:
                    dst.write(leftover)
                    bytes_data   += len(leftover)
                    n_data_lines += leftover.count(b"\n")
                    last_block    = leftover
                    leftover      = b""

                while bytes_data < chunk_target_bytes:
                    block = src.read(_CHUNK_BLOCK_SIZE)
                    if not block:
                        eof = True
                        break
                    dst.write(block)
                    bytes_data   += len(block)
                    n_data_lines += block.count(b"\n")
                    last_block    = block

            if bytes_data == 0:
                # Nothing written (EOF on first iteration of a new chunk) — clean up and stop.
                tmp.unlink(missing_ok=True)
                break

            if not eof:
                # We overshot the target. Find the split point within last_block and truncate.
                # last_block is the block that pushed bytes_data over chunk_target_bytes.
                bytes_before_last = bytes_data - len(last_block)
                target_in_block   = int(chunk_target_bytes) - bytes_before_last

                # Find the last \n at or before the target position in last_block.
                split_in_block = last_block.rfind(b"\n", 0, max(1, target_in_block + 1))
                if split_in_block == -1:
                    # No \n before target — find the first \n after target.
                    split_in_block = last_block.find(b"\n", target_in_block)
                    if split_in_block == -1:
                        # No \n anywhere in last_block (extremely wide rows) — keep it all.
                        split_in_block = len(last_block) - 1

                keep     = split_in_block + 1           # bytes of last_block to keep in this chunk
                leftover = last_block[keep:]            # rest seeds the next chunk

                # Truncate the temp file: header + bytes_before_last + keep
                truncate_at = len(header_bytes) + bytes_before_last + keep
                with open(tmp, "r+b") as f:
                    f.truncate(truncate_at)

                # Fix line count: remove the lines that moved into leftover
                n_data_lines -= leftover.count(b"\n")
            elif last_block and last_block[-1:] != b"\n":
                # Final chunk and the file does not end with a trailing newline.
                # The last data line has no \n so it was not counted — add it now.
                n_data_lines += 1

            start_line = line_cursor + 1
            end_line   = line_cursor + n_data_lines
            size_bytes = tmp.stat().st_size

            yield chunk_index, tmp, start_line, end_line, size_bytes

            chunk_index += 1
            line_cursor  = end_line


# ── Pre-flight ─────────────────────────────────────────────────────────────────

def print_preflight_plan(
    table_stats: dict,
    namespace: str,
    mode: str,
    bucket: str,
    bronze_prefix: str,
    progress_key: str,
    confirmed: bool,
    user_namespace: str | None = None,
) -> None:
    """Print the upload and ingest plan.

    When user_namespace is provided (user-tenant ingest), it is displayed prominently
    so the user knows exactly where their data will land (u_username__dataset).

    Raises RuntimeError if confirmed=False so the notebook halts after display.
    Set CONFIRMED = True in the configuration cell and re-run to proceed.
    """
    W = 72
    print("=" * W)
    print("PRE-FLIGHT PLAN")
    print("=" * W)

    if user_namespace:
        print(f"\nDestination  : user-tenant space  →  namespace: {user_namespace}")
        print(  f"               (private to your account; visible only to you)")
    else:
        print(f"\nDestination  : shared tenant  →  namespace: {namespace}")

    total_gb = sum(s["size_bytes"] for s in table_stats.values()) / 1e9
    print("\nSTEP 1 -- MinIO Upload  (all tables uploaded before any ingest begins)")
    for table, s in table_stats.items():
        print(f"  {table:<45s}  {s['size_bytes'] / 1e9:>7.1f} GB")
    print(f"  {'TOTAL':<45s}  {total_gb:>7.1f} GB")

    display_ns = user_namespace or namespace
    print(f"\nSTEP 2 -- Spark Ingest into Delta  (namespace: {display_ns})")
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


def _verify_chunk_upload(
    minio_client,
    bucket: str,
    chunk_key: str,
    expected_size_bytes: int,
) -> None:
    """Confirm a chunk file exists in MinIO at the expected byte size.

    Raises RuntimeError if the object is missing or the size does not match,
    signalling that the chunk must be re-uploaded before ingest proceeds.
    """
    try:
        stat = minio_client.stat_object(bucket, chunk_key)
    except Exception as e:
        raise RuntimeError(
            f"[verify] Chunk not found in MinIO: s3a://{bucket}/{chunk_key}\n"
            f"  Error: {e}\n"
            "  The chunk must be re-uploaded."
        ) from e

    if stat.size != expected_size_bytes:
        raise RuntimeError(
            f"[verify] Size mismatch for s3a://{bucket}/{chunk_key}\n"
            f"  Expected : {expected_size_bytes:,} bytes\n"
            f"  Found    : {stat.size:,} bytes\n"
            "  The chunk must be re-uploaded."
        )
    print(f"  [verify] s3a://{bucket}/{chunk_key}  {stat.size / 1e9:.2f} GB — OK")


def _build_dataset_config(
    tenant, dataset, bucket, bronze_prefix, silver_base,
    table_stats, schemas, schema_defs, mode, file_ext, delimiter,
    user_tenant: bool = False,
    username: str | None = None,
) -> dict:
    is_parquet = file_ext == ".parquet"
    defaults = (
        {"parquet": {"inferSchema": True}}
        if is_parquet
        else {"csv": {"header": True, "delimiter": delimiter, "inferSchema": False}}
    )
    cfg = {}
    if user_tenant:
        cfg["dataset"] = f"u_{username}__{dataset}"
    else:
        cfg["dataset"] = dataset
        cfg["tenant"] = tenant
        cfg["is_tenant"] = True
    if user_tenant:
        data_plane = f"s3a://{bucket}/users-general-warehouse/{username}/"
    else:
        data_plane = f"s3a://{bucket}/tenant-general-warehouse/{tenant}/"
    cfg["paths"] = {
        "data_plane":  data_plane,
        "bronze_base": f"s3a://{bucket}/{bronze_prefix}/",
        "silver_base": silver_base,
    }
    cfg["defaults"] = defaults
    cfg["tables"] = [
        {
            "name": table, "enabled": True,
            "schema": schema_defs.get(table, []),
            "partition_by": None, "mode": mode,
            "bronze_path": f"s3a://{bucket}/{bronze_prefix}/{table}{file_ext}",
        }
        for table in table_stats
    ]
    return cfg


def upload_files(
    minio_client,
    bucket: str,
    table_stats: dict,
    bronze_prefix: str,
    file_ext: str,
) -> None:
    """Upload all data files to MinIO bronze.

    Skips any file whose size already matches the remote object, so re-running
    after a partial upload only uploads what is missing.
    """
    print("Checking / uploading data files...")
    for table, s in table_stats.items():
        if s["chunked"]:
            print(f"  {table}: chunked — will upload per-chunk during ingest, skipping here")
            continue

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

def _build_chunk_config(
    tenant: str,
    dataset: str,
    bucket: str,
    silver_base: str,
    schema_defs: dict,
    table: str,
    chunk_bronze_path: str,
    file_ext: str,
    delimiter: str,
    mode: str,
    bronze_prefix: str = "",
    user_tenant: bool = False,
    username: str | None = None,
) -> dict:
    """Build a single-table ingest config JSON pointing at one chunk file in MinIO."""
    is_parquet = file_ext == ".parquet"
    defaults = (
        {"parquet": {"inferSchema": True}}
        if is_parquet
        else {"csv": {"header": True, "delimiter": delimiter, "inferSchema": False}}
    )
    cfg: dict = {}
    if user_tenant:
        cfg["dataset"] = f"u_{username}__{dataset}"
        data_plane = f"s3a://{bucket}/users-general-warehouse/{username}/"
    else:
        cfg["dataset"] = dataset
        cfg["tenant"]    = tenant
        cfg["is_tenant"] = True
        data_plane = f"s3a://{bucket}/tenant-general-warehouse/{tenant}/"
    cfg["paths"]    = {
        "data_plane":  data_plane,
        "bronze_base": f"s3a://{bucket}/{bronze_prefix}/",
        "silver_base": silver_base,
    }
    cfg["defaults"] = defaults
    cfg["tables"]   = [{
        "name":         table,
        "enabled":      True,
        "schema":       schema_defs.get(table, []),
        "partition_by": None,
        "mode":         mode,
        "bronze_path":  chunk_bronze_path,
    }]
    return cfg


def _ingest_chunked(
    spark,
    minio_client,
    bucket: str,
    progress_key: str,
    namespace: str,
    table: str,
    stats: dict,
    schemas: dict,
    schema_defs: dict,
    silver_base: str,
    tenant: str,
    dataset: str,
    bronze_prefix: str,
    mode: str,
    file_ext: str,
    delimiter: str,
    progress_log: list,
    user_tenant: bool = False,
    username: str | None = None,
) -> int:
    """Split a large TSV/CSV file into chunks, upload each to MinIO, and ingest
    via the upstream ingest() pipeline one chunk at a time.

    Resume logic (on restart):
      uploaded + not ingested  →  verify MinIO size, re-upload if mismatch, then ingest
      uploaded + ingested      →  skip entirely
      neither                  →  upload then ingest

    Each chunk file is retained in MinIO under {bronze_prefix}/{table}/ after ingest.
    Returns (rows_done, spark) — spark may be a new session if a reconnect occurred
    mid-chunk; the caller must reassign its spark variable from the returned value.
    """
    # Build lookup tables from the progress log for this table.
    uploaded_log = {
        e["chunk"]: e
        for e in progress_log
        if e["table"] == table and e.get("status") == "uploaded"
    }
    ingested_chunks = {
        e["chunk"]
        for e in progress_log
        if e["table"] == table and e.get("status") == "ingested"
    }
    rows_done = sum(
        e["rows_written"]
        for e in progress_log
        if e["table"] == table and e.get("status") == "ingested"
    )

    chunk_target_bytes = stats["size_bytes"] / stats["n_chunks"]
    n_chunks           = stats["n_chunks"]

    for chunk_index, tmp_path, start_line, end_line, size_bytes in \
            _chunk_file_binary(stats["path"], chunk_target_bytes, file_ext):

        n_rows    = end_line - start_line + 1
        chunk_key = f"{bronze_prefix}/{table}/{table}_chunk_{chunk_index:03d}{file_ext}"
        cfg_key   = f"{bronze_prefix}/config/{table}_chunk_{chunk_index:03d}.json"
        label     = f"Chunk {chunk_index + 1}/{n_chunks}"

        # ── Already fully ingested — skip ──────────────────────────────────────
        if chunk_index in ingested_chunks:
            print(f"  {label}: already ingested — skipping")
            tmp_path.unlink(missing_ok=True)
            continue

        # ── Upload (or re-upload if verify fails) ──────────────────────────────
        already_uploaded = chunk_index in uploaded_log
        if already_uploaded:
            logged_size = uploaded_log[chunk_index]["size_bytes"]
            print(f"  {label}: already uploaded — verifying...")
            try:
                _verify_chunk_upload(minio_client, bucket, chunk_key, logged_size)
            except RuntimeError as exc:
                print(f"  {label}: verification failed — re-uploading  ({exc})")
                already_uploaded = False

        if not already_uploaded:
            print(f"  {label}: uploading {size_bytes / 1e9:.2f} GB "
                  f"→ s3a://{bucket}/{chunk_key} ...", end=" ", flush=True)
            minio_client.fput_object(bucket, chunk_key, str(tmp_path))
            print("done")
            _append_progress(minio_client, bucket, progress_key, {
                "table":      table,
                "chunk":      chunk_index,
                "status":     "uploaded",
                "minio_path": f"s3a://{bucket}/{chunk_key}",
                "size_bytes": size_bytes,
                "timestamp":  datetime.now(timezone.utc).isoformat(),
            })
        else:
            # Verify the already-uploaded size matches the local chunk we just wrote.
            # (Handles the edge case where the file was re-split differently on restart.)
            logged_size = uploaded_log[chunk_index]["size_bytes"]
            if logged_size != size_bytes:
                print(f"  {label}: WARNING — logged size {logged_size:,} B != "
                      f"local size {size_bytes:,} B; re-uploading to be safe")
                minio_client.fput_object(bucket, chunk_key, str(tmp_path))
                _append_progress(minio_client, bucket, progress_key, {
                    "table":      table,
                    "chunk":      chunk_index,
                    "status":     "uploaded",
                    "minio_path": f"s3a://{bucket}/{chunk_key}",
                    "size_bytes": size_bytes,
                    "timestamp":  datetime.now(timezone.utc).isoformat(),
                })

        tmp_path.unlink(missing_ok=True)

        # ── Ingest via upstream pipeline ───────────────────────────────────────
        chunk_mode = mode if chunk_index == 0 else "append"
        chunk_cfg  = _build_chunk_config(
            tenant, dataset, bucket, silver_base, schema_defs,
            table, f"s3a://{bucket}/{chunk_key}", file_ext, delimiter, chunk_mode,
            bronze_prefix=bronze_prefix,
            user_tenant=user_tenant, username=username,
        )
        cfg_bytes = json.dumps(chunk_cfg, indent=2).encode()
        minio_client.put_object(
            bucket, cfg_key, io.BytesIO(cfg_bytes), len(cfg_bytes),
            content_type="application/json",
        )

        print(f"  {label}: ingesting lines {start_line:,}–{end_line:,} "
              f"({n_rows:,} rows, mode={chunk_mode})...")

        if not _check_spark_health(spark):
            print(f"  {label}: [spark] session unhealthy — reconnecting...")
            spark = reconnect_spark(spark)

        result = _lakehouse_ingest(
            f"s3a://{bucket}/{cfg_key}",
            spark=spark, minio_client=minio_client,
        )
        if result and not result.get("success", True):
            raise RuntimeError(
                f"ingest() returned failure for {table} chunk {chunk_index}: {result}"
            )

        rows_done += n_rows
        _append_progress(minio_client, bucket, progress_key, {
            "table":           table,
            "chunk":           chunk_index,
            "status":          "ingested",
            "start_line":      start_line,
            "end_line":        end_line,
            "rows_written":    n_rows,
            "rows_cumulative": rows_done,
            "timestamp":       datetime.now(timezone.utc).isoformat(),
        })
        print(f"  {label}: complete — {rows_done:,} cumulative rows")

        # Retain chunk 0 config as a record of schema and ingest settings.
        # Clean up all other per-chunk config files (pipeline artifacts).
        # Chunk data files are retained at {bronze_prefix}/{table}/ for records.
        if chunk_index > 0:
            try:
                minio_client.remove_object(bucket, cfg_key)
            except Exception as e:
                print(f"  {label}: WARNING — could not delete s3a://{bucket}/{cfg_key}: {e}")

    return rows_done, spark


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
    config_key: str,
    user_tenant: bool = False,
    username: str | None = None,
):
    """Ingest all tables into Delta silver.

    Non-chunked tables are batched into a single _lakehouse_ingest() call using a
    merged config uploaded to config_key in MinIO.

    Chunked tables are split into ~chunk_target_bytes files locally, uploaded to
    MinIO one at a time, and ingested via _lakehouse_ingest() per chunk so no large
    payload ever crosses the gRPC connection. Chunk files are deleted from MinIO
    after each successful ingest.

    Loads the progress log first — completed tables and chunks are skipped
    automatically so an interrupted ingest resumes from where it left off.

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

    # Split pending tables into non-chunked (pipeline) and chunked (streaming)
    pending_non_chunked = {
        t: s for t, s in table_stats.items()
        if not s["chunked"] and t not in complete_tables
    }
    pending_chunked = {
        t: s for t, s in table_stats.items()
        if s["chunked"] and t not in complete_tables
    }

    already_done = [t for t in table_stats if t in complete_tables]
    if already_done:
        print(f"Skipping already complete: {', '.join(already_done)}\n")

    # ── Non-chunked: single _lakehouse_ingest() call with merged config ──────────
    if pending_non_chunked:
        if not _check_spark_health(spark):
            print("[spark] Session unhealthy — reconnecting...")
            spark = reconnect_spark(spark)

        print("=" * 60)
        print(f"Ingesting {len(pending_non_chunked)} non-chunked table(s) via pipeline:")
        for t, s in pending_non_chunked.items():
            print(f"  {t}: {s['data_lines']:,} rows | {s['size_bytes'] / 1e9:.1f} GB")

        cfg = _build_dataset_config(
            tenant, dataset, bucket, bronze_prefix, silver_base,
            pending_non_chunked, schemas, schema_defs, mode, file_ext, delimiter,
            user_tenant=user_tenant, username=username,
        )
        cfg_bytes = json.dumps(cfg, indent=2).encode()
        minio_client.put_object(
            bucket, config_key, io.BytesIO(cfg_bytes), len(cfg_bytes),
            content_type="application/json",
        )
        print(f"Config -> s3a://{bucket}/{config_key}")

        result = _lakehouse_ingest(
            f"s3a://{bucket}/{config_key}",
            spark=spark, minio_client=minio_client,
        )
        if result and not result.get("success", True):
            raise RuntimeError(f"ingest() returned failure: {result}")

        now = datetime.now(timezone.utc).isoformat()
        for tbl_result in (result or {}).get("tables", []):
            table     = tbl_result["name"]
            rows_done = tbl_result.get("rows_written", table_stats[table]["data_lines"])
            _append_progress(minio_client, bucket, progress_key, {
                "table": table, "chunk": 0,
                "start_line": 1, "end_line": rows_done,
                "rows_written": rows_done, "rows_cumulative": rows_done,
                "status": "ingested", "timestamp": now,
            })
            _append_progress(minio_client, bucket, progress_key, {
                "table": table, "status": "complete",
                "total_rows": rows_done, "total_chunks": 1,
                "timestamp": now,
            })
            complete_tables.add(table)
            print(f"  {table}: {rows_done:,} rows — COMPLETE")

    # ── Chunked: split locally, upload per-chunk, ingest via upstream pipeline ───
    for table, stats in pending_chunked.items():
        print("=" * 60)
        print(f"Ingesting (chunked): {table}")
        print(f"  {stats['data_lines']:,} rows | {stats['n_chunks']} chunk(s) "
              f"| {stats['size_bytes'] / 1e9:.1f} GB")

        rows_done, spark = _ingest_chunked(
            spark=spark,
            minio_client=minio_client,
            bucket=bucket,
            progress_key=progress_key,
            namespace=namespace,
            table=table,
            stats=stats,
            schemas=schemas,
            schema_defs=schema_defs,
            silver_base=silver_base,
            tenant=tenant,
            dataset=dataset,
            bronze_prefix=bronze_prefix,
            mode=mode,
            file_ext=file_ext,
            delimiter=delimiter,
            progress_log=progress_log,
            user_tenant=user_tenant,
            username=username,
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

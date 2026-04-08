#!/usr/bin/env python3
"""Pre-flight plan for BERDL ingest.

Prints upload sizes and chunk counts for every table without starting Spark
or JupyterHub. Run this before executing the ingest notebook to review the
plan and confirm before any data is transferred.

Usage:
    python scripts/ingest_preflight.py \
        --data-dir /path/to/data \
        --tenant kescience \
        --dataset my_dataset \
        [--mode overwrite|append] \
        [--chunk-target-gb 20] \
        [--no-chunked]
"""

import argparse
import os
import sys
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env from the repo root into os.environ (no-op if absent)."""
    for search in [Path.cwd()] + list(Path.cwd().parents):
        env_path = search / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
            return


def _bootstrap_syspath() -> None:
    """Add the repo's scripts/ directory to sys.path."""
    for search in [Path.cwd()] + list(Path.cwd().parents):
        if (search / "scripts" / "ingest_lib.py").exists():
            sys.path.insert(0, str(search / "scripts"))
            return
    print("ERROR: Could not find scripts/ingest_lib.py", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the BERDL ingest pre-flight plan (no Spark required)."
    )
    parser.add_argument("--data-dir", required=True, type=Path,
                        help="Directory containing source data files")
    parser.add_argument("--tenant", required=True,
                        help="Lakehouse tenant name (e.g. kescience)")
    parser.add_argument("--dataset", required=True,
                        help="Dataset name (e.g. my_dataset)")
    parser.add_argument("--mode", default="overwrite",
                        choices=["overwrite", "append"],
                        help="Ingest mode (default: overwrite)")
    parser.add_argument("--chunk-target-gb", type=float, default=20.0,
                        help="Tables above this GB are ingested in chunks (default: 20)")
    parser.add_argument("--no-chunked", action="store_true",
                        help="Force single-batch ingest regardless of table size")
    parser.add_argument("--user-tenant", action="store_true",
                        help="Store in user-tenant space (u_username__dataset); "
                             "resolves username from ~/.mc/config.json")
    args = parser.parse_args()

    _load_dotenv()
    _bootstrap_syspath()

    from ingest_lib import (
        initialize_minio,
        detect_source_files,
        export_sqlite,
        parse_sql_schema,
        build_table_stats,
        print_preflight_plan,
        get_minio_username,
    )

    BUCKET         = "cdm-lake"
    DATASET        = args.dataset
    CHUNKED_INGEST = not args.no_chunked

    minio_client = initialize_minio()

    # Resolve paths — user-tenant uses different warehouse roots than shared tenants
    user_namespace = None
    if args.user_tenant:
        username      = get_minio_username()
        user_namespace = f"u_{username}__{DATASET}"
        NAMESPACE     = user_namespace
        BRONZE_PREFIX = f"users-general-warehouse/{username}/data/{DATASET}"
    else:
        NAMESPACE     = f"{args.tenant}_{DATASET}"
        BRONZE_PREFIX = f"tenant-general-warehouse/{args.tenant}/datasets/{DATASET}"

    PROGRESS_KEY = f"{BRONZE_PREFIX}/_ingest_progress.jsonl"

    SOURCE_MODE, SOURCE_DB, SQL_SCHEMA, data_files, FILE_EXT, DELIMITER = \
        detect_source_files(args.data_dir)

    if SOURCE_MODE == "parquet":
        SCHEMAS, SCHEMA_DEFS = {}, {}
    elif SQL_SCHEMA:
        SCHEMAS, SCHEMA_DEFS = parse_sql_schema(SQL_SCHEMA)
    else:
        SCHEMAS, SCHEMA_DEFS = {}, {}

    if SOURCE_MODE == "sqlite":
        data_files = export_sqlite(SOURCE_DB, DATASET, SCHEMAS)

    TABLE_STATS = build_table_stats(
        data_files, SCHEMAS, args.chunk_target_gb, CHUNKED_INGEST, DELIMITER
    )

    print_preflight_plan(
        table_stats=TABLE_STATS,
        namespace=NAMESPACE,
        mode=args.mode,
        bucket=BUCKET,
        bronze_prefix=BRONZE_PREFIX,
        progress_key=PROGRESS_KEY,
        confirmed=True,  # display only — confirmation is handled by the caller
        user_namespace=user_namespace,
    )


if __name__ == "__main__":
    main()

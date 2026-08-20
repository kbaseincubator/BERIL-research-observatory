#!/usr/bin/env python3
"""Plan or execute a non-interactive Parquet ingest into BERDL staging."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:
    from scripts.ingest_lib import (
        build_table_stats,
        detect_source_files,
        initialize,
        print_preflight_plan,
        run_ingest,
        upload_files,
        verify_ingest,
    )
else:
    from ingest_lib import (
        build_table_stats,
        detect_source_files,
        initialize,
        print_preflight_plan,
        run_ingest,
        upload_files,
        verify_ingest,
    )

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_OBJECT_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_BUCKET = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
_OTHER_SOURCE_SUFFIXES = {".csv", ".db", ".sqlite", ".sqlite3", ".tsv"}


class ConfigurationError(ValueError):
    """Raised before any external operation when an ingest target is unsafe."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_identifier(value: str, label: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ConfigurationError(f"{label} must be a safe SQL identifier")
    return value


def _validate_object_key(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not value or value.endswith("/") or str(path) != value:
        raise ConfigurationError(f"{label} must be a relative object key")
    if any(part in {"", ".", ".."} or not _OBJECT_SEGMENT.fullmatch(part)
           for part in path.parts):
        raise ConfigurationError(f"{label} contains an unsafe path segment")
    return value


def _validate_inputs(args: argparse.Namespace) -> tuple[Path, str]:
    data_dir = args.data_dir.resolve()
    if not data_dir.is_dir() or args.data_dir.is_symlink():
        raise ConfigurationError("data directory must be an ordinary directory")

    tenant = _validate_identifier(args.tenant, "tenant")
    dataset = _validate_identifier(args.dataset, "dataset")
    if not _BUCKET.fullmatch(args.bucket):
        raise ConfigurationError("bucket must be a safe S3 bucket name")
    expected_namespace = f"{tenant}.{dataset}"
    if args.staging_namespace != expected_namespace:
        raise ConfigurationError(
            "staging namespace must exactly match <tenant>.<dataset>"
        )

    _validate_object_key(args.bronze_prefix, "bronze prefix")
    _validate_object_key(args.progress_key, "progress key")
    _validate_object_key(args.config_key, "config key")
    prefix = f"{args.bronze_prefix.rstrip('/')}/"
    if not args.progress_key.startswith(prefix) or not args.config_key.startswith(prefix):
        raise ConfigurationError(
            "progress and config keys must be children of the bronze prefix"
        )

    files = [path for path in data_dir.iterdir() if path.is_file()]
    other_sources = sorted(
        path.name for path in files if path.suffix.lower() in _OTHER_SOURCE_SUFFIXES
    )
    if other_sources:
        raise ConfigurationError(
            "Parquet staging does not accept mixed tabular source formats: "
            + ", ".join(other_sources)
        )
    parquet = sorted(path for path in files if path.suffix == ".parquet")
    if not parquet:
        raise ConfigurationError(
            "data directory contains no files with the lowercase .parquet extension"
        )
    if any(path.is_symlink() for path in parquet):
        raise ConfigurationError("Parquet inputs must be ordinary files, not symlinks")
    if len({path.stem for path in parquet}) != len(parquet):
        raise ConfigurationError("Parquet table names must be unique")
    for path in parquet:
        _validate_identifier(path.stem, f"table name {path.stem!r}")
    return data_dir, expected_namespace


def _write_outcome(path: Path, outcome: dict[str, Any]) -> None:
    if path.exists():
        raise ConfigurationError(f"outcome path already exists: {path}")
    if not path.parent.is_dir():
        raise ConfigurationError(f"outcome parent directory does not exist: {path.parent}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(outcome, stream, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_outcome_path(path: Path) -> None:
    if path.exists():
        raise ConfigurationError(f"outcome path already exists: {path}")
    if not path.parent.is_dir():
        raise ConfigurationError(f"outcome parent directory does not exist: {path.parent}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plan a Parquet-only BERDL staging ingest. Add --execute-staging to "
            "upload, ingest, and independently verify source row counts."
        )
    )
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--staging-namespace", required=True)
    parser.add_argument("--mode", choices=("overwrite", "append"), default="overwrite")
    parser.add_argument("--bucket", default="cdm-lake")
    parser.add_argument("--bronze-prefix", required=True)
    parser.add_argument("--progress-key", required=True)
    parser.add_argument("--config-key", required=True)
    parser.add_argument("--chunk-target-gb", type=float, default=20.0)
    parser.add_argument("--outcome", type=Path)
    parser.add_argument(
        "--execute-staging",
        action="store_true",
        help="perform staging mutations; canonical promotion is never performed",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    data_dir, namespace = _validate_inputs(args)
    if args.chunk_target_gb <= 0:
        raise ConfigurationError("chunk target must be positive")
    if args.execute_staging and args.outcome is None:
        raise ConfigurationError("--outcome is required with --execute-staging")
    if args.outcome is not None:
        _validate_outcome_path(args.outcome)

    source_mode, _source_db, _sql_schema, data_files, file_ext, delimiter = (
        detect_source_files(data_dir)
    )
    if source_mode != "parquet":
        raise ConfigurationError("only Parquet staging is supported")
    schemas: dict = {}
    schema_defs: dict = {}
    table_stats = build_table_stats(
        data_files, schemas, args.chunk_target_gb, True, delimiter
    )
    print_preflight_plan(
        table_stats,
        namespace,
        args.mode,
        args.bucket,
        args.bronze_prefix,
        args.progress_key,
        confirmed=args.execute_staging,
        plan_only=not args.execute_staging,
    )
    if not args.execute_staging:
        return 0

    started_at = _utc_now()
    phase = "initialize"
    try:
        spark, minio_client = initialize()
        phase = "upload"
        source_sha256 = upload_files(
            minio_client,
            args.bucket,
            table_stats,
            args.bronze_prefix,
            file_ext,
            force=True,
            verify_sha256=True,
        )
        phase = "ingest"
        spark = run_ingest(
            spark,
            minio_client,
            table_stats,
            schemas,
            schema_defs,
            namespace,
            args.tenant,
            args.dataset,
            args.bucket,
            args.bronze_prefix,
            args.mode,
            file_ext,
            delimiter,
            args.progress_key,
            args.config_key,
        )
        phase = "verify"
        verification = verify_ingest(
            spark,
            namespace,
            table_stats,
            minio_client,
            args.bucket,
            args.progress_key,
            bronze_prefix=args.bronze_prefix,
        )
        for table in verification["tables"]:
            table["source_sha256"] = source_sha256[table["table"]]
        outcome = {
            "schema_version": "1.0.0",
            "status": "verified" if verification["verified"] else "failed",
            "started_at": started_at,
            "finished_at": _utc_now(),
            "destination": {
                "bucket": args.bucket,
                "bronze_prefix": args.bronze_prefix,
                "namespace": namespace,
                "mode": args.mode,
            },
            "verification": verification,
        }
        _write_outcome(args.outcome, outcome)
        return 0 if verification["verified"] else 1
    except Exception as error:  # noqa: BLE001 - sanitize every infrastructure failure
        outcome = {
            "schema_version": "1.0.0",
            "status": "failed",
            "started_at": started_at,
            "finished_at": _utc_now(),
            "failed_phase": phase,
            "error_type": type(error).__name__,
            "destination": {
                "bucket": args.bucket,
                "bronze_prefix": args.bronze_prefix,
                "namespace": namespace,
                "mode": args.mode,
            },
        }
        _write_outcome(args.outcome, outcome)
        print(f"ERROR: staging failed during {phase} ({type(error).__name__})", file=sys.stderr)
        return 1


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    try:
        raise SystemExit(run(args))
    except ConfigurationError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

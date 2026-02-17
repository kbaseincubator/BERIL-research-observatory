#!/usr/bin/env python3
"""Execute SQL on BERDL Spark and export the result to MinIO."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SQL and export result to object storage.")
    parser.add_argument("--query", help="SQL query text.")
    parser.add_argument("--query-file", help="Path to SQL file.")
    parser.add_argument("--path", required=True, help="Output path, usually s3a://cdm-lake/...")
    parser.add_argument(
        "--format",
        default="parquet",
        choices=["parquet", "delta", "json", "csv"],
        help="Output format.",
    )
    parser.add_argument(
        "--mode",
        default="overwrite",
        choices=["overwrite", "append", "ignore", "error", "errorifexists"],
        help="Save mode.",
    )
    parser.add_argument(
        "--partition-by",
        default="",
        help="Comma-separated partition columns.",
    )
    parser.add_argument("--coalesce", type=int, help="Optional coalesce target partitions.")
    parser.add_argument("--count", action="store_true", help="Compute row count before export.")
    parser.add_argument("--manifest", help="Optional local path for export manifest JSON.")
    parser.add_argument("--app-name", default="berdl-local-export", help="Spark app name.")
    parser.add_argument(
        "--host-template",
        help="Spark Connect host template. Defaults to BERDL_SPARK_HOST_TEMPLATE or spark.berdl.kbase.us.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Spark Connect port. Defaults to BERDL_SPARK_PORT or 443.",
    )
    parser.add_argument(
        "--no-ssl",
        action="store_true",
        help="Disable SSL for Spark Connect (for local/port-forward scenarios).",
    )
    parser.add_argument("--grpc-proxy", help="Set grpc_proxy for Spark Connect traffic.")
    parser.add_argument(
        "--https-proxy",
        help="Set https_proxy for HTTP clients (including token validation).",
    )
    parser.add_argument("--no-proxy", help="Set no_proxy value.")
    parser.add_argument(
        "--berdl-proxy",
        action="store_true",
        help="Use BERDL proxy defaults: metrics.berdl.kbase.us + grpc/https proxy http://127.0.0.1:8123.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional dotenv file to load before reading environment variables.",
    )
    parser.add_argument(
        "--kbase-token",
        help="Optional explicit token. Defaults to KBASE_AUTH_TOKEN env var.",
    )
    return parser.parse_args()


def resolve_query(args: argparse.Namespace) -> str:
    if args.query and args.query_file:
        raise ValueError("Use only one of --query or --query-file.")
    if args.query_file:
        return Path(args.query_file).read_text()
    if args.query:
        return args.query
    raise ValueError("Provide --query or --query-file.")


def apply_proxy_settings(args: argparse.Namespace) -> None:
    if args.berdl_proxy:
        if args.host_template is None:
            args.host_template = "metrics.berdl.kbase.us"
        if args.grpc_proxy is None:
            args.grpc_proxy = "http://127.0.0.1:8123"
        if args.https_proxy is None:
            args.https_proxy = "http://127.0.0.1:8123"
        if args.no_proxy is None:
            args.no_proxy = "localhost,127.0.0.1"

    if args.grpc_proxy:
        os.environ["grpc_proxy"] = args.grpc_proxy
    if args.https_proxy:
        os.environ["https_proxy"] = args.https_proxy
    if args.no_proxy:
        os.environ["no_proxy"] = args.no_proxy


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    apply_proxy_settings(args)

    token = args.kbase_token or os.getenv("KBASE_AUTH_TOKEN")
    if not token:
        print("KBASE_AUTH_TOKEN is required.", file=sys.stderr)
        return 2

    host_template = args.host_template or os.getenv(
        "BERDL_SPARK_HOST_TEMPLATE", "spark.berdl.kbase.us"
    )
    port = args.port or int(os.getenv("BERDL_SPARK_PORT", "443"))
    use_ssl = not args.no_ssl

    try:
        query = resolve_query(args).strip().rstrip(";")
    except Exception as exc:
        print(f"Failed to load query: {exc}", file=sys.stderr)
        return 2

    if not query:
        print("Query cannot be empty.", file=sys.stderr)
        return 2

    try:
        from spark_connect_remote import create_spark_session
    except Exception as exc:
        print(f"Cannot import spark_connect_remote: {exc}", file=sys.stderr)
        return 2

    try:
        spark = create_spark_session(
            host_template=host_template,
            port=port,
            use_ssl=use_ssl,
            kbase_token=token,
            app_name=args.app_name,
        )
        df = spark.sql(query)
        if args.coalesce is not None:
            df = df.coalesce(args.coalesce)

        row_count = None
        if args.count:
            row_count = df.count()

        writer = df.write.mode(args.mode).format(args.format)
        partition_cols = [c.strip() for c in args.partition_by.split(",") if c.strip()]
        if partition_cols:
            writer = writer.partitionBy(*partition_cols)
        if args.format == "csv":
            writer = writer.option("header", "true")

        writer.save(args.path)
    except Exception as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1

    manifest: dict[str, Any] = {
        "query": query,
        "host_template": host_template,
        "port": port,
        "use_ssl": use_ssl,
        "grpc_proxy": os.getenv("grpc_proxy"),
        "https_proxy": os.getenv("https_proxy"),
        "no_proxy": os.getenv("no_proxy"),
        "output_path": args.path,
        "format": args.format,
        "mode": args.mode,
        "partition_by": partition_cols,
        "row_count": row_count,
    }

    if args.manifest:
        manifest_path = Path(args.manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
        print(f"Wrote manifest to {manifest_path}")

    print(json.dumps(manifest, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

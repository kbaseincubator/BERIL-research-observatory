#!/usr/bin/env python3
"""
Ingest AlphaFold metadata into Delta Lake via Spark Connect (remote).

Reads TSVs from MinIO bronze storage and writes Delta Lake tables to
kescience_alphafold, using Spark Connect through the SSH tunnel proxy.

Prerequisites:
  - SSH SOCKS tunnels on ports 1337, 1338
  - pproxy on port 8123
  - Active JupyterHub Spark session
  - TSVs already uploaded to MinIO

Usage:
  /tmp/berdl_py313/bin/python3 scripts/remote_ingest_alphafold.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

# Set proxy for Spark Connect
os.environ["https_proxy"] = "http://127.0.0.1:8123"
os.environ["http_proxy"] = "http://127.0.0.1:8123"
os.environ["no_proxy"] = "localhost,127.0.0.1"

from pyspark.sql import SparkSession

BRONZE_BASE = "s3a://cdm-lake/tenant-general-warehouse/kescience/datasets/alphafold"
DATABASE = "kescience_alphafold"

TABLES = [
    {
        "name": "alphafold_entries",
        "file": f"{BRONZE_BASE}/alphafold_entries.tsv",
        "schema": (
            "uniprot_accession STRING, first_residue INT, last_residue INT, "
            "alphafold_id STRING, model_version INT"
        ),
    },
    {
        "name": "alphafold_msa_depths",
        "file": f"{BRONZE_BASE}/alphafold_msa_depths.tsv",
        "schema": "uniprot_accession STRING, msa_depth INT",
    },
]


def main():
    auth_token = os.getenv("KBASE_AUTH_TOKEN")
    if not auth_token:
        print("ERROR: KBASE_AUTH_TOKEN not found in .env")
        sys.exit(1)

    print("Connecting to Spark Connect at hub.berdl.kbase.us:443...")
    spark = (
        SparkSession.builder.remote("sc://hub.berdl.kbase.us:443")
        .config("spark.connect.grpc.http.proxy", "http://127.0.0.1:8123")
        .config("spark.connect.grpc.channelBuilder", "netty")
        .getOrCreate()
    )
    print(f"Spark session ready (v{spark.version})")

    # Create database if not exists
    print(f"\nCreating database {DATABASE}...")
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")

    for table_info in TABLES:
        name = table_info["name"]
        full_name = f"{DATABASE}.{name}"
        print(f"\n{'=' * 60}")
        print(f"Ingesting {full_name}")
        print(f"{'=' * 60}")

        # Read TSV from MinIO
        print(f"  Reading from {table_info['file']}...")
        df = (
            spark.read.option("header", "true")
            .option("delimiter", "\t")
            .option("inferSchema", "false")
            .schema(table_info["schema"])
            .csv(table_info["file"])
        )

        # Show sample
        print(f"  Schema:")
        df.printSchema()
        print(f"  Sample (5 rows):")
        df.show(5, truncate=False)

        # Count rows
        row_count = df.count()
        print(f"  Row count: {row_count:,}")

        # Write as Delta table
        print(f"  Writing Delta table {full_name}...")
        df.write.format("delta").mode("overwrite").saveAsTable(full_name)
        print(f"  Done: {full_name}")

    # Verify
    print(f"\n{'=' * 60}")
    print(f"VERIFICATION")
    print(f"{'=' * 60}")
    for table_info in TABLES:
        full_name = f"{DATABASE}.{table_info['name']}"
        count = spark.sql(f"SELECT COUNT(*) as n FROM {full_name}").collect()[0].n
        print(f"  {full_name}: {count:,} rows")

    spark.stop()
    print(f"\nIngestion complete.")


if __name__ == "__main__":
    main()

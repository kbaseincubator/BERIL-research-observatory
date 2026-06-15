#!/usr/bin/env python3
"""
Ingest AlphaFold metadata into the Iceberg lakehouse via Spark Connect (remote).

Reads TSVs from MinIO bronze storage and writes Iceberg tables to
kescience.alphafold using Spark Connect through the SSH tunnel proxy.

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

project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

os.environ["https_proxy"] = "http://127.0.0.1:8123"
os.environ["http_proxy"] = "http://127.0.0.1:8123"
os.environ["no_proxy"] = "localhost,127.0.0.1"

from spark_connect_remote import create_spark_session

BRONZE_BASE = "s3a://cdm-lake/tenant-general-warehouse/kescience/datasets/alphafold"
TENANT = "kescience"
NAMESPACE = "alphafold"

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

    print("Connecting to Spark Connect...")
    spark = create_spark_session(
        kbase_token=auth_token,
        app_name="ingest-alphafold",
    )
    print(f"Spark session ready (v{spark.version})")

    catalog_ns = f"{TENANT}.{NAMESPACE}"
    print(f"\nCreating namespace {catalog_ns}...")
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {catalog_ns}")

    for table_info in TABLES:
        name = table_info["name"]
        full_name = f"{catalog_ns}.{name}"
        print(f"\n{'=' * 60}")
        print(f"Ingesting {full_name}")
        print(f"{'=' * 60}")

        print(f"  Reading from {table_info['file']}...")
        df = (
            spark.read.option("header", "true")
            .option("delimiter", "\t")
            .option("inferSchema", "false")
            .schema(table_info["schema"])
            .csv(table_info["file"])
        )

        print("  Schema:")
        df.printSchema()
        print("  Sample (5 rows):")
        df.show(5, truncate=False)

        row_count = df.count()
        print(f"  Row count: {row_count:,}")

        print(f"  Writing Iceberg table {full_name}...")
        df.writeTo(full_name).createOrReplace()
        print(f"  Done: {full_name}")

    print(f"\n{'=' * 60}")
    print("VERIFICATION")
    print(f"{'=' * 60}")
    for table_info in TABLES:
        full_name = f"{catalog_ns}.{table_info['name']}"
        count = spark.sql(f"SELECT COUNT(*) as n FROM {full_name}").collect()[0].n
        print(f"  {full_name}: {count:,} rows")

    spark.stop()
    print("\nIngestion complete.")


if __name__ == "__main__":
    main()

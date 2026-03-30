#!/usr/bin/env python3
"""
Upload transformed InterProScan tables to MinIO and ingest into BERDL.

Adds 3 tables to the existing kbase_ke_pangenome database:
  - interproscan_domains (~833M rows)
  - interproscan_go (deduplicated GO assignments)
  - interproscan_pathways (deduplicated pathway assignments)

Prerequisites:
  1. Run 09_transform_results.py to produce the 3 gzipped TSVs
  2. Run from JupyterHub (needs berdl_notebook_utils, data_lakehouse_ingest)

Usage:
  # Upload files to MinIO, then ingest
  python 10_ingest_interproscan_results.py

  # Skip upload (files already on MinIO)
  python 10_ingest_interproscan_results.py --skip-upload

  # Ingest a single table
  python 10_ingest_interproscan_results.py --table interproscan_go
"""

import argparse
import os
import sys

from berdl_notebook_utils.berdl_settings import get_settings
from berdl_notebook_utils.minio_governance import get_minio_credentials
from data_lakehouse_ingest import ingest
from minio import Minio

BUCKET = "cdm-lake"
MINIO_PREFIX = "users-general-warehouse/psdehal/data/interproscan_results"

TABLE_FILES = {
    "interproscan_domains": "interproscan_domains.tsv.gz",
    "interproscan_go": "interproscan_go.tsv.gz",
    "interproscan_pathways": "interproscan_pathways.tsv.gz",
}

INGEST_CONFIG = {
    "tenant": "kbase",
    "dataset": "ke_pangenome",
    "paths": {
        "bronze_base": f"s3a://{BUCKET}/{MINIO_PREFIX}/",
        "silver_base": "s3a://cdm-lake/tenant-sql-warehouse/kbase/kbase_ke_pangenome.db",
    },
    "defaults": {"tsv": {"header": True, "delimiter": "\t", "inferSchema": False}},
    "tables": [
        {
            "name": "interproscan_domains",
            "format": "tsv",
            "bronze_path": f"s3a://{BUCKET}/{MINIO_PREFIX}/interproscan_domains.tsv.gz",
            "schema_sql": (
                "gene_cluster_id STRING, md5 STRING, seq_len INT, analysis STRING, "
                "signature_acc STRING, signature_desc STRING, start INT, stop INT, "
                "score STRING, ipr_acc STRING, ipr_desc STRING"
            ),
        },
        {
            "name": "interproscan_go",
            "format": "tsv",
            "bronze_path": f"s3a://{BUCKET}/{MINIO_PREFIX}/interproscan_go.tsv.gz",
            "schema_sql": (
                "gene_cluster_id STRING, go_id STRING, go_source STRING, "
                "n_supporting_analyses INT"
            ),
        },
        {
            "name": "interproscan_pathways",
            "format": "tsv",
            "bronze_path": f"s3a://{BUCKET}/{MINIO_PREFIX}/interproscan_pathways.tsv.gz",
            "schema_sql": (
                "gene_cluster_id STRING, pathway_db STRING, pathway_id STRING, "
                "n_supporting_analyses INT"
            ),
        },
    ],
}


def get_minio_client():
    creds = get_minio_credentials()
    settings = get_settings()
    endpoint = settings.MINIO_ENDPOINT_URL.replace("https://", "").replace("http://", "")
    client = Minio(
        endpoint=endpoint,
        access_key=creds.access_key,
        secret_key=creds.secret_key,
        secure=True,
    )
    print(f"MinIO client ready (user: {creds.username})")
    return client


def upload_files(minio_client, local_dir, tables=None):
    """Upload gzipped TSV files to MinIO."""
    for table_name, filename in TABLE_FILES.items():
        if tables and table_name not in tables:
            continue
        local_path = os.path.join(local_dir, filename)
        if not os.path.exists(local_path):
            print(f"  SKIP  {filename} (not found at {local_path})")
            continue
        size = os.path.getsize(local_path)
        object_name = f"{MINIO_PREFIX}/{filename}"
        print(f"  Uploading {filename} ({size / 1e9:.1f} GB) → {object_name}")
        minio_client.fput_object(
            BUCKET, object_name, local_path,
            content_type="application/gzip",
        )
        print(f"    Done.")


def verify_files(minio_client, tables=None):
    """Verify all source files exist on MinIO."""
    objs = {
        o.object_name.split("/")[-1]: o.size
        for o in minio_client.list_objects(BUCKET, prefix=MINIO_PREFIX, recursive=True)
    }
    all_ok = True
    for table_name, filename in TABLE_FILES.items():
        if tables and table_name not in tables:
            continue
        if filename in objs:
            print(f"  OK  {filename:45s} {objs[filename]:>15,} bytes")
        else:
            print(f"  MISSING  {filename}")
            all_ok = False
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Upload and ingest InterProScan results into BERDL")
    parser.add_argument("--local-dir", default="/pscratch/sd/p/psdehal/interproscan/tables",
                        help="Directory with gzipped TSV files")
    parser.add_argument("--skip-upload", action="store_true",
                        help="Skip upload, files already on MinIO")
    parser.add_argument("--table", choices=list(TABLE_FILES.keys()),
                        help="Ingest only this table")
    args = parser.parse_args()

    tables = [args.table] if args.table else None

    minio_client = get_minio_client()

    if not args.skip_upload:
        print(f"\nUploading files from {args.local_dir}:")
        upload_files(minio_client, args.local_dir, tables)

    print(f"\nVerifying source files on MinIO:")
    if not verify_files(minio_client, tables):
        print("\nERROR: Missing source files. Aborting.")
        sys.exit(1)

    # Filter config to requested tables
    config = dict(INGEST_CONFIG)
    if tables:
        config["tables"] = [t for t in config["tables"] if t["name"] in tables]

    n_tables = len(config["tables"])
    table_names = ", ".join(t["name"] for t in config["tables"])
    print(f"\nRunning data_lakehouse_ingest ({n_tables} tables: {table_names})...")
    print("NOTE: interproscan_domains is ~833M rows — this will take a while.\n")
    report = ingest(config, minio_client=minio_client)

    print(f"\n{'=' * 60}")
    print(f"INGESTION REPORT")
    print(f"{'=' * 60}")
    print(f"Success: {report['success']}")
    print(f"Duration: {report.get('duration_sec', 'N/A')}")
    for t in report.get("tables", []):
        print(
            f"  {t['name']:30s} {str(t.get('rows_written', '?')):>14s} rows  "
            f"[{t.get('status', '?')}]"
        )
    if report.get("errors"):
        for e in report["errors"]:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    main()

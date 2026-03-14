#!/usr/bin/env python3
"""
Upload prepared InterPro files to MinIO and ingest into BERDL as kescience_interpro.

Creates three Delta Lake tables:
  - kescience_interpro.protein2ipr  (~1.5B rows, all UniProt → InterPro mappings)
  - kescience_interpro.entry         (~50K rows, InterPro entry metadata)
  - kescience_interpro.go_mapping    (~30K rows, InterPro → GO term mappings)

Prerequisites:
  - Run 02_download_interpro_bulk.sh (download from EBI FTP)
  - Run 03_prepare_for_ingest.sh (add headers, parse supplementary files)
  - Active Spark session on JupyterHub

Usage:
  python data/interpro_lookup/scripts/04_ingest_interpro.py
  python data/interpro_lookup/scripts/04_ingest_interpro.py --skip-upload  # if already on MinIO
  python data/interpro_lookup/scripts/04_ingest_interpro.py --tables entry,go_mapping  # subset
"""

import argparse
import os
import sys
import time

from berdl_notebook_utils.berdl_settings import get_settings
from berdl_notebook_utils.minio_governance import get_minio_credentials
from minio import Minio

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREPARED_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "prepared")

BUCKET = "cdm-lake"
BRONZE_PREFIX = "tenant-general-warehouse/kescience/datasets/interpro"

# Files to upload: (remote_name, local_path)
FILES = [
    ("protein2ipr.tsv.gz", os.path.join(PREPARED_DIR, "protein2ipr.tsv.gz")),
    ("interpro_entries.tsv", os.path.join(PREPARED_DIR, "interpro_entries.tsv")),
    ("interpro_go_mappings.tsv", os.path.join(PREPARED_DIR, "interpro_go_mappings.tsv")),
    ("interpro_ingest.json", os.path.join(SCRIPT_DIR, "interpro_ingest.json")),
]


def get_minio_client():
    """Create MinIO client from BERDL credentials."""
    creds = get_minio_credentials()
    settings = get_settings()
    endpoint = settings.MINIO_ENDPOINT_URL.replace("https://", "").replace(
        "http://", ""
    )
    client = Minio(
        endpoint=endpoint,
        access_key=creds.access_key,
        secret_key=creds.secret_key,
        secure=True,
    )
    print(f"MinIO client ready (user: {creds.username})")
    return client


def upload_files(minio_client, files_to_upload):
    """Upload prepared files to MinIO bronze storage."""
    print(f"\nUploading to s3a://{BUCKET}/{BRONZE_PREFIX}/")

    for remote_name, local_path in files_to_upload:
        if not os.path.exists(local_path):
            print(f"  SKIP {remote_name} (not found at {local_path})")
            continue

        remote_key = f"{BRONZE_PREFIX}/{remote_name}"
        fsize = os.path.getsize(local_path)
        fsize_mb = fsize / 1024 / 1024

        if fsize_mb > 1000:
            print(f"  Uploading {remote_name} ({fsize_mb:.0f} MB) — this may take a while...",
                  flush=True)
        else:
            print(f"  Uploading {remote_name} ({fsize_mb:.1f} MB)...", end="", flush=True)

        t0 = time.time()
        minio_client.fput_object(BUCKET, remote_key, local_path)
        elapsed = time.time() - t0

        rate = fsize_mb / elapsed if elapsed > 0 else 0
        print(f" done ({elapsed:.0f}s, {rate:.1f} MB/s)")

    # Verify uploads
    print(f"\nVerifying uploads:")
    objects = list(
        minio_client.list_objects(BUCKET, prefix=BRONZE_PREFIX, recursive=True)
    )
    for obj in objects:
        name = obj.object_name.split("/")[-1]
        size_mb = obj.size / 1024 / 1024
        print(f"  {name:40s} {size_mb:>10.1f} MB")


def run_ingest(minio_client, tables_filter=None):
    """Run data_lakehouse_ingest to create Delta tables."""
    from data_lakehouse_ingest import ingest

    cfg_path = f"s3a://{BUCKET}/{BRONZE_PREFIX}/interpro_ingest.json"
    print(f"\nRunning data_lakehouse_ingest from {cfg_path}")

    if tables_filter:
        print(f"  Filtering to tables: {tables_filter}")

    t0 = time.time()
    report = ingest(cfg_path, minio_client=minio_client)
    elapsed = time.time() - t0

    # Summary
    print(f"\n{'=' * 60}")
    print(f"INGESTION REPORT")
    print(f"{'=' * 60}")
    print(f"Success: {report['success']}")
    print(f"Duration: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    for t in report.get("tables", []):
        if tables_filter and t["name"] not in tables_filter:
            continue
        status = t.get("status", "unknown")
        rows = t.get("rows_written", 0)
        print(f"  {t['name']:30s} {rows:>14,} rows  [{status}]")
    if report.get("errors"):
        print(f"\nErrors:")
        for e in report["errors"]:
            print(f"  ERROR: {e}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Ingest InterPro into BERDL")
    parser.add_argument("--skip-upload", action="store_true",
                        help="Skip upload (files already on MinIO)")
    parser.add_argument("--tables", type=str, default="",
                        help="Comma-separated table names to ingest (default: all)")
    args = parser.parse_args()

    tables_filter = set(args.tables.split(",")) if args.tables else None

    # Validate prepared files exist
    if not args.skip_upload:
        missing = [name for name, path in FILES if not os.path.exists(path)]
        if missing:
            print("ERROR: Missing prepared files:")
            for name in missing:
                print(f"  {name}")
            print("\nRun 03_prepare_for_ingest.sh first.")
            sys.exit(1)

    minio_client = get_minio_client()

    if not args.skip_upload:
        upload_files(minio_client, FILES)

    report = run_ingest(minio_client, tables_filter)

    if report["success"]:
        print(f"\nInterPro data is now queryable as kescience_interpro.*")
        print(f"\nExample queries:")
        print(f"  -- All InterPro entries for a UniProt protein")
        print(f"  SELECT * FROM kescience_interpro.protein2ipr")
        print(f"  WHERE uniprot_acc = 'A0A2M8CU66'")
        print(f"")
        print(f"  -- Pangenome gene clusters with InterPro domains")
        print(f"  SELECT ba.gene_cluster_id, ip.ipr_id, ip.ipr_desc, ip.source_db")
        print(f"  FROM kbase_ke_pangenome.bakta_annotations ba")
        print(f"  JOIN kescience_interpro.protein2ipr ip")
        print(f"    ON REPLACE(ba.uniref100, 'UniRef100_', '') = ip.uniprot_acc")
        print(f"  LIMIT 10")
    else:
        print(f"\nIngestion had errors — check report above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Run Delta Lake ingestion for bakta reannotation tables.

Files are already on MinIO at the user staging area:
  s3a://cdm-lake/users-general-warehouse/psdehal/data/bakta_reannotation/

This script runs data_lakehouse_ingest directly using an inline config dict,
skipping the upload step.

Usage:
  python run_ingest.py
"""

from berdl_notebook_utils.berdl_settings import get_settings
from berdl_notebook_utils.minio_governance import get_minio_credentials
from data_lakehouse_ingest import ingest
from minio import Minio

BUCKET = "cdm-lake"
USER_PREFIX = "users-general-warehouse/psdehal/data/bakta_reannotation"

INGEST_CONFIG = {
    "tenant": "kbase",
    "dataset": "ke_pangenome",
    "paths": {
        "bronze_base": f"s3a://{BUCKET}/{USER_PREFIX}/",
        "silver_base": "s3a://cdm-lake/tenant-sql-warehouse/kbase/kbase_ke_pangenome.db",
    },
    "defaults": {"tsv": {"header": True, "delimiter": "\t", "inferSchema": False}},
    "tables": [
        {
            "name": "bakta_annotations",
            "format": "tsv",
            "bronze_path": f"s3a://{BUCKET}/{USER_PREFIX}/bakta_annotations.tsv",
            "schema_sql": (
                "gene_cluster_id STRING, length INT, gene STRING, product STRING, "
                "hypothetical BOOLEAN, ec STRING, go STRING, cog_id STRING, "
                "cog_category STRING, kegg_orthology_id STRING, refseq STRING, "
                "uniparc STRING, uniref100 STRING, uniref90 STRING, uniref50 STRING, "
                "molecular_weight DOUBLE, isoelectric_point DOUBLE"
            ),
        },
        {
            "name": "bakta_db_xrefs",
            "format": "tsv",
            "bronze_path": f"s3a://{BUCKET}/{USER_PREFIX}/bakta_db_xrefs.tsv",
            "schema_sql": "gene_cluster_id STRING, db STRING, accession STRING",
        },
        {
            "name": "bakta_pfam_domains",
            "format": "tsv",
            "bronze_path": f"s3a://{BUCKET}/{USER_PREFIX}/bakta_pfam_domains.tsv",
            "schema_sql": (
                "gene_cluster_id STRING, pfam_id STRING, pfam_name STRING, "
                "start INT, stop INT, score DOUBLE, evalue DOUBLE, "
                "aa_cov DOUBLE, hmm_cov DOUBLE"
            ),
        },
        {
            "name": "bakta_amr",
            "format": "tsv",
            "bronze_path": f"s3a://{BUCKET}/{USER_PREFIX}/bakta_amr.tsv",
            "schema_sql": (
                "gene_cluster_id STRING, amr_gene STRING, amr_product STRING, "
                "method STRING, identity DOUBLE, query_cov DOUBLE, "
                "subject_cov DOUBLE, accession STRING"
            ),
        },
    ],
}


def main():
    creds = get_minio_credentials()
    settings = get_settings()
    endpoint = settings.MINIO_ENDPOINT_URL.replace("https://", "").replace("http://", "")

    minio_client = Minio(
        endpoint=endpoint,
        access_key=creds.access_key,
        secret_key=creds.secret_key,
        secure=True,
    )
    print(f"MinIO client ready (user: {creds.username})")

    # Verify source files exist
    print(f"\nVerifying source files on MinIO:")
    expected = [
        "bakta_annotations.tsv",
        "bakta_db_xrefs.tsv",
        "bakta_pfam_domains.tsv",
        "bakta_amr.tsv",
    ]
    objs = {
        o.object_name.split("/")[-1]: o.size
        for o in minio_client.list_objects(BUCKET, prefix=USER_PREFIX, recursive=True)
    }
    all_present = True
    for f in expected:
        if f in objs:
            print(f"  OK  {f:45s} {objs[f]:>15,} bytes")
        else:
            print(f"  MISSING  {f}")
            all_present = False
    if not all_present:
        print("\nERROR: Missing source files. Aborting.")
        return

    # Run ingestion using inline config dict (no need to upload JSON)
    print(f"\nRunning data_lakehouse_ingest (inline config, 4 tables)...")
    print("NOTE: bakta_annotations.tsv is 19 GB — this will take a while.\n")
    report = ingest(INGEST_CONFIG, minio_client=minio_client)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"INGESTION REPORT")
    print(f"{'=' * 60}")
    print(f"Success: {report['success']}")
    print(f"Duration: {report.get('duration_sec', 'N/A')}")
    for t in report.get("tables", []):
        print(
            f"  {t['name']:30s} {str(t.get('rows_written', '?')):>14s} rows  [{t.get('status', '?')}]"
        )
    if report.get("errors"):
        for e in report["errors"]:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    main()

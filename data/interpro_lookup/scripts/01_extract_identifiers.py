#!/usr/bin/env python3
"""
Extract UniRef/UniParc accessions from bakta_annotations in BERDL.

Queries the bakta_annotations table for all gene clusters and extracts
UniProt accessions from UniRef100/90/50 columns plus UniParc IDs.

Outputs:
  data/interpro_lookup/gene_cluster_accessions.tsv
    Columns: gene_cluster_id, uniref100_acc, uniref90_acc, uniref50_acc, uniparc

Usage:
  # On JupyterHub (CLI):
  python data/interpro_lookup/scripts/01_extract_identifiers.py

  # With chunk size (default processes all at once):
  python data/interpro_lookup/scripts/01_extract_identifiers.py --chunk-size 5000000
"""

import argparse
import os
import sys
import time

# Spark session — works from JupyterHub CLI
try:
    from berdl_notebook_utils.setup_spark_session import get_spark_session
except ImportError:
    from get_spark_session import get_spark_session

DB = "kbase_ke_pangenome"
OUT_DIR = "data/interpro_lookup"
OUT_FILE = os.path.join(OUT_DIR, "gene_cluster_accessions.tsv")
CHECKPOINT_FILE = os.path.join(OUT_DIR, "checkpoints", "extract_checkpoint.txt")


def parse_uniref_accession(uniref_id):
    """Extract UniProt accession from UniRef ID.

    UniRef50_F4GG65 -> F4GG65
    UniRef90_A0A000 -> A0A000
    UniRef100_P12345 -> P12345
    """
    if uniref_id and "_" in uniref_id:
        return uniref_id.split("_", 1)[1]
    return None


def main():
    parser = argparse.ArgumentParser(description="Extract UniRef/UniParc from BERDL")
    parser.add_argument("--chunk-size", type=int, default=0,
                        help="Process in chunks of N rows (0 = all at once)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last checkpoint")
    args = parser.parse_args()

    os.makedirs(os.path.join(OUT_DIR, "checkpoints"), exist_ok=True)

    # Check for resume
    offset = 0
    if args.resume and os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            offset = int(f.read().strip())
        print(f"Resuming from offset {offset:,}")

    print("Connecting to Spark...")
    spark = get_spark_session()

    # Count total rows first
    total = spark.sql(f"SELECT COUNT(*) AS n FROM {DB}.bakta_annotations").collect()[0]["n"]
    print(f"Total bakta_annotations rows: {total:,}")

    # Check available columns
    cols_df = spark.sql(f"DESCRIBE {DB}.bakta_annotations").toPandas()
    available_cols = set(cols_df["col_name"].tolist())
    print(f"Available columns: {sorted(available_cols)}")

    # Build SELECT for available UniRef/UniParc columns
    select_cols = ["gene_cluster_id"]
    for col in ["uniref100", "uniref90", "uniref50", "uniparc"]:
        if col in available_cols:
            select_cols.append(col)
        else:
            print(f"WARNING: column '{col}' not found in bakta_annotations")

    if len(select_cols) == 1:
        print("ERROR: No UniRef/UniParc columns found!")
        sys.exit(1)

    col_list = ", ".join(select_cols)

    if args.chunk_size > 0:
        _extract_chunked(spark, col_list, total, args.chunk_size, offset)
    else:
        _extract_all(spark, col_list)

    spark.stop()
    print(f"\nDone. Output: {OUT_FILE}")


def _extract_all(spark, col_list):
    """Extract all rows in one query, convert to pandas, write TSV."""
    print(f"Extracting: SELECT {col_list} FROM {DB}.bakta_annotations")
    print("This may take a while for 132.5M rows...")

    t0 = time.time()
    # Use Spark to write directly to avoid .toPandas() OOM
    df = spark.sql(f"SELECT {col_list} FROM {DB}.bakta_annotations")

    # Write via Spark to a temp parquet, then convert
    # Actually, for TSV we need pandas. Let's do chunked approach instead.
    print("Writing via Spark (parquet) to avoid OOM...")
    parquet_path = os.path.join(OUT_DIR, "_temp_accessions_parquet")
    df.write.mode("overwrite").parquet(parquet_path)
    elapsed = time.time() - t0
    print(f"Parquet written in {elapsed:.0f}s")

    # Now read parquet locally and convert to TSV with parsed accessions
    _parquet_to_tsv(spark, parquet_path)


def _extract_chunked(spark, col_list, total, chunk_size, offset):
    """Extract in chunks using LIMIT/OFFSET via row_number."""
    print(f"Extracting in chunks of {chunk_size:,} (offset={offset:,})")

    # Use row_number for deterministic chunking
    # First, create a temp view with row numbers
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW bakta_numbered AS
        SELECT {col_list}, ROW_NUMBER() OVER (ORDER BY gene_cluster_id) AS rn
        FROM {DB}.bakta_annotations
    """)

    mode = "a" if offset > 0 else "w"
    write_header = offset == 0

    chunk_start = offset
    while chunk_start < total:
        chunk_end = min(chunk_start + chunk_size, total)
        print(f"\nChunk: rows {chunk_start:,} - {chunk_end:,} of {total:,}")

        t0 = time.time()
        chunk_df = spark.sql(f"""
            SELECT * FROM bakta_numbered
            WHERE rn > {chunk_start} AND rn <= {chunk_end}
        """).drop("rn").toPandas()

        # Parse UniRef accessions
        for col in ["uniref100", "uniref90", "uniref50"]:
            acc_col = f"{col}_acc"
            if col in chunk_df.columns:
                chunk_df[acc_col] = chunk_df[col].apply(parse_uniref_accession)
            else:
                chunk_df[acc_col] = None

        # Select output columns
        out_cols = ["gene_cluster_id", "uniref100_acc", "uniref90_acc", "uniref50_acc"]
        if "uniparc" in chunk_df.columns:
            out_cols.append("uniparc")

        chunk_df[out_cols].to_csv(
            OUT_FILE, sep="\t", index=False,
            mode=mode, header=write_header
        )

        elapsed = time.time() - t0
        print(f"  Written {len(chunk_df):,} rows in {elapsed:.1f}s")

        # Checkpoint
        with open(CHECKPOINT_FILE, "w") as f:
            f.write(str(chunk_end))

        mode = "a"
        write_header = False
        chunk_start = chunk_end


def _parquet_to_tsv(spark, parquet_path):
    """Convert parquet output to TSV with parsed accessions."""
    import pandas as pd

    print("Converting parquet to TSV with parsed accessions...")
    t0 = time.time()

    # Read parquet in chunks via pyarrow
    import pyarrow.parquet as pq

    dataset = pq.ParquetDataset(parquet_path)
    first_chunk = True

    for i, batch in enumerate(dataset.fragments):
        table = batch.to_table()
        chunk = table.to_pandas()

        # Parse UniRef accessions
        for col in ["uniref100", "uniref90", "uniref50"]:
            acc_col = f"{col}_acc"
            if col in chunk.columns:
                chunk[acc_col] = chunk[col].apply(parse_uniref_accession)
            else:
                chunk[acc_col] = None

        out_cols = ["gene_cluster_id", "uniref100_acc", "uniref90_acc", "uniref50_acc"]
        if "uniparc" in chunk.columns:
            out_cols.append("uniparc")

        chunk[out_cols].to_csv(
            OUT_FILE, sep="\t", index=False,
            mode="w" if first_chunk else "a",
            header=first_chunk
        )
        first_chunk = False

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1} parquet fragments...")

    elapsed = time.time() - t0
    print(f"TSV written in {elapsed:.0f}s: {OUT_FILE}")

    # Clean up temp parquet
    import shutil
    shutil.rmtree(parquet_path, ignore_errors=True)


if __name__ == "__main__":
    main()

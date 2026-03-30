#!/usr/bin/env python3
"""
Combine per-chunk bakta table TSVs into final tables.

Reads all tables/chunk_NNN/ and tables/cts_chunk_NNN/ directories,
concatenates matching TSVs, and writes final combined files.

Usage:
  python combine_tables.py
"""

import glob
import os

WORK_DIR = "/pscratch/sd/p/psdehal/bakta_reannotation"
TABLES_DIR = os.path.join(WORK_DIR, "tables")
FINAL_DIR = os.path.join(TABLES_DIR, "final")

TABLE_NAMES = [
    "bakta_annotations",
    "bakta_db_xrefs",
    "bakta_pfam_domains",
    "bakta_amr",
]


def combine_table(table_name):
    """Combine all per-chunk TSVs for one table into a single file."""
    chunk_dirs = sorted(
        glob.glob(os.path.join(TABLES_DIR, "chunk_*"))
        + glob.glob(os.path.join(TABLES_DIR, "cts_chunk_*"))
    )

    output_path = os.path.join(FINAL_DIR, f"{table_name}.tsv")
    row_count = 0
    chunks_found = 0
    header_written = False

    with open(output_path, "w") as out_f:
        for chunk_dir in chunk_dirs:
            tsv_path = os.path.join(chunk_dir, f"{table_name}.tsv")
            if not os.path.exists(tsv_path):
                print(f"  WARNING: {tsv_path} not found")
                continue
            chunks_found += 1
            with open(tsv_path) as in_f:
                header = in_f.readline()
                if not header_written:
                    out_f.write(header)
                    header_written = True
                for line in in_f:
                    out_f.write(line)
                    row_count += 1

    fsize = os.path.getsize(output_path)
    print(
        f"  {table_name:30s} {row_count:>14,} rows  "
        f"{fsize / (1024**3):>8.2f} GB  ({chunks_found} chunks)"
    )
    return row_count


def main():
    os.makedirs(FINAL_DIR, exist_ok=True)
    print(f"Combining tables into {FINAL_DIR}/\n")

    total_rows = 0
    for table_name in TABLE_NAMES:
        rows = combine_table(table_name)
        total_rows += rows

    print(f"\nTotal rows across all tables: {total_rows:,}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Collect InterProScan TSV results from NERSC and prepare for BERDL ingest.

After InterProScan jobs complete on NERSC:
  1. Upload results to MinIO
  2. Combine into a single TSV with header
  3. Ingest into kescience_interpro as a new table (interproscan_results)

InterProScan TSV format (11 or 15 columns depending on options):
  1. protein_accession
  2. sequence_md5
  3. sequence_length
  4. analysis (source database: Pfam, PRINTS, etc.)
  5. signature_accession
  6. signature_description
  7. start_location
  8. stop_location
  9. score (e-value)
  10. status (T = true match)
  11. date
  12. interpro_accession (if -iprlookup)
  13. interpro_description (if -iprlookup)
  14. go_annotations (if -goterms)
  15. pathways (if -pa)

Usage:
  # Point at the directory of InterProScan TSV results
  python 08_collect_results.py /path/to/results/

  # Or upload from MinIO path
  python 08_collect_results.py --minio-path cts/io/psdehal/interproscan_results/
"""

import argparse
import csv
import os
import sys
from pathlib import Path

HEADER = [
    "protein_accession",
    "sequence_md5",
    "sequence_length",
    "analysis",
    "signature_accession",
    "signature_description",
    "start_location",
    "stop_location",
    "score",
    "status",
    "date",
    "interpro_accession",
    "interpro_description",
    "go_annotations",
    "pathways",
]


def collect_results(results_dir: str, output_file: str):
    """Combine all InterProScan TSV files into one with header."""
    results_path = Path(results_dir)
    tsv_files = sorted(results_path.glob("split_*.tsv"))

    if not tsv_files:
        print(f"No split_*.tsv files found in {results_dir}")
        sys.exit(1)

    print(f"Found {len(tsv_files)} result files in {results_dir}")

    n_rows = 0
    n_empty = 0
    with open(output_file, "w", newline="") as out:
        writer = csv.writer(out, delimiter="\t")
        writer.writerow(HEADER)

        for tsv_file in tsv_files:
            file_rows = 0
            with open(tsv_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # InterProScan TSV has no header, just data
                    parts = line.split("\t")
                    # Pad to 15 columns if needed
                    while len(parts) < 15:
                        parts.append("")
                    writer.writerow(parts[:15])
                    file_rows += 1
                    n_rows += 1

            if file_rows == 0:
                n_empty += 1

            if (tsv_files.index(tsv_file) + 1) % 1000 == 0:
                print(f"  Processed {tsv_files.index(tsv_file) + 1}/{len(tsv_files)} files, "
                      f"{n_rows:,} rows so far")

    print(f"\nDone: {n_rows:,} rows from {len(tsv_files)} files → {output_file}")
    if n_empty:
        print(f"  ({n_empty} files had no results — sequences with no domain hits)")


def main():
    parser = argparse.ArgumentParser(
        description="Collect InterProScan results for BERDL ingest")
    parser.add_argument("results_dir", help="Directory with split_NNNNN.tsv files")
    parser.add_argument("--output", default="interproscan_combined.tsv",
                        help="Output combined TSV file")
    args = parser.parse_args()

    collect_results(args.results_dir, args.output)

    print(f"\nNext steps:")
    print(f"  1. Upload {args.output} to MinIO:")
    print(f"     mc cp {args.output} cts/io/psdehal/interproscan_results/")
    print(f"  2. Ingest into BERDL (add interproscan_results table to interpro_ingest.json)")


if __name__ == "__main__":
    main()

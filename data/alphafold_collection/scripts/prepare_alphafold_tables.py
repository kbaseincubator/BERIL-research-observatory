#!/usr/bin/env python3
"""
Parse AlphaFold EBI metadata CSVs into headerized TSVs for Delta Lake ingestion.

Input files (from EBI FTP, no headers):
  accession_ids.csv — 5 columns: uniprot_accession, first_residue, last_residue, alphafold_id, version
  msa_depths.csv    — 2 columns: alphafold_id, msa_depth (assumed format)

Output files:
  alphafold_entries.tsv    — with header row, tab-separated
  alphafold_msa_depths.tsv — with header row, tab-separated

Usage:
  python prepare_alphafold_tables.py [--input-dir DIR] [--output-dir DIR] [--sample N]
"""

import argparse
import csv
import os
import sys


def parse_accession_ids(input_path, output_path, sample_n=0):
    """Parse accession_ids.csv into alphafold_entries.tsv.

    Input columns (no header, comma-separated):
      0: UniProt accession (e.g., A8H2R3)
      1: First residue index (e.g., 1)
      2: Last residue index (e.g., 199)
      3: AlphaFold DB identifier (e.g., AF-A8H2R3-F1)
      4: Latest version number (e.g., 4)

    Output columns (tab-separated, with header):
      uniprot_accession, first_residue, last_residue, alphafold_id, model_version
    """
    print(f"Parsing {input_path} -> {output_path}")
    count = 0
    with open(input_path, "r") as fin, open(output_path, "w", newline="") as fout:
        writer = csv.writer(fout, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "uniprot_accession",
                "first_residue",
                "last_residue",
                "alphafold_id",
                "model_version",
            ]
        )
        reader = csv.reader(fin)
        for row in reader:
            if len(row) < 5:
                continue
            writer.writerow(
                [
                    row[0].strip(),
                    row[1].strip(),
                    row[2].strip(),
                    row[3].strip(),
                    row[4].strip(),
                ]
            )
            count += 1
            if sample_n and count >= sample_n:
                break
            if count % 10_000_000 == 0:
                print(f"  ... {count:,} rows")
    print(f"  Done: {count:,} rows written")
    return count


def parse_msa_depths(input_path, output_path, sample_n=0):
    """Parse msa_depths.csv into alphafold_msa_depths.tsv.

    The MSA depths file format needs to be verified after download.
    Expected format (comma-separated, no header):
      0: AlphaFold DB identifier or UniProt accession
      1: MSA depth (integer)

    Output columns (tab-separated, with header):
      uniprot_accession, msa_depth

    If the input uses AlphaFold IDs (AF-XXXXX-F1), extract the UniProt
    accession from the middle segment.
    """
    print(f"Parsing {input_path} -> {output_path}")

    # Peek at first line to detect format
    with open(input_path, "r") as f:
        first_line = f.readline().strip()
    parts = first_line.split(",")
    print(f"  First line: {first_line}")
    print(f"  Detected {len(parts)} columns")

    # Determine if first column is AlphaFold ID or UniProt accession
    id_col = parts[0].strip()
    uses_af_id = id_col.startswith("AF-")

    count = 0
    with open(input_path, "r") as fin, open(output_path, "w", newline="") as fout:
        writer = csv.writer(fout, delimiter="\t", lineterminator="\n")
        writer.writerow(["uniprot_accession", "msa_depth"])
        reader = csv.reader(fin)
        for row in reader:
            if len(row) < 2:
                continue
            identifier = row[0].strip()
            depth = row[1].strip()

            # Extract UniProt accession from AlphaFold ID if needed
            if uses_af_id and identifier.startswith("AF-"):
                # AF-A8H2R3-F1 -> A8H2R3
                uniprot = identifier.split("-")[1]
            else:
                uniprot = identifier

            writer.writerow([uniprot, depth])
            count += 1
            if sample_n and count >= sample_n:
                break
            if count % 10_000_000 == 0:
                print(f"  ... {count:,} rows")
    print(f"  Done: {count:,} rows written")
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Prepare AlphaFold metadata for Delta Lake ingestion"
    )
    parser.add_argument(
        "--input-dir",
        default="/pscratch/sd/p/psdehal/alphafold_collection",
        help="Directory containing downloaded CSVs",
    )
    parser.add_argument(
        "--output-dir",
        default="/pscratch/sd/p/psdehal/alphafold_collection",
        help="Directory for output TSVs",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Only process first N rows (0 = all rows)",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Parse accession_ids.csv
    acc_in = os.path.join(args.input_dir, "accession_ids.csv")
    acc_out = os.path.join(args.output_dir, "alphafold_entries.tsv")
    if not os.path.exists(acc_in):
        print(f"ERROR: {acc_in} not found. Run download_alphafold_data.sh first.")
        sys.exit(1)
    n_entries = parse_accession_ids(acc_in, acc_out, sample_n=args.sample)

    # Parse msa_depths.csv
    msa_in = os.path.join(args.input_dir, "msa_depths.csv")
    msa_out = os.path.join(args.output_dir, "alphafold_msa_depths.tsv")
    if not os.path.exists(msa_in):
        print(f"WARNING: {msa_in} not found. Skipping MSA depths.")
        n_msa = 0
    else:
        n_msa = parse_msa_depths(msa_in, msa_out, sample_n=args.sample)

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"  alphafold_entries.tsv:    {n_entries:>14,} rows")
    print(f"  alphafold_msa_depths.tsv: {n_msa:>14,} rows")
    print(f"\nOutput directory: {args.output_dir}")


if __name__ == "__main__":
    main()

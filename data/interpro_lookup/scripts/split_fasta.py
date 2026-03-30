#!/usr/bin/env python3
"""
Split large FASTA files into sub-chunks of N sequences each.

Usage:
  # Split all chunks in a directory into 10K-sequence sub-chunks
  python split_fasta.py /path/to/fasta_dir/ /path/to/output/ --chunk-size 10000

  # Split a single FASTA file
  python split_fasta.py /path/to/file.fasta /path/to/output/ --chunk-size 10000

Output files are named split_00000.fasta, split_00001.fasta, etc.
Numbering is global across all input files (continuous).
"""

import argparse
import os
from pathlib import Path


def split_fasta_file(input_path: str, output_dir: str, chunk_size: int,
                     start_index: int = 0) -> int:
    """
    Split a FASTA file into sub-chunks.

    Returns the next split index (for chaining across files).
    """
    current_split = start_index
    current_count = 0
    out_f = None

    with open(input_path) as f:
        for line in f:
            if line.startswith(">"):
                if current_count % chunk_size == 0:
                    if out_f:
                        out_f.close()
                    split_name = f"split_{current_split:05d}.fasta"
                    out_f = open(os.path.join(output_dir, split_name), "w")
                    current_split += 1
                current_count += 1
            if out_f:
                # Strip asterisks (stop codons) — InterProScan rejects them
                if not line.startswith(">"):
                    line = line.replace("*", "")
                out_f.write(line)

    if out_f:
        out_f.close()

    return current_split


def main():
    parser = argparse.ArgumentParser(description="Split FASTA files into sub-chunks")
    parser.add_argument("input", help="Input FASTA file or directory of FASTA files")
    parser.add_argument("output_dir", help="Output directory for split files")
    parser.add_argument("--chunk-size", type=int, default=10000,
                        help="Sequences per sub-chunk (default: 10000)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    input_path = Path(args.input)

    if input_path.is_dir():
        fasta_files = sorted(input_path.glob("*.fasta")) + sorted(input_path.glob("*.fa"))
        print(f"Found {len(fasta_files)} FASTA files in {input_path}")
    else:
        fasta_files = [input_path]

    split_index = 0
    total_seqs = 0

    for fasta_file in fasta_files:
        n_seqs = sum(1 for line in open(fasta_file) if line.startswith(">"))
        n_splits = (n_seqs + args.chunk_size - 1) // args.chunk_size
        print(f"  {fasta_file.name}: {n_seqs:,} sequences → {n_splits} splits "
              f"(split_{split_index:05d} – split_{split_index + n_splits - 1:05d})")

        split_index = split_fasta_file(str(fasta_file), args.output_dir,
                                       args.chunk_size, split_index)
        total_seqs += n_seqs

    print(f"\nDone: {total_seqs:,} sequences → {split_index} split files in {args.output_dir}")
    print(f"SLURM array range: --array=0-{split_index - 1}")


if __name__ == "__main__":
    main()

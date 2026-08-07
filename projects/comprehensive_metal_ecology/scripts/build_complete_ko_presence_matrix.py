"""
build_complete_ko_presence_matrix.py
====================================
Build a complete genus × KO presence matrix from mgnify and SPIRE genome-level data.

This script aggregates per-genome KO presence data from the per_ko_metal_associations
project to create a comprehensive genus-level matrix covering all 275 metal KOs.

Inputs:
  - per_ko_metal_associations/data/mgnify_all_ko_matrix.parquet
  - per_ko_metal_associations/data/spire_all_ko_matrix.parquet

Outputs:
  - comprehensive_metal_ecology/data/genus_ko_presence_all_275_kos.csv
    (genus_lower, ko, n_genomes_with_ko)
"""

import os
import sys
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'

import pandas as pd
import numpy as np

# Paths
PROJECT_DIR = Path(__file__).parent.parent
PER_KO_DIR = PROJECT_DIR.parent / "per_ko_metal_associations"
DATA_DIR = PROJECT_DIR / "data"
RESULTS_DIR = PROJECT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

MGNIFY_MATRIX = PER_KO_DIR / "data" / "mgnify_all_ko_matrix.parquet"
SPIRE_MATRIX = PER_KO_DIR / "data" / "spire_all_ko_matrix.parquet"
DENSITY_FILE = DATA_DIR / "01_genus_ko_density_spark.csv"
OUTPUT_FILE = DATA_DIR / "genus_ko_presence_all_275_kos.csv"

def build_genus_ko_matrix():
    """Build complete genus × KO presence matrix from genome-level data."""
    print("=" * 80)
    print("Building complete genus × KO presence matrix")
    print("=" * 80)

    # Load density file to get genus normalization
    print(f"\nLoading genus density from {DENSITY_FILE.name}...")
    density = pd.read_csv(DENSITY_FILE)
    genus_to_lower = dict(zip(density['genus_lower'], density['genus_lower']))
    print(f"  {len(density)} unique genera in density file")

    # Combine mgnify and spire data
    print(f"\nLoading genome-level KO matrices...")
    print(f"  Loading {MGNIFY_MATRIX.name}...")
    mgnify = pd.read_parquet(MGNIFY_MATRIX)
    print(f"    Rows: {len(mgnify):,}")

    print(f"  Loading {SPIRE_MATRIX.name}...")
    spire = pd.read_parquet(SPIRE_MATRIX)
    print(f"    Rows: {len(spire):,}")

    # Combine
    print(f"\nCombining matrices...")
    combined = pd.concat([mgnify, spire], ignore_index=True)
    print(f"  Total rows: {len(combined):,}")
    print(f"  Unique KOs: {combined['ko_id'].nunique()}")
    print(f"  Unique genera: {combined['genus'].nunique()}")

    # Normalize genus names to lowercase
    combined['genus_lower'] = combined['genus'].str.lower()

    # Filter to only rows with valid KO and genus
    combined = combined[combined['ko_id'].notna() & combined['genus_lower'].notna()].copy()
    print(f"\n  After filtering NAs: {len(combined):,} rows")

    # For presence, use the 'present' column if available, otherwise use count > 0
    if 'present' in combined.columns:
        print(f"  Using 'present' column (KO present in genome: 0/1)")
        # Only count rows where present=1 (or True)
        combined = combined[combined['present'] == True].copy()
    else:
        print(f"  Using count > 0 (inferring presence)")
        combined = combined[combined['count'] > 0].copy()

    print(f"  After filtering to present KOs: {len(combined):,} rows")

    # Aggregate: count unique genomes per (genus, KO) pair
    print(f"\nAggregating by genus and KO...")
    genus_ko_presence = (
        combined
        .groupby(['genus_lower', 'ko_id'])
        .agg(n_genomes_with_ko=('genome_id', 'nunique'))
        .reset_index()
    )

    print(f"  Result: {len(genus_ko_presence):,} (genus, KO) pairs")
    print(f"  Unique genera: {genus_ko_presence['genus_lower'].nunique()}")
    print(f"  Unique KOs: {genus_ko_presence['ko_id'].nunique()}")

    # Save
    print(f"\nSaving to {OUTPUT_FILE.name}...")
    genus_ko_presence.to_csv(OUTPUT_FILE, index=False)
    print(f"  Saved: {OUTPUT_FILE}")

    # Report statistics
    print(f"\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"\nGenera per KO:")
    print(f"  Min: {genus_ko_presence.groupby('ko_id').size().min()}")
    print(f"  Median: {genus_ko_presence.groupby('ko_id').size().median():.0f}")
    print(f"  Max: {genus_ko_presence.groupby('ko_id').size().max()}")
    print(f"  Mean: {genus_ko_presence.groupby('ko_id').size().mean():.1f}")

    print(f"\nKOs per genus:")
    print(f"  Min: {genus_ko_presence.groupby('genus_lower').size().min()}")
    print(f"  Median: {genus_ko_presence.groupby('genus_lower').size().median():.0f}")
    print(f"  Max: {genus_ko_presence.groupby('genus_lower').size().max()}")
    print(f"  Mean: {genus_ko_presence.groupby('genus_lower').size().mean():.1f}")

    print(f"\nGenomes per KO (when present in genus):")
    print(f"  Min: {genus_ko_presence['n_genomes_with_ko'].min()}")
    print(f"  Median: {genus_ko_presence['n_genomes_with_ko'].median():.0f}")
    print(f"  Max: {genus_ko_presence['n_genomes_with_ko'].max()}")
    print(f"  Mean: {genus_ko_presence['n_genomes_with_ko'].mean():.1f}")

    # Overlap check with density
    overlap_genera = set(genus_ko_presence['genus_lower'].unique()) & set(density['genus_lower'].unique())
    print(f"\nGenus overlap with density file: {len(overlap_genera)}/{len(density)} ({100*len(overlap_genera)/len(density):.1f}%)")

    return genus_ko_presence

if __name__ == "__main__":
    build_genus_ko_matrix()

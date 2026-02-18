"""
Helper to load essential gene families from the lakehouse.

This references data from projects/essential_genome rather than copying it.
Attribution: Dehal (2026), essential_genome project
"""

import pandas as pd
import subprocess
import os
from pathlib import Path

LAKEHOUSE_PATH = "berdl-minio/cdm-lake/tenant-general-warehouse/microbialdiscoveryforge/projects/essential_genome/data/essential_families.tsv"
TEMP_FILE = "/tmp/essential_families.tsv"


def load_essential_families_from_lakehouse():
    """
    Load essential gene families from the lakehouse via MinIO.

    Returns:
        pd.DataFrame: Essential families data
    """
    # Set proxy for MinIO
    env = os.environ.copy()
    env['https_proxy'] = 'http://127.0.0.1:8123'
    env['no_proxy'] = 'localhost,127.0.0.1'

    # Download to temp location
    print(f"📥 Downloading essential families from lakehouse...")
    print(f"   Source: {LAKEHOUSE_PATH}")
    print(f"   Attribution: projects/essential_genome (Dehal, 2026)")

    result = subprocess.run(
        ['mc', 'cp', LAKEHOUSE_PATH, TEMP_FILE],
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to download from lakehouse: {result.stderr}")

    # Load into pandas
    df = pd.read_csv(TEMP_FILE, sep='\t')
    print(f"✅ Loaded {len(df):,} ortholog groups")

    return df


def get_universal_essential_families():
    """
    Get the 859 universally essential gene families.

    Returns:
        pd.DataFrame: Universally essential families
    """
    df = load_essential_families_from_lakehouse()
    universal = df[df['essentiality_class'] == 'universally_essential'].copy()
    print(f"✅ Filtered to {len(universal):,} universally essential families")
    return universal


if __name__ == "__main__":
    # Test
    families = get_universal_essential_families()
    print("\nSample families:")
    print(families[['OG_id', 'rep_gene', 'rep_desc', 'n_organisms']].head())

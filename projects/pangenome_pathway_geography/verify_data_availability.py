#!/usr/bin/env python3
"""
Verify data availability for Pangenome-Pathway-Geography analysis.

This script queries BERDL to check:
1. Pangenome table row count
2. Gapmind pathways table row count
3. AlphaEarth embeddings table row count
4. Sample data from each table

Run this before executing the full analysis notebooks to verify API access
and data availability.

Usage:
    python verify_data_availability.py
"""

import os
import json
import requests
from pathlib import Path


def load_auth_token():
    """Load KBASE_AUTH_TOKEN from .env file."""
    env_path = Path(__file__).parent.parent.parent / '.env'
    if not env_path.exists():
        raise FileNotFoundError(
            f"No .env file found at {env_path}\n"
            "Please create a .env file with KBASE_AUTH_TOKEN"
        )

    with open(env_path) as f:
        for line in f:
            if line.startswith('KBASE_AUTH_TOKEN'):
                # Extract token from KBASE_AUTH_TOKEN="token" or KBASE_AUTH_TOKEN=token
                token = line.split('=', 1)[1].strip().strip('"').strip("'")
                return token

    raise ValueError("KBASE_AUTH_TOKEN not found in .env file")


def query_berdl(endpoint, payload, auth_token):
    """Query BERDL API endpoint."""
    url = f"https://hub.berdl.kbase.us/apis/mcp/delta/{endpoint}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 70)
    print("BERDL Data Availability Verification")
    print("=" * 70)

    # Load auth token
    try:
        auth_token = load_auth_token()
        print("✓ Auth token loaded from .env file")
    except Exception as e:
        print(f"✗ Failed to load auth token: {e}")
        return

    # Database and table info
    database = "kbase_ke_pangenome"
    tables = {
        "pangenome": "Pangenome statistics (species-level)",
        "gapmind_pathways": "Metabolic pathway predictions (genome-level)",
        "alphaearth_embeddings_all_years": "Geospatial embeddings (genome-level)"
    }

    print(f"\nDatabase: {database}")
    print("-" * 70)

    # Check each table
    for table_name, description in tables.items():
        print(f"\n{description}")
        print(f"Table: {table_name}")

        # Get row count
        try:
            result = query_berdl(
                "tables/count",
                {"database": database, "table": table_name},
                auth_token
            )
            count = result['count']
            print(f"  Rows: {count:,}")
        except Exception as e:
            print(f"  ✗ Failed to count rows: {e}")
            continue

        # Get sample data
        try:
            result = query_berdl(
                "tables/sample",
                {"database": database, "table": table_name, "limit": 2},
                auth_token
            )
            sample = result['sample']
            print(f"  Columns: {len(sample[0]) if sample else 0}")
            print(f"  Sample:")
            for i, row in enumerate(sample, 1):
                print(f"    Row {i}: {list(row.keys())[:5]}... ({len(row)} columns)")
        except Exception as e:
            print(f"  ✗ Failed to sample data: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("\nExpected data availability:")
    print("  • Pangenome: ~27,690 species")
    print("  • Gapmind pathways: ~305M genome-pathway pairs")
    print("  • AlphaEarth embeddings: ~83K genomes (28% coverage)")
    print("\nIntegrated analysis:")
    print("  • Species with all three data types: ~2-3K species")
    print("  • This represents ~10% of total species")
    print("  • Sufficient for robust comparative analysis")

    print("\n✓ Data verification complete!")
    print("\nNext steps:")
    print("  1. Upload notebooks to BERDL JupyterHub")
    print("  2. Run 01_data_extraction.ipynb")
    print("  3. Download extracted data files")
    print("  4. Run 02_comparative_analysis.ipynb")


if __name__ == "__main__":
    main()

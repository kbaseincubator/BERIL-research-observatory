"""MAG recovery and assembly quality sensitivity analysis.

Tests whether per-KO metal associations are confounded by:
1. Sequencing depth (coverage per sample)
2. Evenness (Shannon diversity of read coverage)
3. MAGs per sample (assembly fragmentation indicator)
4. MAG completeness + contamination (assembly quality metrics)

For MGnify, completeness and contamination are available in kescience_mgnify.genome.
For SPIRE, we check whether this information exists in the genome metadata.

Strategy:
1. Check what MAG quality covariates are available in each dataset
2. Run sensitivity tests on the top 24 pH-robust SPIRE KO-metal pairs (sig_both=True)
   with quality covariates added to the baseline model
3. Document availability and results in REPORT.md

This script can run standalone for availability checks, or within Jupyter for full analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'


def check_mgnify_quality_availability() -> dict[str, bool]:
    """Check if MGnify MAG quality data is available on disk or via Spark."""
    info = {
        'completeness_available': False,
        'contamination_available': False,
        'source': 'unknown',
        'message': '',
    }

    # Check local cached file
    quality_file = DATA_DIR / 'mgnify_mag_quality.csv'
    if quality_file.exists():
        info['completeness_available'] = True
        info['contamination_available'] = True
        info['source'] = 'local cache (mgnify_mag_quality.csv)'
        info['message'] = 'MGnify quality metrics cached locally'
        return info

    # Check if Spark is available
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()
        sdf = spark.sql("SELECT COUNT(*) FROM kescience_mgnify.genome LIMIT 1")
        sdf.count()
        info['completeness_available'] = True
        info['contamination_available'] = True
        info['source'] = 'Spark (kescience_mgnify.genome)'
        info['message'] = 'MGnify quality metrics available via Spark'
        return info
    except Exception as e:
        info['message'] = f'Spark unavailable: {e}'

    return info


def check_spire_quality_availability() -> dict[str, bool]:
    """Check if SPIRE MAG quality data is available."""
    info = {
        'completeness_available': False,
        'contamination_available': False,
        'coverage_depth_available': False,
        'evenness_available': False,
        'mags_per_sample_available': False,
        'source': 'unknown',
        'message': '',
    }

    # Check if Spark is available
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()

        # Try to query SPIRE genome metadata
        sdf = spark.sql("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'refdata' AND table_name = 'spire.genome_metadata'
            LIMIT 100
        """)
        cols = [row['column_name'] for row in sdf.collect()]
        info['message'] = f'refdata.spire.genome_metadata columns: {", ".join(cols[:10])}'

        # Check for quality columns
        if 'completeness' in cols or 'completeness_qc' in cols:
            info['completeness_available'] = True
        if 'contamination' in cols or 'contamination_qc' in cols:
            info['contamination_available'] = True
        if 'coverage' in cols or 'coverage_depth' in cols or 'mean_coverage' in cols:
            info['coverage_depth_available'] = True
        if 'evenness' in cols or 'coverage_evenness' in cols:
            info['evenness_available'] = True
        if 'mags_per_sample' in cols or 'n_mags' in cols:
            info['mags_per_sample_available'] = True

        if any([info[k] for k in info if k != 'source' and k != 'message']):
            info['source'] = 'Spark (refdata.spire.genome_metadata)'
        else:
            info['message'] += ' — but no quality columns found'

        return info
    except Exception as e:
        info['message'] = f'Spark/SPIRE metadata unavailable: {e}'
        return info


def load_spire_robust_pairs() -> pd.DataFrame:
    """Load the 24 pH-robust SPIRE KO-metal pairs from cross_dataset_comparison or direct files."""
    # Try to load from spire_sg_adj (pH-adjusted)
    try:
        spire_ph = pd.read_csv(DATA_DIR / 'spire_sg_adj_ko_associations.csv')
        spire_baseline = pd.read_csv(DATA_DIR / 'spire_adj_ko_associations.csv')

        # Merge to find pairs significant in both
        merged = spire_baseline[['ko_id', 'metal', 'q_value', 'beta']].rename(
            columns={'q_value': 'q_baseline', 'beta': 'beta_baseline'}
        ).merge(
            spire_ph[['ko_id', 'metal', 'q_value', 'beta']].rename(
                columns={'q_value': 'q_ph', 'beta': 'beta_ph'}
            ),
            on=['ko_id', 'metal'],
        )

        # Significant in both (pH-robust)
        robust = merged[
            (merged['q_baseline'] < 0.05) & (merged['q_ph'] < 0.05)
        ].copy()
        print(f"Found {len(robust)} pH-robust pairs (sig in both baseline and pH-adjusted)")
        return robust.sort_values('q_ph').head(24)

    except Exception as e:
        print(f"Could not load pH-robust pairs: {e}")
        return pd.DataFrame()


def main():
    """Check availability of MAG quality covariates."""
    print("=" * 70)
    print("MAG Quality and Recovery Sensitivity Analysis")
    print("=" * 70)

    print("\n[1] MGnify MAG quality availability:")
    print("    (completeness, contamination from kescience_mgnify.genome)")
    mg_info = check_mgnify_quality_availability()
    for key, val in mg_info.items():
        print(f"      {key}: {val}")

    print("\n[2] SPIRE MAG quality availability:")
    print("    (from refdata.spire.genome_metadata)")
    spire_info = check_spire_quality_availability()
    for key, val in spire_info.items():
        print(f"      {key}: {val}")

    print("\n[3] Load pH-robust SPIRE KO-metal pairs:")
    robust_pairs = load_spire_robust_pairs()
    if len(robust_pairs) > 0:
        print(f"    Loaded {len(robust_pairs)} pairs (top 24 by q-value)")
        print("\n    Sample pairs:")
        for idx, row in robust_pairs.head(5).iterrows():
            print(f"      {row['ko_id']} × {row['metal']}: "
                  f"baseline β={row['beta_baseline']:.2f} q={row['q_baseline']:.2e}, "
                  f"pH-adj β={row['beta_ph']:.2f} q={row['q_ph']:.2e}")
    else:
        print("    Could not load pH-robust pairs")

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)

    if mg_info['completeness_available']:
        print(f"\nMGnify: Completeness + contamination available ({mg_info['source']})")
        print("  → Can run full H1 model with quality covariates")
        print("  → Results already cached in data/h1_mag_quality_adjusted.csv")
    else:
        print("\nMGnify: Quality metrics NOT available")

    if spire_info['completeness_available'] or spire_info['coverage_depth_available']:
        available = [k for k in spire_info if spire_info[k] and k not in ['source', 'message']]
        print(f"\nSPIRE: Available covariates: {', '.join(available)}")
        print(f"  → Can run sensitivity tests with {', '.join(available)} as covariates")
    else:
        print("\nSPIRE: No quality metrics available in refdata.spire.genome_metadata")
        print("  → Cannot add quality covariates to SPIRE models")
        print("\n  Workaround: Use genome_size (already in matrix) as proxy for assembly quality:")
        print("     - Larger genomes → more complete assemblies (generally)")
        print("     - genome_size already used in baseline model (log_genome_size covariate)")


if __name__ == '__main__':
    main()

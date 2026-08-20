#!/usr/bin/env python3
"""
pH partial-correlation sensitivity analysis for CWM per-KO × USA × USGS signals.

Tests whether 6 FDR-significant KO-metal pairs survive after controlling for soil pH.
Uses 50 km spatial thinning (per KO per grid cell) and Spearman partial correlation.
"""

import os
import sys
os.environ['OMP_NUM_THREADS'] = '1'
sys.path.append('/opt/conda/lib/python3.13/site-packages')

import berdl_notebook_utils
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from statsmodels.stats.multitest import multipletests

# ============================================================================
# Setup
# ============================================================================

spark = berdl_notebook_utils.get_spark_session()

PROJ_DIR = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology')
DATA_DIR = PROJ_DIR / 'data'
OUT_PATH = DATA_DIR / 'cwm_per_ko_usa_ph_adjusted.csv'

# Target pairs (from cwm_per_ko_usa_spearman.csv, q_BH < 0.05, 50km thinning)
TARGET_PAIRS = [
    ('K16014', 'Hg'),
    ('K04655', 'Hg'),
    ('K03605', 'Hg'),
    ('K04654', 'Hg'),
    ('K04654', 'As'),
    ('K00859', 'Pb'),
]

# ============================================================================
# Step 1: Pull pH from sample_metadata
# ============================================================================

print("[1/6] Pulling pH from arkinlab.microbeatlas.sample_metadata...")
pH_df = spark.sql(
    "SELECT sample_id, ph FROM arkinlab.microbeatlas.sample_metadata "
    "WHERE ph IS NOT NULL"
).toPandas()

print(f"  → {len(pH_df)} samples with pH")
print(f"  pH range: {pH_df['ph'].min():.2f} – {pH_df['ph'].max():.2f}")

# ============================================================================
# Step 2: Load CWM data
# ============================================================================

print("\n[2/6] Loading USA CWM × USGS joined data...")
cwm_df = pd.read_parquet(DATA_DIR / 'usa_cwm' / 'usa_cwm_usgs_joined.parquet')
print(f"  → {len(cwm_df)} rows, {cwm_df['sample_id'].nunique()} unique samples, "
      f"{cwm_df['ko_id'].nunique()} unique KOs")

# ============================================================================
# Step 3: Apply 50 km spatial thinning (one sample per KO per grid cell)
# ============================================================================

print("\n[3/6] Applying 50 km spatial thinning per KO (DEG=0.45)...")
np.random.seed(42)

DEG = 0.45  # ~50 km
cwm_df['lat_grid'] = (cwm_df['lat_x'] / DEG).astype(int)
cwm_df['lon_grid'] = (cwm_df['lon_x'] / DEG).astype(int)

# For each (ko_id, lat_grid, lon_grid) combination, sample one row
idx_to_keep = []
for (ko_id, lat_g, lon_g), group in cwm_df.groupby(['ko_id', 'lat_grid', 'lon_grid']):
    rng = np.random.RandomState(42)
    idx = group.index[rng.choice(len(group))]
    idx_to_keep.append(idx)

thinned = cwm_df.loc[idx_to_keep].reset_index(drop=True)
print(f"  → {len(thinned)} rows after thinning (one per KO per grid cell)")

# ============================================================================
# Step 4: Merge pH
# ============================================================================

print("\n[4/6] Merging pH data...")
thinned_ph = thinned.merge(pH_df, on='sample_id', how='left')
print(f"  → {thinned_ph['ph'].notna().sum()} / {len(thinned_ph)} rows have pH")

# ============================================================================
# Step 5: Compute partial Spearman for each target pair
# ============================================================================

print("\n[5/6] Computing partial Spearman correlations...")

def partial_spearman(x, y, z):
    """Spearman correlation between x and y controlling for z (OLS residuals)."""
    def resid(a, b):
        slope, intercept, _, _, _ = stats.linregress(b, a)
        return a - (slope * b + intercept)

    x_r = resid(x, z)
    y_r = resid(y, z)
    rho, p = stats.spearmanr(x_r, y_r)
    return rho, p

results = []

for ko_id, metal in TARGET_PAIRS:
    # Subset to this KO-metal pair
    pair_df = thinned_ph[thinned_ph['ko_id'] == ko_id].copy()

    if len(pair_df) == 0:
        print(f"  ✗ {ko_id} × {metal}: NO SAMPLES")
        results.append({
            'ko_id': ko_id,
            'metal': metal,
            'rho_raw': np.nan,
            'p_raw': np.nan,
            'q_raw': np.nan,
            'rho_partial': np.nan,
            'p_partial': np.nan,
            'q_partial': np.nan,
            'n_complete': 0,
            'n_after_ph_drop': 0,
        })
        continue

    n_complete = len(pair_df)

    # Drop rows where pH, cwm, or metal is missing
    pair_df_ph = pair_df.dropna(subset=['ph', 'cwm', metal])
    n_after_ph_drop = len(pair_df_ph)

    if n_after_ph_drop < 3:
        print(f"  ✗ {ko_id} × {metal}: n={n_after_ph_drop} after pH drop (too few)")
        results.append({
            'ko_id': ko_id,
            'metal': metal,
            'rho_raw': np.nan,
            'p_raw': np.nan,
            'q_raw': np.nan,
            'rho_partial': np.nan,
            'p_partial': np.nan,
            'q_partial': np.nan,
            'n_complete': n_complete,
            'n_after_ph_drop': n_after_ph_drop,
        })
        continue

    # Raw Spearman
    rho_raw, p_raw = stats.spearmanr(pair_df_ph['cwm'], pair_df_ph[metal])

    # Partial Spearman (controlling for pH)
    rho_partial, p_partial = partial_spearman(
        pair_df_ph['cwm'].values,
        pair_df_ph[metal].values,
        pair_df_ph['ph'].values
    )

    results.append({
        'ko_id': ko_id,
        'metal': metal,
        'rho_raw': rho_raw,
        'p_raw': p_raw,
        'q_raw': np.nan,
        'rho_partial': rho_partial,
        'p_partial': p_partial,
        'q_partial': np.nan,
        'n_complete': n_complete,
        'n_after_ph_drop': n_after_ph_drop,
    })

    print(f"  ✓ {ko_id} × {metal}: n={n_after_ph_drop}, "
          f"ρ_raw={rho_raw:+.3f} (p={p_raw:.4f}), "
          f"ρ_partial={rho_partial:+.3f} (p={p_partial:.4f})")

results_df = pd.DataFrame(results)

# ============================================================================
# Step 6: Apply BH-FDR correction
# ============================================================================

print("\n[6/6] Applying BH-FDR correction (across 6 tests)...")

# FDR correction on raw p-values
p_raw_valid = results_df['p_raw'].dropna()
if len(p_raw_valid) > 0:
    reject_raw, q_raw, _, _ = multipletests(p_raw_valid, method='fdr_bh')
    results_df.loc[results_df['p_raw'].notna(), 'q_raw'] = q_raw

# FDR correction on partial p-values
p_partial_valid = results_df['p_partial'].dropna()
if len(p_partial_valid) > 0:
    reject_partial, q_partial, _, _ = multipletests(p_partial_valid, method='fdr_bh')
    results_df.loc[results_df['p_partial'].notna(), 'q_partial'] = q_partial

# ============================================================================
# Print summary table
# ============================================================================

print("\n" + "="*110)
print("SUMMARY: pH PARTIAL-CORRELATION SENSITIVITY ANALYSIS")
print("="*110)
print()

for _, row in results_df.iterrows():
    ko_id = row['ko_id']
    metal = row['metal']
    rho_r = row['rho_raw']
    p_r = row['p_raw']
    q_r = row['q_raw']
    rho_p = row['rho_partial']
    p_p = row['p_partial']
    q_p = row['q_partial']
    n = row['n_after_ph_drop']

    # Format with significance markers
    sig_raw = "**" if (not np.isnan(q_r)) and q_r < 0.05 else "  "
    sig_partial = "**" if (not np.isnan(q_p)) and q_p < 0.05 else "  "

    if np.isnan(rho_r):
        print(f"{ko_id:8s} × {metal:3s}  |  "
              f"rho_raw: NaN                              |  "
              f"rho_partial: NaN                           |  "
              f"n={n:3.0f}")
    else:
        print(f"{ko_id:8s} × {metal:3s}  |  "
              f"rho_raw: {rho_r:+.3f} (p={p_r:.4f}, q={q_r:.4f}) {sig_raw}  |  "
              f"rho_partial: {rho_p:+.3f} (p={p_p:.4f}, q={q_p:.4f}) {sig_partial}  |  "
              f"n={n:3.0f}")

print()
print("** = FDR-significant at q < 0.05")
print()

# Count survival
n_sig_raw = (results_df['q_raw'] < 0.05).sum()
n_sig_partial = (results_df['q_partial'] < 0.05).sum()

print(f"Raw signal: {n_sig_raw}/6 pairs FDR-significant")
print(f"After pH adjustment: {n_sig_partial}/6 pairs FDR-significant")
print()

if n_sig_partial < n_sig_raw:
    print("✓ RESULT: pH adjustment attenuates signal → supports pH/redox confound hypothesis")
elif n_sig_partial == n_sig_raw:
    if n_sig_raw == 0:
        print("~ RESULT: No significant pairs in either test")
    else:
        print("~ RESULT: Signal robust to pH adjustment → pH not primary confound")
else:
    print("✗ RESULT: More pairs sig after adjustment (unexpected)")

print()
print(f"Saving to: {OUT_PATH}")
results_df.to_csv(OUT_PATH, index=False)
print("✓ Done")

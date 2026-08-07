#!/usr/bin/env python3
"""
Test whether the CURATED 7-KO cofactor signal survives joint housekeeping control.

The manuscript H4c used the EXPANDED 47-KO cofactor_per_mb (n=842) and found
the cofactor signal dies (p=0.264). But the curated 7-KO set has β=−0.033
(3× stronger than expanded β=−0.011). This script tests the curated set
in the same joint model.

Model: B_std ~ ne_cofactor_z + translation_z + replication_repair_z + gsize_z
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import sys
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path('data')
TREE = str(DATA / 'gtdb_bac_genus_pruned.tree')

sys.path.insert(0, str(Path('scripts')))
from pgls_utils import run_pgls

def _z(s):
    v = s.dropna()
    if len(v) < 5 or v.std() == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - v.mean()) / v.std()

# Load base dataset
df = pd.read_csv(DATA / 'soil_sample_pgls_dataset.csv')
ne = pd.read_csv(DATA / 'non_exclusive_category_densities.csv')

# Merge curated cofactor
df = df.merge(ne[['genus_lower', 'ne_cofactor_z', 'ne_resistance_z']], on='genus_lower', how='left')

# Ensure z-scores
df['gsize_z'] = _z(df['mean_genome_mb'])
ne_idx = ne.set_index('genus_lower')
df['curated_cofactor_z'] = _z(pd.Series(ne_idx['ne_cofactor_z'].reindex(df['genus_lower']).values, index=df.index))
df['curated_resistance_z'] = _z(pd.Series(ne_idx['ne_resistance_z'].reindex(df['genus_lower']).values, index=df.index))
df['translation_z'] = _z(df['translation_per_mb'])
df['replication_repair_z'] = _z(df['replication_repair_per_mb'])

mask = (df['curated_cofactor_z'].notna() &
        df['translation_z'].notna() &
        df['replication_repair_z'].notna() &
        df['gsize_z'].notna() &
        df['mean_levins_B_std'].notna())
print(f"n genera with all predictors: {mask.sum()}")

# Model 1: Curated cofactor alone (reference)
print("\n=== Model 1: B_std ~ curated_cofactor_z + gsize_z ===")
r1 = run_pgls(df, TREE, 'mean_levins_B_std', ['curated_cofactor_z', 'gsize_z'],
              taxon_col='genus_lower', label='curated_cofactor_alone', min_n=30)
if r1:
    b = r1['betas']['curated_cofactor_z']
    se = r1['SEs']['curated_cofactor_z']
    p = r1['p_values']['curated_cofactor_z']
    print(f"  cofactor: β={b:.4f}, SE={se:.4f}, p={p:.4e}")
    print(f"  n={r1['n']}, λ={r1['lambda_est']:.3f}, R²={r1['r2']:.4f}")

# Model 2: Full housekeeping joint model with CURATED cofactor
print("\n=== Model 2: B_std ~ curated_cofactor_z + translation_z + replication_repair_z + gsize_z ===")
preds = ['curated_cofactor_z', 'translation_z', 'replication_repair_z', 'gsize_z']
r2 = run_pgls(df, TREE, 'mean_levins_B_std', preds,
              taxon_col='genus_lower', label='curated_cofactor_joint', min_n=30)
if r2:
    for pred in preds:
        b = r2['betas'][pred]
        se = r2['SEs'][pred]
        p = r2['p_values'][pred]
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '†' if p < 0.1 else 'NS'
        print(f"  {pred:30s}: β={b:+.4f}, SE={se:.4f}, p={p:.4e} {sig}")
    print(f"  n={r2['n']}, λ={r2['lambda_est']:.3f}, R²={r2['r2']:.4f}")

    # Attenuation
    b_alone = r1['betas']['curated_cofactor_z'] if r1 else np.nan
    b_joint = r2['betas']['curated_cofactor_z']
    atten = (1 - abs(b_joint) / abs(b_alone)) * 100 if b_alone != 0 else np.nan
    print(f"\n  Attenuation: {atten:.1f}% (from {b_alone:.4f} to {b_joint:.4f})")

# Model 3: For comparison, expanded cofactor in same joint model
print("\n=== Model 3 (comparison): B_std ~ expanded_cofactor_z + translation_z + replication_repair_z + gsize_z ===")
df['expanded_cofactor_z'] = _z(df['cofactor_per_mb'])
preds3 = ['expanded_cofactor_z', 'translation_z', 'replication_repair_z', 'gsize_z']
r3 = run_pgls(df, TREE, 'mean_levins_B_std', preds3,
              taxon_col='genus_lower', label='expanded_cofactor_joint', min_n=30)
if r3:
    for pred in preds3:
        b = r3['betas'][pred]
        se = r3['SEs'][pred]
        p = r3['p_values'][pred]
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '†' if p < 0.1 else 'NS'
        print(f"  {pred:30s}: β={b:+.4f}, SE={se:.4f}, p={p:.4e} {sig}")
    print(f"  n={r3['n']}, λ={r3['lambda_est']:.3f}, R²={r3['r2']:.4f}")

# Model 4: Curated cofactor + curated resistance + housekeeping
print("\n=== Model 4: B_std ~ curated_cofactor_z + curated_resistance_z + translation_z + replication_repair_z + gsize_z ===")
preds4 = ['curated_cofactor_z', 'curated_resistance_z', 'translation_z', 'replication_repair_z', 'gsize_z']
r4 = run_pgls(df, TREE, 'mean_levins_B_std', preds4,
              taxon_col='genus_lower', label='curated_split_joint', min_n=30)
if r4:
    for pred in preds4:
        b = r4['betas'][pred]
        se = r4['SEs'][pred]
        p = r4['p_values'][pred]
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '†' if p < 0.1 else 'NS'
        print(f"  {pred:30s}: β={b:+.4f}, SE={se:.4f}, p={p:.4e} {sig}")
    print(f"  n={r4['n']}, λ={r4['lambda_est']:.3f}, R²={r4['r2']:.4f}")

print("\nDONE.")

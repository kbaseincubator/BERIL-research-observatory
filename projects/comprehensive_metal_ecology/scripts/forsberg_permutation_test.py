#!/usr/bin/env python3
"""
Forsberg permutation test on RDA
Tests whether metal fraction is significantly different from pH+climate fraction
using scipy.stats permutation testing on RDA variance explained.

Hypothesis: Forsberg et al. claim that pH dominates over metals.
Claim being tested: metals unique R² (0.064) vs pH+climate unique R² (0.041)

Output: data/forsberg_permutation_results.csv
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from scipy import stats

DATA = Path('data')
CCP_DATA = Path('../community_composition_prediction/data')

print("=" * 70)
print("TASK C: Forsberg permutation test on RDA")
print("=" * 70)

# ── Load RDA input data ──────────────────────────────────────────────────────
print("\n── Loading RDA input data ────────────────────────────────────────────")

try:
    fm = pd.read_parquet(CCP_DATA / 'feature_matrix.parquet')
    print(f"✓ Feature matrix loaded: {fm.shape}")
    print(f"  Samples: {fm.shape[0]}, Genera: {fm.shape[1]}")
except Exception as e:
    print(f"ERROR: Could not load feature_matrix.parquet: {e}")
    sys.exit(1)

# CLR-transform the data (assuming it's already counts or CLR-ish)
X_clr = fm.values  # shape: (n_samples, n_genera)

# Load environmental covariates - try different paths
env_file = None
for candidate in [
    '../community_composition_prediction/data/environmental_covariates.csv',
    '../hybrid_metal_prediction/data/environmental_covariates.csv',
    'data/genome_env_covariates.csv',
    'data/genus_lat_env_covariates.csv',
]:
    cand_path = Path(candidate)
    if cand_path.exists():
        env_file = cand_path
        break

if env_file is None:
    print("ERROR: Could not find environmental_covariates file")
    print("Checked:")
    for candidate in [
        '../community_composition_prediction/data/environmental_covariates.csv',
        '../hybrid_metal_prediction/data/environmental_covariates.csv',
        'data/genome_env_covariates.csv',
        'data/genus_lat_env_covariates.csv',
    ]:
        print(f"  - {candidate}")
    sys.exit(1)

print(f"✓ Loading environmental data from: {env_file}")
env_df = pd.read_csv(env_file, index_col=0)
print(f"  Shape: {env_df.shape}")
print(f"  Columns: {env_df.columns.tolist()[:10]}")

# Align samples (try index-based first, then positional if needed)
common_idx = fm.index.intersection(env_df.index)
print(f"\n✓ Common samples (by index): {len(common_idx)}")

if len(common_idx) == 0:
    # Fall back to positional alignment - use first N rows of both
    print("  Index mismatch - using positional alignment (first N rows)")
    n_align = min(fm.shape[0], env_df.shape[0])
    X_clr = fm.iloc[:n_align].values
    X_env = env_df.iloc[:n_align].values
    print(f"✓ Aligned by position: {n_align} samples")
else:
    X_clr = fm.loc[common_idx].values
    X_env = env_df.loc[common_idx].values
    print(f"✓ Aligned by index: {len(common_idx)} samples")

# Drop rows with NaN values
valid_mask = ~(np.isnan(X_clr).any(axis=1) | np.isnan(X_env).any(axis=1))
X_clr = X_clr[valid_mask]
X_env = X_env[valid_mask]
print(f"\n✓ Dropped rows with NaN: {X_clr.shape[0]} samples remaining")

# Identify metal and pH+climate columns based on name patterns
# Expected: pH, Temp, Precip (or similar) for climate; Cu, Zn, Pb, Ni for metals
metal_cols = []
phclim_cols = []

for i, col in enumerate(env_df.columns):
    col_lower = col.lower()
    # Check for pH + climate patterns first (more specific)
    if any(p in col_lower for p in ['ph', 'temp', 'precip', 'precipitation']):
        phclim_cols.append(i)
    # Then metals (exact names)
    elif any(m in col_lower for m in ['_cu', '_zn', '_pb', '_ni', 'log_cu', 'log_zn', 'log_pb', 'log_ni']):
        metal_cols.append(i)

if len(metal_cols) == 0 or len(phclim_cols) == 0:
    print(f"WARNING: Could not auto-detect column groups")
    print(f"  Metal columns found: {len(metal_cols)}")
    print(f"  pH+Climate columns found: {len(phclim_cols)}")
    print(f"  All columns: {env_df.columns.tolist()}")
    # Try default assumption (last 4 are metals)
    if X_env.shape[1] >= 7:
        phclim_cols = list(range(3))
        metal_cols = list(range(3, min(7, X_env.shape[1])))
        print(f"  Using default: pH+climate={phclim_cols}, metals={metal_cols}")

print(f"\n✓ Metal columns: {[env_df.columns[i] for i in metal_cols]}")
print(f"✓ pH+Climate columns: {[env_df.columns[i] for i in phclim_cols]}")

# ── RDA implementation ───────────────────────────────────────────────────────
print("\n– RDA setup (via LinearRegression) –––––––––––––––––––––––––––––")

def rda_r2(Y, X):
    """Fraction of total variance in Y explained by X via linear regression."""
    if X.shape[1] == 0:
        return 0.0
    reg = LinearRegression().fit(X, Y)
    Y_hat = reg.predict(X)
    ss_res = ((Y - Y_hat)**2).sum()
    ss_tot = ((Y - Y.mean(axis=0))**2).sum()
    return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

X_metal  = X_env[:, metal_cols] if metal_cols else np.zeros((X_env.shape[0], 1))
X_phclim = X_env[:, phclim_cols] if phclim_cols else np.zeros((X_env.shape[0], 1))
X_all    = X_env

r2_all    = rda_r2(X_clr, X_all)
r2_metal  = rda_r2(X_clr, X_metal)
r2_phclim = rda_r2(X_clr, X_phclim)

print(f"\nVariance explained (R²):")
print(f"  All env vars:        {r2_all:.4f}")
print(f"  Metals only:         {r2_metal:.4f}")
print(f"  pH+climate only:     {r2_phclim:.4f}")

# ── Permutation test ────────────────────────────────────────────────────────
print("\n── Permutation test (n_perm=999) ––––––––––––––––––––––––––––")
print("Test: Are metals significantly different from pH+climate?")
print("Hypothesis (Forsberg): pH+climate > metals\n")

n_perm = 999
r2_metal_perm = np.zeros(n_perm)
r2_phclim_perm = np.zeros(n_perm)

np.random.seed(42)
for i in range(n_perm):
    # Permute rows of X_env
    perm_idx = np.random.permutation(X_env.shape[0])
    X_env_perm = X_env[perm_idx]

    X_metal_perm = X_env_perm[:, metal_cols] if metal_cols else np.zeros((X_env.shape[0], 1))
    X_phclim_perm = X_env_perm[:, phclim_cols] if phclim_cols else np.zeros((X_env.shape[0], 1))

    r2_metal_perm[i] = rda_r2(X_clr, X_metal_perm)
    r2_phclim_perm[i] = rda_r2(X_clr, X_phclim_perm)

    if (i + 1) % 200 == 0:
        print(f"  Completed {i + 1}/{n_perm} permutations")

# Compute p-values (one-tailed: observed > permuted)
p_metal = (r2_metal_perm >= r2_metal).sum() / (n_perm + 1)
p_phclim = (r2_phclim_perm >= r2_phclim).sum() / (n_perm + 1)

print(f"\nPermutation p-values:")
print(f"  Metals:      p = {p_metal:.4f} (observed R² = {r2_metal:.4f})")
print(f"  pH+climate:  p = {p_phclim:.4f} (observed R² = {r2_phclim:.4f})")

# ── Save results ────────────────────────────────────────────────────────────
res_df = pd.DataFrame({
    'test': ['Forsberg permutation'] * 2,
    'model': ['metals', 'pH+climate'],
    'r_squared': [r2_metal, r2_phclim],
    'permutation_pvalue': [p_metal, p_phclim],
    'n_permutations': [n_perm] * 2,
    'interpretation': [
        'Metals' if r2_metal > r2_phclim else 'pH+climate',
        'pH+climate' if r2_phclim > r2_metal else 'Metals'
    ]
})

res_df.to_csv(DATA / 'forsberg_permutation_results.csv', index=False)
print(f"\n✓ Saved -> data/forsberg_permutation_results.csv\n")

# ── Final summary ───────────────────────────────────────────────────────────
print("=" * 70)
print("FORSBERG TEST SUMMARY")
print("=" * 70)
print(f"\nN samples: {X_clr.shape[0]}")
print(f"N genera: {X_clr.shape[1]}")
print(f"N env vars: {X_env.shape[1]}")

print(f"\nVariance explained:")
print(f"  Metals R²:        {r2_metal:.4f}  (p_perm = {p_metal:.4f})")
print(f"  pH+climate R²:    {r2_phclim:.4f}  (p_perm = {p_phclim:.4f})")

if r2_metal > r2_phclim:
    print(f"\n⚠ Result: METALS > pH+climate (contradicts Forsberg hypothesis)")
    print(f"   Difference: {r2_metal - r2_phclim:.4f}")
else:
    print(f"\n✓ Result: pH+climate > metals (supports Forsberg hypothesis)")
    print(f"   Difference: {r2_phclim - r2_metal:.4f}")

print("=" * 70)
print("Done.\n")

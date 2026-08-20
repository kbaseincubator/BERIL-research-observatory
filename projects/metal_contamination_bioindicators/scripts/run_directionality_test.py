#!/usr/bin/env python3
"""
Directionality analysis: environment → microbiome (forward) vs
microbiome → environment (reverse) prediction strength.

Optimized version using sampling and faster computation.
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
import json
from pathlib import Path
from scipy.stats import spearmanr, rankdata
import warnings
warnings.filterwarnings('ignore')

DATA = Path(__file__).parent.parent / 'data'


def batch_spearmanr(y_vec, X_mat):
    """Batch Spearman correlation using rank-based method (very fast)."""
    n = len(y_vec)
    if n < 3:
        return np.full(X_mat.shape[1], np.nan)

    # Rank the data
    ry = rankdata(y_vec, nan_policy='propagate').astype(np.float64)
    rX = rankdata(X_mat, axis=0, nan_policy='propagate').astype(np.float64)

    # Remove NaNs
    valid = ~(np.isnan(ry) | np.isnan(rX).any(axis=1))
    if valid.sum() < 3:
        return np.full(X_mat.shape[1], np.nan)

    ry_valid = ry[valid]
    rX_valid = rX[valid]

    # Standardize
    ry_c = ry_valid - ry_valid.mean()
    rX_c = rX_valid - rX_valid.mean(axis=0)

    # Compute Pearson on ranks (= Spearman)
    numer = ry_c @ rX_c
    norm_y = np.sqrt((ry_c ** 2).sum())
    norm_X = np.sqrt((rX_c ** 2).sum(axis=0))

    denom = norm_y * norm_X
    denom[denom < 1e-10] = np.nan
    return numer / denom


def forward_direction_simple(X_env, clr_mat, genus_names, verbose=True):
    """
    Forward direction using Spearman correlation instead of RF.
    Much faster and still informative for directionality.
    """
    genus_rho = {}

    for g_idx, genus in enumerate(genus_names):
        if g_idx % 10 == 0 and verbose:
            print(f"  Forward: processing genus {g_idx+1}/{len(genus_names)}...")

        y = clr_mat[:, g_idx]
        valid = ~np.isnan(y)
        if valid.sum() < 50:
            genus_rho[genus] = np.nan
            continue

        # Use Spearman correlation between env and genus CLR
        # This gives us a correlation strength without the RF overhead
        y_valid = y[valid]
        X_valid = X_env[valid]

        # Get correlation with each env variable and take max
        rhos = []
        for j in range(X_env.shape[1]):
            rho, _ = spearmanr(X_valid[:, j], y_valid, nan_policy='omit')
            rhos.append(rho if not np.isnan(rho) else 0)

        # Use mean correlation as proxy for predictability
        genus_rho[genus] = np.mean([r for r in rhos if not np.isnan(r)])

    return genus_rho


def forward_direction_pc1(X_env, clr_mat, env_var_names, verbose=True):
    """
    Forward direction: correlation between env features and CLR PC1.
    Returns both the mean correlation and individual correlations.
    """
    # Compute PCA on CLR matrix
    from sklearn.decomposition import PCA

    valid_mask = ~np.isnan(clr_mat).any(axis=1)
    if valid_mask.sum() < 100:
        print("  Not enough valid samples for PC1")
        return np.nan, {}

    clr_valid = clr_mat[valid_mask]
    pca = PCA(n_components=1)
    pc1 = pca.fit_transform(clr_valid)[:, 0]

    print(f"  PC1 explains {pca.explained_variance_ratio_[0]:.1%} of variance")

    # Map back to full
    pc1_full = np.full(len(clr_mat), np.nan)
    pc1_full[valid_mask] = pc1

    # Correlation with each env feature
    rho_by_var = {}
    rhos = []
    for j, var_name in enumerate(sorted(env_var_names)):
        # Find valid pairs for this variable
        mask = ~(np.isnan(X_env[:, j]) | np.isnan(pc1_full))
        if mask.sum() < 3:
            rho_by_var[var_name] = np.nan
            continue

        rho, _ = spearmanr(X_env[mask, j], pc1_full[mask], nan_policy='omit')
        rho_by_var[var_name] = rho
        if not np.isnan(rho):
            rhos.append(rho)

    # Return mean correlation and per-variable dict
    mean_rho = np.mean(rhos) if rhos else np.nan
    return mean_rho, rho_by_var


def reverse_direction_from_file(verbose=True):
    """Load pre-computed reverse direction results."""
    rho_df = pd.read_parquet(DATA / 'usa_rf_env_targets_rho.parquet')
    rho_clr = rho_df[rho_df['feature_set'] == 'clr_only'].copy()

    rev_rho = {}
    for _, row in rho_clr.iterrows():
        rev_rho[row['target']] = row['spearman_rho']

    if verbose:
        print(f"  Loaded {len(rev_rho)} reverse direction values")

    return rev_rho


# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data...")
mat = pd.read_parquet(DATA / 'analysis_matrix.parquet')
redox = pd.read_parquet(DATA / 'redox_proxy.parquet',
                        columns=['sample_id', 'p_oxic_5m_proxy'])
mwas = pd.read_parquet(DATA / 'mwas_results.parquet')
cov = pd.read_parquet(DATA / 'sample_covariates.parquet',
                      columns=['sample_id', 'study_id'])

print(f"  analysis_matrix: {mat.shape[0]:,} samples × {mat.shape[1]} columns")
print(f"  redox_proxy: {redox.shape}")
print(f"  mwas_results: {mwas.shape[0]:,} results")

# Filter to USA
print("\nFiltering to USA (lat 24-50, lon -130 to -65)...")
usa = mat[(mat['lat'] >= 24) & (mat['lat'] <= 50) &
          (mat['lon'] >= -130) & (mat['lon'] <= -65)].copy()
print(f"  USA samples: {len(usa):,}")

# Merge
usa = usa.merge(redox, on='sample_id', how='left')
usa = usa.merge(cov, on='sample_id', how='left')
print(f"  After merges: {len(usa):,}")

# ── Build environment feature matrix ──────────────────────────────────────────
print("\nBuilding environment feature matrix...")

env_vars = {
    'sg_pH': 'sg_pH',
    'sg_clay': 'sg_clay',
    'log_sg_SOC': lambda df: np.log(df['sg_SOC'].fillna(0.01) + 0.01),
    'lat': 'lat',
    'lon': 'lon',
    'p_oxic_5m_proxy': 'p_oxic_5m_proxy',
    's25_as_AT': 's25_as_AT',
    's25_cr_AT': 's25_cr_AT',
    's25_ni_AT': 's25_ni_AT',
}

X_env_data = {}
for name, col in env_vars.items():
    if callable(col):
        X_env_data[name] = col(usa).to_numpy()
    else:
        X_env_data[name] = usa[col].to_numpy()

# Standardize
for name in X_env_data:
    arr = X_env_data[name].copy()
    valid = ~np.isnan(arr)
    if valid.sum() > 0:
        mean = arr[valid].mean()
        std = arr[valid].std()
        if std > 0:
            arr[valid] = (arr[valid] - mean) / std
    arr[np.isnan(arr)] = 0
    X_env_data[name] = arr

X_env = np.column_stack([X_env_data[name] for name in sorted(env_vars.keys())])
env_var_names = sorted(env_vars.keys())

print(f"  X_env shape: {X_env.shape}")
print(f"  Env variables: {env_var_names}")

# ── Extract top-40 MWAS genera ────────────────────────────────────────────────
print("\nExtracting top-40 MWAS genera...")
top40_genera = mwas.nlargest(40, 'weighted_rho')['genus'].unique().tolist()

clr_cols = [f'clr_{g}' for g in top40_genera]
clr_cols_exist = [c for c in clr_cols if c in usa.columns]
print(f"  {len(clr_cols_exist)} CLR columns available")

clr_mat = usa[clr_cols_exist].to_numpy(dtype=np.float64)
genus_names_exist = [c.replace('clr_', '') for c in clr_cols_exist]

print(f"  CLR matrix: {clr_mat.shape}")

# ── FORWARD direction ─────────────────────────────────────────────────────────
print("\n" + "="*70)
print("FORWARD DIRECTION: environment → microbiome")
print("="*70)

print("\n(1) Env → individual genus CLR:")
forward_genus_rho = forward_direction_simple(X_env, clr_mat, genus_names_exist,
                                             verbose=True)

valid_forward = {g: r for g, r in forward_genus_rho.items() if not np.isnan(r)}
if valid_forward:
    rhos = np.array(list(valid_forward.values()))
    print(f"\n  Mean forward correlation: {rhos.mean():.3f}")
    print(f"  Median: {np.median(rhos):.3f}, Std: {rhos.std():.3f}")
    print(f"  Range: [{rhos.min():.3f}, {rhos.max():.3f}]")

print("\n(2) Env → CLR PC1:")
forward_pc1_rho, forward_pc1_by_var = forward_direction_pc1(X_env, clr_mat, env_var_names, verbose=True)
print(f"  Mean forward correlation (env → PC1): {forward_pc1_rho:.3f}")
print(f"\n  Per-variable correlations (env → PC1):")
for var_name in sorted(env_var_names):
    rho = forward_pc1_by_var.get(var_name, np.nan)
    print(f"    {var_name:25s}: ρ = {rho:7.3f}")

# ── REVERSE direction ─────────────────────────────────────────────────────────
print("\n" + "="*70)
print("REVERSE DIRECTION: microbiome → environment (from file)")
print("="*70)
reverse_env_rho = reverse_direction_from_file(verbose=True)

# ── Asymmetry analysis ────────────────────────────────────────────────────────
print("\n" + "="*70)
print("ASYMMETRY ANALYSIS")
print("="*70)

env_var_group = {
    'sg_pH': 'Soil',
    'sg_clay': 'Soil',
    'log_sg_SOC': 'Soil',
    'lat': 'Geographic',
    'lon': 'Geographic',
    'p_oxic_5m_proxy': 'Redox',
    's25_as_AT': 'Metals',
    's25_cr_AT': 'Metals',
    's25_ni_AT': 'Metals',
}

asymmetry_by_var = {}

print("\nPer-variable asymmetry (forward env → PC1 vs reverse CLR → env):")
print(f"{'Variable':<20} {'Forward ρ':>12} {'Reverse ρ':>12} {'Index':>10} {'Group':<12}")
print("-" * 70)

for var_name in sorted(env_var_names):
    # Use the individual forward correlation for this variable (not the mean)
    forward_rho = forward_pc1_by_var.get(var_name, np.nan)
    reverse_rho = reverse_env_rho.get(var_name, np.nan)

    if not np.isnan(forward_rho) and not np.isnan(reverse_rho):
        denom = forward_rho + reverse_rho
        if abs(denom) > 1e-10:
            index = (forward_rho - reverse_rho) / denom
        else:
            index = np.nan
    else:
        index = np.nan

    group = env_var_group.get(var_name, 'Unknown')

    asymmetry_by_var[var_name] = {
        'forward': float(forward_rho) if not np.isnan(forward_rho) else None,
        'reverse': float(reverse_rho) if not np.isnan(reverse_rho) else None,
        'directionality_index': float(index) if not np.isnan(index) else None,
        'group': group
    }

    print(f"{var_name:<20} {forward_rho:>12.3f} {reverse_rho:>12.3f} "
          f"{index:>10.3f} {group:<12}")

# ── Group summary ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("GROUP SUMMARY")
print("="*70)

group_summary = {}
for group_name in set(env_var_group.values()):
    vars_in_group = [v for v, g in env_var_group.items() if g == group_name]

    forward_vals = [asymmetry_by_var[v]['forward'] for v in vars_in_group
                    if asymmetry_by_var[v]['forward'] is not None]
    reverse_vals = [asymmetry_by_var[v]['reverse'] for v in vars_in_group
                    if asymmetry_by_var[v]['reverse'] is not None]
    index_vals = [asymmetry_by_var[v]['directionality_index'] for v in vars_in_group
                  if asymmetry_by_var[v]['directionality_index'] is not None]

    if forward_vals and reverse_vals:
        group_summary[group_name] = {
            'mean_forward': float(np.mean(forward_vals)),
            'mean_reverse': float(np.mean(reverse_vals)),
            'mean_directionality_index': float(np.mean(index_vals)) if index_vals else None,
            'n_variables': len(vars_in_group)
        }

print(f"{'Group':<15} {'Mean Forward ρ':>15} {'Mean Reverse ρ':>15} {'Index':>10}")
print("-" * 60)
for group, summary in sorted(group_summary.items()):
    fwd = summary['mean_forward']
    rev = summary['mean_reverse']
    idx = summary.get('mean_directionality_index', np.nan)
    print(f"{group:<15} {fwd:>15.3f} {rev:>15.3f} {idx:>10.3f}")

# ── Per-genus analysis ────────────────────────────────────────────────────────
print("\n" + "="*70)
print("PER-GENUS ANALYSIS")
print("="*70)

mean_reverse_all = np.mean([v for v in reverse_env_rho.values()
                            if not np.isnan(v)])

print(f"\nMean reverse (across all env vars): {mean_reverse_all:.3f}")
print(f"\nTop 20 genera by forward correlation:")
print(f"{'Genus':<30} {'Forward ρ':>12} {'Index':>10}")
print("-" * 55)

sorted_genera = sorted(forward_genus_rho.items(),
                       key=lambda x: x[1] if not np.isnan(x[1]) else -np.inf,
                       reverse=True)

genus_asymmetry = {}
for genus, forward_rho in sorted_genera[:20]:
    if np.isnan(forward_rho):
        continue

    denom = forward_rho + mean_reverse_all
    if abs(denom) > 1e-10:
        index = (forward_rho - mean_reverse_all) / denom
    else:
        index = np.nan

    genus_asymmetry[genus] = {
        'forward': float(forward_rho),
        'index': float(index) if not np.isnan(index) else None
    }

    print(f"{genus:<30} {forward_rho:>12.3f} {index:>10.3f}")

# ── Write output ──────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("WRITING OUTPUT")
print("="*70)

output = {
    'metadata': {
        'n_samples': int(len(usa)),
        'env_variables': env_var_names,
        'correlation_method': 'Spearman rank',
        'notes': 'Forward direction uses Spearman correlation (not RF) for computational efficiency'
    },
    'forward_rho': {g: (float(r) if not np.isnan(r) else None)
                    for g, r in forward_genus_rho.items()},
    'community_pc1_forward': float(forward_pc1_rho) if not np.isnan(forward_pc1_rho) else None,
    'reverse_rho': {var: (float(rho) if not np.isnan(rho) else None)
                    for var, rho in reverse_env_rho.items()},
    'asymmetry_by_var': asymmetry_by_var,
    'group_summary': group_summary,
    'genus_asymmetry': genus_asymmetry
}

output_path = DATA / 'directionality_results.json'
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Saved to {output_path}")

# ── Print interpretation ──────────────────────────────────────────────────────
print("\n" + "="*70)
print("INTERPRETATION")
print("="*70)

pc1_forward = output['community_pc1_forward']
print(f"\nCommunity (PC1) level:")
print(f"  Env → PC1 (forward):  ρ = {pc1_forward:.3f}")
print(f"  PC1 → env (reverse):  ρ_mean = {mean_reverse_all:.3f}")

if pc1_forward > mean_reverse_all:
    print(f"  ➜ ENVIRONMENT DRIVES MICROBIOME")
    print(f"    (forward > reverse: {pc1_forward:.3f} > {mean_reverse_all:.3f})")
else:
    print(f"  ➜ MICROBIOME REFLECTS ENVIRONMENT")
    print(f"    (reverse > forward: {mean_reverse_all:.3f} > {pc1_forward:.3f})")

print("\nVariable type asymmetries:")
for group, summary in sorted(group_summary.items()):
    fwd = summary['mean_forward']
    rev = summary['mean_reverse']
    if fwd > rev:
        print(f"  {group:>12}: environment dominant (Δ = {fwd - rev:+.3f})")
    else:
        print(f"  {group:>12}: microbiome-reflective (Δ = {fwd - rev:+.3f})")

print("\nDone.")

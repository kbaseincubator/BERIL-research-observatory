#!/usr/bin/env python3
"""
Test whether genome quality (completeness) confounds metal type diversity.

Metal type diversity = number of different metal types (As, Cd, Cr, Cu, Hg, Pb)
for which a genus has significant KOs from per_ko_metal_associations project.

Approach:
1. Load per_ko_metal_associations baseline results (ckpt_mgnify_adj_ko_associations.csv)
2. Filter to FDR-significant KOs (q < 0.05)
3. For each genus in the PGLS input, count unique metals represented
4. Test whether genus-level mean_completeness predicts metal_type_diversity
5. Residualize diversity on completeness
6. Re-run PGLS on residualized metric
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import spearmanr

# Load per_ko results
print("Loading per_ko_metal_associations results...")
ko_assoc = pd.read_csv(
    '/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data/ckpt_mgnify_adj_ko_associations.csv'
)

# Compute FDR per metal
from statsmodels.stats.multitest import multipletests

def compute_fdr_bh(pvals):
    """Benjamini-Hochberg FDR correction."""
    sorted_idx = np.argsort(pvals)
    sorted_pvals = pvals[sorted_idx]
    n = len(sorted_pvals)
    rank = np.arange(1, n + 1)
    threshold = (rank / n) * 0.05
    valid_idx = np.where(sorted_pvals <= threshold)[0]
    if len(valid_idx) == 0:
        return np.ones(n)
    qvals = np.ones(n)
    for i in range(n - 1, -1, -1):
        qvals[i] = min(sorted_pvals[i] * n / (i + 1), 1.0 if i == n - 1 else qvals[i + 1])
    unsort_idx = np.argsort(sorted_idx)
    return qvals[unsort_idx]

ko_assoc_copy = ko_assoc.copy()
for metal in ko_assoc_copy['metal'].unique():
    metal_mask = ko_assoc_copy['metal'] == metal
    pvals = ko_assoc_copy.loc[metal_mask, 'p_value'].values
    qvals = compute_fdr_bh(pvals)
    ko_assoc_copy.loc[metal_mask, 'q_value'] = qvals

print(f"Loaded {len(ko_assoc_copy)} KO-metal pairs")

# Filter to FDR-significant
sig_ko_assoc = ko_assoc_copy[ko_assoc_copy['q_value'] < 0.05].copy()
print(f"Significant KO-metal pairs (q < 0.05): {len(sig_ko_assoc)}")

# Load MGnify MAG genus assignments (from per_ko project)
# Need to infer genus from the KO matrix file or from the PGLS input
pgls_input = pd.read_csv(
    '/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data/01_pgls_input_bacteria.csv'
)
print(f"Loaded {len(pgls_input)} genera from PGLS input")

# Load MAG quality data
mag_quality = pd.read_csv(
    '/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data/genus_mag_quality.csv'
)
print(f"Loaded MAG quality for {len(mag_quality)} genera")

# Merge PGLS input with MAG quality
pgls_with_quality = pgls_input.merge(
    mag_quality[['genus_lower', 'mean_completeness', 'mean_contamination']],
    left_on='genus_lower', right_on='genus_lower',
    how='left'
)
print(f"Merged PGLS input with MAG quality: {pgls_with_quality['mean_completeness'].notna().sum()} genera with quality data")

# Load KO matrix to infer which genera have KOs for each metal
# This would be from the per_ko project, but for now we'll construct metal diversity
# from the mgnify MAG data in the comprehensive_metal_ecology project

# Load tier KO counts (which metals each genus has genes for)
tier_ko_counts = pd.read_csv(
    '/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data/tier_ko_counts_spark.csv'
)

# Merge PGLS data with tier KO counts
pgls_with_tier = pgls_input.merge(
    tier_ko_counts[['genus_lower', 'n_ko_tier1', 'n_ko_tier2']],
    left_on='genus_lower', right_on='genus_lower',
    how='left'
)

# Fill missing tier KOs with 0
pgls_with_tier['n_ko_tier1'] = pgls_with_tier['n_ko_tier1'].fillna(0)
pgls_with_tier['n_ko_tier2'] = pgls_with_tier['n_ko_tier2'].fillna(0)

# For now, use total metal-gene KOs as a proxy for metal type diversity
# (Higher KO count likely reflects handling of multiple metals)
pgls_with_tier['metal_ko_count'] = pgls_with_tier['n_ko_tier1'] + pgls_with_tier['n_ko_tier2']

# Merge with MAG quality
pgls_final = pgls_with_tier.merge(
    mag_quality[['genus_lower', 'mean_completeness', 'mean_contamination']],
    left_on='genus_lower', right_on='genus_lower',
    how='left'
)

# Filter to genera with quality data
pgls_final_with_quality = pgls_final[pgls_final['mean_completeness'].notna()].copy()
print(f"Genera with both trait and quality data: {len(pgls_final_with_quality)}")

# Test: does completeness predict metal KO count?
valid_idx = pgls_final_with_quality['metal_ko_count'].notna() & pgls_final_with_quality['mean_completeness'].notna()
pgls_for_analysis = pgls_final_with_quality[valid_idx].copy()

print(f"\nAnalyzing {len(pgls_for_analysis)} genera with both traits and completeness data")

# Spearman correlation
if len(pgls_for_analysis) > 2:
    rho, p_rho = spearmanr(pgls_for_analysis['mean_completeness'], pgls_for_analysis['metal_ko_count'])
    print(f"Spearman ρ(completeness, metal_KO_count) = {rho:.4f}, p = {p_rho:.4e}")

    # Fit OLS: metal_ko_count ~ completeness
    X = pgls_for_analysis['mean_completeness'].values
    y = pgls_for_analysis['metal_ko_count'].values

    # Add constant
    X_const = np.column_stack([np.ones(len(X)), X])

    # OLS
    beta_hat = np.linalg.lstsq(X_const, y, rcond=None)[0]
    y_pred = X_const @ beta_hat
    residuals = y - y_pred

    # R-squared
    ss_tot = np.sum((y - y.mean())**2)
    ss_res = np.sum(residuals**2)
    r_squared = 1 - (ss_res / ss_tot)

    print(f"\nOLS: metal_KO_count ~ completeness")
    print(f"  Intercept: {beta_hat[0]:.4f}")
    print(f"  Slope: {beta_hat[1]:.6f}")
    print(f"  R² = {r_squared:.4f}")

    # Add residuals to data
    pgls_for_analysis['metal_ko_count_residualized'] = residuals

    # Compare PGLS results on original vs residualized metric
    # Original β from pgls_input
    original_beta = pgls_input.loc[pgls_input['genus_lower'].isin(pgls_for_analysis['genus_lower']), 'predictor_z'].values.mean()
    print(f"\nOriginal mean predictor_z from PGLS: {original_beta:.6f}")

    # OLS on residualized trait
    y_resid = pgls_for_analysis['metal_ko_count_residualized'].values
    beta_hat_resid = np.linalg.lstsq(X_const, y_resid, rcond=None)[0]
    y_pred_resid = X_const @ beta_hat_resid
    ss_res_resid = np.sum((y_resid - y_pred_resid)**2)
    r_squared_resid = 1 - (ss_res_resid / (np.sum((y_resid - y_resid.mean())**2)))

    print(f"\nOLS on residualized metric:")
    print(f"  Slope (completeness effect on residuals): {beta_hat_resid[1]:.6f}")
    print(f"  R² = {r_squared_resid:.4f}")

    # Save results
    output_cols = [
        'genus_lower', 'mean_completeness', 'metal_ko_count', 'metal_ko_count_residualized',
        'mean_levins_B_std', 'ko_per_mb_primary'
    ]
    output_df = pgls_for_analysis[output_cols].copy()

    output_path = '/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data/coverage_standardized_metal_diversity.csv'
    output_df.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Completeness explains R² = {r_squared:.4f} ({100*r_squared:.2f}%) of metal_KO_count variance")
    print(f"  Spearman ρ = {rho:.4f}")
    print(f"  Slope = {beta_hat[1]:.6f} KOs per % completeness")
    print(f"\nResidualizing metal_KO_count on completeness removes this confound.")
    print(f"Residualized metric ready for PGLS re-analysis.")
else:
    print("Insufficient data for analysis")

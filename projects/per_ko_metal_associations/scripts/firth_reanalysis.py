#!/usr/bin/env python3
"""
Firth's penalized logistic regression on 69 SPIRE KO-metal pairs.
Corrects for quasi-complete separation bias in standard logistic regression.

Usage:
    cd /home/hmacgregor/BERIL-research-observatory
    python3 projects/per_ko_metal_associations/scripts/firth_reanalysis.py
"""

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm
from pathlib import Path
import sys

# IQR values for the 6 metals
IQR_VALUES = {
    'As': 0.041,
    'Cd': 0.088,
    'Cr': 0.077,
    'Cu': 0.028,
    'Hg': 0.093,
    'Pb': 0.032,
}

# Metal name mapping: short name -> PF1 column
METAL_COL_MAP = {
    'As': 'PF1_As',
    'Cd': 'PF1_Cd',
    'Cr': 'PF1_Cr',
    'Cu': 'PF1_Cu',
    'Hg': 'PF1_Hg',
    'Pb': 'PF1_Pb',
}


def firth_logistic(X, y, max_iter=250, tol=1e-7):
    """
    Firth's penalized logistic regression.

    Modifies the score (gradient) by adding Jeffrey's prior penalty,
    which removes first-order bias and provides better estimates
    for quasi-separated data.

    Args:
        X: design matrix (n x p), should include intercept column as first column
        y: binary outcome (n,)
        max_iter: maximum iterations
        tol: convergence tolerance

    Returns:
        beta: coefficient estimates (p,)
        se: standard errors (p,)
        pvalues: two-tailed p-values (p,)
    """
    n, p = X.shape
    beta = np.zeros(p)

    for iteration in range(max_iter):
        eta = X @ beta
        pi = expit(eta)

        # Weights from logistic model
        W = pi * (1 - pi)  # (n,)

        # Fisher information matrix: X'WX
        XtW = X.T * W  # (p x n) — broadcasts W across rows
        XtWX = XtW @ X  # (p x p)

        # Hat matrix diagonal
        # h_i = w_i * x_i' (X'WX)^{-1} x_i
        try:
            XtWX_inv = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        except np.linalg.LinAlgError:
            print(f"    Warning: singular Fisher information at iteration {iteration}")
            break

        # Efficient computation of hat diagonal
        # h = diag(X * W^{1/2} (X'WX)^{-1} W^{1/2} X')
        # = row-wise sum of (X * sqrt(W)[:, None]) * (X @ XtWX_inv) * sqrt(W)
        sqW = np.sqrt(W)
        XsqW = X * sqW[:, None]  # (n x p)
        H_diag = np.sum(XsqW * (XsqW @ XtWX_inv), axis=1)  # (n,)

        # Firth's modified score: U = X'(y - pi + h*(0.5 - pi))
        adj_resid = y - pi + H_diag * (0.5 - pi)
        score = X.T @ adj_resid

        # Newton-Raphson step
        try:
            delta = np.linalg.solve(XtWX + np.eye(p) * 1e-10, score)
        except np.linalg.LinAlgError:
            print(f"    Warning: singular system at iteration {iteration}")
            break

        beta_new = beta + delta

        # Check convergence
        if np.max(np.abs(delta)) < tol:
            beta = beta_new
            break
        beta = beta_new

    # Compute final standard errors from Fisher information
    eta = X @ beta
    pi = expit(eta)
    W = pi * (1 - pi)
    XtWX = (X.T * W) @ X

    try:
        cov = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        print(f"    Warning: could not invert final Fisher information")
        se = np.full(p, np.nan)

    # Two-tailed p-values
    z = beta / se
    pvalues = 2 * (1 - norm.cdf(np.abs(z)))

    return beta, se, pvalues


def benjamini_hochberg(pvalues, alpha=0.05):
    """Compute Benjamini-Hochberg FDR-adjusted q-values."""
    n = len(pvalues)
    if n == 0:
        return np.array([])

    # Sort p-values and get indices
    sorted_idx = np.argsort(pvalues)
    sorted_p = pvalues[sorted_idx]

    # Compute critical values: (i / n) * alpha, where i = 1, 2, ..., n
    i = np.arange(1, n + 1)
    crit = (i / n) * alpha

    # Find largest i where p_i <= (i/n)*alpha
    mask = sorted_p <= crit
    if np.any(mask):
        threshold = sorted_p[np.where(mask)[0][-1]]
    else:
        threshold = 0

    # Compute q-values: min_{j >= i} (n/j * p_j)
    qvalues = np.ones(n)
    for i in range(n - 1, -1, -1):
        qvalues[i] = min(n / (i + 1) * sorted_p[i], qvalues[i + 1] if i < n - 1 else 1.0)

    # Unsort to match original order
    q_out = np.empty(n)
    q_out[sorted_idx] = qvalues
    return q_out


def main():
    # Paths
    repo_root = Path('/home/hmacgregor/BERIL-research-observatory')
    data_dir = repo_root / 'projects' / 'per_ko_metal_associations' / 'data'

    # Load data
    print("Loading SPIRE matrix...")
    matrix = pd.read_parquet(data_dir / 'spire_all_ko_matrix.parquet')

    print("Loading target pairs...")
    targets = pd.read_csv(data_dir / 'spire_total_vs_direct_effects.csv')

    # Get all unique genomes with metadata
    print("Building genome reference...")
    all_genomes = matrix.drop_duplicates('genome_id')[
        ['genome_id', 'genome_size', 'latitude', 'longitude', 'PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb', 'sg_pH']
    ].reset_index(drop=True)

    print(f"  Total genomes: {len(all_genomes)}")

    # Compute log_n_mags_site: MAGs per sampling site
    print("Computing log(n_mags_per_site)...")
    all_genomes['lat_r'] = all_genomes['latitude'].round(2)
    all_genomes['lon_r'] = all_genomes['longitude'].round(2)
    site_counts = all_genomes.groupby(['lat_r', 'lon_r'])['genome_id'].count().reset_index()
    site_counts.columns = ['lat_r', 'lon_r', 'n_mags_site']
    all_genomes = all_genomes.merge(site_counts, on=['lat_r', 'lon_r'], how='left')
    all_genomes['log_n_mags_site'] = np.log(all_genomes['n_mags_site'].fillna(1).astype(float))
    print(f"  Sites with MAGs: {len(site_counts)}")

    # Create KO presence sets for fast lookup
    print("Building KO presence lookup...")
    ko_present_sets = {}
    for ko_id in matrix['ko_id'].unique():
        ko_present_sets[ko_id] = set(matrix[matrix['ko_id'] == ko_id]['genome_id'].values)

    print(f"  Indexed {len(ko_present_sets)} KOs")

    # Process each KO-metal pair
    results = []
    n_pairs = len(targets)

    print(f"\nProcessing {n_pairs} KO-metal pairs...")

    for idx, row in targets.iterrows():
        ko_id = row['ko_id']
        metal_short = row['metal']
        metal_col = METAL_COL_MAP[metal_short]
        iqr = IQR_VALUES[metal_short]

        if (idx + 1) % 10 == 0:
            print(f"  [{idx + 1}/{n_pairs}] {ko_id} x {metal_short}")

        # Get genomes with this KO
        present_ids = ko_present_sets.get(ko_id, set())

        # Model 1 (total): filter to genomes with non-null metal only
        genomes_total = all_genomes[
            all_genomes[metal_col].notna()
        ].copy()

        if len(genomes_total) == 0:
            print(f"    ERROR: No valid genomes for {ko_id} x {metal_short}")
            continue

        # Model 2 (direct): additionally filter to non-null pH
        genomes_direct = genomes_total[
            genomes_total['sg_pH'].notna()
        ].copy()

        if len(genomes_direct) == 0:
            print(f"    ERROR: No genomes with pH for {ko_id} x {metal_short}")
            continue

        # Binary outcomes
        y_total = genomes_total['genome_id'].isin(present_ids).astype(int).values
        y_direct = genomes_direct['genome_id'].isin(present_ids).astype(int).values

        n_present_total = np.sum(y_total)
        n_total = len(y_total)
        n_present_direct = np.sum(y_direct)
        n_direct = len(y_direct)

        if n_present_total == 0 or n_present_total == n_total:
            print(f"    ERROR: Complete separation in total model for {ko_id} x {metal_short}")
            continue

        if n_present_direct == 0 or n_present_direct == n_direct:
            print(f"    ERROR: Complete separation in direct model for {ko_id} x {metal_short}")
            continue

        # Prepare X for baseline model: intercept + metal + log_gs + log_n_mags_site
        X_total = np.column_stack([
            np.ones(n_total),
            genomes_total[metal_col].values,
            np.log(genomes_total['genome_size'].values),
            genomes_total['log_n_mags_site'].values,
        ])

        # Prepare X for pH-adjusted model: intercept + metal + log_gs + sg_pH + log_n_mags_site
        X_direct = np.column_stack([
            np.ones(n_direct),
            genomes_direct[metal_col].values,
            np.log(genomes_direct['genome_size'].values),
            genomes_direct['sg_pH'].values,
            genomes_direct['log_n_mags_site'].values,
        ])

        # Run Firth's method for both models
        try:
            beta_firth_total, se_firth_total, p_firth_total = firth_logistic(X_total, y_total)
            beta_firth_direct, se_firth_direct, p_firth_direct = firth_logistic(X_direct, y_direct)
        except Exception as e:
            print(f"    ERROR in Firth for {ko_id} x {metal_short}: {e}")
            continue

        # Extract metal coefficients (index 1, after intercept)
        # Use pre-computed standard logistic estimates from targets table
        beta_std_total = row['beta_total']
        beta_std_direct = row['beta_direct']

        result = {
            'ko_id': ko_id,
            'metal': metal_short,
            'beta_firth_total': beta_firth_total[1],
            'se_firth_total': se_firth_total[1],
            'p_firth_total': p_firth_total[1],
            'or_iqr_firth_total': np.exp(beta_firth_total[1] * iqr),
            'beta_firth_direct': beta_firth_direct[1],
            'se_firth_direct': se_firth_direct[1],
            'p_firth_direct': p_firth_direct[1],
            'or_iqr_firth_direct': np.exp(beta_firth_direct[1] * iqr),
            'beta_std_total': beta_std_total,
            'beta_std_direct': beta_std_direct,
            'n_present': n_present_total,
            'n_total_base': n_total,
            'n_total_direct': n_direct,
            'beta_nmags': beta_firth_total[3],  # log_n_mags_site coefficient (index 3 in total model)
            'p_nmags': p_firth_total[3],        # its p-value
        }
        results.append(result)

    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    print(f"\nSuccessfully processed {len(results_df)} pairs")

    # Apply BH-FDR correction per metal, separately for total and direct
    metals = results_df['metal'].unique()

    print(f"\nApplying BH-FDR correction...")
    results_df['q_firth_total'] = np.nan
    results_df['q_firth_direct'] = np.nan

    for metal in metals:
        metal_mask = results_df['metal'] == metal

        # Total model
        p_vals_total = results_df.loc[metal_mask, 'p_firth_total'].values
        q_vals_total = benjamini_hochberg(p_vals_total)
        results_df.loc[metal_mask, 'q_firth_total'] = q_vals_total

        # Direct model
        p_vals_direct = results_df.loc[metal_mask, 'p_firth_direct'].values
        q_vals_direct = benjamini_hochberg(p_vals_direct)
        results_df.loc[metal_mask, 'q_firth_direct'] = q_vals_direct

    # Reorder columns
    results_df = results_df[[
        'ko_id', 'metal',
        'beta_firth_total', 'se_firth_total', 'p_firth_total', 'q_firth_total', 'or_iqr_firth_total',
        'beta_firth_direct', 'se_firth_direct', 'p_firth_direct', 'q_firth_direct', 'or_iqr_firth_direct',
        'beta_std_total', 'beta_std_direct',
        'n_present', 'n_total_base', 'n_total_direct',
        'beta_nmags', 'p_nmags',
    ]]

    # Save results
    output_file = data_dir / 'ckpt_spire_firth_ko_associations.csv'
    results_df.to_csv(output_file, index=False)
    print(f"\nSaved results to {output_file}")

    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    # Direction changes (sign reversals)
    direction_change_total = (np.sign(results_df['beta_std_total']) != np.sign(results_df['beta_firth_total']))
    direction_change_direct = (np.sign(results_df['beta_std_direct']) != np.sign(results_df['beta_firth_direct']))

    print(f"\nDirection changes (sign reversals):")
    print(f"  Total model: {direction_change_total.sum()} / {len(results_df)}")
    print(f"  Direct model: {direction_change_direct.sum()} / {len(results_df)}")

    # Inflation ratios
    ratio_total = results_df['beta_std_total'].abs() / results_df['beta_firth_total'].abs()
    ratio_direct = results_df['beta_std_direct'].abs() / results_df['beta_firth_direct'].abs()

    print(f"\nInflation ratios (|beta_std| / |beta_firth|):")
    print(f"  Total model: mean={ratio_total.mean():.1f}x, median={ratio_total.median():.1f}x, max={ratio_total.max():.1f}x")
    print(f"  Direct model: mean={ratio_direct.mean():.1f}x, median={ratio_direct.median():.1f}x, max={ratio_direct.max():.1f}x")

    # Top pairs by |beta_std_total|
    print(f"\n{'Top 15 pairs by |beta_std_total|':─^80}")
    print(f"{'KO':<10} {'Metal':>6} {'β_std_total':>12} {'β_firth_total':>14} {'ratio':>7} {'β_std_dir':>12} {'β_firth_dir':>14} {'ratio_dir':>8}")
    print("─" * 80)

    top_15 = results_df.nlargest(15, 'beta_std_total', keep='all')

    for _, r in top_15.iterrows():
        ratio = abs(r['beta_std_total']) / abs(r['beta_firth_total'])
        ratio_dir = abs(r['beta_std_direct']) / abs(r['beta_firth_direct'])
        print(f"{r['ko_id']:<10} {r['metal']:>6} {r['beta_std_total']:>12.2f} {r['beta_firth_total']:>14.4f} {ratio:>7.1f}x {r['beta_std_direct']:>12.2f} {r['beta_firth_direct']:>14.4f} {ratio_dir:>8.1f}x")

    print("\n" + "=" * 80)
    print(f"Results saved to: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()

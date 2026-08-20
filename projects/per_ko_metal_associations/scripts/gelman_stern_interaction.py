#!/usr/bin/env python3
"""
Gelman & Stern (2006) joint interaction model for pH × metal effect on KO presence.

For each H1-significant KO-metal pair, computes contrast between baseline and pH-adjusted betas.

Gelman & Stern approach: z = (beta_baseline - beta_ph_adjusted) / SE_difference,
where SE_difference = sqrt(SE_baseline^2 + SE_pH^2).
"""

import pandas as pd
import numpy as np
from scipy import stats

# Load data
print("Loading baseline and pH-adjusted associations...")
baseline_df = pd.read_csv(
    '/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data/ckpt_spire_adj_ko_associations.csv'
)
ph_adjusted_df = pd.read_csv(
    '/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data/ckpt_spire_sg_adj_ko_associations.csv'
)

print(f"Baseline associations: {len(baseline_df)} rows")
print(f"pH-adjusted associations: {len(ph_adjusted_df)} rows")

# Compute FDR per metal for baseline
def compute_fdr_bh(pvals):
    """Benjamini-Hochberg FDR correction."""
    sorted_idx = np.argsort(pvals)
    sorted_pvals = pvals[sorted_idx]
    n = len(sorted_pvals)
    # BH critical values
    rank = np.arange(1, n + 1)
    threshold = (rank / n) * 0.05
    # Find largest i where p(i) <= threshold
    valid_idx = np.where(sorted_pvals <= threshold)[0]
    if len(valid_idx) == 0:
        return np.ones(n)
    # Compute q-values: minimum of all q(j) for j >= i
    qvals = np.ones(n)
    for i in range(n - 1, -1, -1):
        qvals[i] = min(sorted_pvals[i] * n / (i + 1), 1.0 if i == n - 1 else qvals[i + 1])
    # Unsort back
    unsort_idx = np.argsort(sorted_idx)
    return qvals[unsort_idx]

baseline_df_copy = baseline_df.copy()
for metal in baseline_df_copy['metal'].unique():
    metal_mask = baseline_df_copy['metal'] == metal
    pvals = baseline_df_copy.loc[metal_mask, 'p_value'].values
    qvals = compute_fdr_bh(pvals)
    baseline_df_copy.loc[metal_mask, 'q_value'] = qvals

ph_adjusted_df_copy = ph_adjusted_df.copy()
for metal in ph_adjusted_df_copy['metal'].unique():
    metal_mask = ph_adjusted_df_copy['metal'] == metal
    pvals = ph_adjusted_df_copy.loc[metal_mask, 'p_value'].values
    qvals = compute_fdr_bh(pvals)
    ph_adjusted_df_copy.loc[metal_mask, 'q_value'] = qvals

# Merge
merged_df = baseline_df_copy.merge(
    ph_adjusted_df_copy,
    on=['ko_id', 'metal'],
    how='inner',
    suffixes=('_baseline', '_ph_adj')
)

print(f"Merged pairs: {len(merged_df)}")

# Filter: either baseline OR pH-adjusted significant (q < 0.05)
sig_pairs = merged_df[
    (merged_df['q_value_baseline'] < 0.05) | (merged_df['q_value_ph_adj'] < 0.05)
].copy()

print(f"Significant pairs (q < 0.05 in either model): {len(sig_pairs)}")

# Compute Gelman & Stern contrast
sig_pairs['beta_diff'] = sig_pairs['beta_baseline'] - sig_pairs['beta_ph_adj']
sig_pairs['se_diff'] = np.sqrt(
    sig_pairs['se_baseline']**2 + sig_pairs['se_ph_adj']**2
)

# Compute z and p-value, handling division by zero
sig_pairs['z_diff'] = np.where(
    sig_pairs['se_diff'] > 0,
    sig_pairs['beta_diff'] / sig_pairs['se_diff'],
    np.nan
)

sig_pairs['p_diff'] = 2 * (1 - stats.norm.cdf(np.abs(sig_pairs['z_diff'])))

# Count significant contrasts
valid_idx = ~sig_pairs['z_diff'].isna()
sig_contrasts = ((np.abs(sig_pairs.loc[valid_idx, 'z_diff']) > 1.96)).sum()
print(f"Pairs with significant Gelman & Stern contrast (|z| > 1.96): {sig_contrasts}")

# Output results
results_cols = [
    'ko_id', 'metal',
    'beta_baseline', 'se_baseline',
    'beta_ph_adj', 'se_ph_adj',
    'beta_diff', 'se_diff', 'z_diff', 'p_diff'
]

output_df = sig_pairs[results_cols].copy()
output_df = output_df.dropna(subset=['z_diff', 'p_diff'])
output_df = output_df.sort_values('p_diff')

output_path = '/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data/gelman_stern_interaction_results.csv'
output_df.to_csv(output_path, index=False)

print(f"\nResults saved to {output_path}")
print(f"Total pairs in output: {len(output_df)}")

# Summary by direction
print("\nSummary by metal:")
for metal in sorted(output_df['metal'].unique()):
    metal_data = output_df[output_df['metal'] == metal]
    sig_count = (np.abs(metal_data['z_diff']) > 1.96).sum()
    print(f"{metal}: {len(metal_data)} pairs; {sig_count} with |z| > 1.96")

print("\nSummary by direction (across all metals):")
baseline_stronger = output_df[output_df['beta_diff'] > 0]
ph_stronger = output_df[output_df['beta_diff'] < 0]
print(f"Baseline stronger (beta_baseline > beta_ph_adj): {len(baseline_stronger)}")
print(f"  Significant contrasts: {(np.abs(baseline_stronger['z_diff']) > 1.96).sum()}")
print(f"pH-adjusted stronger (beta_ph_adj > beta_baseline): {len(ph_stronger)}")
print(f"  Significant contrasts: {(np.abs(ph_stronger['z_diff']) > 1.96).sum()}")

print("\nDone.")

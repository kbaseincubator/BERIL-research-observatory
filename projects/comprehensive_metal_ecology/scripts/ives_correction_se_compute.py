#!/usr/bin/env python3
"""
Compute per-genus SE of Levins' B from bootstrap resampling,
then quantify attenuation bias and run Ives correction.

Output:
  data/ives_se_joined.csv       - PGLS input + se_levins_B
  data/ives_correction_results.csv - attenuation + corrected lambda summary
"""

import os
import sys
import numpy as np
import pandas as pd
import subprocess

REPO = '/home/hmacgregor/BERIL-research-observatory'
DATA = f'{REPO}/projects/comprehensive_metal_ecology/data'

# ── 1. Load bootstrap niche data ─────────────────────────────────────────────
print("1. Loading bootstrap niche data...")
boot = pd.read_csv(f'{DATA}/genus_bootstrap_niche.csv')
print(f"   Bootstrap genera: {len(boot)}")
print(f"   Columns: {list(boot.columns)}")

# Compute SE of Levins' B: SE = sd / sqrt(n_otus)
# sd_levins_B_std = SD of B across bootstrap OTU resamplings
# n_otus = number of OTU resamples used
boot['se_levins_B'] = boot['sd_levins_B_std'] / np.sqrt(boot['n_otus'])

# Quick sanity: mean SE and variance fraction
print(f"\n   sd_levins_B_std: mean={boot['sd_levins_B_std'].mean():.4f} median={boot['sd_levins_B_std'].median():.4f}")
print(f"   n_otus: min={boot['n_otus'].min():.0f} median={boot['n_otus'].median():.0f} max={boot['n_otus'].max():.0f}")
print(f"   se_levins_B: mean={boot['se_levins_B'].mean():.4f} median={boot['se_levins_B'].median():.4f}")

# ── 2. Load PGLS input ────────────────────────────────────────────────────────
print("\n2. Loading PGLS input...")
pgls = pd.read_csv(f'{DATA}/01_pgls_input_bacteria.csv')
print(f"   PGLS genera: {len(pgls)}")

# ── 3. Join SE to PGLS input ─────────────────────────────────────────────────
print("\n3. Joining SE to PGLS input...")
df_ives = pgls.merge(
    boot[['genus_lower', 'se_levins_B', 'sd_levins_B_std', 'n_otus']],
    on='genus_lower', how='left'
)
n_with_se = df_ives['se_levins_B'].notna().sum()
print(f"   Genera with SE: {n_with_se} / {len(df_ives)}")
print(f"   Genera missing SE: {df_ives['se_levins_B'].isna().sum()}")

# ── 4. Attenuation bias analysis ─────────────────────────────────────────────
print("\n4. Attenuation bias analysis...")
df_se = df_ives.dropna(subset=['se_levins_B'])

# Variance of the trait (Levins' B, standardized)
var_B_total = df_se['mean_levins_B_std'].var()
# Mean measurement error variance
mean_se2 = (df_se['se_levins_B'] ** 2).mean()
# Reliability ratio (fraction of variance that is true signal)
var_B_true = max(var_B_total - mean_se2, 0)
reliability_ratio = var_B_true / var_B_total if var_B_total > 0 else np.nan
# Attenuation factor for regression coefficient
attenuation = reliability_ratio  # beta_observed = attenuation * beta_true

print(f"   var(B_total) = {var_B_total:.4f}")
print(f"   mean(SE²)    = {mean_se2:.4f}  ({100*mean_se2/var_B_total:.1f}% of total variance)")
print(f"   var(B_true)  = {var_B_true:.4f}")
print(f"   Reliability ratio λ_R = {reliability_ratio:.4f}")
print(f"   Attenuation factor: β_observed ≈ {attenuation:.3f} × β_true")
print(f"   Implied true β ≈ {-0.021 / attenuation:.4f} (vs observed -0.021)")

# ── 5. Save enhanced PGLS input ──────────────────────────────────────────────
df_ives.to_csv(f'{DATA}/ives_se_joined.csv', index=False)
print(f"\n5. Saved: {DATA}/ives_se_joined.csv")

# ── 6. Summary for R script ───────────────────────────────────────────────────
summary_df = pd.DataFrame([{
    'n_genera_total': len(pgls),
    'n_genera_with_se': n_with_se,
    'var_B_total': var_B_total,
    'mean_se2': mean_se2,
    'fraction_meas_error': mean_se2 / var_B_total,
    'reliability_ratio': reliability_ratio,
    'attenuation_factor': attenuation,
    'beta_observed': -0.021,
    'beta_corrected_estimate': -0.021 / attenuation if attenuation > 0 else np.nan,
}])
summary_df.to_csv(f'{DATA}/ives_attenuation_summary.csv', index=False)
print(f"   Saved: {DATA}/ives_attenuation_summary.csv")

print("\n✓ Python step complete. Run ives_correction.R for phylosig + corrected PGLS.")

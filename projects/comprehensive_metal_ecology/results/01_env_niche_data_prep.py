#!/usr/bin/env python3
"""
Environmental niche breadth analysis — data preparation step
Builds PGLS input datasets for temperature, geochemical, and environmental gradient niche breadth
"""
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

# Set working directory
import os
os.chdir('/home/hmacgregor/BERIL-research-observatory')

# Load data
print("Loading data files...")
env_covariates = pd.read_csv('projects/comprehensive_metal_ecology/data/genus_lat_env_covariates.csv')
pgls_bacteria = pd.read_csv('projects/comprehensive_metal_ecology/data/01_pgls_input_bacteria.csv')
ngsa_pgls = pd.read_csv('projects/comprehensive_metal_ecology/data/02_ngsa_pgls_input.csv')
mgnify_geo = pd.read_csv('projects/microbeatlas_metal_ecology/data/mgnify_genus_geo_niche.csv')
mgnify_pgls = pd.read_csv('projects/comprehensive_metal_ecology/data/mgnify_pgls_input.csv')
social_niche = pd.read_csv('projects/comprehensive_metal_ecology/results/social_niche_breadth_pgls_input.csv')

print(f"env_covariates: {env_covariates.shape}")
print(f"pgls_bacteria: {pgls_bacteria.shape}")
print(f"ngsa_pgls: {ngsa_pgls.shape}")
print(f"mgnify_geo: {mgnify_geo.shape}")
print(f"mgnify_pgls: {mgnify_pgls.shape}")
print(f"social_niche: {social_niche.shape}")

# ============================================================================
# Dataset A: Global temperature niche breadth (primary predictors)
# ============================================================================
print("\n" + "="*70)
print("Dataset A: Temperature niche breadth (global)")
print("="*70)

env_filtered = env_covariates[env_covariates['n_samples'] >= 10].copy()
print(f"After n_samples >= 10 filter: {env_filtered.shape[0]} genera")

dataset_a = env_filtered.merge(
    pgls_bacteria[['genus_lower', 'ko_per_mb_primary', 'mean_genome_mb', 'mean_levins_B_std', 'phylum', 'kingdom']],
    on='genus_lower',
    how='inner'
)
print(f"After join with pgls_bacteria: {dataset_a.shape[0]} genera")

# Z-score predictors within this dataset
dataset_a['ko_per_mb_z'] = stats.zscore(dataset_a['ko_per_mb_primary'], nan_policy='omit')
dataset_a['genome_mb_z'] = stats.zscore(dataset_a['mean_genome_mb'], nan_policy='omit')

# Response variables: temperature breadth and geochemical variables
print(f"  median_temp_range_C: n={dataset_a['median_temp_range_C'].notna().sum()}, median={dataset_a['median_temp_range_C'].median():.3f}, range=[{dataset_a['median_temp_range_C'].min():.1f}, {dataset_a['median_temp_range_C'].max():.1f}]")
print(f"  median_soil_ph: n={dataset_a['median_soil_ph'].notna().sum()}, median={dataset_a['median_soil_ph'].median():.3f}")
print(f"  median_soil_moisture: n={dataset_a['median_soil_moisture'].notna().sum()}, median={dataset_a['median_soil_moisture'].median():.3f}")

# Save Dataset A
output_a = dataset_a[['genus_lower', 'phylum', 'kingdom', 'n_samples',
                       'median_temp_range_C', 'median_soil_ph', 'median_soil_moisture',
                       'median_cmmi_nearest_km',
                       'ko_per_mb_primary', 'mean_genome_mb', 'ko_per_mb_z', 'genome_mb_z',
                       'mean_levins_B_std']]
output_a.to_csv('projects/comprehensive_metal_ecology/results/env_niche_A_pgls_input.csv', index=False)
print(f"Dataset A saved: {output_a.shape[0]} genera")

# ============================================================================
# Dataset B: Temperature niche with tier1/tier2 subcategories
# ============================================================================
print("\n" + "="*70)
print("Dataset B: Temperature niche + subcategories (tier1/tier2)")
print("="*70)

dataset_b = env_filtered.merge(
    ngsa_pgls[['genus_lower', 'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z', 'mean_levins_B_std', 'phylum', 'kingdom']],
    on='genus_lower',
    how='inner'
)
print(f"After join with ngsa_pgls: {dataset_b.shape[0]} genera")

# Add genome_mb from pgls_bacteria
dataset_b = dataset_b.merge(
    pgls_bacteria[['genus_lower', 'mean_genome_mb']],
    on='genus_lower',
    how='left'
)

# Z-score genome_mb within this dataset
dataset_b['genome_mb_z'] = stats.zscore(dataset_b['mean_genome_mb'], nan_policy='omit')

output_b = dataset_b[['genus_lower', 'phylum', 'kingdom', 'n_samples',
                       'median_temp_range_C', 'median_soil_ph',
                       'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z', 'genome_mb_z',
                       'mean_levins_B_std']]
output_b.to_csv('projects/comprehensive_metal_ecology/results/env_niche_B_pgls_input.csv', index=False)
print(f"Dataset B saved: {output_b.shape[0]} genera")

# ============================================================================
# Dataset C: Environmental gradient representation
# (pH, temperature, moisture combined via compositional variation)
# ============================================================================
print("\n" + "="*70)
print("Dataset C: Multi-environment gradient breadth")
print("="*70)

# Use env covariates with reasonable coverage
env_multi = env_filtered[
    (env_filtered['median_temp_range_C'].notna()) &
    (env_filtered['median_soil_ph'].notna()) &
    (env_filtered['median_soil_moisture'].notna()) &
    (env_filtered['n_samples'] >= 20)
].copy()
print(f"After requiring pH, temp, moisture with n_samples >= 20: {env_multi.shape[0]} genera")

# Create a composite environmental breadth metric
# Normalize each dimension
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()

env_breadth_data = env_multi[['median_temp_range_C', 'median_soil_ph', 'median_soil_moisture']].copy()
env_breadth_scaled = scaler.fit_transform(env_breadth_data.fillna(env_breadth_data.mean()))

# Create composite measure: average absolute z-score (breadth across dimensions)
env_multi['env_gradient_breadth'] = np.mean(np.abs(env_breadth_scaled), axis=1)
print(f"  env_gradient_breadth: mean={env_multi['env_gradient_breadth'].mean():.3f}, median={env_multi['env_gradient_breadth'].median():.3f}")

# Join with PGLS data
dataset_c = env_multi.merge(
    pgls_bacteria[['genus_lower', 'ko_per_mb_primary', 'mean_genome_mb', 'mean_levins_B_std', 'phylum', 'kingdom']],
    on='genus_lower',
    how='inner'
)
print(f"After join with pgls_bacteria: {dataset_c.shape[0]} genera")

# Z-score predictors
dataset_c['ko_per_mb_z'] = stats.zscore(dataset_c['ko_per_mb_primary'], nan_policy='omit')
dataset_c['genome_mb_z'] = stats.zscore(dataset_c['mean_genome_mb'], nan_policy='omit')

output_c = dataset_c[['genus_lower', 'phylum', 'kingdom', 'n_samples',
                       'median_temp_range_C', 'median_soil_ph', 'median_soil_moisture',
                       'env_gradient_breadth',
                       'ko_per_mb_primary', 'mean_genome_mb', 'ko_per_mb_z', 'genome_mb_z',
                       'mean_levins_B_std']]
output_c.to_csv('projects/comprehensive_metal_ecology/results/env_niche_C_pgls_input.csv', index=False)
print(f"Dataset C saved: {output_c.shape[0]} genera")

# ============================================================================
# Dataset D: MGnify metal niche breadth (limited but metal-specific)
# ============================================================================
print("\n" + "="*70)
print("Dataset D: MGnify metal niche (Cu, Zn)")
print("="*70)

# Filter for genera with metal SD measurements
mgnify_filtered = mgnify_geo[
    ((mgnify_geo['Cu_n'] >= 10) | (mgnify_geo['Zn_n'] >= 10))
].copy()
print(f"After Cu_n or Zn_n >= 10 filter: {mgnify_filtered.shape[0]} genera")

dataset_d = mgnify_filtered.merge(
    mgnify_pgls[['genus_lower', 'ko_per_mb_total_z', 'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z']],
    on='genus_lower',
    how='inner'
)
print(f"After join with mgnify_pgls: {dataset_d.shape[0]} genera")

# Add genome_mb info if available, otherwise create proxy
if 'mean_genome_mb' not in dataset_d.columns:
    # We don't have genome size in MGnify pgls, so we'll need to work with what we have
    dataset_d['genome_mb_z'] = np.nan
    print("  Note: genome_mb_z not available in mgnify data (will be excluded from some models)")

print(f"  Cu_sd: n={dataset_d['Cu_sd'].notna().sum()}, median={dataset_d['Cu_sd'].median():.3f}")
print(f"  Zn_sd: n={dataset_d['Zn_sd'].notna().sum()}, median={dataset_d['Zn_sd'].median():.3f}")

# Create composite metal niche
dataset_d['metal_niche_composite'] = np.sqrt(
    dataset_d[['Cu_sd', 'Zn_sd']].fillna(0).pow(2).sum(axis=1)
)
print(f"  metal_niche_composite: n={dataset_d['metal_niche_composite'].notna().sum()}, median={dataset_d['metal_niche_composite'].median():.3f}")

output_d = dataset_d[['genus_lower', 'Cu_sd', 'Zn_sd', 'metal_niche_composite',
                       'ko_per_mb_total_z', 'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z', 'genome_mb_z']]
output_d.to_csv('projects/comprehensive_metal_ecology/results/env_niche_D_pgls_input.csv', index=False)
print(f"Dataset D saved: {output_d.shape[0]} genera")

# ============================================================================
# Dataset E: Cross-niche correlation matrix
# ============================================================================
print("\n" + "="*70)
print("Cross-niche correlation data")
print("="*70)

# Build a master dataframe with all available niche metrics
master_niche = pgls_bacteria[['genus_lower', 'mean_levins_B_std']].copy()

# Add temperature metric
master_niche = master_niche.merge(
    env_covariates[['genus_lower', 'median_temp_range_C', 'median_soil_ph']],
    on='genus_lower',
    how='left'
)

# Add MGnify metal metrics
master_niche = master_niche.merge(
    mgnify_geo[['genus_lower', 'Cu_sd', 'Zn_sd']],
    on='genus_lower',
    how='left'
)

# Add social niche breadth
master_niche = master_niche.merge(
    social_niche[['genus', 'count_breadth_std']].rename(columns={'genus': 'genus_lower'}),
    on='genus_lower',
    how='left'
)

print(f"Master niche dataframe: {master_niche.shape[0]} genera")

# Compute correlations
correlations = []

pairs = [
    ('median_temp_range_C', 'mean_levins_B_std', 'Temperature vs Cross-biome Levins B'),
    ('median_soil_ph', 'mean_levins_B_std', 'pH vs Cross-biome Levins B'),
    ('Cu_sd', 'mean_levins_B_std', 'Cu niche vs Cross-biome Levins B'),
    ('Zn_sd', 'mean_levins_B_std', 'Zn niche vs Cross-biome Levins B'),
    ('median_temp_range_C', 'median_soil_ph', 'Temperature vs Soil pH'),
    ('median_temp_range_C', 'Cu_sd', 'Temperature vs Cu niche'),
    ('Cu_sd', 'Zn_sd', 'Cu vs Zn niche breadth'),
    ('mean_levins_B_std', 'count_breadth_std', 'Cross-biome vs Social Levins B'),
]

for var1, var2, description in pairs:
    # Filter to non-null values
    subset = master_niche[[var1, var2]].dropna()
    if len(subset) >= 3:
        rho, p = spearmanr(subset[var1], subset[var2])
        correlations.append({
            'pair': description,
            'var1': var1,
            'var2': var2,
            'n': len(subset),
            'rho': rho,
            'p_value': p,
            'sig': '*' if p < 0.05 else ''
        })
        print(f"  {description}: n={len(subset)}, rho={rho:.4f}, p={p:.4f} {('*' if p<0.05 else '')}")

corr_df = pd.DataFrame(correlations)
corr_df.to_csv('projects/comprehensive_metal_ecology/results/cross_niche_correlations.csv', index=False)

print("\n" + "="*70)
print("Data preparation complete!")
print("="*70)
print("\nOutput files saved:")
print("  - env_niche_A_pgls_input.csv (Temperature primary)")
print("  - env_niche_B_pgls_input.csv (Temperature tier1/tier2)")
print("  - env_niche_C_pgls_input.csv (Multi-environment gradient)")
print("  - env_niche_D_pgls_input.csv (MGnify metals)")
print("  - cross_niche_correlations.csv")

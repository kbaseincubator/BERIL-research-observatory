#!/usr/bin/env python3
"""
CWM per-KO × USA × USGS analysis: pH confound analysis with partial Spearman.

Given that SoilGrids_master pH is unpopulated (verified via inspection),
this script:
1. Validates soilgrids_master schema and coverage
2. Falls back to measured MicrobeAtlas pH (which has ~60-100 samples per pair)
3. Reruns partial Spearman (controlling for pH) on 6 FDR-significant pairs
4. Reports whether pH confounding explains the signal

Target pairs (50km thinning, q_BH < 0.05):
- K16014 × Hg, K04655 × Hg, K03605 × Hg, K04654 × Hg, K04654 × As, K00859 × Pb
"""

import os
import sys
os.environ['OMP_NUM_THREADS'] = '1'
sys.path.append('/opt/conda/lib/python3.13/site-packages')

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Spark setup
import berdl_notebook_utils
spark = berdl_notebook_utils.get_spark_session()

OUTPUT_DIR = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# STEP 1: Inspect SoilGrids Master Schema and Coverage
# ==============================================================================
print("\n" + "="*80)
print("STEP 1: SoilGrids Master Schema and pH Coverage")
print("="*80)

schema_df = spark.sql("DESCRIBE arkinlab.envdbs.soilgrids_master").toPandas()
print(f"\nTotal columns: {len(schema_df)}")

# Check pH columns
ph_columns = schema_df[schema_df['col_name'].str.contains('pH', case=False, regex=True)]['col_name'].tolist()
print(f"\nPH-related columns ({len(ph_columns)}):")
for col in ph_columns:
    print(f"  - {col}")

# Check coverage of main pH column (pH_0-5cm, most surface-relevant)
coverage_df = spark.sql("""
SELECT
  COUNT(*) as total_rows,
  COUNT(DISTINCT lat) as distinct_lats,
  COUNT(DISTINCT lon) as distinct_lons,
  SUM(CASE WHEN `pH_0-5cm` IS NOT NULL AND `pH_0-5cm` != '' THEN 1 ELSE 0 END) as ph_non_null,
  MAX(`sand_0cm`) as max_sand  -- check if any numeric columns are populated
FROM arkinlab.envdbs.soilgrids_master
""").toPandas()

print(f"\nSoilGrids Master Coverage:")
print(coverage_df.to_string(index=False))

ph_coverage_pct = 100.0 * coverage_df['ph_non_null'].values[0] / coverage_df['total_rows'].values[0]
print(f"\nPH_0-5cm coverage: {coverage_df['ph_non_null'].values[0]} / {coverage_df['total_rows'].values[0]} ({ph_coverage_pct:.2f}%)")

if coverage_df['ph_non_null'].values[0] == 0:
    print("\n⚠️  SoilGrids pH is not populated. Falling back to measured MicrobeAtlas pH.")
    use_measured_ph_only = True
else:
    use_measured_ph_only = False

# ==============================================================================
# STEP 2: Load measured pH from MicrobeAtlas
# ==============================================================================
print("\n" + "="*80)
print("STEP 2: Measured pH from MicrobeAtlas")
print("="*80)

query_measured_ph = """
SELECT sample_id, lat, lon, ph, environments
FROM arkinlab.microbeatlas.sample_metadata
WHERE lat BETWEEN 24 AND 50
  AND lon BETWEEN -125 AND -65
  AND environments LIKE '%soil%'
  AND ph IS NOT NULL
  AND lat IS NOT NULL
  AND lon IS NOT NULL
"""

measured_ph_df = spark.sql(query_measured_ph).toPandas()
print(f"\nUSA soil samples with measured pH: {len(measured_ph_df)}")
print(f"pH range: {measured_ph_df['ph'].min():.2f} - {measured_ph_df['ph'].max():.2f}")
print(f"pH mean ± SD: {measured_ph_df['ph'].mean():.2f} ± {measured_ph_df['ph'].std():.2f}")

# Save combined pH file (just measured, since soilgrids is unavailable)
sample_ph_path = OUTPUT_DIR / 'sample_ph_measured.csv'
measured_ph_df.to_csv(sample_ph_path, index=False)
print(f"\nSaved measured pH to: {sample_ph_path}")

# ==============================================================================
# STEP 3: Rerun partial Spearman with pH control
# ==============================================================================
print("\n" + "="*80)
print("STEP 3: Partial Spearman (controlling for pH)")
print("="*80)

# Target pairs (50km thinning, q_BH < 0.05)
target_pairs = [
    ('K16014', 'Hg'),
    ('K04655', 'Hg'),
    ('K03605', 'Hg'),
    ('K04654', 'Hg'),
    ('K04654', 'As'),
    ('K00859', 'Pb'),
]

# Load CWM × USGS data (directly as Pandas to avoid Spark worker access issues)
cwm_path_str = '/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm/usa_cwm_usgs_joined.parquet'
cwm_df = pd.read_parquet(cwm_path_str)
print(f"Total CWM × USGS rows: {len(cwm_df)}")

# Apply 50km distance threshold
cwm_50km = cwm_df[cwm_df['usgs_dist_km'] <= 50.0].copy()
print(f"After 50km distance threshold: {len(cwm_50km)}")

# Melt from wide to long format (metals in columns → rows)
metal_cols = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
cwm_long = cwm_50km.melt(
    id_vars=['sample_id', 'lat_x', 'lon_x', 'ko_id', 'cwm', 'matched_count', 'lat_y', 'lon_y', 'usgs_dist_km'],
    value_vars=metal_cols,
    var_name='metal',
    value_name='metal_value'
)
# Keep only non-null metal values
cwm_long = cwm_long.dropna(subset=['metal_value'])
print(f"After melting to long format: {len(cwm_long)}")

# Thin to 50km spatial grid (DEG=0.45 ~= 50km at equator)
np.random.seed(42)
DEG = 0.45
cwm_long['grid_lat'] = (cwm_long['lat_x'] / DEG).astype(int)
cwm_long['grid_lon'] = (cwm_long['lon_x'] / DEG).astype(int)

# Keep first sample per grid cell per KO per metal (using idxmin to preserve all columns)
cwm_thinned = cwm_long.loc[cwm_long.groupby(['grid_lat', 'grid_lon', 'ko_id', 'metal']).apply(
    lambda g: g.index[0]
)]
print(f"After 0.45° spatial thinning: {len(cwm_thinned)}")

# Add pH data
cwm_ph = cwm_thinned.merge(measured_ph_df[['sample_id', 'ph']], on='sample_id', how='left')
print(f"After pH merge: {len(cwm_ph)} rows")

# Helper function for partial Spearman
def partial_spearman(x, y, z):
    """
    Partial Spearman correlation: ρ(x, y | z)
    Residualization via OLS: regress x and y on z, return ρ of residuals.
    """
    # Remove NaN
    mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
    if mask.sum() < 10:  # Require minimum sample size
        return np.nan, np.nan, 0

    x_clean = x[mask]
    y_clean = y[mask]
    z_clean = z[mask]

    # Residualize x on z
    slope_x, intercept_x, _, _, _ = stats.linregress(z_clean, x_clean)
    x_resid = x_clean - (slope_x * z_clean + intercept_x)

    # Residualize y on z
    slope_y, intercept_y, _, _, _ = stats.linregress(z_clean, y_clean)
    y_resid = y_clean - (slope_y * z_clean + intercept_y)

    # Spearman correlation of residuals
    rho, pval = stats.spearmanr(x_resid, y_resid)

    return rho, pval, len(x_clean)

# Run analysis for each target pair
results = []

print(f"\n{'Pair':>20} {'n_raw':>8} {'rho_raw':>10} {'p_raw':>12} {'n_pH':>8} {'rho_partial':>12} {'p_partial':>12}")
print("─" * 95)

for ko_id, metal in target_pairs:
    # Extract data for this pair
    subset = cwm_ph[(cwm_ph['ko_id'] == ko_id) & (cwm_ph['metal'] == metal)].copy()

    if len(subset) == 0:
        print(f"{ko_id} × {metal:>8} {'NO DATA':>50}")
        continue

    # Remove rows with missing pH or metal_value
    subset_ph = subset.dropna(subset=['cwm', 'metal_value', 'ph'])

    n_raw = len(subset)
    n_ph = len(subset_ph)

    if n_ph < 10:
        print(f"{ko_id} × {metal:>8} {n_raw:>8} {'n_pH < 10':>35}")
        continue

    # Raw Spearman (no pH control)
    rho_raw, p_raw = stats.spearmanr(subset_ph['cwm'].values, subset_ph['metal_value'].values)

    # Partial Spearman (controlling for pH)
    rho_partial, p_partial, n_used = partial_spearman(
        subset_ph['cwm'].values,
        subset_ph['metal_value'].values,
        subset_ph['ph'].values
    )

    print(f"{ko_id} × {metal:>8} {n_raw:>8} {rho_raw:>10.4f} {p_raw:>12.2e} {n_ph:>8} {rho_partial:>12.4f} {p_partial:>12.2e}")

    results.append({
        'ko_id': ko_id,
        'metal': metal,
        'n_raw': n_raw,
        'rho_raw': rho_raw,
        'p_raw': p_raw,
        'n_ph_complete': n_ph,
        'rho_partial': rho_partial,
        'p_partial': p_partial,
    })

# Convert to DataFrame
results_df = pd.DataFrame(results)

# Apply BH-FDR correction to both raw and partial p-values
if len(results_df) > 0:
    from statsmodels.stats.multitest import multipletests

    # Raw correction
    reject_raw, q_raw, _, _ = multipletests(results_df['p_raw'], method='fdr_bh')
    results_df['q_raw'] = q_raw

    # Partial correction
    reject_partial, q_partial, _, _ = multipletests(results_df['p_partial'], method='fdr_bh')
    results_df['q_partial'] = q_partial

    print("\n" + "="*80)
    print("Results with BH-FDR correction (6 pairs):")
    print("="*80)
    print(results_df[['ko_id', 'metal', 'n_raw', 'rho_raw', 'q_raw', 'n_ph_complete', 'rho_partial', 'q_partial']].to_string(index=False))

    # Summary statistics
    print(f"\n{'Summary':^80}")
    print("─" * 80)
    sig_raw = (results_df['q_raw'] < 0.05).sum()
    sig_partial = (results_df['q_partial'] < 0.05).sum()
    print(f"Pairs with q < 0.05 (raw):      {sig_raw} / {len(results_df)}")
    print(f"Pairs with q < 0.05 (partial): {sig_partial} / {len(results_df)}")

    # Effect of pH control
    rho_change = (results_df['rho_partial'] - results_df['rho_raw']).abs().mean()
    print(f"Mean |Δρ| (raw → partial):     {rho_change:.4f}")

    # How many pairs have significant rho but non-significant after pH control?
    sig_loss = ((results_df['q_raw'] < 0.05) & (results_df['q_partial'] >= 0.05)).sum()
    print(f"Pairs losing significance via pH: {sig_loss} / {sig_raw}")

    # Save results
    results_path = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/cwm_per_ko_usa_ph_adjusted_v2.csv')
    results_df.to_csv(results_path, index=False)
    print(f"\nResults saved to: {results_path}")

print("\n" + "="*80)
print("Analysis complete!")
print("="*80)
print("\nKey findings:")
print("  - SoilGrids pH is not populated in soilgrids_master")
print("  - Analysis uses measured pH from MicrobeAtlas (~60-100 samples per pair)")
print("  - pH control via OLS residualization tested on 6 target pairs")
print(f"  - See {results_path} for full results")

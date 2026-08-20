"""Elevation sensitivity check for the 88 all-controls-surviving KO-metal pairs.

Joins MGnify MAG coordinates to arkinlab.envdbs.etopo1_elevation (0.1-degree grid)
via Spark, then re-runs the logistic regression with elevation added as a covariate:
    KO_present ~ PF1_metal + latitude + elevation + log_genome_size + C(phylum)

Saves:
    data/h1_elevation_adjusted.csv  — 88 rows with beta/SE/p/q for elev-adjusted model
                                       plus prior latitude-only beta/p for comparison

Usage (on-cluster):
    python scripts/run_elevation_sensitivity.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.formula.api import logit

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / 'data'
OUT_PATH = DATA_DIR / 'h1_elevation_adjusted.csv'

METAL_COLS = ['PF1_Cu', 'PF1_Pb', 'PF1_Cr', 'PF1_As', 'PF1_Cd', 'PF1_Hg']


# ── 1. Load 88 pairs ──────────────────────────────────────────────────────────
rob = pd.read_csv(DATA_DIR / 'h1_robustness_summary.csv')
pairs_88 = rob[rob['survives_all_controls_with_p3']].copy()
print(f'Pairs to test: {len(pairs_88)}')

# ── 2. Load MGnify KO matrix (subset needed columns) ─────────────────────────
needed_kos = set(pairs_88['ko_id'])
print(f'Loading KO matrix for {len(needed_kos)} KOs ...')
mat = pd.read_parquet(
    DATA_DIR / 'mgnify_all_ko_matrix.parquet',
    columns=['genome_id', 'ko_id', 'present', 'latitude', 'longitude',
             'genome_size', 'genus', 'phylum'],
)
# Keep only rows needed for these 88 KOs
mat = mat[mat['ko_id'].isin(needed_kos)].copy()

# Build per-MAG metadata (one row per genome_id)
mag_meta = (
    mat[['genome_id', 'latitude', 'longitude', 'genome_size', 'phylum']]
    .drop_duplicates('genome_id')
    .copy()
)
mag_meta['log_genome_size'] = np.log(mag_meta['genome_size'].clip(lower=1))

# Also grab metal columns from the full matrix (one metal value per MAG)
metal_df = (
    pd.read_parquet(
        DATA_DIR / 'mgnify_all_ko_matrix.parquet',
        columns=['genome_id'] + METAL_COLS,
    )
    .drop_duplicates('genome_id')
)
mag_meta = mag_meta.merge(metal_df, on='genome_id', how='left')

n_mags = mag_meta['genome_id'].nunique()
print(f'MAGs: {n_mags}')

# ── 3. Fetch ETOPO1 elevation via Spark ───────────────────────────────────────
print('Connecting to Spark ...')
from berdl_notebook_utils import get_spark_session
spark = get_spark_session()
print(f'Spark version: {spark.version}')

# Build the set of rounded lat/lon to query
mag_meta['lat_rnd'] = (mag_meta['latitude'] * 10).round() / 10
mag_meta['lon_rnd'] = (mag_meta['longitude'] * 10).round() / 10
unique_coords = mag_meta[['lat_rnd', 'lon_rnd']].drop_duplicates()
print(f'Unique 0.1° grid cells to query: {len(unique_coords)}')

# Build a temp view of target coordinates, then join ETOPO1
coords_sdf = spark.createDataFrame(
    unique_coords.rename(columns={'lat_rnd': 'q_lat', 'lon_rnd': 'q_lon'})
)
coords_sdf.createOrReplaceTempView('target_coords')
spark.sql('''
    CREATE OR REPLACE TEMP VIEW etopo AS
    SELECT ROUND(CAST(lat AS DOUBLE), 1) AS e_lat,
           ROUND(CAST(lon AS DOUBLE), 1) AS e_lon,
           CAST(elevation AS DOUBLE)     AS elevation_m
    FROM arkinlab.envdbs.etopo1_elevation
''')

elev_sdf = spark.sql('''
    SELECT t.q_lat, t.q_lon, e.elevation_m
    FROM target_coords t
    JOIN etopo e
      ON t.q_lat = e.e_lat AND t.q_lon = e.e_lon
''')
elev_df = elev_sdf.toPandas()
print(f'Elevation values retrieved: {len(elev_df)} / {len(unique_coords)} requested')

# Merge elevation back into mag_meta
mag_meta = mag_meta.merge(
    elev_df.rename(columns={'q_lat': 'lat_rnd', 'q_lon': 'lon_rnd'}),
    on=['lat_rnd', 'lon_rnd'],
    how='left',
)
n_with_elev = mag_meta['elevation_m'].notna().sum()
print(f'MAGs with elevation: {n_with_elev} / {n_mags} '
      f'({100 * n_with_elev / n_mags:.1f}%)')

# ── 4. Run logistic regression for each of the 88 pairs ───────────────────────
print('\nRunning elevation-adjusted regressions ...')
results = []

for _, row in pairs_88.iterrows():
    ko_id = row['ko_id']
    metal = row['metal']
    beta_lat = row.get('beta_h4', np.nan)
    p_lat    = row.get('q_h4', np.nan)

    # Build analysis DataFrame for this KO
    ko_rows = mat[(mat['ko_id'] == ko_id)][['genome_id', 'present']].copy()
    df = mag_meta.merge(ko_rows, on='genome_id', how='inner')
    df = df.dropna(subset=[metal, 'latitude', 'elevation_m', 'log_genome_size', 'phylum'])

    n_present = int(df['present'].sum())
    n_total   = len(df)

    if n_total < 20 or n_present < 5 or (n_total - n_present) < 5:
        results.append({
            'ko_id': ko_id, 'metal': metal,
            'beta_elev': np.nan, 'se_elev': np.nan,
            'p_elev': np.nan, 'q_elev': np.nan,
            'beta_lat_only': beta_lat, 'p_lat_only': p_lat,
            'n_total': n_total, 'n_present': n_present,
            'converged': False, 'note': 'insufficient_data',
        })
        continue

    # Filter phylum groups with both present and absent
    grp = df.groupby('phylum')['present'].agg(['sum', 'count'])
    valid = grp[(grp['sum'] >= 1) & (grp['count'] - grp['sum'] >= 1) & (grp['count'] >= 2)].index
    df = df[df['phylum'].isin(valid)].copy()
    if len(df) < 20:
        results.append({
            'ko_id': ko_id, 'metal': metal,
            'beta_elev': np.nan, 'se_elev': np.nan,
            'p_elev': np.nan, 'q_elev': np.nan,
            'beta_lat_only': beta_lat, 'p_lat_only': p_lat,
            'n_total': len(df), 'n_present': n_present,
            'converged': False, 'note': 'phylum_filter_too_few',
        })
        continue

    formula = f'present ~ {metal} + latitude + elevation_m + log_genome_size + C(phylum)'
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            model = logit(formula, data=df).fit(disp=False, maxiter=200)
        beta = float(model.params[metal])
        se   = float(model.bse[metal])
        p    = float(model.pvalues[metal])
        results.append({
            'ko_id': ko_id, 'metal': metal,
            'beta_elev': beta, 'se_elev': se,
            'p_elev': p, 'q_elev': np.nan,  # fill BH below
            'beta_lat_only': beta_lat, 'p_lat_only': p_lat,
            'n_total': len(df), 'n_present': n_present,
            'converged': bool(model.mle_retvals.get('converged', True)),
            'note': '',
        })
    except Exception as exc:
        results.append({
            'ko_id': ko_id, 'metal': metal,
            'beta_elev': np.nan, 'se_elev': np.nan,
            'p_elev': np.nan, 'q_elev': np.nan,
            'beta_lat_only': beta_lat, 'p_lat_only': p_lat,
            'n_total': len(df), 'n_present': n_present,
            'converged': False, 'note': f'error:{exc}',
        })

out = pd.DataFrame(results)

# BH FDR over the finite p-values
finite = out['p_elev'].notna()
if finite.sum() > 0:
    from statsmodels.stats.multitest import multipletests
    _, q_vals, _, _ = multipletests(out.loc[finite, 'p_elev'], method='fdr_bh')
    out.loc[finite, 'q_elev'] = q_vals

# ── 5. Report ─────────────────────────────────────────────────────────────────
n_converged = finite.sum()
n_sig       = (out['q_elev'] < 0.05).sum()
# Direction flip: sign of beta_elev vs sign of beta_lat_only
both_finite = out['beta_elev'].notna() & out['beta_lat_only'].notna()
n_flip = (np.sign(out.loc[both_finite, 'beta_elev']) !=
          np.sign(out.loc[both_finite, 'beta_lat_only'])).sum()
beta_change = (out.loc[both_finite, 'beta_elev'] - out.loc[both_finite, 'beta_lat_only']).abs()

if both_finite.sum() >= 2:
    rho, p_rho = spearmanr(
        out.loc[both_finite, 'beta_lat_only'],
        out.loc[both_finite, 'beta_elev'],
    )
else:
    rho, p_rho = np.nan, np.nan

print(f'\n=== Elevation Sensitivity Results ===')
print(f'Pairs tested:       88')
print(f'Converged:          {n_converged}')
print(f'FDR-sig (q<0.05):   {n_sig} / {n_converged}')
print(f'Direction flips:    {n_flip} / {both_finite.sum()}')
print(f'β Spearman ρ (elev vs lat-only): {rho:.3f} (p={p_rho:.4f})')
print(f'Mean |Δβ|:  {beta_change.mean():.4f}  Range: {beta_change.min():.4f}–{beta_change.max():.4f}')

out.to_csv(OUT_PATH, index=False)
print(f'\nSaved: {OUT_PATH}')

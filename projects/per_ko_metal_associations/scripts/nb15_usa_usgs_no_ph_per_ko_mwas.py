#!/usr/bin/env python3
"""
NB15: USA per-KO MWAS — TOTAL EFFECT (no pH covariate)
========================================================
Identical to NB15b but REMOVES SoilGrids sg_pH covariate.
This produces the total-effect estimates for TOTAL measured metals.

Design: Z = [intercept, lat, phylum_dummies]

Reuses cached nb15_soil_metal_wide.parquet from NB15b run.
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import t as t_dist
from scipy.spatial import cKDTree
from statsmodels.stats.multitest import multipletests

REPO = Path('/home/hmacgregor/BERIL-research-observatory')
PROJ = REPO / 'projects' / 'per_ko_metal_associations'
MEP  = REPO / 'projects' / 'microbeatlas_metal_ecology'
BIOI = REPO / 'projects' / 'metal_contamination_bioindicators'
OUT  = PROJ / 'data'
USGS = Path('/home/hmacgregor/data/envdbs/usgs_geochem')

METALS   = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
MIN_PREV = 20
MAX_DIST = 1.0
CACHE    = OUT / 'nb15_soil_metal_wide.parquet'


def score_test_metal(Y, x_m, Z_arr):
    """OLS partial-correlation score test for all KOs simultaneously."""
    n, K = Y.shape
    p = Z_arr.shape[1]
    df = n - p - 1
    Q, _ = np.linalg.qr(Z_arr, mode='reduced')
    x_proj  = Q @ (Q.T @ x_m)
    x_resid = x_m - x_proj
    x_ss    = float(np.dot(x_resid, x_resid))
    QTY     = Q.T @ Y
    Y_resid = Y - Q @ QTY
    cov_xy  = x_resid @ Y_resid
    y_ss    = np.einsum('ij,ij->j', Y_resid, Y_resid)
    denom   = np.sqrt(x_ss * np.maximum(y_ss, 1e-12))
    r       = cov_xy / denom
    r_clip  = np.clip(r, -1 + 1e-9, 1 - 1e-9)
    t_stat  = r_clip * np.sqrt(df) / np.sqrt(1 - r_clip**2)
    p_vals  = 2 * t_dist.sf(np.abs(t_stat), df=df)
    beta    = cov_xy / x_ss
    return beta, t_stat, p_vals


def main():
    print('=== NB15: USA per-KO MWAS (USGS point-level, TOTAL EFFECT, no pH) ===')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 1. USA MAG lat/lon + phylum
    # ------------------------------------------------------------------
    print('\n[1] Loading USA MAG locations...')
    geo = pd.read_csv(MEP / 'data' / 'final_mags_geospatial_traits.csv')
    usa_mask = geo['lat'].between(24, 50) & geo['lon'].between(-125, -65)
    usa_geo  = geo[usa_mask][['genome_id', 'lat', 'lon', 'phylum']].copy()
    print(f'    USA MAGs: {len(usa_geo):,}')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 2. USGS soil metal concentrations (load from cache if available)
    # ------------------------------------------------------------------
    if CACHE.exists():
        print(f'\n[2] Loading cached soil metal wide table: {CACHE.name}')
        metal_wide = pd.read_parquet(CACHE)
        print(f'    Rows: {len(metal_wide):,}')
    else:
        print('\n[2] Extracting metal concentrations from USGS long-format data...')
        meta = pd.read_parquet(USGS / 'usgs_geochem.parquet',
                               columns=['lab_id', 'latitude', 'longitude', 'primary_class'])
        soil_meta = meta[
            (meta['primary_class'] == 'soil') &
            meta['latitude'].between(24, 50) &
            meta['longitude'].between(-125, -65) &
            meta['latitude'].notna()
        ].copy()
        soil_ids = set(soil_meta['lab_id'].values)
        del meta
        print(f'    Soil samples (N. America): {len(soil_meta):,}')

        import re
        metal_prefix_pat = r'^(As|Cd|Cr|Cu|Hg|Pb)_ppm_'
        pf = pd.read_parquet(USGS / 'usgs_geochem_joined.parquet',
                             columns=['lab_id', 'parameter', 'qualified_value'])
        chunks = []
        rows_seen = 0
        for i, chunk in enumerate(pf):
            if i == 0:
                # Single chunk if parquet_file.iter_batches; adapt if using pd.read_parquet
                pass

        # Simpler version: just read and filter directly
        df = pd.read_parquet(USGS / 'usgs_geochem_joined.parquet',
                             columns=['lab_id', 'parameter', 'qualified_value'])
        mask_lab = df['lab_id'].isin(soil_ids)
        mask_metal = df['parameter'].str.match(metal_prefix_pat, na=False)
        metal_long = df[mask_lab & mask_metal].copy()
        metal_long['metal'] = metal_long['parameter'].str.split('_').str[0]
        metal_long = metal_long[['lab_id', 'metal', 'qualified_value']]
        del df
        print(f'    Metal measurements: {len(metal_long):,}')

        metal_long.loc[metal_long['qualified_value'] <= 0, 'qualified_value'] = np.nan
        metal_wide = (
            metal_long
            .groupby(['lab_id', 'metal'])['qualified_value']
            .median().unstack('metal')
        )
        metal_wide.columns.name = None
        metal_wide = metal_wide.reset_index()
        for m in METALS:
            if m not in metal_wide.columns:
                metal_wide[m] = np.nan
        metal_wide = metal_wide.merge(
            soil_meta[['lab_id', 'latitude', 'longitude']], on='lab_id', how='inner')
        metal_wide.attrs = {}
        metal_wide.to_parquet(CACHE, index=False)
        print(f'    Saved cache: {CACHE.name}')

    # ------------------------------------------------------------------
    # 3. NN join: USA MAGs → USGS metal sites
    # ------------------------------------------------------------------
    print(f'\n[3] Joining USA MAGs to USGS metal sites (max {MAX_DIST}° ≈ 111 km)...')
    tree = cKDTree(metal_wide[['latitude', 'longitude']].values)
    dists, idxs = tree.query(usa_geo[['lat', 'lon']].values, k=1)
    nn_metals = np.full((len(usa_geo), len(METALS)), np.nan)
    matched_mask = dists <= MAX_DIST
    for i, m in enumerate(METALS):
        nn_metals[matched_mask, i] = metal_wide[m].iloc[idxs[matched_mask]].values
    del tree, metal_wide

    within = usa_geo.copy()
    for i, m in enumerate(METALS):
        within[m] = nn_metals[:, i]
    print(f'    Matched: {matched_mask.sum():,} / {len(usa_geo):,} MAGs')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 4. KO matrix (long → wide binary)
    # ------------------------------------------------------------------
    print('\n[4] Loading KO matrix...')
    usa_ids     = set(within['genome_id'])
    ko_long     = pd.read_parquet(PROJ / 'data' / 'mgnify_all_ko_matrix.parquet',
                                   columns=['genome_id', 'ko_id'])
    ko_long_usa = ko_long[ko_long['genome_id'].isin(usa_ids)].copy()
    del ko_long
    ko_long_usa['present'] = np.uint8(1)
    ko_wide = ko_long_usa.pivot_table(
        index='genome_id', columns='ko_id', values='present',
        fill_value=0, aggfunc='max'
    )
    ko_wide.columns.name = None
    ko_wide = ko_wide.reset_index()
    del ko_long_usa
    print(f'    KOs in matrix: {len(ko_wide.columns) - 1}')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 5. Merge + prevalence filter
    # ------------------------------------------------------------------
    df = within.merge(ko_wide, on='genome_id', how='inner')
    print(f'\n[5] Analysis dataset: {len(df):,} MAGs')
    ko_cols   = [c for c in df.columns if c.startswith('K')]
    prev_all  = df[ko_cols].sum()
    valid_kos = prev_all[prev_all >= MIN_PREV].index.tolist()
    print(f'    KOs passing prevalence ≥ {MIN_PREV}: {len(valid_kos):,}')
    df['phylum'] = df['phylum'].fillna('Unknown')
    phy_counts   = df['phylum'].value_counts()
    df['phylum'] = df['phylum'].where(phy_counts[df['phylum']].values >= 5, 'Rare')
    print(f'    Unique phyla: {df["phylum"].nunique()}')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 6. Score test per metal WITHOUT sg_pH
    # ------------------------------------------------------------------
    print('\n[6] Running score tests per metal (TOTAL EFFECT, no pH covariate)...')
    all_results = []

    for metal in METALS:
        valid_mask = df[metal].notna()
        n_valid = valid_mask.sum()
        if n_valid < 100:
            continue

        df_m  = df[valid_mask].copy()
        Y_m   = df_m[valid_kos].values.astype(np.float64)
        prev_m = Y_m.sum(axis=0)
        valid_m = [k for k, p in zip(valid_kos, prev_m) if p >= MIN_PREV]
        if not valid_m:
            continue
        ki       = [valid_kos.index(k) for k in valid_m]
        Y_m_filt = Y_m[:, ki].astype(np.float64)
        n_pos_m  = Y_m_filt.sum(axis=0).astype(int)

        # Standardize metal
        mu, sd = df_m[metal].mean(), df_m[metal].std()
        if sd == 0:
            continue
        x_m = ((df_m[metal] - mu) / sd).values.astype(np.float64)

        # Standardize latitude covariate ONLY (no pH)
        lat_std = df_m['lat'].values
        lat_std = (lat_std - lat_std.mean()) / lat_std.std()

        phy_dum = pd.get_dummies(df_m['phylum'], prefix='ph', drop_first=True).astype(float).values
        Z_arr   = np.column_stack([np.ones(len(df_m)), lat_std, phy_dum])

        beta, t_stat, p_vals = score_test_metal(Y_m_filt, x_m, Z_arr)
        _, q_vals, _, _ = multipletests(p_vals, method='fdr_bh')

        res = pd.DataFrame({
            'ko_id':    valid_m,
            'metal':    metal,
            'beta_ols': beta,
            't_stat':   t_stat,
            'p_value':  p_vals,
            'q_value':  q_vals,
            'n_pos':    n_pos_m,
            'n_mags':   n_valid,
        })
        n_sig = (q_vals < 0.05).sum()
        print(f'    {metal}: n={n_valid:,}, KOs tested={len(valid_m):,}, q<0.05={n_sig}')
        all_results.append(res)
        sys.stdout.flush()

    results_df = pd.concat(all_results, ignore_index=True)
    sig_df     = results_df[results_df['q_value'] < 0.05]
    print(f'\n    Total FDR q<0.05 pairs: {len(sig_df)}')

    # ------------------------------------------------------------------
    # 7. Save
    # ------------------------------------------------------------------
    out = OUT / 'nb15_usa_usgs_no_ph_per_ko_mwas.csv'
    results_df.to_csv(out, index=False)
    print(f'\n[Saved: {out}]')

    # Summary
    print('\n' + '=' * 72)
    print('RESULTS — USA per-KO MWAS (TOTAL EFFECT, NO pH COVARIATE)')
    print('=' * 72)
    for metal in METALS:
        m_res = results_df[results_df['metal'] == metal]
        if len(m_res):
            n_sig = (m_res['q_value'] < 0.05).sum()
            print(f'{metal}: {len(m_res)} tested, {n_sig} FDR significant')

    print('=' * 72)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
NB15b: USA per-KO MWAS — pH-adjusted sensitivity check
========================================================
Identical to NB15 (USGS NGDB point-level soil data, nearest-neighbor join)
but adds SoilGrids sg_pH as a covariate in the null design matrix:

  Z = [intercept, lat, sg_pH, phylum_dummies]

Reports what fraction of NB15's 1,743 significant pairs survive pH adjustment,
mirroring the global MWAS pH sensitivity check (NB04: 151/219 survived).

Caches the heavy 46M-row USGS extraction as nb15_soil_metal_wide.parquet
so subsequent runs skip that step.
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
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
    print('=== NB15b: USA per-KO MWAS (USGS point-level + pH-adjusted) ===')
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
    # 2. SoilGrids pH join (0.25° grid)
    # ------------------------------------------------------------------
    print('\n[2] Joining SoilGrids pH...')
    sg = pd.read_parquet(BIOI / 'data' / 'soilgrids_grid.parquet',
                         columns=['sg_pH', 'lat_grid_025', 'lon_grid_025'])
    usa_geo['lat025'] = (usa_geo['lat'] * 4).round() / 4
    usa_geo['lon025'] = (usa_geo['lon'] * 4).round() / 4
    sg = sg.rename(columns={'lat_grid_025': 'lat025', 'lon_grid_025': 'lon025'})
    usa_geo = usa_geo.merge(sg[['lat025', 'lon025', 'sg_pH']], on=['lat025', 'lon025'], how='left')
    n_ph = usa_geo['sg_pH'].notna().sum()
    print(f'    MAGs with sg_pH: {n_ph:,} / {len(usa_geo):,} ({n_ph/len(usa_geo)*100:.1f}%)')
    # Impute missing pH with USA mean (only a small fraction missing)
    ph_mean = usa_geo['sg_pH'].mean()
    usa_geo['sg_pH'] = usa_geo['sg_pH'].fillna(ph_mean)
    print(f'    sg_pH mean: {ph_mean:.2f}; {len(usa_geo)-n_ph} imputed with mean')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 3. USGS soil metal concentrations (load from cache if available)
    # ------------------------------------------------------------------
    if CACHE.exists():
        print(f'\n[3] Loading cached soil metal wide table: {CACHE.name}')
        metal_wide = pd.read_parquet(CACHE)
        print(f'    Rows: {len(metal_wide):,}')
    else:
        print('\n[3] Extracting metal concentrations from USGS long-format data...')
        usgs_meta = pd.read_parquet(
            USGS / 'usgs_geochem.parquet',
            columns=['lab_id', 'latitude', 'longitude', 'primary_class']
        )
        soil_meta = usgs_meta[
            (usgs_meta['primary_class'] == 'soil') &
            usgs_meta['latitude'].between(24, 50) &
            usgs_meta['longitude'].between(-125, -65)
        ].copy()
        print(f'    USA soil samples: {len(soil_meta):,}')
        soil_lab_ids = set(soil_meta['lab_id'].values)
        del usgs_meta

        pf = pq.ParquetFile(USGS / 'usgs_geochem_joined.parquet')
        metal_prefix_pat = r'^(As|Cd|Cr|Cu|Hg|Pb)_ppm_'
        chunks, total_rows = [], 0
        for batch in pf.iter_batches(
            batch_size=1_000_000,
            columns=['lab_id', 'parameter', 'qualified_value']
        ):
            df_b = batch.to_pandas()
            total_rows += len(df_b)
            mask_lab   = df_b['lab_id'].isin(soil_lab_ids)
            mask_metal = df_b['parameter'].str.match(metal_prefix_pat, na=False)
            sub = df_b[mask_lab & mask_metal].copy()
            if len(sub):
                sub['metal'] = sub['parameter'].str.split('_').str[0]
                chunks.append(sub[['lab_id', 'metal', 'qualified_value']])
            if total_rows % 10_000_000 == 0:
                print(f'    Read {total_rows/1e6:.0f}M rows ...', flush=True)

        metal_long = pd.concat(chunks, ignore_index=True)
        print(f'    Scanned {total_rows/1e6:.0f}M rows; kept {len(metal_long):,}')
        metal_long.loc[metal_long['qualified_value'] <= 0, 'qualified_value'] = np.nan
        metal_wide = (
            metal_long
            .groupby(['lab_id', 'metal'])['qualified_value']
            .median()
            .unstack('metal')
        )
        metal_wide.columns.name = None
        metal_wide = metal_wide.reset_index()
        for m in METALS:
            if m not in metal_wide.columns:
                metal_wide[m] = np.nan
        metal_wide = metal_wide.merge(
            soil_meta[['lab_id', 'latitude', 'longitude']], on='lab_id', how='inner'
        )
        del metal_long, soil_meta
        metal_wide.attrs = {}
        metal_wide.to_parquet(CACHE, index=False)
        print(f'    Cached to {CACHE.name}')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 4. Nearest-neighbor join: USA MAGs → USGS soil sample points
    # ------------------------------------------------------------------
    print(f'\n[4] Nearest-neighbor join (max {MAX_DIST}°)...')
    tree       = cKDTree(metal_wide[['latitude', 'longitude']].values)
    dists, idx = tree.query(usa_geo[['lat', 'lon']].values, k=1, workers=-1)
    usa_geo    = usa_geo.copy()
    usa_geo['nn_dist'] = dists
    usa_geo['nn_idx']  = idx
    within = usa_geo[usa_geo['nn_dist'] <= MAX_DIST].copy()
    print(f'    MAGs within {MAX_DIST}°: {len(within):,} ({len(within)/len(usa_geo)*100:.1f}%)')
    nn_metals = metal_wide[METALS].values[within['nn_idx'].values]
    for i, m in enumerate(METALS):
        within[m] = nn_metals[:, i]
    del tree, metal_wide
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 5. KO matrix (long → wide binary)
    # ------------------------------------------------------------------
    print('\n[5] Loading KO matrix...')
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
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 6. Merge + prevalence filter
    # ------------------------------------------------------------------
    df = within.merge(ko_wide, on='genome_id', how='inner')
    print(f'\n[6] Analysis dataset: {len(df):,} MAGs')
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
    # 7. Score test per metal with sg_pH in Z
    # ------------------------------------------------------------------
    print('\n[7] Running pH-adjusted score tests per metal...')
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

        # Standardize continuous covariates
        lat_std = df_m['lat'].values
        lat_std = (lat_std - lat_std.mean()) / lat_std.std()
        ph_vals = df_m['sg_pH'].values
        ph_std  = (ph_vals - ph_vals.mean()) / ph_vals.std()

        phy_dum = pd.get_dummies(df_m['phylum'], prefix='ph', drop_first=True).astype(float).values
        Z_arr   = np.column_stack([np.ones(len(df_m)), lat_std, ph_std, phy_dum])

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
    # 8. Save
    # ------------------------------------------------------------------
    out_path = OUT / 'nb15b_usa_usgs_ph_adjusted_per_ko_mwas.csv'
    results_df.to_csv(out_path, index=False)
    print(f'\n[8] Saved: {out_path}')

    # ------------------------------------------------------------------
    # 9. Survival vs NB15 (pH-unadjusted)
    # ------------------------------------------------------------------
    print('\n=== pH ADJUSTMENT SURVIVAL (NB15b vs NB15) ===')
    nb15 = pd.read_csv(OUT / 'nb15_usa_usgs_pointlevel_per_ko_mwas.csv')
    nb15_sig = nb15[nb15['q_value'] < 0.05]
    nb15_pairs  = set(zip(nb15_sig['ko_id'], nb15_sig['metal']))
    nb15b_pairs = set(zip(sig_df['ko_id'], sig_df['metal']))
    survived    = nb15_pairs & nb15b_pairs
    print(f'\nNB15 (unadjusted): {len(nb15_pairs)} sig pairs')
    print(f'NB15b (pH-adj):    {len(nb15b_pairs)} sig pairs')
    print(f'Survived pH control: {len(survived)} '
          f'({len(survived)/max(len(nb15_pairs),1)*100:.1f}% of NB15)')

    print('\nPer-metal survival:')
    for m in METALS:
        nb15_m   = {ko for ko, mt in nb15_pairs if mt == m}
        nb15b_m  = {ko for ko, mt in nb15b_pairs if mt == m}
        surv_m   = nb15_m & nb15b_m
        print(f'  {m}: {len(surv_m)}/{len(nb15_m)} survive '
              f'({len(surv_m)/max(len(nb15_m),1)*100:.1f}%)')

    # ------------------------------------------------------------------
    # 10. Cross-tabulation vs global MGnify + field-strict
    # ------------------------------------------------------------------
    print('\n=== CROSS-TABULATION (NB15b pH-adjusted) ===')
    global_df = pd.read_csv(OUT / 'mgnify_all_ko_associations.csv')
    global_sig = global_df[global_df['q_value'] < 0.05].copy()
    global_sig['metal_short'] = global_sig['metal'].str.replace('PF1_', '', regex=False)
    global_pairs = set(zip(global_sig['ko_id'], global_sig['metal_short']))
    ov_global = global_pairs & nb15b_pairs
    print(f'\nGlobal MGnify: {len(global_pairs)} sig pairs')
    print(f'Replicated in NB15b: {len(ov_global)} ({len(ov_global)/len(global_pairs)*100:.1f}%)')
    print('\nPer-metal (global → NB15b):')
    for m in METALS:
        g_m   = {ko for ko, mt in global_pairs if mt == m}
        b_m   = {ko for ko, mt in nb15b_pairs if mt == m}
        ov    = g_m & b_m
        print(f'  {m}: global={len(g_m)}, NB15b={len(b_m)}, overlap={len(ov)}')
    if ov_global:
        print('Overlapping KO×metal:')
        for ko, m in sorted(ov_global):
            print(f'  {ko} × {m}')

    spire_df = pd.read_csv(OUT / 'spire_all_ko_associations.csv')
    spire_sig = spire_df[spire_df['q_value'] < 0.05].copy()
    spire_sig['metal_short'] = spire_sig['metal'].str.replace('PF1_', '', regex=False)
    spire_pairs = set(zip(spire_sig['ko_id'], spire_sig['metal_short']))
    ov_spire = spire_pairs & nb15b_pairs
    print(f'\nSPIRE: {len(spire_pairs)} sig pairs')
    print(f'Replicated in NB15b: {len(ov_spire)} ({len(ov_spire)/len(spire_pairs)*100:.1f}%)')

    fs_df = pd.read_csv(OUT / 'field_strict_ko_annotations.csv')
    fs_kos     = set(fs_df['ko_id'])
    nb15b_kos  = set(sig_df['ko_id'])
    fs_in_nb15b = fs_kos & nb15b_kos
    print(f'\nField-strict KOs: {len(fs_kos)} total, {len(fs_in_nb15b)} in NB15b sig')
    if fs_in_nb15b:
        for ko in sorted(fs_in_nb15b):
            m_rows = sig_df[sig_df['ko_id'] == ko][['metal', 'q_value']].values
            for metal, qv in m_rows:
                print(f'  {ko} × {metal}  q={qv:.3f}')

    print('\n=== DONE ===')


if __name__ == '__main__':
    main()

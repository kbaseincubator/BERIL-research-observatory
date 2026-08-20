#!/usr/bin/env python3
"""
NB15: USA per-KO MWAS using USGS NGDB point-level soil data
============================================================
Corrects NB14's 0.5° grid (nb33_usgs_full_grid.parquet) with actual
USGS NGDB point samples (primary_class='soil'), joined by nearest-neighbor
to 1,473 USA MAG locations.

Data:
- 144K USA soil samples (primary_class='soil') with lat/lon
- 6 metals: As, Cd, Cr, Cu, Hg, Pb (median across methods per sample)
- Nearest-neighbor join to USA MAGs; max 1.0° (~90-110 km) cutoff

Controls: latitude (continuous) + phylum (categorical)
Method: OLS partial-correlation score test (vectorized, same as NB14)

Cross-tabulation:
- vs NB14 (grid-level, 476 sig pairs)
- vs global MGnify (219 sig pairs)
- vs SPIRE (75 sig pairs)
- vs 84 field-strict KOs
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
OUT  = PROJ / 'data'
USGS = Path('/home/hmacgregor/data/envdbs/usgs_geochem')

METALS    = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
MIN_PREV  = 20
MAX_DIST  = 1.0   # degrees; ~90-110 km at mid-USA latitudes


def score_test_metal(Y, x_m, Z_arr):
    """OLS partial-correlation score test for all KOs simultaneously.

    Returns (beta, t_stat, p_vals) for each column of Y.
    beta = OLS coefficient of x_m after partialling out Z.
    """
    n, K = Y.shape
    p = Z_arr.shape[1]
    df = n - p - 1

    Q, _ = np.linalg.qr(Z_arr, mode='reduced')

    x_proj  = Q @ (Q.T @ x_m)
    x_resid = x_m - x_proj
    x_ss    = float(np.dot(x_resid, x_resid))

    QTY    = Q.T @ Y
    Y_resid = Y - Q @ QTY

    cov_xy = x_resid @ Y_resid
    y_ss   = np.einsum('ij,ij->j', Y_resid, Y_resid)

    denom     = np.sqrt(x_ss * np.maximum(y_ss, 1e-12))
    r         = cov_xy / denom
    r_clipped = np.clip(r, -1 + 1e-9, 1 - 1e-9)
    t_stat    = r_clipped * np.sqrt(df) / np.sqrt(1 - r_clipped**2)
    p_vals    = 2 * t_dist.sf(np.abs(t_stat), df=df)
    beta      = cov_xy / x_ss

    return beta, t_stat, p_vals


def main():
    print('=== NB15: USA per-KO MWAS (USGS point-level soil data) ===')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 1. USA MAG lat/lon + phylum
    # ------------------------------------------------------------------
    print('\n[1] Loading USA MAG locations...')
    geo = pd.read_csv(MEP / 'data' / 'final_mags_geospatial_traits.csv')
    usa_mask = (
        geo['lat'].between(24, 50) &
        geo['lon'].between(-125, -65)
    )
    usa_geo = geo[usa_mask][['genome_id', 'lat', 'lon', 'phylum']].copy()
    print(f'    USA MAGs: {len(usa_geo):,}')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 2. USGS soil sample metadata (lat/lon, USA, primary_class='soil')
    # ------------------------------------------------------------------
    print('\n[2] Loading USGS soil sample metadata...')
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
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 3. Extract metal concentrations (chunked read of 46M-row parquet)
    # ------------------------------------------------------------------
    print('\n[3] Extracting metal concentrations from long-format USGS data...')
    pf = pq.ParquetFile(USGS / 'usgs_geochem_joined.parquet')

    metal_prefix_pat = r'^(As|Cd|Cr|Cu|Hg|Pb)_ppm_'
    chunks = []
    total_rows = 0
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
            kept = sum(len(c) for c in chunks)
            print(f'    Read {total_rows/1e6:.0f}M rows ... kept {kept:,}')
            sys.stdout.flush()

    metal_long = pd.concat(chunks, ignore_index=True)
    del chunks
    kept_rows = len(metal_long)
    print(f'    Total rows scanned: {total_rows/1e6:.0f}M')
    print(f'    Metal measurement rows retained: {kept_rows:,}')
    print(f'    Unique soil samples with metal data: {metal_long["lab_id"].nunique():,}')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 4. Pivot: median per (lab_id, metal); below-detection → NaN
    # ------------------------------------------------------------------
    print('\n[4] Pivoting to wide format (median per sample per metal)...')
    metal_long.loc[metal_long['qualified_value'] <= 0, 'qualified_value'] = np.nan
    metal_wide = (
        metal_long
        .groupby(['lab_id', 'metal'])['qualified_value']
        .median()
        .unstack('metal')
    )
    metal_wide.columns.name = None
    metal_wide = metal_wide.reset_index()

    # Ensure all 6 metals present as columns
    for m in METALS:
        if m not in metal_wide.columns:
            metal_wide[m] = np.nan

    metal_wide = metal_wide.merge(
        soil_meta[['lab_id', 'latitude', 'longitude']],
        on='lab_id', how='inner'
    )
    print(f'    Soil samples with ≥1 metal: {len(metal_wide):,}')
    for m in METALS:
        n_v = metal_wide[m].notna().sum()
        print(f'    {m}: {n_v:,} valid measurements')
    del metal_long, soil_meta
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 5. Nearest-neighbor join: USA MAGs → USGS soil sample points
    # ------------------------------------------------------------------
    print(f'\n[5] Nearest-neighbor join (max {MAX_DIST}°)...')
    usgs_coords = metal_wide[['latitude', 'longitude']].values
    tree = cKDTree(usgs_coords)
    mag_coords  = usa_geo[['lat', 'lon']].values
    dists, idx  = tree.query(mag_coords, k=1, workers=-1)

    usa_geo = usa_geo.copy()
    usa_geo['nn_dist'] = dists
    usa_geo['nn_idx']  = idx
    within = usa_geo[usa_geo['nn_dist'] <= MAX_DIST].copy()
    print(f'    MAGs within {MAX_DIST}° of a soil sample: {len(within):,} '
          f'({len(within)/len(usa_geo)*100:.1f}%)')

    nn_metals = metal_wide[METALS].values[within['nn_idx'].values]
    for i, m in enumerate(METALS):
        within[m] = nn_metals[:, i]
    del tree, metal_wide
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 6. KO matrix (long → wide binary)
    # ------------------------------------------------------------------
    print('\n[6] Loading and pivoting KO matrix...')
    usa_ids = set(within['genome_id'])
    ko_long = pd.read_parquet(
        PROJ / 'data' / 'mgnify_all_ko_matrix.parquet',
        columns=['genome_id', 'ko_id']
    )
    ko_long_usa = ko_long[ko_long['genome_id'].isin(usa_ids)].copy()
    del ko_long
    print(f'    USA genomes with KO data: {ko_long_usa["genome_id"].nunique():,}')
    ko_long_usa['present'] = np.uint8(1)
    ko_wide = ko_long_usa.pivot_table(
        index='genome_id', columns='ko_id', values='present',
        fill_value=0, aggfunc='max'
    )
    ko_wide.columns.name = None
    ko_wide = ko_wide.reset_index()
    print(f'    KO wide matrix: {ko_wide.shape}')
    del ko_long_usa
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 7. Merge + global prevalence filter
    # ------------------------------------------------------------------
    df = within.merge(ko_wide, on='genome_id', how='inner')
    print(f'\n[7] Analysis dataset: {len(df):,} MAGs')
    ko_cols  = [c for c in df.columns if c.startswith('K')]
    prev_all = df[ko_cols].sum()
    valid_kos = prev_all[prev_all >= MIN_PREV].index.tolist()
    print(f'    KOs passing global prevalence ≥ {MIN_PREV}: {len(valid_kos):,}')

    df['phylum'] = df['phylum'].fillna('Unknown')
    phy_counts   = df['phylum'].value_counts()
    df['phylum'] = df['phylum'].where(phy_counts[df['phylum']].values >= 5, 'Rare')
    print(f'    Unique phyla (after rare grouping): {df["phylum"].nunique()}')
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 8. Score test per metal (vectorized)
    # ------------------------------------------------------------------
    print('\n[8] Running OLS score tests per metal...')
    all_results = []

    for metal in METALS:
        valid_mask = df[metal].notna()
        n_valid = valid_mask.sum()
        if n_valid < 100:
            print(f'    {metal}: only {n_valid} non-missing MAGs, skipping')
            continue

        df_m = df[valid_mask].copy()
        Y_m  = df_m[valid_kos].values.astype(np.float64)

        # Per-metal prevalence filter (reapply within metal subset)
        prev_m    = Y_m.sum(axis=0)
        valid_m   = [k for k, p in zip(valid_kos, prev_m) if p >= MIN_PREV]
        if len(valid_m) == 0:
            print(f'    {metal}: no KOs pass prevalence filter in this subset, skipping')
            continue
        ki         = [valid_kos.index(k) for k in valid_m]
        Y_m_filt   = Y_m[:, ki].astype(np.float64)
        n_pos_m    = Y_m_filt.sum(axis=0).astype(int)

        # Standardize metal
        mu = df_m[metal].mean()
        sd = df_m[metal].std()
        if sd == 0:
            print(f'    {metal}: zero variance, skipping')
            continue
        x_m = ((df_m[metal] - mu) / sd).values.astype(np.float64)

        # Null design matrix Z = [intercept, lat, phylum_dummies]
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
    # 9. Save
    # ------------------------------------------------------------------
    out_path = OUT / 'nb15_usa_usgs_pointlevel_per_ko_mwas.csv'
    results_df.to_csv(out_path, index=False)
    print(f'\n[9] Saved: {out_path}')

    # ------------------------------------------------------------------
    # 10. Cross-tabulation
    # ------------------------------------------------------------------
    print('\n=== CROSS-TABULATION ===')
    nb15_pairs = set(zip(sig_df['ko_id'], sig_df['metal']))

    # NB14 (grid-level)
    nb14 = pd.read_csv(OUT / 'nb14_usa_usgs_per_ko_mwas.csv')
    nb14_sig   = nb14[nb14['q_value'] < 0.05]
    nb14_pairs = set(zip(nb14_sig['ko_id'], nb14_sig['metal']))
    ov_nb14    = nb14_pairs & nb15_pairs
    print(f'\nNB14 grid-level:  {len(nb14_pairs)} sig pairs')
    print(f'NB15 point-level: {len(nb15_pairs)} sig pairs')
    print(f'Agreement (same KO×metal in both): {len(ov_nb14)} '
          f'({len(ov_nb14)/max(len(nb14_pairs),1)*100:.1f}% of NB14)')
    if ov_nb14:
        for ko, m in sorted(ov_nb14):
            print(f'  {ko} × {m}')

    # Global MGnify (219 sig pairs, metals like 'PF1_As')
    global_df = pd.read_csv(OUT / 'mgnify_all_ko_associations.csv')
    global_sig = global_df[global_df['q_value'] < 0.05].copy()
    global_sig['metal_short'] = global_sig['metal'].str.replace('PF1_', '', regex=False)
    global_pairs = set(zip(global_sig['ko_id'], global_sig['metal_short']))
    ov_global    = global_pairs & nb15_pairs
    print(f'\nGlobal MGnify: {len(global_pairs)} sig pairs')
    print(f'Replicated in NB15: {len(ov_global)} ({len(ov_global)/len(global_pairs)*100:.1f}%)')
    print('\nPer-metal (global → NB15):')
    for m in METALS:
        g_m   = {ko for ko, mt in global_pairs if mt == m}
        nb15_m = {ko for ko, mt in nb15_pairs if mt == m}
        ov    = g_m & nb15_m
        print(f'  {m}: global={len(g_m)}, NB15={len(nb15_m)}, overlap={len(ov)}')
    if ov_global:
        print('Overlapping KO×metal:')
        for ko, m in sorted(ov_global):
            print(f'  {ko} × {m}')

    # SPIRE (75 sig pairs)
    spire_df  = pd.read_csv(OUT / 'spire_all_ko_associations.csv')
    spire_sig = spire_df[spire_df['q_value'] < 0.05].copy()
    spire_sig['metal_short'] = spire_sig['metal'].str.replace('PF1_', '', regex=False)
    spire_pairs = set(zip(spire_sig['ko_id'], spire_sig['metal_short']))
    ov_spire    = spire_pairs & nb15_pairs
    print(f'\nSPIRE: {len(spire_pairs)} sig pairs')
    print(f'Replicated in NB15: {len(ov_spire)} ({len(ov_spire)/len(spire_pairs)*100:.1f}%)')

    # Field-strict KOs (84)
    fs_df = pd.read_csv(OUT / 'field_strict_ko_annotations.csv')
    fs_kos    = set(fs_df['ko_id'])
    nb15_kos  = set(sig_df['ko_id'])
    fs_in_nb15 = fs_kos & nb15_kos
    print(f'\nField-strict KOs: {len(fs_kos)} total, {len(fs_in_nb15)} appear in NB15 sig')
    if fs_in_nb15:
        for ko in sorted(fs_in_nb15):
            m_rows = sig_df[sig_df['ko_id'] == ko][['metal', 'q_value']].values
            for metal, qv in m_rows:
                print(f'  {ko} × {metal}  q={qv:.3f}')

    print('\n=== DONE ===')


if __name__ == '__main__':
    main()

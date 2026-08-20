#!/usr/bin/env python3
"""
Firth logistic regression for 65 SPIRE-significant KO-metal pairs using
GEMAS European data with measured speciation drivers.

Model: KO_present ~ metal_AR_z + pH_CaCl2 + TOC_pct + log(genome_size) + log(n_mags_site)

Both metal and pH are measured at the same GEMAS site (not raster values).
This is the strongest available test of whether the KO-metal associations
survive speciation conditioning with actually measured soil properties.

Usage:
    python3 projects/per_ko_metal_associations/scripts/firth_gemas_measured_speciation.py
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm
from scipy.spatial import cKDTree
from pathlib import Path

REPO  = Path('/home/hmacgregor/BERIL-research-observatory')
DATA  = REPO / 'projects' / 'per_ko_metal_associations' / 'data'
ENVDB = Path('/home/hmacgregor/data/envdbs')

METALS = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
MAX_KM = 50.0
EARTH_R = 6371.0

GEMAS_METAL_MAP = {
    'As': 'As_ppm_AR', 'Cd': 'Cd_ppm_AR', 'Cr': 'Cr_ppm_AR',
    'Cu': 'Cu_ppm_AR', 'Hg': 'Hg_ppm_AR', 'Pb': 'Pb_ppm_AR',
}


def firth_logistic(X, y, max_iter=250, tol=1e-7):
    n, p = X.shape
    beta = np.zeros(p)
    for _ in range(max_iter):
        eta = X @ beta
        pi = expit(eta)
        W = pi * (1 - pi)
        XtWX = (X.T * W) @ X
        try:
            XtWX_inv = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        except np.linalg.LinAlgError:
            break
        sqW = np.sqrt(W)
        XsqW = X * sqW[:, None]
        H_diag = np.sum(XsqW * (XsqW @ XtWX_inv), axis=1)
        score = X.T @ (y - pi + H_diag * (0.5 - pi))
        try:
            delta = np.linalg.solve(XtWX + np.eye(p) * 1e-10, score)
        except np.linalg.LinAlgError:
            break
        beta_new = beta + delta
        if np.max(np.abs(delta)) < tol:
            beta = beta_new
            break
        beta = beta_new
    eta = X @ beta
    pi = expit(eta)
    W = pi * (1 - pi)
    XtWX = (X.T * W) @ X
    try:
        cov = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)
    z = beta / se
    pvalues = 2 * (1 - norm.cdf(np.abs(z)))
    return beta, se, pvalues


def benjamini_hochberg(pvalues):
    n = len(pvalues)
    if n == 0:
        return np.array([])
    sorted_idx = np.argsort(pvalues)
    sorted_p = pvalues[sorted_idx]
    qvalues = np.ones(n)
    for i in range(n - 1, -1, -1):
        qvalues[i] = min(n / (i + 1) * sorted_p[i],
                         qvalues[i + 1] if i < n - 1 else 1.0)
    q_out = np.empty(n)
    q_out[sorted_idx] = qvalues
    return q_out


def main():
    print("=" * 72)
    print("FIRTH — GEMAS MEASURED METALS + MEASURED pH + TOC")
    print("(European SPIRE MAGs only; both metal and pH measured at same site)")
    print("=" * 72)

    # Load SPIRE matrix
    print("\nLoading SPIRE KO matrix...")
    matrix = pd.read_parquet(DATA / 'spire_all_ko_matrix.parquet')
    spire_sites = matrix.drop_duplicates('genome_id')[
        ['genome_id', 'latitude', 'longitude', 'genome_size']
    ].copy()

    # European SPIRE sites
    eur = spire_sites[
        (spire_sites.latitude >= 28) & (spire_sites.latitude <= 71) &
        (spire_sites.longitude >= -17) & (spire_sites.longitude <= 41)
    ].copy()
    print(f"  European SPIRE MAGs: {len(eur)}")

    # Load GEMAS full parquet (has pH_CaCl2 and TOC_pct)
    print("\nLoading GEMAS full dataset...")
    gemas = pd.read_parquet(
        ENVDB / 'gemas_data/gemas_final.parquet',
        columns=['latitude', 'longitude',
                 'As_ppm_AR', 'Cd_ppm_AR', 'Cr_ppm_AR',
                 'Cu_ppm_AR', 'Hg_ppm_AR', 'Pb_ppm_AR',
                 'pH_CaCl2', 'TOC_pct']
    )
    gemas_ok = gemas.dropna(subset=['latitude', 'longitude']).copy()
    print(f"  GEMAS sites: {len(gemas_ok)}")
    print(f"  pH_CaCl2 non-null: {gemas_ok['pH_CaCl2'].notna().sum()}")
    print(f"  TOC_pct non-null:  {gemas_ok['TOC_pct'].notna().sum()}")

    # Z-score metals within GEMAS (AR ppm → dimensionless)
    for m in METALS:
        col = GEMAS_METAL_MAP[m]
        vals = gemas_ok[col].values.astype(float)
        mu, sd = np.nanmean(vals), np.nanstd(vals)
        gemas_ok[f'metal_z_{m}'] = (vals - mu) / sd if sd > 0 else np.nan

    # Z-score pH and TOC too (for coefficient interpretability)
    for col in ['pH_CaCl2', 'TOC_pct']:
        vals = gemas_ok[col].values.astype(float)
        mu, sd = np.nanmean(vals), np.nanstd(vals)
        gemas_ok[f'{col}_z'] = (vals - mu) / sd if sd > 0 else np.nan

    # Nearest-neighbour join: SPIRE European MAGs → GEMAS
    tree = cKDTree(np.radians(gemas_ok[['latitude', 'longitude']].values))
    dists_rad, idxs = tree.query(
        np.radians(eur[['latitude', 'longitude']].values), k=1,
        distance_upper_bound=MAX_KM / EARTH_R
    )
    dists_km = dists_rad * EARTH_R
    eur = eur.copy()
    eur['dist_km'] = dists_km
    matched = eur[dists_km < MAX_KM].copy()
    midxs = idxs[dists_km < MAX_KM]

    for m in METALS:
        matched[f'metal_z_{m}'] = gemas_ok[f'metal_z_{m}'].iloc[midxs].values
    matched['pH_CaCl2_z'] = gemas_ok['pH_CaCl2_z'].iloc[midxs].values
    matched['TOC_pct_z']  = gemas_ok['TOC_pct_z'].iloc[midxs].values
    print(f"\n  Matched within {MAX_KM} km: {len(matched)} European MAGs")

    # n_mags_site within matched set
    matched['lat_r'] = matched['latitude'].round(2)
    matched['lon_r'] = matched['longitude'].round(2)
    sc = matched.groupby(['lat_r','lon_r'])['genome_id'].count().reset_index()
    sc.columns = ['lat_r', 'lon_r', 'n_mags_site']
    matched = matched.merge(sc, on=['lat_r','lon_r'], how='left')
    matched['log_n_mags_site'] = np.log(matched['n_mags_site'].fillna(1).astype(float))

    # 50 km spatial thinning
    DEG = 0.45
    matched['lat_bin'] = (matched['latitude'] / DEG).round().astype(int)
    matched['lon_bin'] = (matched['longitude'] / DEG).round().astype(int)
    matched['grid_cell'] = matched['lat_bin'].astype(str) + '_' + matched['lon_bin'].astype(str)
    thin = (matched.sort_values('genome_size', ascending=False)
                   .drop_duplicates('grid_cell').copy())
    print(f"  After 50 km thinning: {len(thin)} independent cells")

    # KO presence lookup (all SPIRE MAGs, to get correct presence vectors)
    print("\nBuilding KO presence lookup...")
    ko_present_sets = {}
    for ko_id, grp in matrix.groupby('ko_id'):
        ko_present_sets[ko_id] = set(grp['genome_id'].values)

    # Target pairs
    firth_sig = pd.read_csv(DATA / 'ckpt_spire_firth_ko_associations.csv')
    targets = firth_sig[firth_sig['q_firth_total'] < 0.05].copy()
    print(f"  Target pairs: {len(targets)}")

    # Run Firth: two models
    # Model A (metal only):  KO ~ metal_z + log(genome_size) + log(n_mags)
    # Model B (+ pH + TOC):  KO ~ metal_z + pH_z + TOC_z + log(genome_size) + log(n_mags)
    print(f"\nRunning Firth for {len(targets)} pairs on {len(thin)} thinned cells...")

    results = []
    for _, row in targets.iterrows():
        ko_id  = row['ko_id']
        metal  = row['metal']
        mcol   = f'metal_z_{metal}'

        present_ids = ko_present_sets.get(ko_id, set())

        # Restrict to rows where metal AND pH AND TOC are non-null
        sub_B = thin[thin[mcol].notna() &
                     thin['pH_CaCl2_z'].notna() &
                     thin['TOC_pct_z'].notna()].copy()
        sub_A = thin[thin[mcol].notna()].copy()

        rec = {'ko_id': ko_id, 'metal': metal,
               'n_A': len(sub_A), 'n_B': len(sub_B),
               'beta_orig': row['beta_firth_total'],
               'p_orig': row['p_firth_total'],
               'q_orig': row['q_firth_total']}

        for label, sub in [('A', sub_A), ('B', sub_B)]:
            if len(sub) < 8:
                rec[f'note_{label}'] = 'too_few'
                continue
            y = sub['genome_id'].isin(present_ids).astype(int).values
            np_ = int(y.sum())
            if np_ == 0 or np_ == len(y):
                rec[f'note_{label}'] = 'separation'
                continue

            if label == 'A':
                X = np.column_stack([
                    np.ones(len(sub)),
                    sub[mcol].values,
                    np.log(sub['genome_size'].values),
                    sub['log_n_mags_site'].values,
                ])
            else:
                X = np.column_stack([
                    np.ones(len(sub)),
                    sub[mcol].values,
                    sub['pH_CaCl2_z'].values,
                    sub['TOC_pct_z'].values,
                    np.log(sub['genome_size'].values),
                    sub['log_n_mags_site'].values,
                ])

            try:
                beta, se, pvals = firth_logistic(X, y)
                rec[f'beta_{label}']  = beta[1]
                rec[f'se_{label}']    = se[1]
                rec[f'p_{label}']     = pvals[1]
                rec[f'n_present_{label}'] = np_
                rec[f'note_{label}']  = 'ok'
            except Exception as e:
                rec[f'note_{label}'] = f'error:{e}'

        results.append(rec)

    res = pd.DataFrame(results)

    # BH-FDR per model
    for label in ['A', 'B']:
        ok_mask = res.get(f'note_{label}', pd.Series('')) == 'ok'
        if ok_mask.any():
            res.loc[ok_mask, f'q_{label}'] = benjamini_hochberg(
                res.loc[ok_mask, f'p_{label}'].values
            )
            res.loc[ok_mask, f'same_sign_{label}'] = (
                np.sign(res.loc[ok_mask, f'beta_{label}']) ==
                np.sign(res.loc[ok_mask, 'beta_orig'])
            )

    # Save
    out = DATA / 'firth_gemas_measured_speciation_results.csv'
    res.to_csv(out, index=False)
    print(f"\n[Saved: {out}]")

    # Summary
    print("\n" + "=" * 72)
    print("RESULTS")
    print("=" * 72)

    for label, desc in [('A', 'Metal only (no pH/TOC)'), ('B', 'Metal + pH_measured + TOC_measured')]:
        ok = res[res.get(f'note_{label}', pd.Series('')).values == 'ok'].copy()
        if len(ok) == 0:
            print(f"\n  Model {label} ({desc}): no successful fits")
            continue

        fdr = int((ok[f'q_{label}'] < 0.05).sum()) if f'q_{label}' in ok.columns else 0
        nom = int((ok[f'p_{label}'] < 0.05).sum())
        ss  = int(ok[f'same_sign_{label}'].sum()) if f'same_sign_{label}' in ok.columns else 0
        ss_nom = int(((ok[f'p_{label}'] < 0.05) & (ok[f'same_sign_{label}'] == True)).sum()) \
            if f'same_sign_{label}' in ok.columns else 0
        med_n = ok[f'n_{label}'].median()

        print(f"\n  Model {label}: {desc}")
        print(f"    Fitted pairs:    {len(ok)}/{len(res)}")
        print(f"    Median n cells:  {med_n:.0f}")
        print(f"    Same direction:  {ss}/{len(ok)} ({ss/len(ok)*100:.1f}%)")
        print(f"    Nom. sig p<0.05: {nom}/{len(ok)}")
        print(f"    Nom. sig + same: {ss_nom}/{len(ok)}")
        print(f"    BH-FDR q<0.05:   {fdr}/{len(ok)}")

        if nom > 0:
            nom_df = ok[ok[f'p_{label}'] < 0.05].copy()
            print(f"\n    Nominally significant pairs:")
            print(f"    {'KO':10s} {'Metal':5s} {'β_meas':>8s} {'p':>8s} {'β_raster':>9s} {'Dir':>4s}")
            for _, r in nom_df.sort_values(f'p_{label}').iterrows():
                ss_sym = '✓' if r.get(f'same_sign_{label}', False) else '✗'
                print(f"    {r.ko_id:10s} {r.metal:5s} "
                      f"{r[f'beta_{label}']:+8.3f} "
                      f"{r[f'p_{label}']:8.4f} "
                      f"{r.beta_orig:+9.3f} {ss_sym:>4s}")

    print()
    print("  --- Four-way comparison ---")
    print(f"  {'Analysis':40s} {'n_cells':>8s} {'FDR':>5s} {'Dir%':>6s}")
    print("  " + "-" * 64)
    print(f"  {'SPIRE raster (full)':40s} {'2,477':>8s} {'65':>5s} {'—':>6s}")
    print(f"  {'Raster thinned 50 km':40s} {'312':>8s} {'0':>5s} {'81.5%':>6s}")
    print(f"  {'Measured total (GEMAS+USGS, 50 km thin)':40s} {'124':>8s} {'0':>5s} {'40.0%':>6s}")

    ok_B = res[res.get('note_B', pd.Series('')).values == 'ok']
    if len(ok_B) > 0:
        ss_B = int(ok_B['same_sign_B'].sum()) if 'same_sign_B' in ok_B.columns else 0
        fdr_B = int((ok_B['q_B'] < 0.05).sum()) if 'q_B' in ok_B.columns else 0
        n_cells_B = int(ok_B['n_B'].median())
        print(f"  {'Measured metal + pH + TOC (GEMAS EUR)':40s} "
              f"{n_cells_B:>8d} {fdr_B:>5d} {ss_B/len(ok_B)*100:>5.1f}%")

    print("=" * 72)


if __name__ == '__main__':
    main()

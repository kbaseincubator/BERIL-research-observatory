#!/usr/bin/env python3
"""
Spatial thinning sensitivity: re-run Firth logistic regression for the
69 Firth-significant KO-metal pairs after thinning SPIRE MAGs to one
representative per 50-km grid cell.

Goal: quantify how many of the 69 pairs survive with consistent direction
and nominal significance when pseudo-replication from raster metal values
is removed by ensuring no two sites share a grid cell.

Usage:
    python3 projects/per_ko_metal_associations/scripts/firth_spatial_thinning.py
"""

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm
from pathlib import Path

DATA = Path('projects/per_ko_metal_associations/data')

METAL_COL_MAP = {
    'As': 'PF1_As', 'Cd': 'PF1_Cd', 'Cr': 'PF1_Cr',
    'Cu': 'PF1_Cu', 'Hg': 'PF1_Hg', 'Pb': 'PF1_Pb',
}
IQR_VALUES = {
    'As': 0.041, 'Cd': 0.088, 'Cr': 0.077,
    'Cu': 0.028, 'Hg': 0.093, 'Pb': 0.032,
}


def firth_logistic(X, y, max_iter=250, tol=1e-7):
    n, p = X.shape
    beta = np.zeros(p)
    for _ in range(max_iter):
        eta = X @ beta
        pi = expit(eta)
        W = pi * (1 - pi)
        XtW = X.T * W
        XtWX = XtW @ X
        try:
            XtWX_inv = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        except np.linalg.LinAlgError:
            break
        sqW = np.sqrt(W)
        XsqW = X * sqW[:, None]
        H_diag = np.sum(XsqW * (XsqW @ XtWX_inv), axis=1)
        adj_resid = y - pi + H_diag * (0.5 - pi)
        score = X.T @ adj_resid
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
        qvalues[i] = min(n / (i + 1) * sorted_p[i], qvalues[i + 1] if i < n - 1 else 1.0)
    q_out = np.empty(n)
    q_out[sorted_idx] = qvalues
    return q_out


def main():
    print("=" * 70)
    print("SPATIAL THINNING SENSITIVITY (50 km grid, one MAG per cell)")
    print("=" * 70)

    # ── Load full SPIRE matrix ────────────────────────────────────────────
    print("\nLoading SPIRE matrix...")
    matrix = pd.read_parquet(DATA / 'spire_all_ko_matrix.parquet')

    # ── Spatial thinning ─────────────────────────────────────────────────
    sites = matrix.drop_duplicates('genome_id')[
        ['genome_id', 'latitude', 'longitude', 'genome_size',
         'PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb', 'sg_pH']
    ].copy()

    DEG = 0.45  # ~50 km at equator
    sites['lat_bin'] = (sites['latitude'] / DEG).round().astype(int)
    sites['lon_bin'] = (sites['longitude'] / DEG).round().astype(int)
    sites['grid_cell'] = sites['lat_bin'].astype(str) + '_' + sites['lon_bin'].astype(str)

    # One MAG per cell: keep largest genome (stable tie-breaker)
    thin_ids = (sites.sort_values('genome_size', ascending=False)
                     .drop_duplicates('grid_cell')['genome_id'].values)
    thin_set = set(thin_ids)

    n_full = len(sites)
    n_thin = len(thin_ids)
    print(f"  Full dataset: {n_full} MAGs")
    print(f"  After 50-km thinning: {n_thin} MAGs ({n_thin/n_full*100:.1f}% retained)")

    # ── Build thinned genome reference ───────────────────────────────────
    all_genomes = sites[sites['genome_id'].isin(thin_set)].copy()

    # log(n_mags_per_site): compute within the thinned set
    all_genomes['lat_r'] = all_genomes['latitude'].round(2)
    all_genomes['lon_r'] = all_genomes['longitude'].round(2)
    site_counts = (all_genomes.groupby(['lat_r', 'lon_r'])['genome_id']
                              .count().reset_index()
                              .rename(columns={'genome_id': 'n_mags_site'}))
    all_genomes = all_genomes.merge(site_counts, on=['lat_r', 'lon_r'], how='left')
    all_genomes['log_n_mags_site'] = np.log(all_genomes['n_mags_site'].fillna(1).astype(float))

    # ── Build KO presence lookup (thinned set only) ───────────────────────
    print("\nBuilding KO presence lookup (thinned MAGs)...")
    matrix_thin = matrix[matrix['genome_id'].isin(thin_set)]
    ko_present_sets = {}
    for ko_id, grp in matrix_thin.groupby('ko_id'):
        ko_present_sets[ko_id] = set(grp['genome_id'].values)
    print(f"  Indexed {len(ko_present_sets)} KOs")

    # ── Load 69 significant pairs from Firth checkpoint ───────────────────
    firth_sig = pd.read_csv(DATA / 'ckpt_spire_firth_ko_associations.csv')
    # Baseline-significant pairs only (the 69 that define the superset)
    targets = firth_sig[firth_sig['q_firth_total'] < 0.05].copy()
    print(f"\nRe-testing {len(targets)} Firth-significant pairs on thinned dataset...")

    # ── Run Firth on thinned data ────────────────────────────────────────
    results = []
    for idx, row in targets.iterrows():
        ko_id = row['ko_id']
        metal_short = row['metal']
        metal_col = METAL_COL_MAP[metal_short]
        iqr = IQR_VALUES[metal_short]

        present_ids = ko_present_sets.get(ko_id, set())

        genomes_total = all_genomes[all_genomes[metal_col].notna()].copy()
        genomes_direct = genomes_total[genomes_total['sg_pH'].notna()].copy()

        y_total = genomes_total['genome_id'].isin(present_ids).astype(int).values
        y_direct = genomes_direct['genome_id'].isin(present_ids).astype(int).values

        n_present_total = int(np.sum(y_total))
        n_total = len(y_total)
        n_present_direct = int(np.sum(y_direct))
        n_direct = len(y_direct)

        if n_present_total == 0 or n_present_total == n_total:
            print(f"  SKIP (separation): {ko_id} x {metal_short} "
                  f"(n_present={n_present_total}, n={n_total})")
            results.append({'ko_id': ko_id, 'metal': metal_short,
                            'note': 'separation_total', 'n_total': n_total, 'n_present': n_present_total})
            continue

        if n_present_direct == 0 or n_present_direct == n_direct:
            print(f"  SKIP (separation direct): {ko_id} x {metal_short}")
            results.append({'ko_id': ko_id, 'metal': metal_short,
                            'note': 'separation_direct', 'n_total': n_total, 'n_present': n_present_total})
            continue

        X_total = np.column_stack([
            np.ones(n_total),
            genomes_total[metal_col].values,
            np.log(genomes_total['genome_size'].values),
            genomes_total['log_n_mags_site'].values,
        ])
        X_direct = np.column_stack([
            np.ones(n_direct),
            genomes_direct[metal_col].values,
            np.log(genomes_direct['genome_size'].values),
            genomes_direct['sg_pH'].values,
            genomes_direct['log_n_mags_site'].values,
        ])

        try:
            b_total, se_total, p_total = firth_logistic(X_total, y_total)
            b_direct, se_direct, p_direct = firth_logistic(X_direct, y_direct)
        except Exception as e:
            print(f"  ERROR: {ko_id} x {metal_short}: {e}")
            continue

        results.append({
            'ko_id': ko_id, 'metal': metal_short, 'note': 'ok',
            'beta_thin_total': b_total[1], 'se_thin_total': se_total[1], 'p_thin_total': p_total[1],
            'beta_thin_direct': b_direct[1], 'se_thin_direct': se_direct[1], 'p_thin_direct': p_direct[1],
            'n_total': n_total, 'n_present': n_present_total,
            'n_direct': n_direct, 'n_present_direct': n_present_direct,
            # Original full-data values for comparison
            'beta_orig_total': row['beta_firth_total'], 'p_orig_total': row['p_firth_total'],
            'q_orig_total': row['q_firth_total'],
            'beta_orig_direct': row['beta_firth_direct'], 'p_orig_direct': row['p_firth_direct'],
            'q_orig_direct': row['q_firth_direct'],
        })

    res_df = pd.DataFrame(results)
    ok = res_df[res_df['note'] == 'ok'].copy()
    print(f"\nSuccessfully fit: {len(ok)} / {len(targets)} pairs")

    # ── Apply BH-FDR over the 69 thinned pairs ───────────────────────────
    if len(ok) > 0:
        ok['q_thin_total'] = benjamini_hochberg(ok['p_thin_total'].values)
        ok['q_thin_direct'] = benjamini_hochberg(ok['p_thin_direct'].values)
        ok['same_sign_total'] = np.sign(ok['beta_thin_total']) == np.sign(ok['beta_orig_total'])
        ok['same_sign_direct'] = np.sign(ok['beta_thin_direct']) == np.sign(ok['beta_orig_direct'])

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SURVIVAL SUMMARY")
    print("=" * 70)
    print(f"\nOriginal Firth-significant pairs tested: {len(targets)}")
    print(f"Successfully fit on thinned data: {len(ok)}")
    skipped = len(targets) - len(ok)
    print(f"Skipped (separation after thinning): {skipped}")

    if len(ok) > 0:
        same_sign_total = ok['same_sign_total'].sum()
        nom_sig = (ok['p_thin_total'] < 0.05).sum()
        bh_sig_total = (ok['q_thin_total'] < 0.05).sum()
        bh_sig_adj = ((ok['q_thin_total'] < 0.05) & (ok['q_thin_direct'] < 0.05)).sum()

        print(f"\n--- Total model (baseline) ---")
        print(f"Same direction as original: {same_sign_total} / {len(ok)} ({same_sign_total/len(ok)*100:.1f}%)")
        print(f"Nominally significant (p < 0.05): {nom_sig} / {len(ok)} ({nom_sig/len(ok)*100:.1f}%)")
        print(f"BH-FDR q < 0.05: {bh_sig_total} / {len(ok)} ({bh_sig_total/len(ok)*100:.1f}%)")
        print(f"BH-FDR q < 0.05 (both total + direct): {bh_sig_adj} / {len(ok)}")

        print(f"\n--- Per-metal breakdown (total model, p < 0.05) ---")
        for metal in sorted(ok['metal'].unique()):
            sub = ok[ok['metal'] == metal]
            n_nom = (sub['p_thin_total'] < 0.05).sum()
            n_ss = sub['same_sign_total'].sum()
            print(f"  {metal}: {n_nom}/{len(sub)} nominally significant, "
                  f"{n_ss}/{len(sub)} same direction")

        print(f"\n--- β attenuation (thin vs full) ---")
        ok['beta_ratio_total'] = ok['beta_thin_total'].abs() / ok['beta_orig_total'].abs()
        print(f"Median |β_thin|/|β_orig|: {ok['beta_ratio_total'].median():.3f}")
        print(f"Mean   |β_thin|/|β_orig|: {ok['beta_ratio_total'].mean():.3f}")

    # ── Save output ────────────────────────────────────────────────────────
    out_path = DATA / 'firth_spatial_thinning_results.csv'
    res_df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path} ({len(res_df)} rows)")

    # ── Detailed table of survivors ────────────────────────────────────────
    if len(ok) > 0:
        surv = ok[ok['p_thin_total'] < 0.05].copy()
        if len(surv) > 0:
            print(f"\n--- Nominally significant in thinned dataset ({len(surv)} pairs) ---")
            print(f"{'KO':10s} {'Metal':5s} {'β_thin':>8s} {'p_thin':>10s} {'β_orig':>8s} {'Sign?':>6s}")
            print("-" * 55)
            for _, r in surv.sort_values('p_thin_total').iterrows():
                ss = "✓" if r['same_sign_total'] else "✗"
                print(f"{r['ko_id']:10s} {r['metal']:5s} {r['beta_thin_total']:+8.3f} "
                      f"{r['p_thin_total']:10.4f} {r['beta_orig_total']:+8.3f} {ss:>6s}")

        lost = ok[ok['p_thin_total'] >= 0.05].copy()
        if len(lost) > 0:
            print(f"\n--- Lost in thinned dataset ({len(lost)} pairs) ---")
            print(f"{'KO':10s} {'Metal':5s} {'β_thin':>8s} {'p_thin':>10s} {'β_orig':>8s} {'Sign?':>6s}")
            print("-" * 55)
            for _, r in lost.sort_values('p_thin_total').iterrows():
                ss = "✓" if r['same_sign_total'] else "✗"
                print(f"{r['ko_id']:10s} {r['metal']:5s} {r['beta_thin_total']:+8.3f} "
                      f"{r['p_thin_total']:10.4f} {r['beta_orig_total']:+8.3f} {ss:>6s}")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()

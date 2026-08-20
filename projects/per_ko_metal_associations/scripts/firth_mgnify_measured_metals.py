#!/usr/bin/env python3
"""
Strongest validation: MGnify soil MAGs (independent MAG collection)
crossed with GEMAS + USGS measured soil metal concentrations (no raster).

Both the MAG collection and the metal values are independent of SPIRE.
Any signal that survives here is the most defensible evidence we have.

Usage:
    OMP_NUM_THREADS=1 python3 projects/per_ko_metal_associations/scripts/firth_mgnify_measured_metals.py
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.special import expit
from scipy.stats import norm
from scipy.spatial import cKDTree
from pathlib import Path

REPO  = Path('/home/hmacgregor/BERIL-research-observatory')
DATA  = REPO / 'projects' / 'per_ko_metal_associations' / 'data'
MEP   = REPO / 'projects' / 'metagenomic_environment_prediction' / 'data'
ENVDB = Path('/home/hmacgregor/data/envdbs')
USGS  = ENVDB / 'usgs_geochem'

METALS   = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
MAX_KM   = 50.0
EARTH_R  = 6371.0
DEG      = 0.45   # ~50 km at equator

# Cached USGS wide table (saves ~4 min on repeated runs)
USGS_WIDE_CACHE = DATA / 'usgs_soil_metal_wide.parquet'


# ── Firth helpers ──────────────────────────────────────────────────────────

def firth_logistic(X, y, max_iter=250, tol=1e-7):
    n, p = X.shape
    beta = np.zeros(p)
    for _ in range(max_iter):
        eta = X @ beta; pi = expit(eta); W = pi * (1 - pi)
        XtWX = (X.T * W) @ X
        try:
            XtWX_inv = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        except np.linalg.LinAlgError:
            break
        sqW = np.sqrt(W); XsqW = X * sqW[:, None]
        H_diag = np.sum(XsqW * (XsqW @ XtWX_inv), axis=1)
        score = X.T @ (y - pi + H_diag * (0.5 - pi))
        try:
            delta = np.linalg.solve(XtWX + np.eye(p) * 1e-10, score)
        except np.linalg.LinAlgError:
            break
        beta_new = beta + delta
        if np.max(np.abs(delta)) < tol:
            beta = beta_new; break
        beta = beta_new
    eta = X @ beta; pi = expit(eta); W = pi * (1 - pi)
    XtWX = (X.T * W) @ X
    try:
        cov = np.linalg.inv(XtWX + np.eye(p) * 1e-10); se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)
    z = beta / se; pvals = 2 * (1 - norm.cdf(np.abs(z)))
    return beta, se, pvals


def benjamini_hochberg(pvalues):
    n = len(pvalues)
    if n == 0: return np.array([])
    idx = np.argsort(pvalues); sp = pvalues[idx]; q = np.ones(n)
    for i in range(n - 1, -1, -1):
        q[i] = min(n / (i + 1) * sp[i], q[i + 1] if i < n - 1 else 1.0)
    q_out = np.empty(n); q_out[idx] = q; return q_out


def nn_join(query_ll, ref_ll, max_km):
    tree = cKDTree(np.radians(ref_ll))
    dr, idxs = tree.query(np.radians(query_ll), k=1,
                           distance_upper_bound=max_km / EARTH_R)
    dk = dr * EARTH_R; idxs[dk >= max_km] = -1
    return dk, idxs


def zscale(df, cols):
    for c in cols:
        v = df[c].values.astype(float)
        mu, sd = np.nanmean(v), np.nanstd(v)
        df[c] = (v - mu) / sd if sd > 0 else np.nan
    return df


# ── USGS wide metal table ──────────────────────────────────────────────────

def build_usgs_wide():
    if USGS_WIDE_CACHE.exists():
        print("  Loading USGS wide table from cache...")
        return pd.read_parquet(USGS_WIDE_CACHE)

    print("  Building USGS wide table (chunked read ~4 min)...")
    import re
    meta = pd.read_parquet(USGS / 'usgs_geochem.parquet',
                           columns=['lab_id', 'latitude', 'longitude', 'primary_class'])
    soil_meta = meta[
        (meta['primary_class'] == 'soil') &
        meta['latitude'].between(24, 72) &
        meta['longitude'].between(-140, -55) &
        meta['latitude'].notna()
    ].copy()
    soil_ids = set(soil_meta['lab_id'].values)
    del meta

    pat = re.compile(r'^(As|Cd|Cr|Cu|Hg|Pb)_ppm_')
    pf = pq.ParquetFile(USGS / 'usgs_geochem_joined.parquet')
    chunks = []
    rows = 0
    for batch in pf.iter_batches(batch_size=1_000_000,
                                  columns=['lab_id', 'parameter', 'qualified_value']):
        df = batch.to_pandas(); rows += len(df)
        m_lab = df['lab_id'].isin(soil_ids)
        m_met = df['parameter'].str.match(pat, na=False)
        sub = df[m_lab & m_met].copy()
        if len(sub):
            sub['metal'] = sub['parameter'].str.split('_').str[0]
            chunks.append(sub[['lab_id', 'metal', 'qualified_value']])
        if rows % 10_000_000 == 0:
            print(f"    {rows/1e6:.0f}M rows scanned...", flush=True)

    long = pd.concat(chunks, ignore_index=True)
    long.loc[long['qualified_value'] <= 0, 'qualified_value'] = np.nan
    wide = long.groupby(['lab_id', 'metal'])['qualified_value'].median().unstack('metal')
    wide.columns.name = None; wide = wide.reset_index()
    for m in METALS:
        if m not in wide.columns: wide[m] = np.nan
    wide = wide.merge(soil_meta[['lab_id', 'latitude', 'longitude']], on='lab_id', how='inner')
    wide.attrs = {}
    wide.to_parquet(USGS_WIDE_CACHE, index=False)
    print(f"  Saved USGS wide table: {len(wide):,} sites → {USGS_WIDE_CACHE}")
    return wide


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("FIRTH — MGnify MAGs × MEASURED METALS (GEMAS + USGS)")
    print("(Independent MAGs + independent metal concentrations)")
    print("=" * 72)

    # Load target pairs
    firth_sig = pd.read_csv(DATA / 'ckpt_spire_firth_ko_associations.csv')
    targets   = firth_sig[firth_sig['q_firth_total'] < 0.05].copy()
    print(f"\nTarget pairs: {len(targets)}")

    # Load MGnify soil MAG metadata
    print("\nLoading MGnify soil MAG metadata...")
    feat = pd.read_csv(MEP / 'mgnify_mag_feature_matrix.csv',
                       usecols=['genome_id', 'latitude', 'longitude',
                                'biome_name', 'length', 'completeness', 'contamination'])
    feat = feat[
        (feat['biome_name'] == 'Soil') &
        (feat['completeness'] >= 70) &
        (feat['contamination'] <= 10) &
        feat['latitude'].notna()
    ].rename(columns={'length': 'genome_size'}).copy()
    print(f"  MGnify soil MAGs: {len(feat)}")

    # Load KO cache (built by firth_mgnify_replication.py)
    print("\nLoading KO cache...")
    ko_df = pd.read_parquet(DATA / 'mgnify_target_ko_cache.parquet')
    ko_df = ko_df[ko_df['genome_id'].isin(set(feat['genome_id']))].copy()
    print(f"  {len(ko_df):,} (genome_id, ko_id) pairs for soil MAGs with coords")

    # ── GEMAS European join ──────────────────────────────────────────────
    print("\n[EUROPE] Joining MGnify European MAGs → GEMAS...")
    eur = feat[
        feat.latitude.between(28, 71) & feat.longitude.between(-17, 41)
    ].copy()
    print(f"  European MGnify soil MAGs: {len(eur)}")

    gemas = pd.read_parquet(
        ENVDB / 'gemas_data/gemas_final.parquet',
        columns=['latitude', 'longitude',
                 'As_ppm_AR', 'Cd_ppm_AR', 'Cr_ppm_AR',
                 'Cu_ppm_AR', 'Hg_ppm_AR', 'Pb_ppm_AR']
    ).dropna(subset=['latitude', 'longitude'])

    for m in METALS:
        v = gemas[f'{m}_ppm_AR'].values.astype(float)
        mu, sd = np.nanmean(v), np.nanstd(v)
        gemas[f'metal_z_{m}'] = (v - mu) / sd if sd > 0 else np.nan

    dk, idxs = nn_join(eur[['latitude','longitude']].values,
                       gemas[['latitude','longitude']].values, MAX_KM)
    eur_m = eur[idxs >= 0].copy(); midx = idxs[idxs >= 0]
    for m in METALS:
        eur_m[f'metal_z_{m}'] = gemas[f'metal_z_{m}'].iloc[midx].values
    eur_m['region'] = 'europe'
    print(f"  Matched: {len(eur_m)}/{len(eur)} within {MAX_KM} km")

    # ── USGS North American join ─────────────────────────────────────────
    print("\n[N. AMERICA] Joining MGnify N. American MAGs → USGS...")
    na = feat[
        feat.latitude.between(24, 72) & feat.longitude.between(-140, -55)
    ].copy()
    print(f"  N. American MGnify soil MAGs: {len(na)}")

    usgs_wide = build_usgs_wide()
    print(f"  USGS soil sites: {len(usgs_wide):,}")

    for m in METALS:
        v = usgs_wide[m].values.astype(float)
        mu, sd = np.nanmean(v), np.nanstd(v)
        usgs_wide[f'metal_z_{m}'] = (v - mu) / sd if sd > 0 else np.nan

    dk, idxs = nn_join(na[['latitude','longitude']].values,
                       usgs_wide[['latitude','longitude']].values, MAX_KM)
    na_m = na[idxs >= 0].copy(); midx = idxs[idxs >= 0]
    for m in METALS:
        na_m[f'metal_z_{m}'] = usgs_wide[f'metal_z_{m}'].iloc[midx].values
    na_m['region'] = 'north_america'
    print(f"  Matched: {len(na_m)}/{len(na)} within {MAX_KM} km")

    # ── Combine + thin ────────────────────────────────────────────────────
    parts = [df for df in [eur_m, na_m] if len(df) > 0]
    combined = pd.concat(parts, ignore_index=True, sort=False)
    print(f"\nCombined: {len(combined)} MGnify MAGs "
          f"({(combined.region=='europe').sum()} EUR + "
          f"{(combined.region=='north_america').sum()} NA)")

    combined['lat_r'] = combined.latitude.round(2)
    combined['lon_r'] = combined.longitude.round(2)
    sc = combined.groupby(['lat_r','lon_r'])['genome_id'].count().reset_index()
    sc.columns = ['lat_r','lon_r','n_mags_site']
    combined = combined.merge(sc, on=['lat_r','lon_r'], how='left')
    combined['log_n_mags_site'] = np.log(combined['n_mags_site'].fillna(1).astype(float))

    combined['lat_bin'] = (combined.latitude / DEG).round().astype(int)
    combined['lon_bin'] = (combined.longitude / DEG).round().astype(int)
    combined['grid_cell'] = combined.lat_bin.astype(str) + '_' + combined.lon_bin.astype(str)
    thin = (combined.sort_values('genome_size', ascending=False)
                    .drop_duplicates('grid_cell').copy())
    print(f"After 50 km thinning: {len(thin)} independent cells "
          f"({(thin.region=='europe').sum()} EUR + "
          f"{(thin.region=='north_america').sum()} NA)")

    # KO presence sets (thinned)
    thin_ids = set(thin['genome_id'])
    ko_thin  = ko_df[ko_df['genome_id'].isin(thin_ids)]
    ko_present = {}
    for ko_id, grp in ko_thin.groupby('ko_id'):
        ko_present[ko_id] = set(grp['genome_id'])

    # ── Firth ─────────────────────────────────────────────────────────────
    print(f"\nRunning Firth for {len(targets)} pairs on {len(thin)} thinned cells...")
    results = []
    for _, row in targets.iterrows():
        ko_id = row['ko_id']; metal = row['metal']; mcol = f'metal_z_{metal}'
        present_ids = ko_present.get(ko_id, set())
        sub = thin[thin[mcol].notna()].copy()

        rec = {'ko_id': ko_id, 'metal': metal,
               'n_total': len(sub),
               'beta_orig': row['beta_firth_total'],
               'p_orig':    row['p_firth_total'],
               'q_orig':    row['q_firth_total']}

        if len(sub) < 10:
            rec['note'] = 'too_few'; results.append(rec); continue
        y = sub['genome_id'].isin(present_ids).astype(int).values
        np_ = int(y.sum())
        if np_ == 0 or np_ == len(y):
            rec['note'] = 'separation'; rec['n_present'] = np_
            results.append(rec); continue

        X = np.column_stack([
            np.ones(len(sub)),
            sub[mcol].values,
            np.log(sub['genome_size'].values),
            sub['log_n_mags_site'].values,
        ])
        try:
            beta, se, pvals = firth_logistic(X, y)
            rec.update({'note': 'ok', 'beta_mgnify_meas': beta[1],
                        'se_mgnify_meas': se[1], 'p_mgnify_meas': pvals[1],
                        'n_present': np_})
        except Exception as e:
            rec['note'] = f'error:{e}'
        results.append(rec)

    res = pd.DataFrame(results)
    ok  = res[res['note'] == 'ok'].copy()

    if len(ok):
        ok['q_mgnify_meas'] = benjamini_hochberg(ok['p_mgnify_meas'].values)
        ok['same_sign']     = np.sign(ok['beta_mgnify_meas']) == np.sign(ok['beta_orig'])

    out = DATA / 'firth_mgnify_measured_metals_results.csv'
    res.to_csv(out, index=False)
    print(f"\n[Saved: {out}]")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("RESULTS — MGnify MAGs × MEASURED METALS")
    print("=" * 72)
    print(f"\nFitted: {len(ok)}/{len(targets)}")

    if len(ok):
        fdr  = int((ok['q_mgnify_meas'] < 0.05).sum())
        nom  = int((ok['p_mgnify_meas'] < 0.05).sum())
        ss   = int(ok['same_sign'].sum())
        ssn  = int(((ok['p_mgnify_meas'] < 0.05) & ok['same_sign']).sum())

        print(f"Same direction as SPIRE raster:     {ss}/{len(ok)} ({ss/len(ok)*100:.1f}%)")
        print(f"Nominally sig. p<0.05:              {nom}/{len(ok)}")
        print(f"Nom. sig AND same direction:         {ssn}/{len(ok)}")
        print(f"BH-FDR q<0.05:                      {fdr}/{len(ok)}")

        print(f"\n--- Per-metal ---")
        for m in METALS:
            s = ok[ok['metal'] == m]
            if not len(s): continue
            ns = int(s['same_sign'].sum()); nn = int((s['p_mgnify_meas'] < 0.05).sum())
            print(f"  {m}: {ns}/{len(s)} same sign, {nn}/{len(s)} nom. sig, "
                  f"median n={s['n_total'].median():.0f}")

        ok['beta_ratio'] = ok['beta_mgnify_meas'].abs() / ok['beta_orig'].abs()
        print(f"\nMedian |β_MGnify_meas|/|β_SPIRE|: {ok['beta_ratio'].median():.3f}")

        if nom:
            print(f"\n--- Nominally significant ({nom}) ---")
            print(f"{'KO':10s} {'Metal':5s} {'β_meas':>8s} {'p':>8s} {'q':>8s} {'β_SPIRE':>8s} Dir")
            print("-" * 62)
            for _, r in ok[ok['p_mgnify_meas'] < 0.05].sort_values('p_mgnify_meas').iterrows():
                s = '✓' if r['same_sign'] else '✗'
                print(f"{r.ko_id:10s} {r.metal:5s} "
                      f"{r.beta_mgnify_meas:+8.3f} {r.p_mgnify_meas:8.4f} "
                      f"{r.q_mgnify_meas:8.4f} {r.beta_orig:+8.3f} {s}")

        print(f"\n--- Full comparison ---")
        print(f"{'Analysis':44s} {'n_cells':>8s} {'FDR':>5s} {'Dir%':>6s}")
        print("-" * 68)
        rows_ = [
            ("SPIRE raster (full)",                 "2,477", "65",  "—"),
            ("Raster thinned 50 km",                  "312",  "0",  "81.5%"),
            ("Measured total (GEMAS+USGS SPIRE)",      "124",  "0",  "40.0%"),
            ("Measured + pH + TOC (GEMAS SPIRE)",       "32",  "0",  "39.7%"),
            ("MGnify × raster",                        "371",  "6",  "55.4%"),
        ]
        for label, nc, fdr_, dir_ in rows_:
            print(f"  {label:42s} {nc:>8s} {fdr_:>5s} {dir_:>6s}")
        print(f"  {'MGnify × measured (GEMAS+USGS)':42s} "
              f"{len(thin):>8d} {fdr:>5d} {ss/len(ok)*100:>5.1f}%")

    print("=" * 72)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Firth logistic regression for 65 SPIRE-significant KO-metal pairs using
REGIONALLY MEASURED soil metal concentrations instead of the CSU raster.

Metal sources (actual laboratory measurements):
  Europe  — GEMAS (4,343 sites, AR aqua-regia, cached locally)
  N. America — USGS NGDB (144K soil samples, chunked from usgs_geochem_joined.parquet)

Design:
  • Join each SPIRE MAG to nearest measured site within 50 km (haversine BallTree)
  • Z-score metal values WITHIN each dataset before combining (different units/ranges)
  • Run Firth total model: KO_present ~ metal_z + log(genome_size) + log(n_mags_site)
  • Apply BH-FDR across the 65 pairs
  • Compare direction and significance to SPIRE raster Firth results

Usage:
    cd /home/hmacgregor/BERIL-research-observatory
    OMP_NUM_THREADS=1 python3 projects/per_ko_metal_associations/scripts/firth_measured_metals.py
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.special import expit
from scipy.stats import norm
from scipy.spatial import cKDTree
from pathlib import Path

REPO  = Path('/home/hmacgregor/BERIL-research-observatory')
DATA  = REPO / 'projects' / 'per_ko_metal_associations' / 'data'
USGS  = Path('/home/hmacgregor/data/envdbs/usgs_geochem')

METALS = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
MAX_KM = 50.0
EARTH_R = 6371.0


# ── Firth logistic regression (same implementation as firth_reanalysis.py) ──

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


def nn_join(query_latlon, ref_latlon, max_km):
    """Return (dist_km, idx) for each query row; idx=-1 if no match within max_km."""
    tree = cKDTree(np.radians(ref_latlon))
    dists_rad, idxs = tree.query(np.radians(query_latlon), k=1,
                                  distance_upper_bound=max_km / EARTH_R)
    dists_km = dists_rad * EARTH_R
    no_match = dists_km >= max_km
    idxs[no_match] = -1
    return dists_km, idxs


def zscale_cols(df, cols):
    """In-place z-score of cols; returns df (same object)."""
    for c in cols:
        vals = df[c].values.astype(float)
        mu, sd = np.nanmean(vals), np.nanstd(vals)
        if sd > 0:
            df[c] = (vals - mu) / sd
        else:
            df[c] = np.nan
    return df


# ── Part 1: GEMAS European sites ──────────────────────────────────────────────

def build_europe_df(spire_sites, gemas_path):
    print("\n[EUROPE] Joining SPIRE European MAGs to GEMAS measured metals...")
    gemas = pd.read_csv(gemas_path)

    # GEMAS metal columns → standardise to our naming
    gemas_metal_map = {
        'gemas_As': 'As', 'gemas_Cd': 'Cd', 'gemas_Cr': 'Cr',
        'gemas_Cu': 'Cu', 'gemas_Hg': 'Hg', 'gemas_Pb': 'Pb',
    }
    gemas_has = [c for c in gemas_metal_map if c in gemas.columns]
    # Require at least As or Hg to be non-null
    gemas_ok = gemas.dropna(subset=['lat', 'lon']).copy()

    # Z-score GEMAS metals WITHIN the GEMAS dataset (AR ppm → dimensionless)
    for g_col, m_name in gemas_metal_map.items():
        if g_col in gemas_ok.columns:
            vals = gemas_ok[g_col].values.astype(float)
            mu, sd = np.nanmean(vals), np.nanstd(vals)
            gemas_ok[f'metal_z_{m_name}'] = (vals - mu) / sd if sd > 0 else np.nan

    # Restrict SPIRE sites to European bounding box
    eur = spire_sites[
        (spire_sites.latitude >= 28) & (spire_sites.latitude <= 71) &
        (spire_sites.longitude >= -17) & (spire_sites.longitude <= 41)
    ].copy()
    if len(eur) == 0:
        print("  No European SPIRE sites found.")
        return pd.DataFrame()

    # NN join to GEMAS
    dist_km, idxs = nn_join(
        eur[['latitude', 'longitude']].values,
        gemas_ok[['lat', 'lon']].values,
        MAX_KM
    )
    eur['dist_km'] = dist_km
    matched = eur[idxs >= 0].copy()
    matched_idx = idxs[idxs >= 0]

    # Attach z-scored metal values
    for m in METALS:
        zcol = f'metal_z_{m}'
        if zcol in gemas_ok.columns:
            matched[f'metal_z_{m}'] = gemas_ok[zcol].iloc[matched_idx].values
        else:
            matched[f'metal_z_{m}'] = np.nan

    matched['region'] = 'europe'
    print(f"  European SPIRE MAGs: {len(eur)} → {len(matched)} matched within {MAX_KM} km of GEMAS")
    for m in METALS:
        n_ok = matched[f'metal_z_{m}'].notna().sum()
        print(f"    {m}: {n_ok}/{len(matched)} non-null")
    return matched


# ── Part 2: USGS North American sites ────────────────────────────────────────

def build_northamerica_df(spire_sites, usgs_dir):
    print("\n[N. AMERICA] Joining SPIRE North American MAGs to USGS measured metals...")

    # Load USGS site metadata (lat/lon, primary_class)
    print("  Loading USGS site metadata...")
    usgs_meta = pd.read_parquet(
        usgs_dir / 'usgs_geochem.parquet',
        columns=['lab_id', 'latitude', 'longitude', 'primary_class']
    )
    soil_meta = usgs_meta[
        (usgs_meta['primary_class'] == 'soil') &
        usgs_meta['latitude'].between(24, 72) &
        usgs_meta['longitude'].between(-140, -55) &
        usgs_meta['latitude'].notna() & usgs_meta['longitude'].notna()
    ].copy()
    soil_lab_ids = set(soil_meta['lab_id'].values)
    print(f"  USGS soil samples (N. America): {len(soil_meta):,}")
    del usgs_meta

    # Chunked extraction of metal concentrations from the 46M-row joined parquet
    print("  Extracting metal concentrations (chunked read — ~2-4 min)...")
    metal_prefix_pat = r'^(As|Cd|Cr|Cu|Hg|Pb)_ppm_'
    pf = pq.ParquetFile(usgs_dir / 'usgs_geochem_joined.parquet')
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
            print(f"    Scanned {total_rows/1e6:.0f}M rows ...", flush=True)
    del pf

    metal_long = pd.concat(chunks, ignore_index=True)
    del chunks
    print(f"  Rows with metal data: {len(metal_long):,}")

    # Pivot: median per (lab_id, metal)
    metal_long.loc[metal_long['qualified_value'] <= 0, 'qualified_value'] = np.nan
    metal_wide = (
        metal_long.groupby(['lab_id', 'metal'])['qualified_value']
        .median().unstack('metal')
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
    print(f"  USGS wide table: {len(metal_wide):,} soil sites with ≥1 metal")
    for m in METALS:
        print(f"    {m}: {metal_wide[m].notna().sum():,}")

    # Z-score USGS metals WITHIN the USGS dataset
    for m in METALS:
        vals = metal_wide[m].values.astype(float)
        mu, sd = np.nanmean(vals), np.nanstd(vals)
        metal_wide[f'metal_z_{m}'] = (vals - mu) / sd if sd > 0 else np.nan

    # Restrict SPIRE sites to North American bounding box
    na = spire_sites[
        (spire_sites.latitude >= 24) & (spire_sites.latitude <= 72) &
        (spire_sites.longitude >= -140) & (spire_sites.longitude <= -55)
    ].copy()
    if len(na) == 0:
        print("  No N. American SPIRE sites found.")
        return pd.DataFrame()

    # NN join to USGS sites
    dist_km, idxs = nn_join(
        na[['latitude', 'longitude']].values,
        metal_wide[['latitude', 'longitude']].values,
        MAX_KM
    )
    na['dist_km'] = dist_km
    matched = na[idxs >= 0].copy()
    matched_idx = idxs[idxs >= 0]

    for m in METALS:
        zcol = f'metal_z_{m}'
        matched[f'metal_z_{m}'] = metal_wide[zcol].iloc[matched_idx].values

    matched['region'] = 'north_america'
    print(f"  N. American SPIRE MAGs: {len(na)} → {len(matched)} matched within {MAX_KM} km of USGS")
    for m in METALS:
        n_ok = matched[f'metal_z_{m}'].notna().sum()
        print(f"    {m}: {n_ok}/{len(matched)} non-null")
    return matched


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("FIRTH ANALYSIS — REGIONALLY MEASURED METAL DATA")
    print("(GEMAS Europe + USGS N. America, ≤50 km join)")
    print("=" * 72)

    # Load SPIRE matrix
    print("\nLoading SPIRE KO matrix...")
    matrix = pd.read_parquet(DATA / 'spire_all_ko_matrix.parquet')
    spire_sites = matrix.drop_duplicates('genome_id')[
        ['genome_id', 'latitude', 'longitude', 'genome_size']
    ].copy()
    print(f"  Total SPIRE MAGs: {len(spire_sites)}")

    # Build KO presence lookup
    print("Building KO presence lookup...")
    ko_present_sets = {}
    for ko_id, grp in matrix.groupby('ko_id'):
        ko_present_sets[ko_id] = set(grp['genome_id'].values)
    print(f"  Indexed {len(ko_present_sets)} KOs")

    # Load target pairs
    firth_sig = pd.read_csv(DATA / 'ckpt_spire_firth_ko_associations.csv')
    targets = firth_sig[firth_sig['q_firth_total'] < 0.05].copy()
    print(f"  Target pairs (SPIRE Firth q<0.05): {len(targets)}")

    # ── Build measured dataset ──────────────────────────────────────────────
    gemas_path = REPO / 'projects/comprehensive_metal_ecology/data/env_cache/gemas.csv'
    df_eur = build_europe_df(spire_sites, gemas_path)
    df_na  = build_northamerica_df(spire_sites, USGS)

    parts = [df for df in [df_eur, df_na] if len(df) > 0]
    if not parts:
        print("ERROR: no measured data matched. Exiting.")
        sys.exit(1)

    combined = pd.concat(parts, ignore_index=True, sort=False)
    print(f"\nCombined dataset: {len(combined)} MAGs "
          f"({(combined.region=='europe').sum()} EUR + "
          f"{(combined.region=='north_america').sum()} NA)")

    # log(n_mags_per_site) within the combined set
    combined['lat_r'] = combined['latitude'].round(2)
    combined['lon_r'] = combined['longitude'].round(2)
    site_counts = combined.groupby(['lat_r', 'lon_r'])['genome_id'].count().reset_index()
    site_counts.columns = ['lat_r', 'lon_r', 'n_mags_site']
    combined = combined.merge(site_counts, on=['lat_r', 'lon_r'], how='left')
    combined['log_n_mags_site'] = np.log(combined['n_mags_site'].fillna(1).astype(float))

    # ── 50 km spatial thinning on the measured dataset ──────────────────────
    DEG = 0.45
    combined['lat_bin'] = (combined['latitude'] / DEG).round().astype(int)
    combined['lon_bin'] = (combined['longitude'] / DEG).round().astype(int)
    combined['grid_cell'] = combined['lat_bin'].astype(str) + '_' + combined['lon_bin'].astype(str)
    thin = (combined.sort_values('genome_size', ascending=False)
                    .drop_duplicates('grid_cell').copy())
    print(f"After 50 km thinning: {len(thin)} spatially independent cells "
          f"({(thin.region=='europe').sum()} EUR + {(thin.region=='north_america').sum()} NA)")

    # ── Run Firth for each KO-metal pair ────────────────────────────────────
    print(f"\nRunning Firth for {len(targets)} pairs on thinned measured dataset...")
    results = []

    for _, row in targets.iterrows():
        ko_id     = row['ko_id']
        metal     = row['metal']
        metal_col = f'metal_z_{metal}'

        present_ids = ko_present_sets.get(ko_id, set())

        # Filter to rows with non-null measured metal value (thinned)
        sub = thin[thin[metal_col].notna()].copy()
        if len(sub) < 10:
            results.append({'ko_id': ko_id, 'metal': metal, 'note': 'too_few'})
            continue

        y = sub['genome_id'].isin(present_ids).astype(int).values
        n_present = int(np.sum(y))
        n_total   = len(y)

        if n_present == 0 or n_present == n_total:
            results.append({'ko_id': ko_id, 'metal': metal, 'note': 'separation',
                            'n_present': n_present, 'n_total': n_total})
            continue

        X = np.column_stack([
            np.ones(n_total),
            sub[metal_col].values,
            np.log(sub['genome_size'].values),
            sub['log_n_mags_site'].values,
        ])

        try:
            beta, se, pvals = firth_logistic(X, y)
        except Exception as e:
            results.append({'ko_id': ko_id, 'metal': metal, 'note': f'error:{e}'})
            continue

        results.append({
            'ko_id': ko_id, 'metal': metal, 'note': 'ok',
            'beta_measured': beta[1], 'se_measured': se[1], 'p_measured': pvals[1],
            'n_total': n_total, 'n_present': n_present,
            'beta_orig': row['beta_firth_total'], 'p_orig': row['p_firth_total'],
            'q_orig': row['q_firth_total'],
        })

    res_df = pd.DataFrame(results)
    ok = res_df[res_df['note'] == 'ok'].copy()

    if len(ok) > 0:
        ok['q_measured'] = benjamini_hochberg(ok['p_measured'].values)
        ok['same_sign']  = np.sign(ok['beta_measured']) == np.sign(ok['beta_orig'])

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("RESULTS — MEASURED DATA FIRTH")
    print("=" * 72)
    print(f"\nTarget pairs:             {len(targets)}")
    print(f"Successfully fit:         {len(ok)}")
    print(f"Skipped (separation/few): {len(targets) - len(ok)}")

    if len(ok) > 0:
        nom   = (ok['p_measured'] < 0.05).sum()
        fdr   = (ok['q_measured'] < 0.05).sum()
        ss    = ok['same_sign'].sum()
        ss_nom = ((ok['p_measured'] < 0.05) & ok['same_sign']).sum()
        print(f"\n--- Total model (measured z-score) ---")
        print(f"Same direction as SPIRE raster:       {ss}/{len(ok)} ({ss/len(ok)*100:.1f}%)")
        print(f"Nominally significant (p < 0.05):     {nom}/{len(ok)} ({nom/len(ok)*100:.1f}%)")
        print(f"Nom. sig AND same direction:           {ss_nom}/{len(ok)} ({ss_nom/len(ok)*100:.1f}%)")
        print(f"BH-FDR q < 0.05:                      {fdr}/{len(ok)}")

        print(f"\n--- Per-metal (p < 0.05, measured) ---")
        for m in sorted(ok['metal'].unique()):
            s = ok[ok['metal'] == m]
            n_nom = (s['p_measured'] < 0.05).sum()
            n_ss  = s['same_sign'].sum()
            n_mags_m = s['n_total'].median()
            print(f"  {m}: {n_nom}/{len(s)} nominally sig, "
                  f"{n_ss}/{len(s)} same sign, "
                  f"median n_thinned={n_mags_m:.0f}")

        print(f"\n--- β attenuation (measured vs SPIRE raster) ---")
        ok['beta_ratio'] = ok['beta_measured'].abs() / ok['beta_orig'].abs()
        print(f"Median |β_measured|/|β_raster|: {ok['beta_ratio'].median():.3f}")

        print(f"\n--- Nominally significant in measured dataset ---")
        print(f"{'KO':10s} {'Metal':5s} {'β_meas':>8s} {'p_meas':>10s} "
              f"{'β_raster':>9s} {'Sign?':>6s} {'region_counts':>15s}")
        print("-" * 70)
        nom_df = ok[ok['p_measured'] < 0.05].sort_values('p_measured')
        for _, r in nom_df.iterrows():
            ss_sym = '✓' if r['same_sign'] else '✗'
            # Count regions for this metal
            sub_r = thin[thin[f'metal_z_{r.metal}'].notna()]
            reg_str = (f"EUR={int((sub_r.region=='europe').sum())} "
                       f"NA={int((sub_r.region=='north_america').sum())}")
            print(f"{r.ko_id:10s} {r.metal:5s} {r.beta_measured:+8.3f} "
                  f"{r.p_measured:10.4f} {r.beta_orig:+9.3f} {ss_sym:>6s} {reg_str:>15s}")

        # Save results before comparison table (in case it errors)
        out = DATA / 'firth_measured_metals_results.csv'
        res_df.to_csv(out, index=False)
        print(f"\n[Saved: {out}]")

        # Comparison table
        print(f"\n--- Three-way comparison ---")
        print(f"{'Analysis':35s}  {'n_indep':>8s}  {'FDR sig':>8s}  {'Nom+Dir':>9s}  {'Dir%':>6s}")
        print("-" * 75)
        print(f"{'SPIRE raster (full)':35s}  {'2477':>8s}  {'65':>8s}  {'—':>9s}  {'—':>6s}")
        rast_thin = pd.read_csv(DATA / 'firth_spatial_thinning_results.csv')
        rast_ok = rast_thin[rast_thin['note'] == 'ok'] if 'note' in rast_thin.columns else rast_thin
        if len(rast_ok) > 0 and 'p_thin_total' in rast_ok.columns:
            # Compute same_sign_total if not pre-computed
            if 'same_sign_total' not in rast_ok.columns:
                rast_ok = rast_ok.copy()
                rast_ok['same_sign_total'] = (
                    np.sign(rast_ok['beta_thin_total']) == np.sign(rast_ok['beta_orig_total'])
                )
            r_nom_dir = ((rast_ok['p_thin_total'] < 0.05) & (rast_ok['same_sign_total'] == True)).sum()
            r_dir = rast_ok['same_sign_total'].mean() * 100
            print(f"{'SPIRE raster (50 km thinned)':35s}  {'312':>8s}  {'0':>8s}  "
                  f"{r_nom_dir:>9d}  {r_dir:>5.1f}%")
        print(f"{'Measured EUR+NA (50 km thinned)':35s}  {len(thin):>8d}  "
              f"{fdr:>8d}  {ss_nom:>9d}  {ss/len(ok)*100:>5.1f}%")

    print("=" * 72)


if __name__ == '__main__':
    main()

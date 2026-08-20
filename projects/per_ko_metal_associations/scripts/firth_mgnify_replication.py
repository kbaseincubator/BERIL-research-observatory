#!/usr/bin/env python3
"""
Cross-database replication: run Firth logistic regression for the 65
SPIRE-significant KO-metal pairs on MGnify MAGs (independent MAG collection).

Metal values: same CSU raster (Qi et al. 2025) joined via BallTree ≤50 km.
KO data: kescience_mgnify.gene_eggnog (Spark) → filtered to 52 target KOs.
Coordinates: mgnify_mag_feature_matrix.csv (8,849 MAGs with lat/lon).

If the associations are real biology rather than SPIRE-specific artifacts,
they should appear with consistent direction in the MGnify MAGs.

Usage (standalone, no JupyterHub required):
    OMP_NUM_THREADS=1 python3 projects/per_ko_metal_associations/scripts/firth_mgnify_replication.py
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import re
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm
from scipy.spatial import cKDTree
from pathlib import Path

REPO  = Path('/home/hmacgregor/BERIL-research-observatory')
DATA  = REPO / 'projects' / 'per_ko_metal_associations' / 'data'
MEP   = REPO / 'projects' / 'metagenomic_environment_prediction' / 'data'
ENVDB = Path('/home/hmacgregor/data/envdbs')

MAX_KM  = 50.0
EARTH_R = 6371.0
METALS  = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
PF1_COLS = {m: f'PF1_{m}' for m in METALS}

KO_CACHE = DATA / 'mgnify_target_ko_cache.parquet'  # built by this script


# ── Firth helpers (same as all other scripts in this project) ──────────────

def firth_logistic(X, y, max_iter=250, tol=1e-7):
    n, p = X.shape
    beta = np.zeros(p)
    for _ in range(max_iter):
        eta = X @ beta
        pi  = expit(eta)
        W   = pi * (1 - pi)
        XtWX = (X.T * W) @ X
        try:
            XtWX_inv = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        except np.linalg.LinAlgError:
            break
        sqW  = np.sqrt(W)
        XsqW = X * sqW[:, None]
        H_diag = np.sum(XsqW * (XsqW @ XtWX_inv), axis=1)
        score  = X.T @ (y - pi + H_diag * (0.5 - pi))
        try:
            delta = np.linalg.solve(XtWX + np.eye(p) * 1e-10, score)
        except np.linalg.LinAlgError:
            break
        beta_new = beta + delta
        if np.max(np.abs(delta)) < tol:
            beta = beta_new
            break
        beta = beta_new
    eta  = X @ beta
    pi   = expit(eta)
    W    = pi * (1 - pi)
    XtWX = (X.T * W) @ X
    try:
        cov = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        se  = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)
    z      = beta / se
    pvals  = 2 * (1 - norm.cdf(np.abs(z)))
    return beta, se, pvals


def benjamini_hochberg(pvalues):
    n = len(pvalues)
    if n == 0:
        return np.array([])
    idx   = np.argsort(pvalues)
    sp    = pvalues[idx]
    q     = np.ones(n)
    for i in range(n - 1, -1, -1):
        q[i] = min(n / (i + 1) * sp[i], q[i + 1] if i < n - 1 else 1.0)
    q_out = np.empty(n)
    q_out[idx] = q
    return q_out


# ── Part 1: Build KO cache from Spark ─────────────────────────────────────

def build_ko_cache(target_kos):
    """Query kescience_mgnify.gene_eggnog for target_kos; save to KO_CACHE."""
    print("  Connecting to Spark...")
    spark = None
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()
        print(f"  Spark {spark.version} connected via berdl_notebook_utils")
    except Exception as e1:
        try:
            sys.path.insert(0, str(REPO / 'tools'))
            from get_spark_session import get_spark_session
            spark = get_spark_session()
            print(f"  Spark {spark.version} connected via repo tools")
        except Exception as e2:
            print(f"  Spark unavailable ({e1}; {e2}). Cannot build KO cache.")
            return False

    from pyspark.sql import functions as F
    from pyspark.sql.types import ArrayType, StringType

    # UDF: parse comma-separated KEGG_ko field → list of K##### IDs
    @F.udf(returnType=ArrayType(StringType()))
    def extract_kos(kegg_ko_str):
        if not kegg_ko_str:
            return []
        return re.findall(r'K\d{5}', kegg_ko_str)

    ko_list_lit = target_kos  # Python list — will be broadcast

    print(f"  Querying kescience_mgnify.gene_eggnog for {len(ko_list_lit)} KOs...")
    raw = spark.sql("""
        SELECT genome_id, kegg_ko
        FROM kescience_mgnify.gene_eggnog
        WHERE kegg_ko IS NOT NULL AND kegg_ko != ''
    """)

    pairs = (
        raw
        .withColumn('ko_list', extract_kos(F.col('kegg_ko')))
        .select('genome_id', F.explode('ko_list').alias('ko_id'))
        .filter(F.col('ko_id').isin(ko_list_lit))
        .select('genome_id', 'ko_id')
        .dropDuplicates()
    )
    pairs_df = pairs.toPandas()
    pairs_df.attrs = {}

    spark.stop()
    spark = None
    print(f"  Found {len(pairs_df):,} (genome_id, ko_id) pairs")

    pairs_df.to_parquet(KO_CACHE, index=False)
    print(f"  Saved: {KO_CACHE}")
    return True


# ── Part 2: CSU raster join ────────────────────────────────────────────────

def join_csu(latlons_df):
    """Join lat/lon DataFrame to CSU metal mobility grid (≤50 km). Returns df with PF1_* cols."""
    print("  Loading CSU metal mobility grid...")
    csu = pd.read_parquet(
        ENVDB / 'bioavailable_metals/global_mobility_grid.parquet',
        columns=['latitude', 'longitude'] + [f'PF1_{m}' for m in METALS]
    )
    csu_coords = csu[['latitude', 'longitude']].values

    tree = cKDTree(np.radians(csu_coords))
    query_coords = np.radians(latlons_df[['latitude', 'longitude']].values)
    dists_rad, idxs = tree.query(query_coords, k=1,
                                  distance_upper_bound=MAX_KM / EARTH_R)
    dists_km = dists_rad * EARTH_R
    matched  = dists_km < MAX_KM

    out = latlons_df.copy()
    for m in METALS:
        col = f'PF1_{m}'
        vals = np.full(len(out), np.nan)
        vals[matched] = csu[col].iloc[idxs[matched]].values
        out[col] = vals

    n_match = matched.sum()
    print(f"  Matched {n_match}/{len(out)} MAGs to CSU raster within {MAX_KM} km")
    return out


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("FIRTH — MGnify MAGs (cross-database replication)")
    print("(same CSU raster; independent MAG collection)")
    print("=" * 72)

    # Load target pairs
    firth_sig = pd.read_csv(DATA / 'ckpt_spire_firth_ko_associations.csv')
    targets   = firth_sig[firth_sig['q_firth_total'] < 0.05].copy()
    target_kos = sorted(targets['ko_id'].unique().tolist())
    print(f"\nTarget pairs: {len(targets)} ({len(target_kos)} unique KOs)")

    # Load MGnify MAG metadata with lat/lon
    print("\nLoading MGnify MAG metadata...")
    feat = pd.read_csv(MEP / 'mgnify_mag_feature_matrix.csv',
                       usecols=['genome_id', 'latitude', 'longitude',
                                'biome_name', 'length', 'completeness', 'contamination'])
    # Soil MAGs only; QC filter
    feat = feat[
        (feat['biome_name'] == 'Soil') &
        (feat['completeness'] >= 70) &
        (feat['contamination'] <= 10) &
        feat['latitude'].notna() &
        feat['longitude'].notna()
    ].copy()
    feat = feat.rename(columns={'length': 'genome_size'})
    print(f"  Soil MGnify MAGs (QC-passed, with coords): {len(feat)}")

    # Build or load KO cache
    print("\nKO annotations for target KOs...")
    if KO_CACHE.exists():
        ko_df = pd.read_parquet(KO_CACHE)
        cached_kos = set(ko_df['ko_id'].unique())
        missing = set(target_kos) - cached_kos
        if missing:
            print(f"  Cache exists but missing {len(missing)} KOs — rebuilding from Spark")
            KO_CACHE.unlink()
            if not build_ko_cache(target_kos):
                sys.exit(1)
            ko_df = pd.read_parquet(KO_CACHE)
        else:
            print(f"  Loaded from cache: {len(ko_df):,} pairs, "
                  f"{ko_df['ko_id'].nunique()} unique KOs")
    else:
        print("  Cache not found — querying Spark")
        if not build_ko_cache(target_kos):
            sys.exit(1)
        ko_df = pd.read_parquet(KO_CACHE)

    # Restrict to MAGs that are in our feature matrix
    ko_df = ko_df[ko_df['genome_id'].isin(set(feat['genome_id'].values))].copy()
    print(f"  After restricting to soil MAGs with coords: {len(ko_df):,} pairs")
    print(f"  Coverage per target KO:")
    for ko in sorted(target_kos):
        n = int((ko_df['ko_id'] == ko).sum())
        print(f"    {ko}: {n} MAGs")

    # CSU raster join
    print("\nJoining MGnify soil MAGs to CSU raster...")
    feat = join_csu(feat)

    # n_mags_site within MGnify set
    feat['lat_r'] = feat['latitude'].round(2)
    feat['lon_r'] = feat['longitude'].round(2)
    sc = feat.groupby(['lat_r','lon_r'])['genome_id'].count().reset_index()
    sc.columns = ['lat_r', 'lon_r', 'n_mags_site']
    feat = feat.merge(sc, on=['lat_r','lon_r'], how='left')
    feat['log_n_mags_site'] = np.log(feat['n_mags_site'].fillna(1).astype(float))

    # 50 km spatial thinning
    DEG = 0.45
    feat['lat_bin'] = (feat['latitude'] / DEG).round().astype(int)
    feat['lon_bin'] = (feat['longitude'] / DEG).round().astype(int)
    feat['grid_cell'] = feat['lat_bin'].astype(str) + '_' + feat['lon_bin'].astype(str)
    thin = (feat.sort_values('genome_size', ascending=False)
                .drop_duplicates('grid_cell').copy())
    print(f"  After 50 km thinning: {len(thin)} independent cells")

    # Build KO presence sets (thinned MAGs)
    thin_ids = set(thin['genome_id'].values)
    ko_thin = ko_df[ko_df['genome_id'].isin(thin_ids)]
    ko_present_sets = {}
    for ko_id, grp in ko_thin.groupby('ko_id'):
        ko_present_sets[ko_id] = set(grp['genome_id'].values)

    # Run Firth for each target pair
    print(f"\nRunning Firth for {len(targets)} pairs on {len(thin)} thinned MGnify cells...")
    results = []
    for _, row in targets.iterrows():
        ko_id  = row['ko_id']
        metal  = row['metal']
        pf1col = f'PF1_{metal}'

        present_ids = ko_present_sets.get(ko_id, set())
        sub = thin[thin[pf1col].notna()].copy()

        if len(sub) < 10:
            results.append({'ko_id': ko_id, 'metal': metal, 'note': 'too_few',
                            'n_total': len(sub)})
            continue

        y = sub['genome_id'].isin(present_ids).astype(int).values
        np_ = int(y.sum())
        n   = len(y)

        if np_ == 0 or np_ == n:
            results.append({'ko_id': ko_id, 'metal': metal, 'note': 'separation',
                            'n_total': n, 'n_present': np_})
            continue

        X = np.column_stack([
            np.ones(n),
            sub[pf1col].values,
            np.log(sub['genome_size'].values),
            sub['log_n_mags_site'].values,
        ])

        try:
            beta, se, pvals = firth_logistic(X, y)
            results.append({
                'ko_id': ko_id, 'metal': metal, 'note': 'ok',
                'beta_mgnify': beta[1], 'se_mgnify': se[1], 'p_mgnify': pvals[1],
                'n_total': n, 'n_present': np_,
                'beta_orig': row['beta_firth_total'],
                'p_orig': row['p_firth_total'],
                'q_orig': row['q_firth_total'],
            })
        except Exception as e:
            results.append({'ko_id': ko_id, 'metal': metal, 'note': f'error:{e}'})

    res = pd.DataFrame(results)
    ok  = res[res['note'] == 'ok'].copy()

    if len(ok) > 0:
        ok['q_mgnify']   = benjamini_hochberg(ok['p_mgnify'].values)
        ok['same_sign']  = np.sign(ok['beta_mgnify']) == np.sign(ok['beta_orig'])

    # Save
    out = DATA / 'firth_mgnify_replication_results.csv'
    res.to_csv(out, index=False)
    print(f"\n[Saved: {out}]")

    # Summary
    print("\n" + "=" * 72)
    print("RESULTS — MGnify CROSS-DATABASE REPLICATION")
    print("=" * 72)
    skipped = len(res) - len(ok)
    print(f"\nTarget pairs:         {len(targets)}")
    print(f"Successfully fit:     {len(ok)}")
    print(f"Skipped:             {skipped}")

    if len(ok) > 0:
        fdr   = int((ok['q_mgnify'] < 0.05).sum())
        nom   = int((ok['p_mgnify'] < 0.05).sum())
        ss    = int(ok['same_sign'].sum())
        ss_nom= int(((ok['p_mgnify'] < 0.05) & ok['same_sign']).sum())
        med_n = ok['n_total'].median()

        print(f"\n--- Total model (CSU raster, MGnify MAGs) ---")
        print(f"Median n thinned cells:        {med_n:.0f}")
        print(f"Same direction as SPIRE:       {ss}/{len(ok)} ({ss/len(ok)*100:.1f}%)")
        print(f"Nominally sig. p<0.05:         {nom}/{len(ok)}")
        print(f"Nom. sig AND same direction:   {ss_nom}/{len(ok)}")
        print(f"BH-FDR q<0.05:                 {fdr}/{len(ok)}")

        print(f"\n--- Per-metal ---")
        for m in sorted(ok['metal'].unique()):
            s    = ok[ok['metal'] == m]
            n_ss = int(s['same_sign'].sum())
            n_nm = int((s['p_mgnify'] < 0.05).sum())
            print(f"  {m}: {n_ss}/{len(s)} same sign, "
                  f"{n_nm}/{len(s)} nominally sig, "
                  f"median n={s['n_total'].median():.0f}")

        print(f"\n--- β attenuation (MGnify vs SPIRE raster) ---")
        ok['beta_ratio'] = ok['beta_mgnify'].abs() / ok['beta_orig'].abs()
        print(f"Median |β_MGnify|/|β_SPIRE|:  {ok['beta_ratio'].median():.3f}")

        if nom > 0 or fdr > 0:
            show = ok[ok['p_mgnify'] < 0.05].sort_values('p_mgnify')
            print(f"\n--- Nominally significant ({len(show)}) ---")
            print(f"{'KO':10s} {'Metal':5s} {'β_MGnify':>9s} {'p':>8s} {'q':>8s} "
                  f"{'β_SPIRE':>8s} {'Dir':>4s}")
            print("-" * 60)
            for _, r in show.iterrows():
                ss_s = '✓' if r['same_sign'] else '✗'
                print(f"{r.ko_id:10s} {r.metal:5s} {r.beta_mgnify:+9.3f} "
                      f"{r.p_mgnify:8.4f} {r.q_mgnify:8.4f} "
                      f"{r.beta_orig:+8.3f} {ss_s:>4s}")

        print(f"\n--- Full comparison table ---")
        print(f"{'Analysis':42s} {'n_cells':>8s} {'FDR':>5s} {'Dir%':>6s}")
        print("-" * 66)
        print(f"{'SPIRE raster (full)':42s} {'2,477':>8s} {'65':>5s} {'—':>6s}")
        print(f"{'Raster thinned 50 km':42s} {'312':>8s} {'0':>5s} {'81.5%':>6s}")
        print(f"{'Measured total (GEMAS+USGS, 50 km)':42s} {'124':>8s} {'0':>5s} {'40.0%':>6s}")
        print(f"{'Measured + pH + TOC (GEMAS EUR)':42s} {'32':>8s} {'0':>5s} {'39.7%':>6s}")
        print(f"{'MGnify raster (cross-database)':42s} "
              f"{len(thin):>8d} {fdr:>5d} {ss/len(ok)*100:>5.1f}%")

    print("=" * 72)


if __name__ == '__main__':
    main()

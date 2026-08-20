#!/usr/bin/env python3
"""
Firth logistic regression for 65 SPIRE-significant KO-metal pairs using
NMDC community-level metagenomes × USGS measured metal concentrations.

Unit of analysis: whole metagenome (biosample), not individual MAG.
A metagenome "has" a KO if any annotated gene in the assembly has that annotation.
This tests whether community-level KO presence associates with measured local metals.

Metal source: USGS NGDB point-level soil samples (median concentration within 50 km).
Spatial thinning: 0.45° grid (~50 km), one metagenome per cell.
Covariate: latitude (to control for broad geographic gradients).

Usage:
    python3 projects/per_ko_metal_associations/scripts/firth_nmdc_community_metals.py
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm, binom
from scipy.spatial import cKDTree
from pathlib import Path

REPO  = Path('/home/hmacgregor/BERIL-research-observatory')
DATA  = REPO / 'projects' / 'per_ko_metal_associations' / 'data'
EARTH_R = 6371.0
MAX_KM  = 50.0
DEG     = 0.45  # ~50 km thinning grid


# ---------------------------------------------------------------------------
# Firth IRLS
# ---------------------------------------------------------------------------

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
    eta = X @ beta
    pi  = expit(eta)
    W   = pi * (1 - pi)
    XtWX = (X.T * W) @ X
    try:
        cov = np.linalg.inv(XtWX + np.eye(p) * 1e-10)
        se  = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)
    z = beta / se
    pvalues = 2 * (1 - norm.cdf(np.abs(z)))
    return beta, se, pvalues


def benjamini_hochberg(pvalues):
    n = len(pvalues)
    if n == 0:
        return np.array([])
    sorted_idx  = np.argsort(pvalues)
    sorted_p    = pvalues[sorted_idx]
    qvalues     = np.ones(n)
    for i in range(n - 1, -1, -1):
        qvalues[i] = min(n / (i + 1) * sorted_p[i],
                         qvalues[i + 1] if i < n - 1 else 1.0)
    q_out = np.empty(n)
    q_out[sorted_idx] = qvalues
    return q_out


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def get_nmdc_biosamples():
    """Return USA soil biosamples with lat/lon and workflow_run_id from NMDC."""
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()
    except Exception as e:
        raise RuntimeError(f'Cannot connect to Spark: {e}')

    import pyspark.sql.functions as F

    soil_terms = (
        'terrestrial biome', 'temperate woodland biome', 'cropland biome',
        'temperate grassland biome', 'temperate broadleaf forest biome',
        'forest biome', 'grassland biome', 'temperate mixed forest biome',
        'temperate shrubland biome', 'agricultural biome',
    )
    bs_df = spark.sql(f"""
        SELECT b.id AS biosample_id,
               CAST(b.lat_lon_latitude  AS DOUBLE) AS latitude,
               CAST(b.lat_lon_longitude AS DOUBLE) AS longitude,
               w.workflow_run_id
        FROM nmdc_metadata.biosample_set b
        JOIN nmdc_metadata.biosample_to_workflow_run w ON b.id = w.biosample_id
        JOIN (SELECT DISTINCT workflow_run_id
              FROM nmdc_results.annotation_kegg_orthology) ko
             ON w.workflow_run_id = ko.workflow_run_id
        WHERE (b.env_broad_scale_term_name IN {soil_terms}
               OR b.env_local_scale_term_name LIKE '%soil%')
          AND w.workflow_type = 'nmdc:MetagenomeAnnotation'
          AND b.lat_lon_latitude  IS NOT NULL
          AND CAST(b.lat_lon_latitude  AS DOUBLE) BETWEEN 24 AND 50
          AND CAST(b.lat_lon_longitude AS DOUBLE) BETWEEN -125 AND -65
    """).dropDuplicates(['biosample_id'])

    bs_pd = bs_df.toPandas()
    bs_pd.attrs = {}
    spark.stop()

    bs_pd['latitude']  = bs_pd['latitude'].astype(float)
    bs_pd['longitude'] = bs_pd['longitude'].astype(float)
    bs_pd = bs_pd.dropna(subset=['latitude', 'longitude'])
    print(f'  USA NMDC soil metagenomes: {len(bs_pd):,}')
    return bs_pd


def thin_biosamples(bs_pd):
    """One metagenome per 50 km cell, most-central (median lat/lon) as tie-breaker."""
    bs_pd = bs_pd.copy()
    bs_pd['lat_bin'] = (bs_pd['latitude']  / DEG).round().astype(int)
    bs_pd['lon_bin'] = (bs_pd['longitude'] / DEG).round().astype(int)
    bs_pd['grid_cell'] = bs_pd['lat_bin'].astype(str) + '_' + bs_pd['lon_bin'].astype(str)
    # Arbitrary tie-break: first occurrence after shuffle (reproducible)
    thinned = bs_pd.drop_duplicates('grid_cell').reset_index(drop=True)
    print(f'  After 50 km thinning: {len(thinned)} cells')
    return thinned


def join_usgs_metals(thinned):
    """Join USGS soil metal wide table within 50 km."""
    usgs_path = DATA / 'usgs_soil_metal_wide.parquet'
    usgs = pd.read_parquet(usgs_path)
    usgs = usgs.dropna(subset=['latitude', 'longitude']).drop_duplicates(['latitude', 'longitude'])

    tree = cKDTree(np.radians(usgs[['latitude', 'longitude']].values))
    dr, idx = tree.query(
        np.radians(thinned[['latitude', 'longitude']].values),
        k=1, distance_upper_bound=MAX_KM / EARTH_R
    )
    matched_mask = dr < MAX_KM / EARTH_R
    thinned = thinned.copy()
    thinned['dist_km_usgs'] = dr * EARTH_R

    metals = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
    for m in metals:
        thinned[f'usgs_{m}'] = np.nan
        thinned.loc[matched_mask, f'usgs_{m}'] = usgs[m].iloc[idx[matched_mask]].values

    n_matched = matched_mask.sum()
    print(f'  Thinned cells with USGS metals within 50 km: {n_matched} / {len(thinned)}')
    for m in metals:
        n = thinned[f'usgs_{m}'].notna().sum()
        print(f'    {m}: {n}/{n_matched}')

    return thinned[matched_mask].reset_index(drop=True)


def get_ko_presence(workflow_run_ids, target_kos):
    """
    Query NMDC annotation_kegg_orthology for target KO presence per workflow run.
    Returns DataFrame: workflow_run_id × ko_id (bool presence).
    """
    cache_path = DATA / 'nmdc_community_ko_presence.parquet'
    if cache_path.exists():
        print('  Loading cached KO presence matrix...')
        return pd.read_parquet(cache_path)

    print('  Querying NMDC KO annotations (1.8B rows, targeting 65 KOs)...')
    try:
        from berdl_notebook_utils.setup_spark_session import get_spark_session
        spark = get_spark_session()
    except Exception as e:
        raise RuntimeError(f'Cannot connect to Spark: {e}')

    import pyspark.sql.functions as F

    ko_list_quoted = [f"'KO:{k}'" for k in target_kos]
    ko_filter = f"({', '.join(ko_list_quoted)})"

    wf_list_quoted = [f"'{w}'" for w in workflow_run_ids]
    # Split into chunks to avoid huge IN clause
    chunk_size = 500
    results = []
    for i in range(0, len(wf_list_quoted), chunk_size):
        chunk = wf_list_quoted[i:i + chunk_size]
        wf_filter = f"({', '.join(chunk)})"
        chunk_df = spark.sql(f"""
            SELECT DISTINCT workflow_run_id,
                   REGEXP_REPLACE(annotation_id, '^KO:', '') AS ko_id
            FROM nmdc_results.annotation_kegg_orthology
            WHERE annotation_id IN {ko_filter}
              AND workflow_run_id IN {wf_filter}
        """)
        results.append(chunk_df.toPandas())
        print(f'    chunk {i // chunk_size + 1}/{(len(wf_list_quoted) + chunk_size - 1) // chunk_size} done')

    spark.stop()

    pairs = pd.concat(results, ignore_index=True)
    pairs.attrs = {}
    pairs['present'] = True
    presence = pairs.pivot_table(
        index='workflow_run_id', columns='ko_id',
        values='present', aggfunc='any', fill_value=False
    ).reset_index()

    presence.attrs = {}
    presence.to_parquet(cache_path, index=False)
    print(f'  Saved: {cache_path}')
    return presence


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('=' * 72)
    print('FIRTH — NMDC COMMUNITY METAGENOMES × USGS MEASURED METALS')
    print('(USA soil metagenomes; KO presence at community level)')
    print('=' * 72)

    # Target pairs from SPIRE raster analysis
    firth_sig = pd.read_csv(DATA / 'ckpt_spire_firth_ko_associations.csv')
    targets   = firth_sig[firth_sig['q_firth_total'] < 0.05].copy()
    target_kos = sorted(targets['ko_id'].unique())
    print(f'\nTarget pairs: {len(targets)} ({len(target_kos)} unique KOs)')

    # 1. Get NMDC biosamples
    print('\n[1] Loading NMDC USA soil biosamples...')
    bs = get_nmdc_biosamples()

    # 2. Spatial thinning
    print('\n[2] Spatial thinning...')
    thinned = thin_biosamples(bs)

    # 3. Join USGS metals
    print('\n[3] Joining USGS measured metals...')
    thinned = join_usgs_metals(thinned)

    # Z-score metals within USGS dataset
    metals = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
    for m in metals:
        col = f'usgs_{m}'
        vals = thinned[col].values.astype(float)
        mu, sd = np.nanmean(vals), np.nanstd(vals)
        thinned[f'metal_z_{m}'] = (vals - mu) / sd if sd > 0 else 0.0

    # Z-score latitude
    thinned['lat_z'] = (thinned['latitude'] - thinned['latitude'].mean()) / thinned['latitude'].std()

    # 4. Query KO presence per metagenome
    print('\n[4] Getting KO presence per metagenome...')
    wf_ids = thinned['workflow_run_id'].tolist()
    presence = get_ko_presence(wf_ids, target_kos)

    # Merge presence into thinned cells
    merged = thinned.merge(presence, on='workflow_run_id', how='left')
    print(f'  Merged: {len(merged)} rows (should equal thinned n={len(thinned)})')

    # KO prevalence across cells
    ko_cols = [c for c in presence.columns if c != 'workflow_run_id']
    print(f'\n  KO prevalence (fraction of metagenomes with KO):')
    for ko in sorted(target_kos):
        if ko in merged.columns:
            prev = merged[ko].fillna(False).mean()
            print(f'    {ko}: {prev:.3f}')

    # 5. Run Firth
    print(f'\n[5] Running Firth for {len(targets)} pairs on {len(merged)} metagenomes...')

    results = []
    for _, row in targets.iterrows():
        ko_id = row['ko_id']
        metal = row['metal']
        mcol  = f'metal_z_{metal}'

        rec = {
            'ko_id':     ko_id,
            'metal':     metal,
            'beta_orig': row['beta_firth_total'],
            'p_orig':    row['p_firth_total'],
            'q_orig':    row['q_firth_total'],
        }

        if ko_id not in merged.columns:
            rec['note'] = 'ko_absent_from_nmdc'
            results.append(rec)
            continue

        sub = merged[merged[mcol].notna()].copy()
        rec['n'] = len(sub)

        y = sub[ko_id].fillna(False).astype(int).values
        n_pos = int(y.sum())
        rec['n_present'] = n_pos

        if len(sub) < 8 or n_pos == 0 or n_pos == len(sub):
            rec['note'] = 'separation_or_too_few'
            results.append(rec)
            continue

        X = np.column_stack([
            np.ones(len(sub)),
            sub[mcol].values,
            sub['lat_z'].values,
        ])

        try:
            beta, se, pvals = firth_logistic(X, y)
            rec['beta']  = beta[1]
            rec['se']    = se[1]
            rec['p']     = pvals[1]
            rec['note']  = 'ok'
        except Exception as e:
            rec['note'] = f'error:{e}'

        results.append(rec)

    res = pd.DataFrame(results)

    # BH-FDR
    ok_mask = res['note'] == 'ok'
    if ok_mask.any():
        res.loc[ok_mask, 'q'] = benjamini_hochberg(res.loc[ok_mask, 'p'].values)
        res.loc[ok_mask, 'same_sign'] = (
            np.sign(res.loc[ok_mask, 'beta']) == np.sign(res.loc[ok_mask, 'beta_orig'])
        )

    # Save
    out = DATA / 'firth_nmdc_community_metals_results.csv'
    res.to_csv(out, index=False)
    print(f'\n[Saved: {out}]')

    # Summary
    print('\n' + '=' * 72)
    print('RESULTS')
    print('=' * 72)

    ok = res[ok_mask].copy()
    print(f'\nFitted pairs:    {len(ok)} / {len(res)}')
    print(f'Median n sites:  {ok["n"].median():.0f}')

    if len(ok) == 0:
        print('No successful fits.')
        return

    n_fdr  = int((ok['q'] < 0.05).sum())
    n_nom  = int((ok['p'] < 0.05).sum())
    n_same = int(ok['same_sign'].sum())

    print(f'Same direction:  {n_same}/{len(ok)} ({n_same/len(ok)*100:.1f}%)')
    binom_p = binom.sf(n_same - 1, len(ok), 0.5)
    print(f'Binomial p(≥{n_same}/2): {binom_p:.3f}')
    print(f'Nominally sig:   {n_nom}/{len(ok)}')
    print(f'BH-FDR q<0.05:   {n_fdr}/{len(ok)}')

    # β attenuation vs original SPIRE raster
    ok2 = ok[ok['beta_orig'].notna() & ok['beta'].notna()]
    if len(ok2) > 0:
        attenuation = np.median(np.abs(ok2['beta'].values) / np.abs(ok2['beta_orig'].values))
        print(f'Median |β_nmdc| / |β_raster|: ×{attenuation:.3f}')

    # Per-metal breakdown
    print('\n  Per-metal direction consistency:')
    for m in metals:
        sub_m = ok[ok['metal'] == m]
        if len(sub_m) == 0:
            continue
        ss = int(sub_m['same_sign'].sum())
        print(f'    {m}: {ss}/{len(sub_m)} ({ss/len(sub_m)*100:.1f}%)')

    if n_nom > 0:
        print(f'\n  Nominally significant pairs:')
        nom_df = ok[ok['p'] < 0.05].sort_values('p')
        print(f"  {'KO':10s} {'Metal':5s} {'β_nmdc':>8s} {'p':>8s} {'β_raster':>9s} {'Dir':>4s}")
        for _, r in nom_df.iterrows():
            ss_sym = '✓' if r.get('same_sign', False) else '✗'
            print(f"  {r.ko_id:10s} {r.metal:5s} "
                  f"{r['beta']:+8.3f} {r['p']:8.4f} {r.beta_orig:+9.3f} {ss_sym:>4s}")

    # 2×2 comparison table
    print('\n  --- Validation matrix summary ---')
    print(f'  {"Analysis":45s} {"n_sites":>8s} {"FDR":>5s} {"Dir%":>6s}')
    print('  ' + '-' * 68)
    print(f'  {"SPIRE raster (pseudo-replicated)":45s} {"2,477":>8s} {"65":>5s} {"—":>6s}')
    print(f'  {"SPIRE raster (50 km thinned)":45s} {"312":>8s} {"0":>5s} {"81.5%":>6s}')
    print(f'  {"SPIRE + measured GEMAS/USGS":45s} {"124":>8s} {"0":>5s} {"40.0%":>6s}')
    print(f'  {"MGnify + measured GEMAS/USGS":45s} {"138":>8s} {"0":>5s} {"44.6%":>6s}')
    if len(ok) > 0:
        ss_pct = f'{n_same/len(ok)*100:.1f}%'
        print(f'  {"NMDC community + measured USGS":45s} {len(ok):>8d} {n_fdr:>5d} {ss_pct:>6s}')
    print('=' * 72)


if __name__ == '__main__':
    main()

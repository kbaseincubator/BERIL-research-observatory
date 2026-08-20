"""
CWM per KO × USA × USGS measured metals.

Community-weighted mean KO prevalence per sample (MicrobeAtlas USA 16S surveys)
correlated with USGS measured soil metal concentrations.

Join path for ke_pangenome genus × KO prevalence:
  bakta_db_xrefs → gene_cluster → gtdb_species_clade → genus

Join path for MicrobeAtlas OTU relative abundances:
  sample_metadata (USA soil, lat/lon) → otu_counts_long → otu_metadata (genus taxonomy)

USGS join: ≤25 km (vs 200 km for NGSA → removes join-radius inflation).
Thinning: 50 km (0.45° grid), one sample per cell.
"""

import os, sys
import numpy as np, pandas as pd
from scipy import stats
from scipy.stats import rankdata

os.environ['OMP_NUM_THREADS'] = '1'
sys.path.append('/opt/conda/lib/python3.13/site-packages')

BASE     = '/home/hmacgregor/BERIL-research-observatory'
PROJ_MA  = f'{BASE}/projects/microbeatlas_metal_ecology'
PROJ_KO  = f'{BASE}/projects/per_ko_metal_associations'
CACHE    = f'{PROJ_MA}/data/usa_cwm'
os.makedirs(CACHE, exist_ok=True)

METALS   = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
DEG      = 0.45    # ~50 km thinning grid
USGS_KM  = 25      # join radius for USGS metals
R_EARTH  = 6371    # km

TARGET_KOS = [
    'K00077','K00368','K00425','K00426','K00549','K00859','K01056','K01193',
    'K01531','K01546','K01547','K01548','K01823','K02005','K02011','K02012',
    'K02021','K02564','K02755','K02756','K02757','K03272','K03429','K03605',
    'K03702','K03737','K03789','K03820','K03932','K04078','K04098','K04653',
    'K04654','K04655','K06201','K07054','K07093','K07217','K07646','K08217',
    'K09131','K09931','K10005','K10006','K10007','K10008','K14335','K15733',
    'K16013','K16014','K17331','K19147',
]

KO_LIST_SQL = "('" + "','".join(TARGET_KOS) + "')"


# ── Spark init ─────────────────────────────────────────────────────────────────
import berdl_notebook_utils
spark = berdl_notebook_utils.get_spark_session()
print("Spark OK")


# ── STEP 1+2 combined: CWM per (sample, KO) computed entirely in Spark ─────────
# Avoids temp view joins (Bug 3) and maxResultSize (Bug 6) by:
# - Embedding ke_pangenome computation inline as subquery (no temp view)
# - Computing aggregated CWM server-side before toPandas (result ≪ 1 GB)
#
# Pitfalls applied:
# - element_at(arr, -1): last element, null-safe (Bug 10 fix)
# - No temp views against catalog tables (Bug 3)
# - IN clause has only 52 items, well under 1K limit (Bug 5)

CACHE_CWM = f'{CACHE}/usa_cwm_per_ko.parquet'
if os.path.exists(CACHE_CWM):
    print(f"[STEP 1-2] Loading cached CWM: {CACHE_CWM}")
    cwm_long = pd.read_parquet(CACHE_CWM)
else:
    print("[STEP 1-2] Computing CWM per (sample, KO) in Spark (one query)...")

    cwm_spark = spark.sql(f"""
        SELECT
            m.sample_id,
            m.lat,
            m.lon,
            kp.ko_id,
            SUM(CAST(o.count AS DOUBLE) * kp.prevalence)
              / SUM(CAST(o.count AS DOUBLE)) AS cwm,
            SUM(CAST(o.count AS DOUBLE)) AS matched_count
        FROM arkinlab.microbeatlas.otu_counts_long o
        JOIN (
            SELECT sample_id, lat, lon
            FROM arkinlab.microbeatlas.sample_metadata
            WHERE lat BETWEEN 24 AND 50
              AND lon BETWEEN -125 AND -65
              AND environments LIKE '%soil%'
              AND lat IS NOT NULL AND lon IS NOT NULL
        ) m ON o.sample_id = m.sample_id
        JOIN arkinlab.microbeatlas.otu_metadata om ON o.otu_id = om.otu_id
        JOIN (
            SELECT num.genus_lower, num.ko_id,
                   CAST(num.n_with_ko AS DOUBLE) / CAST(den.n_total AS DOUBLE)
                     AS prevalence
            FROM (
                SELECT
                    LOWER(REGEXP_EXTRACT(sc.GTDB_taxonomy, 'g__([^;]+)', 1))
                        AS genus_lower,
                    x.accession AS ko_id,
                    COUNT(DISTINCT gc.gtdb_species_clade_id) AS n_with_ko
                FROM kbase.ke_pangenome.bakta_db_xrefs x
                JOIN kbase.ke_pangenome.gene_cluster gc
                    ON x.gene_cluster_id = gc.gene_cluster_id
                JOIN kbase.ke_pangenome.gtdb_species_clade sc
                    ON gc.gtdb_species_clade_id = sc.gtdb_species_clade_id
                WHERE x.db = 'KEGG'
                  AND x.accession IN {KO_LIST_SQL}
                  AND sc.GTDB_taxonomy LIKE '%g__%'
                GROUP BY genus_lower, ko_id
            ) num
            JOIN (
                SELECT
                    LOWER(REGEXP_EXTRACT(GTDB_taxonomy, 'g__([^;]+)', 1))
                        AS genus_lower,
                    COUNT(*) AS n_total
                FROM kbase.ke_pangenome.gtdb_species_clade
                WHERE GTDB_taxonomy LIKE '%g__%'
                GROUP BY genus_lower
            ) den ON num.genus_lower = den.genus_lower
        ) kp ON LOWER(element_at(SPLIT(om.tax, ';'), -1)) = kp.genus_lower
        WHERE om.tax IS NOT NULL
          AND SIZE(SPLIT(om.tax, ';')) >= 3
        GROUP BY m.sample_id, m.lat, m.lon, kp.ko_id
    """)

    n_rows = cwm_spark.count()
    print(f"  CWM result rows: {n_rows:,}")
    cwm_long = cwm_spark.toPandas(); cwm_long.attrs = {}
    cwm_long.to_parquet(CACHE_CWM, index=False)

print(f"  CWM: {cwm_long['sample_id'].nunique():,} samples × "
      f"{cwm_long['ko_id'].nunique()} KOs")


# ── STEP 4: USGS metal join (≤25 km) ──────────────────────────────────────────
CACHE_JOIN = f'{CACHE}/usa_cwm_usgs_joined.parquet'
if os.path.exists(CACHE_JOIN):
    print(f"[STEP 4] Loading cached USGS join: {CACHE_JOIN}")
    joined = pd.read_parquet(CACHE_JOIN)
else:
    print(f"[STEP 4] Joining to USGS metals (≤{USGS_KM} km)...")

    usgs = pd.read_parquet(f'{PROJ_KO}/data/usgs_soil_metal_wide.parquet')

    # Get unique sample locations from CWM
    locs = cwm_long[['sample_id','lat','lon']].drop_duplicates('sample_id').copy()

    # Nearest USGS site per sample (haversine, vectorized per chunk)
    def haversine_min(lat1, lon1, lat2_arr, lon2_arr):
        """Return min distance and index in lat2_arr/lon2_arr to (lat1, lon1)."""
        lat1_r = np.radians(lat1)
        lon1_r = np.radians(lon1)
        lat2_r = np.radians(lat2_arr)
        lon2_r = np.radians(lon2_arr)
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = np.sin(dlat/2)**2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon/2)**2
        km = 2 * R_EARTH * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        idx = np.argmin(km)
        return km[idx], idx

    usgs_lat = usgs['latitude'].values
    usgs_lon = usgs['longitude'].values

    matched_locs = []
    for _, row in locs.iterrows():
        dist, idx = haversine_min(row['lat'], row['lon'], usgs_lat, usgs_lon)
        if dist <= USGS_KM:
            matched_locs.append({
                'sample_id': row['sample_id'],
                'lat': row['lat'],
                'lon': row['lon'],
                'usgs_dist_km': dist,
                **{m: usgs.iloc[idx][m] for m in METALS}
            })

    loc_metals = pd.DataFrame(matched_locs).drop(columns=['lat', 'lon'])
    print(f"  Samples matched to USGS (≤{USGS_KM} km): {len(loc_metals):,} / {len(locs):,}")

    joined = cwm_long.merge(loc_metals, on='sample_id', how='inner')
    joined.attrs = {}
    joined.to_parquet(CACHE_JOIN, index=False)

print(f"  Joined: {joined['sample_id'].nunique():,} samples, {joined['ko_id'].nunique()} KOs")


# ── STEP 5: 50 km thinning ─────────────────────────────────────────────────────
print("[STEP 5] Thinning to 50 km cells...")
rng = np.random.default_rng(42)

# Determine lat/lon column names (handle possible _x suffix from merge)
lat_col = 'lat_x' if 'lat_x' in joined.columns else 'lat'
lon_col = 'lon_x' if 'lon_x' in joined.columns else 'lon'

# Thin on unique sample locations, then filter joined
locs_j = joined[['sample_id', lat_col, lon_col]].drop_duplicates('sample_id').copy()
locs_j = locs_j.rename(columns={lat_col: 'lat', lon_col: 'lon'})
locs_j['cell_lat'] = (locs_j['lat'] / DEG).apply(np.floor)
locs_j['cell_lon'] = (locs_j['lon'] / DEG).apply(np.floor)

kept_ids = set()
for _, grp in locs_j.groupby(['cell_lat','cell_lon']):
    kept_ids.add(rng.choice(grp['sample_id'].values))

joined_thin = joined[joined['sample_id'].isin(kept_ids)].copy()
n_thin = joined_thin['sample_id'].nunique()
n_full = joined['sample_id'].nunique()
print(f"  After thinning: {n_thin} samples (from {n_full})")


# ── STEP 6: Spearman per KO-metal pair ────────────────────────────────────────
print("[STEP 6] Spearman correlations...")

def spearman_sweep(df, label):
    rows = []
    for metal in METALS:
        if metal not in df.columns:
            continue
        for ko in TARGET_KOS:
            sub = df[df['ko_id'] == ko][['cwm', metal]].dropna()
            if sub['cwm'].std() == 0 or len(sub) < 20:
                continue
            rho, p = stats.spearmanr(sub[metal], sub['cwm'])
            rows.append({'ko_id': ko, 'metal': metal, 'rho': rho, 'p': p,
                         'n': len(sub)})
    if not rows:
        return pd.DataFrame()
    res = pd.DataFrame(rows)
    m = len(res)
    ranks = rankdata(res['p'])
    res['q_BH'] = np.minimum(res['p'] * m / ranks, 1.0)
    sig = (res['q_BH'] < 0.05).sum()
    print(f"\n{label}: n_tests={m}, FDR<0.05: {sig}/{m}")
    if sig:
        top = res[res['q_BH'] < 0.05].sort_values('q_BH')
        print(top[['ko_id','metal','rho','p','q_BH','n']].head(15).to_string())
    else:
        top5 = res.sort_values('q_BH').head(5)
        print("  Top 5 (all q>0.05):")
        print(top5[['ko_id','metal','rho','p','q_BH','n']].to_string())
    return res

res_full = spearman_sweep(joined,      "Unthinned")
res_thin = spearman_sweep(joined_thin, "50 km thinned")


# ── Save ───────────────────────────────────────────────────────────────────────
res_full['thinning'] = 'none'
res_thin['thinning'] = '50km'
combined = pd.concat([res_full, res_thin], ignore_index=True)
out = f'{PROJ_MA}/data/cwm_per_ko_usa_spearman.csv'
combined.to_csv(out, index=False)
print(f"\nSaved: {out}")

# Summary
print("\n=== FINAL SUMMARY ===")
for label, res in [("Unthinned", res_full), ("50km-thinned", res_thin)]:
    n_s = joined_thin['sample_id'].nunique() if label == '50km-thinned' else joined['sample_id'].nunique()
    sig = (res['q_BH'] < 0.05).sum() if len(res) else 0
    total = len(res)
    print(f"  {label}: n_samples≈{n_s}, tests={total}, FDR<0.05={sig}/{total}")
    if len(res):
        print(f"    rho range: {res['rho'].min():.3f} – {res['rho'].max():.3f}")

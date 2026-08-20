#!/usr/bin/env python3
"""
CWM per canonical mer KO × USA × USGS measured metals.

Test whether canonical mercury resistance genes (merA/merB = K16950/K00534)
are associated with soil Hg concentrations.

Based on cwm_per_ko_usa_usgs.py pattern, but for just 2 KOs.
"""

import os, sys
import numpy as np, pandas as pd
from scipy import stats
from scipy.stats import rankdata
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'
sys.path.append('/opt/conda/lib/python3.13/site-packages')

BASE     = '/home/hmacgregor/BERIL-research-observatory'
PROJ_MA  = Path(BASE) / 'projects' / 'microbeatlas_metal_ecology'
PROJ_KO  = Path(BASE) / 'projects' / 'per_ko_metal_associations'
OUT      = PROJ_MA / 'data'
OUT.mkdir(exist_ok=True, parents=True)

METALS   = ['As', 'Cd', 'Cr', 'Cu', 'Hg', 'Pb']
DEG      = 0.45    # ~50 km thinning grid
USGS_KM  = 25      # join radius for USGS metals
R_EARTH  = 6371    # km

# Canonical mercury resistance genes found in ke_pangenome
CANONICAL_MER_KOS = ['K16950', 'K00534']  # merA/merB equivalents
KO_LIST_SQL = "('" + "','".join(CANONICAL_MER_KOS) + "')"

print(f"[INFO] Testing canonical mer KOs: {CANONICAL_MER_KOS}")
print(f"[INFO] Output: {OUT}")

# ──────────────────────────────────────────────────────────────────────────────
# SPARK INIT
# ──────────────────────────────────────────────────────────────────────────────
import berdl_notebook_utils
spark = berdl_notebook_utils.get_spark_session()
print("[OK] Spark session initialized")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1: Verify canonical mer KOs exist in ke_pangenome
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("STEP 1: Verifying canonical mer KOs in ke_pangenome")
print("="*80)

verify_df = spark.sql(f"""
    SELECT accession, COUNT(DISTINCT gene_cluster_id) AS n_clusters
    FROM kbase.ke_pangenome.bakta_db_xrefs
    WHERE db = 'KEGG' AND accession IN {KO_LIST_SQL}
    GROUP BY accession
    ORDER BY n_clusters DESC
""").toPandas()

print(f"\nCanonical mer KEGG IDs found:")
print(verify_df.to_string(index=False))

if len(verify_df) == 0:
    print("[ERROR] No canonical mer KOs found in ke_pangenome!")
    sys.exit(1)

found_kos = verify_df['accession'].tolist()
print(f"\n[OK] Using {len(found_kos)} mer KOs: {found_kos}")

# Update list to only include KOs that exist
CANONICAL_MER_KOS = found_kos
KO_LIST_SQL = "('" + "','".join(CANONICAL_MER_KOS) + "')"

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2-3: Compute CWM per (sample, KO) in Spark
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("STEP 2-3: Computing CWM per (sample, KO)")
print("="*80)

print(f"[*] Computing CWM for {len(CANONICAL_MER_KOS)} canonical mer KOs...")

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
print(f"[OK] CWM computed: {n_rows:,} (sample, KO) pairs")

cwm_long = cwm_spark.toPandas()
cwm_long.attrs = {}

print(f"  Samples: {cwm_long['sample_id'].nunique():,}")
print(f"  KOs: {cwm_long['ko_id'].nunique()}")

if len(cwm_long) == 0:
    print("[ERROR] No CWM results! Exiting.")
    sys.exit(1)

print("\nFirst 10 rows:")
print(cwm_long.head(10).to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4: Join to USGS metals
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print(f"STEP 4: Joining to USGS metals (≤{USGS_KM} km)")
print("="*80)

usgs = pd.read_parquet(PROJ_KO / 'data' / 'usgs_soil_metal_wide.parquet')
print(f"[OK] Loaded {len(usgs)} USGS samples")

# Get unique sample locations from CWM
locs = cwm_long[['sample_id','lat','lon']].drop_duplicates('sample_id').copy()
print(f"[*] Joining {len(locs)} unique samples to USGS...")

# Nearest USGS site per sample (haversine, vectorized)
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
print(f"[OK] Matched to USGS (≤{USGS_KM} km): {len(loc_metals)} / {len(locs)}")

joined = cwm_long.merge(loc_metals, on='sample_id', how='inner')
print(f"[OK] Joined: {joined['sample_id'].nunique():,} samples, {joined['ko_id'].nunique()} KOs")

if len(joined) == 0:
    print("[ERROR] No samples matched between CWM and USGS!")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 5: 50 km thinning
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("STEP 5: Spatial thinning (50 km grid)")
print("="*80)

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
print(f"[OK] Thinned: {n_thin} samples (from {n_full})")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 6: Spearman per (KO, metal) pair
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("STEP 6: Spearman correlations")
print("="*80)

def spearman_sweep(df, label):
    rows = []
    for metal in METALS:
        if metal not in df.columns:
            continue
        for ko in CANONICAL_MER_KOS:
            sub = df[df['ko_id'] == ko][['cwm', metal]].dropna()
            if sub.empty or sub['cwm'].std() == 0 or len(sub) < 5:
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
        print(top[['ko_id','metal','rho','p','q_BH','n']].to_string(index=False))
    else:
        top5 = res.sort_values('q_BH').head(5)
        print("  Top 5 (all q>0.05):")
        print(top5[['ko_id','metal','rho','p','q_BH','n']].to_string(index=False))
    return res

res_full = spearman_sweep(joined,      "Unthinned")
res_thin = spearman_sweep(joined_thin, "50 km thinned")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 7: Save results
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("STEP 7: Saving results")
print("="*80)

if len(res_full) > 0 or len(res_thin) > 0:
    res_full['thinning'] = 'none' if len(res_full) > 0 else 'none'
    res_thin['thinning'] = '50km' if len(res_thin) > 0 else '50km'
    combined = pd.concat([res_full, res_thin], ignore_index=True)
else:
    combined = pd.DataFrame(columns=['ko_id', 'metal', 'rho', 'p', 'n', 'q_BH', 'thinning'])

out = OUT / 'cwm_canonical_mer_usa_spearman.csv'
combined.to_csv(out, index=False)
print(f"[OK] Results saved: {out}")

# ──────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)

print(f"""
Canonical Mercury Resistance Gene CWM Analysis
==============================================

Input data:
  - MicrobeAtlas USA soil 16S samples: {cwm_long['sample_id'].nunique():,}
  - USGS geochemistry samples: {len(usgs):,}
  - Joined (≤25 km): {joined['sample_id'].nunique():,}
  - After 50 km thinning: {n_thin} independent cells

Canonical mer KOs:
  - KEGG IDs: {', '.join(CANONICAL_MER_KOS)}
  - Prevalence range: {verify_df['n_clusters'].min()} – {verify_df['n_clusters'].max()} genome clusters

Statistical results:
  Unthinned:
    - Tests: {len(res_full) if len(res_full) > 0 else 0}
    - FDR<0.05: {(res_full['q_BH'] < 0.05).sum() if len(res_full) > 0 else 0}

  50km-thinned (n={n_thin} independent cells):
    - Tests: {len(res_thin) if len(res_thin) > 0 else 0}
    - FDR<0.05: {(res_thin['q_BH'] < 0.05).sum() if len(res_thin) > 0 else 0}

CONCLUSION FOR MERCURY (Hg):
""")

if len(res_thin) > 0:
    hg_thin = res_thin[res_thin['metal'] == 'Hg']
    if len(hg_thin) > 0:
        n_hg_sig = (hg_thin['q_BH'] < 0.05).sum()
        if n_hg_sig > 0:
            print(f"  ✓ SIGNIFICANT: {n_hg_sig} canonical mer KO(s) associated with Hg")
            print(hg_thin[hg_thin['q_BH'] < 0.05][['ko_id', 'rho', 'p', 'q_BH', 'n']].to_string(index=False))
        else:
            print(f"  ✗ NULL: Canonical mer genes do NOT associate with Hg (q>0.05)")
            if len(hg_thin) > 0:
                print(f"    {hg_thin[['ko_id', 'rho', 'p', 'q_BH', 'n']].to_string(index=False)}")
else:
    print(f"  ⚠ INSUFFICIENT DATA: No Hg results in thinned analysis")

print(f"\nOutput: {out}")

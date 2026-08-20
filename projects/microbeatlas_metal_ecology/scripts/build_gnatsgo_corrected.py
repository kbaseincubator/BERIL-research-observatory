#!/usr/bin/env python3
"""
build_gnatsgo_corrected.py

Replaces the faulty gNATSGO centroid-nearest-neighbor join with a correct approach:
  1. Sample MURASTER_30m_CONUS_2026.tif at each sample's lat/lon (WGS84 → EPSG:5070)
  2. Extract mukey from raster pixel value
  3. Query muaggatt directly from the GPKG for those mukeys (point-in-polygon equivalent)
  4. Rebuild covariate_matrix_634_v2.csv with corrected gNATSGO columns

Fixes: slope_pct, awc_0_25cm, hydrologic_group, flood_freq, land_cap_class, drainage_class_gnatsgo
Note: drainage_class (from SSURGO REST API) is kept as-is; gNATSGO drainage_class is
      added as a separate column for comparison only.

Usage: python3 build_gnatsgo_corrected.py
"""
import numpy as np
import pandas as pd
import sqlite3
import rasterio
from pyproj import Transformer
from pathlib import Path

DATA    = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
GPKG    = Path("/home/hmacgregor/data/envdbs/gNATSGO/extracted_gpkg/gNATSGO_gpkg_01_30_2026/gNATSGO_02_13_2026.gpkg")
RASTER  = Path("/home/hmacgregor/data/envdbs/gNATSGO/extracted_gpkg/gNATSGO_gpkg_01_30_2026/MURASTER_30m_CONUS_2026.tif")

# ── 0. Load base covariate matrix (v2) ───────────────────────────────────────
print("Loading covariate_matrix_634_v2.csv...")
cov = pd.read_csv(DATA / "covariate_matrix_634_v2.csv", keep_default_na=False, na_values=[''])
print(f"  Shape: {cov.shape}")

lats = cov['lat'].values
lons = cov['lon'].values
n = len(lats)

# ── 1. Transform WGS84 lat/lon → EPSG:5070 ───────────────────────────────────
print("Transforming coordinates to EPSG:5070 (Albers)...")
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)
xs, ys = transformer.transform(lons, lats)  # always_xy: lon, lat → x, y
print(f"  X range: {xs.min():.0f} – {xs.max():.0f}")
print(f"  Y range: {ys.min():.0f} – {ys.max():.0f}")

# ── 2. Sample MURASTER at each point ─────────────────────────────────────────
print("Sampling MURASTER_30m_CONUS_2026.tif...")
mukeys = np.zeros(n, dtype=np.int64)

with rasterio.open(RASTER) as src:
    # rasterio.sample expects (col, row) in pixel space; sample() handles transform
    coords_xy = list(zip(xs, ys))
    values = list(src.sample(coords_xy, indexes=1))

for i, v in enumerate(values):
    mukeys[i] = int(v[0]) if v[0] != 0 else -1  # 0 = NoData → -1

n_valid = (mukeys > 0).sum()
n_nodata = (mukeys <= 0).sum()
print(f"  Valid mukeys: {n_valid}/{n}  (NoData / off-grid: {n_nodata})")
print(f"  Unique mukeys: {len(set(mukeys[mukeys > 0]))}")

# ── 3. Query muaggatt for these mukeys ───────────────────────────────────────
print(f"Querying muaggatt from GPKG...")
valid_mukeys = [int(m) for m in mukeys if m > 0]
placeholders = ','.join(['?'] * len(valid_mukeys))

conn = sqlite3.connect(GPKG)
query = f"""
SELECT mukey,
       slopegradwta   AS slope_pct_gn,
       aws025wta      AS awc_0_25cm_gn,
       drclassdcd     AS drainage_class_gn,
       hydgrpdcd      AS hydrologic_group_gn,
       flodfreqdcd    AS flood_freq_gn,
       niccdcd        AS land_cap_class_gn,
       hydclprs       AS hydric_class_presence_gn,
       pondfreqprs    AS ponding_freq_gn,
       wtdepannmin    AS wtd_annual_min_gn
FROM muaggatt
WHERE mukey IN ({placeholders})
"""
muagg = pd.read_sql_query(query, conn, params=valid_mukeys)
conn.close()

print(f"  muaggatt rows returned: {len(muagg)}")
muagg_dict = {int(row.mukey): row for _, row in muagg.iterrows()}

# ── 4. Merge attributes into covariate matrix ────────────────────────────────
print("Merging corrected gNATSGO attributes...")
gn_cols = ['slope_pct_gn', 'awc_0_25cm_gn', 'drainage_class_gn', 'hydrologic_group_gn',
           'flood_freq_gn', 'land_cap_class_gn', 'hydric_class_presence_gn',
           'ponding_freq_gn', 'wtd_annual_min_gn']
for col in gn_cols:
    cov[col] = np.nan if col not in ['drainage_class_gn', 'hydrologic_group_gn',
                                      'flood_freq_gn', 'land_cap_class_gn',
                                      'hydric_class_presence_gn', 'ponding_freq_gn'] else None

for i, mk in enumerate(mukeys):
    if mk <= 0 or mk not in muagg_dict:
        continue
    row = muagg_dict[mk]
    for col in gn_cols:
        cov.at[i, col] = row[col]

# ── 5. Coverage report ────────────────────────────────────────────────────────
print("\n=== Coverage of corrected gNATSGO columns ===")
for col in gn_cols:
    n_nn = cov[col].notna().sum()
    print(f"  {col}: {n_nn}/{n} ({n_nn/n*100:.1f}%)")

# Compare corrected vs original slope/drainage
print("\n=== Corrected vs original slope_pct correlation ===")
both_slope = cov[['slope_pct', 'slope_pct_gn']].dropna()
if len(both_slope) > 10:
    r = both_slope.corr(method='spearman').iloc[0, 1]
    print(f"  Spearman r(slope_pct_orig vs slope_pct_gn): {r:.3f}  n={len(both_slope)}")

print("\n=== Corrected vs SSURGO drainage_class ===")
both_drain = cov[cov['drainage_class'].notna() & cov['drainage_class_gn'].notna()].copy()
print(f"  Both non-NA: {len(both_drain)}")
order = {'Excessively drained':1,'Somewhat excessively drained':2,'Well drained':3,
         'Moderately well drained':4,'Somewhat poorly drained':5,'Poorly drained':6,'Very poorly drained':7}
both_drain['ss_num'] = both_drain['drainage_class'].map(order)
both_drain['gn_num'] = both_drain['drainage_class_gn'].map(order)
valid_drain = both_drain[both_drain['ss_num'].notna() & both_drain['gn_num'].notna()]
if len(valid_drain) > 10:
    from scipy import stats
    r, p = stats.spearmanr(valid_drain['ss_num'], valid_drain['gn_num'])
    exact = (valid_drain['ss_num'] == valid_drain['gn_num']).sum()
    within1 = (abs(valid_drain['ss_num'] - valid_drain['gn_num']) <= 1).sum()
    print(f"  Corrected gNATSGO vs SSURGO drainage: Spearman r={r:.3f}, p={p:.2e}")
    print(f"  Exact agreement: {exact}/{len(valid_drain)} ({exact/len(valid_drain)*100:.1f}%)")
    print(f"  Within 1 class:  {within1}/{len(valid_drain)} ({within1/len(valid_drain)*100:.1f}%)")

# ── 6. Replace faulty columns in covariate matrix ────────────────────────────
print("\nReplacing faulty centroid-based columns with corrected raster-based columns...")
replacements = {
    'slope_pct':      'slope_pct_gn',
    'awc_0_25cm':     'awc_0_25cm_gn',
    'hydrologic_group': 'hydrologic_group_gn',
    'flood_freq':     'flood_freq_gn',
    'land_cap_class': 'land_cap_class_gn',
    'hydric_pct':     'hydric_class_presence_gn',
    'ponding_pct':    'ponding_freq_gn',
}
for orig, corrected in replacements.items():
    if corrected in cov.columns:
        cov[orig] = cov[corrected]
        n_ok = cov[orig].notna().sum()
        print(f"  {orig} ← {corrected}: {n_ok}/{n} non-NA")

# Drop working columns
cov = cov.drop(columns=[c for c in gn_cols if c in cov.columns])

# ── 7. Save ───────────────────────────────────────────────────────────────────
out_path = DATA / "covariate_matrix_634_v2.csv"
cov.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}  ({cov.shape[0]} × {cov.shape[1]} cols)")

# Check effective complete-case count
confounders_v2 = ['clay_pct','organic_matter','cec','log10_mine','lc_forest_pct',
                  'shannon','mat_c','map_mm','sand_0cm','bulk_density_0cm','elevation_m',
                  'slope_pct','awc_0_25cm','hydric_pct','ponding_pct','land_cap_class']
cov2 = pd.read_csv(out_path, keep_default_na=False, na_values=[''])
cc = cov2[confounders_v2].notna().all(axis=1).sum()
print(f"\nComplete-case with key confounders ({len(confounders_v2)} vars): {cc}/{n}")

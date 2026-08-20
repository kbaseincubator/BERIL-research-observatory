#!/usr/bin/env python3
"""
build_extended_covariates.py

Extends covariate_matrix_634.csv with:
  - Climate: MAT, MAP, temp_seasonality, precip_seasonality (WorldClim 0.25°)
  - Soil: nitrogen_0cm, sand_0cm, silt_0cm, bulk_density_0cm (SoilGrids master 0.25°)
  - Elevation: elevation_m (ETOPO1 0.1°)
  - Fixes: impute epa_tri_releases=0 for NA samples; drop tectonic_boundary_dist
  - Optionally adds: tectonic_boundary_dist_v2 if tectonic_dist.csv exists

Outputs: covariate_matrix_634_v2.csv

Usage: python3 build_extended_covariates.py
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree

DATA    = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
ENV_DB  = Path("/home/hmacgregor/data/envdbs")
SCRIPTS = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts")

# ── 0. Load base covariate matrix ────────────────────────────────────────────
print("Loading base covariate matrix...")
cov = pd.read_csv(DATA / "covariate_matrix_634.csv")
print(f"  Base: {cov.shape[0]} rows × {cov.shape[1]} cols")

samples = cov[['sample_id','lat','lon']].copy()

# ── 1. WorldClim: MAT, MAP, seasonality ──────────────────────────────────────
print("\n[1] WorldClim...")
wc = pd.read_parquet(ENV_DB / "global_worldclim_all.parquet")
# 0.25° grid join
samples['_lat4'] = (samples.lat * 4).round() / 4
samples['_lon4'] = (samples.lon * 4).round() / 4
wc_sub = wc[['lat','lon','annual_mean_temp_c','annual_precip_mm',
             'temp_seasonality','precip_seasonality','temp_annual_range_c']].copy()
merged = samples.merge(wc_sub, left_on=['_lat4','_lon4'], right_on=['lat','lon'], how='left')
cov['mat_c']            = merged['annual_mean_temp_c'].values
cov['map_mm']           = merged['annual_precip_mm'].values
cov['temp_seasonality'] = merged['temp_seasonality'].values
cov['precip_seasonality'] = merged['precip_seasonality'].values
cov['temp_annual_range_c'] = merged['temp_annual_range_c'].values

# Fill remaining NAs with nearest-neighbor
wc_na = cov['mat_c'].isna()
if wc_na.sum() > 0:
    tree = cKDTree(wc[['lat','lon']].values)
    _, idxs = tree.query(samples.loc[wc_na, ['lat','lon']].values, k=1)
    for col, wcol in [('mat_c','annual_mean_temp_c'), ('map_mm','annual_precip_mm'),
                      ('temp_seasonality','temp_seasonality'), ('precip_seasonality','precip_seasonality'),
                      ('temp_annual_range_c','temp_annual_range_c')]:
        cov.loc[wc_na, col] = wc.iloc[idxs][wcol].values

print(f"  MAT: {cov['mat_c'].notna().sum()}/634 non-NA, range {cov['mat_c'].min():.1f}–{cov['mat_c'].max():.1f} °C")
print(f"  MAP: {cov['map_mm'].notna().sum()}/634 non-NA, range {cov['map_mm'].min():.0f}–{cov['map_mm'].max():.0f} mm")

# ── 2. SoilGrids master: nitrogen, sand, silt, bulk_density ──────────────────
print("\n[2] SoilGrids master (0.25°)...")
sg = pd.read_parquet(ENV_DB / "SoilGrids/soilgrids_master.parquet")
sg_cols = ['lat','lon','nitrogen_0cm','sand_0cm','silt_0cm','bulk_density_0cm']
sg_sub = sg[sg_cols].copy()

# 0.25° grid join
merged_sg = samples.merge(sg_sub, left_on=['_lat4','_lon4'], right_on=['lat','lon'], how='left')
cov['nitrogen_0cm']     = merged_sg['nitrogen_0cm'].values
cov['sand_0cm']         = merged_sg['sand_0cm'].values
cov['silt_0cm']         = merged_sg['silt_0cm'].values
cov['bulk_density_0cm'] = merged_sg['bulk_density_0cm'].values

# Nearest-neighbor fill for any remaining NAs
sg_na = cov['nitrogen_0cm'].isna()
if sg_na.sum() > 0:
    sg_clean = sg_sub.dropna().reset_index(drop=True)
    tree_sg = cKDTree(sg_clean[['lat','lon']].values)
    _, idxs = tree_sg.query(samples.loc[sg_na, ['lat','lon']].values, k=1)
    for col in ['nitrogen_0cm','sand_0cm','silt_0cm','bulk_density_0cm']:
        cov.loc[sg_na, col] = sg_clean.iloc[idxs][col].values

for col in ['nitrogen_0cm','sand_0cm','silt_0cm','bulk_density_0cm']:
    print(f"  {col}: {cov[col].notna().sum()}/634, range {cov[col].min():.1f}–{cov[col].max():.1f}")

# ── 3. Elevation (ETOPO1 0.1°) ────────────────────────────────────────────────
print("\n[3] Elevation (ETOPO1)...")
elev = pd.read_parquet(ENV_DB / "etopo1_elevation_0.1deg.parquet")
elev_us = elev[(elev.lat >= 24) & (elev.lat <= 50) & (elev.lon >= -130) & (elev.lon <= -65)].copy()
tree_e = cKDTree(elev_us[['lat','lon']].values)
_, idxs_e = tree_e.query(samples[['lat','lon']].values, k=1)
cov['elevation_m'] = elev_us.iloc[idxs_e]['elevation'].values
print(f"  elevation_m: {cov['elevation_m'].notna().sum()}/634, range {cov['elevation_m'].min():.0f}–{cov['elevation_m'].max():.0f} m")

# ── 4. Replace epa_tri_releases with corrected radius-sum values ──────────────
# enriched_metadata left NULLs for samples with no nearby facility; the fix
# uses the same 0.5° radius-sum approach as organic releases (0 = no facility).
# Run add_metal_tri_covariate.py from JupyterHub to produce metal_tri_by_sample.csv.
print("\n[4] Patching epa_tri_releases from corrected radius-sum file...")
metal_tri_file = DATA / "metal_tri_by_sample.csv"
if metal_tri_file.exists():
    metal_tri = pd.read_csv(metal_tri_file)
    cov = cov.drop(columns=['epa_tri_releases'], errors='ignore')
    cov = cov.merge(metal_tri[['sample_id', 'epa_tri_releases']], on='sample_id', how='left')
    print(f"  epa_tri_releases: {cov['epa_tri_releases'].notna().sum()}/634 non-NA")
    print(f"  Zeros (no facility): {(cov['epa_tri_releases']==0).sum()}, non-zero: {(cov['epa_tri_releases']>0).sum()}")
else:
    print(f"  metal_tri_by_sample.csv not found — run add_metal_tri_covariate.py from JupyterHub.")
    print(f"  epa_tri_releases unchanged: {cov['epa_tri_releases'].notna().sum()}/634")

# ── 4c. gNATSGO: slope, AWC, hydrologic group, flood frequency ───────────────
print("\n[4c] gNATSGO (nearest-neighbour join)...")
gn = pd.read_parquet('/home/hmacgregor/data/envdbs/gNATSGO/gNATSGO_snake_case.parquet')
gn_usa = gn[(gn.latitude >= 24) & (gn.latitude <= 50) &
            (gn.longitude >= -130) & (gn.longitude <= -65)].copy()
gn_cols = ['latitude', 'longitude',
           'slope_gradient_weighted_average',
           'available_water_storage_0_25cm_wta',
           'hydrologic_group_dominant_condition',
           'flood_frequency_dominant_condition',
           'hydric_classification_presence',
           'ponding_frequency_presence',
           'non_irrigated_capability_class_dominant_condition']
gn_sub = gn_usa[gn_cols].dropna(subset=['latitude', 'longitude']).reset_index(drop=True)

tree_gn = cKDTree(gn_sub[['latitude', 'longitude']].values)
_, idxs_gn = tree_gn.query(samples[['lat', 'lon']].values, k=1)
matched_gn = gn_sub.iloc[idxs_gn].reset_index(drop=True)

cov['slope_pct']        = matched_gn['slope_gradient_weighted_average'].values
cov['awc_0_25cm']       = matched_gn['available_water_storage_0_25cm_wta'].values
cov['hydrologic_group'] = matched_gn['hydrologic_group_dominant_condition'].values
cov['flood_freq']       = matched_gn['flood_frequency_dominant_condition'].values
cov['hydric_pct']       = matched_gn['hydric_classification_presence'].values
cov['ponding_pct']      = matched_gn['ponding_frequency_presence'].values
cov['land_cap_class']   = matched_gn['non_irrigated_capability_class_dominant_condition'].values

for col in ['slope_pct', 'awc_0_25cm', 'hydrologic_group', 'flood_freq',
            'hydric_pct', 'ponding_pct', 'land_cap_class']:
    n = cov[col].notna().sum()
    print(f"  {col}: {n}/634 non-NA")

# ── 5. Drop tectonic_boundary_dist (17.5% coverage, causing n=55 effective) ──
print("\n[5] Dropping tectonic_boundary_dist (17.5% coverage)...")
if 'tectonic_boundary_dist' in cov.columns:
    cov = cov.drop(columns=['tectonic_boundary_dist'])
    print("  Dropped.")

# ── 6. Optional: add recomputed tectonic distance if available ────────────────
tectonic_file = DATA / "tectonic_dist_634.csv"
if tectonic_file.exists():
    print(f"\n[6] Loading recomputed tectonic distances from {tectonic_file}...")
    td = pd.read_csv(tectonic_file)
    cov = cov.merge(td[['sample_id','tectonic_dist_km']], on='sample_id', how='left')
    print(f"  tectonic_dist_km: {cov['tectonic_dist_km'].notna().sum()}/634 non-NA")
else:
    print(f"\n[6] Tectonic dist file not found ({tectonic_file}) — skipping.")

# ── 7. Report coverage summary ────────────────────────────────────────────────
print("\n=== Coverage summary ===")
drop_cols = {'sample_id','lat','lon'} | set(c for c in cov.columns if c.startswith('phylum_') or c.startswith('ph_'))
for col in cov.columns:
    if col in drop_cols:
        continue
    n = cov[col].notna().sum()
    print(f"  {col}: {n}/634 ({n/634*100:.1f}%)")

# ── 8. Complete-case count for new full model ─────────────────────────────────
print("\n=== Effective full model complete-case count ===")
# New confounder set
new_confounders = [
    'ph_soilgrids', 'drainage_class', 'organic_matter', 'clay_pct', 'cec',
    'lith_class', 'usgs_mine_distance', 'epa_tri_releases', 'epa_tri_organic_releases',
    'lc_forest_pct', 'lc_cultivated_pct', 'lc_urban_pct', 'lc_barren_pct',
    'shannon',
    'phylum_Acidobacteria', 'phylum_Actinobacteria', 'phylum_Ascomycota',
    'phylum_Bacteroidetes', 'phylum_Basidiomycota', 'phylum_Planctomycetes',
    'phylum_Proteobacteria', 'phylum_Thaumarchaeota',
    'mat_c', 'map_mm',
    'nitrogen_0cm', 'sand_0cm', 'bulk_density_0cm',
    'elevation_m',
]
new_confounders = [c for c in new_confounders if c in cov.columns]
complete_new = cov[new_confounders].notna().all(axis=1).sum()
print(f"  New model ({len(new_confounders)} confounders): {complete_new}/634 ({complete_new/634*100:.1f}%)")

# Show bottlenecks
for col in new_confounders:
    n = cov[col].notna().sum()
    if n < 500:
        print(f"  BOTTLENECK: {col} = {n}/634 ({n/634*100:.1f}%)")

# ── 9. Save ───────────────────────────────────────────────────────────────────
out_path = DATA / "covariate_matrix_634_v2.csv"
cov.drop(columns=[c for c in ['_lat4','_lon4'] if c in cov.columns], inplace=True)
cov.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Shape: {cov.shape}")

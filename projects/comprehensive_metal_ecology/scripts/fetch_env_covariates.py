#!/usr/bin/env python3
"""
Fetch environmental covariates for all genome locations.

Sources:
  - SoilGrids COG: pH, organic carbon, clay
  - Open-Meteo Historical API: mean annual temperature, total annual precipitation

Caches SoilGrids to CSV so they don't need re-reading.
Output: data/genome_env_covariates.csv
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import json
import time
import requests
import numpy as np
import pandas as pd
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / 'data' / 'genome_env_covariates.csv'
CACHE_DIR = PROJ / 'data' / 'env_cache'
CACHE_DIR.mkdir(exist_ok=True)
SG_CACHE_CSV = CACHE_DIR / 'soilgrids_locs.csv'
CLIMATE_CACHE = CACHE_DIR / 'openmeteo_cache.json'

print("Loading genome locations...", flush=True)
mags = pd.read_csv(PROJ / 'data' / 'genome_coords.csv')
unique_locs = mags[['latitude', 'longitude']].drop_duplicates().reset_index(drop=True)
print(f"  {len(mags):,} MAGs, {len(unique_locs):,} unique locations", flush=True)

# ── SoilGrids via COG ────────────────────────────────────────────────────
if SG_CACHE_CSV.exists():
    print(f"\nLoading cached SoilGrids from {SG_CACHE_CSV}...", flush=True)
    sg_df = pd.read_csv(SG_CACHE_CSV)
    for col in ['ph_h2o', 'organic_carbon_density', 'clay_pct']:
        n = sg_df[col].notna().sum()
        print(f"  {col}: {n}/{len(sg_df)} ({100*n/len(sg_df):.1f}%)", flush=True)
else:
    print("\nSampling SoilGrids COGs...", flush=True)
    import rasterio
    from pyproj import Transformer

    SOILGRIDS_COGS = {
        'ph_h2o': ('https://files.isric.org/soilgrids/latest/data/phh2o/phh2o_0-5cm_mean.vrt', 0.1),
        'organic_carbon_density': ('https://files.isric.org/soilgrids/latest/data/ocd/ocd_0-5cm_mean.vrt', 0.01),
        'clay_pct': ('https://files.isric.org/soilgrids/latest/data/clay/clay_0-5cm_mean.vrt', 0.1),
    }
    TILE_SIZE = 128

    sg_df = unique_locs.copy()
    lats = unique_locs.latitude.values
    lons = unique_locs.longitude.values

    for col_name, (url, scale) in SOILGRIDS_COGS.items():
        print(f"  {col_name}...", flush=True)
        values = np.full(len(lats), np.nan)
        try:
            with rasterio.open(url) as src:
                transformer = Transformer.from_crs('EPSG:4326', src.crs, always_xy=True)
                nodata = src.nodata
                projected = np.array([transformer.transform(lon, lat) for lat, lon in zip(lats, lons)])
                xs, ys = projected[:, 0], projected[:, 1]
                rows_arr = np.array([src.index(x, y)[0] for x, y in zip(xs, ys)])
                cols_arr = np.array([src.index(x, y)[1] for x, y in zip(xs, ys)])
                row_tiles = rows_arr // TILE_SIZE
                col_tiles = cols_arr // TILE_SIZE
                tile_keys = list(set(zip(row_tiles, col_tiles)))
                print(f"    {len(tile_keys)} tiles...", flush=True)

                for ti, (rt, ct) in enumerate(tile_keys):
                    r_start = rt * TILE_SIZE
                    c_start = ct * TILE_SIZE
                    window = rasterio.windows.Window(c_start, r_start, TILE_SIZE, TILE_SIZE)
                    try:
                        data = src.read(1, window=window)
                    except:
                        continue
                    mask = (row_tiles == rt) & (col_tiles == ct)
                    for idx in np.where(mask)[0]:
                        lr = rows_arr[idx] - r_start
                        lc = cols_arr[idx] - c_start
                        if 0 <= lr < data.shape[0] and 0 <= lc < data.shape[1]:
                            raw = data[lr, lc]
                            if raw != nodata and raw > 0:
                                values[idx] = raw * scale
                    if (ti + 1) % 100 == 0:
                        print(f"      tile {ti+1}/{len(tile_keys)}", flush=True)

            n_valid = np.isfinite(values).sum()
            print(f"    Coverage: {n_valid}/{len(lats)} ({100*n_valid/len(lats):.1f}%)", flush=True)
        except Exception as e:
            print(f"    ERROR: {e}", flush=True)
        sg_df[col_name] = values

    sg_df.to_csv(SG_CACHE_CSV, index=False)
    print(f"  Saved SoilGrids cache: {SG_CACHE_CSV}", flush=True)

# ── Open-Meteo climate ───────────────────────────────────────────────────
OPENMETEO_URL = "https://archive-api.open-meteo.com/v1/archive"

def load_json_cache(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

def save_json_cache(cache, path):
    with open(path, 'w') as f:
        json.dump(cache, f)

print("\nFetching Open-Meteo climate data...", flush=True)
clim_cache = load_json_cache(CLIMATE_CACHE)
print(f"  Cache: {len(clim_cache)} entries", flush=True)

session = requests.Session()
temp_vals = np.full(len(unique_locs), np.nan)
precip_vals = np.full(len(unique_locs), np.nan)
n_fetched = 0

for i, row in unique_locs.iterrows():
    key = f"{row.latitude:.4f},{row.longitude:.4f}"
    if key in clim_cache and clim_cache[key]:
        r = clim_cache[key]
    else:
        params = {
            "latitude": row.latitude, "longitude": row.longitude,
            "start_date": "2019-01-01", "end_date": "2020-12-31",
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "UTC",
        }
        r = {}
        for attempt in range(3):
            try:
                resp = session.get(OPENMETEO_URL, params=params, timeout=60)
                if resp.status_code == 429:
                    time.sleep(10 * (attempt + 1))
                    continue
                if resp.status_code != 200:
                    break
                data = resp.json()
                daily = data.get("daily", {})
                temps = [t for t in (daily.get("temperature_2m_mean") or []) if t is not None]
                precips = [p for p in (daily.get("precipitation_sum") or []) if p is not None]
                r = {
                    "mean_annual_temp_C": round(np.mean(temps), 2) if temps else None,
                    "mean_annual_precip_mm": round(np.sum(precips) / 2.0, 1) if precips else None,
                }
                break
            except:
                time.sleep(2)
        clim_cache[key] = r
        n_fetched += 1
        if n_fetched % 50 == 0:
            print(f"    Fetched {n_fetched}...", flush=True)
            save_json_cache(clim_cache, CLIMATE_CACHE)
        time.sleep(0.1)

    if r.get("mean_annual_temp_C") is not None:
        temp_vals[i] = r["mean_annual_temp_C"]
    if r.get("mean_annual_precip_mm") is not None:
        precip_vals[i] = r["mean_annual_precip_mm"]

save_json_cache(clim_cache, CLIMATE_CACHE)
print(f"  New fetches: {n_fetched}", flush=True)
print(f"  Temperature coverage: {np.isfinite(temp_vals).sum()}/{len(unique_locs)}", flush=True)
print(f"  Precipitation coverage: {np.isfinite(precip_vals).sum()}/{len(unique_locs)}", flush=True)

# ── Combine and save ─────────────────────────────────────────────────────
sg_df['mean_annual_temp_C'] = temp_vals
sg_df['mean_annual_precip_mm'] = precip_vals

result = mags.merge(sg_df, on=['latitude', 'longitude'], how='left')

print(f"\n{'='*60}", flush=True)
print(f"FINAL MAG-level coverage ({len(result):,} genomes):", flush=True)
for col in ['ph_h2o', 'organic_carbon_density', 'clay_pct', 'mean_annual_temp_C', 'mean_annual_precip_mm']:
    if col in result.columns:
        n = result[col].notna().sum()
        print(f"  {col:30s}: {n:,}/{len(result):,} ({100*n/len(result):.1f}%)", flush=True)

result.to_csv(OUT, index=False)
print(f"\nSaved: {OUT} ({len(result):,} rows)", flush=True)
print("DONE.", flush=True)

#!/usr/bin/env python3
"""
Extract extended environmental covariates for CWM sample IDs.

Variable sources (confirmed by NB06 confounder screen):
  enriched_metadata_gee (OLM + ERA5, via sample_id → SRS_Join_Key):
    - olm_soil_organic_matter_0cm_pct  → soil_som_pct
    - olm_soil_clay_0cm_pct            → clay_pct
    - olm_soil_sand_0cm_pct            → sand_pct
    - ERA5_total_precipitation_mm       → precip_mm
  sample_metadata (direct sample_id join):
    - altitude_m                        → altitude_m  (self-reported, sparse)
  arkinlab.envdbs.etopo1_elevation (0.1° global grid, 2.1M non-null rows):
    - elevation (string → DOUBLE)       → elevation_m (spatial join on rounded lat/lon)

REJECTED sources (from NB06 screen + microbeatlas NB30):
  - arkinlab.envdbs.srtm_elevation:  ALL elevation values NULL (confirmed useless)
  - arkinlab.envdbs.soilgrids:       only bdod + ocd; very sparse (152/5000 genera)
  - arkinlab.envdbs.chelsa_bioclim:  US Great Plains corridor ONLY, not global
  - arkinlab.envdbs.soiltemp:        soil temp range (redundant with temp_K in h3a CSV)

Output: data/cwm_sample_env_extended.csv
  Columns: sample_id, soil_som_pct, clay_pct, sand_pct, precip_mm, altitude_m, elevation_m

Run in JupyterHub (soil sample join only works there):
  OMP_NUM_THREADS=1 python3 scripts/extract_sample_env_extended.py
"""

import os
import sys
from pathlib import Path

DATA = Path("data")

# ─── Spark setup ─────────────────────────────────────────────────────────────
try:
    from scripts.berdl_utils import get_spark_session
    spark = get_spark_session()
except Exception:
    import importlib.util
    ROOT = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "berdl_utils",
        ROOT / "scripts" / "berdl_utils.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    spark = mod.get_spark_session()

print("Spark session active.")

# ─── Load CWM sample IDs ─────────────────────────────────────────────────────
import pandas as pd
cwm_ids = (
    pd.read_csv(DATA / "h3a_cwm_sample_data.csv", usecols=["sample_id"])
    .drop_duplicates()
)
print(f"CWM sample IDs to enrich: {len(cwm_ids):,}")

cwm_spark = spark.createDataFrame(cwm_ids)
cwm_spark.createOrReplaceTempView("cwm_sample_ids")

# ─── 1. OLM + ERA5 from enriched_metadata_gee ─────────────────────────────────
# Join path: cwm_sample_ids → sample_metadata → enriched_metadata_gee
# Note: enriched_metadata_gee only links to soil/agricultural samples via
# SRS_Join_Key; non-soil samples will return NULL for these variables.
# FIRST() de-duplicates the many-to-one SRS → sample_id mapping.
print("\nQuerying enriched_metadata_gee (OLM + ERA5)...")
gee_sdf = spark.sql("""
    SELECT
        sm.sample_id,
        FIRST(g.olm_soil_organic_matter_0cm_pct)  AS soil_som_pct,
        FIRST(g.olm_soil_clay_0cm_pct)            AS clay_pct,
        FIRST(g.olm_soil_sand_0cm_pct)            AS sand_pct,
        FIRST(g.ERA5_total_precipitation_mm)       AS precip_mm
    FROM cwm_sample_ids ci
    JOIN arkinlab.microbeatlas.sample_metadata sm
         ON ci.sample_id = sm.sample_id
    JOIN arkinlab.microbeatlas.enriched_metadata_gee g
         ON sm.SRS_Join_Key = g.SRS_Join_Key
    GROUP BY sm.sample_id
""")
gee_df = gee_sdf.toPandas()
print(f"  Rows: {len(gee_df):,}")
for col in ["soil_som_pct", "clay_pct", "sand_pct", "precip_mm"]:
    n = gee_df[col].notna().sum()
    print(f"  {col}: {n:,} ({100*n/len(gee_df):.0f}%)")

# ─── 2. altitude_m from sample_metadata (self-reported, sparse) ───────────────
print("\nQuerying sample_metadata for altitude...")
alt_sdf = spark.sql("""
    SELECT
        ci.sample_id,
        FIRST(TRY_CAST(sm.altitude_m AS DOUBLE)) AS altitude_m
    FROM cwm_sample_ids ci
    JOIN arkinlab.microbeatlas.sample_metadata sm
         ON ci.sample_id = sm.sample_id
    WHERE sm.altitude_m IS NOT NULL
      AND TRY_CAST(sm.altitude_m AS DOUBLE) IS NOT NULL
    GROUP BY ci.sample_id
""")
alt_df = alt_sdf.toPandas()
print(f"  Samples with altitude_m: {len(alt_df):,}")

# ─── 3. ETOPO1 elevation (0.1° global grid, 2.1M non-null rows) ───────────────
# Schema: lat (string), lon (string), elevation (string) — all need casting
# NB07 pattern: round coords to 0.1°, join via temp view with numeric types
print("\nQuerying arkinlab.envdbs.etopo1_elevation (0.1° grid)...")
cwm_coords = (
    pd.read_csv(DATA / "h3a_cwm_sample_data.csv", usecols=["sample_id", "lat", "lon"])
    .drop_duplicates("sample_id")
    .dropna(subset=["lat", "lon"])
)
cwm_coords["lat_rnd"] = (cwm_coords["lat"] * 10).round() / 10
cwm_coords["lon_rnd"] = (cwm_coords["lon"] * 10).round() / 10
coords_sdf = spark.createDataFrame(cwm_coords[["sample_id", "lat_rnd", "lon_rnd"]])
coords_sdf.createOrReplaceTempView("cwm_coords")
print(f"  Samples with lat/lon for spatial join: {len(cwm_coords):,}")

spark.sql("""
    CREATE OR REPLACE TEMP VIEW etopo AS
    SELECT ROUND(CAST(lat AS DOUBLE), 1) AS e_lat,
           ROUND(CAST(lon AS DOUBLE), 1) AS e_lon,
           CAST(elevation AS DOUBLE)     AS elevation_m
    FROM arkinlab.envdbs.etopo1_elevation
""")

etopo_sdf = spark.sql("""
    SELECT c.sample_id, e.elevation_m
    FROM cwm_coords c
    JOIN etopo e
      ON c.lat_rnd = e.e_lat AND c.lon_rnd = e.e_lon
""")
etopo_df = etopo_sdf.toPandas()
print(f"  Samples with elevation_m: {len(etopo_df):,}")

# ─── Merge and save ───────────────────────────────────────────────────────────
env_ext = (
    gee_df
    .merge(alt_df, on="sample_id", how="outer")
    .merge(etopo_df, on="sample_id", how="outer")
)
print(f"\nMerged: {len(env_ext):,} samples")
for col in ["soil_som_pct", "clay_pct", "sand_pct", "precip_mm", "altitude_m", "elevation_m"]:
    if col in env_ext.columns:
        n = env_ext[col].notna().sum()
        print(f"  {col}: {n:,} ({100*n/len(env_ext):.0f}%)")

out = DATA / "cwm_sample_env_extended.csv"
env_ext.to_csv(out, index=False)
print(f"\nSaved → {out}")
spark.stop()
print("Done.")

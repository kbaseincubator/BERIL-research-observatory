#!/usr/bin/env python3
"""
Fill GLiM lithology and SoilGrids pH from Spark tables.

GLiM:  arkinlab.envdbs.global_lithology_glim  (0.25° grid)
pH:    arkinlab.envdbs.soilgrids_master        (pH_0cm column)

For each of the 634 thinned cell centroids, round lat/lon to nearest 0.25°
and join to the Spark table.  Overwrites:
  data/usa_cwm/glim_thinned_cells.csv
  data/usa_cwm/soilgrids_ph_thinned_cells.csv  (updates only missing cells)
"""
import os, sys
os.environ["OMP_NUM_THREADS"] = "1"

import pandas as pd
import numpy as np

DATA = "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"

# ── Load thinned cell centroids ───────────────────────────────────────────────
cells = pd.read_csv(f"{DATA}/thinned_sample_ids.csv")
print(f"Thinned cells: {len(cells)}")

# Round to nearest 0.25° (GLiM/SoilGrids resolution)
cells["lat_grid"] = (cells["lat"] / 0.25).round() * 0.25
cells["lon_grid"] = (cells["lon"] / 0.25).round() * 0.25
print(f"Unique 0.25° grid cells: {cells[['lat_grid','lon_grid']].drop_duplicates().shape[0]}")

# ── Spark ─────────────────────────────────────────────────────────────────────
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("no active session")
except Exception:
    sys.path.append("/opt/conda/lib/python3.13/site-packages")
    import berdl_notebook_utils
    spark = berdl_notebook_utils.get_spark_session()

print("Spark session ready")

# ── 1. GLiM ──────────────────────────────────────────────────────────────────
print("\n=== GLiM lithology ===")
glim_raw = spark.sql("""
    SELECT CAST(lat AS DOUBLE) AS lat_grid,
           CAST(lon AS DOUBLE) AS lon_grid,
           lithology_class
    FROM arkinlab.envdbs.global_lithology_glim
    WHERE CAST(lat AS DOUBLE) BETWEEN 24 AND 50
      AND CAST(lon AS DOUBLE) BETWEEN -125 AND -65
      AND lithology_class IS NOT NULL
""").toPandas()
glim_raw.attrs = {}
print(f"GLiM USA rows: {len(glim_raw)}, unique classes: {glim_raw['lithology_class'].nunique()}")
print(glim_raw["lithology_class"].value_counts().head())

# Join to thinned cells on rounded grid
glim_cells = cells[["sample_id", "lat", "lon", "lat_grid", "lon_grid"]].merge(
    glim_raw, on=["lat_grid", "lon_grid"], how="left"
)
n_matched = glim_cells["lithology_class"].notna().sum()
print(f"Matched {n_matched}/{len(cells)} cells ({100*n_matched/len(cells):.1f}%)")
if n_matched < len(cells):
    missing = glim_cells[glim_cells["lithology_class"].isna()]
    print("  Unmatched grid cells (first 5):")
    print(missing[["lat_grid","lon_grid"]].drop_duplicates().head())

# Rename and save
out_glim = glim_cells[["lat", "lon", "lithology_class"]].rename(
    columns={"lithology_class": "lith_class"}
)
out_glim.to_csv(f"{DATA}/glim_thinned_cells.csv", index=False)
print(f"Saved: {DATA}/glim_thinned_cells.csv")
print(out_glim["lith_class"].value_counts())

# ── 2. SoilGrids pH (fill missing) ──────────────────────────────────────────
print("\n=== SoilGrids pH ===")
# Check existing cache
ph_existing = pd.read_csv(f"{DATA}/soilgrids_ph_thinned_cells.csv")
print(f"Existing cache: {len(ph_existing)} rows, {ph_existing['ph_soilgrids'].notna().sum()} non-null")

# Which cells are missing?
missing_mask = ph_existing["ph_soilgrids"].isna()
n_missing = missing_mask.sum()
print(f"Missing pH: {n_missing}")

if n_missing > 0:
    # Check all available pH-like columns in soilgrids_master
    cols_df = spark.sql("DESCRIBE arkinlab.envdbs.soilgrids_master").toPandas()
    ph_cols = [c for c in cols_df["col_name"].tolist() if "ph" in c.lower() or "pH" in c]
    print(f"pH columns in soilgrids_master: {ph_cols}")

    # Query soilgrids_master using pH_0cm (confirmed non-null)
    sg_raw = spark.sql("""
        SELECT CAST(lat AS DOUBLE) AS lat_grid,
               CAST(lon AS DOUBLE) AS lon_grid,
               `pH_0cm`
        FROM arkinlab.envdbs.soilgrids_master
        WHERE CAST(lat AS DOUBLE) BETWEEN 24 AND 50
          AND CAST(lon AS DOUBLE) BETWEEN -125 AND -65
          AND `pH_0cm` IS NOT NULL
    """).toPandas()
    sg_raw.attrs = {}
    print(f"SoilGrids_master USA non-null pH_0cm rows: {len(sg_raw)}")

    if len(sg_raw) > 0:
        # ph_existing uses columns: cell_lat, cell_lon, lat, lon, ph_soilgrids
        # Round existing lat/lon to 0.25° to join with soilgrids_master grid
        ph_existing["lat_grid"] = (ph_existing["lat"] / 0.25).round() * 0.25
        ph_existing["lon_grid"] = (ph_existing["lon"] / 0.25).round() * 0.25

        # Only update missing rows
        missing_rows = ph_existing[ph_existing["ph_soilgrids"].isna()].copy()
        filled = missing_rows.merge(
            sg_raw.rename(columns={"pH_0cm": "ph_spark"}),
            on=["lat_grid","lon_grid"], how="left"
        )
        n_filled = filled["ph_spark"].notna().sum()
        print(f"Filled {n_filled}/{n_missing} missing cells from Spark")

        # Apply fills back using index
        for row_idx, ph_val in zip(missing_rows.index, filled["ph_spark"]):
            if not pd.isna(ph_val):
                ph_existing.loc[row_idx, "ph_soilgrids"] = float(ph_val)

        ph_existing.drop(columns=["lat_grid","lon_grid"], inplace=True)
        ph_existing.to_csv(f"{DATA}/soilgrids_ph_thinned_cells.csv", index=False)
        final_notnull = ph_existing["ph_soilgrids"].notna().sum()
        print(f"Updated cache: {final_notnull}/{len(ph_existing)} non-null "
              f"({100*final_notnull/len(ph_existing):.1f}%)")
    else:
        print("WARNING: soilgrids_master has 0 non-null pH_0cm rows for USA — check table")
else:
    print("No missing pH cells — cache is complete.")

print("\nDone.")

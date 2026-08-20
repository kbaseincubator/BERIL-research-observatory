#!/usr/bin/env python3
"""
add_metal_tri_covariate.py

Produces metal_tri_by_sample.csv — corrected epa_tri_releases for all 634
thinned samples.

Problem: enriched_metadata.epa_tri_releases left NULLs for samples with no
TRI facility within the join radius, instead of assigning 0.  This gives 67%
coverage (425/634) and a spurious complete-case attrition of 209 samples.

Fix: same 0.5° radius-sum approach used for organic releases.  Samples with
no facility within the radius get 0 (true zero, not missing).

Source: arkinlab.envdbs.epa_tri_metals WHERE chemical = 'YES'
  chemical = 'YES' → metal release
  chemical = 'NO'  → organic/other release (handled by add_organic_tri_covariate.py)

Run from JupyterHub (Spark catalog access required).

Output: data/usa_cwm/metal_tri_by_sample.csv (sample_id, epa_tri_releases)
Then re-run build_extended_covariates.py to incorporate into covariate_matrix_634_v2.csv.
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
COV_PATH = DATA / "covariate_matrix_634.csv"

# ── 1. Load sample coordinates ────────────────────────────────────────────────
print(f"Loading sample coordinates from {COV_PATH}")
cov = pd.read_csv(COV_PATH)
print(f"  {len(cov)} samples")
print(f"  Current epa_tri_releases: {cov['epa_tri_releases'].notna().sum()}/634 non-NA")

# ── 2. Spark: query metal TRI releases ───────────────────────────────────────
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("no active session")
except Exception:
    sys.path.append("/opt/conda/lib/python3.13/site-packages")
    import berdl_notebook_utils
    spark = berdl_notebook_utils.get_spark_session()

print("Spark ready. Querying metal TRI releases (chemical = 'YES')...")

metal_df = spark.sql("""
    SELECT
        CAST(lat AS DOUBLE) AS fac_lat,
        CAST(lon AS DOUBLE) AS fac_lon,
        SUM(CAST(total_releases_lbs AS DOUBLE)) AS metal_lbs
    FROM arkinlab.envdbs.epa_tri_metals
    WHERE chemical = 'YES'
      AND lat IS NOT NULL
      AND lon IS NOT NULL
      AND CAST(lat AS DOUBLE) BETWEEN 24 AND 55
      AND CAST(lon AS DOUBLE) BETWEEN -130 AND -60
    GROUP BY CAST(lat AS DOUBLE), CAST(lon AS DOUBLE)
""").toPandas()
metal_df.attrs = {}

print(f"  Metal TRI facilities (USA): {len(metal_df)}")
print(f"  Total metal lbs: {metal_df['metal_lbs'].sum():.2e}")
print(f"  Non-zero facilities: {(metal_df['metal_lbs'] > 0).sum()}")

# ── 3. Radius-sum join: 0.5 deg (~50 km), 0 default ─────────────────────────
from scipy.spatial import cKDTree

RADIUS_DEG = 0.5

fac_coords   = metal_df[["fac_lat", "fac_lon"]].values
fac_releases = metal_df["metal_lbs"].values
tree = cKDTree(fac_coords)

sample_coords = cov[["lat", "lon"]].values

print(f"Radius-sum join (radius={RADIUS_DEG} deg)...")
metal_sum = np.zeros(len(cov))
for i, coord in enumerate(sample_coords):
    idx = tree.query_ball_point(coord, RADIUS_DEG)
    if idx:
        metal_sum[i] = fac_releases[idx].sum()

n_nonzero = (metal_sum > 0).sum()
print(f"  Samples with metal releases > 0: {n_nonzero}/{len(cov)}")
print(f"  Samples with zero (no facility): {(metal_sum == 0).sum()}/{len(cov)}")
print(f"  Median lbs (non-zero): {np.median(metal_sum[metal_sum > 0]):.2e}")
print(f"  Max: {metal_sum.max():.2e}")

# ── 4. Save ──────────────────────────────────────────────────────────────────
out = pd.DataFrame({
    "sample_id":       cov["sample_id"].values,
    "epa_tri_releases": metal_sum,
})
out_path = DATA / "metal_tri_by_sample.csv"
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Coverage: {out['epa_tri_releases'].notna().sum()}/634 (should be 634)")
print()
print("Next: re-run build_extended_covariates.py to update covariate_matrix_634_v2.csv")

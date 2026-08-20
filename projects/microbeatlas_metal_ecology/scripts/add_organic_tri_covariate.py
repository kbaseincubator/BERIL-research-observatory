#!/usr/bin/env python3
"""
add_organic_tri_covariate.py

Adds epa_tri_organic_releases to covariate_matrix_634.csv.

Source: arkinlab.envdbs.epa_tri_metals WHERE chemical = 'NO'
  chemical = 'NO'  means the release is NON-METAL (organic/other)
  chemical = 'YES' means metal release

Aggregation: sum of all organic TRI releases (lbs) within 0.5 degrees of each
sample location, across all available years (2018-2023).

Output: covariate_matrix_634.csv updated in-place with epa_tri_organic_releases column.
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
COV_PATH = DATA / "covariate_matrix_634.csv"

# ── 1. Load covariate matrix ──────────────────────────────────────────────────
print(f"Loading covariate matrix: {COV_PATH}")
cov = pd.read_csv(COV_PATH)
print(f"  Rows: {len(cov)}, Columns: {list(cov.columns)}")

# ── 2. Spark: query organic TRI releases ─────────────────────────────────────
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("no active session")
except Exception:
    sys.path.append("/opt/conda/lib/python3.13/site-packages")
    import berdl_notebook_utils
    spark = berdl_notebook_utils.get_spark_session()

print("Spark ready. Querying organic TRI releases...")

organic_df = spark.sql("""
    SELECT
        CAST(lat AS DOUBLE) AS fac_lat,
        CAST(lon AS DOUBLE) AS fac_lon,
        SUM(CAST(total_releases_lbs AS DOUBLE)) AS organic_lbs
    FROM arkinlab.envdbs.epa_tri_metals
    WHERE chemical = 'NO'
      AND lat IS NOT NULL
      AND lon IS NOT NULL
      AND CAST(lat AS DOUBLE) BETWEEN 24 AND 55
      AND CAST(lon AS DOUBLE) BETWEEN -130 AND -60
    GROUP BY CAST(lat AS DOUBLE), CAST(lon AS DOUBLE)
""").toPandas()
organic_df.attrs = {}

print(f"  Organic TRI facilities (USA): {len(organic_df)}")
print(f"  Total organic lbs: {organic_df['organic_lbs'].sum():.2e}")
print(f"  Non-zero facilities: {(organic_df['organic_lbs'] > 0).sum()}")

# ── 3. Radius-sum join: sum organic releases within 0.5 deg of each sample ───
# 0.5 degrees ~ 50 km at mid-latitudes; matches spatial thinning resolution
RADIUS_DEG = 0.5

from scipy.spatial import cKDTree

fac_coords = organic_df[["fac_lat", "fac_lon"]].values
fac_releases = organic_df["organic_lbs"].values
tree = cKDTree(fac_coords)

sample_coords = cov[["lat", "lon"]].values

# Query all facilities within RADIUS_DEG for each sample
print(f"Radius-sum join (radius={RADIUS_DEG} deg)...")
organic_sum = np.zeros(len(cov))
for i, coord in enumerate(sample_coords):
    idx = tree.query_ball_point(coord, RADIUS_DEG)
    if idx:
        organic_sum[i] = fac_releases[idx].sum()

cov["epa_tri_organic_releases"] = organic_sum

n_nonzero = (organic_sum > 0).sum()
print(f"  Samples with organic releases > 0: {n_nonzero}/{len(cov)}")
print(f"  Median organic lbs (non-zero): {np.median(organic_sum[organic_sum > 0]):.2e}")
print(f"  Max: {organic_sum.max():.2e}")

# ── 4. Save updated covariate matrix ─────────────────────────────────────────
cov.to_csv(COV_PATH, index=False)
print(f"\nSaved: {COV_PATH}")
print(f"New columns: {[c for c in cov.columns if 'organic' in c]}")
print("Done.")

#!/usr/bin/env python3
"""
Continuation of env niche breadth: CSU and NGSA spatial joins + per-genus SD.
Uses Pandas entirely (Spark workers can't read local filesystem).
Prerequisite: env_niche_global_spark.csv already computed.
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
from pyspark.sql import functions as F

OUTPUT = "projects/comprehensive_metal_ecology/data"
CSU_GRID_PATH = "/home/hmacgregor/data/envdbs/global_mobility_grid.parquet"
MIN_N = 10

csu_metal_cols = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']
ngsa_icp_cols = ['Cu_ICP_MS_mg_kg_0_2', 'Ni_ICP_MS_mg_kg_0_5', 'Zn_ICP_MS_mg_kg_0_9',
                  'Pb_ICP_MS_mg_kg_0_1', 'As_ICP_MS_mg_kg_0_4', 'Co_ICP_MS_mg_kg_0_1',
                  'Cr_ICP_MS_mg_kg_0_5', 'Hg_AR_mg_kg_0_01']
ngsa_mmi_cols = ['Cu_MMI_ME_mg_kg_0_01', 'Ni_MMI_ME_mg_kg_0_005', 'Zn_MMI_ME_mg_kg_0_02',
                  'Pb_MMI_ME_mg_kg_0_01', 'As_MMI_ME_mg_kg_0_01', 'Co_MMI_ME_mg_kg_0_005',
                  'Cr_MMI_ME_mg_kg_0_001', 'Hg_MMI_ME_mg_kg_0_001']
ngsa_all_cols = ngsa_icp_cols + ngsa_mmi_cols

# ─────────────────────────────────────────────────────────────────
# STEP 1: Build sample-genus mapping from Spark (collect to Pandas)
# ─────────────────────────────────────────────────────────────────
print("Step 1: Building sample-genus table...")
_tax_parts = F.split(F.col("Tax"), ";")
otu_meta = spark.table("arkinlab_microbeatlas.otu_metadata") \
    .select(
        "otu_id",
        F.when(F.size(_tax_parts) >= 6, _tax_parts.getItem(5)).alias("genus")
    ) \
    .filter(F.col("genus").isNotNull() & (F.length(F.trim(F.col("genus"))) > 0))

otu_counts = spark.table("arkinlab_microbeatlas.otu_counts_long") \
    .select(F.col("sample_id").alias("accession_id"), "otu_id", "count") \
    .filter(F.col("count") > 0)

sample_genus_spark = otu_counts.join(otu_meta, on="otu_id", how="inner") \
    .select("accession_id", F.lower(F.trim(F.col("genus"))).alias("genus_lower")) \
    .distinct()

print("  Collecting sample→genera mapping (collect_set, compact format)...")
sample_to_genera = sample_genus_spark.groupBy("accession_id") \
    .agg(F.collect_set("genus_lower").alias("genera"))
stg_pd = sample_to_genera.toPandas()
print(f"  sample→genera: {len(stg_pd)} samples, now exploding...")
sg_pd = stg_pd.explode("genera").rename(columns={"genera": "genus_lower"})
sg_pd = sg_pd.dropna(subset=["genus_lower"])
print(f"  sample_genus: {len(sg_pd)} rows, {sg_pd['genus_lower'].nunique()} unique genera")

# ─────────────────────────────────────────────────────────────────
# STEP 2: Per-sample lat/lon
# ─────────────────────────────────────────────────────────────────
print("Step 2: Collecting sample coordinates...")
georoc_spark = spark.table("arkinlab_microbeatlas.enriched_metadata") \
    .select("accession_id", "lat", "lon") \
    .filter(F.col("lat").isNotNull() & F.col("lon").isNotNull())
sample_coords_pd = georoc_spark.toPandas()
print(f"  {len(sample_coords_pd)} samples with coordinates")

# ─────────────────────────────────────────────────────────────────
# STEP 3: CSU metal mobility grid spatial join (global)
# ─────────────────────────────────────────────────────────────────
import os as _os
if _os.path.exists(f"{OUTPUT}/env_niche_csu_spark.csv"):
    print("Step 3: CSU CSV already exists, skipping.")
else:
    print("Step 3: CSU mobility grid spatial join...")
csu_grid = pd.read_parquet(CSU_GRID_PATH)

csu_coords = csu_grid[['latitude', 'longitude']].values.astype(np.float32)
print(f"  Building KDTree on {len(csu_grid)} cells...")
csu_tree = cKDTree(csu_coords)

samp_xy = sample_coords_pd[['lat', 'lon']].values.astype(np.float32)
dists_csu, idxs_csu = csu_tree.query(samp_xy, k=1, workers=4)

MAX_CSU_DEG = 0.09
csu_assigned = sample_coords_pd[['accession_id']].copy()
valid_csu = dists_csu <= MAX_CSU_DEG
for col in csu_metal_cols:
    vals = csu_grid[col].values[idxs_csu].astype(float)
    vals[~valid_csu] = np.nan
    csu_assigned[col] = vals
print(f"  CSU matched: {valid_csu.sum()} samples")

# Merge sample_genus × CSU, aggregate per genus
print("  Aggregating CSU niche breadth per genus...")
sg_csu = sg_pd.merge(csu_assigned, on='accession_id', how='inner')
csu_sd = sg_csu.groupby('genus_lower')[csu_metal_cols].std()
csu_n = sg_csu.groupby('genus_lower')[csu_metal_cols].count()

csu_df = csu_sd.rename(columns={c: c + '_sd' for c in csu_metal_cols})
for col in csu_metal_cols:
    csu_df[col + '_n'] = csu_n[col]
csu_df = csu_df.reset_index()
csu_df.to_csv(f"{OUTPUT}/env_niche_csu_spark.csv", index=False)
print(f"  Saved env_niche_csu_spark.csv ({len(csu_df)} genera)")

# ─────────────────────────────────────────────────────────────────
# STEP 4: NGSA spatial join (Australia only)
# ─────────────────────────────────────────────────────────────────
print("Step 4: NGSA spatial join (Australia only)...")
ngsa_pd = spark.table("arkinlab_envdbs.ngsa_geochemistry") \
    .select(
        F.col("lat").cast("double").alias("ngsa_lat"),
        F.col("lon").cast("double").alias("ngsa_lon"),
        *ngsa_all_cols
    ) \
    .filter(F.col("ngsa_lat").isNotNull()) \
    .toPandas()
print(f"  NGSA: {len(ngsa_pd)} stations")

aus_mask = (
    (sample_coords_pd['lat'] >= -45) & (sample_coords_pd['lat'] <= -10) &
    (sample_coords_pd['lon'] >= 110) & (sample_coords_pd['lon'] <= 155)
)
aus_samples = sample_coords_pd[aus_mask].copy()
print(f"  Australian samples: {len(aus_samples)}")

ngsa_tree = cKDTree(ngsa_pd[['ngsa_lat', 'ngsa_lon']].values)
dists_aus, idxs_aus = ngsa_tree.query(aus_samples[['lat', 'lon']].values, k=1)

MAX_NGSA_DEG = 200.0 / 111.0
aus_ngsa = aus_samples[['accession_id']].copy()
valid_aus = dists_aus <= MAX_NGSA_DEG
for col in ngsa_all_cols:
    numeric_col = pd.to_numeric(ngsa_pd[col], errors='coerce')
    vals = numeric_col.values[idxs_aus].copy().astype(float)
    vals[~valid_aus] = np.nan
    aus_ngsa[col] = vals
print(f"  NGSA matched: {valid_aus.sum()} Australian samples")

# Merge sample_genus × NGSA, aggregate per genus
print("  Aggregating NGSA niche breadth per genus...")
sg_ngsa = sg_pd.merge(aus_ngsa, on='accession_id', how='inner')
ngsa_sd = sg_ngsa.groupby('genus_lower')[ngsa_all_cols].std()
ngsa_n = sg_ngsa.groupby('genus_lower')[ngsa_icp_cols].count()

ngsa_df = ngsa_sd.rename(columns={c: c + '_sd' for c in ngsa_all_cols})
for col in ngsa_icp_cols:
    ngsa_df[col + '_n'] = ngsa_n[col]
ngsa_df = ngsa_df.reset_index()
ngsa_df.to_csv(f"{OUTPUT}/env_niche_ngsa_spark.csv", index=False)
print(f"  Saved env_niche_ngsa_spark.csv ({len(ngsa_df)} genera)")

print("\n=== CSU + NGSA niche breadth complete ===")
spark.stop()

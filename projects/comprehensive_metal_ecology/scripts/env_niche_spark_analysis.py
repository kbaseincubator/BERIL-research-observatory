#!/usr/bin/env python3
"""
Per-genus environmental niche breadth from MicrobeAtlas per-sample data.
Computes SD of pH, temperature, GeoROC bedrock metals (global),
CSU mobile metals (global), and NGSA ICP-MS + MMI_ME metals (Australia).
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
from pyspark.sql import functions as F

OUTPUT = "projects/comprehensive_metal_ecology/data"
MIN_N = 10
CSU_GRID_PATH = "/home/hmacgregor/data/envdbs/global_mobility_grid.parquet"

# ─────────────────────────────────────────────────────────────────
# STEP 1: Sample-genus presence table
# otu_counts_long has sample_id (int); need to map to accession_id via enriched_metadata
# ─────────────────────────────────────────────────────────────────
print("Step 1: Building sample-genus table...")
# otu_counts_long.sample_id IS the full accession_id string (e.g. SRR4241976.SRS1690913)
# Tax column format: Kingdom;Phylum;Class;Order;Family;Genus (6 semicolons → genus at index 5)
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

sample_genus = otu_counts.join(otu_meta, on="otu_id", how="inner") \
    .select("accession_id", F.lower(F.trim(F.col("genus"))).alias("genus_lower")) \
    .distinct()

print("  sample_genus built (lazy)")

# ─────────────────────────────────────────────────────────────────
# STEP 2: Per-sample environmental features from Spark tables
# ─────────────────────────────────────────────────────────────────
print("Step 2: Loading per-sample environmental features...")

gee = spark.table("arkinlab_microbeatlas.enriched_metadata_gee") \
    .select(
        F.col("SRS_Join_Key").alias("srs_key"),
        (F.col("olm_soil_ph_0cm_H2O") / 10.0).alias("soil_pH"),
        F.col("ERA5_mean_2m_air_temperature_K").alias("temp_K"),
    )

georoc = spark.table("arkinlab_microbeatlas.enriched_metadata") \
    .select(
        "accession_id",
        F.split(F.col("accession_id"), "[.]").getItem(1).alias("srs_key"),
        "lat", "lon",
        F.col("GeoROC_Rocks_georoc_Cu_ppm").alias("georoc_Cu"),
        F.col("GeoROC_Rocks_georoc_Ni_ppm").alias("georoc_Ni"),
        F.col("GeoROC_Rocks_georoc_Zn_ppm").alias("georoc_Zn"),
        F.col("GeoROC_Rocks_georoc_Co_ppm").alias("georoc_Co"),
        F.col("GeoROC_Rocks_georoc_Cr_ppm").alias("georoc_Cr"),
        F.col("GeoROC_Rocks_georoc_Pb_ppm").alias("georoc_Pb"),
        F.col("GeoROC_Rocks_georoc_As_ppm").alias("georoc_As"),
        F.col("GeoROC_Rocks_georoc_Cd_ppm").alias("georoc_Cd"),
        F.col("GeoROC_Rocks_georoc_Hg_ppm").alias("georoc_Hg"),
    )

# ─────────────────────────────────────────────────────────────────
# STEP 3: Global niche breadth (pH, temp, GeoROC) via Spark
# ─────────────────────────────────────────────────────────────────
print("Step 3: Computing global per-genus niche breadth (SD)...")

# Join sample_genus → georoc (on accession_id), then → gee (on srs_key)
sg_env = sample_genus \
    .join(georoc, on="accession_id", how="left") \
    .join(gee, on="srs_key", how="left")

global_niche = sg_env.groupBy("genus_lower").agg(
    F.stddev("soil_pH").alias("pH_sd"),
    F.count(F.when(F.col("soil_pH").isNotNull(), 1)).alias("pH_n"),
    F.stddev("temp_K").alias("temp_sd"),
    F.count(F.when(F.col("temp_K").isNotNull(), 1)).alias("temp_n"),
    F.stddev("georoc_Cu").alias("georoc_Cu_sd"),
    F.count(F.when(F.col("georoc_Cu").isNotNull(), 1)).alias("georoc_Cu_n"),
    F.stddev("georoc_Ni").alias("georoc_Ni_sd"),
    F.count(F.when(F.col("georoc_Ni").isNotNull(), 1)).alias("georoc_Ni_n"),
    F.stddev("georoc_Zn").alias("georoc_Zn_sd"),
    F.count(F.when(F.col("georoc_Zn").isNotNull(), 1)).alias("georoc_Zn_n"),
    F.stddev("georoc_Co").alias("georoc_Co_sd"),
    F.count(F.when(F.col("georoc_Co").isNotNull(), 1)).alias("georoc_Co_n"),
    F.stddev("georoc_Cr").alias("georoc_Cr_sd"),
    F.count(F.when(F.col("georoc_Cr").isNotNull(), 1)).alias("georoc_Cr_n"),
    F.stddev("georoc_Pb").alias("georoc_Pb_sd"),
    F.count(F.when(F.col("georoc_Pb").isNotNull(), 1)).alias("georoc_Pb_n"),
    F.stddev("georoc_As").alias("georoc_As_sd"),
    F.count(F.when(F.col("georoc_As").isNotNull(), 1)).alias("georoc_As_n"),
    F.stddev("georoc_Cd").alias("georoc_Cd_sd"),
    F.count(F.when(F.col("georoc_Cd").isNotNull(), 1)).alias("georoc_Cd_n"),
    F.stddev("georoc_Hg").alias("georoc_Hg_sd"),
    F.count(F.when(F.col("georoc_Hg").isNotNull(), 1)).alias("georoc_Hg_n"),
    F.count("accession_id").alias("total_n"),
)

global_df = global_niche.toPandas()
global_df.to_csv(f"{OUTPUT}/env_niche_global_spark.csv", index=False)
print(f"  Saved env_niche_global_spark.csv ({len(global_df)} genera)")

# ─────────────────────────────────────────────────────────────────
# STEP 4: Per-sample lat/lon (needed for spatial joins)
# ─────────────────────────────────────────────────────────────────
print("Step 4: Collecting sample coordinates...")
sample_coords_pd = georoc.select("accession_id", "lat", "lon") \
    .filter(F.col("lat").isNotNull() & F.col("lon").isNotNull()) \
    .toPandas()
print(f"  {len(sample_coords_pd)} samples with coordinates")

# ─────────────────────────────────────────────────────────────────
# STEP 5: CSU metal mobility grid spatial join (global)
# ─────────────────────────────────────────────────────────────────
print("Step 5: CSU mobility grid spatial join (global)...")
csu_grid = pd.read_parquet(CSU_GRID_PATH)
csu_metal_cols = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']

csu_coords = csu_grid[['latitude', 'longitude']].values.astype(np.float32)
print(f"  Building CSU KDTree on {len(csu_grid)} grid cells...")
csu_tree = cKDTree(csu_coords)

samp_xy = sample_coords_pd[['lat', 'lon']].values.astype(np.float32)
dists_csu, idxs_csu = csu_tree.query(samp_xy, k=1, workers=4)

# Grid resolution ~0.045 deg; use 0.09 deg threshold (2× resolution)
MAX_CSU_DEG = 0.09
csu_assigned = sample_coords_pd[['accession_id']].copy()
valid_csu = dists_csu <= MAX_CSU_DEG
for col in csu_metal_cols:
    vals = csu_grid[col].values[idxs_csu].astype(float)
    vals[~valid_csu] = np.nan
    csu_assigned[col] = vals
print(f"  CSU assigned: {valid_csu.sum()} / {len(sample_coords_pd)} samples matched")

# Upload CSU sample data to Spark via parquet (avoids PyArrow ChunkedArray issue)
csu_for_spark = csu_assigned.copy()
for col in csu_metal_cols:
    csu_for_spark[col] = csu_for_spark[col].astype('float64')
csu_pq = f"{OUTPUT}/csu_sample_lookup.parquet"
csu_for_spark.attrs = {}
csu_for_spark.to_parquet(csu_pq, index=False)
csu_spark = spark.read.parquet(csu_pq)
sg_csu = sample_genus.join(csu_spark, on="accession_id", how="inner")
csu_niche = sg_csu.groupBy("genus_lower").agg(
    *[F.stddev(c).alias(c + "_sd") for c in csu_metal_cols],
    *[F.count(F.when(F.col(c).isNotNull(), 1)).alias(c + "_n") for c in csu_metal_cols],
)
csu_df = csu_niche.toPandas()
csu_df.to_csv(f"{OUTPUT}/env_niche_csu_spark.csv", index=False)
print(f"  Saved env_niche_csu_spark.csv ({len(csu_df)} genera)")

# ─────────────────────────────────────────────────────────────────
# STEP 6: NGSA spatial join (Australia only)
# ─────────────────────────────────────────────────────────────────
print("Step 6: NGSA spatial join (Australia only)...")
ngsa_pd = spark.table("arkinlab_envdbs.ngsa_geochemistry") \
    .select(
        F.col("lat").cast("double").alias("ngsa_lat"),
        F.col("lon").cast("double").alias("ngsa_lon"),
        "Cu_ICP_MS_mg_kg_0_2", "Ni_ICP_MS_mg_kg_0_5", "Zn_ICP_MS_mg_kg_0_9",
        "Pb_ICP_MS_mg_kg_0_1", "As_ICP_MS_mg_kg_0_4", "Co_ICP_MS_mg_kg_0_1",
        "Cr_ICP_MS_mg_kg_0_5", "Hg_AR_mg_kg_0_01",
        "Cu_MMI_ME_mg_kg_0_01", "Ni_MMI_ME_mg_kg_0_005", "Zn_MMI_ME_mg_kg_0_02",
        "Pb_MMI_ME_mg_kg_0_01", "As_MMI_ME_mg_kg_0_01", "Co_MMI_ME_mg_kg_0_005",
        "Cr_MMI_ME_mg_kg_0_001", "Hg_MMI_ME_mg_kg_0_001",
    ) \
    .filter(F.col("ngsa_lat").isNotNull()) \
    .toPandas()
print(f"  NGSA: {len(ngsa_pd)} stations")

ngsa_icp_cols = ['Cu_ICP_MS_mg_kg_0_2', 'Ni_ICP_MS_mg_kg_0_5', 'Zn_ICP_MS_mg_kg_0_9',
                  'Pb_ICP_MS_mg_kg_0_1', 'As_ICP_MS_mg_kg_0_4', 'Co_ICP_MS_mg_kg_0_1',
                  'Cr_ICP_MS_mg_kg_0_5', 'Hg_AR_mg_kg_0_01']
ngsa_mmi_cols = ['Cu_MMI_ME_mg_kg_0_01', 'Ni_MMI_ME_mg_kg_0_005', 'Zn_MMI_ME_mg_kg_0_02',
                  'Pb_MMI_ME_mg_kg_0_01', 'As_MMI_ME_mg_kg_0_01', 'Co_MMI_ME_mg_kg_0_005',
                  'Cr_MMI_ME_mg_kg_0_001', 'Hg_MMI_ME_mg_kg_0_001']
ngsa_all_cols = ngsa_icp_cols + ngsa_mmi_cols

# Australian samples
aus_mask = (
    (sample_coords_pd['lat'] >= -45) & (sample_coords_pd['lat'] <= -10) &
    (sample_coords_pd['lon'] >= 110) & (sample_coords_pd['lon'] <= 155)
)
aus_samples = sample_coords_pd[aus_mask].copy()
print(f"  Australian samples: {len(aus_samples)}")

# KDTree on NGSA stations
ngsa_tree = cKDTree(ngsa_pd[['ngsa_lat', 'ngsa_lon']].values)
aus_xy = aus_samples[['lat', 'lon']].values
dists_aus, idxs_aus = ngsa_tree.query(aus_xy, k=1)

# 200 km threshold ≈ 1.8 degrees
MAX_NGSA_DEG = 200.0 / 111.0
aus_ngsa = aus_samples[['accession_id']].copy()
valid_aus = dists_aus <= MAX_NGSA_DEG
for col in ngsa_all_cols:
    vals = ngsa_pd[col].values[idxs_aus].astype(float)
    vals[~valid_aus] = np.nan
    aus_ngsa[col] = vals
print(f"  NGSA matched: {valid_aus.sum()} Australian samples")

# Upload NGSA sample data to Spark via parquet
aus_ngsa_for_spark = aus_ngsa.copy()
for col in ngsa_all_cols:
    aus_ngsa_for_spark[col] = aus_ngsa_for_spark[col].astype('float64')
ngsa_pq = f"{OUTPUT}/ngsa_sample_lookup.parquet"
aus_ngsa_for_spark.attrs = {}
aus_ngsa_for_spark.to_parquet(ngsa_pq, index=False)
ngsa_spark_df = spark.read.parquet(ngsa_pq)
sg_ngsa = sample_genus.join(ngsa_spark_df, on="accession_id", how="inner")
ngsa_niche = sg_ngsa.groupBy("genus_lower").agg(
    *[F.stddev(c).alias(c + "_sd") for c in ngsa_all_cols],
    *[F.count(F.when(F.col(c).isNotNull(), 1)).alias(c + "_n") for c in ngsa_icp_cols],
)
ngsa_df = ngsa_niche.toPandas()
ngsa_df.to_csv(f"{OUTPUT}/env_niche_ngsa_spark.csv", index=False)
print(f"  Saved env_niche_ngsa_spark.csv ({len(ngsa_df)} genera)")

print("\n=== All niche breadth computations complete ===")
print(f"Outputs in {OUTPUT}/")
print("  env_niche_global_spark.csv  (pH_sd, temp_sd, georoc_*_sd)")
print("  env_niche_csu_spark.csv     (PF1_*_sd mobile metals, global)")
print("  env_niche_ngsa_spark.csv    (ICP-MS + MMI_ME _sd, Australia)")

spark.stop()

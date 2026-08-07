#!/usr/bin/env python3
"""
NGSA-only niche breadth: Australia samples × NGSA ICP-MS + MMI_ME metals.
CSU is already done. This script produces env_niche_ngsa_spark.csv.
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

ngsa_icp_cols = ['Cu_ICP_MS_mg_kg_0_2', 'Ni_ICP_MS_mg_kg_0_5', 'Zn_ICP_MS_mg_kg_0_9',
                  'Pb_ICP_MS_mg_kg_0_1', 'As_ICP_MS_mg_kg_0_4', 'Co_ICP_MS_mg_kg_0_1',
                  'Cr_ICP_MS_mg_kg_0_5', 'Hg_AR_mg_kg_0_01']
ngsa_mmi_cols = ['Cu_MMI_ME_mg_kg_0_01', 'Ni_MMI_ME_mg_kg_0_005', 'Zn_MMI_ME_mg_kg_0_02',
                  'Pb_MMI_ME_mg_kg_0_01', 'As_MMI_ME_mg_kg_0_01', 'Co_MMI_ME_mg_kg_0_005',
                  'Cr_MMI_ME_mg_kg_0_001', 'Hg_MMI_ME_mg_kg_0_001']
ngsa_all_cols = ngsa_icp_cols + ngsa_mmi_cols

# ─────────────────────────────────────────────────────────────────
# STEP 1: Build sample-genus mapping
# ─────────────────────────────────────────────────────────────────
print("Step 1: Building sample-genus table (collect_set)...")
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

sample_to_genera = sample_genus_spark.groupBy("accession_id") \
    .agg(F.collect_set("genus_lower").alias("genera"))
stg_pd = sample_to_genera.toPandas()
print(f"  {len(stg_pd)} samples collected, exploding...")
sg_pd = stg_pd.explode("genera").rename(columns={"genera": "genus_lower"}).dropna(subset=["genus_lower"])
print(f"  sample_genus: {len(sg_pd)} rows, {sg_pd['genus_lower'].nunique()} genera")

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
# STEP 3: NGSA spatial join (Australia only)
# ─────────────────────────────────────────────────────────────────
print("Step 3: NGSA spatial join (Australia only)...")
ngsa_pd = spark.table("arkinlab_envdbs.ngsa_geochemistry") \
    .select(
        F.col("lat").cast("double").alias("ngsa_lat"),
        F.col("lon").cast("double").alias("ngsa_lon"),
        *ngsa_all_cols
    ) \
    .filter(F.col("ngsa_lat").isNotNull()) \
    .toPandas()
print(f"  NGSA: {len(ngsa_pd)} stations")

# Australian samples only
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
    # pd.to_numeric coerces detection-limit strings like '<0.2' to NaN
    numeric_col = pd.to_numeric(ngsa_pd[col], errors='coerce')
    vals = numeric_col.values[idxs_aus].copy().astype(float)
    vals[~valid_aus] = np.nan
    aus_ngsa[col] = vals
print(f"  NGSA matched: {valid_aus.sum()} Australian samples")

# Per-genus aggregation
print("  Aggregating NGSA niche breadth per genus...")
sg_ngsa = sg_pd.merge(aus_ngsa, on='accession_id', how='inner')
print(f"  Merged: {len(sg_ngsa)} sample-genus pairs (Australian)")
ngsa_sd = sg_ngsa.groupby('genus_lower')[ngsa_all_cols].std()
ngsa_n = sg_ngsa.groupby('genus_lower')[ngsa_icp_cols].count()

ngsa_df = ngsa_sd.rename(columns={c: c + '_sd' for c in ngsa_all_cols})
for col in ngsa_icp_cols:
    ngsa_df[col + '_n'] = ngsa_n[col]
ngsa_df = ngsa_df.reset_index()
ngsa_df.to_csv(f"{OUTPUT}/env_niche_ngsa_spark.csv", index=False)
print(f"  Saved env_niche_ngsa_spark.csv ({len(ngsa_df)} genera)")

print("\n=== NGSA niche breadth complete ===")
spark.stop()

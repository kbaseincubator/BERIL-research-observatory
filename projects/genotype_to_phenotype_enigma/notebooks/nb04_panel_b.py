#!/usr/bin/env python3
"""Panel B — microbeatlas global 16S biogeography + env modeling.

For each ENIGMA genus present in microbeatlas:
  1. Filter otu_metadata to find OTU IDs matching the genus (Tax column)
  2. Compute per-sample presence/absence from otu_counts_long
  3. Join enriched_metadata_gee for soil pH, temp, precip, metals, etc.
  4. Fit random forest classifier: genus presence ~ env features → variable importance
  5. Save: per-genus env importance table, per-genus global coords

Produces:
  - data/microbeatlas_genus_env_importance.tsv
  - data/microbeatlas_genus_sample_coords.tsv (lat/lon for each genus's samples)
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark_url = f"sc://jupyter-{os.environ['USER']}.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={os.environ['KBASE_AUTH_TOKEN']}"
spark = SparkSession.builder.remote(spark_url).getOrCreate()

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"

# ── ENIGMA genera (from NB03 strain_scalars + existing microbeatlas summary) ──
# Use the genera that already appear in microbeatlas_genus_summary.tsv since those
# are known-resolvable. Add strain-derived genera if not present.
mbg = pd.read_csv(DATA / "microbeatlas_genus_summary.tsv", sep="\t")
ENIGMA_GENERA = mbg["genus"].tolist()
print(f"Target genera ({len(ENIGMA_GENERA)}): {ENIGMA_GENERA}")

# ── 1. Find OTU IDs for each genus ────────────────────────────────────────────
# Tax column format: "Bacteria;Phylum;Class;Order;Family;Genus;Species..."
# Match genus as the 6th component (0-indexed 5).
otu_meta = spark.table("arkinlab_microbeatlas.otu_metadata").select("otu_id", "Tax")

# Build a filter: Tax CONTAINS ";<genus>;" OR ";<genus>" at end
cond = F.lit(False)
for g in ENIGMA_GENERA:
    cond = cond | F.col("Tax").contains(f";{g};") | F.col("Tax").endswith(f";{g}")
otu_hits = otu_meta.filter(cond).toPandas()
print(f"OTUs matching ENIGMA genera: {len(otu_hits)}")

# Assign genus per OTU
def extract_genus(tax):
    if not tax: return None
    parts = tax.split(";")
    for g in ENIGMA_GENERA:
        if g in parts:
            return g
    return None

otu_hits["genus"] = otu_hits["Tax"].apply(extract_genus)
otu_hits = otu_hits.dropna(subset=["genus"])
print(f"OTU genus counts:")
print(otu_hits.genus.value_counts().to_string())

# ── 2. Per-sample presence per genus ──────────────────────────────────────────
# Broadcast the otu→genus map as a small lookup table
otu2genus = spark.createDataFrame(otu_hits[["otu_id", "genus"]])

# Sample × genus presence: count > 0 means present
counts = (
    spark.table("arkinlab_microbeatlas.otu_counts_long")
    .filter(F.col("count") > 0)
    .join(F.broadcast(otu2genus), "otu_id", "inner")
    .select("sample_id", "genus")
    .distinct()
)
# Convert to pandas: expect ~millions of rows
print("Pulling sample-genus presence...")
presence = counts.toPandas()
print(f"Sample-genus presence rows: {len(presence):,}")
print(f"Unique samples: {presence.sample_id.nunique():,}")

# Pivot to wide: sample × genus (binary)
genus_presence_wide = (
    presence.assign(present=1)
    .pivot_table(index="sample_id", columns="genus", values="present", fill_value=0)
    .astype(int)
)
print(f"Presence matrix: {genus_presence_wide.shape}")

# ── 3. Join enriched_metadata_gee for env features ──────────────────────────
# enriched_metadata_gee.SRS_Join_Key matches the first part of sample_id (before the dot)
# sample_id example: 'ERR1304187.ERS1076305' → SRS_Join_Key='ERS1076305' (second part)
# Actually, looking at sample_metadata: sample_id='SRR...SRS...', SRS_Join_Key='SRS...'
# So SRS_Join_Key is the SRS part. Extract it from sample_id.
print("Pulling enriched_metadata_gee...")
env_cols = [
    "SRS_Join_Key", "lat", "lon",
    "ERA5_mean_2m_air_temperature_K", "ERA5_total_precipitation_mm",
    "csu_as_mg_kg_avg", "csu_cd_mg_kg_avg", "csu_co_mg_kg_avg",
    "csu_cr_mg_kg_avg", "csu_cu_mg_kg_avg", "csu_fe_mg_kg_avg",
    "csu_hg_mg_kg_avg", "csu_ni_mg_kg_avg", "csu_pb_mg_kg_avg", "csu_zn_mg_kg_avg",
    "olm_soil_ph_0cm_H2O", "olm_soil_ph_10cm_H2O", "olm_soil_ph_30cm_H2O",
    "olm_soil_ph_60cm_H2O", "olm_soil_ph_100cm_H2O", "olm_soil_ph_200cm_H2O",
    "olm_soil_clay_10cm_pct", "olm_soil_sand_0cm_pct",
]
env = spark.table("arkinlab_microbeatlas.enriched_metadata_gee").select(env_cols).toPandas()
# Deduplicate: keep one row per SRS_Join_Key (some keys appear multiple times)
env = env.drop_duplicates(subset=["SRS_Join_Key"], keep="first")
print(f"enriched_metadata_gee (deduplicated): {len(env):,} rows")

# Build sample_id → SRS join key
presence_samples = genus_presence_wide.reset_index()
presence_samples["SRS_Join_Key"] = (
    presence_samples["sample_id"].str.split(".").str[1]
)

merged = presence_samples.merge(env, on="SRS_Join_Key", how="left")
n_with_env = merged["lat"].notna().sum()
print(f"Samples with env features: {n_with_env:,} / {len(merged):,}")

# Save geo coords per genus (for maps)
geo_rows = []
for g in [c for c in genus_presence_wide.columns if c in ENIGMA_GENERA]:
    g_samples = merged[merged[g] == 1][["lat", "lon"]].dropna()
    g_samples["genus"] = g
    geo_rows.append(g_samples[["genus", "lat", "lon"]])
geo_df = pd.concat(geo_rows, ignore_index=True)
geo_df.to_csv(DATA / "microbeatlas_genus_sample_coords.tsv", sep="\t", index=False)
print(f"Genus sample coords: {len(geo_df):,} rows → microbeatlas_genus_sample_coords.tsv")

# ── 4. Per-genus random forest variable importance ───────────────────────────
from sklearn.ensemble import RandomForestClassifier

feature_cols = [c for c in env_cols if c not in ("SRS_Join_Key", "lat", "lon")]
# Drop features with no non-null values in our subset; median-fill the rest per-column
X_all = merged[feature_cols].copy()
usable_cols = [c for c in feature_cols if X_all[c].notna().sum() > 100]
dropped_cols = sorted(set(feature_cols) - set(usable_cols))
if dropped_cols:
    print(f"Dropping {len(dropped_cols)} features with <100 non-null: {dropped_cols}")
feature_cols = usable_cols
X_all_filled = X_all[feature_cols].fillna(X_all[feature_cols].median())

importance_rows = []
for g in [c for c in genus_presence_wide.columns if c in ENIGMA_GENERA]:
    y = merged[g].astype(int)
    valid = merged["lat"].notna()
    if valid.sum() < 1000 or y[valid].sum() < 100:
        print(f"  {g}: insufficient data (n_valid={valid.sum()}, n_present={y[valid].sum()}) — skipping")
        continue
    X_g = X_all_filled.loc[valid]
    y_g = y.loc[valid]
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=10, n_jobs=8, random_state=42,
        class_weight="balanced",
    )
    rf.fit(X_g, y_g)
    for col, imp_val in zip(feature_cols, rf.feature_importances_):
        importance_rows.append({
            "genus": g, "feature": col, "importance": imp_val,
            "n_samples_total": len(X_g), "n_samples_present": int(y_g.sum()),
            "oob_prevalence": y_g.mean(),
        })
    print(f"  {g}: fit OK (n={len(X_g):,}, prev={y_g.mean():.3f}), top features: "
          f"{[feature_cols[i] for i in np.argsort(rf.feature_importances_)[-3:][::-1]]}")

importance_df = pd.DataFrame(importance_rows)
importance_df.to_csv(DATA / "microbeatlas_genus_env_importance.tsv", sep="\t", index=False)
print(f"Importance table: {len(importance_df)} rows → microbeatlas_genus_env_importance.tsv")

spark.stop()

#!/usr/bin/env python3
"""Panel C — CORAL Oak Ridge geochemistry linkage.

Joins strain isolation wells (coral_strain_locations.tsv) to per-sample geochemistry
from CORAL bricks:
  - ddt_brick0000080: ~50 elements in ppb, 98K rows, 1.8K samples
  - ddt_brick0000010: uranium/nitrate etc in micromolar

Produces:
  - data/strain_well_geochem.tsv: per-strain geochem summary (one row per strain)
  - data/well_geochem_wide.tsv: well × element wide matrix (for spatial maps)
"""
import os
from pathlib import Path
import pandas as pd
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark_url = f"sc://jupyter-{os.environ['USER']}.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={os.environ['KBASE_AUTH_TOKEN']}"
spark = SparkSession.builder.remote(spark_url).getOrCreate()

HERE = Path(__file__).resolve().parent.parent  # project root
DATA = HERE / "data"

# ── Load strain → location from Panel C pre-staged file ──────────────────────
strain_loc = pd.read_csv(DATA / "coral_strain_locations.tsv", sep="\t")
print(f"Strains with CORAL locations: {len(strain_loc)}")
print(f"Unique wells: {strain_loc.location.nunique()}")
print()

# ── Load geochem bricks from Spark ────────────────────────────────────────────
# Brick 80: ppb geochem (element concentrations)
geo80 = (
    spark.table("enigma_coral.ddt_brick0000080")
    .select(
        F.col("sdt_sample_name").alias("sample"),
        F.col("molecule_from_list_sys_oterm_name").alias("element"),
        F.col("concentration_statistic_average_parts_per_billion").alias("ppb"),
    )
    .filter(F.col("ppb").isNotNull())
    .toPandas()
)
print(f"Brick 80 (ppb): {len(geo80):,} rows, {geo80['sample'].nunique():,} samples, {geo80.element.nunique()} elements")

# Brick 10: micromolar geochem (U, NO3, etc)
geo10 = (
    spark.table("enigma_coral.ddt_brick0000010")
    .select(
        F.col("sdt_sample_name").alias("sample"),
        F.col("molecule_from_list_sys_oterm_name").alias("element"),
        F.col("concentration_micromolar").alias("uM"),
    )
    .filter(F.col("uM").isNotNull())
    .groupBy("sample", "element")
    .agg(F.mean("uM").alias("uM"))
    .toPandas()
)
print(f"Brick 10 (µM): {len(geo10):,} rows, {geo10['sample'].nunique():,} samples, {geo10.element.nunique()} elements")

# ── Load sdt_sample to map sample → location ─────────────────────────────────
sample2loc = (
    spark.table("enigma_coral.sdt_sample")
    .select(
        F.col("sdt_sample_name").alias("sample"),
        F.col("sdt_location_name").alias("location"),
        F.col("depth_meter").alias("depth_m"),
    )
    .toPandas()
)
print(f"sdt_sample entries: {len(sample2loc):,}")

# ── Join brick 80 to locations ────────────────────────────────────────────────
geo80_loc = geo80.merge(sample2loc, on="sample", how="left")
n_loc = geo80_loc["location"].notna().sum()
print(f"Brick 80 rows matched to locations: {n_loc:,} / {len(geo80):,}")

# ── Aggregate per-well per-element (median across samples at that well) ──────
well_elem = (
    geo80_loc.dropna(subset=["location"])
    .groupby(["location", "element"])["ppb"]
    .median()
    .reset_index()
)
well_elem_wide = well_elem.pivot(index="location", columns="element", values="ppb")
print(f"Well × element matrix: {well_elem_wide.shape}")
well_elem_wide.to_csv(DATA / "well_geochem_wide.tsv", sep="\t")

# Also write µM wide (for U, NO3)
geo10_loc = geo10.merge(sample2loc, on="sample", how="left").dropna(subset=["location"])
well_uM_wide = (
    geo10_loc.groupby(["location", "element"])["uM"]
    .median()
    .reset_index()
    .pivot(index="location", columns="element", values="uM")
)
print(f"Well × µM element matrix: {well_uM_wide.shape}")
well_uM_wide.to_csv(DATA / "well_geochem_uM_wide.tsv", sep="\t")

# ── Per-strain geochem: merge strain → location → wide elements ─────────────
strain_geo = strain_loc.merge(well_elem_wide, on="location", how="left")
# Add µM columns with suffix
well_uM_renamed = well_uM_wide.copy()
well_uM_renamed.columns = [f"{c}_uM" for c in well_uM_renamed.columns]
strain_geo = strain_geo.merge(well_uM_renamed, on="location", how="left")

strain_geo.to_csv(DATA / "strain_well_geochem.tsv", sep="\t", index=False)
print(f"Strain × geochem: {strain_geo.shape} — saved to strain_well_geochem.tsv")

# Quick summary
elems_with_coverage = (well_elem_wide.notna().sum(axis=0) >= 5).sum()
print(f"Elements measured in ≥5 wells: {elems_with_coverage}")

# Print uranium summary as sanity check (Oak Ridge contamination)
if "uranium atom" in well_uM_wide.columns:
    u = well_uM_wide["uranium atom"].dropna().sort_values(ascending=False)
    print(f"\nUranium (µM) top 10 wells:")
    print(u.head(10).to_string())
    print(f"Median: {u.median():.2f} µM, max: {u.max():.2f} µM")

spark.stop()

#!/usr/bin/env python3
"""
Phase 3: Assemble full covariate matrix for 634 thinned cells.

Sources:
  - soilgrids_ph_thinned_cells.csv       (pH)
  - ssurgo_thinned_cells.csv             (drainage, OM, clay, CEC)
  - glim_thinned_cells.csv               (lithology)
  - Spark: enriched_metadata             (mine_distance, epa_tri, tectonic_dist)
  - Spark: earthenv_master               (land cover classes at 0.25°)
  - Spark: otu_counts_long + metadata    (Shannon H, phylum abundances)
  - Spark: usgs_geochemistry             (As, Cd, Cr, Cu, Hg, Pb)

Output: data/usa_cwm/covariate_matrix_634.csv
"""
import os, sys, json
os.environ["OMP_NUM_THREADS"] = "1"

import pandas as pd
import numpy as np

DATA = "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"
OUT  = f"{DATA}/covariate_matrix_634.csv"

# ── Load cached files ─────────────────────────────────────────────────────────
print("Loading cached covariates...")
ids   = pd.read_csv(f"{DATA}/thinned_sample_ids.csv")   # sample_id, lat, lon
ph    = pd.read_csv(f"{DATA}/soilgrids_ph_thinned_cells.csv")
ssurgo = pd.read_csv(f"{DATA}/ssurgo_thinned_cells.csv")
glim  = pd.read_csv(f"{DATA}/glim_thinned_cells.csv")

print(f"  IDs: {len(ids)}, pH: {len(ph)}, SSURGO: {len(ssurgo)}, GLiM: {len(glim)}")

# Base matrix: one row per sample_id
cov = ids[["sample_id", "lat", "lon"]].copy()

def nn_join(base_df, lookup_df, value_cols, max_dist_deg=0.5):
    """Nearest-neighbor join on lat/lon, within max_dist_deg degrees."""
    from scipy.spatial import cKDTree
    lookup_valid = lookup_df.dropna(subset=value_cols[:1]).copy()
    tree = cKDTree(lookup_valid[["lat","lon"]].values)
    dists, idx = tree.query(base_df[["lat","lon"]].values, k=1)
    result = base_df.copy()
    for col in value_cols:
        vals = lookup_valid[col].values[idx]
        vals = vals.astype(object)
        vals[dists > max_dist_deg] = np.nan
        result[col] = vals
    return result

# ── pH (SoilGrids) — nearest-neighbor join ───────────────────────────────────
ph_valid = ph[ph["ph_soilgrids"].notna()][["lat","lon","ph_soilgrids"]]
cov = nn_join(cov, ph_valid, ["ph_soilgrids"])
print(f"pH coverage: {cov['ph_soilgrids'].notna().sum()}/{len(cov)}")

# ── SSURGO — nearest-neighbor join ───────────────────────────────────────────
ssurgo_valid = ssurgo[ssurgo["drainage_class"].notna() | ssurgo["ph_ssurgo"].notna()]
cov = nn_join(cov, ssurgo_valid,
              ["drainage_class","ph_ssurgo","organic_matter","clay_pct","cec"])
# For SSURGO, don't propagate NaN-only rows (no actual data)
for col in ["ph_ssurgo","organic_matter","clay_pct","cec"]:
    if col in cov.columns:
        cov[col] = pd.to_numeric(cov[col], errors="coerce")
print(f"SSURGO coverage: {cov['drainage_class'].notna().sum()}/{len(cov)}")

# ── GLiM — nearest-neighbor join ─────────────────────────────────────────────
glim_valid = glim[glim["lith_class"].notna()][["lat","lon","lith_class"]]
cov = nn_join(cov, glim_valid, ["lith_class"])
print(f"GLiM coverage: {cov['lith_class'].notna().sum()}/{len(cov)}")

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

# Build sample ID list for IN clauses
sample_ids = cov["sample_id"].tolist()
id_list = "('" + "','".join(sample_ids) + "')"

# ── enriched_metadata: mine_distance, EPA TRI, tectonic_dist ─────────────────
# enriched_metadata.sample_id is BIGINT — join by lat/lon instead of sample_id
print("Querying enriched_metadata for USA cells (lat/lon join)...")
em_df = spark.sql("""
    SELECT CAST(lat AS DOUBLE) AS lat,
           CAST(lon AS DOUBLE) AS lon,
           USGS_MRDS_Mines_nearest_deposit_distance_km AS usgs_mine_distance,
           EPA_TRI_tri_total_releases_lbs              AS epa_tri_releases,
           Tectonic_Plates_tectonic_boundary_distance_km AS tectonic_boundary_dist
    FROM arkinlab.microbeatlas.enriched_metadata
    WHERE CAST(lat AS DOUBLE) BETWEEN 24 AND 55
      AND CAST(lon AS DOUBLE) BETWEEN -130 AND -60
      AND USGS_MRDS_Mines_nearest_deposit_distance_km IS NOT NULL
""").toPandas()
em_df.attrs = {}
print(f"  enriched_metadata USA rows: {len(em_df)}")

# Nearest-neighbor join by lat/lon
cov = nn_join(cov, em_df, ["usgs_mine_distance","epa_tri_releases","tectonic_boundary_dist"])
for col in ["usgs_mine_distance","epa_tri_releases","tectonic_boundary_dist"]:
    cov[col] = pd.to_numeric(cov[col], errors="coerce")
print(f"  mine_distance coverage: {cov['usgs_mine_distance'].notna().sum()}/{len(cov)}")

# ── earthenv_master: land cover classes ───────────────────────────────────────
print("Querying earthenv_master for land cover...")
# Round to 0.25° grid for join
cov["lat_grid"] = (cov["lat"] / 0.25).round() * 0.25
cov["lon_grid"] = (cov["lon"] / 0.25).round() * 0.25

ee_df = spark.sql("""
    SELECT CAST(lat AS DOUBLE) AS lat_grid,
           CAST(lon AS DOUBLE) AS lon_grid,
           landcover_class_1_pct,
           landcover_class_2_pct,
           landcover_class_3_pct,
           landcover_class_4_pct,
           landcover_class_7_pct,
           landcover_class_9_pct,
           landcover_class_11_pct
    FROM arkinlab.envdbs.earthenv_master
    WHERE CAST(lat AS DOUBLE) BETWEEN 24 AND 50
      AND CAST(lon AS DOUBLE) BETWEEN -125 AND -65
      AND landcover_class_7_pct IS NOT NULL
""").toPandas()
ee_df.attrs = {}
print(f"  earthenv USA rows: {len(ee_df)}")

cov = cov.merge(ee_df, on=["lat_grid", "lon_grid"], how="left")

# Compute composite land cover variables
tree_cols = ["landcover_class_1_pct", "landcover_class_2_pct",
             "landcover_class_3_pct", "landcover_class_4_pct"]
cov["lc_forest_pct"]    = cov[tree_cols].sum(axis=1)
cov["lc_cultivated_pct"] = cov["landcover_class_7_pct"]
cov["lc_urban_pct"]     = cov["landcover_class_9_pct"]
cov["lc_barren_pct"]    = cov["landcover_class_11_pct"]
cov.drop(columns=tree_cols + ["landcover_class_7_pct", "landcover_class_9_pct",
                               "landcover_class_11_pct"], inplace=True)
print(f"  land cover coverage: {cov['lc_cultivated_pct'].notna().sum()}/{len(cov)}")
cov.drop(columns=["lat_grid", "lon_grid"], inplace=True)

# ── Metal concentrations from usgs_geochemistry joined parquet ────────────────
# usa_cwm_usgs_joined.parquet has (sample_id, ko_id, cwm, As, Cd, Cr, Cu, Hg, Pb)
# Deduplicate by sample_id to get one row of metal values per sample
print("Loading USGS metal concentrations from join parquet...")
joined = pd.read_parquet(
    f"{DATA}/usa_cwm_usgs_joined.parquet",
    columns=["sample_id", "As", "Cd", "Cr", "Cu", "Hg", "Pb"]
)
metals_df = (
    joined[joined["sample_id"].isin(sample_ids)]
    .drop_duplicates(subset="sample_id")
    .reset_index(drop=True)
)
print(f"  metals rows: {len(metals_df)}, As coverage: {metals_df['As'].notna().sum()}")
cov = cov.merge(metals_df[["sample_id","As","Cd","Cr","Cu","Hg","Pb"]],
                on="sample_id", how="left")

# ── Shannon H and phylum abundances from OTU table ───────────────────────────
print("Computing Shannon H and phylum abundances from OTU counts...")
otu_df = spark.sql(f"""
    WITH counts AS (
        SELECT o.sample_id,
               element_at(SPLIT(om.tax, ';'), 2) AS phylum_raw,
               CAST(o.count AS DOUBLE) AS cnt
        FROM arkinlab.microbeatlas.otu_counts_long o
        JOIN arkinlab.microbeatlas.otu_metadata om ON o.otu_id = om.otu_id
        WHERE o.sample_id IN {id_list}
          AND om.tax IS NOT NULL
          AND SIZE(SPLIT(om.tax, ';')) >= 2
    ),
    totals AS (
        SELECT sample_id, SUM(cnt) AS total_cnt
        FROM counts GROUP BY sample_id
    ),
    ra AS (
        SELECT c.sample_id, c.phylum_raw,
               SUM(c.cnt) / t.total_cnt AS phylum_ra
        FROM counts c JOIN totals t ON c.sample_id = t.sample_id
        GROUP BY c.sample_id, c.phylum_raw, t.total_cnt
    )
    SELECT sample_id, phylum_raw, phylum_ra
    FROM ra
    WHERE phylum_raw IS NOT NULL
""").toPandas()
otu_df.attrs = {}
print(f"  OTU phylum rows: {len(otu_df)}")

# Shannon H per sample (over phyla)
def shannon(s): return -np.sum(s[s > 0] * np.log(s[s > 0]))
shannon_df = (
    otu_df.groupby("sample_id")["phylum_ra"]
    .apply(shannon)
    .reset_index()
    .rename(columns={"phylum_ra": "shannon"})
)
cov = cov.merge(shannon_df, on="sample_id", how="left")
print(f"  Shannon coverage: {cov['shannon'].notna().sum()}/{len(cov)}")

# Pivot to phylum columns — clean phylum name, top 8 by mean RA
otu_df["phylum"] = (
    otu_df["phylum_raw"]
    .str.strip()
    .str.replace(r"^p__", "", regex=True)
    .str.replace(r"[^A-Za-z0-9]", "_", regex=True)
    .str[:30]
)
mean_ra = otu_df.groupby("phylum")["phylum_ra"].mean().sort_values(ascending=False)
top8 = mean_ra.head(8).index.tolist()
print(f"  Top 8 phyla: {top8}")

phylum_pivot = (
    otu_df[otu_df["phylum"].isin(top8)]
    .groupby(["sample_id", "phylum"])["phylum_ra"]
    .sum()
    .unstack(fill_value=0.0)
    .reset_index()
)
phylum_pivot.columns = ["sample_id"] + [f"phylum_{p}" for p in phylum_pivot.columns[1:]]
cov = cov.merge(phylum_pivot, on="sample_id", how="left")
phylum_cols = [c for c in cov.columns if c.startswith("phylum_")]
print(f"  Phylum columns: {phylum_cols}")

# ── Save ──────────────────────────────────────────────────────────────────────
print(f"\nCovariate matrix shape: {cov.shape}")
print("Non-null counts:")
for col in cov.columns:
    n = cov[col].notna().sum()
    if n < len(cov):
        print(f"  {col}: {n}/{len(cov)} ({100*n/len(cov):.1f}%)")

cov.to_csv(OUT, index=False)
print(f"\nSaved: {OUT}")
print("Done.")

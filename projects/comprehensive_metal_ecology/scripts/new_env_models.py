"""
new_env_models.py
==================
Q4 extension (Exploratory): Models F–I using newly available envdbs tables.

  F  science_2025_global_soil_toxic_metals  → soil metal hazard quotients (H4a direct)
  G  soiltemp                               → measured soil temp range (H4b improved)
  H  ecotapestry_lithology_0_25deg          → mafic/felsic bedrock score (H4a categorical)
  I  usgs_ree_occurrences                   → proximity to REE deposits

All models: niche_breadth ~ metal_z + lat_abs_z + [covariate_z]
Results appended to data/latitude_mechanism_results.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

from pgls_utils import run_pgls
from berdl_notebook_utils import get_spark_session

TREE       = DATA / "gtdb_bac_genus_pruned.tree"
PGLS_INPUT = DATA / "01_pgls_input_bacteria.csv"
COV_CSV    = DATA / "genus_lat_env_covariates.csv"
RESULTS    = DATA / "latitude_mechanism_results.csv"
MIN_GENERA = 100
MAX_DIST_DEG = 1.5

print("Connecting to Spark...")
spark = get_spark_session()

genus_env  = pd.read_csv(COV_CSV)
pgls_input = pd.read_csv(PGLS_INPUT)
existing   = pd.read_csv(RESULTS)

def z(s): return (s - s.mean()) / s.std()

def kd_join(genus_env, grid_df, lat_col, lon_col, value_cols,
            max_dist=MAX_DIST_DEG, prefix=""):
    """KD-tree nearest-neighbour join; returns genus_env with new columns."""
    valid = grid_df.dropna(subset=[value_cols[0]]).copy()
    kd    = cKDTree(valid[[lat_col, lon_col]].values)
    dist, idx = kd.query(genus_env[["median_lat", "median_lon"]].values, k=1)
    for col in value_cols:
        vals = valid[col].values[idx]
        genus_env[prefix + col] = np.where(dist <= max_dist, vals, np.nan)
    n_matched = genus_env[prefix + value_cols[0]].notna().sum()
    print(f"  Matched {n_matched:,}/{len(genus_env):,} genera within {max_dist}°")
    return genus_env

def run_model(label, note, df, predictors):
    df = df.dropna(subset=["mean_levins_B_std"] + predictors).copy()
    n  = len(df)
    print(f"\n  Model {label} (n={n}): {predictors}")
    nan_row = {k: np.nan for k in ["beta_metal","SE_metal","p_metal","lambda_est",
                                    "beta_lat","p_lat","beta_soil","p_soil",
                                    "beta_temp","p_temp","beta_cmmi","p_cmmi"]}
    base = {"model": label, "note": note, "predictors": str(predictors), "n_pgls": n}
    if n < MIN_GENERA:
        print(f"    SKIP n={n} < {MIN_GENERA}")
        return {**base, "status": f"SKIP: n<{MIN_GENERA}", **nan_row}
    try:
        res   = run_pgls(df, tree_path=TREE, response="mean_levins_B_std",
                         predictors=predictors, taxon_col="genus_lower",
                         label=f"lat_{label}", min_n=30)
        betas = res.get("betas",  {})
        SEs   = res.get("SEs",    {})
        pvals = res.get("p_values", {})
        lam   = float(res.get("lambda_est", np.nan))
        n_fit = int(res.get("n", n))
        for k, v in betas.items():
            print(f"    {k}: beta={v:.4f} SE={SEs.get(k,np.nan):.4f} p={pvals.get(k,np.nan):.4e}")
        print(f"    lambda={lam:.3f}  n={n_fit}")
        # map to fixed columns; extra predictors land in beta_soil/beta_temp
        pred3 = predictors[2] if len(predictors) > 2 else None
        return {**base, "status": "OK", "lambda_est": lam, "n_pgls": n_fit,
                "beta_metal": betas.get("metal_z",   np.nan),
                "SE_metal":   SEs.get("metal_z",     np.nan),
                "p_metal":    pvals.get("metal_z",   np.nan),
                "beta_lat":   betas.get("lat_abs_z", np.nan),
                "p_lat":      pvals.get("lat_abs_z", np.nan),
                "beta_soil":  betas.get(pred3, np.nan) if pred3 else np.nan,
                "p_soil":     pvals.get(pred3, np.nan) if pred3 else np.nan,
                "beta_temp":  np.nan, "p_temp": np.nan,
                "beta_cmmi":  np.nan, "p_cmmi": np.nan}
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return {**base, "status": f"ERROR: {exc}", **nan_row}

results = []

# ─────────────────────────────────────────────────────────────────────────────
# MODEL F  —  science_2025_global_soil_toxic_metals (HHET hazard quotients)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[F] Aggregating science_2025 soil metal hazard quotients to 0.5° bins...")
f_sql = """
    SELECT
        ROUND(CAST(latitude  AS DOUBLE) / 0.5) * 0.5 AS bin_lat,
        ROUND(CAST(longitude AS DOUBLE) / 0.5) * 0.5 AS bin_lon,
        AVG(CAST(cu AS DOUBLE)) AS hq_cu,
        AVG(CAST(ni AS DOUBLE)) AS hq_ni,
        AVG(CAST(co AS DOUBLE)) AS hq_co,
        AVG(CAST(cr AS DOUBLE)) AS hq_cr,
        AVG(CAST(pb AS DOUBLE)) AS hq_pb,
        COUNT(*) AS n_cells
    FROM arkinlab.envdbs.science_2025_global_soil_toxic_metals
    WHERE threshold_type = 'HHET'
    GROUP BY
        ROUND(CAST(latitude  AS DOUBLE) / 0.5) * 0.5,
        ROUND(CAST(longitude AS DOUBLE) / 0.5) * 0.5
"""
sci_grid = spark.sql(f_sql).toPandas()
print(f"  {len(sci_grid):,} 0.5° bins; lat [{sci_grid.bin_lat.min():.0f}, {sci_grid.bin_lat.max():.0f}]")

genus_env = kd_join(genus_env, sci_grid, "bin_lat", "bin_lon",
                    ["hq_cu","hq_ni","hq_co","hq_cr","hq_pb"], prefix="sci_")
hq_cols = ["sci_hq_cu","sci_hq_ni","sci_hq_co","sci_hq_cr","sci_hq_pb"]
genus_env["sci_metal_hq"] = genus_env[hq_cols].mean(axis=1)

merged_f = pgls_input.merge(genus_env, on="genus_lower", how="inner")
merged_f["metal_z"]   = z(merged_f["predictor_z"])
merged_f["lat_abs_z"] = z(merged_f["lat_abs"])
mf = merged_f[merged_f["sci_metal_hq"].notna()].copy()
mf["sci_hq_z"] = z(mf["sci_metal_hq"])
print(f"  Genera with science_2025 match: {len(mf)}")
results.append(run_model(
    "F_metal_lat_sci2025",
    "H4a: science_2025 HHET soil metal hazard quotients (Cu/Ni/Co/Cr/Pb)",
    mf, ["metal_z", "lat_abs_z", "sci_hq_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# MODEL G  —  soiltemp (measured soil temperature range at −10 cm)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[G] Aggregating soiltemp (−10 cm) to per-site annual range...")
g_sql = """
    SELECT
        ROUND(CAST(longitude AS DOUBLE) / 0.5) * 0.5 AS bin_lon,
        ROUND(CAST(latitude  AS DOUBLE) / 0.5) * 0.5 AS bin_lat,
        MAX(CAST(meantemp AS DOUBLE)) - MIN(CAST(meantemp AS DOUBLE)) AS soil_temp_range,
        AVG(CAST(meantemp AS DOUBLE)) AS soil_temp_mean,
        COUNT(DISTINCT plotcode) AS n_sites
    FROM arkinlab.envdbs.soiltemp
    WHERE height = -10.0
      AND meantemp IS NOT NULL
    GROUP BY
        ROUND(CAST(longitude AS DOUBLE) / 0.5) * 0.5,
        ROUND(CAST(latitude  AS DOUBLE) / 0.5) * 0.5
"""
st_grid = spark.sql(g_sql).toPandas()
print(f"  {len(st_grid):,} 0.5° bins; lat [{st_grid.bin_lat.min():.0f}, {st_grid.bin_lat.max():.0f}]")
print(f"  Soil temp range: {st_grid.soil_temp_range.min():.1f}–{st_grid.soil_temp_range.max():.1f} °C")

genus_env = kd_join(genus_env, st_grid, "bin_lat", "bin_lon",
                    ["soil_temp_range", "soil_temp_mean"], prefix="")

merged_g = pgls_input.merge(genus_env, on="genus_lower", how="inner")
merged_g["metal_z"]   = z(merged_g["predictor_z"])
merged_g["lat_abs_z"] = z(merged_g["lat_abs"])
mg = merged_g[merged_g["soil_temp_range"].notna()].copy()
mg["soil_temp_range_z"] = z(mg["soil_temp_range"])
print(f"  Genera with soiltemp match: {len(mg)}")
results.append(run_model(
    "G_metal_lat_soiltemp",
    "H4b: measured soil temp range at −10 cm (SoilTemp db)",
    mg, ["metal_z", "lat_abs_z", "soil_temp_range_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# MODEL H  —  ecotapestry_lithology_0_25deg (mafic/felsic score)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[H] Loading ecotapestry lithology (0.25°)...")
ecotap = spark.sql(
    "SELECT CAST(lat AS DOUBLE) AS lat, CAST(lon AS DOUBLE) AS lon, lithology_name "
    "FROM arkinlab.envdbs.ecotapestry_lithology_0_25deg"
).toPandas()

# Mafic score: basic (mafic) = 2, intermediate = 1, acid (felsic) = 0
MAFIC = {
    "Basic volcanic":              2.0,
    "Basic plutonics":             2.0,
    "Intermediate volcanic":       1.0,
    "Intermediate plutonics":      1.0,
    "Pyroclastics":                1.0,
    "Metamorphics":                0.5,   # variable
    "Mixed sedimentary rock":      0.4,
    "Siliciclastic sedimentary rock": 0.3,
    "Unconsolidated sediment":     0.3,
    "Carbonate sedimentary rock":  0.2,
    "Evaporite":                   0.1,
    "Acid volcanic":               0.0,
    "Acid plutonics":              0.0,
}
ecotap["mafic_score"] = ecotap["lithology_name"].map(MAFIC)
# Ice/glaciers, NULL, Undefined → NaN (excluded from join)
ecotap_valid = ecotap.dropna(subset=["mafic_score"]).copy()
print(f"  {len(ecotap_valid):,} cells with mafic score (of {len(ecotap):,} total)")

genus_env = kd_join(genus_env, ecotap_valid, "lat", "lon",
                    ["mafic_score"], prefix="", max_dist=0.5)

merged_h = pgls_input.merge(genus_env, on="genus_lower", how="inner")
merged_h["metal_z"]   = z(merged_h["predictor_z"])
merged_h["lat_abs_z"] = z(merged_h["lat_abs"])
mh = merged_h[merged_h["mafic_score"].notna()].copy()
mh["mafic_z"] = z(mh["mafic_score"])
print(f"  Genera with lithology match: {len(mh)}")
results.append(run_model(
    "H_metal_lat_lithology",
    "H4a: ecotapestry mafic/felsic bedrock score (basic=2, acid=0)",
    mh, ["metal_z", "lat_abs_z", "mafic_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# MODEL I  —  usgs_ree_occurrences (proximity to REE deposits)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[I] Loading USGS REE occurrences...")
ree = spark.sql("""
    SELECT CAST(latitude AS DOUBLE) AS lat, CAST(longitude AS DOUBLE) AS lon
    FROM arkinlab.envdbs.usgs_ree_occurrences
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
      AND latitude != '' AND longitude != ''
""").toPandas().dropna()
print(f"  {len(ree):,} REE occurrence points; lat [{ree.lat.min():.1f}, {ree.lat.max():.1f}]")

ree_kd   = cKDTree(ree[["lat","lon"]].values)
g_coords = genus_env[["median_lat","median_lon"]].values
ree_dist, _ = ree_kd.query(g_coords, k=1)
genus_env["ree_nearest_deg"] = ree_dist
print(f"  REE distance range: {ree_dist.min():.2f}–{ree_dist.max():.2f}°")

merged_i = pgls_input.merge(genus_env, on="genus_lower", how="inner")
merged_i["metal_z"]      = z(merged_i["predictor_z"])
merged_i["lat_abs_z"]    = z(merged_i["lat_abs"])
merged_i["ree_log_dist_z"] = z(np.log1p(merged_i["ree_nearest_deg"]))
print(f"  Genera for Model I: {len(merged_i)}")
results.append(run_model(
    "I_metal_lat_ree",
    "REE deposit proximity: does REE geology explain niche breadth?",
    merged_i, ["metal_z", "lat_abs_z", "ree_log_dist_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
new_labels = [r["model"] for r in results]
existing_trimmed = existing[~existing["model"].isin(new_labels)]
out = pd.concat([existing_trimmed, pd.DataFrame(results)], ignore_index=True)
out.to_csv(RESULTS, index=False)
print(f"\nSaved {len(out)} rows to {RESULTS}")
print(out[["model","n_pgls","beta_metal","p_metal","beta_soil","p_soil","status"]].to_string(index=False))

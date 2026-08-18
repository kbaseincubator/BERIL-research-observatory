"""
csu_mobility_model.py
======================
Q4 extension (Exploratory): Model E — metal gene niche breadth vs
CSU bioavailable metal mobility fractions (PF1) from the global
csu_metal_mobility_grid table (arkinlab.envdbs).

Strategy:
  1. Aggregate CSU grid to 0.5-degree bins in Spark (7.37M rows → ~60K bins).
  2. Pull aggregated grid to pandas and build a KD-tree.
  3. For each genus (median lat/lon from genus_lat_env_covariates.csv), find
     the nearest 0.5-degree bin (up to MAX_DIST_DEG = 1.5°).
  4. Merge with PGLS input; run Model E PGLS (multi-predictor, exploratory).
  5. Append Model E row to data/latitude_mechanism_results.csv.

PF1 = mobile (bioavailable) fraction of total metal; values 0–1.
Columns available: PF1_As, PF1_Cd, PF1_Cr, PF1_Cu, PF1_Hg, PF1_Pb.
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
MAX_DIST_DEG = 1.5  # reject genus-grid matches farther than this

# ---------------------------------------------------------------------------
# Step 1 — Aggregate CSU grid to 0.5-degree bins in Spark
# ---------------------------------------------------------------------------
print("Connecting to Spark...")
spark = get_spark_session()

print("Aggregating CSU mobility grid to 0.5° bins...")
csu_sql = """
    SELECT
        ROUND(CAST(latitude  AS DOUBLE) / 0.5) * 0.5 AS bin_lat,
        ROUND(CAST(longitude AS DOUBLE) / 0.5) * 0.5 AS bin_lon,
        AVG(CAST(PF1_As AS DOUBLE)) AS pf1_As,
        AVG(CAST(PF1_Cd AS DOUBLE)) AS pf1_Cd,
        AVG(CAST(PF1_Cr AS DOUBLE)) AS pf1_Cr,
        AVG(CAST(PF1_Cu AS DOUBLE)) AS pf1_Cu,
        AVG(CAST(PF1_Hg AS DOUBLE)) AS pf1_Hg,
        AVG(CAST(PF1_Pb AS DOUBLE)) AS pf1_Pb,
        COUNT(*) AS n_cells
    FROM arkinlab.envdbs.csu_metal_mobility_grid
    GROUP BY
        ROUND(CAST(latitude  AS DOUBLE) / 0.5) * 0.5,
        ROUND(CAST(longitude AS DOUBLE) / 0.5) * 0.5
"""
csu_grid = spark.sql(csu_sql).toPandas()
print(f"  CSU 0.5° bins returned: {len(csu_grid):,}")
print(f"  Coverage: lat {csu_grid.bin_lat.min():.1f} to {csu_grid.bin_lat.max():.1f}")

# ---------------------------------------------------------------------------
# Step 2 — KD-tree spatial join to genus median lat/lons
# ---------------------------------------------------------------------------
genus_env = pd.read_csv(COV_CSV)
print(f"\nGenus covariates loaded: {len(genus_env)} genera")

csu_valid = csu_grid.dropna(subset=["pf1_Cu"]).copy()
tree_coords = csu_valid[["bin_lat", "bin_lon"]].values
kd = cKDTree(tree_coords)

genus_coords = genus_env[["median_lat", "median_lon"]].values
dist, idx = kd.query(genus_coords, k=1)

# Assign CSU values only where match is within MAX_DIST_DEG
for col in ["pf1_As", "pf1_Cd", "pf1_Cr", "pf1_Cu", "pf1_Hg", "pf1_Pb"]:
    vals = csu_valid[col].values[idx]
    vals = np.where(dist <= MAX_DIST_DEG, vals, np.nan)
    genus_env[f"csu_{col}"] = vals

n_csu = genus_env["csu_pf1_Cu"].notna().sum()
print(f"  Genera with CSU match within {MAX_DIST_DEG}°: {n_csu:,} / {len(genus_env):,}")

# Composite CSU mobility index: mean of non-null PF1 values across 6 metals
pf1_cols = ["csu_pf1_As", "csu_pf1_Cd", "csu_pf1_Cr",
            "csu_pf1_Cu", "csu_pf1_Hg", "csu_pf1_Pb"]
genus_env["csu_mobility_index"] = genus_env[pf1_cols].mean(axis=1)

# ---------------------------------------------------------------------------
# Step 3 — Merge with PGLS input and run Model E
# ---------------------------------------------------------------------------
pgls_input = pd.read_csv(PGLS_INPUT)
merged = pgls_input.merge(genus_env, on="genus_lower", how="inner")
print(f"\nMerged with PGLS input: {len(merged)} genera")

def z(s): return (s - s.mean()) / s.std()

merged["metal_z"]       = z(merged["predictor_z"])
merged["lat_abs_z"]     = z(merged["lat_abs"])
merged["csu_mob_z"]     = z(merged["csu_mobility_index"])

merged_csu = merged[merged["csu_mobility_index"].notna()].copy()
merged_csu["csu_mob_z"] = z(merged_csu["csu_mobility_index"])
print(f"  With CSU mobility covariate: {len(merged_csu)}")
print(f"  CSU mobility range: {merged_csu['csu_mobility_index'].min():.3f} – {merged_csu['csu_mobility_index'].max():.3f}")

print("\n[EXPLORATORY] Model E: metal + |lat| + CSU bioavailable mobility index (H4a via PF1)")
if len(merged_csu) < MIN_GENERA:
    print(f"  SKIP: n={len(merged_csu)} < {MIN_GENERA}")
    new_row = {"model": "E_metal_lat_csu_mobility",
               "note": "H4a via CSU PF1 bioavailable mobility fractions (As/Cd/Cr/Cu/Hg/Pb)",
               "predictors": "['metal_z', 'lat_abs_z', 'csu_mob_z']",
               "n_pgls": len(merged_csu), "status": f"SKIP: n<{MIN_GENERA}",
               **{k: np.nan for k in ["beta_metal","SE_metal","p_metal","lambda_est",
                                       "beta_lat","p_lat","beta_soil","p_soil",
                                       "beta_temp","p_temp","beta_cmmi","p_cmmi"]}}
else:
    df = merged_csu.dropna(subset=["mean_levins_B_std","metal_z","lat_abs_z","csu_mob_z"]).copy()
    print(f"  Final n after dropna: {len(df)}")
    res = run_pgls(df, tree_path=TREE,
                   response="mean_levins_B_std",
                   predictors=["metal_z", "lat_abs_z", "csu_mob_z"],
                   taxon_col="genus_lower",
                   label="lat_E_csu", min_n=30)
    betas = res.get("betas",  {})
    SEs   = res.get("SEs",    {})
    pvals = res.get("p_values", {})
    lam   = float(res.get("lambda_est", np.nan))
    n_fit = int(res.get("n", len(df)))
    for k, v in betas.items():
        print(f"    {k}: beta={v:.4f} SE={SEs.get(k,np.nan):.4f} p={pvals.get(k,np.nan):.4e}")
    print(f"    lambda={lam:.3f}  n={n_fit}")
    new_row = {
        "model": "E_metal_lat_csu_mobility",
        "note": "H4a via CSU PF1 bioavailable mobility fractions (As/Cd/Cr/Cu/Hg/Pb)",
        "predictors": "['metal_z', 'lat_abs_z', 'csu_mob_z']",
        "n_pgls": n_fit, "lambda_est": lam, "status": "OK",
        "beta_metal": betas.get("metal_z",   np.nan),
        "SE_metal":   SEs.get("metal_z",     np.nan),
        "p_metal":    pvals.get("metal_z",   np.nan),
        "beta_lat":   betas.get("lat_abs_z", np.nan),
        "p_lat":      pvals.get("lat_abs_z", np.nan),
        "beta_soil":  betas.get("csu_mob_z", np.nan),
        "p_soil":     pvals.get("csu_mob_z", np.nan),
        "beta_temp":  np.nan, "p_temp": np.nan,
        "beta_cmmi":  np.nan, "p_cmmi": np.nan,
    }

# ---------------------------------------------------------------------------
# Append to results CSV
# ---------------------------------------------------------------------------
existing = pd.read_csv(RESULTS)
# Drop any old Model E row if re-running
existing = existing[existing["model"] != "E_metal_lat_csu_mobility"]
out = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
out.to_csv(RESULTS, index=False)
print(f"\nAppended Model E to {RESULTS}")
print(out[["model","n_pgls","beta_metal","p_metal","beta_lat","p_lat","status"]].to_string(index=False))

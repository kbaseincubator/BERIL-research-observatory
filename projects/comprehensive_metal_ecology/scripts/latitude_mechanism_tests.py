"""
latitude_mechanism_tests.py
============================
Q4 (Exploratory): Latitude mechanism tests — does the metal gene → niche breadth
association persist after controlling for latitude? If latitude confounds the
result, do soil metal concentrations (H4a) or climate (H4b) explain it?

Data pipeline:
  1. From arkinlab_microbeatlas.otu_counts_long + otu_metadata:
     OTU presence-by-sample with genus taxonomy.
  2. Joined with arkinlab_microbeatlas.enriched_metadata_gee (via SRS_Join_Key)
     for lat/lon, ERA5 temperature (climate proxy), CSU soil metals.
  3. Aggregated to genus-level median values.
  4. Merged with 01_pgls_input_bacteria.csv.
  5. Three PGLS models (all labelled EXPLORATORY):
     - Model A: niche_breadth ~ metal_z + lat_abs_z          (latitude confounder)
     - Model B: niche_breadth ~ metal_z + lat_abs_z + soil_metal_z  (H4a)
     - Model C: niche_breadth ~ metal_z + lat_abs_z + temp_z (H4b climate stability)

Outputs:
  data/genus_lat_env_covariates.csv  — per-genus lat/env table
  data/latitude_mechanism_results.csv — PGLS results
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

from pgls_utils import run_pgls
from berdl_notebook_utils import get_spark_session

TREE = DATA / "gtdb_bac_genus_pruned.tree"
PGLS_INPUT = DATA / "01_pgls_input_bacteria.csv"
MIN_GENERA = 100

# ---------------------------------------------------------------------------
# Step 1 — Genus-level lat/env from MicrobeAtlas OTU data
# ---------------------------------------------------------------------------

COVARIATE_CSV = DATA / "genus_lat_env_covariates.csv"

# Delete stale cache so the GeoROC join is picked up on this run.
if COVARIATE_CSV.exists():
    COVARIATE_CSV.unlink()
    print(f"Deleted stale cache: {COVARIATE_CSV.name}")

print("Connecting to Spark...")
spark = get_spark_session()

# Aggregate entirely in Spark to avoid pulling >1 GB of row-level data.
# PERCENTILE_APPROX(x, 0.5) = approximate median; NULLs are ignored.
#
# Two geochemistry sources joined per sample:
#   - enriched_metadata_gee (via SRS key): ERA5 temp, terraclimate tmax/tmin, OLM pH
#   - enriched_metadata    (via sample_id): GeoROC bedrock metals Cu/Ni/Zn/Co/Pb/Cr (ppm)
#     Negative GeoROC values = below detection limit; only positives enter the index.
#
# GeoROC metal index = LN(1 + mean_of_positive_values), NULL when no positive value exists.
# Signed lat/lon retained for downstream spatial joins (e.g. cmmi_ores proximity).
print("Querying genus-level lat/env (aggregated in Spark)...")
sql = """
    SELECT
        LOWER(TRIM(regexp_extract(m.Tax, ';([^;]+)$', 1))) AS genus_lower,
        COUNT(DISTINCT regexp_extract(c.sample_id, '(SRS[0-9]+)', 1)) AS n_samples,
        PERCENTILE_APPROX(g.lat, 0.5)                                 AS median_lat,
        PERCENTILE_APPROX(g.lon, 0.5)                                 AS median_lon,
        PERCENTILE_APPROX(ABS(g.lat), 0.5)                            AS lat_abs,
        PERCENTILE_APPROX(g.ERA5_mean_2m_air_temperature_K - 273.15, 0.5)
                                                                       AS era5_temp_C,
        PERCENTILE_APPROX(g.terraclimate_tmax_C - g.terraclimate_tmin_C, 0.5)
                                                                       AS temp_range_C,
        PERCENTILE_APPROX(g.olm_soil_ph_10cm_H2O, 0.5)               AS soil_ph,
        -- GeoROC bedrock metals from enriched_metadata (join via accession_id string).
        -- Only use values > 0 (negatives are below-detection flags in GeoROC).
        PERCENTILE_APPROX(
            CASE
                WHEN (CASE WHEN e.GeoROC_Rocks_georoc_Cu_ppm > 0 THEN 1 ELSE 0 END
                    + CASE WHEN e.GeoROC_Rocks_georoc_Ni_ppm > 0 THEN 1 ELSE 0 END
                    + CASE WHEN e.GeoROC_Rocks_georoc_Zn_ppm > 0 THEN 1 ELSE 0 END
                    + CASE WHEN e.GeoROC_Rocks_georoc_Co_ppm > 0 THEN 1 ELSE 0 END
                    + CASE WHEN e.GeoROC_Rocks_georoc_Pb_ppm > 0 THEN 1 ELSE 0 END
                    + CASE WHEN e.GeoROC_Rocks_georoc_Cr_ppm > 0 THEN 1 ELSE 0 END) = 0
                THEN NULL
                ELSE LN(1 + (
                        COALESCE(GREATEST(e.GeoROC_Rocks_georoc_Cu_ppm, 0), 0)
                      + COALESCE(GREATEST(e.GeoROC_Rocks_georoc_Ni_ppm, 0), 0)
                      + COALESCE(GREATEST(e.GeoROC_Rocks_georoc_Zn_ppm, 0), 0)
                      + COALESCE(GREATEST(e.GeoROC_Rocks_georoc_Co_ppm, 0), 0)
                      + COALESCE(GREATEST(e.GeoROC_Rocks_georoc_Pb_ppm, 0), 0)
                      + COALESCE(GREATEST(e.GeoROC_Rocks_georoc_Cr_ppm, 0), 0)
                    ) / (
                        (CASE WHEN e.GeoROC_Rocks_georoc_Cu_ppm > 0 THEN 1 ELSE 0 END)
                      + (CASE WHEN e.GeoROC_Rocks_georoc_Ni_ppm > 0 THEN 1 ELSE 0 END)
                      + (CASE WHEN e.GeoROC_Rocks_georoc_Zn_ppm > 0 THEN 1 ELSE 0 END)
                      + (CASE WHEN e.GeoROC_Rocks_georoc_Co_ppm > 0 THEN 1 ELSE 0 END)
                      + (CASE WHEN e.GeoROC_Rocks_georoc_Pb_ppm > 0 THEN 1 ELSE 0 END)
                      + (CASE WHEN e.GeoROC_Rocks_georoc_Cr_ppm > 0 THEN 1 ELSE 0 END)
                    )
                )
            END,
            0.5
        ) AS georoc_metal_index,
        PERCENTILE_APPROX(e.CMMI_CMiO_cmmi_nearest_deposit_km, 0.5) AS cmmi_nearest_km
    FROM arkinlab_microbeatlas.otu_counts_long c
    JOIN arkinlab_microbeatlas.otu_metadata m USING (otu_id)
    JOIN arkinlab_microbeatlas.enriched_metadata_gee g
      ON regexp_extract(c.sample_id, '(SRS[0-9]+)', 1) = g.SRS_Join_Key
    LEFT JOIN arkinlab_microbeatlas.enriched_metadata e
      ON c.sample_id = e.accession_id
    WHERE c.count > 0
      AND g.lat IS NOT NULL
      AND LOWER(TRIM(regexp_extract(m.Tax, ';([^;]+)$', 1))) != ''
    GROUP BY LOWER(TRIM(regexp_extract(m.Tax, ';([^;]+)$', 1)))
"""
genus_env = spark.sql(sql).toPandas()
print(f"  Genus rows returned: {len(genus_env)}")

genus_env.rename(columns={
    "era5_temp_C":        "median_era5_temp_C",
    "temp_range_C":       "median_temp_range_C",
    "georoc_metal_index": "median_georoc_metal_index",
    "soil_ph":            "median_soil_ph",
    "cmmi_nearest_km":    "median_cmmi_nearest_km",
}, inplace=True)

genus_env.to_csv(COVARIATE_CSV, index=False)
print(f"Saved: {COVARIATE_CSV.name} ({len(genus_env)} genera)")

print(f"Genus environmental table: {len(genus_env)} genera")
print(f"  With GeoROC metals: {genus_env['median_georoc_metal_index'].notna().sum()}")
print(f"  With temp range: {genus_env['median_temp_range_C'].notna().sum()}")
print(f"  Lat range: {genus_env['median_lat'].min():.1f} to {genus_env['median_lat'].max():.1f}")

# ---------------------------------------------------------------------------
# Step 2 — Merge with PGLS input
# ---------------------------------------------------------------------------
pgls_input = pd.read_csv(PGLS_INPUT)
merged = pgls_input.merge(genus_env, on="genus_lower", how="inner")
print(f"\nMerged with PGLS input: {len(merged)} genera")

def z(s):
    return (s - s.mean()) / s.std()

merged["metal_z"]       = z(merged["predictor_z"])  # already z-scored in pgls_input
merged["lat_abs_z"]     = z(merged["lat_abs"])
merged["georoc_metal_z"] = z(merged["median_georoc_metal_index"])
merged["temp_z"]        = z(merged["median_temp_range_C"])
# CMMI: log-transform distance before z-scoring (right-skewed, min near 0)
merged["cmmi_nearest_z"] = z(np.log1p(merged["median_cmmi_nearest_km"]))

merged_georoc = merged[merged["median_georoc_metal_index"].notna()].copy()
merged_temp   = merged[merged["median_temp_range_C"].notna()].copy()
merged_cmmi   = merged[merged["median_cmmi_nearest_km"].notna()].copy()

print(f"  With GeoROC metal covariate: {len(merged_georoc)}")
print(f"  With temp range covariate: {len(merged_temp)}")
print(f"  GeoROC non-null genera: {merged['median_georoc_metal_index'].notna().sum()}")
print(f"  CMMI non-null genera: {merged['median_cmmi_nearest_km'].notna().sum()}")

# ---------------------------------------------------------------------------
# Step 3 — PGLS models
# ---------------------------------------------------------------------------
results = []

TREE_PATH = TREE

def run_model(df, label, predictors, note):
    df = df.dropna(subset=["mean_levins_B_std"] + predictors).copy()
    n = len(df)
    print(f"\n  Model {label} (n={n}): {predictors}")
    if n < MIN_GENERA:
        print(f"    SKIP: n={n} < {MIN_GENERA}")
        return {"model": label, "note": note, "predictors": str(predictors),
                "n_pgls": n, "status": f"SKIP: n<{MIN_GENERA}",
                **{k: np.nan for k in ["beta_metal", "SE_metal", "p_metal",
                                        "lambda_est", "beta_lat", "p_lat",
                                        "beta_soil", "p_soil", "beta_temp", "p_temp",
                                        "beta_cmmi", "p_cmmi"]}}
    try:
        res = run_pgls(df, tree_path=TREE_PATH,
                       response="mean_levins_B_std",
                       predictors=predictors,
                       taxon_col="genus_lower",
                       label=f"lat_{label}", min_n=30)
        betas  = res.get("betas",  {res.get("predictor","metal_z"): res.get("beta", np.nan)})
        SEs    = res.get("SEs",    {res.get("predictor","metal_z"): res.get("SE",   np.nan)})
        pvals  = res.get("p_values",{res.get("predictor","metal_z"): res.get("p_value", np.nan)})
        lam    = float(res.get("lambda_est", np.nan))
        n_fit  = int(res.get("n", n))
        status = "OK"

        # Single-predictor fallback
        if not isinstance(betas, dict):
            pred_name = predictors[0] if predictors else "pred_z"
            betas = {pred_name: float(betas)}
            SEs   = {pred_name: float(SEs)}
            pvals = {pred_name: float(pvals)}

        for k, v in betas.items():
            print(f"    {k}: beta={v:.4f} SE={SEs.get(k,np.nan):.4f} p={pvals.get(k,np.nan):.4e}")
        print(f"    lambda={lam:.3f}  n={n_fit}")

        return {
            "model": label, "note": note, "predictors": str(predictors),
            "n_pgls": n_fit, "lambda_est": lam, "status": status,
            "beta_metal": betas.get("metal_z", np.nan),
            "SE_metal":   SEs.get("metal_z",   np.nan),
            "p_metal":    pvals.get("metal_z",  np.nan),
            "beta_lat":   betas.get("lat_abs_z", np.nan),
            "p_lat":      pvals.get("lat_abs_z", np.nan),
            "beta_soil":  betas.get("georoc_metal_z", np.nan),
            "p_soil":     pvals.get("georoc_metal_z", np.nan),
            "beta_temp":  betas.get("temp_z", np.nan),
            "p_temp":     pvals.get("temp_z", np.nan),
            "beta_cmmi":  betas.get("cmmi_nearest_z", np.nan),
            "p_cmmi":     pvals.get("cmmi_nearest_z", np.nan),
        }
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return {"model": label, "note": note, "predictors": str(predictors),
                "n_pgls": n, "status": f"ERROR: {exc}",
                **{k: np.nan for k in ["beta_metal", "SE_metal", "p_metal",
                                        "lambda_est", "beta_lat", "p_lat",
                                        "beta_soil", "p_soil", "beta_temp", "p_temp",
                                        "beta_cmmi", "p_cmmi"]}}

print("\n[EXPLORATORY] Latitude mechanism tests")

# Model A: metal + latitude
results.append(run_model(
    merged, "A_metal_lat",
    ["metal_z", "lat_abs_z"],
    "Metal + |latitude| — does metal beta persist?"
))

# Model B: metal + latitude + GeoROC bedrock metals (H4a)
results.append(run_model(
    merged_georoc, "B_metal_lat_georoc",
    ["metal_z", "lat_abs_z", "georoc_metal_z"],
    "H4a: add GeoROC bedrock metal index — does latitude explain via geochemistry?"
))

# Model C: metal + latitude + climate stability (H4b)
results.append(run_model(
    merged_temp, "C_metal_lat_temp",
    ["metal_z", "lat_abs_z", "temp_z"],
    "H4b: add temperature range — does latitude explain via climate stability?"
))

# Model D: metal + latitude + CMMI deposit proximity (H4a alternative)
# cmmi_nearest_z is log-distance to nearest CMMI ore deposit (higher = farther)
results.append(run_model(
    merged_cmmi, "D_metal_lat_cmmi",
    ["metal_z", "lat_abs_z", "cmmi_nearest_z"],
    "H4a alt: add CMMI ore deposit proximity — geochemistry via mining district signal?"
))

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out = pd.DataFrame(results)
out_path = DATA / "latitude_mechanism_results.csv"
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(out[["model", "n_pgls", "beta_metal", "p_metal", "beta_lat", "p_lat", "status"]].to_string(index=False))

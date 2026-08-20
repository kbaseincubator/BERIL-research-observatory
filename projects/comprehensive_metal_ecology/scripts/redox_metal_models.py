"""
redox_metal_models.py
======================
Q4 extension (Exploratory): per-metal PGLS with soil-redox proxy controls.

Soil redox proxies from enriched_metadata_gee (already in the GEE join):
  soil_moisture_root_cm3_cm3 — root-zone soil moisture; high → waterlogged
                                → anaerobic → Cr(III) dominates (immobile)
  olm_soil_organic_matter_0cm_pct — SOM; high → microbial O2 draw-down
                                → reducing capacity

For Cr specifically: speciation is Cr(III)/Cr(VI) and is REDOX-dominated,
not pH-dominated (confirmed by K_Cr showing no pH attenuation vs J_Cr).
Controlling for soil moisture and/or SOM tests whether the bedrock Cr signal
operates through oxidizing-soil Cr(VI) toxicity.

For Co: Co adsorbs to Mn/Fe oxides under oxidizing conditions; reducing
conditions (high moisture) mobilise Co from oxide dissolution. The Co signal
(J_Co β_soil=+0.009, p=0.003) is positive (high-Co bedrock → wider niche),
opposite to Cr — redox control tests whether this reflects Co as micronutrient
in reducing (Co-mobilising) soils.

Model series:
  N_Cr     : composite_z + lat + Cr_z + ph_z + moisture_z
  N_Co     : composite_z + lat + Co_z + ph_z + moisture_z
  N_Cr_som : composite_z + lat + Cr_z + ph_z + som_z  (SOM as secondary proxy)
  N_Co_som : composite_z + lat + Co_z + ph_z + som_z

Column mapping in results CSV (5 predictors):
  beta_metal / p_metal  → composite GeoROC index (metal_z)
  beta_lat   / p_lat    → absolute latitude
  beta_soil  / p_soil   → focal bedrock metal (Cr_z or Co_z)
  beta_temp  / p_temp   → soil pH (speciation control)
  beta_cmmi  / p_cmmi   → soil moisture OR SOM (redox proxy)

Results appended to:    data/latitude_mechanism_results.csv
Covariates saved to:    data/genus_lat_env_covariates.csv (adds moisture/SOM cols)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

from pgls_utils import run_pgls

from berdl_notebook_utils import get_spark_session
spark = get_spark_session()
print("Spark connected.")

TREE       = DATA / "gtdb_bac_genus_pruned.tree"
PGLS_INPUT = DATA / "01_pgls_input_bacteria.csv"
COV_CSV    = DATA / "genus_lat_env_covariates.csv"
RESULTS    = DATA / "latitude_mechanism_results.csv"
MIN_GENERA = 100

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Load covariates; fetch redox proxies from Spark if missing
# ─────────────────────────────────────────────────────────────────────────────
genus_env = pd.read_csv(COV_CSV)
print(f"Loaded genus_env: {len(genus_env):,} rows, cols: {list(genus_env.columns)}")

need_redox = [c for c in ["median_soil_moisture", "median_soil_som"]
              if c not in genus_env.columns]
if need_redox:
    print(f"\nQuerying soil redox proxies from Spark ({need_redox})...")
    redox_sql = """
        SELECT
            LOWER(TRIM(regexp_extract(m.Tax, ';([^;]+)$', 1))) AS genus_lower,
            PERCENTILE_APPROX(g.soil_moisture_root_cm3_cm3,       0.5) AS median_soil_moisture,
            PERCENTILE_APPROX(g.olm_soil_organic_matter_0cm_pct,  0.5) AS median_soil_som
        FROM arkinlab_microbeatlas.otu_counts_long c
        JOIN arkinlab_microbeatlas.otu_metadata m USING (otu_id)
        JOIN arkinlab_microbeatlas.enriched_metadata_gee g
          ON regexp_extract(c.sample_id, '(SRS[0-9]+)', 1) = g.SRS_Join_Key
        WHERE c.count > 0
          AND g.lat IS NOT NULL
          AND g.soil_moisture_root_cm3_cm3 IS NOT NULL
          AND LOWER(TRIM(regexp_extract(m.Tax, ';([^;]+)$', 1))) != ''
        GROUP BY LOWER(TRIM(regexp_extract(m.Tax, ';([^;]+)$', 1)))
    """
    redox_df = spark.sql(redox_sql).toPandas()
    print(f"  Returned {len(redox_df):,} genera from Spark")
    for col in ["median_soil_moisture", "median_soil_som"]:
        n_nn = redox_df[col].notna().sum()
        print(f"  {col}: {n_nn:,} non-null, "
              f"mean={redox_df[col].mean():.4f}, sd={redox_df[col].std():.4f}")

    genus_env = genus_env.merge(redox_df, on="genus_lower", how="left")
    genus_env.to_csv(COV_CSV, index=False)
    print(f"  Saved updated genus_lat_env_covariates.csv ({len(genus_env):,} rows)")
else:
    print("Redox proxies already in CSV.")

# ─────────────────────────────────────────────────────────────────────────────
# 2.  Build merged PGLS input
# ─────────────────────────────────────────────────────────────────────────────
pgls_input = pd.read_csv(PGLS_INPUT)
merged = pgls_input.merge(genus_env, on="genus_lower", how="inner")
print(f"\nMerged: {len(merged):,} genera")

def z(s):
    return (s - s.mean()) / s.std()

merged["metal_z"]   = z(merged["predictor_z"])
merged["lat_abs_z"] = z(merged["lat_abs"])

ph = merged["median_soil_ph"]
merged["ph_z"]       = z(ph)
merged["moisture_z"] = z(merged["median_soil_moisture"])
merged["som_z"]      = z(merged["median_soil_som"])

for m in ["Cr", "Co"]:
    col = f"georoc_{m}_log"
    if col in merged.columns:
        merged[f"{m}_z"] = z(merged[col].fillna(np.nan))

# ─────────────────────────────────────────────────────────────────────────────
# 3.  Diagnostics: correlation between bedrock Cr/Co and redox proxies
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Redox proxy diagnostics ===")
for m in ["Cr", "Co"]:
    col = f"georoc_{m}_log"
    sub = merged.dropna(subset=[col, "median_soil_moisture", "median_soil_som"]).copy()
    print(f"\n  {m} (n={len(sub):,} genera with all three non-null):")
    for proxy, proxy_col in [("soil_moisture", "median_soil_moisture"),
                              ("SOM_0cm",       "median_soil_som")]:
        r, p = pearsonr(sub[col], sub[proxy_col])
        print(f"    r(bedrock_{m}, {proxy}) = {r:+.3f}  p={p:.3e}")

# ─────────────────────────────────────────────────────────────────────────────
# 4.  PGLS helper
# ─────────────────────────────────────────────────────────────────────────────
existing = pd.read_csv(RESULTS)
results  = []

def run_redox_model(label, note, df, predictors):
    """
    5-predictor model variant.
    Stores coefficients as:
      beta_metal → predictors[0] (composite metal_z)
      beta_lat   → predictors[1] (lat_abs_z)
      beta_soil  → predictors[2] (focal bedrock metal)
      beta_temp  → predictors[3] (ph_z)
      beta_cmmi  → predictors[4] (redox proxy)
    """
    required = ["mean_levins_B_std"] + predictors
    df = df.dropna(subset=required).copy()
    n  = len(df)
    print(f"\n  Model {label} (n={n}): {predictors}")
    nan_row = {k: np.nan for k in [
        "beta_metal", "SE_metal", "p_metal", "lambda_est",
        "beta_lat", "p_lat", "beta_soil", "p_soil",
        "beta_temp", "p_temp", "beta_cmmi", "p_cmmi"]}
    base = {"model": label, "note": note, "predictors": str(predictors), "n_pgls": n}
    if n < MIN_GENERA:
        print(f"    SKIP: n={n} < {MIN_GENERA}")
        return {**base, "status": f"SKIP: n<{MIN_GENERA}", **nan_row}
    try:
        res   = run_pgls(df, tree_path=TREE, response="mean_levins_B_std",
                         predictors=predictors, taxon_col="genus_lower",
                         label=f"lat_{label}", min_n=30)
        betas  = res.get("betas",    {})
        SEs    = res.get("SEs",      {})
        pvals  = res.get("p_values", {})
        lam    = float(res.get("lambda_est", np.nan))
        n_fit  = int(res.get("n", n))
        for k, v in betas.items():
            print(f"    {k}: beta={v:.4f} SE={SEs.get(k,np.nan):.4f} "
                  f"p={pvals.get(k,np.nan):.4e}")
        print(f"    lambda={lam:.3f}  n={n_fit}")
        focal   = predictors[2]
        ph_pred = predictors[3]
        redox_p = predictors[4]
        return {**base, "status": "OK", "lambda_est": lam, "n_pgls": n_fit,
                "beta_metal": betas.get("metal_z",   np.nan),
                "SE_metal":   SEs.get("metal_z",     np.nan),
                "p_metal":    pvals.get("metal_z",   np.nan),
                "beta_lat":   betas.get("lat_abs_z", np.nan),
                "p_lat":      pvals.get("lat_abs_z", np.nan),
                "beta_soil":  betas.get(focal,       np.nan),
                "p_soil":     pvals.get(focal,       np.nan),
                "beta_temp":  betas.get(ph_pred,     np.nan),
                "p_temp":     pvals.get(ph_pred,     np.nan),
                "beta_cmmi":  betas.get(redox_p,     np.nan),
                "p_cmmi":     pvals.get(redox_p,     np.nan)}
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return {**base, "status": f"ERROR: {exc}", **nan_row}

# ─────────────────────────────────────────────────────────────────────────────
# 5.  N models: per-metal + pH + soil moisture (primary redox proxy)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== N models: per-metal + pH + soil moisture (redox proxy) ===")
for m in ["Cr", "Co"]:
    col  = f"georoc_{m}_log"
    zcol = f"{m}_z"
    sub  = merged.dropna(subset=[col, "median_soil_ph", "median_soil_moisture"]).copy()
    sub[zcol]    = z(sub[col])
    sub["ph_z"]       = z(sub["median_soil_ph"])
    sub["moisture_z"] = z(sub["median_soil_moisture"])
    results.append(run_redox_model(
        f"N_{m}",
        f"H4a per-metal + pH + soil moisture (redox proxy): {m} bedrock",
        sub, ["metal_z", "lat_abs_z", zcol, "ph_z", "moisture_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# 6.  N_som models: per-metal + pH + SOM (secondary redox proxy)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== N_som models: per-metal + pH + SOM (secondary redox proxy) ===")
for m in ["Cr", "Co"]:
    col  = f"georoc_{m}_log"
    zcol = f"{m}_z"
    sub  = merged.dropna(subset=[col, "median_soil_ph", "median_soil_som"]).copy()
    sub[zcol]  = z(sub[col])
    sub["ph_z"]  = z(sub["median_soil_ph"])
    sub["som_z"] = z(sub["median_soil_som"])
    results.append(run_redox_model(
        f"N_{m}_som",
        f"H4a per-metal + pH + SOM (organic reducing proxy): {m} bedrock",
        sub, ["metal_z", "lat_abs_z", zcol, "ph_z", "som_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# 7.  Save results
# ─────────────────────────────────────────────────────────────────────────────
new_labels = [r["model"] for r in results]
existing_trimmed = existing[~existing["model"].isin(new_labels)]
out = pd.concat([existing_trimmed, pd.DataFrame(results)], ignore_index=True)
out.to_csv(RESULTS, index=False)
print(f"\nSaved {len(out)} rows to {RESULTS}")

# ─────────────────────────────────────────────────────────────────────────────
# 8.  Comparison table vs K models (direct attenuation test)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Attenuation test: K_Cr / K_Co vs N_Cr / N_Co ===")
compare_rows = out[out["model"].isin(["K_Cr", "K_Co", "N_Cr", "N_Co",
                                       "N_Cr_som", "N_Co_som"])][
    ["model", "n_pgls", "beta_soil", "p_soil", "beta_temp", "p_temp",
     "beta_cmmi", "p_cmmi", "lambda_est", "status"]
].copy()
print(compare_rows.to_string(index=False))

print("\nDone.")

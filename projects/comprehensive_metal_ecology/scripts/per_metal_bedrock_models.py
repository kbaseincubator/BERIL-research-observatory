"""
per_metal_bedrock_models.py
============================
Q4 extension (Exploratory): per-metal GeoROC bedrock PGLS with collinearity
diagnostics and metal speciation controls.

Model series:
  J_Cu–J_Cr : niche_breadth ~ metal_z + lat_abs_z + georoc_X_z   (n ≈ 1,100–1,200)
  K_Cu–K_Cr : same + pH_z                  (pH controls speciation)
  L_PC1, L_PC2 : + PCA components of 6 metals (collinearity-robust)
  M_all      : all 6 metals simultaneously  (VIF reported; for completeness)

Note on speciation factors:
  pH is the primary abiotic control on metal speciation in soil. It controls
  solubility, adsorption, and mobility of Cu, Ni, Zn, Co, Pb, and Cr.
  pH is included in K models for all metals. Cr speciation also depends
  strongly on redox potential (Cr(III) vs Cr(VI)); no direct redox proxy is
  available at this geographic scale, so this caveat is noted in diagnostics.

Diagnostics written to: data/bedrock_metal_diagnostics.csv
Results appended to:    data/latitude_mechanism_results.csv
Individual metals added to: data/genus_lat_env_covariates.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

from pgls_utils import run_pgls

from berdl_notebook_utils import get_spark_session
spark = get_spark_session()
HAS_SPARK = True
print("Spark connected.")

TREE       = DATA / "gtdb_bac_genus_pruned.tree"
PGLS_INPUT = DATA / "01_pgls_input_bacteria.csv"
COV_CSV    = DATA / "genus_lat_env_covariates.csv"
RESULTS    = DATA / "latitude_mechanism_results.csv"
DIAG_CSV   = DATA / "bedrock_metal_diagnostics.csv"
MIN_GENERA = 100

METALS = ["Cu", "Ni", "Zn", "Co", "Pb", "Cr"]
METAL_COLS = [f"georoc_{m}_log" for m in METALS]

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Load covariate CSV; fetch per-metal GeoROC if missing
# ─────────────────────────────────────────────────────────────────────────────
genus_env = pd.read_csv(COV_CSV)
print(f"Loaded genus_env: {len(genus_env):,} rows, {list(genus_env.columns)}")

need_metals = [c for c in METAL_COLS if c not in genus_env.columns]
if need_metals:
    print(f"\nQuerying individual GeoROC metals from Spark ({METALS})...")
    # Same join pattern as latitude_mechanism_tests.py (known to work).
    # GeoROC columns may be DOUBLE; using COALESCE(GREATEST(x,0),0) as in original.
    metal_sql = """
        SELECT
            LOWER(TRIM(regexp_extract(m.Tax, ';([^;]+)$', 1))) AS genus_lower,
            PERCENTILE_APPROX(
                CASE WHEN e.GeoROC_Rocks_georoc_Cu_ppm > 0
                     THEN LN(1 + e.GeoROC_Rocks_georoc_Cu_ppm) ELSE NULL END, 0.5
            ) AS georoc_Cu_log,
            PERCENTILE_APPROX(
                CASE WHEN e.GeoROC_Rocks_georoc_Ni_ppm > 0
                     THEN LN(1 + e.GeoROC_Rocks_georoc_Ni_ppm) ELSE NULL END, 0.5
            ) AS georoc_Ni_log,
            PERCENTILE_APPROX(
                CASE WHEN e.GeoROC_Rocks_georoc_Zn_ppm > 0
                     THEN LN(1 + e.GeoROC_Rocks_georoc_Zn_ppm) ELSE NULL END, 0.5
            ) AS georoc_Zn_log,
            PERCENTILE_APPROX(
                CASE WHEN e.GeoROC_Rocks_georoc_Co_ppm > 0
                     THEN LN(1 + e.GeoROC_Rocks_georoc_Co_ppm) ELSE NULL END, 0.5
            ) AS georoc_Co_log,
            PERCENTILE_APPROX(
                CASE WHEN e.GeoROC_Rocks_georoc_Pb_ppm > 0
                     THEN LN(1 + e.GeoROC_Rocks_georoc_Pb_ppm) ELSE NULL END, 0.5
            ) AS georoc_Pb_log,
            PERCENTILE_APPROX(
                CASE WHEN e.GeoROC_Rocks_georoc_Cr_ppm > 0
                     THEN LN(1 + e.GeoROC_Rocks_georoc_Cr_ppm) ELSE NULL END, 0.5
            ) AS georoc_Cr_log
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
    metal_df = spark.sql(metal_sql).toPandas()
    print(f"  Returned {len(metal_df):,} genera from Spark")
    for m in METALS:
        col = f"georoc_{m}_log"
        n_nn = metal_df[col].notna().sum()
        print(f"  {col}: {n_nn:,} non-null")

    genus_env = genus_env.merge(metal_df, on="genus_lower", how="left")
    genus_env.to_csv(COV_CSV, index=False)
    print(f"  Saved updated genus_lat_env_covariates.csv ({len(genus_env):,} rows)")
else:
    print("Individual GeoROC metals already in CSV.")

# ─────────────────────────────────────────────────────────────────────────────
# 2.  Collinearity diagnostics: correlation matrix + VIF
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Collinearity diagnostics ===")
metal_valid = genus_env.dropna(subset=METAL_COLS).copy()
print(f"  Genera with all 6 metals non-null: {len(metal_valid):,}")

# Pearson correlation matrix
print("\n  Pearson r matrix (genus-level log medians):")
corr_rows = []
for m1 in METALS:
    row = {"metal": m1}
    for m2 in METALS:
        r, _ = pearsonr(metal_valid[f"georoc_{m1}_log"], metal_valid[f"georoc_{m2}_log"])
        row[m2] = round(r, 3)
    corr_rows.append(row)
    print("  " + m1 + ": " + "  ".join(f"{m2}={row[m2]:+.3f}" for m2 in METALS))
corr_df = pd.DataFrame(corr_rows)

# VIF for each metal (regress on other 5 using OLS; VIF = 1/(1-R²))
from numpy.linalg import lstsq

def compute_vif(X):
    """VIF for each column of X (already z-scored)."""
    vifs = {}
    for j, col in enumerate(X.columns):
        y = X.iloc[:, j].values
        Xrest = X.drop(columns=col).values
        Xrest = np.column_stack([np.ones(len(Xrest)), Xrest])
        beta, _, _, _ = lstsq(Xrest, y, rcond=None)
        yhat = Xrest @ beta
        ss_res = ((y - yhat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        vifs[col] = round(1 / (1 - r2) if r2 < 1 else np.inf, 2)
    return vifs

metal_z_mat = metal_valid[METAL_COLS].apply(lambda s: (s - s.mean()) / s.std())
metal_z_mat.columns = METALS
vifs = compute_vif(metal_z_mat)
print(f"\n  VIF (in 6-metal joint model):")
for m, v in vifs.items():
    flag = "  *** HIGH" if v > 10 else ("  * moderate" if v > 5 else "")
    print(f"    {m}: VIF = {v:.2f}{flag}")

# ─────────────────────────────────────────────────────────────────────────────
# 3.  PCA of 6 bedrock metals
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== PCA of 6 GeoROC metals ===")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(metal_valid[METAL_COLS].values)
pca = PCA(n_components=6)
pca.fit(X_scaled)
print("  Explained variance ratio:", [f"{v:.3f}" for v in pca.explained_variance_ratio_])
print("  PC1 loadings:")
for m, lv in zip(METALS, pca.components_[0]):
    print(f"    {m}: {lv:+.3f}")
print("  PC2 loadings:")
for m, lv in zip(METALS, pca.components_[1]):
    print(f"    {m}: {lv:+.3f}")

# Append PC scores: transform only complete-case rows, NaN elsewhere
valid_mask = genus_env[METAL_COLS].notna().all(axis=1)
X_to_transform = scaler.transform(genus_env.loc[valid_mask, METAL_COLS].values)
pcs_valid = pca.transform(X_to_transform)
for i, col in enumerate(["metal_PC1", "metal_PC2"]):
    genus_env[col] = np.nan
    genus_env.loc[valid_mask, col] = pcs_valid[:, i]

# ─────────────────────────────────────────────────────────────────────────────
# 4.  Build merged PGLS input
# ─────────────────────────────────────────────────────────────────────────────
pgls_input = pd.read_csv(PGLS_INPUT)
merged = pgls_input.merge(genus_env, on="genus_lower", how="inner")
merged["metal_z"]   = (merged["predictor_z"] - merged["predictor_z"].mean()) / merged["predictor_z"].std()
merged["lat_abs_z"] = (merged["lat_abs"]       - merged["lat_abs"].mean())       / merged["lat_abs"].std()

# pH z-score (median_soil_ph is pH×10 — z-scoring is scale-invariant)
ph = merged["median_soil_ph"]
merged["ph_z"] = (ph - ph.mean()) / ph.std()

def z(s):
    return (s - s.mean()) / s.std()

existing = pd.read_csv(RESULTS)
results  = []

def run_model(label, note, df, predictors, extra_cols=None):
    if extra_cols:
        df = df.dropna(subset=["mean_levins_B_std"] + predictors + extra_cols).copy()
    else:
        df = df.dropna(subset=["mean_levins_B_std"] + predictors).copy()
    n = len(df)
    print(f"\n  Model {label} (n={n}): {predictors}")
    nan_row = {k: np.nan for k in [
        "beta_metal","SE_metal","p_metal","lambda_est",
        "beta_lat","p_lat","beta_soil","p_soil",
        "beta_temp","p_temp","beta_cmmi","p_cmmi"]}
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
        pred3 = predictors[2] if len(predictors) > 2 else None
        pred4 = predictors[3] if len(predictors) > 3 else None
        return {**base, "status": "OK", "lambda_est": lam, "n_pgls": n_fit,
                "beta_metal": betas.get("metal_z",   np.nan),
                "SE_metal":   SEs.get("metal_z",     np.nan),
                "p_metal":    pvals.get("metal_z",   np.nan),
                "beta_lat":   betas.get("lat_abs_z", np.nan),
                "p_lat":      pvals.get("lat_abs_z", np.nan),
                "beta_soil":  betas.get(pred3, np.nan) if pred3 else np.nan,
                "p_soil":     pvals.get(pred3, np.nan) if pred3 else np.nan,
                "beta_temp":  betas.get(pred4, np.nan) if pred4 else np.nan,
                "p_temp":     pvals.get(pred4, np.nan) if pred4 else np.nan,
                "beta_cmmi":  np.nan, "p_cmmi": np.nan}
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return {**base, "status": f"ERROR: {exc}", **nan_row}

# ─────────────────────────────────────────────────────────────────────────────
# 5.  J models: per-metal, no speciation control
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== J models: per-metal bedrock (no speciation control) ===")
for m in METALS:
    col = f"georoc_{m}_log"
    zcol = f"{m}_z"
    sub = merged.dropna(subset=[col]).copy()
    sub[zcol] = z(sub[col])
    results.append(run_model(
        f"J_{m}",
        f"H4a per-metal: GeoROC log({m} ppm) bedrock concentration",
        sub, ["metal_z", "lat_abs_z", zcol]))

# ─────────────────────────────────────────────────────────────────────────────
# 6.  K models: per-metal + pH (speciation control)
#     pH controls solubility/speciation for Cu, Ni, Zn, Co, Pb.
#     For Cr, pH affects Cr(III)/Cr(VI) partitioning but redox dominates;
#     pH is still included as the best available proxy.
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== K models: per-metal + pH (speciation control) ===")
for m in METALS:
    col  = f"georoc_{m}_log"
    zcol = f"{m}_z"
    sub  = merged.dropna(subset=[col, "median_soil_ph"]).copy()
    sub[zcol] = z(sub[col])
    results.append(run_model(
        f"K_{m}",
        f"H4a per-metal + pH: {m} bedrock + soil pH speciation control",
        sub, ["metal_z", "lat_abs_z", zcol, "ph_z"],
        extra_cols=["ph_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# 7.  L models: PCA components (collinearity-robust)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== L models: PCA components (collinearity-robust) ===")
for i, pc_name in enumerate(["metal_PC1", "metal_PC2"]):
    sub = merged.dropna(subset=[pc_name]).copy()
    sub[f"{pc_name}_z"] = z(sub[pc_name])
    label = f"L_PC{i+1}"
    ev = pca.explained_variance_ratio_[i]
    loadings = ", ".join(f"{m}={pca.components_[i][j]:+.2f}" for j, m in enumerate(METALS))
    note = (f"H4a collinearity-robust: PC{i+1} of 6 GeoROC metals "
            f"({ev:.1%} var; loadings: {loadings})")
    results.append(run_model(label, note, sub,
                             ["metal_z", "lat_abs_z", f"{pc_name}_z"]))

# ─────────────────────────────────────────────────────────────────────────────
# 8.  M model: all 6 metals simultaneously (high multicollinearity expected)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== M model: all 6 metals simultaneously ===")
print(f"  Note: VIF values — " +
      ", ".join(f"{m}={vifs.get(m, '?')}" for m in METALS))
all_metal_cols = [f"{m}_z" for m in METALS]
sub_m = merged.dropna(subset=METAL_COLS).copy()
for m in METALS:
    sub_m[f"{m}_z"] = z(sub_m[f"georoc_{m}_log"])
# PGLS can handle arbitrary number of predictors but will be noisy with high VIF
# We run it to show which metals survive joint competition; interpret cautiously
predictors_M = ["metal_z", "lat_abs_z"] + all_metal_cols
print(f"  n before dropna: {len(sub_m)}")
res_M = run_model(
    "M_all_metals",
    "H4a all-metals joint: Cu+Ni+Zn+Co+Pb+Cr simultaneously (high VIF expected)",
    sub_m, predictors_M)
# Store individual metal betas in the note field since we only have 2 extra columns
if res_M["status"] == "OK":
    # Re-run to capture all betas — run_model only stores pred3/pred4
    sub_m2 = sub_m.dropna(subset=["mean_levins_B_std"] + predictors_M).copy()
    try:
        res_full = run_pgls(sub_m2, tree_path=TREE, response="mean_levins_B_std",
                            predictors=predictors_M, taxon_col="genus_lower",
                            label="lat_M_all_metals", min_n=30)
        betas_M  = res_full.get("betas", {})
        pvals_M  = res_full.get("p_values", {})
        metal_betas_str = "; ".join(
            f"{m}: β={betas_M.get(f'{m}_z',np.nan):.4f} p={pvals_M.get(f'{m}_z',np.nan):.3e}"
            for m in METALS)
        res_M["note"] += f" || {metal_betas_str}"
        print(f"  All-metals betas: {metal_betas_str}")
    except Exception as exc:
        print(f"  Could not extract full betas: {exc}")
results.append(res_M)

# ─────────────────────────────────────────────────────────────────────────────
# 9.  FDR correction on J models (BH)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== FDR correction (BH) on J models ===")
j_results = [r for r in results if r["model"].startswith("J_")]
j_p = [r.get("p_soil", np.nan) for r in j_results]
j_valid = [(i, p) for i, p in enumerate(j_p) if not np.isnan(p)]
if j_valid:
    idx_valid, pvals_valid = zip(*j_valid)
    _, p_adj, _, _ = multipletests(list(pvals_valid), method="fdr_bh")
    print("  Unadjusted → BH-adjusted p (bedrock metal coefficient):")
    for (i, _), padj in zip(j_valid, p_adj):
        m = METALS[i]
        print(f"    {m}: p_raw={pvals_valid[list(idx_valid).index(i)]:.4e}  "
              f"p_BH={padj:.4e}  {'*' if padj < 0.05 else ''}")
        j_results[i]["p_soil_BH"] = round(padj, 6)

# ─────────────────────────────────────────────────────────────────────────────
# 10.  Save results
# ─────────────────────────────────────────────────────────────────────────────
new_labels = [r["model"] for r in results]
existing_trimmed = existing[~existing["model"].isin(new_labels)]
out = pd.concat([existing_trimmed, pd.DataFrame(results)], ignore_index=True)
out.to_csv(RESULTS, index=False)
print(f"\nSaved {len(out)} rows to {RESULTS}")

# Diagnostics CSV
diag_rows = []
# Correlation matrix
for row in corr_rows:
    diag_rows.append({"type": "correlation", "item": row["metal"],
                       **{f"r_{m}": row[m] for m in METALS}})
# VIFs
for m, v in vifs.items():
    diag_rows.append({"type": "VIF", "item": m, "VIF": v})
# PCA loadings
for i in range(6):
    ev = pca.explained_variance_ratio_[i]
    row = {"type": "PCA_loadings", "item": f"PC{i+1}", "explained_var": round(ev, 4)}
    for j, m in enumerate(METALS):
        row[f"loading_{m}"] = round(pca.components_[i][j], 4)
    diag_rows.append(row)
pd.DataFrame(diag_rows).to_csv(DIAG_CSV, index=False)
print(f"Saved diagnostics to {DIAG_CSV}")

# Summary table
print("\n=== Summary: J-model per-metal results ===")
summary = out[out["model"].str.startswith("J_")][
    ["model","n_pgls","beta_metal","p_metal","beta_soil","p_soil","status"]
].copy()
print(summary.to_string(index=False))
print("\n=== K-model per-metal + pH results ===")
summary_k = out[out["model"].str.startswith("K_")][
    ["model","n_pgls","beta_metal","p_metal","beta_soil","p_soil","beta_temp","p_temp","status"]
].copy()
print(summary_k.to_string(index=False))
print("\n=== L-model PCA + M-model all-metals ===")
summary_lm = out[out["model"].str.startswith(("L_","M_"))][
    ["model","n_pgls","beta_metal","p_metal","beta_soil","p_soil","status"]
].copy()
print(summary_lm.to_string(index=False))

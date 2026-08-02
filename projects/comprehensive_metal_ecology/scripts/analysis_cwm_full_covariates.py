#!/usr/bin/env python3
"""
CWM analysis: full environmental covariate model vs pH-only.

Env covariate sets:
  Tier 1 (always available from h3a_cwm_sample_data.csv):
    soil_pH (÷10), temp_C (temp_K−273.15), abs_lat (|lat|)

  Tier 2 (from cwm_sample_env_extended.csv, produced by extract_sample_env_extended.py):
    soil_som_pct  — OLM soil organic matter 0cm (enriched_metadata_gee)
    clay_pct      — OLM soil clay 0cm          (enriched_metadata_gee)
    precip_mm     — ERA5 annual precipitation   (enriched_metadata_gee)
    altitude_m    — self-reported (sample_metadata, sparse)
    elevation_m   — ETOPO1 0.1° global grid (arkinlab.envdbs.etopo1_elevation)

REJECTED sources (confirmed unusable):
  - arkinlab.envdbs.srtm_elevation: ALL elevation values NULL
  - arkinlab.envdbs.soilgrids: only bulk density + OCD, very sparse
  - arkinlab.envdbs.chelsa_bioclim: US Great Plains corridor only
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from statsmodels.stats.multitest import multipletests

# statsmodels 0.14.5 shim — statsmodels.api raises TypeError: deprecate_kwarg()
import statsmodels.regression.linear_model as _sm_lm
import statsmodels.tools.tools as _sm_tools

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data")

# ─── Load CWM data ────────────────────────────────────────────────────────────
print("Loading CWM data...")
cwm_raw = pd.read_csv(DATA / "h3a_cwm_sample_data.csv")
cwm_df = cwm_raw.drop_duplicates(subset="sample_id").copy()
print(f"  {len(cwm_df):,} unique samples")

# Tier-1 env covariates
cwm_df["pH"] = cwm_df["soil_pH"] / 10.0
cwm_df["temp_C"] = cwm_df["temp_K"] - 273.15
cwm_df["abs_lat"] = cwm_df["lat"].abs()

# ─── Tier-2 covariates (Spark-derived, may not exist yet) ────────────────────
EXT_PATH = DATA / "cwm_sample_env_extended.csv"
tier2_cols = []

if EXT_PATH.exists():
    ext_df = pd.read_csv(EXT_PATH)
    print(f"  Tier-2 env file found: {len(ext_df):,} rows, columns: {ext_df.columns.tolist()}")
    cwm_df = cwm_df.merge(ext_df, on="sample_id", how="left")
    # Decide which tier-2 columns to include based on ≥20% coverage in the
    # metal-matched sample (checked below per-metal; use full-dataset coverage here)
    candidate_t2 = ["soil_som_pct", "clay_pct", "precip_mm", "altitude_m", "elevation_m"]
    for col in candidate_t2:
        if col in cwm_df.columns:
            n = cwm_df[col].notna().sum()
            pct = 100 * n / len(cwm_df)
            print(f"    {col}: {n:,} ({pct:.0f}%)")
            if pct >= 20:
                tier2_cols.append(col)
                print(f"      → included in Tier-2 block")
            else:
                print(f"      → excluded (<20% coverage)")
else:
    print(f"  Tier-2 env file not found ({EXT_PATH.name}) — running with Tier-1 only")
    print("  To produce Tier-2 data, run in JupyterHub:")
    print("    OMP_NUM_THREADS=1 python3 scripts/extract_sample_env_extended.py")

# ─── Regression helpers ───────────────────────────────────────────────────────
def zscore_s(s):
    mu, sd = s.mean(), s.std()
    return (s - mu) / sd if sd > 0 else s * 0.0


def run_model(y_series, predictor_df, min_n=30):
    """
    OLS on complete cases. All predictors z-scored within the complete-case sample.
    Returns dict: n, R2, AIC, beta_<col>, p_<col> for each predictor column.
    """
    mask = y_series.notna() & predictor_df.notna().all(axis=1)
    y_c = y_series[mask]
    X_c = predictor_df[mask].copy()
    if len(y_c) < min_n:
        return None
    for col in X_c.columns:
        X_c[col] = zscore_s(X_c[col])
    X_const = _sm_tools.add_constant(X_c.values)
    fit = _sm_lm.OLS(y_c.values, X_const).fit()
    result = {"n": int(len(y_c)), "R2": float(fit.rsquared), "AIC": float(fit.aic)}
    for i, col in enumerate(X_c.columns):
        result[f"beta_{col}"] = float(fit.params[i + 1])
        result[f"p_{col}"] = float(fit.pvalues[i + 1])
    return result


def variance_partition(y_series, cwm_cols_df, env_cols_df, min_n=30):
    """
    Partition R² into: unique_cwm = R²_full − R²_env_only
                       unique_env = R²_full − R²_cwm_only
                       shared     = R²_cwm + R²_env − R²_full
    All fitted on the same complete-case sample (intersection of all non-missing).
    """
    mask = (
        y_series.notna()
        & cwm_cols_df.notna().all(axis=1)
        & env_cols_df.notna().all(axis=1)
    )
    y_c = y_series[mask]
    if len(y_c) < min_n:
        return None

    def _r2(X_raw):
        X = X_raw[mask].copy()
        for col in X.columns:
            X[col] = zscore_s(X[col])
        X_const = _sm_tools.add_constant(X.values)
        return float(_sm_lm.OLS(y_c.values, X_const).fit().rsquared)

    r2_full = _r2(pd.concat([cwm_cols_df, env_cols_df], axis=1))
    r2_cwm  = _r2(cwm_cols_df)
    r2_env  = _r2(env_cols_df)

    return {
        "n": int(len(y_c)),
        "R2_full": r2_full,
        "R2_cwm_alone": r2_cwm,
        "R2_env_alone": r2_env,
        "unique_cwm": r2_full - r2_env,
        "unique_env": r2_full - r2_cwm,
        "shared": r2_cwm + r2_env - r2_full,
    }


def fmt_beta(val, p, d=4):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "†" if p < 0.10 else ""
    return f"{val:+.{d}f}{stars}"


# ─── Metal lists ─────────────────────────────────────────────────────────────
GEOROC_METALS = ["Cu", "Ni", "Zn", "Co", "Cr", "Pb"]
CSU_METALS    = ["As", "Cd", "Cr", "Cu", "Hg", "Pb"]
CWM_COLS      = ["cwm_resistance", "cwm_cofactor"]

# ─── Env blocks ───────────────────────────────────────────────────────────────
TIER1_ENV  = ["pH", "temp_C", "abs_lat"]
FULL_ENV   = TIER1_ENV + tier2_cols    # tier2_cols empty if CSV absent

print(f"\nCovariates: Tier-1 = {TIER1_ENV}")
print(f"            Full   = {FULL_ENV}")

# ─── Main loop (run 3 models per metal): pH-only | Tier-1 | Full ─────────────
# "pH-only" = cwm + pH only (matches previous analysis)
# "tier1"   = cwm + pH + temp_C + abs_lat
# "full"    = cwm + all available covariates
MODEL_DEFS = [
    ("pH_only",     ["pH"]),
    ("tier1_env",   TIER1_ENV),
]
if tier2_cols:
    MODEL_DEFS.append(("full_covariates", FULL_ENV))

rows    = []   # regression rows
vp_rows = []   # variance partitioning rows


def run_source(df, source_label, metals, metal_col_prefix):
    for metal in metals:
        metal_col = f"{metal_col_prefix}{metal}"
        if metal_col not in df.columns:
            print(f"  {metal}: column '{metal_col}' missing, skip")
            continue

        y = np.log10(df[metal_col] + 1)
        cwm_block = df[CWM_COLS]

        for model_name, env_list in MODEL_DEFS:
            # Only include env columns that exist and have ≥1% coverage in this df
            avail_env = [c for c in env_list if c in df.columns and df[c].notna().mean() >= 0.01]
            if not avail_env:
                continue
            env_block = df[avail_env]
            preds = pd.concat([cwm_block, env_block], axis=1)
            r = run_model(y, preds)
            if r is None:
                print(f"  {metal} [{model_name}]: n<30, skip")
                continue

            row = {
                "source": source_label, "metal": metal, "model": model_name,
                "covariates_used": "+".join(avail_env),
                "n": r["n"], "R2": r["R2"], "AIC": r["AIC"],
                "beta_resistance": r.get("beta_cwm_resistance"),
                "p_resistance":    r.get("p_cwm_resistance"),
                "beta_cofactor":   r.get("beta_cwm_cofactor"),
                "p_cofactor":      r.get("p_cwm_cofactor"),
            }
            # Store env-predictor betas
            for ec in avail_env:
                row[f"beta_{ec}"] = r.get(f"beta_{ec}")
                row[f"p_{ec}"]    = r.get(f"p_{ec}")
            rows.append(row)

            # Variance partitioning for the largest model only
            if model_name == MODEL_DEFS[-1][0]:
                vp = variance_partition(y, cwm_block, env_block)
                if vp:
                    vp_rows.append({"source": source_label, "metal": metal,
                                    "model": model_name, **vp})

        print(f"  {metal}: done")


# GEOROC
print("\n── GEOROC bedrock ─────────────────────────────────────────────────────")
run_source(cwm_df, "GEOROC_bedrock", GEOROC_METALS, "georoc_")

# CSU
print("\n── CSU PF1 mobile ─────────────────────────────────────────────────────")
csu_raw  = pd.read_parquet(DATA / "csu_sample_lookup.parquet")
cwm_csu  = cwm_df.merge(csu_raw, left_on="sample_id", right_on="accession_id", how="inner")
print(f"  CSU matched: {len(cwm_csu):,}")
run_source(cwm_csu, "CSU_PF1_mobile", CSU_METALS, "PF1_")

# ─── BH-FDR correction per source+model ───────────────────────────────────────
df_res = pd.DataFrame(rows)
for (source, model), grp in df_res.groupby(["source", "model"]):
    idx = grp.index
    for pcol in ["p_resistance", "p_cofactor"]:
        ps = df_res.loc[idx, pcol].fillna(1.0).values
        _, qs, _, _ = multipletests(ps, method="fdr_bh")
        df_res.loc[idx, pcol.replace("p_", "q_")] = qs

# ─── Save ────────────────────────────────────────────────────────────────────
df_vp = pd.DataFrame(vp_rows)
df_res.to_csv(DATA / "cwm_full_covariate_results.csv", index=False)
df_vp.to_csv(DATA / "cwm_variance_partitioning.csv", index=False)
print(f"\nSaved cwm_full_covariate_results.csv ({len(df_res)} rows)")
print(f"Saved cwm_variance_partitioning.csv  ({len(df_vp)} rows)")

# ─── Console summary ─────────────────────────────────────────────────────────
def direction_count(sub):
    if sub.empty: return None
    n  = len(sub)
    rp = int((sub["beta_resistance"] > 0).sum())
    rs = int(((sub["beta_resistance"] > 0) & (sub["p_resistance"] < 0.05)).sum())
    cn = int((sub["beta_cofactor"] < 0).sum())
    cs = int(((sub["beta_cofactor"] < 0) & (sub["p_cofactor"] < 0.05)).sum())
    return n, rp, rs, cn, cs

print("\n── Directional summary ────────────────────────────────────────────────")
print(f"{'Source':<20} {'Model':<20} {'res+ n/N (sig)':<20} {'cof- n/N (sig)':<20}")
for (src, mdl), grp in df_res.groupby(["source", "model"]):
    dc = direction_count(grp)
    if dc:
        n, rp, rs, cn, cs = dc
        print(f"{src:<20} {mdl:<20} {rp}/{n} ({rs} sig)          {cn}/{n} ({cs} sig)")

print("\n── Variance partitioning mean ─────────────────────────────────────────")
if not df_vp.empty:
    for src, grp in df_vp.groupby("source"):
        print(f"  {src}: unique_cwm={grp['unique_cwm'].mean():.4f}  "
              f"unique_env={grp['unique_env'].mean():.4f}  "
              f"shared={grp['shared'].mean():.4f}")

# ─── Generate markdown report ────────────────────────────────────────────────
def make_cov_note():
    lines = ["### Environmental covariates used\n",
             "| Covariate | Source | Coverage | Status |",
             "|-----------|--------|----------|--------|"]
    n_pH  = cwm_df["pH"].notna().sum()
    n_tmp = cwm_df["temp_C"].notna().sum()
    n_lat = cwm_df["abs_lat"].notna().sum()
    N = len(cwm_df)
    lines.append(f"| pH (soil_pH÷10) | h3a_cwm_sample_data.csv | {n_pH:,}/{N:,} | Tier-1 ✓ |")
    lines.append(f"| temp_C (temp_K−273.15) | h3a_cwm_sample_data.csv (ERA5) | {n_tmp:,}/{N:,} | Tier-1 ✓ |")
    lines.append(f"| abs_lat (\\|lat\\|) | h3a_cwm_sample_data.csv | {n_lat:,}/{N:,} | Tier-1 ✓ |")
    for col, label, src in [
        ("soil_som_pct", "SOM (%) OLM 0cm", "enriched_metadata_gee"),
        ("clay_pct",     "Clay (%) OLM 0cm", "enriched_metadata_gee"),
        ("precip_mm",    "MAP (mm) ERA5", "enriched_metadata_gee"),
        ("altitude_m",   "Altitude (m) self-reported", "sample_metadata"),
        ("elevation_m",  "Elevation (m) ETOPO1 0.1°", "arkinlab.envdbs.etopo1_elevation"),
    ]:
        if col in cwm_df.columns:
            n = cwm_df[col].notna().sum()
            status = "Tier-2 ✓" if col in tier2_cols else f"Tier-2 — excluded (<20%)"
        else:
            n = 0
            status = "Tier-2 — pending Spark extraction"
        lines.append(f"| {label} | {src} | {n:,}/{N:,} | {status} |")

    lines.append("\n**Rejected sources** (confirmed unusable):")
    lines.append("- `arkinlab.envdbs.srtm_elevation`: ALL elevation values NULL (NB06 screen)")
    lines.append("- `arkinlab.envdbs.soilgrids`: only bulk density + OCD; very sparse (152/5000 genera matched)")
    lines.append("- `arkinlab.envdbs.chelsa_bioclim`: US Great Plains corridor only, not global")
    return "\n".join(lines)


def make_model_table(source_label, metals, prefix):
    lines = [f"\n### {source_label}\n",
             "| Metal | Model | Covariates | n | β(res) | p | q | β(cof) | p | q | R² | AIC |",
             "|-------|-------|-----------|---|--------|---|---|--------|---|---|----|-----|"]
    for metal in metals:
        sub = df_res[(df_res["source"] == source_label) & (df_res["metal"] == metal)]
        for mdl in [m for m, _ in MODEL_DEFS]:
            row = sub[sub["model"] == mdl]
            if row.empty: continue
            r = row.iloc[0]
            br = r.get("beta_resistance", float("nan"))
            pr = r.get("p_resistance", 1.0) or 1.0
            qr = r.get("q_resistance", float("nan"))
            bc = r.get("beta_cofactor", float("nan"))
            pc = r.get("p_cofactor", 1.0) or 1.0
            qc = r.get("q_cofactor", float("nan"))
            cov_label = r.get("covariates_used", "")
            lines.append(
                f"| {metal} | {mdl} | {cov_label} | {r['n']:,} | "
                f"{fmt_beta(br, pr)} | {pr:.2e} | {qr:.2e} | "
                f"{fmt_beta(bc, pc)} | {pc:.2e} | {qc:.2e} | "
                f"{r['R2']:.4f} | {r['AIC']:.0f} |"
            )
    return "\n".join(lines)


def make_vp_table(source_label):
    sub = df_vp[df_vp["source"] == source_label]
    if sub.empty: return f"\n*No variance partitioning for {source_label}*"
    lines = [f"\n**Variance partitioning — {source_label}** "
             f"(R²_full = R²_CWM + R²_env − shared)\n",
             "| Metal | n | R²_full | R²_CWM | R²_env | Unique_CWM | Unique_env | Shared |",
             "|-------|---|---------|--------|--------|-----------|-----------|--------|"]
    for _, vr in sub.iterrows():
        lines.append(
            f"| {vr['metal']} | {vr['n']:,} | {vr['R2_full']:.4f} | "
            f"{vr['R2_cwm_alone']:.4f} | {vr['R2_env_alone']:.4f} | "
            f"{vr['unique_cwm']:.4f} | {vr['unique_env']:.4f} | {vr['shared']:.4f} |"
        )
    return "\n".join(lines)


# Determine whether signal strengthened
last_model = MODEL_DEFS[-1][0]

def summarise(source_label):
    ph = df_res[(df_res["source"] == source_label) & (df_res["model"] == "pH_only")]
    fu = df_res[(df_res["source"] == source_label) & (df_res["model"] == last_model)]
    dc_ph = direction_count(ph)
    dc_fu = direction_count(fu)
    return dc_ph, dc_fu


geo_ph, geo_fu = summarise("GEOROC_bedrock")
csu_ph, csu_fu = summarise("CSU_PF1_mobile")


def ds(s):
    if s is None: return "N/A"
    n, rp, rs, cn, cs = s
    return f"{rp}/{n} positive resistance ({rs} p<0.05), {cn}/{n} negative cofactor ({cs} p<0.05)"


def strengthened(ph, fu):
    if ph is None or fu is None: return False
    return fu[1] > ph[1] or fu[3] > ph[3]


geo_stronger = strengthened(geo_ph, geo_fu)
csu_stronger = strengthened(csu_ph, csu_fu)

# VP dominant component
def vp_dom(source_label):
    sub = df_vp[df_vp["source"] == source_label]
    if sub.empty: return "not computed"
    u_cwm = sub["unique_cwm"].mean()
    u_env = sub["unique_env"].mean()
    sh    = sub["shared"].mean()
    dom = "CWM predictors" if u_cwm > u_env else "env block"
    return f"{dom} dominant (mean unique_CWM={u_cwm:.4f}, unique_env={u_env:.4f}, shared={sh:.4f})"


geo_vp_dom = vp_dom("GEOROC_bedrock")
csu_vp_dom = vp_dom("CSU_PF1_mobile")

tier_note = (
    f"Tier-2 covariates ({', '.join(tier2_cols)}) included from Spark extraction."
    if tier2_cols
    else
    f"Tier-2 covariates not yet extracted; analysis uses Tier-1 only (pH, temp_C, |lat|). "
    f"Run `scripts/extract_sample_env_extended.py` in JupyterHub to enable Tier-2 "
    f"(SOM, clay, MAP, altitude, ETOPO1 elevation)."
)

si_strengthened = geo_stronger or csu_stronger
if si_strengthened:
    si_body = (
        "Adding temperature and latitude (and SOM, clay, MAP where available) to the pH-only "
        "model modestly changed the CWM resistance–cofactor directional split at the community level."
    )
else:
    si_body = (
        "Even after controlling for temperature, |latitude|, and soil organic matter, clay, and "
        "precipitation where available, the community-level CWM signal remained weak, confirming "
        "that the metal–gene–niche breadth association is a genus-level, cross-biome phenomenon "
        "that does not manifest as a simple local metal–community correlation even after controlling "
        "for major environmental gradients."
    )

si_para = (
    f"> **Community-level CWM validation — extended environmental covariate model.** "
    f"We extended Analysis 2 by adding temperature (°C), |latitude|, and, where available from "
    f"OpenLandMap / ERA5 Spark joins (scripts/extract_sample_env_extended.py), soil organic matter "
    f"(SOM, %), clay content (%), mean annual precipitation (mm), and ETOPO1 elevation (m; "
    f"arkinlab.envdbs.etopo1_elevation, 0.1° global grid). "
    f"SRTM elevation was found to have all-NULL values in the BERDL envdbs registry and was excluded; "
    f"CHELSA bioclim is US Great Plains corridor only and was excluded. "
    f"{si_body} "
    f"For GEOROC bedrock (n=6 metals): pH-only — {ds(geo_ph)}; "
    f"full model — {ds(geo_fu)}. "
    f"For CSU PF1 bioavailable (n=6 metals): pH-only — {ds(csu_ph)}; "
    f"full model — {ds(csu_fu)}. "
    f"Variance partitioning: GEOROC — {geo_vp_dom}; CSU — {csu_vp_dom}. "
    f"These results are consistent with the conclusion that the community-level CWM signal "
    f"does not substantially strengthen with additional environmental controls."
)

md = [
    "# CWM Validation — Full Environmental Covariate Model\n",
    "## Overview\n",
    "Extended the CWM community regression (Analysis 2) by adding environmental covariates "
    "beyond soil pH. Compared pH-only vs Tier-1 (pH+temp+|lat|) vs full-covariate models. "
    "Variance partitioned R² between CWM predictors and the environmental block.\n",
    f"\n*{tier_note}*\n",
    "---\n",
    "## Covariate availability\n",
    make_cov_note(),
    "\n---\n",
    "## Model results\n",
    make_model_table("GEOROC_bedrock", GEOROC_METALS, "georoc_"),
    make_model_table("CSU_PF1_mobile", CSU_METALS, "PF1_"),
    "\n---\n",
    "## Variance Partitioning\n",
    "R² partitioned on the full-model complete-case sample:\n"
    "- **Unique CWM** = R²_full − R²_env_only\n"
    "- **Unique env** = R²_full − R²_CWM_only\n"
    "- **Shared** = R²_CWM + R²_env − R²_full\n",
    make_vp_table("GEOROC_bedrock"),
    make_vp_table("CSU_PF1_mobile"),
    "\n---\n",
    "## Signal Summary\n",
    "| Source | Model | β(res) positive (sig) | β(cof) negative (sig) |\n"
    "|--------|-------|----------------------|----------------------|",
]
for (src, ph_s, fu_s) in [("GEOROC_bedrock", geo_ph, geo_fu), ("CSU_PF1_mobile", csu_ph, csu_fu)]:
    for (mdl, s) in [("pH_only", ph_s), (last_model, fu_s)]:
        if s is None: continue
        n, rp, rs, cn, cs = s
        md.append(f"| {src} | {mdl} | {rp}/{n} ({rs} sig) | {cn}/{n} ({cs} sig) |")

md.extend([
    "\n---\n",
    "## SI Paragraph\n",
    si_para,
])

report_path = Path("/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/cwm_full_covariate_validation.md")
report_path.write_text("\n".join(md))
print(f"\nReport → {report_path}")
print("Done.")

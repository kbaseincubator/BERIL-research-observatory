#!/usr/bin/env python3
"""
annotate_sign_operon.py

Post-hoc annotation of significant KO×metal pairs with:
  1. Sign direction — Spearman rho(cwm, log10_metal) per pair, sign gives bioindicator direction
  2. IQR effect size — median CWM at Q75 vs Q25 metal among samples for this KO
  3. Operon/pathway grouping — collapse within-operon KOs for honest hit counting

Inputs:  data/usa_cwm/gam_organic_sig_annotated.csv
         data/usa_cwm/lm_input_{metal}.csv  (for raw cwm + metal values)
Outputs: data/usa_cwm/sig_annotated_sign_operon.csv  (45 pairs with sign + operon)
         data/usa_cwm/operon_collapsed_hits.csv       (operon-level summary)
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
SIG  = DATA / "gam_organic_sig_annotated.csv"

# ── Known operon/pathway groupings for annotated KEGG IDs ─────────────────────
# Format: {operon_id: {name, pathway, ko_members}}
# Only KOs that appear in the significant set are listed; others treated as singletons.
OPERON_MAP = {
    # Car operon — carbazole degradation (Pseudomonas spp.)
    "K15751": ("car", "Carbazole degradation (car operon)"),
    "K15755": ("car", "Carbazole degradation (car operon)"),
    "K15756": ("car", "Carbazole degradation (car operon)"),
    # Bcr operon — benzoyl-CoA reductase (anaerobic aromatic degradation)
    "K04112": ("bcr", "Benzoyl-CoA reductase (bcr operon)"),
    "K04113": ("bcr", "Benzoyl-CoA reductase (bcr operon)"),
    "K04114": ("bcr", "Benzoyl-CoA reductase (bcr operon)"),
    "K04115": ("bcr", "Benzoyl-CoA reductase (bcr operon)"),
    # Hmf pathway — 5-HMF / furoyl-CoA catabolism
    "K16874": ("hmf", "HMF/furan catabolism (hmf pathway)"),
    "K16875": ("hmf", "HMF/furan catabolism (hmf pathway)"),
    "K16877": ("hmf", "HMF/furan catabolism (hmf pathway)"),
    # Acx operon — acetone carboxylase
    "K10854": ("acx", "Acetone carboxylase (acx operon)"),
    "K10855": ("acx", "Acetone carboxylase (acx operon)"),
    # Bxl ABC transport system — xylobiose
    "K17327": ("bxl", "Xylobiose ABC transporter (bxl system)"),
    "K17328": ("bxl", "Xylobiose ABC transporter (bxl system)"),
}

# ── Load significant pairs ─────────────────────────────────────────────────────
print("Loading significant pairs...")
sig = pd.read_csv(SIG)
print(f"  Pairs: {len(sig)}")

# ── Compute sign + IQR effect per pair ────────────────────────────────────────
print("Computing sign direction from raw CWM data...")

metals_needed = sig["metal"].unique().tolist()
lm_data = {}
for metal in metals_needed:
    p = DATA / f"lm_input_{metal}.csv"
    if not p.exists():
        print(f"  WARN: {p.name} not found; sign for {metal} will be NA")
        continue
    # Load only the columns we need
    df = pd.read_csv(p, usecols=["ko_id", "cwm", "log10_metal"])
    lm_data[metal] = df
    print(f"  Loaded {metal}: {len(df):,} rows")

sign_rows = []
for _, row in sig.iterrows():
    ko, metal = row["ko_id"], row["metal"]
    spearman_rho = np.nan
    delta_cwm_iqr = np.nan
    if metal in lm_data:
        sub = lm_data[metal][lm_data[metal]["ko_id"] == ko].dropna(
            subset=["cwm", "log10_metal"])
        if len(sub) >= 10:
            rho, _ = spearmanr(sub["log10_metal"], sub["cwm"])
            spearman_rho = rho
            # IQR effect: median CWM in top quartile - median CWM in bottom quartile
            q25 = sub["log10_metal"].quantile(0.25)
            q75 = sub["log10_metal"].quantile(0.75)
            lo_cwm = sub.loc[sub["log10_metal"] <= q25, "cwm"].median()
            hi_cwm = sub.loc[sub["log10_metal"] >= q75, "cwm"].median()
            delta_cwm_iqr = hi_cwm - lo_cwm
    sign_rows.append({
        "ko_id": ko,
        "metal": metal,
        "spearman_rho": spearman_rho,
        "beta_sign": int(np.sign(spearman_rho)) if not np.isnan(spearman_rho) else np.nan,
        "delta_cwm_iqr": delta_cwm_iqr,
        "direction": ("positive" if spearman_rho > 0 else "negative")
                      if not np.isnan(spearman_rho) else "unknown",
    })

sign_df = pd.DataFrame(sign_rows)

# ── Merge sign into sig ────────────────────────────────────────────────────────
sig = sig.merge(sign_df, on=["ko_id", "metal"], how="left")

# ── Add operon annotation ──────────────────────────────────────────────────────
sig["operon_id"] = sig["ko_id"].map(
    lambda k: OPERON_MAP.get(k, (k, "singleton"))[0])
sig["operon_name"] = sig["ko_id"].map(
    lambda k: OPERON_MAP.get(k, (None, "singleton"))[1])

# ── Print direction summary ────────────────────────────────────────────────────
print("\nSign direction by metal:")
for metal in ["As", "Pb", "Cr"]:
    sub = sig[sig["metal"] == metal]
    pos = (sub["beta_sign"] == 1).sum()
    neg = (sub["beta_sign"] == -1).sum()
    print(f"  {metal}: {len(sub)} pairs — {pos} positive (↑CWM with ↑metal), {neg} negative")

print("\nAll significant pairs with sign:")
display_cols = ["ko_id", "metal", "q_BH_full", "delta_r2_full",
                "spearman_rho", "beta_sign", "direction", "delta_cwm_iqr",
                "operon_id", "description"]
print(sig[display_cols].to_string(index=False))

# ── Save annotated CSV ─────────────────────────────────────────────────────────
out_path = DATA / "sig_annotated_sign_operon.csv"
sig.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")

# ── Operon-collapsed table ─────────────────────────────────────────────────────
print("\nBuilding operon-collapsed hit table...")

operon_rows = []
for (operon_id, metal), grp in sig.groupby(["operon_id", "metal"]):
    best_row = grp.loc[grp["q_BH_full"].idxmin()]
    operon_rows.append({
        "operon_id": operon_id,
        "metal": metal,
        "n_kos_in_operon": len(grp),
        "ko_ids": ";".join(grp["ko_id"].tolist()),
        "best_ko": best_row["ko_id"],
        "q_BH_min": best_row["q_BH_full"],
        "delta_r2_max": grp["delta_r2_full"].max(),
        "delta_cwm_iqr": grp["delta_cwm_iqr"].mean(),  # mean over operon KOs
        "direction": best_row["direction"],
        "beta_sign": best_row["beta_sign"],
        "operon_name": best_row["operon_name"],
        "description": best_row["description"],
        "kegg_l2_name": best_row.get("kegg_l2_name", ""),
        "outcome": best_row["outcome"],
    })

operon_df = pd.DataFrame(operon_rows).sort_values(["metal", "q_BH_min"])
operon_path = DATA / "operon_collapsed_hits.csv"
operon_df.to_csv(operon_path, index=False)
print(f"Saved: {operon_path}")

n_individual = len(sig)
n_operon = len(operon_df)
print(f"\nOperon collapsing: {n_individual} individual KO×metal pairs → {n_operon} operon-level hits")
print(f"\nOperon-collapsed hits:")
print(operon_df[["operon_id","metal","n_kos_in_operon","q_BH_min","delta_r2_max",
                 "direction","operon_name"]].to_string(index=False))

# ── Positive-direction bioindicator summary ────────────────────────────────────
pos_hits = operon_df[operon_df["beta_sign"] == 1]
neg_hits = operon_df[operon_df["beta_sign"] == -1]
print(f"\nPositive direction (↑CWM with ↑metal, bioindicator): {len(pos_hits)}/{n_operon}")
print(f"Negative direction (↓CWM with ↑metal, anti-indicator): {len(neg_hits)}/{n_operon}")
print("\nPositive hits:")
print(pos_hits[["operon_id","metal","q_BH_min","delta_r2_max","operon_name"]].to_string(index=False))
print("\nNegative hits:")
print(neg_hits[["operon_id","metal","q_BH_min","delta_r2_max","operon_name"]].to_string(index=False))

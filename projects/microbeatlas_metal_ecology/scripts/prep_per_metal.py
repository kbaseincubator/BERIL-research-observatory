#!/usr/bin/env python3
"""
Preprocess CWM + covariates into one CSV per metal for fast R lm() fitting.
Output: data/usa_cwm/lm_input_{metal}.csv with columns:
  ko_id, sample_id, cwm, log10_metal, ph_soilgrids, ph_ssurgo, ...all other covariates
"""
import os, sys
os.environ["OMP_NUM_THREADS"] = "1"
import pandas as pd
import numpy as np

DATA = "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"
METALS = ["As", "Cd", "Cr", "Cu", "Hg", "Pb"]

print("Loading CWM parquet...")
cwm = pd.read_parquet(f"{DATA}/cwm_all_ko_thinned_634.parquet")
print(f"CWM: {len(cwm)} rows, {cwm['ko_id'].nunique()} KOs, {cwm['sample_id'].nunique()} samples")

print("Loading covariate matrix...")
cov = pd.read_csv(f"{DATA}/covariate_matrix_634.csv")
print(f"COV: {len(cov)} rows, {len(cov.columns)} cols")

print("Merging CWM with covariates...")
merged = cwm.merge(cov, on="sample_id", how="inner")
print(f"Merged: {len(merged)} rows")

for metal in METALS:
    if metal not in merged.columns:
        print(f"  SKIP {metal}: column missing")
        continue
    sub = merged[merged[metal].notna()].copy()
    sub["log10_metal"] = np.log10(np.maximum(sub[metal], 1e-6))
    # Drop raw metal columns except the one being processed (keep log10)
    drop_cols = [m for m in METALS if m != metal]
    sub.drop(columns=drop_cols, inplace=True, errors="ignore")
    out_path = f"{DATA}/lm_input_{metal}.csv"
    sub.to_csv(out_path, index=False)
    n_rows = len(sub)
    n_kos = sub["ko_id"].nunique()
    print(f"  {metal}: {n_rows} rows, {n_kos} KOs → {out_path}")

print("Done.")

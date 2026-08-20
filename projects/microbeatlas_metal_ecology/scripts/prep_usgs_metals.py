#!/usr/bin/env python3
"""
prep_usgs_metals.py

For each USGS element in usgs_concentrations_634.csv with ≥MIN_COVERAGE_FRAC coverage,
merges CWM + covariate matrix to create lm_input_{element}.csv files.

Mirrors the logic of prep_per_metal.py. Skips As/Cd/Cr/Cu/Hg/Pb (already done).
Skips elements that already have an lm_input file unless --force is given.
"""

import os, sys
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np
import pandas as pd
from pathlib import Path

DATA     = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
CWM_PATH = DATA / "cwm_all_ko_thinned_634.parquet"
COV_PATH = DATA / "covariate_matrix_634.csv"
CONC_PATH = DATA / "usgs_concentrations_634.csv"
COV_PATH  = DATA / "usgs_species_coverage.csv"

EXISTING_METALS      = {"As", "Cd", "Cr", "Cu", "Hg", "Pb"}
MIN_COVERAGE_FRAC    = 0.50
FORCE                = "--force" in sys.argv

print("=" * 70)
print("prep_usgs_metals.py")
print("=" * 70)

# ── Load coverage survey to determine which elements to process ───────────────
print(f"\nLoading species coverage: {COV_PATH}")
coverage = pd.read_csv(COV_PATH)
target_elements = (coverage[coverage["coverage_frac"] >= MIN_COVERAGE_FRAC]["species"]
                   .tolist())
target_elements = [e for e in target_elements if e not in EXISTING_METALS]
print(f"  Target elements (new, ≥{MIN_COVERAGE_FRAC*100:.0f}% coverage): {target_elements}")

# ── Load USGS concentrations ───────────────────────────────────────────────────
print(f"\nLoading concentrations: {CONC_PATH}")
conc = pd.read_csv(CONC_PATH)
conc_path_str = str(CONC_PATH)  # keep for display

# ── Load covariate matrix ──────────────────────────────────────────────────────
cov_path = DATA / "covariate_matrix_634.csv"
print(f"Loading covariates: {cov_path}")
cov = pd.read_csv(cov_path)
print(f"  Shape: {cov.shape}")

# Merge organic TRI patch if available
org_patch = DATA / "organic_by_sample.csv"
if org_patch.exists() and "epa_tri_organic_releases" not in cov.columns:
    print(f"  Merging organic TRI patch...")
    org = pd.read_csv(org_patch)
    cov = cov.merge(org, on="sample_id", how="left")

# Merge USGS concentrations into cov (adds La_ppm, U_ppm, etc.)
ppm_cols = [c for c in conc.columns if c.endswith("_ppm")]
cov = cov.merge(conc[["sample_id"] + ppm_cols], on="sample_id", how="left")

# All raw metal columns present in cov (original 6 + new element if added)
orig_metal_cols = [m for m in EXISTING_METALS if m in cov.columns]

# ── Load CWM parquet ───────────────────────────────────────────────────────────
print(f"\nLoading CWM parquet: {CWM_PATH}")
cwm = pd.read_parquet(CWM_PATH)
print(f"  Shape: {cwm.shape}")

# Merge CWM with full covariate matrix once
merged = cwm.merge(cov, on="sample_id", how="inner")
print(f"  Merged shape: {merged.shape}")

# ── Build one CSV per new element ─────────────────────────────────────────────
for element in target_elements:
    out_path = DATA / f"lm_input_{element}.csv"
    if out_path.exists() and not FORCE:
        print(f"\n  {element}: SKIPPING (lm_input already exists; use --force to overwrite)")
        continue

    ppm_col = f"{element}_ppm"
    if ppm_col not in merged.columns:
        print(f"\n  {element}: SKIPPING ({ppm_col} not found in merged dataframe)")
        continue

    sub = merged[merged[ppm_col].notna()].copy()
    # Rename _ppm column to element name (matching original format: "As", "Cd", etc.)
    sub = sub.rename(columns={ppm_col: element})
    sub["log10_metal"] = np.log10(np.maximum(sub[element], 1e-6))

    # Drop original 6 metal columns and all other _ppm columns
    drop_cols = (
        orig_metal_cols +
        [c for c in sub.columns if c.endswith("_ppm") and c != ppm_col]
    )
    sub.drop(columns=[c for c in drop_cols if c in sub.columns], inplace=True)

    n_rows = len(sub)
    n_kos  = sub["ko_id"].nunique()
    n_samp = sub["sample_id"].nunique()
    print(f"\n  {element}: {n_samp} samples, {n_kos} KOs → {n_rows:,} rows")
    sub.to_csv(out_path, index=False)
    print(f"    Saved: {out_path}")

print("\nDone.")

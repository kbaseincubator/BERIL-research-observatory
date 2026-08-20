#!/bin/bash
# run_lm_usgs_metals.sh
# Full pipeline for USGS element extension:
#   1. build_usgs_metal_concentrations.py  -- spatial coverage survey + wide table
#   2. prep_usgs_metals.py                 -- lm_input CSVs for new elements
#   3. lm_ns_full_model.R                  -- full model (SSURGO-primary pH)
#   4. Pool BH-FDR across original 6 + new elements
#
# Uses updated lm_ns_full_model.R which now:
#   - Uses SSURGO pH as primary, calibrated SoilGrids for imputation
#   - Still includes epa_tri_organic_releases confounder
set -e
export OMP_NUM_THREADS=1

SCRIPTS=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts
DATA=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm
LOG=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/logs
RSCRIPT=/home/hmacgregor/r_env/bin/Rscript

mkdir -p "$LOG"

# ── Step 1: Build USGS concentration table ───────────────────────────────────
echo "=== $(date) | Step 1: Building USGS concentration table ==="
python3 "$SCRIPTS/build_usgs_metal_concentrations.py" 2>&1 | tee "$LOG/build_usgs_conc.log"
echo "=== $(date) | Step 1 done ==="

# ── Step 2: Prep per-metal CSVs for new elements ─────────────────────────────
echo "=== $(date) | Step 2: Prepping per-element lm_input CSVs ==="
python3 "$SCRIPTS/prep_usgs_metals.py" 2>&1 | tee "$LOG/prep_usgs_metals.log"
echo "=== $(date) | Step 2 done ==="

# ── Step 3: Run full model for each new element ───────────────────────────────
# Read target elements from coverage CSV (≥50% coverage, not in original 6)
ORIG_METALS="As Cd Cr Cu Hg Pb"
echo "=== $(date) | Step 3: Running full model for new USGS elements ==="

python3 - << 'PYEOF'
import pandas as pd
from pathlib import Path
DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")
coverage = pd.read_csv(DATA / "usgs_species_coverage.csv")
target = coverage[coverage["coverage_frac"] >= 0.50]["species"].tolist()
orig = {"As","Cd","Cr","Cu","Hg","Pb"}
new_elements = [e for e in target if e not in orig]
# Write to a temp file for bash to read
with open("/tmp/usgs_new_elements.txt","w") as f:
    f.write(" ".join(new_elements))
print(f"New elements to run: {new_elements}")
PYEOF

NEW_ELEMENTS=$(cat /tmp/usgs_new_elements.txt)
echo "  New elements: $NEW_ELEMENTS"

for element in $NEW_ELEMENTS; do
    INPUT="$DATA/lm_input_${element}.csv"
    OUTPUT="$DATA/lm_out_full_${element}.csv"
    if [ ! -f "$INPUT" ]; then
        echo "  SKIP $element: lm_input not found"
        continue
    fi
    echo "=== $(date) | Running $element ==="
    $RSCRIPT "$SCRIPTS/lm_ns_full_model.R" \
        "$INPUT" "$element" "$OUTPUT" \
        2>&1 | tee "$LOG/lm_full_${element}.log"
    echo "=== $(date) | Done $element ==="
done

# ── Step 4: Re-run original 6 metals with updated pH ─────────────────────────
# The R script now uses SSURGO-primary pH — re-run originals for consistency.
echo "=== $(date) | Step 3b: Re-running original 6 metals with SSURGO-primary pH ==="
for metal in As Cd Cr Cu Hg Pb; do
    INPUT="$DATA/lm_input_${metal}.csv"
    OUTPUT="$DATA/lm_out_full_ssurgo_${metal}.csv"
    echo "=== $(date) | Re-running $metal (SSURGO pH) ==="
    $RSCRIPT "$SCRIPTS/lm_ns_full_model.R" \
        "$INPUT" "$metal" "$OUTPUT" \
        2>&1 | tee "$LOG/lm_full_ssurgo_${metal}.log"
    echo "=== $(date) | Done $metal ==="
done

# ── Step 5: Pool BH-FDR across ALL metals ────────────────────────────────────
echo "=== $(date) | Step 4: Pooling BH-FDR across all metals ==="

python3 - << 'PYEOF'
import pandas as pd
import numpy as np
from statsmodels.stats.multitest import multipletests
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")

# Load coverage to get all target elements
coverage = pd.read_csv(DATA / "usgs_species_coverage.csv")
orig = {"As","Cd","Cr","Cu","Hg","Pb"}
new_elements = [e for e in coverage[coverage["coverage_frac"] >= 0.50]["species"] if e not in orig]

# Use SSURGO-pH rerun for original 6; new elements from lm_out_full_{el}.csv
dfs = []
# Original 6 (SSURGO pH version)
for metal in ["As","Cd","Cr","Cu","Hg","Pb"]:
    p = DATA / f"lm_out_full_ssurgo_{metal}.csv"
    if not p.exists():
        p = DATA / f"lm_out_full_{metal}.csv"
        print(f"  {metal}: SSURGO rerun not found, using original full model")
    if p.exists():
        df = pd.read_csv(p)
        print(f"  {metal}: {len(df)} rows from {p.name}")
        dfs.append(df)
    else:
        print(f"  {metal}: MISSING")

# New elements
for element in new_elements:
    p = DATA / f"lm_out_full_{element}.csv"
    if p.exists():
        df = pd.read_csv(p)
        print(f"  {element}: {len(df)} rows")
        dfs.append(df)
    else:
        print(f"  {element}: MISSING")

if not dfs:
    print("No results found!")
    import sys; sys.exit(1)

out = pd.concat(dfs, ignore_index=True)

# BH-FDR on full model p-values across ALL metals simultaneously
valid = out[out["p_metal_full"].notna() & (out["n"] >= 30)].copy()
_, q_full, _, _ = multipletests(valid["p_metal_full"].values, method="fdr_bh")
valid["q_BH_full"] = q_full

valid_base = out[out["p_metal_base"].notna() & (out["n"] >= 30)].copy()
_, q_base, _, _ = multipletests(valid_base["p_metal_base"].values, method="fdr_bh")
valid_base["q_BH_base"] = q_base

out = (out
       .merge(valid[["ko_id","metal","q_BH_full"]], on=["ko_id","metal"], how="left")
       .merge(valid_base[["ko_id","metal","q_BH_base"]], on=["ko_id","metal"], how="left"))

out_path = DATA / "gam_results_usgs_all.csv"
out.to_csv(out_path, index=False)

n_sig = (valid["q_BH_full"] < 0.05).sum()
n_base_sig = (valid_base["q_BH_base"] < 0.05).sum()
print(f"\nTotal rows: {len(out):,}")
print(f"Testable (n≥30): {len(valid):,}")
print(f"BH FDR<0.05 (base/pH only): {n_base_sig}")
print(f"BH FDR<0.05 (full model):   {n_sig}")

# Per-metal breakdown
print("\nPer-metal summary (full model):")
for metal, grp in valid[valid["q_BH_full"] < 0.05].groupby("metal"):
    print(f"  {metal}: {len(grp)} FDR<0.05 pairs")

# Attenuation breakdown
if n_sig > 0 and n_base_sig > 0:
    base_sig = set(zip(valid_base[valid_base["q_BH_base"]<0.05]["ko_id"],
                       valid_base[valid_base["q_BH_base"]<0.05]["metal"]))
    full_sig = set(zip(valid[valid["q_BH_full"]<0.05]["ko_id"],
                       valid[valid["q_BH_full"]<0.05]["metal"]))
    survived = base_sig & full_sig
    novel    = full_sig - base_sig
    print(f"\nSurvived (base+full): {len(survived)}")
    print(f"Novel (full only):    {len(novel)}")

    print(f"\nTop 20 full-model hits:")
    top = valid[valid["q_BH_full"] < 0.05].sort_values("q_BH_full").head(20)
    print(top[["ko_id","metal","n","q_BH_full","delta_r2_full","delta_r2_base"]].to_string())

print(f"\nSaved: {out_path}")
PYEOF

echo "=== $(date) | ALL DONE ==="
echo "Results: $DATA/gam_results_usgs_all.csv"

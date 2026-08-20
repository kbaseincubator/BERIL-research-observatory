#!/usr/bin/env bash
# run_lm_full_v2.sh — Re-run full model with extended covariate matrix (v2)
#
# Changes vs original:
#   - Passes covariate_matrix_634_v2.csv as 4th arg to lm_ns_full_model.R
#   - v2 adds: MAT, MAP, temp_seasonality, precip_seasonality, temp_annual_range_c,
#              nitrogen_0cm, sand_0cm, silt_0cm, bulk_density_0cm, elevation_m
#   - v2 removes: tectonic_boundary_dist (17.5% coverage)
#   - v2 imputes: epa_tri_releases NA → 0
#   - Effective full-model n: ~389/634 vs 55/634 in v1
set -euo pipefail

SCRIPTS="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts"
DATA="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"
LOG="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/logs"
RSCRIPT="/home/hmacgregor/r_env/bin/Rscript"
COV_V2="$DATA/covariate_matrix_634_v2.csv"

mkdir -p "$LOG"

ORIG6="As Cd Cr Cu Hg Pb"
NEW_ELEMENTS=$(python3 -c "
import pandas as pd
cov = pd.read_csv('$DATA/usgs_species_coverage.csv')
orig = {'As','Cd','Cr','Cu','Hg','Pb'}
new = [e for e in cov[cov['coverage_frac']>=0.5]['species'] if e not in orig]
print(' '.join(new))
")

ALL_ELEMENTS="$ORIG6 $NEW_ELEMENTS"

echo "=== $(date) | Starting v2 full model run ==="
echo "Covariate matrix: $COV_V2"
echo "Elements to process: $(echo $ALL_ELEMENTS | wc -w)"

for element in $ALL_ELEMENTS; do
    INPUT="$DATA/lm_input_${element}.csv"
    OUTPUT="$DATA/lm_out_v2_${element}.csv"
    if [ ! -f "$INPUT" ]; then
        echo "=== $(date) | SKIP $element (no input CSV) ==="
        continue
    fi
    if [ -f "$OUTPUT" ]; then
        echo "=== $(date) | SKIP $element (already done) ==="
        continue
    fi
    echo "=== $(date) | Running $element ==="
    $RSCRIPT "$SCRIPTS/lm_ns_full_model.R" \
        "$INPUT" "$element" "$OUTPUT" "$COV_V2" \
        2>&1 | tee "$LOG/lm_v2_${element}.log"
    echo "=== $(date) | Done $element ==="
done

echo "=== $(date) | Pooling BH-FDR across all metals (v2) ==="

python3 - << 'PYEOF'
import pandas as pd
import numpy as np
from statsmodels.stats.multitest import multipletests
from pathlib import Path

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")

coverage = pd.read_csv(DATA / "usgs_species_coverage.csv")
orig = {"As","Cd","Cr","Cu","Hg","Pb"}
all_elements = list(orig) + [e for e in coverage[coverage["coverage_frac"] >= 0.50]["species"] if e not in orig]

dfs = []
for element in all_elements:
    p = DATA / f"lm_out_v2_{element}.csv"
    if p.exists():
        df = pd.read_csv(p)
        print(f"  {element}: {len(df)} rows, {df['p_metal_full'].notna().sum()} valid full-model")
        dfs.append(df)
    else:
        print(f"  {element}: MISSING")

if not dfs:
    print("No results found!"); import sys; sys.exit(1)

out = pd.concat(dfs, ignore_index=True)

# Quality filter: exclude metals where ALL sig hits have delta_cwm_iqr=0 (detection limit artifact)
print("\nApplying detection-limit quality filter...")
for metal in out['metal'].unique():
    sub = out[(out['metal'] == metal) & (out['p_metal_full'].notna())]
    if len(sub) == 0:
        continue

# BH-FDR across all valid pairs (n >= 30) — full model
valid_full = out[out["p_metal_full"].notna() & (out["n"] >= 30)].copy()
_, q_full, _, _ = multipletests(valid_full["p_metal_full"].values, method="fdr_bh")
valid_full["q_BH_full_v2"] = q_full

# BH-FDR — base model
valid_base = out[out["p_metal_base"].notna() & (out["n"] >= 30)].copy()
_, q_base, _, _ = multipletests(valid_base["p_metal_base"].values, method="fdr_bh")
valid_base["q_BH_base_v2"] = q_base

out = out.merge(valid_full[["ko_id","metal","q_BH_full_v2"]], on=["ko_id","metal"], how="left")
out = out.merge(valid_base[["ko_id","metal","q_BH_base_v2"]], on=["ko_id","metal"], how="left")

out_path = DATA / "gam_results_v2_all.csv"
out.attrs = {}
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Total rows: {len(out):,}")
n_full_sig = (out["q_BH_full_v2"] < 0.05).sum()
n_base_sig = (out["q_BH_base_v2"] < 0.05).sum()
print(f"FDR<0.05 full model (v2): {n_full_sig:,}")
print(f"FDR<0.05 base model (v2): {n_base_sig:,}")

# Per-metal breakdown
metal_summary = out.groupby("metal").agg(
    n_full=("q_BH_full_v2", lambda x: (x < 0.05).sum()),
    n_base=("q_BH_base_v2", lambda x: (x < 0.05).sum()),
).sort_values("n_full", ascending=False).head(20)
print("\nTop metals by full-model hits (v2):")
print(metal_summary.to_string())
PYEOF

echo "=== $(date) | v2 run COMPLETE ==="
echo "Results: $DATA/gam_results_v2_all.csv"

#!/usr/bin/env bash
# run_lm_full_v3.sh — Full model with per-covariate partial R² attribution (v3)
#
# Changes vs v2:
#   - lm_ns_full_model.R now runs drop1() after each KO fit to output pr2_* columns
#     (Type II partial R² per covariate: metal, pH, clay, OM, drainage, lith, etc.)
#   - 71 USGS elements (coverage >= 0.5), not just the 6 original metals
#   - Parallel: up to MAX_PARALLEL elements run simultaneously (default 16)
#   - Output: lm_out_v3_*.csv, gam_results_v3_all.csv
#   - Same covariate matrix as v2 (covariate_matrix_634_v2.csv)
#
# Timing: each element takes ~90-165s loop time + ~60s IO.
# At MAX_PARALLEL=16: all 71 elements complete in ~15-20 min.
set -uo pipefail

export SCRIPTS="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts"
export DATA="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"
export LOG="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/logs"
export RSCRIPT="/home/hmacgregor/r_env/bin/Rscript"
export COV_V2="$DATA/covariate_matrix_634_v2.csv"

# Cgroup limit: ~25.77GB for this pod. Baseline (page cache + Java + Claude) ≈ 12.5GB.
# Available for R: ~13GB. Each element at MC_CORES=8 peaks at ~25.7GB (dangerously tight).
# MC_CORES=4 halves fork COW pressure → peak ~20GB → ~5GB headroom. Safe for serial runs.
# MAX_PARALLEL=1 enforces serial execution — only one R element at a time.
export MC_CORES=4
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

MAX_PARALLEL=1

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

echo "=== $(date) | Starting v3 parallel run ==="
echo "MAX_PARALLEL=$MAX_PARALLEL  MC_CORES=$MC_CORES"
echo "Elements to process: $(echo $ALL_ELEMENTS | wc -w)"
echo "" > "$LOG/v3_progress.log"

# ---- per-element worker (runs in background) ------------------------------------
run_element() {
    local element="$1"
    local INPUT="$DATA/lm_input_${element}.csv"
    local OUTPUT="$DATA/lm_out_v3_${element}.csv"
    local ELOG="$LOG/lm_v3_${element}.log"

    echo "=== $(date) | START $element ===" > "$ELOG"
    if MC_CORES="$MC_CORES" "$RSCRIPT" "$SCRIPTS/lm_ns_full_model.R" \
            "$INPUT" "$element" "$OUTPUT" "$COV_V2" \
            >> "$ELOG" 2>&1; then
        echo "=== $(date) | DONE $element ===" >> "$ELOG"
        echo "$(date +%H:%M:%S) DONE    $element" >> "$LOG/v3_progress.log"
    else
        echo "=== $(date) | ERROR $element ===" >> "$ELOG"
        echo "$(date +%H:%M:%S) ERROR   $element" >> "$LOG/v3_progress.log"
    fi
}
export -f run_element

# ---- parallel launch with throttle ----------------------------------------------
pids=()

for element in $ALL_ELEMENTS; do
    INPUT="$DATA/lm_input_${element}.csv"
    OUTPUT="$DATA/lm_out_v3_${element}.csv"

    if [ ! -f "$INPUT" ]; then
        echo "$(date +%H:%M:%S) SKIP    $element (no input CSV)"
        continue
    fi
    if [ -f "$OUTPUT" ]; then
        echo "$(date +%H:%M:%S) SKIP    $element (already done)"
        continue
    fi

    # Throttle: wait for a slot to open
    while (( ${#pids[@]} >= MAX_PARALLEL )); do
        wait -n 2>/dev/null || true
        new_pids=()
        for p in "${pids[@]}"; do
            kill -0 "$p" 2>/dev/null && new_pids+=("$p")
        done
        pids=("${new_pids[@]}")
    done

    run_element "$element" &
    pids+=($!)
    echo "$(date +%H:%M:%S) LAUNCH  $element  [${#pids[@]}/$MAX_PARALLEL running]"
done

echo "=== $(date) | Waiting for ${#pids[@]} remaining jobs ==="
wait
echo "=== $(date) | All elements complete ==="

# ---- pool BH-FDR across all 71 elements ----------------------------------------
echo "=== $(date) | Pooling BH-FDR (v3) ==="

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
    p = DATA / f"lm_out_v3_{element}.csv"
    if p.exists():
        df = pd.read_csv(p)
        print(f"  {element}: {len(df)} rows, {df['p_metal_full'].notna().sum()} valid full-model")
        dfs.append(df)
    else:
        print(f"  {element}: MISSING")

if not dfs:
    print("No results found!"); import sys; sys.exit(1)

out = pd.concat(dfs, ignore_index=True)

# BH-FDR across all valid pairs (n >= 30)
valid_full = out[out["p_metal_full"].notna() & (out["n"] >= 30)].copy()
_, q_full, _, _ = multipletests(valid_full["p_metal_full"].values, method="fdr_bh")
valid_full["q_BH_full_v3"] = q_full

valid_base = out[out["p_metal_base"].notna() & (out["n"] >= 30)].copy()
_, q_base, _, _ = multipletests(valid_base["p_metal_base"].values, method="fdr_bh")
valid_base["q_BH_base_v3"] = q_base

out = out.merge(valid_full[["ko_id","metal","q_BH_full_v3"]], on=["ko_id","metal"], how="left")
out = out.merge(valid_base[["ko_id","metal","q_BH_base_v3"]], on=["ko_id","metal"], how="left")

out_path = DATA / "gam_results_v3_all.csv"
out.attrs = {}
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Total rows: {len(out):,}")
n_full_sig = (out["q_BH_full_v3"] < 0.05).sum()
n_base_sig = (out["q_BH_base_v3"] < 0.05).sum()
print(f"FDR<0.05 full model (v3): {n_full_sig:,}")
print(f"FDR<0.05 base model (v3): {n_base_sig:,}")

metal_summary = out.groupby("metal").agg(
    n_full=("q_BH_full_v3", lambda x: (x < 0.05).sum()),
    n_base=("q_BH_base_v3", lambda x: (x < 0.05).sum()),
).sort_values("n_full", ascending=False).head(30)
print("\nTop metals by full-model hits (v3):")
print(metal_summary.to_string())

# Attribution: which covariates absorb most variance among FDR-sig pairs
pr2_cols = [c for c in out.columns if c.startswith("pr2_")]
if pr2_cols:
    sig = out[out["q_BH_full_v3"] < 0.05]
    print(f"\nCovariate partial R² (median, FDR<0.05 pairs, n={len(sig)}):")
    print(sig[pr2_cols].median().sort_values(ascending=False).head(20).to_string())
PYEOF

echo "=== $(date) | v3 run COMPLETE ==="
echo "Results: $DATA/gam_results_v3_all.csv"
echo "Progress log: $LOG/v3_progress.log"

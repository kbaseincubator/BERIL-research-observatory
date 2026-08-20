#!/usr/bin/env bash
# run_lm_metal_only.sh — Metal-only model (no pH, no confounders) for all 71 USGS elements
# Compares with base (pH only) and full (all confounders) to show what pH and confounders explain.
set -euo pipefail

SCRIPTS="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts"
DATA="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"
LOG="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/logs"
RSCRIPT="/home/hmacgregor/r_env/bin/Rscript"

mkdir -p "$LOG"

# All 71 elements: original 6 + new USGS elements
ORIG6="As Cd Cr Cu Hg Pb"
NEW_ELEMENTS=$(python3 -c "
import pandas as pd
cov = pd.read_csv('$DATA/usgs_species_coverage.csv')
orig = {'As','Cd','Cr','Cu','Hg','Pb'}
new = [e for e in cov[cov['coverage_frac']>=0.5]['species'] if e not in orig]
print(' '.join(new))
")

ALL_ELEMENTS="$ORIG6 $NEW_ELEMENTS"

for element in $ALL_ELEMENTS; do
    INPUT="$DATA/lm_input_${element}.csv"
    OUTPUT="$DATA/lm_out_noph_${element}.csv"
    if [ ! -f "$INPUT" ]; then
        echo "=== $(date) | SKIP $element (no input CSV) ==="
        continue
    fi
    if [ -f "$OUTPUT" ]; then
        echo "=== $(date) | SKIP $element (already done) ==="
        continue
    fi
    echo "=== $(date) | Running $element ==="
    $RSCRIPT "$SCRIPTS/lm_ns_metal_only.R" \
        "$INPUT" "$element" "$OUTPUT" \
        2>&1 | tee "$LOG/lm_noph_${element}.log"
    echo "=== $(date) | Done $element ==="
done

echo "=== $(date) | Pooling BH-FDR across all metals ==="

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
    p = DATA / f"lm_out_noph_{element}.csv"
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
valid = out[out["p_metal_noph"].notna() & (out["n"] >= 30)].copy()
_, q_noph, _, _ = multipletests(valid["p_metal_noph"].values, method="fdr_bh")
valid["q_BH_noph"] = q_noph

# Merge back
out = out.merge(valid[["ko_id","metal","q_BH_noph"]], on=["ko_id","metal"], how="left")
out_path = DATA / "gam_results_noph_all.csv"
out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Total rows: {len(out):,}")
n_sig = (out["q_BH_noph"] < 0.05).sum()
print(f"FDR<0.05 (metal only, no pH): {n_sig:,}")
PYEOF

echo "=== $(date) | ALL DONE ==="
echo "Results: $DATA/gam_results_noph_all.csv"

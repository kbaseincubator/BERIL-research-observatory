#!/usr/bin/env bash
# run_lm_spatial.sh — Spatial sensitivity: full model + spatial trend surface + 30 MEM eigenvectors
#
# Passes covariate_matrix_634_spatial.csv as 4th arg to lm_ns_full_model.R.
# lm_ns_full_model.R auto-detects sp_* columns via grep and adds them to linear_candidates.
# Outputs: lm_out_spatial_{element}.csv (original 6 metals only, ~1 hour)
set -euo pipefail

SCRIPTS="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts"
DATA="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"
LOG="/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/logs/spatial"
RSCRIPT="/home/hmacgregor/r_env/bin/Rscript"
COV_SPATIAL="$DATA/covariate_matrix_634_spatial.csv"

mkdir -p "$LOG"

METALS="As Cd Cr Cu Hg Pb"

echo "=== $(date) | Starting spatial sensitivity run ===" | tee "$LOG/run_spatial.log"
echo "Covariate matrix: $COV_SPATIAL" | tee -a "$LOG/run_spatial.log"

for metal in $METALS; do
    INPUT="$DATA/lm_input_${metal}.csv"
    OUTPUT="$DATA/lm_out_spatial_${metal}.csv"

    if [ ! -f "$INPUT" ]; then
        echo "=== $(date) | SKIP $metal (no input CSV) ===" | tee -a "$LOG/run_spatial.log"
        continue
    fi

    echo "=== $(date) | Running $metal ===" | tee -a "$LOG/run_spatial.log"
    $RSCRIPT "$SCRIPTS/lm_ns_full_model.R" \
        "$INPUT" "$metal" "$OUTPUT" "$COV_SPATIAL" \
        > "$LOG/lm_spatial_${metal}.log" 2>&1
    echo "=== $(date) | Done $metal ===" | tee -a "$LOG/run_spatial.log"
done

echo "=== $(date) | All metals done ===" | tee -a "$LOG/run_spatial.log"

# Pool results with BH-FDR across all 6 metals
python3 -c "
import pandas as pd, numpy as np
from pathlib import Path
from statsmodels.stats.multitest import multipletests

DATA = Path('$DATA')
metals = 'As Cd Cr Cu Hg Pb'.split()
dfs = []
for m in metals:
    f = DATA / f'lm_out_spatial_{m}.csv'
    if f.exists():
        df = pd.read_csv(f)
        df['metal'] = m
        dfs.append(df)
if not dfs:
    print('No output files found'); exit(1)

out = pd.concat(dfs, ignore_index=True)
mask = out['p_metal_full'].notna()
_, q, _, _ = multipletests(out.loc[mask, 'p_metal_full'], method='fdr_bh')
out.loc[mask, 'q_BH_spatial'] = q
mask_base = out['p_metal_base'].notna()
_, q_base, _, _ = multipletests(out.loc[mask_base, 'p_metal_base'], method='fdr_bh')
out.loc[mask_base, 'q_BH_spatial_base'] = q_base

out.to_csv(DATA / 'gam_results_spatial.csv', index=False)
n_sig = (out['q_BH_spatial'] < 0.05).sum()
print(f'Pooled {len(out):,} tests; FDR<0.05 spatial full model: {n_sig}')
by_metal = out[out['q_BH_spatial'] < 0.05].groupby('metal').size().sort_values(ascending=False)
print(by_metal.to_string())
" | tee -a "$LOG/run_spatial.log"

echo "=== $(date) | Spatial sensitivity COMPLETE ===" | tee -a "$LOG/run_spatial.log"

#!/bin/bash
# Run lm_ns_per_metal.R sequentially for all 6 metals.
set -e
SCRIPTS=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts
DATA=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm
LOG=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/logs
RSCRIPT=/home/hmacgregor/r_env/bin/Rscript

mkdir -p "$LOG"
export OMP_NUM_THREADS=1

for metal in As Cd Cr Cu Hg Pb; do
    echo "=== $(date) | Starting $metal ==="
    $RSCRIPT "$SCRIPTS/lm_ns_per_metal.R" \
        "$DATA/lm_input_${metal}.csv" \
        "$metal" \
        "$DATA/lm_out_${metal}.csv" \
        2>&1 | tee -a "$LOG/lm_ns_${metal}.log"
    echo "=== $(date) | Done $metal ==="
done

echo "=== All metals done. Concatenating... ==="
python3 - <<'EOF'
import pandas as pd, os
DATA = "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"
dfs = []
for metal in ["As","Cd","Cr","Cu","Hg","Pb"]:
    p = f"{DATA}/lm_out_{metal}.csv"
    if os.path.exists(p):
        dfs.append(pd.read_csv(p))
        print(f"  {metal}: {len(dfs[-1])} rows")
    else:
        print(f"  {metal}: MISSING")
out = pd.concat(dfs, ignore_index=True)
valid = out[out["p_metal"].notna() & (out["n"] >= 30)]
valid["q_BH"] = pd.NA
from statsmodels.stats.multitest import multipletests
_, q, _, _ = multipletests(valid["p_metal"].values, method="fdr_bh")
valid = valid.copy(); valid["q_BH"] = q
out = out.merge(valid[["ko_id","metal","q_BH"]], on=["ko_id","metal"], how="left")
out.to_csv(f"{DATA}/gam_results_base_only.csv", index=False)
print(f"\nTotal rows: {len(out)}")
print(f"Testable (n>=30): {len(valid)}")
n_sig = (valid["q_BH"] < 0.05).sum()
print(f"BH FDR<0.05: {n_sig}")
if n_sig > 0:
    top = valid[valid["q_BH"] < 0.05].sort_values("q_BH").head(20)
    print(top[["ko_id","metal","n","p_metal","q_BH","delta_r2"]].to_string())
else:
    top = valid.sort_values("p_metal").head(10)
    print("Top 10 by p (all q>0.05):")
    print(top[["ko_id","metal","n","p_metal","delta_r2"]].to_string())
print(f"\nSaved: {DATA}/gam_results_base_only.csv")
EOF
echo "=== $(date) | COMPLETE ==="

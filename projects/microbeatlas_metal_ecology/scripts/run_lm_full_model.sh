#!/bin/bash
# Run lm_ns_full_model.R sequentially for all 6 metals.
set -e
SCRIPTS=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/scripts
DATA=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm
LOG=/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/logs
RSCRIPT=/home/hmacgregor/r_env/bin/Rscript

mkdir -p "$LOG"
export OMP_NUM_THREADS=1

for metal in As Cd Cr Cu Hg Pb; do
    echo "=== $(date) | Starting $metal ==="
    $RSCRIPT "$SCRIPTS/lm_ns_full_model.R" \
        "$DATA/lm_input_${metal}.csv" \
        "$metal" \
        "$DATA/lm_out_full_${metal}.csv" \
        2>&1 | tee "$LOG/lm_full_${metal}.log"
    echo "=== $(date) | Done $metal ==="
done

echo "=== All metals done. Concatenating + BH-FDR... ==="
python3 - <<'EOF'
import pandas as pd
from statsmodels.stats.multitest import multipletests
import os

DATA = "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm"

dfs = []
for metal in ["As","Cd","Cr","Cu","Hg","Pb"]:
    p = f"{DATA}/lm_out_full_{metal}.csv"
    if os.path.exists(p):
        dfs.append(pd.read_csv(p))
        print(f"  {metal}: {len(dfs[-1])} rows")
    else:
        print(f"  {metal}: MISSING")

out = pd.concat(dfs, ignore_index=True)

# BH-FDR on full model p-values
valid_full = out[out["p_metal_full"].notna() & (out["n"] >= 30)].copy()
_, q_full, _, _ = multipletests(valid_full["p_metal_full"].values, method="fdr_bh")
valid_full["q_BH_full"] = q_full

# BH-FDR on base model p-values (same samples, for attenuation)
valid_base = out[out["p_metal_base"].notna() & (out["n"] >= 30)].copy()
_, q_base, _, _ = multipletests(valid_base["p_metal_base"].values, method="fdr_bh")
valid_base["q_BH_base"] = q_base

out = out.merge(valid_full[["ko_id","metal","q_BH_full"]], on=["ko_id","metal"], how="left")
out = out.merge(valid_base[["ko_id","metal","q_BH_base"]], on=["ko_id","metal"], how="left")
out.to_csv(f"{DATA}/gam_results_raw.csv", index=False)

n_sig_full = (valid_full["q_BH_full"] < 0.05).sum()
n_sig_base = (valid_base["q_BH_base"] < 0.05).sum()
print(f"\nTotal rows: {len(out)}")
print(f"Testable (n>=30): {len(valid_full)}")
print(f"BH FDR<0.05 (base model / pH only):       {n_sig_base}")
print(f"BH FDR<0.05 (full model / all confounders): {n_sig_full}")

# Attenuation: base-sig pairs that fall out in full model
if n_sig_base > 0 and n_sig_full > 0:
    base_sig = set(zip(valid_base[valid_base["q_BH_base"]<0.05]["ko_id"],
                       valid_base[valid_base["q_BH_base"]<0.05]["metal"]))
    full_sig = set(zip(valid_full[valid_full["q_BH_full"]<0.05]["ko_id"],
                       valid_full[valid_full["q_BH_full"]<0.05]["metal"]))
    survived  = base_sig & full_sig
    attenuated = base_sig - full_sig
    novel      = full_sig - base_sig
    print(f"\nOf {n_sig_base} base-sig pairs:")
    print(f"  Survived full-model control: {len(survived)}")
    print(f"  Attenuated (lost sig):       {len(attenuated)}")
    print(f"  Novel (only in full model):  {len(novel)}")

print(f"\nTop 20 full-model hits:")
top = valid_full[valid_full["q_BH_full"] < 0.05].sort_values("q_BH_full").head(20)
print(top[["ko_id","metal","n","p_metal_full","q_BH_full","delta_r2_full","delta_r2_base"]].to_string())

print(f"\nSaved: {DATA}/gam_results_raw.csv")
EOF
echo "=== $(date) | COMPLETE ==="

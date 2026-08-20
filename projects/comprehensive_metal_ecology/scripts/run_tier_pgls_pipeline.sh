#!/bin/bash
# Run after compute_tier_z_scores.py has produced data/tier_z_scores_full.csv
# Step 2: merge + build PGLS input
# Step 3: run R PGLS for all 33 responses
# Step 4+5: produce comparison table and interpretation

set -e
cd /home/hmacgregor/BERIL-research-observatory

TIER_CSV="projects/comprehensive_metal_ecology/data/tier_z_scores_full.csv"

if [ ! -f "$TIER_CSV" ]; then
    echo "ERROR: $TIER_CSV not found. Run compute_tier_z_scores.py in JupyterHub first."
    exit 1
fi

echo "=== Step 2: Merging tier z-scores with env niche PGLS input ==="
python3 - << 'PYEOF'
import pandas as pd
from pathlib import Path

DATA = Path('projects/comprehensive_metal_ecology')
tier  = pd.read_csv(DATA / 'data/tier_z_scores_full.csv')
env   = pd.read_csv(DATA / 'results/env_niche_all_pgls_input.csv')

merged = env.merge(tier[['genus_lower','ko_per_mb_tier1_z','ko_per_mb_tier2_z']],
                   on='genus_lower', how='inner')
merged.to_csv(DATA / 'results/env_niche_tier_pgls_full_input.csv', index=False)
print(f"Merged PGLS input: {len(merged)} genera")
print(f"  (env niche: {len(env)}, tier: {len(tier)}, overlap: {len(merged)})")
PYEOF

echo ""
echo "=== Step 3: Running R PGLS for all 33 responses ==="
OMP_NUM_THREADS=1 /home/hmacgregor/r_env/bin/Rscript \
    projects/comprehensive_metal_ecology/results/env_niche_tier_pgls_full.R \
    2>&1 | tee /tmp/env_niche_tier_pgls_full.log

echo ""
echo "=== Step 4+5: Comparison table and interpretation ==="
python3 - << 'PYEOF'
import pandas as pd
import numpy as np

DATA = 'projects/comprehensive_metal_ecology/results'

# Load full-n results
full = pd.read_csv(f'{DATA}/env_niche_tier_pgls_full_results.csv')
n386 = pd.read_csv(f'{DATA}/env_niche_tier_pgls_results.csv')

def pivot_wide(df, suffix):
    t1 = df[df['predictor']=='ko_per_mb_tier1_z'].set_index('response')[['n','lambda','beta','SE','p']]
    t2 = df[df['predictor']=='ko_per_mb_tier2_z'].set_index('response')[['beta','SE','p']]
    t1.columns = [f'n{suffix}', f'lam{suffix}', f'b_r{suffix}', f'se_r{suffix}', f'p_r{suffix}']
    t2.columns = [f'b_c{suffix}', f'se_c{suffix}', f'p_c{suffix}']
    return t1.join(t2)

w_full = pivot_wide(full, '_full')
w_386  = pivot_wide(n386, '_386')

wide = w_full.join(w_386, how='left').reset_index()

def classify(pr, pc):
    r = pr < 0.05; c = pc < 0.05
    if r and c:  return "both"
    if c and not r: return "cofactor_only"
    if r and not c: return "resist_only"
    return "neither"

wide['outcome_full'] = wide.apply(lambda r: classify(r['p_r_full'], r['p_c_full']), axis=1)
wide['outcome_386']  = wide.apply(lambda r: classify(r['p_r_386'],  r['p_c_386']),  axis=1)
wide['changed']      = wide['outcome_full'] != wide['outcome_386']

# Print comparison table
print("\n=== COMPARISON TABLE (full n vs n=386) ===")
cols = ['response','n_full','b_r_full','p_r_full','b_c_full','p_c_full',
        'p_r_386','p_c_386','outcome_full','outcome_386','changed']
print(wide[cols].to_string(index=False, float_format='{:.4f}'.format))

print("\n=== OUTCOME COUNTS (full n) ===")
print(wide['outcome_full'].value_counts())
print("\n=== OUTCOME COUNTS (n=386) ===")
print(wide['outcome_386'].value_counts())
print(f"\n=== RESPONSES WHERE OUTCOME CHANGED: {wide['changed'].sum()} ===")
print(wide[wide['changed']][['response','outcome_386','outcome_full',
                              'p_r_full','p_c_full']].to_string(index=False))

# Significant cofactor responses (full n)
sig_cof = wide[wide['p_c_full']<0.05]
print(f"\nSignificant cofactor (p<0.05) at full n: {len(sig_cof)}")
for _, r in sig_cof.iterrows():
    print(f"  {r['response']}: β_c={r['b_c_full']:.4f} p_c={r['p_c_full']:.4f} | β_r={r['b_r_full']:.4f} p_r={r['p_r_full']:.4f}")

sig_res = wide[wide['p_r_full']<0.05]
print(f"\nSignificant resistance (p<0.05) at full n: {len(sig_res)}")
for _, r in sig_res.iterrows():
    print(f"  {r['response']}: β_r={r['b_r_full']:.4f} p_r={r['p_r_full']:.4f} | β_c={r['b_c_full']:.4f} p_c={r['p_c_full']:.4f}")

wide.to_csv(f'{DATA}/env_niche_tier_comparison.csv', index=False)
print(f"\nSaved env_niche_tier_comparison.csv")
PYEOF

echo ""
echo "=== Pipeline complete ==="

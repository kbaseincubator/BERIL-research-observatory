#!/usr/bin/env python3
"""
Propensity score matching for KO×metal pairs.
Match high-metal and low-metal sites on environmental covariates,
then test KO prevalence difference with paired Wilcoxon.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUT = CME / 'confound_results'

MIN_GENOMES_PER_GENUS = 8
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
PS_COVARIATES = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
                 'mean_annual_temp_C', 'mean_annual_precip_mm']

metal_col_map = {
    'Hg': 'PF1_Hg', 'As': 'PF1_As', 'Cu': 'PF1_Cu',
    'Cr': 'PF1_Cr', 'Cd': 'PF1_Cd', 'Pb': 'PF1_Pb'
}

# Target pairs: top 10 Hg, top 5 As/Cu/Cd
TARGET_PAIRS = [
    ('K01547','Hg'), ('K01546','Hg'), ('K01548','Hg'), ('K01535','Hg'),
    ('K06207','Hg'), ('K07646','Hg'), ('K02863','Hg'), ('K00525','Hg'),
    ('K03073','Hg'), ('K07223','Hg'),
    ('K01547','As'), ('K01548','As'), ('K01546','As'), ('K12141','As'), ('K01535','As'),
    ('K12141','Cu'), ('K02075','Cu'), ('K12140','Cu'), ('K02077','Cu'), ('K08482','Cu'),
    ('K02886','Cd'), ('K03043','Cd'), ('K02982','Cd'), ('K02874','Cd'), ('K02906','Cd'),
]

# ── Load data ────────────────────────────────────────────────────────
print("Loading data...")
needed_kos = list(set(ko for ko, _ in TARGET_PAIRS))

mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols_file = [c for c in env_full.columns if c not in ('latitude', 'longitude', 'genome_id')]
genome_meta = genome_meta.merge(env_full[['genome_id'] + env_cols_file], on='genome_id', how='left')

ko_wide = mg[mg.ko_id.isin(needed_kos)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()
del mg, ko_wide

genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index.tolist()
genus_idx = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera}
print(f"  Genomes: {len(genome_df):,}, usable genera: {len(usable_genera)}")

# ── Propensity score matching per genus ──────────────────────────────
print("\nRunning propensity score matching...")

def propensity_match_genus(sub, metal_col, ko_col):
    """Within one genus: split by median metal, match on propensity score, test KO."""
    y_metal = sub[metal_col].values
    ko = sub[ko_col].values
    cov_vals = sub[PS_COVARIATES].values

    mask = np.isfinite(y_metal) & np.all(np.isfinite(cov_vals), axis=1)
    if mask.sum() < 10:
        return None

    y_m = y_metal[mask]
    ko_m = ko[mask]
    cov_m = cov_vals[mask]

    median_metal = np.median(y_m)
    high = y_m > median_metal
    low = y_m <= median_metal
    if high.sum() < 3 or low.sum() < 3:
        return None

    scaler = StandardScaler()
    cov_scaled = scaler.fit_transform(cov_m)

    treatment = high.astype(int)
    try:
        lr = LogisticRegression(max_iter=1000, solver='lbfgs')
        lr.fit(cov_scaled, treatment)
        ps = lr.predict_proba(cov_scaled)[:, 1]
    except Exception:
        return None

    # Greedy 1:1 nearest-neighbor matching without replacement
    high_idx = np.where(high)[0]
    low_idx = np.where(low)[0]
    matched_high = []
    matched_low = []
    used_low = set()
    for hi in high_idx:
        dists = np.abs(ps[hi] - ps[low_idx])
        order = np.argsort(dists)
        for o in order:
            li = low_idx[o]
            if li not in used_low:
                matched_high.append(hi)
                matched_low.append(li)
                used_low.add(li)
                break

    if len(matched_high) < 3:
        return None

    ko_high = ko_m[matched_high]
    ko_low = ko_m[matched_low]
    diff = ko_high - ko_low

    if np.all(diff == 0):
        return {'stat': 0, 'p': 1.0, 'n_pairs': len(matched_high),
                'mean_diff': 0.0, 'ps_balance': 0.0}

    try:
        stat, p = stats.wilcoxon(ko_high, ko_low, alternative='two-sided')
    except Exception:
        return None

    ps_high = ps[matched_high]
    ps_low = ps[matched_low]
    ps_balance = np.mean(np.abs(ps_high - ps_low))

    return {'stat': stat, 'p': p, 'n_pairs': len(matched_high),
            'mean_diff': np.mean(diff), 'ps_balance': ps_balance}


results = []
for ko_id, metal_short in TARGET_PAIRS:
    metal_col = metal_col_map[metal_short]
    if ko_id not in genome_df.columns:
        print(f"  {ko_id} × {metal_short}: KO not in data — skipping")
        continue

    genus_results = []
    for genus in usable_genera:
        idx = genus_idx[genus]
        sub = genome_df.iloc[idx]
        res = propensity_match_genus(sub, metal_col, ko_id)
        if res is not None:
            genus_results.append(res)

    if not genus_results:
        print(f"  {ko_id} × {metal_short}: no genera with enough data")
        continue

    # Meta-analysis: combine p-values via Fisher's method
    pvals = [r['p'] for r in genus_results]
    total_pairs = sum(r['n_pairs'] for r in genus_results)
    mean_balance = np.mean([r['ps_balance'] for r in genus_results])
    mean_diff = np.mean([r['mean_diff'] for r in genus_results])

    # Fisher's combined p
    chi2 = -2 * np.sum(np.log(np.maximum(pvals, 1e-300)))
    combined_p = stats.chi2.sf(chi2, df=2 * len(pvals))

    # Count genera where p < 0.05
    n_sig_genera = sum(1 for p in pvals if p < 0.05)

    results.append({
        'ko_id': ko_id, 'metal': metal_short,
        'n_genera_tested': len(genus_results),
        'n_genera_sig': n_sig_genera,
        'total_matched_pairs': total_pairs,
        'mean_ko_diff': mean_diff,
        'mean_ps_balance': mean_balance,
        'fisher_chi2': chi2,
        'fisher_p': combined_p,
    })

    print(f"  {ko_id} × {metal_short}: {len(genus_results)} genera, "
          f"{n_sig_genera} sig, Fisher p={combined_p:.2e}, "
          f"mean_diff={mean_diff:+.3f}, balance={mean_balance:.3f}")

# FDR correction
res_df = pd.DataFrame(results)
if len(res_df) > 0:
    _, fdr, _, _ = multipletests(res_df.fisher_p, method='fdr_bh')
    res_df['fisher_q'] = fdr

    res_df.to_csv(OUT / 'propensity_score_matching.csv', index=False)
    print(f"\nSaved to {OUT / 'propensity_score_matching.csv'}")

    print(f"\n{'='*60}")
    print("RESULTS: Propensity Score Matching")
    print(f"{'='*60}")

    for metal in ['Hg', 'As', 'Cu', 'Cd']:
        sub = res_df[res_df.metal == metal]
        if len(sub) == 0:
            continue
        n_survive = (sub.fisher_q < 0.05).sum()
        print(f"\n  {metal}: {n_survive}/{len(sub)} pairs survive FDR<0.05 after PS matching")
        for _, r in sub.iterrows():
            sig = '*' if r.fisher_q < 0.05 else ' '
            print(f"    {sig} {r.ko_id}: Fisher q={r.fisher_q:.2e}, "
                  f"diff={r.mean_ko_diff:+.3f}, {r.n_genera_tested}g/{r.total_matched_pairs}p")

    total_survive = (res_df.fisher_q < 0.05).sum()
    print(f"\n  TOTAL: {total_survive}/{len(res_df)} pairs survive FDR<0.05")

print("\nDONE")

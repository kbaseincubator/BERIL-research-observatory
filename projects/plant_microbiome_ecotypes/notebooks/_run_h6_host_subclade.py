#!/usr/bin/env python3
"""H6 closure: full 18-species subclade x host test, with permutation chi² + within-species correction."""
import os, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data'

sub = pd.read_csv(f'{DATA}/species_subclade_definitions_full.csv')
host = pd.read_csv(f'{DATA}/genome_host_species.csv')[['genome_id','host_species']].drop_duplicates()

# Merge on fixed ID (subclade defs use bare NCBI accessions, host uses GTDB-prefixed)
m = sub.merge(host.rename(columns={'genome_id':'genome_id_fixed'}),
             on='genome_id_fixed', how='left')
print(f'Merged: {len(m):,} rows ({m["host_species"].notna().sum():,} with host annotation)')

# Per-species test
results = []
np.random.seed(42)
n_perms = 1000

for sp_id in m['gtdb_species_clade_id'].unique():
    d = m[m['gtdb_species_clade_id'] == sp_id]
    with_host = d[d['host_species'].notna()].copy()

    if len(with_host) < 5 or with_host['host_species'].nunique() < 2 or with_host['subclade'].nunique() < 2:
        results.append({
            'species': sp_id,
            'n_with_host': int(len(with_host)),
            'n_hosts': int(with_host['host_species'].nunique()) if len(with_host) else 0,
            'n_subclades_with_host': int(with_host['subclade'].nunique()) if len(with_host) else 0,
            'chi2_perm_p': np.nan, 'min_E': np.nan, 'frac_E_below_5': np.nan,
            'cochran_ok': False,
            'fisher_best_p': np.nan, 'fisher_best_p_bonf_within': np.nan,
            'n_pairs_tested': 0, 'best_pair': '',
            'testable': False,
        })
        continue

    ct = pd.crosstab(with_host['subclade'], with_host['host_species'])
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        results.append({
            'species': sp_id,
            'n_with_host': int(len(with_host)),
            'n_hosts': int(with_host['host_species'].nunique()),
            'n_subclades_with_host': int(with_host['subclade'].nunique()),
            'chi2_perm_p': np.nan, 'min_E': np.nan, 'frac_E_below_5': np.nan,
            'cochran_ok': False,
            'fisher_best_p': np.nan, 'fisher_best_p_bonf_within': np.nan,
            'n_pairs_tested': 0, 'best_pair': '',
            'testable': False,
        })
        continue

    # Chi² with Cochran flag
    chi2_obs, chi2_p_param, _, expected = stats.chi2_contingency(ct)
    min_E = float(expected.min())
    frac_low = float((expected < 5).sum() / expected.size)
    cochran_ok = (frac_low <= 0.20) and (min_E >= 1)

    # Permutation chi² (valid even when Cochran fails): permute host labels within species
    sub_arr = with_host['subclade'].values
    host_arr = with_host['host_species'].values
    perm_chi2 = []
    for _ in range(n_perms):
        host_shuf = np.random.permutation(host_arr)
        ct_perm = pd.crosstab(pd.Series(sub_arr), pd.Series(host_shuf))
        if ct_perm.shape[0] >= 2 and ct_perm.shape[1] >= 2:
            chi2_p, _, _, _ = stats.chi2_contingency(ct_perm)
            perm_chi2.append(chi2_p)
    perm_chi2 = np.array(perm_chi2)
    chi2_perm_p = (np.sum(perm_chi2 >= chi2_obs) + 1) / (len(perm_chi2) + 1) if len(perm_chi2) else np.nan

    # 2x2 collapsed Fisher across all (subclade, host) pairs, with within-species Bonferroni
    n_pairs = ct.shape[0] * ct.shape[1]
    best_p = 1.0
    best_pair = None
    for sc in ct.index:
        for h in ct.columns:
            a = int(ct.loc[sc, h])
            row_sum = int(ct.loc[sc].sum())
            col_sum = int(ct[h].sum())
            tot = int(ct.values.sum())
            b = row_sum - a
            c = col_sum - a
            dd = tot - a - b - c
            if a < 1: continue
            _, p = stats.fisher_exact([[a, b], [c, dd]])
            if p < best_p:
                best_p = p
                best_pair = (sc, h, a, b, c, dd)
    fisher_bonf = min(1.0, best_p * n_pairs)

    results.append({
        'species': sp_id,
        'n_with_host': int(len(with_host)),
        'n_hosts': int(with_host['host_species'].nunique()),
        'n_subclades_with_host': int(with_host['subclade'].nunique()),
        'chi2_perm_p': float(chi2_perm_p), 'min_E': min_E, 'frac_E_below_5': frac_low,
        'cochran_ok': bool(cochran_ok),
        'fisher_best_p': float(best_p),
        'fisher_best_p_bonf_within': float(fisher_bonf),
        'n_pairs_tested': int(n_pairs),
        'best_pair': str(best_pair) if best_pair else '',
        'testable': True,
    })

res = pd.DataFrame(results)

# Across-species correction (BH-FDR + Bonferroni) on the more-conservative within-species-corrected Fisher p
testable = res[res['testable']==True].copy()
n_test = len(testable)
if n_test > 0:
    bonf_alpha = 0.05 / n_test
    _, q_bh, _, _ = multipletests(testable['fisher_best_p_bonf_within'].values, method='fdr_bh')
    testable['fisher_q_bh_across'] = q_bh
    testable['passes_bonferroni_across'] = testable['fisher_best_p_bonf_within'] < bonf_alpha
    res = res.merge(testable[['species','fisher_q_bh_across','passes_bonferroni_across']],
                   on='species', how='left')

# Print
print(f'\n=== H6 Subclade × Host (full 18 species, 2026-04-25) ===')
print(f'  primary p: Fisher 2x2 best-pair, Bonferroni-corrected within species (S × H pairs tested)')
print(f'  across-species correction: BH-FDR + Bonferroni on the within-corrected p\n')
print(f'{"Species":<32} {"n":>4} {"hosts":>5} {"subc":>4} {"pairs":>5} {"raw p":>9} {"within p":>9} {"q BH":>9} {"Bonf":>5}')
print('-'*100)
testable_sorted = res[res['testable']==True].sort_values('fisher_best_p_bonf_within')
for _, r in testable_sorted.iterrows():
    sp_short = r['species'].split('--')[0].replace('s__','')[:31]
    bonf = '***' if r.get('passes_bonferroni_across', False) else ''
    print(f'{sp_short:<32} {r["n_with_host"]:>4.0f} {r["n_hosts"]:>5.0f} '
          f'{r["n_subclades_with_host"]:>4.0f} {r["n_pairs_tested"]:>5.0f} '
          f'{r["fisher_best_p"]:>9.2e} {r["fisher_best_p_bonf_within"]:>9.2e} '
          f'{r.get("fisher_q_bh_across", np.nan):>9.2e} {bonf:>5}')

# Summary
print(f'\n=== Summary ===')
print(f'Species testable: {n_test}')
sig_within = (testable_sorted['fisher_best_p_bonf_within'] < 0.05).sum()
sig_within_bh = (testable_sorted.get('fisher_q_bh_across', pd.Series([1.0]*len(testable_sorted))) < 0.05).sum()
sig_within_bonf = (testable_sorted.get('passes_bonferroni_across', pd.Series([False]*len(testable_sorted)))).sum()
print(f'  Within-species Bonferroni-corrected p<0.05: {sig_within}/{n_test}')
print(f'  + Across-species BH-FDR q<0.05: {sig_within_bh}/{n_test}')
print(f'  + Across-species Bonferroni (α={0.05/n_test:.4f}): {sig_within_bonf}/{n_test}')

if sig_within_bonf > 0:
    sig_set = testable_sorted[testable_sorted.get('passes_bonferroni_across', False)]
    print(f'\nSpecies with robust H6 evidence (both corrections):')
    for _, r in sig_set.iterrows():
        sp_short = r['species'].split('--')[0].replace('s__','')
        print(f'  {sp_short}: best subclade-host pair {r["best_pair"]}')

out = f'{DATA}/h6_host_subclade_full.csv'
res.to_csv(out, index=False)
print(f'\nSaved: {out}')

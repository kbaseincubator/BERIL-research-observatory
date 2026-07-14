#!/usr/bin/env python3
"""C1 closure: cluster-robust GLM (cluster=genus) for marker phylo control.

Replaces NB14 Cell 2's L1-regularized logit (suggestive, not confirmatory)
with frequentist Logit + cluster-robust SEs at genus level. This is the
pragmatic stand-in for a full PGLMM: it accounts for within-genus
correlation without estimating a random-effect covariance, which would
need a 2000-genus tree we don't have in tractable form.
"""
import os, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import Binomial
from statsmodels.tools import add_constant
from statsmodels.stats.multitest import multipletests

DATA = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data'

# Load same data NB14 Cell 2 used
markers = pd.read_csv(f'{DATA}/species_marker_matrix_v2.csv')
sp_comp = pd.read_csv(f'{DATA}/species_compartment.csv',
                     usecols=['gtdb_species_clade_id','genus','phylum','is_plant_associated'])
pangenome = pd.read_csv(f'{DATA}/pangenome_stats.csv',
                       usecols=['gtdb_species_clade_id','no_gene_clusters'])

# Merge
sp = markers.merge(sp_comp, on='gtdb_species_clade_id', how='inner')
sp = sp.merge(pangenome.rename(columns={'no_gene_clusters':'genome_size'}),
             on='gtdb_species_clade_id', how='inner')
sp = sp.dropna(subset=['is_plant_associated','genome_size','genus','phylum'])
sp['is_plant'] = sp['is_plant_associated'].astype(int)
sp['genome_size_log'] = np.log10(sp['genome_size'].clip(lower=1))

print(f'Species with full covariates: {len(sp):,}')
print(f'  plant-associated: {sp["is_plant"].sum():,}')
print(f'  genera: {sp["genus"].nunique():,}')

# Top phyla as fixed-effect dummies (more conservative phylogenetic control than NB14's top-20 genera)
top_phyla = sp['phylum'].value_counts().head(10).index.tolist()
sp['phylum_group'] = sp['phylum'].where(sp['phylum'].isin(top_phyla), 'other')
phylum_dummies = pd.get_dummies(sp['phylum_group'], prefix='phylum', drop_first=True)

# Design: is_plant + log10(genome_size) + phylum dummies
# Cluster = genus (random effect proxy via cluster-robust SEs)
X_design = pd.concat([sp[['is_plant','genome_size_log']].reset_index(drop=True),
                    phylum_dummies.reset_index(drop=True)], axis=1).astype(float)
X = add_constant(X_design.values)
genus_arr = sp['genus'].values
n_clusters = sp['genus'].nunique()

print(f'\nDesign matrix: {X.shape} (constant + is_plant + genome_size + {phylum_dummies.shape[1]} phylum dummies)')
print(f'Cluster groups (genus): {n_clusters:,}')

marker_cols = [c for c in markers.columns if c.endswith('_present')]
results = []

for marker in marker_cols:
    y = sp[marker].values.astype(int)
    n_pos = int(y.sum())
    if n_pos < 30 or (len(y) - n_pos) < 30:
        results.append({'marker': marker.replace('_present',''), 'n_pos': n_pos,
                       'coef_plant': np.nan, 'se_plant_robust': np.nan, 'p_plant': np.nan,
                       'or_plant': np.nan, 'survives': False, 'note': 'insufficient positives'})
        continue

    try:
        # GLM with cluster-robust covariance (genus)
        m = GLM(y, X, family=Binomial()).fit(cov_type='cluster', cov_kwds={'groups': genus_arr})
        coef_plant = float(m.params[1])  # index 1 is is_plant (after const)
        se_robust = float(m.bse[1])
        p_plant = float(m.pvalues[1])
        results.append({
            'marker': marker.replace('_present',''),
            'n_pos': n_pos,
            'coef_plant': coef_plant,
            'se_plant_robust': se_robust,
            'p_plant': p_plant,
            'or_plant': float(np.exp(coef_plant)),
            'ci_lo': float(np.exp(coef_plant - 1.96*se_robust)),
            'ci_hi': float(np.exp(coef_plant + 1.96*se_robust)),
            'survives': p_plant < 0.05 and coef_plant > 0,
            'note': '',
        })
    except Exception as e:
        results.append({'marker': marker.replace('_present',''), 'n_pos': n_pos,
                       'coef_plant': np.nan, 'se_plant_robust': np.nan, 'p_plant': np.nan,
                       'or_plant': np.nan, 'survives': False, 'note': str(e)[:60]})

res = pd.DataFrame(results)

# BH-FDR across testable markers
valid = res['p_plant'].notna()
res['q_plant_bh'] = np.nan
if valid.sum() > 0:
    _, q, _, _ = multipletests(res.loc[valid,'p_plant'].values, method='fdr_bh')
    res.loc[valid,'q_plant_bh'] = q

res['survives_strict'] = (res['coef_plant'] > 0) & (res['q_plant_bh'] < 0.05) & (res['coef_plant'].abs() > 0.2)

# Sort by coefficient
res_sorted = res.sort_values('coef_plant', ascending=False, na_position='last')

print('\n=== Cluster-robust GLM (cluster=genus) for 17 refined markers ===')
print(f'{"Marker":<28} {"N+":>6} {"Coef":>7} {"SE":>6} {"OR":>6} {"95% CI":>16} {"p":>10} {"q_BH":>10} {"Sig":>5}')
print('-'*110)
for _, r in res_sorted.iterrows():
    if pd.isna(r['coef_plant']):
        print(f'{r["marker"]:<28} {r["n_pos"]:>6} {"":>7} {"":>6} {"":>6} {"":>16} {"":>10} {"":>10} {r["note"]:>5}')
    else:
        ci = f'[{r["ci_lo"]:.2f}, {r["ci_hi"]:.2f}]'
        sig = '***' if r['survives_strict'] else ('*' if r['p_plant'] < 0.05 else '')
        print(f'{r["marker"]:<28} {r["n_pos"]:>6} {r["coef_plant"]:>7.3f} {r["se_plant_robust"]:>6.3f} '
              f'{r["or_plant"]:>6.2f} {ci:>16} {r["p_plant"]:>10.2e} {r["q_plant_bh"]:>10.2e} {sig:>5}')

n_sig_robust = res['survives_strict'].sum()
n_total = res['p_plant'].notna().sum()
print(f'\nMarkers significant (cluster-robust, q<0.05 BH-FDR, |coef|>0.2): {n_sig_robust}/{n_total}')

# Compare to NB14 L1-bootstrap result
print(f'\n=== Comparison to NB14 L1-bootstrap result ===')
l1 = pd.read_csv(f'{DATA}/regularized_phylo_control.csv')
print(f'NB14 L1-bootstrap "significant" markers: {l1["significant"].sum()}/{len(l1)}')
merged = res.merge(l1[['marker','coef_plant','significant']].rename(
    columns={'coef_plant':'l1_coef','significant':'l1_sig'}), on='marker', how='left')
print(f'\n{"Marker":<28} {"L1 coef":>8} {"L1 sig":>7} {"Robust coef":>12} {"Robust sig":>11} {"Agree":>6}')
for _, r in merged.dropna(subset=['coef_plant']).sort_values('coef_plant', ascending=False).iterrows():
    agree = '✓' if (bool(r['survives_strict']) == bool(r['l1_sig'])) else '✗'
    print(f'{r["marker"]:<28} {r["l1_coef"]:>8.3f} {str(r["l1_sig"]):>7} '
          f'{r["coef_plant"]:>12.3f} {str(r["survives_strict"]):>11} {agree:>6}')

out = f'{DATA}/c1_cluster_robust.csv'
res.to_csv(out, index=False)
print(f'\nSaved: {out}')

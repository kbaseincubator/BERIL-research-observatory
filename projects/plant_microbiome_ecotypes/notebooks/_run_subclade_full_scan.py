#!/usr/bin/env python3
"""Full 65-species subclade × plant-association scan (closes item 19)."""
import os, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.cluster import AgglomerativeClustering
from sklearn.manifold import MDS
from statsmodels.stats.multitest import multipletests

from pyspark.sql.connect.session import SparkSession

DATA='/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data'
token = os.environ['KBASE_AUTH_TOKEN']
url = f'sc://jupyter-aparkin.jupyterhub-prod:15002/;use_ssl=false;x-kbase-token={token}'
spark = SparkSession.builder.remote(url).getOrCreate()
print('Spark connected')

# Identify plant-associated species with >=20 genomes
ge = pd.read_csv(f'{DATA}/genome_environment.csv',
                 usecols=['genome_id','gtdb_species_clade_id','is_plant_associated'])
sp_comp = pd.read_csv(f'{DATA}/species_compartment.csv')
plant_sp = sp_comp[sp_comp['is_plant_associated']==True]['gtdb_species_clade_id'].unique()
gc_per_sp = ge[ge['gtdb_species_clade_id'].isin(plant_sp)].groupby('gtdb_species_clade_id').size()
target_species = gc_per_sp[gc_per_sp >= 20].sort_values(ascending=False).index.tolist()
print(f'Plant species with >=20 genomes: {len(target_species)}')

def fix_genome_id(gid):
    if gid.startswith('GCA_'): return 'GB_' + gid
    if gid.startswith('GCF_'): return 'RS_' + gid
    return gid

# Pull all subclade assignments + run tests
all_subclades_rows = []
test_rows = []

for i, sp_id in enumerate(target_species):
    print(f'[{i+1}/{len(target_species)}] {sp_id.split("--")[0].replace("s__","")[:40]}', end=' ')

    # Query phylogenetic distances for this species
    phylo_dist = spark.sql(f"""
        SELECT pd.genome1_id, pd.genome2_id, pd.branch_distance
        FROM kbase_ke_pangenome.phylogenetic_tree_distance_pairs pd
        JOIN kbase_ke_pangenome.phylogenetic_tree pt
             ON pd.phylogenetic_tree_id = pt.phylogenetic_tree_id
        WHERE pt.gtdb_species_clade_id = '{sp_id}'
    """).toPandas()

    if len(phylo_dist) == 0:
        print('NO PHYLO DATA')
        continue

    genomes = sorted(set(phylo_dist['genome1_id']) | set(phylo_dist['genome2_id']))
    n_genomes = len(genomes)
    if n_genomes < 10:
        print(f'too few genomes ({n_genomes})')
        continue

    # Build distance matrix
    g_idx = {g: i for i, g in enumerate(genomes)}
    D = np.zeros((n_genomes, n_genomes))
    for _, r in phylo_dist.iterrows():
        i_, j_ = g_idx.get(r['genome1_id']), g_idx.get(r['genome2_id'])
        if i_ is not None and j_ is not None:
            D[i_, j_] = r['branch_distance']
            D[j_, i_] = r['branch_distance']

    # Cluster: 3 subclades, average linkage
    n_clusters = min(3, max(2, n_genomes // 15))
    clustering = AgglomerativeClustering(n_clusters=n_clusters, metric='precomputed', linkage='average')
    labels = clustering.fit_predict(D)

    # Apply genome ID fix and merge with env
    sub = pd.DataFrame({'genome_id': genomes, 'gtdb_species_clade_id': sp_id, 'subclade': labels})
    sub['genome_id_fixed'] = sub['genome_id'].apply(fix_genome_id)
    m = sub.merge(ge.rename(columns={'genome_id':'genome_id_fixed'})[['genome_id_fixed','is_plant_associated']],
                 on='genome_id_fixed', how='left')
    m['is_plant'] = (m['is_plant_associated']==1)

    n_plant = int(m['is_plant'].sum())
    n_nonplant = int((~m['is_plant']).sum())

    # Need at least 3 plant + 3 non-plant + 2 subclades to test
    if n_plant < 3 or n_nonplant < 3 or m['subclade'].nunique() < 2:
        test_rows.append({'species': sp_id, 'n_genomes': n_genomes, 'n_subclades': m['subclade'].nunique(),
                         'n_plant': n_plant, 'n_nonplant': n_nonplant,
                         'best_subclade': -1, 'best_plant_frac': np.nan,
                         'fisher_p': np.nan, 'chi2_p': np.nan, 'min_E': np.nan,
                         'frac_E_below_5': np.nan, 'cochran_ok': False, 'testable': False})
        all_subclades_rows.append(m)
        print(f'untestable n_plant={n_plant}, n_nonplant={n_nonplant}')
        continue

    # Chi² with Cochran check
    ct = pd.crosstab(m['subclade'], m['is_plant'])
    chi2, chi2_p, _, expected = stats.chi2_contingency(ct)
    min_E = float(expected.min())
    frac_low = float((expected < 5).sum() / expected.size)
    cochran_ok = (frac_low <= 0.20) and (min_E >= 1)  # standard Cochran rule

    # Fisher's exact on collapsed 2x2 (best-subclade vs rest)
    by_sc = m.groupby('subclade')['is_plant'].agg(['sum','size'])
    by_sc['frac'] = by_sc['sum'] / by_sc['size']
    best_sc = int(by_sc['frac'].idxmax())
    a = int(m[(m['subclade']==best_sc) & m['is_plant']].shape[0])
    b = int(m[(m['subclade']==best_sc) & (~m['is_plant'])].shape[0])
    c = int(m[(m['subclade']!=best_sc) & m['is_plant']].shape[0])
    dd= int(m[(m['subclade']!=best_sc) & (~m['is_plant'])].shape[0])
    _, fisher_p = stats.fisher_exact([[a,b],[c,dd]])

    test_rows.append({
        'species': sp_id, 'n_genomes': n_genomes, 'n_subclades': m['subclade'].nunique(),
        'n_plant': n_plant, 'n_nonplant': n_nonplant,
        'best_subclade': best_sc, 'best_plant_frac': float(by_sc.loc[best_sc, 'frac']),
        'fisher_p': float(fisher_p), 'chi2_p': float(chi2_p),
        'min_E': min_E, 'frac_E_below_5': frac_low, 'cochran_ok': bool(cochran_ok),
        'testable': True
    })
    all_subclades_rows.append(m)
    sig_mark = '***' if fisher_p < 0.05 else ''
    print(f'plant={n_plant}/{n_genomes}, fisher_p={fisher_p:.2e} {sig_mark}')

# Save results
if all_subclades_rows:
    all_sub = pd.concat(all_subclades_rows, ignore_index=True)
    all_sub.to_csv(f'{DATA}/species_subclade_definitions_full.csv', index=False)
    print(f'\nSaved: {DATA}/species_subclade_definitions_full.csv ({len(all_sub):,} genome assignments)')

test_df = pd.DataFrame(test_rows)
# BH-FDR and Bonferroni on testable species
testable = test_df[test_df['testable']].copy()
if len(testable) > 0:
    _, bh_q, _, _ = multipletests(testable['fisher_p'].values, method='fdr_bh')
    testable['fisher_q_bh'] = bh_q
    bonf_alpha = 0.05 / len(testable)
    testable['passes_bonferroni'] = testable['fisher_p'] < bonf_alpha
    test_df = test_df.merge(testable[['species','fisher_q_bh','passes_bonferroni']],
                            on='species', how='left')

test_df.to_csv(f'{DATA}/subclade_full_scan.csv', index=False)
print(f'Saved: {DATA}/subclade_full_scan.csv')

# Summary
print(f'\n=== Summary ===')
print(f'Species attempted: {len(target_species)}')
print(f'Species with phylo data: {(test_df["n_subclades"]>=2).sum()}')
testable_count = test_df['testable'].sum()
print(f'Testable (>=3 plant + >=3 non-plant): {testable_count}')
if testable_count > 0:
    sig_05 = test_df[(test_df['testable']==True) & (test_df['fisher_p']<0.05)]
    cochran = test_df[(test_df['testable']==True) & (test_df['cochran_ok']==True)]
    bh_sig = test_df[(test_df['testable']==True) & (test_df.get('fisher_q_bh', 1.0) < 0.05)]
    bonf_sig = test_df[(test_df['testable']==True) & (test_df.get('passes_bonferroni', False)==True)]
    print(f'  Fisher p<0.05 (uncorrected): {len(sig_05)}')
    print(f'  Cochran OK (chi² valid): {len(cochran)}')
    print(f'  Survives BH-FDR q<0.05: {len(bh_sig)}')
    print(f'  Survives Bonferroni (α={0.05/testable_count:.4f}): {len(bonf_sig)}')

    print(f'\nTop 10 by Fisher p:')
    top = test_df[test_df['testable']==True].nsmallest(10, 'fisher_p')
    for _, r in top.iterrows():
        sp_short = r['species'].split('--')[0].replace('s__','')[:35]
        cochran_mark = '✓' if r['cochran_ok'] else '✗'
        bonf = '*' if r.get('passes_bonferroni', False) else ''
        print(f'  {sp_short:<35} N={r["n_genomes"]:>4} plant={r["n_plant"]:>4} '
              f'fisher_p={r["fisher_p"]:.2e}  Cochran:{cochran_mark}  q={r.get("fisher_q_bh", np.nan):.2e} {bonf}')

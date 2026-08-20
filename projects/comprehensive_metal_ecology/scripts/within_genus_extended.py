#!/usr/bin/env python3
"""
Extended within-genus analysis for newly identified candidate KOs:
- Phospholipase C (plc, K01114)
- Vitamin B6 biosynthesis (pdxS/pdx1 K06215, pyridoxine dehydrogenase K05275)
- Transposases (K07497, K07486, K07484, K07480, K07481)
- Heat shock regulator (hspR, K13640)
- H+-ATPase (PMA1, K01535)
- Ceramide glucosyltransferase (K00720)
- tRNA modification (mnmC, K15461)
- Magnesium transporter (mgtE, K06213)
- Ribosomal protein (rplA, K02863)
- hypE (K04655) - missed from original set
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
OUT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')

MIN_GENOMES_PER_GENUS = 5
MIN_GENERA = 10

EXTENDED_KOS = {
    'K01114': 'plc',
    'K06215': 'pdxS/pdx1',
    'K05275': 'pdxDH',
    'K08681': 'pdxT/pdx2',
    'K07497': 'IS_transposase1',
    'K07486': 'IS_transposase2',
    'K07484': 'IS_transposase3',
    'K07480': 'insB',
    'K07481': 'IS5_transposase',
    'K13640': 'hspR',
    'K01535': 'PMA1/PMA2',
    'K00720': 'UGCG',
    'K15461': 'mnmC',
    'K06213': 'mgtE',
    'K02863': 'rplA',
    'K04655': 'hypE',
}

METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']

print("Loading genome-level matrix...")
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude'] + METALS)

mg = mg[mg.ko_id.isin(EXTENDED_KOS)].copy()
print(f"Filtered to {len(EXTENDED_KOS)} target KOs: {mg.shape[0]:,} rows")

genome_meta = mg.groupby('genome_id').first()[['genus', 'genome_size', 'latitude'] + METALS].reset_index()
ko_wide = mg.pivot_table(index='genome_id', columns='ko_id', values='present', fill_value=0).reset_index()
genome_df = genome_meta.merge(ko_wide, on='genome_id')

print(f"Genome-level table: {genome_df.shape}")
genus_counts = genome_df.genus.value_counts()
usable_genera = genus_counts[genus_counts >= MIN_GENOMES_PER_GENUS]
print(f"Genera with ≥{MIN_GENOMES_PER_GENUS} genomes: {len(usable_genera)} "
      f"({usable_genera.sum():,} genomes)")

results = []
for ko_id, gene_name in EXTENDED_KOS.items():
    if ko_id not in genome_df.columns:
        print(f"  {ko_id} ({gene_name}): not in genome matrix, skipping")
        continue

    for metal in METALS:
        metal_short = metal.replace('PF1_', '')
        genus_effects = []

        for genus, n_genomes in usable_genera.items():
            gdf = genome_df[genome_df.genus == genus].copy()
            ko_col = gdf[ko_id].values
            metal_col = gdf[metal].values

            if ko_col.std() == 0 or np.isnan(metal_col).all():
                continue
            prev = ko_col.mean()
            if prev < 0.05 or prev > 0.95:
                continue

            mask = np.isfinite(metal_col)
            if mask.sum() < MIN_GENOMES_PER_GENUS:
                continue

            try:
                rho, p = stats.pointbiserialr(ko_col[mask], metal_col[mask])
                if np.isfinite(rho):
                    se = 1.0 / np.sqrt(mask.sum() - 3) if mask.sum() > 3 else np.nan
                    genus_effects.append({
                        'genus': genus, 'n': mask.sum(), 'rho': rho, 'p': p, 'se': se
                    })
            except:
                continue

        n_genera = len(genus_effects)
        if n_genera < MIN_GENERA:
            results.append({
                'ko_id': ko_id, 'gene_name': gene_name, 'metal': metal_short,
                'n_genera': n_genera, 'n_genomes': 0,
                'meta_rho': np.nan, 'meta_z': np.nan, 'meta_p': np.nan,
                'median_within_rho': np.nan,
                'frac_positive': np.nan, 'sign_test_p': np.nan,
                'status': f'too_few_genera ({n_genera})'
            })
            continue

        gdf = pd.DataFrame(genus_effects)
        total_genomes = gdf.n.sum()
        weights = (gdf.n - 3).clip(lower=1)
        z_vals = np.arctanh(gdf.rho.clip(-0.999, 0.999))
        meta_z = np.average(z_vals, weights=weights)
        meta_se = 1.0 / np.sqrt(weights.sum())
        meta_z_stat = meta_z / meta_se
        meta_p = 2 * stats.norm.sf(abs(meta_z_stat))
        meta_rho = np.tanh(meta_z)

        frac_pos = (gdf.rho > 0).mean()
        n_pos = (gdf.rho > 0).sum()
        sign_p = stats.binomtest(n_pos, n_genera, 0.5).pvalue

        results.append({
            'ko_id': ko_id, 'gene_name': gene_name, 'metal': metal_short,
            'n_genera': n_genera, 'n_genomes': total_genomes,
            'meta_rho': meta_rho, 'meta_z': meta_z_stat, 'meta_p': meta_p,
            'median_within_rho': gdf.rho.median(),
            'frac_positive': frac_pos, 'sign_test_p': sign_p,
            'status': 'tested'
        })

results_df = pd.DataFrame(results)
tested = results_df[results_df.status == 'tested'].copy()

if len(tested) > 0:
    _, q_vals, _, _ = multipletests(tested.meta_p.values, method='fdr_bh')
    tested['q_fdr'] = q_vals
    results_df = results_df.merge(tested[['ko_id', 'metal', 'q_fdr']],
                                   on=['ko_id', 'metal'], how='left')
else:
    results_df['q_fdr'] = np.nan

print(f"\n{'='*90}")
print(f"EXTENDED WITHIN-GENUS ANALYSIS")
print(f"{'='*90}")
print(f"Tests run: {len(tested)}")
print(f"FDR < 0.05: {(tested.q_fdr < 0.05).sum()}")
print(f"FDR < 0.10: {(tested.q_fdr < 0.10).sum()}")

print(f"\n{'KO':10s} {'Gene':18s} {'Metal':4s} {'n_gen':>5s} {'n_gnm':>6s} "
      f"{'meta_ρ':>7s} {'meta_p':>10s} {'q(FDR)':>10s} {'med_ρ':>7s} "
      f"{'%pos':>5s} {'sign_p':>8s}")
print(f"{'-'*95}")

for ko_id in EXTENDED_KOS:
    ko_rows = results_df[results_df.ko_id == ko_id].sort_values('meta_p')
    for _, r in ko_rows.iterrows():
        if r.status != 'tested':
            continue
        sig = '***' if r.q_fdr < 0.001 else '**' if r.q_fdr < 0.01 else '*' if r.q_fdr < 0.05 else '†' if r.q_fdr < 0.10 else ''
        print(f"{r.ko_id:10s} {r.gene_name:18s} {r.metal:4s} {r.n_genera:5d} {r.n_genomes:6d} "
              f"{r.meta_rho:+7.4f} {r.meta_p:10.2e} {r.q_fdr:10.4f} {r.median_within_rho:+7.4f} "
              f"{r.frac_positive:5.1%} {r.sign_test_p:8.4f} {sig}")
    if ko_id in ['K05275', 'K07481', 'K13640', 'K00720', 'K06213', 'K04655']:
        print()

results_df.to_csv(OUT / 'within_genus_extended_results.csv', index=False)
print(f"\nSaved to {OUT / 'within_genus_extended_results.csv'}")
print("DONE.")

#!/usr/bin/env python3
"""
Within-genus KO × metal variation analysis.

Tests whether KO presence varies with local soil metal concentration
WITHIN genera (same genus, different environments). This separates
gene-level selection from taxonomic turnover.

Design:
  For each target KO × metal:
    1. Filter to genera with ≥N genomes and KO prevalence 5-95%
    2. Within each genus, run logistic regression: KO_present ~ metal_z
    3. Combine genus-level effects via inverse-variance meta-analysis
    4. Compare to the between-genus (community composition) effect

Data: per_ko_metal_associations MGnify genome-level matrix
  - 8,585 genomes, 6,451 KOs, 6 metals, 3,300 genera
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
OUT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
KEGG_LIST = Path('/home/hmacgregor/BERIL-research-observatory/projects/final_draft/data/kegg_ko_list.csv')

MIN_GENOMES_PER_GENUS = 5
MIN_GENERA = 10

# Target KOs: top replicated + biologically interesting
TARGET_KOS = {
    # KDP operon
    'K01546': 'kdpA', 'K01547': 'kdpB', 'K01548': 'kdpC',
    'K07646': 'kdpD', 'K07667': 'kdpE',
    # Constitutive K+ (opposite control)
    'K03498': 'trkH',
    # Pentose phosphate / oxidative stress
    'K00036': 'G6PD/zwf', 'K00033': 'PGD/gnd', 'K00384': 'trxB',
    # Hydrogenase maturation
    'K04651': 'hypA', 'K04652': 'hypB', 'K04653': 'hypC',
    'K04654': 'hypD', 'K04656': 'hypF',
    # Membrane integrity
    'K06045': 'shc', 'K06188': 'aqpZ',
    # Curated metal genes for comparison
    'K07241': 'hoxN/nixA', 'K01992': 'ABC-2.P', 'K01531': 'mgtA',
    'K20265': 'gadC', 'K08364': 'merP',
    # Cobalamin pathway (from earlier finding)
    'K02230': 'cobN', 'K09883': 'cobT', 'K02225': 'cobC1', 'K02007': 'cbiM',
}

METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']

# ── 1. Load genome-level data ───────────────────────────────────────────────
print("Loading genome-level matrix...")
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude'] + METALS)

# Filter to target KOs
mg = mg[mg.ko_id.isin(TARGET_KOS)].copy()
print(f"Filtered to {len(TARGET_KOS)} target KOs: {mg.shape[0]:,} rows")
print(f"Unique genomes: {mg.genome_id.nunique()}")
print(f"Unique genera: {mg.genus.nunique()}")

# Pivot to genome × KO wide format
genome_meta = mg.groupby('genome_id').first()[['genus', 'genome_size', 'latitude'] + METALS].reset_index()
ko_wide = mg.pivot_table(index='genome_id', columns='ko_id', values='present', fill_value=0).reset_index()
genome_df = genome_meta.merge(ko_wide, on='genome_id')

print(f"Genome-level table: {genome_df.shape}")
genus_counts = genome_df.genus.value_counts()
usable_genera = genus_counts[genus_counts >= MIN_GENOMES_PER_GENUS]
print(f"Genera with ≥{MIN_GENOMES_PER_GENUS} genomes: {len(usable_genera)} "
      f"({usable_genera.sum():,} genomes)")

# ── 2. Within-genus analysis ────────────────────────────────────────────────
results = []

for ko_id, gene_name in TARGET_KOS.items():
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

            # Need variation in both KO and metal
            if ko_col.std() == 0 or np.isnan(metal_col).all():
                continue
            prev = ko_col.mean()
            if prev < 0.05 or prev > 0.95:
                continue

            # Within-genus: point-biserial correlation
            mask = np.isfinite(metal_col)
            if mask.sum() < MIN_GENOMES_PER_GENUS:
                continue

            try:
                rho, p = stats.pointbiserialr(ko_col[mask], metal_col[mask])
                if np.isfinite(rho):
                    se = 1.0 / np.sqrt(mask.sum() - 3) if mask.sum() > 3 else np.nan
                    genus_effects.append({
                        'genus': genus, 'n': mask.sum(), 'rho': rho, 'p': p,
                        'se': se, 'prevalence': prev
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
                'frac_positive': np.nan, 'frac_sig': np.nan,
                'sign_test_p': np.nan,
                'status': f'too_few_genera ({n_genera})'
            })
            continue

        gdf = pd.DataFrame(genus_effects)
        total_genomes = gdf.n.sum()

        # Meta-analysis: inverse-variance weighted mean
        weights = gdf.n - 3  # df-based weight
        weights = weights.clip(lower=1)
        z_vals = np.arctanh(gdf.rho.clip(-0.999, 0.999))  # Fisher z
        meta_z = np.average(z_vals, weights=weights)
        meta_se = 1.0 / np.sqrt(weights.sum())
        meta_z_stat = meta_z / meta_se
        meta_p = 2 * stats.norm.sf(abs(meta_z_stat))
        meta_rho = np.tanh(meta_z)

        # Sign consistency: fraction of genera where effect is same direction
        frac_pos = (gdf.rho > 0).mean()
        frac_sig = (gdf.p < 0.05).mean()

        # Sign test: are more genera positive than expected by chance?
        n_pos = (gdf.rho > 0).sum()
        sign_p = stats.binomtest(n_pos, n_genera, 0.5).pvalue

        results.append({
            'ko_id': ko_id, 'gene_name': gene_name, 'metal': metal_short,
            'n_genera': n_genera, 'n_genomes': total_genomes,
            'meta_rho': meta_rho, 'meta_z': meta_z_stat, 'meta_p': meta_p,
            'median_within_rho': gdf.rho.median(),
            'frac_positive': frac_pos, 'frac_sig': frac_sig,
            'sign_test_p': sign_p,
            'status': 'tested'
        })

results_df = pd.DataFrame(results)
tested = results_df[results_df.status == 'tested'].copy()

# FDR correction
from statsmodels.stats.multitest import multipletests
if len(tested) > 0:
    _, q_vals, _, _ = multipletests(tested.meta_p.values, method='fdr_bh')
    tested['q_fdr'] = q_vals
    results_df = results_df.merge(tested[['ko_id', 'metal', 'q_fdr']],
                                   on=['ko_id', 'metal'], how='left')
else:
    results_df['q_fdr'] = np.nan

# ── 3. Print results ────────────────────────────────────────────────────────
print(f"\n{'='*90}")
print(f"WITHIN-GENUS KO × METAL ANALYSIS")
print(f"{'='*90}")
print(f"Target KOs tested: {len(TARGET_KOS)}")
print(f"Tests run: {len(tested)}")
print(f"FDR < 0.05: {(tested.q_fdr < 0.05).sum() if 'q_fdr' in tested.columns else 0}")
print(f"FDR < 0.10: {(tested.q_fdr < 0.10).sum() if 'q_fdr' in tested.columns else 0}")

# Show all results grouped by KO
print(f"\n{'='*90}")
print(f"{'KO':10s} {'Gene':12s} {'Metal':4s} {'n_gen':>5s} {'n_gnm':>6s} "
      f"{'meta_ρ':>7s} {'meta_p':>10s} {'q(FDR)':>10s} {'med_ρ':>7s} "
      f"{'%pos':>5s} {'sign_p':>8s}")
print(f"{'-'*90}")

for ko_id in TARGET_KOS:
    ko_rows = results_df[results_df.ko_id == ko_id].sort_values('meta_p')
    for _, r in ko_rows.iterrows():
        if r.status != 'tested':
            continue
        sig = '***' if r.q_fdr < 0.001 else '**' if r.q_fdr < 0.01 else '*' if r.q_fdr < 0.05 else '†' if r.q_fdr < 0.10 else ''
        print(f"{r.ko_id:10s} {r.gene_name:12s} {r.metal:4s} {r.n_genera:5d} {r.n_genomes:6d} "
              f"{r.meta_rho:+7.4f} {r.meta_p:10.2e} {r.q_fdr:10.4f} {r.median_within_rho:+7.4f} "
              f"{r.frac_positive:5.1%} {r.sign_test_p:8.4f} {sig}")
    # Separator between operons
    if ko_id in ['K07667', 'K03498', 'K00384', 'K04656', 'K06188', 'K08364', 'K02007']:
        print()

# ── 4. Compare between-genus vs within-genus ─────────────────────────────────
print(f"\n{'='*90}")
print(f"BETWEEN-GENUS vs WITHIN-GENUS COMPARISON")
print(f"{'='*90}")

# Load between-genus (community-level) effects
between = pd.read_csv(OUT / 'clean_ko_metal_survey_results.csv')

for ko_id, gene_name in list(TARGET_KOS.items())[:10]:
    for metal in ['Hg', 'As', 'Pb']:
        metal_full = f'PF1_{metal}'
        bw_row = between[(between.ko_id == ko_id) & (between.metal == metal_full)]
        wi_row = tested[(tested.ko_id == ko_id) & (tested.metal == metal)]

        if len(bw_row) == 0 or len(wi_row) == 0:
            continue

        bw = bw_row.iloc[0]
        wi = wi_row.iloc[0]

        bw_sig = '***' if bw.q_spearman < 0.001 else '**' if bw.q_spearman < 0.01 else '*' if bw.q_spearman < 0.05 else 'NS'
        wi_sig = '***' if wi.q_fdr < 0.001 else '**' if wi.q_fdr < 0.01 else '*' if wi.q_fdr < 0.05 else '†' if wi.q_fdr < 0.10 else 'NS'

        print(f"  {ko_id} ({gene_name:10s}) × {metal:3s}:  "
              f"BETWEEN ρ={bw.rho:+.4f} {bw_sig:4s}  |  "
              f"WITHIN ρ={wi.meta_rho:+.4f} {wi_sig:4s}  "
              f"(n_genera={wi.n_genera}, {wi.frac_positive:.0%} same dir)")

# ── 5. Save ──────────────────────────────────────────────────────────────────
results_df.to_csv(OUT / 'within_genus_ko_metal_results.csv', index=False)
print(f"\nSaved to {OUT / 'within_genus_ko_metal_results.csv'}")
print("DONE.")

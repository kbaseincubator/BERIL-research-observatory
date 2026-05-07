"""
Step 3: Core vs. accessory enrichment analysis.

For species encoding both nutrient-cycling and metal-handling gene families,
tests whether co-occurring genes concentrate in the core genome vs.
auxiliary/singleton fractions. Uses Fisher's exact test per species
with Stouffer meta-analysis.

Outputs:
  data/core_enrichment_summary.csv — per-group-pair core enrichment stats
  data/core_enrichment_per_species.csv — per-species Fisher results
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

print("Loading species gene families...")
df = pd.read_csv(os.path.join(DATA_DIR, 'species_gene_families.csv'))
print(f"Loaded {len(df)} species")

nutrient_gene_sets = {
    'P_genes': ['phoA', 'phoD_pfam', 'pstA', 'pstB', 'pstC', 'pstS', 'phnC', 'phnD', 'phnE'],
    'N_genes': ['nifH', 'nifD', 'nifH_pfam'],
    'Phz_genes': ['phzF', 'phzA', 'phzB', 'phzD', 'phzG', 'phzS', 'phzM'],
}

metal_genes = ['copA', 'corA', 'feoB_pfam', 'HMA_pfam']

print("\n=== Core vs. Accessory Enrichment ===\n")

summary_rows = []

for nutrient_label, nutrient_list in nutrient_gene_sets.items():
    nutrient_has_cols = [f'has_{g}' for g in nutrient_list if f'has_{g}' in df.columns]
    metal_has_cols = [f'has_{g}' for g in metal_genes if f'has_{g}' in df.columns]

    has_nutrient = (df[nutrient_has_cols].sum(axis=1) >= 1)
    has_metal = (df[metal_has_cols].sum(axis=1) >= 1)
    both_mask = has_nutrient & has_metal

    co_species = df[both_mask].copy()
    print(f"\n{nutrient_label} + Metal: {len(co_species)} species with both")

    nutrient_core_cols = [f'n_{g}_core' for g in nutrient_list if f'n_{g}_core' in df.columns]
    nutrient_noncore_cols = ([f'n_{g}_aux' for g in nutrient_list if f'n_{g}_aux' in df.columns] +
                            [f'n_{g}_singleton' for g in nutrient_list if f'n_{g}_singleton' in df.columns])
    metal_core_cols = [f'n_{g}_core' for g in metal_genes if f'n_{g}_core' in df.columns]
    metal_noncore_cols = ([f'n_{g}_aux' for g in metal_genes if f'n_{g}_aux' in df.columns] +
                         [f'n_{g}_singleton' for g in metal_genes if f'n_{g}_singleton' in df.columns])

    nutrient_total_cols = [f'n_{g}' for g in nutrient_list if f'n_{g}' in df.columns]
    metal_total_cols = [f'n_{g}' for g in metal_genes if f'n_{g}' in df.columns]

    co_species['nutrient_core'] = co_species[nutrient_core_cols].sum(axis=1)
    co_species['nutrient_noncore'] = co_species[nutrient_noncore_cols].sum(axis=1)
    co_species['metal_core'] = co_species[metal_core_cols].sum(axis=1)
    co_species['metal_noncore'] = co_species[metal_noncore_cols].sum(axis=1)

    total_nutrient_core = int(co_species['nutrient_core'].sum())
    total_nutrient_noncore = int(co_species['nutrient_noncore'].sum())
    total_metal_core = int(co_species['metal_core'].sum())
    total_metal_noncore = int(co_species['metal_noncore'].sum())

    nutrient_core_frac = total_nutrient_core / (total_nutrient_core + total_nutrient_noncore) if (total_nutrient_core + total_nutrient_noncore) > 0 else 0
    metal_core_frac = total_metal_core / (total_metal_core + total_metal_noncore) if (total_metal_core + total_metal_noncore) > 0 else 0

    print(f"  {nutrient_label} core fraction: {nutrient_core_frac:.3f} ({total_nutrient_core} core / {total_nutrient_core + total_nutrient_noncore} total)")
    print(f"  Metal core fraction: {metal_core_frac:.3f} ({total_metal_core} core / {total_metal_core + total_metal_noncore} total)")

    per_species_results = []
    z_scores = []

    for _, row in co_species.iterrows():
        nc = int(row['nutrient_core'])
        nnc = int(row['nutrient_noncore'])
        mc = int(row['metal_core'])
        mnc = int(row['metal_noncore'])

        if (nc + nnc) < 2 or (mc + mnc) < 2:
            continue

        ct = np.array([[nc, nnc], [mc, mnc]])
        try:
            odds_ratio, p_val = stats.fisher_exact(ct)
        except ValueError:
            continue

        if p_val > 0 and p_val < 1:
            z = stats.norm.ppf(1 - p_val / 2)
            if odds_ratio < 1:
                z = -z
            z_scores.append(z)

        per_species_results.append({
            'species_id': row['gtdb_species_clade_id'],
            'nutrient_group': nutrient_label,
            'nutrient_core': nc,
            'nutrient_noncore': nnc,
            'metal_core': mc,
            'metal_noncore': mnc,
            'odds_ratio': round(odds_ratio, 3) if odds_ratio != float('inf') else 'inf',
            'fisher_p': p_val,
        })

    if z_scores:
        stouffer_z = np.sum(z_scores) / np.sqrt(len(z_scores))
        stouffer_p = 2 * (1 - stats.norm.cdf(abs(stouffer_z)))
    else:
        stouffer_z = 0
        stouffer_p = 1

    print(f"  Species with enough data for Fisher: {len(per_species_results)}")
    print(f"  Stouffer meta-Z: {stouffer_z:.3f}")
    print(f"  Stouffer meta-p: {stouffer_p:.2e}")

    ors = [r['odds_ratio'] for r in per_species_results if r['odds_ratio'] != 'inf']
    ors_numeric = [float(x) for x in ors]
    median_or = np.median(ors_numeric) if ors_numeric else 0
    frac_enriched = np.mean([x > 1 for x in ors_numeric]) if ors_numeric else 0
    print(f"  Median OR across species: {median_or:.3f}")
    print(f"  Fraction species with OR > 1: {frac_enriched:.3f}")

    summary_rows.append({
        'nutrient_group': nutrient_label,
        'n_species_both': len(co_species),
        'n_species_testable': len(per_species_results),
        'nutrient_core_frac': round(nutrient_core_frac, 4),
        'metal_core_frac': round(metal_core_frac, 4),
        'stouffer_z': round(stouffer_z, 3),
        'stouffer_p': stouffer_p,
        'median_OR': round(median_or, 3),
        'frac_enriched': round(frac_enriched, 3),
    })

    per_sp_df = pd.DataFrame(per_species_results)
    if len(per_sp_df) > 0:
        out_sp = os.path.join(DATA_DIR, f'core_enrichment_{nutrient_label}.csv')
        per_sp_df.to_csv(out_sp, index=False)

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(os.path.join(DATA_DIR, 'core_enrichment_summary.csv'), index=False)
print(f"\nSaved core_enrichment_summary.csv")

print("\n=== Aggregate Core Fraction by Functional Group ===")
all_genes = (nutrient_gene_sets['P_genes'] + nutrient_gene_sets['N_genes'] +
             nutrient_gene_sets['Phz_genes'] + metal_genes)
for g in all_genes:
    total_col = f'n_{g}'
    core_col = f'n_{g}_core'
    if total_col in df.columns and core_col in df.columns:
        total = int(df[total_col].sum())
        core = int(df[core_col].sum())
        frac = core / total if total > 0 else 0
        print(f"  {g:>12s}: {core:>8d} core / {total:>8d} total = {frac:.3f}")

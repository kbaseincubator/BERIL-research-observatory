"""
Step 2: Co-occurrence matrix and statistical testing.

Computes Jaccard index, phi coefficient, and Fisher's exact test for
pairwise associations between gene family groups. Tests against a
permutation null that shuffles group labels within species.

Outputs:
  data/cooccurrence_matrix.csv — pairwise statistics
  data/pairwise_detail.csv — per-gene-family pair statistics
  data/contingency_tables.txt — 2x2 tables for key comparisons
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from itertools import combinations

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

print("Loading species gene families...")
df = pd.read_csv(os.path.join(DATA_DIR, 'species_gene_families.csv'))
print(f"Loaded {len(df)} species, {len(df.columns)} columns")

groups = {
    'P_acquisition': ['phoA', 'phoD_pfam', 'pstA', 'pstB', 'pstC', 'pstS', 'phnC', 'phnD', 'phnE'],
    'N_fixation': ['nifH', 'nifD', 'nifH_pfam'],
    'Metal_handling': ['copA', 'corA', 'feoB_pfam', 'HMA_pfam'],
    'Phenazine': ['phzF', 'phzA', 'phzB', 'phzD', 'phzG', 'phzS', 'phzM'],
}

group_has = {}
for gname, genes in groups.items():
    cols = [f'has_{g}' for g in genes if f'has_{g}' in df.columns]
    group_has[gname] = (df[cols].sum(axis=1) >= 1).astype(int).values

phz_operon = df['has_phz_operon'].values if 'has_phz_operon' in df.columns else (group_has['Phenazine'] >= 1)
group_has['Phenazine_operon'] = phz_operon


def jaccard(a, b):
    both = np.sum((a == 1) & (b == 1))
    either = np.sum((a == 1) | (b == 1))
    return both / either if either > 0 else 0.0


def phi_coefficient(a, b):
    n11 = np.sum((a == 1) & (b == 1))
    n10 = np.sum((a == 1) & (b == 0))
    n01 = np.sum((a == 0) & (b == 1))
    n00 = np.sum((a == 0) & (b == 0))
    denom = np.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denom == 0:
        return 0.0
    return (n11 * n00 - n10 * n01) / denom


def contingency_2x2(a, b):
    n11 = int(np.sum((a == 1) & (b == 1)))
    n10 = int(np.sum((a == 1) & (b == 0)))
    n01 = int(np.sum((a == 0) & (b == 1)))
    n00 = int(np.sum((a == 0) & (b == 0)))
    return np.array([[n11, n10], [n01, n00]])


print("\n=== Group-Level Co-occurrence ===\n")

results = []
contingency_text = []

group_names = list(group_has.keys())
for g1, g2 in combinations(group_names, 2):
    a, b = group_has[g1], group_has[g2]
    j = jaccard(a, b)
    phi = phi_coefficient(a, b)
    ct = contingency_2x2(a, b)
    odds_ratio, fisher_p = stats.fisher_exact(ct)

    n_a = int(np.sum(a))
    n_b = int(np.sum(b))
    n_both = int(ct[0, 0])
    n_total = len(a)

    expected = (n_a / n_total) * (n_b / n_total) * n_total
    enrichment = n_both / expected if expected > 0 else float('inf')

    results.append({
        'group_A': g1,
        'group_B': g2,
        'n_A': n_a,
        'n_B': n_b,
        'n_both': n_both,
        'n_neither': int(ct[1, 1]),
        'expected_both': round(expected, 1),
        'enrichment_ratio': round(enrichment, 3),
        'jaccard': round(j, 4),
        'phi': round(phi, 4),
        'odds_ratio': round(odds_ratio, 3) if odds_ratio != float('inf') else 'inf',
        'fisher_p': fisher_p,
    })

    ct_str = (
        f"\n--- {g1} vs {g2} ---\n"
        f"              {g2}=1    {g2}=0\n"
        f"  {g1}=1    {ct[0,0]:>8d}  {ct[0,1]:>8d}  | {n_a}\n"
        f"  {g1}=0    {ct[1,0]:>8d}  {ct[1,1]:>8d}  | {n_total - n_a}\n"
        f"             {n_b:>8d}  {n_total - n_b:>8d}  | {n_total}\n"
        f"  Jaccard={j:.4f}  Phi={phi:.4f}  OR={odds_ratio:.3f}  Fisher p={fisher_p:.2e}\n"
        f"  Expected both={expected:.1f}  Observed={n_both}  Enrichment={enrichment:.2f}x\n"
    )
    contingency_text.append(ct_str)
    print(ct_str)

res_df = pd.DataFrame(results)
res_df.to_csv(os.path.join(DATA_DIR, 'cooccurrence_matrix.csv'), index=False)
print(f"\nSaved cooccurrence_matrix.csv ({len(res_df)} pairs)")

with open(os.path.join(DATA_DIR, 'contingency_tables.txt'), 'w') as f:
    f.write("Group-Level 2x2 Contingency Tables\n")
    f.write("=" * 60 + "\n")
    f.write(f"Total species: {len(df)}\n")
    for ct in contingency_text:
        f.write(ct)

print("\n=== Permutation Test (1000 shuffles) ===\n")

np.random.seed(42)
N_PERM = 1000

key_pairs = [
    ('P_acquisition', 'Metal_handling'),
    ('N_fixation', 'Metal_handling'),
    ('Phenazine_operon', 'Metal_handling'),
    ('P_acquisition', 'N_fixation'),
    ('Phenazine_operon', 'P_acquisition'),
]

for g1, g2 in key_pairs:
    a, b = group_has[g1], group_has[g2]
    observed_phi = phi_coefficient(a, b)

    null_phis = np.zeros(N_PERM)
    for i in range(N_PERM):
        shuffled_b = np.random.permutation(b)
        null_phis[i] = phi_coefficient(a, shuffled_b)

    perm_p = (np.sum(np.abs(null_phis) >= np.abs(observed_phi)) + 1) / (N_PERM + 1)
    z_score = (observed_phi - np.mean(null_phis)) / np.std(null_phis) if np.std(null_phis) > 0 else float('inf')

    print(f"{g1} vs {g2}:")
    print(f"  Observed phi = {observed_phi:.4f}")
    print(f"  Null mean = {np.mean(null_phis):.4f} +/- {np.std(null_phis):.4f}")
    print(f"  Z-score = {z_score:.2f}")
    print(f"  Permutation p = {perm_p:.4f}")
    print()

print("\n=== Per-Gene-Family Pairwise Detail ===\n")

nutrient_genes = groups['P_acquisition'] + groups['N_fixation'] + ['phzF', 'phzA', 'phzB', 'phzD', 'phzG', 'phzS', 'phzM']
metal_genes = groups['Metal_handling']

detail_rows = []
for ng in nutrient_genes:
    ng_col = f'has_{ng}'
    if ng_col not in df.columns:
        continue
    a = df[ng_col].values
    for mg in metal_genes:
        mg_col = f'has_{mg}'
        if mg_col not in df.columns:
            continue
        b = df[mg_col].values
        j = jaccard(a, b)
        phi = phi_coefficient(a, b)
        ct = contingency_2x2(a, b)
        or_val, fp = stats.fisher_exact(ct)
        n_a = int(np.sum(a))
        n_b = int(np.sum(b))
        n_both = int(ct[0, 0])
        expected = (n_a / len(a)) * (n_b / len(a)) * len(a) if len(a) > 0 else 0
        enrichment = n_both / expected if expected > 0 else float('inf')

        detail_rows.append({
            'nutrient_gene': ng,
            'metal_gene': mg,
            'n_nutrient': n_a,
            'n_metal': n_b,
            'n_both': n_both,
            'expected': round(expected, 1),
            'enrichment': round(enrichment, 3),
            'jaccard': round(j, 4),
            'phi': round(phi, 4),
            'odds_ratio': round(or_val, 3) if or_val != float('inf') else 'inf',
            'fisher_p': fp,
        })

detail_df = pd.DataFrame(detail_rows)
detail_df.to_csv(os.path.join(DATA_DIR, 'pairwise_detail.csv'), index=False)
print(f"Saved pairwise_detail.csv ({len(detail_df)} pairs)")

print("\nTop 10 enrichments (nutrient x metal):")
detail_sorted = detail_df.sort_values('enrichment', ascending=False)
for _, row in detail_sorted.head(10).iterrows():
    print(f"  {row['nutrient_gene']:>10s} x {row['metal_gene']:<10s}: "
          f"enrichment={row['enrichment']:.2f}x  phi={row['phi']:.4f}  "
          f"n_both={row['n_both']}  p={row['fisher_p']:.2e}")

print("\nBottom 5 enrichments (depleted co-occurrence):")
detail_neg = detail_df[detail_df['phi'] < 0].sort_values('phi')
for _, row in detail_neg.head(5).iterrows():
    print(f"  {row['nutrient_gene']:>10s} x {row['metal_gene']:<10s}: "
          f"enrichment={row['enrichment']:.2f}x  phi={row['phi']:.4f}  "
          f"n_both={row['n_both']}  p={row['fisher_p']:.2e}")

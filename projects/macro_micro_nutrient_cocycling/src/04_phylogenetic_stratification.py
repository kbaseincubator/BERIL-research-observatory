"""
Step 4: Phylogenetic stratification of co-occurrence.

Stratifies co-occurrence by GTDB phylum and class. Identifies lineages where
macro-micro nutrient gene co-occurrence is strongest. Tests prediction that
plant-associated/soil/rhizosphere lineages show stronger co-occurrence.

Outputs:
  data/phylum_cooccurrence.csv — per-phylum co-occurrence statistics
  data/class_cooccurrence.csv — per-class co-occurrence (top lineages)
  data/phenazine_operon_taxonomy.csv — taxonomic distribution of phz operon carriers
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

print("Loading data...")
df = pd.read_csv(os.path.join(DATA_DIR, 'species_gene_families.csv'))
tax = pd.read_csv(os.path.join(DATA_DIR, 'species_taxonomy.csv'))
print(f"Gene families: {len(df)} species, Taxonomy: {len(tax)} species")

merged = df.merge(tax[['gtdb_species_clade_id', 'GTDB_species', 'domain', 'phylum', 'class', 'order', 'family', 'genus']],
                  on='gtdb_species_clade_id', how='left')
print(f"Merged: {len(merged)} species")

has_cols = {
    'P': 'has_P_acquisition',
    'N': 'has_N_fixation',
    'M': 'has_metal_handling',
    'Phz': 'has_phz_operon',
}

for label, col in has_cols.items():
    if col not in merged.columns:
        merged[col] = 0

print(f"\n=== Phylum-Level Stratification ===\n")

phylum_rows = []
for phylum, grp in merged.groupby('phylum'):
    if len(grp) < 10:
        continue
    n = len(grp)
    n_p = int(grp['has_P_acquisition'].sum())
    n_n = int(grp['has_N_fixation'].sum())
    n_m = int(grp['has_metal_handling'].sum())
    n_phz = int(grp['has_phz_operon'].sum())
    n_pm = int(((grp['has_P_acquisition'] == 1) & (grp['has_metal_handling'] == 1)).sum())
    n_nm = int(((grp['has_N_fixation'] == 1) & (grp['has_metal_handling'] == 1)).sum())

    p_frac = n_p / n
    m_frac = n_m / n
    expected_pm = p_frac * m_frac * n
    pm_enrichment = n_pm / expected_pm if expected_pm > 0 else 0

    n_frac = n_n / n
    expected_nm = n_frac * m_frac * n
    nm_enrichment = n_nm / expected_nm if expected_nm > 0 else 0

    a_pm = np.array([grp['has_P_acquisition'].values, grp['has_metal_handling'].values])
    phi_pm = 0
    if n > 1:
        n11 = n_pm
        n10 = n_p - n_pm
        n01 = n_m - n_pm
        n00 = n - n_p - n_m + n_pm
        denom = np.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
        if denom > 0:
            phi_pm = (n11*n00 - n10*n01) / denom

    phylum_rows.append({
        'phylum': phylum,
        'n_species': n,
        'n_P': n_p,
        'n_N': n_n,
        'n_Metal': n_m,
        'n_Phz_operon': n_phz,
        'frac_P': round(p_frac, 3),
        'frac_N': round(n_frac, 3),
        'frac_M': round(m_frac, 3),
        'n_P_Metal': n_pm,
        'n_N_Metal': n_nm,
        'PM_enrichment': round(pm_enrichment, 3),
        'NM_enrichment': round(nm_enrichment, 3),
        'phi_PM': round(phi_pm, 4),
    })

phy_df = pd.DataFrame(phylum_rows).sort_values('n_species', ascending=False)
phy_df.to_csv(os.path.join(DATA_DIR, 'phylum_cooccurrence.csv'), index=False)
print(f"Saved phylum_cooccurrence.csv ({len(phy_df)} phyla)")

print("\nTop phyla by P-Metal enrichment (n>=50):")
top = phy_df[phy_df['n_species'] >= 50].sort_values('PM_enrichment', ascending=False).head(15)
for _, row in top.iterrows():
    print(f"  {row['phylum']:>30s}: n={row['n_species']:>5d}  P={row['frac_P']:.2f}  M={row['frac_M']:.2f}  "
          f"P&M={row['n_P_Metal']:>5d}  enrich={row['PM_enrichment']:.2f}x  phi={row['phi_PM']:.4f}  "
          f"N-fix={row['frac_N']:.2f}  Phz={row['n_Phz_operon']}")

print(f"\n=== Class-Level Stratification ===\n")

class_rows = []
for cls, grp in merged.groupby('class'):
    if len(grp) < 20:
        continue
    n = len(grp)
    n_p = int(grp['has_P_acquisition'].sum())
    n_n = int(grp['has_N_fixation'].sum())
    n_m = int(grp['has_metal_handling'].sum())
    n_phz = int(grp['has_phz_operon'].sum())
    n_pm = int(((grp['has_P_acquisition'] == 1) & (grp['has_metal_handling'] == 1)).sum())
    n_nm = int(((grp['has_N_fixation'] == 1) & (grp['has_metal_handling'] == 1)).sum())

    p_frac = n_p / n
    m_frac = n_m / n
    expected_pm = p_frac * m_frac * n
    pm_enrichment = n_pm / expected_pm if expected_pm > 0 else 0

    n11 = n_pm
    n10 = n_p - n_pm
    n01 = n_m - n_pm
    n00 = n - n_p - n_m + n_pm
    denom = np.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
    phi_pm = (n11*n00 - n10*n01) / denom if denom > 0 else 0

    class_rows.append({
        'class': cls,
        'n_species': n,
        'n_P': n_p,
        'n_N': n_n,
        'n_Metal': n_m,
        'n_Phz_operon': n_phz,
        'frac_P': round(p_frac, 3),
        'frac_N': round(n_n / n, 3),
        'frac_M': round(m_frac, 3),
        'n_P_Metal': n_pm,
        'PM_enrichment': round(pm_enrichment, 3),
        'phi_PM': round(phi_pm, 4),
    })

cls_df = pd.DataFrame(class_rows).sort_values('n_species', ascending=False)
cls_df.to_csv(os.path.join(DATA_DIR, 'class_cooccurrence.csv'), index=False)
print(f"Saved class_cooccurrence.csv ({len(cls_df)} classes)")

print("\nTop classes by P-Metal phi (n>=50):")
top_cls = cls_df[cls_df['n_species'] >= 50].sort_values('phi_PM', ascending=False).head(15)
for _, row in top_cls.iterrows():
    print(f"  {row['class']:>35s}: n={row['n_species']:>5d}  P={row['frac_P']:.2f}  M={row['frac_M']:.2f}  "
          f"phi={row['phi_PM']:.4f}  enrich={row['PM_enrichment']:.2f}x  N={row['frac_N']:.2f}  Phz={row['n_Phz_operon']}")

print(f"\n=== Phenazine Operon Taxonomic Distribution ===\n")

phz_species = merged[merged['has_phz_operon'] == 1].copy()
phz_has_cols = [f'has_{g}' for g in ['phzA', 'phzB', 'phzD', 'phzF', 'phzG', 'phzS', 'phzM'] if f'has_{g}' in merged.columns]

phz_tax = phz_species[['gtdb_species_clade_id', 'GTDB_species', 'phylum', 'class', 'order', 'family', 'genus',
                         'has_P_acquisition', 'has_N_fixation', 'has_metal_handling', 'n_phz_genes'] + phz_has_cols]
phz_tax = phz_tax.sort_values(['phylum', 'class', 'order', 'family'])
phz_tax.to_csv(os.path.join(DATA_DIR, 'phenazine_operon_taxonomy.csv'), index=False)
print(f"Saved phenazine_operon_taxonomy.csv ({len(phz_tax)} species)")

print(f"\nPhenazine operon carriers by family:")
for family, grp in phz_tax.groupby('family'):
    n = len(grp)
    genera = grp['genus'].unique()
    pm = int(grp['has_P_acquisition'].sum())
    mm = int(grp['has_metal_handling'].sum())
    print(f"  {family}: {n} species (genera: {', '.join(genera[:5])}) P={pm}/{n} Metal={mm}/{n}")

print(f"\n=== Predicted Plant-Associated Lineages ===\n")

plant_families = ['f__Pseudomonadaceae', 'f__Rhizobiaceae', 'f__Burkholderiaceae',
                  'f__Streptomycetaceae', 'f__Bacillaceae', 'f__Xanthomonadaceae',
                  'f__Enterobacteriaceae', 'f__Oxalobacteraceae', 'f__Comamonadaceae']

for fam in plant_families:
    subset = merged[merged['family'] == fam]
    if len(subset) == 0:
        continue
    n = len(subset)
    n_p = int(subset['has_P_acquisition'].sum())
    n_m = int(subset['has_metal_handling'].sum())
    n_pm = int(((subset['has_P_acquisition'] == 1) & (subset['has_metal_handling'] == 1)).sum())
    n_phz = int(subset['has_phz_operon'].sum())
    frac_p = n_p / n
    frac_m = n_m / n
    expected_pm = frac_p * frac_m * n
    enrichment = n_pm / expected_pm if expected_pm > 0 else 0

    print(f"  {fam}: n={n}  P={frac_p:.2f}  M={frac_m:.2f}  P&M={n_pm}  enrich={enrichment:.2f}x  Phz_operon={n_phz}")

print("\nGlobal baseline for comparison:")
n = len(merged)
n_p = int(merged['has_P_acquisition'].sum())
n_m = int(merged['has_metal_handling'].sum())
n_pm = int(((merged['has_P_acquisition'] == 1) & (merged['has_metal_handling'] == 1)).sum())
frac_p = n_p / n
frac_m = n_m / n
expected_pm = frac_p * frac_m * n
enrichment = n_pm / expected_pm if expected_pm > 0 else 0
print(f"  GLOBAL: n={n}  P={frac_p:.2f}  M={frac_m:.2f}  P&M={n_pm}  enrich={enrichment:.2f}x")

#!/usr/bin/env python3
"""
Cobalamin auxotrophy vs niche breadth test.

Binary question: Are genera with COMPLETE cobalamin biosynthesis pathways
more specialist than cobalamin auxotrophs?

This is NOT confounded by genome size because it's a binary (complete/incomplete)
classification, not a per-Mb density.

Uses KEGG modules M00122 (cobalamin anaerobic) + M00924 (cobalamin aerobic).
A genus is classified as "cobalamin prototroph" if it has ≥ threshold fraction
of the pathway KOs present in its pangenome.

Tests:
  1. Mann-Whitney U: B_std(prototroph) vs B_std(auxotroph)
  2. PGLS: B_std ~ prototroph_binary (phylogenetically controlled)
  3. PGLS: B_std ~ pathway_completeness (continuous, 0-1 fraction)
  4. Sensitivity: vary completeness threshold (50%, 70%, 90%)
  5. Control: same test for ribosomal protein pathway (should be null —
     all genera have complete ribosomes)
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

DATA = Path('data')
TREE = str(DATA / 'gtdb_bac_genus_pruned.tree')

sys.path.insert(0, str(Path('scripts')))
from pgls_utils import run_pgls

def _z(s):
    v = s.dropna()
    if len(v) < 5 or v.std() == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - v.mean()) / v.std()

# ── 1. Define cobalamin pathway KOs ─────────────────────────────────────────
# M00122: Cobalamin biosynthesis (anaerobic) — 12 steps
# M00924: Cobalamin biosynthesis (aerobic) — partial overlap
# Combined unique KOs from KEGG REST for both modules
# Source: expanded_kegg_metal_cofactor_densities.csv was built from these modules

exp = pd.read_csv(DATA / 'expanded_kegg_metal_cofactor_densities.csv')
print(f"Expanded cofactor densities: {exp.shape}")
print(f"Columns: {list(exp.columns)}")

# The cobalamin_per_mb column exists — let's also get the raw KO list
# from the curated_mrg_ko_ids_v2.csv for the 7 curated cofactor KOs
km = pd.read_csv(DATA / 'curated_mrg_ko_ids_v2.csv')
curated_cof = km[km['is_cofactor'] == True]
print(f"\nCurated cofactor KOs (n={len(curated_cof)}):")
print(curated_cof[['KO', 'gene_name', 'evidence_tier']].to_string())

# Get all cobalamin KOs from the expanded set
# These were queried from KEGG modules M00122 + M00924
# Let's load the KO presence matrix and identify cobalamin KOs
nb25 = pd.read_parquet(DATA / 'nb25_ko_presence_matrix.parquet')
nb25['genus_lower'] = nb25['genus_lower'].str.replace(r'^g__', '', regex=True)

# Load the pathway assignment file if it exists
pathway_file = DATA / 'kegg_pathway_overlay.csv'
if pathway_file.exists():
    pw = pd.read_csv(pathway_file)
    print(f"\nPathway overlay: {pw.shape}")
    print(f"Columns: {list(pw.columns)}")
    pw_col = [c for c in pw.columns if 'pathway' in c.lower() or 'name' in c.lower()]
    if pw_col:
        cobalamin_rows = pw[pw[pw_col[0]].str.contains('cobalamin', case=False, na=False)]
        print(f"Cobalamin rows: {len(cobalamin_rows)}")
    else:
        print("No pathway column found — using hardcoded KO list")
else:
    print("\nNo pathway overlay file — using KEGG module KOs directly")

# Also try to get cobalamin KOs from the expanded density computation
# The expanded file has cobalamin_per_mb — we need the underlying KOs
# Let's query the KEGG modules
print("\n── Querying cobalamin module KOs from data ──")

# Check what's in the tier_ko_counts file
tier_kos = pd.read_csv(DATA / 'tier_ko_counts_spark.csv') if (DATA / 'tier_ko_counts_spark.csv').exists() else None

# Alternative: use the metals_per_ko file to find cobalamin-associated KOs
metals_ko = pd.read_csv(DATA / 'metals_per_ko.csv') if (DATA / 'metals_per_ko.csv').exists() else None

# Let's use a direct approach: the expanded_kegg_metal_cofactor_densities.csv
# was computed from specific pathway KO sets. We know the cobalamin module KOs
# from the KEGG REST API query that produced that file.
# Standard cobalamin biosynthesis KOs (M00122 + M00924):
COBALAMIN_KOS = [
    'K02303',  # cobA/btuR - cob(I)alamin adenosyltransferase
    'K19221',  # cobA - uroporphyrinogen-III C-methyltransferase
    'K02224',  # cobB/cbiA - cobyrinic acid a,c-diamide synthase
    'K02225',  # cobC/cbiC - precorrin-8X methylmutase  [IN CURATED SET]
    'K02227',  # cobD/cbiB - adenosylcobinamide-phosphate synthase
    'K02228',  # cobF - precorrin-6A synthase
    'K02229',  # cobG - precorrin-3B synthase
    'K02230',  # cobH/cbiC - precorrin-8W decarboxylase
    'K02231',  # cobI/cbiL - precorrin-2 C20-methyltransferase
    'K02232',  # cobJ/cbiH - precorrin-3B C17-methyltransferase
    'K02233',  # cobK/cbiJ - precorrin-6A reductase
    'K02234',  # cobL/cbiET - precorrin-6Y C5,15-methyltransferase
    'K02235',  # cobM/cbiF - precorrin-4 C11-methyltransferase
    'K02236',  # cobN - cobaltochelatase subunit CobN
    'K09882',  # cobO/btuR - cob(I)alamin adenosyltransferase
    'K02237',  # cobP/cobU - adenosylcobinamide kinase
    'K02238',  # cobQ/cbiP - adenosylcobyric acid synthase
    'K02239',  # cobR - cob(II)yrinic acid a,c-diamide reductase
    'K02240',  # cobS/cobV - adenosylcobinamide-GDP ribazoletransferase
    'K02241',  # cobT/cobU - nicotinate-nucleotide-dimethylbenzimidazole phosphoribosyltransferase
    'K02242',  # cobU/cobP - adenosylcobinamide kinase / adenosylcobinamide-phosphate guanylyltransferase
    'K13786',  # cobC - alpha-ribazole phosphatase
    'K06042',  # bluB - 5,6-dimethylbenzimidazole synthase
]

# Also add anaerobic pathway KOs (cbi genes)
COBALAMIN_KOS_ANAEROBIC = [
    'K02189',  # cbiA - cobyrinic acid a,c-diamide synthase
    'K02190',  # cbiB - adenosylcobinamide-phosphate synthase
    'K02191',  # cbiC - precorrin-8X methylmutase
    'K02192',  # cbiD - cobalt-precorrin-5B(C1)-methyltransferase
    'K03399',  # cbiE - cobalt-precorrin-7 C5-methyltransferase
    'K02194',  # cbiF - cobalt-precorrin-4 C11-methyltransferase
    'K02195',  # cbiG - cobalt-precorrin-5A hydrolase
    'K02196',  # cbiH - cobalt-precorrin-3 C17-methyltransferase
    'K13789',  # cbiJ - cobalt-precorrin-6A reductase
    'K02197',  # cbiK - sirohydrochlorin cobaltochelatase
    'K02198',  # cbiL - cobalt-precorrin-2 C20-methyltransferase
    'K02200',  # cbiN - cobalt transport protein
    'K02201',  # cbiO - cobalt transport ATP-binding protein
    'K02202',  # cbiP - adenosylcobyric acid synthase
    'K02203',  # cbiQ - cobalt transport protein
    'K06043',  # cbiT - cobalt-precorrin-6B C15-methyltransferase
]

ALL_COBALAMIN = list(set(COBALAMIN_KOS + COBALAMIN_KOS_ANAEROBIC))
print(f"\nTotal cobalamin KOs queried: {len(ALL_COBALAMIN)}")

# ── 2. Compute per-genus pathway completeness ──────────────────────────────
# For each genus, what fraction of cobalamin KOs are present?

cob_presence = nb25[nb25['ko'].isin(ALL_COBALAMIN)].copy()
print(f"Cobalamin KO hits in pangenome: {len(cob_presence):,}")
print(f"Unique cobalamin KOs found: {cob_presence['ko'].nunique()}")
print(f"Genera with ≥1 cobalamin KO: {cob_presence['genus_lower'].nunique():,}")

# Get total KOs available per genus
meta = pd.read_csv(DATA / '01_genus_ko_density_spark.csv')[
    ['genus_lower', 'n_genomes', 'mean_genome_mb']].drop_duplicates()

# Count present cobalamin KOs per genus
cob_per_genus = (cob_presence
    .groupby('genus_lower')['ko']
    .nunique()
    .reset_index()
    .rename(columns={'ko': 'n_cobalamin_kos'}))

# Also compute what fraction of cobalamin KOs are found in the full dataset
n_cob_kos_in_data = cob_presence['ko'].nunique()
print(f"Cobalamin KOs detected in dataset: {n_cob_kos_in_data} of {len(ALL_COBALAMIN)} queried")

# Pathway completeness = n_present / n_available_in_dataset
cob_per_genus['completeness'] = cob_per_genus['n_cobalamin_kos'] / n_cob_kos_in_data

# Join with niche breadth
niche = pd.read_csv(DATA / 'soil_sample_pgls_dataset.csv')[
    ['genus_lower', 'mean_levins_B_std', 'mean_genome_mb']].drop_duplicates()

df = niche.merge(cob_per_genus, on='genus_lower', how='left')
df['n_cobalamin_kos'] = df['n_cobalamin_kos'].fillna(0)
df['completeness'] = df['completeness'].fillna(0)
df = df[df['mean_levins_B_std'].notna()]

print(f"\n── Dataset ──")
print(f"Total genera with niche breadth: {len(df):,}")
print(f"Genera with ≥1 cobalamin KO: {(df['n_cobalamin_kos'] > 0).sum():,}")
print(f"Genera with 0 cobalamin KOs (auxotrophs): {(df['n_cobalamin_kos'] == 0).sum():,}")
print(f"Completeness distribution:")
print(df['completeness'].describe())
print(f"\nCompleteness histogram:")
for thresh in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    n = (df['completeness'] >= thresh).sum()
    print(f"  ≥{thresh:.0%}: {n:5d} genera")

# ── 3. Binary classification at multiple thresholds ────────────────────────

print(f"\n{'='*70}")
print("TEST 1: Mann-Whitney U (non-phylogenetic)")
print(f"{'='*70}")

for thresh_label, thresh in [('any (≥1 KO)', 0.01), ('≥30%', 0.30), ('≥50%', 0.50), ('≥70%', 0.70)]:
    proto = df[df['completeness'] >= thresh]
    auxo  = df[df['completeness'] < thresh]
    if len(proto) < 10 or len(auxo) < 10:
        print(f"\n  Threshold {thresh_label}: n_proto={len(proto)}, n_auxo={len(auxo)} — SKIP (too few)")
        continue
    u, p = stats.mannwhitneyu(proto['mean_levins_B_std'], auxo['mean_levins_B_std'],
                               alternative='less')
    print(f"\n  Threshold {thresh_label}:")
    print(f"    Prototroph (n={len(proto):,}): median B_std = {proto['mean_levins_B_std'].median():.4f}")
    print(f"    Auxotroph  (n={len(auxo):,}):  median B_std = {auxo['mean_levins_B_std'].median():.4f}")
    print(f"    Mann-Whitney U = {u:.0f}, p = {p:.4e} (one-sided: prototroph < auxotroph)")
    # Effect size (rank-biserial)
    r_rb = 1 - (2 * u) / (len(proto) * len(auxo))
    print(f"    Rank-biserial r = {r_rb:.3f}")
    # Also report genome size difference
    u_gs, p_gs = stats.mannwhitneyu(proto['mean_genome_mb'], auxo['mean_genome_mb'])
    print(f"    Genome size: proto median={proto['mean_genome_mb'].median():.2f} Mb, "
          f"auxo median={auxo['mean_genome_mb'].median():.2f} Mb (p={p_gs:.4e})")

# ── 4. PGLS tests ──────────────────────────────────────────────────────────

print(f"\n{'='*70}")
print("TEST 2: PGLS (phylogenetically controlled)")
print(f"{'='*70}")

# Continuous completeness
df['completeness_z'] = _z(df['completeness'])
df['gsize_z'] = _z(df['mean_genome_mb'])

print("\n  Model A: B_std ~ completeness_z (no genome size control)")
rA = run_pgls(df, TREE, 'mean_levins_B_std', ['completeness_z'],
              taxon_col='genus_lower', label='completeness_alone', min_n=30)
if rA:
    b = rA.get('beta', rA.get('betas', {}).get('completeness_z', np.nan))
    se = rA.get('SE', rA.get('SEs', {}).get('completeness_z', np.nan))
    p = rA.get('p_value', rA.get('p_values', {}).get('completeness_z', np.nan))
    print(f"    β={b:.4f}, SE={se:.4f}, p={p:.4e}")
    print(f"    n={rA['n']}, λ={rA['lambda_est']:.3f}, R²={rA['r2']:.4f}")

print("\n  Model B: B_std ~ completeness_z + gsize_z")
rB = run_pgls(df, TREE, 'mean_levins_B_std', ['completeness_z', 'gsize_z'],
              taxon_col='genus_lower', label='completeness_gsize', min_n=30)
if rB:
    for pred in ['completeness_z', 'gsize_z']:
        b = rB['betas'][pred]
        se = rB['SEs'][pred]
        p = rB['p_values'][pred]
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'NS'
        print(f"    {pred:20s}: β={b:+.4f}, SE={se:.4f}, p={p:.4e} {sig}")
    print(f"    n={rB['n']}, λ={rB['lambda_est']:.3f}, R²={rB['r2']:.4f}")

# Binary prototroph at ≥50% threshold
for thresh_label, thresh in [('≥1 KO', 0.01), ('≥30%', 0.30), ('≥50%', 0.50)]:
    df[f'proto_{thresh_label}'] = (df['completeness'] >= thresh).astype(float)
    proto_col = f'proto_{thresh_label}'
    n_proto = int(df[proto_col].sum())
    n_auxo = len(df) - n_proto
    if n_proto < 30 or n_auxo < 30:
        print(f"\n  Model C ({thresh_label}): SKIP (n_proto={n_proto}, n_auxo={n_auxo})")
        continue

    print(f"\n  Model C ({thresh_label}): B_std ~ prototroph_binary (n_proto={n_proto}, n_auxo={n_auxo})")
    rC = run_pgls(df, TREE, 'mean_levins_B_std', [proto_col],
                  taxon_col='genus_lower', label=f'binary_{thresh_label}', min_n=30)
    if rC:
        b = rC.get('beta', rC.get('betas', {}).get(proto_col, np.nan))
        se = rC.get('SE', rC.get('SEs', {}).get(proto_col, np.nan))
        p = rC.get('p_value', rC.get('p_values', {}).get(proto_col, np.nan))
        print(f"    β={b:.4f}, SE={se:.4f}, p={p:.4e}")
        print(f"    n={rC['n']}, λ={rC['lambda_est']:.3f}")

    print(f"  Model D ({thresh_label}): B_std ~ prototroph_binary + gsize_z")
    rD = run_pgls(df, TREE, 'mean_levins_B_std', [proto_col, 'gsize_z'],
                  taxon_col='genus_lower', label=f'binary_gsize_{thresh_label}', min_n=30)
    if rD:
        for pred in [proto_col, 'gsize_z']:
            b = rD['betas'][pred]
            se = rD['SEs'][pred]
            p = rD['p_values'][pred]
            sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'NS'
            print(f"    {pred:20s}: β={b:+.4f}, SE={se:.4f}, p={p:.4e} {sig}")
        print(f"    n={rD['n']}, λ={rD['lambda_est']:.3f}")

# ── 5. Control: ribosomal protein pathway ──────────────────────────────────
print(f"\n{'='*70}")
print("CONTROL: Ribosomal protein pathway completeness")
print(f"{'='*70}")

# Ribosomal proteins are in the landscape data
ribo = pd.read_csv(DATA / 'nc_ribosomal_proteins_density.csv') if (DATA / 'nc_ribosomal_proteins_density.csv').exists() else None
if ribo is not None:
    print(f"Ribosomal density data: {ribo.shape}")
    ribo_col = [c for c in ribo.columns if 'per_mb' in c.lower() or 'density' in c.lower() or '_z' in c.lower()]
    print(f"  Available columns: {ribo_col}")
else:
    print("  No ribosomal density file found — skipping control")

# ── 6. Genome size independence check ──────────────────────────────────────
print(f"\n{'='*70}")
print("GENOME SIZE INDEPENDENCE CHECK")
print(f"{'='*70}")

r_gs, p_gs = stats.spearmanr(df['completeness'], df['mean_genome_mb'])
print(f"Spearman(completeness, genome_size): rho={r_gs:.3f}, p={p_gs:.3e}")
print(f"  If this is near zero, completeness is genome-size-independent")

# Partial correlation: completeness ~ B_std controlling for genome size
from scipy.stats import spearmanr
mask = df[['completeness', 'mean_levins_B_std', 'mean_genome_mb']].notna().all(axis=1)
x = df.loc[mask, 'completeness'].values
y = df.loc[mask, 'mean_levins_B_std'].values
z = df.loc[mask, 'mean_genome_mb'].values

# Partial Spearman via residuals
from scipy.stats import rankdata
rx = rankdata(x)
ry = rankdata(y)
rz = rankdata(z)
# Residualize x and y on z
from numpy.polynomial.polynomial import polyfit
def resid(a, b):
    coef = np.polyfit(b, a, 1)
    return a - np.polyval(coef, b)
rx_res = resid(rx, rz)
ry_res = resid(ry, rz)
r_partial, p_partial = spearmanr(rx_res, ry_res)
print(f"Partial Spearman(completeness, B_std | genome_size): rho={r_partial:.4f}, p={p_partial:.4e}")

# Save results
results = {
    'completeness_genome_size_rho': r_gs,
    'completeness_genome_size_p': p_gs,
    'partial_spearman_rho': r_partial,
    'partial_spearman_p': p_partial,
    'n_genera': len(df),
    'n_prototroph_any': int((df['completeness'] > 0).sum()),
    'n_auxotroph': int((df['completeness'] == 0).sum()),
    'n_cobalamin_kos_in_data': n_cob_kos_in_data,
}
import json
with open(DATA / 'cobalamin_auxotrophy_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved results to {DATA / 'cobalamin_auxotrophy_results.json'}")

print("\nDONE.")

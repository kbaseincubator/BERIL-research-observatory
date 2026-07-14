"""NB05: HGT event characterisation, GT2 neighbourhood analysis, and metal resistance link."""
import ast, warnings
from collections import Counter
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, mannwhitneyu

PROJ    = '/home/hmacgregor/BERIL-research-observatory/projects/t4ss_cazy_environmental_hgt'
# Input data: staged in project data/ directory (copied from misc_exploratory)
HGT_CSV = f'{PROJ}/data/Detected_HGT_Events.csv'
GT2_CSV = f'{PROJ}/data/GT2_neighborhood_signatures.csv'
# Metal traits file: large file kept in shared misc_exploratory data store
MT_CSV  = '/home/hmacgregor/BERIL-research-observatory/projects/misc_exploratory/exploratory/data/mgnify_mag_metal_traits.csv'

# ── NB05.1: HGT events ─────────────────────────────────────────────────────
hgt = pd.read_csv(HGT_CSV)
print(f"HGT events: {len(hgt)} rows  columns: {hgt.columns.tolist()}")

# Node_4915 confirmation
node_row = hgt[hgt['Clade_ID'] == 'Node_4915']
if len(node_row):
    r = node_row.iloc[0]
    print(f"\nNode_4915: {int(r['Total_Genes'])} genes  {r['Syntenic_Percentage']:.1f}% syntenic  "
          f"{int(r['Distinct_Phyla'])} phyla  MaxDiv={r['Max_Divergence']:.3f}")
    print(f"  Phyla: {r['Phyla_Involved']}")
else:
    print("\nNode_4915 not found in events file")

# Distinct phyla distribution
print(f"\nDistinct_Phyla distribution:")
print(hgt['Distinct_Phyla'].value_counts().sort_index().to_string())
n_multi = (hgt['Distinct_Phyla'] >= 3).sum()
print(f"Events spanning ≥3 phyla: {n_multi} ({100*n_multi/len(hgt):.1f}%)")

# Divergence vs synteny Spearman
rho, p = spearmanr(hgt['Max_Divergence'], hgt['Syntenic_Percentage'])
print(f"\nSpearman ρ(divergence, synteny): {rho:.3f}  p={p:.3e}")

# Most-involved phyla
all_phyla = []
for phyla_str in hgt['Phyla_Involved'].dropna():
    all_phyla.extend([p.strip() for p in str(phyla_str).split(',')])
phy_counts = Counter(all_phyla)
print("\nMost-involved phyla across all HGT events:")
for phy, cnt in phy_counts.most_common(10):
    print(f"  {cnt:3d}  {phy}")

# ── NB05.2: GT2 neighbourhood analysis ─────────────────────────────────────
gt2 = pd.read_csv(GT2_CSV)
print(f"\nGT2 neighbourhood: {len(gt2)} genomes")

t4ss_count, gt2_count = 0, 0
func_counter = Counter()
for _, row in gt2.iterrows():
    try:
        funcs = ast.literal_eval(row['neighborhood_funcs'])
    except Exception:
        funcs = []
    for f in funcs:
        if 'T4SS' in str(f):
            t4ss_count += 1
        if 'GT2' in str(f):
            gt2_count += 1
        func_counter[str(f)] += 1

print(f"T4SS occurrences in neighbourhoods: {t4ss_count}")
print(f"GT2 occurrences in neighbourhoods:  {gt2_count}")
print("\nTop neighbourhood functions:")
for func, cnt in func_counter.most_common(15):
    print(f"  {cnt:5d}  {func[:60]}")

gt2_genomes = set(gt2['genome_id'])
print(f"\nGT2 unique genomes (source CSV): {len(gt2_genomes)}")

# ── NB05.3: GT2 × metal resistance ─────────────────────────────────────────
mt = pd.read_csv(MT_CSV)
print(f"\nMetal traits: {len(mt):,} MAGs")
mt['is_gt2'] = mt['genome_id'].isin(gt2_genomes)

gt2_mags  = mt[mt['is_gt2']]['n_metal_types']
rest_mags  = mt[~mt['is_gt2']]['n_metal_types']
stat, p_mw = mannwhitneyu(gt2_mags, rest_mags, alternative='greater')
print(f"GT2-neighbourhood MAGs (n={len(gt2_mags)}): mean metal types = {gt2_mags.mean():.3f}")
print(f"Other MAGs          (n={len(rest_mags):,}): mean metal types = {rest_mags.mean():.4f}")
print(f"Fold-difference: {gt2_mags.mean()/max(rest_mags.mean(), 1e-10):.1f}×")
print(f"Mann-Whitney U p={p_mw:.2e}")

# ── Figures ─────────────────────────────────────────────────────────────────

# Figure 1: HGT events scatter (divergence vs synteny)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ax = axes[0]
sc = ax.scatter(hgt['Max_Divergence'], hgt['Syntenic_Percentage'],
                c=hgt['Distinct_Phyla'], cmap='plasma', alpha=0.7, s=40)
plt.colorbar(sc, ax=ax, label='Distinct phyla')
ax.set_xlabel('Max divergence (branch length)')
ax.set_ylabel('Syntenic percentage (%)')
ax.set_title(f'HGT events: divergence vs synteny\nSpearman ρ={rho:.3f} p={p:.2e}')

# Figure 2: Phyla involvement
ax = axes[1]
top_phyla = [k for k, _ in phy_counts.most_common(10)]
top_counts = [phy_counts[k] for k in top_phyla]
ax.barh(top_phyla[::-1], top_counts[::-1], color='#1f77b4', alpha=0.8)
ax.set_xlabel('Number of HGT events involved in')
ax.set_title('Most-involved phyla in HGT events')

plt.tight_layout()
plt.savefig(f'{PROJ}/figures/fig_nb05_hgt_scatter.png', dpi=150)
plt.close()

# Figure 3: Neighbourhood function frequencies
fig, ax = plt.subplots(figsize=(10, 6))
top_funcs = func_counter.most_common(15)
funcs_labels = [f[:40] for f, _ in top_funcs[::-1]]
funcs_counts = [c for _, c in top_funcs[::-1]]
colors = ['#d62728' if 'T4SS' in f else ('#2ca02c' if 'GT2' in f else '#aec7e8')
          for f in funcs_labels]
ax.barh(funcs_labels, funcs_counts, color=colors, alpha=0.85)
ax.set_xlabel('Count in GT2-proximal neighbourhoods')
ax.set_title('Top functions in GT2 T4SS-proximal neighbourhoods\n(red=T4SS, green=GT2)')
plt.tight_layout()
plt.savefig(f'{PROJ}/figures/fig_nb05_neighbourhood_functions.png', dpi=150)
plt.close()
print("Figures saved.")

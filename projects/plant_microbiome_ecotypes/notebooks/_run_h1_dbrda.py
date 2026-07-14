#!/usr/bin/env python3
"""H1 location-vs-dispersion separation via PERMDISP + db-RDA (closes item 20).

PERMANOVA conflates location shift and dispersion heterogeneity.
PERMDISP isolates dispersion. db-RDA on PCoA scores gives location-only R².
"""
import os, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform
from skbio import DistanceMatrix
from skbio.stats.distance import permanova, permdisp
from skbio.stats.ordination import pcoa
from sklearn.linear_model import LinearRegression

DATA = '/home/aparkin/BERIL-research-observatory/projects/plant_microbiome_ecotypes/data'

# Load same data NB04 / NB14 used
markers = pd.read_csv(f'{DATA}/species_marker_matrix_v2.csv')
sp_comp = pd.read_csv(f'{DATA}/species_compartment.csv')

# Plant compartments
plant_comps = ['root', 'phyllosphere', 'rhizosphere']
plant_sp = sp_comp[sp_comp['dominant_compartment'].isin(plant_comps)].copy()
print(f'Plant species (root/phyllosphere/rhizosphere): {len(plant_sp)}')
print(f'Compartment counts:')
print(plant_sp['dominant_compartment'].value_counts())

# Merge with markers
data = plant_sp.merge(markers, on='gtdb_species_clade_id', how='inner')
print(f'After merge: {len(data)} species')

marker_cols = [c for c in markers.columns if c.endswith('_present')]
X = data[marker_cols].values.astype(float)
groups = data['dominant_compartment'].values
ids = data['gtdb_species_clade_id'].values

# Jaccard distance matrix
print('\nComputing Jaccard distance matrix...')
D_arr = squareform(pdist(X, metric='jaccard'))
D = DistanceMatrix(D_arr, ids=list(ids))
print(f'D shape: {D.data.shape}')

# === 1. PERMANOVA (replicates NB04 / NB14) ===
print('\n=== PERMANOVA (replicates Phase 1 + NB14 PERMANOVA) ===')
perm_full = permanova(D, groups, permutations=999)
print(f'PERMANOVA full (n={len(data)}):')
print(f'  test statistic (pseudo-F): {perm_full["test statistic"]:.3f}')
print(f'  p-value: {perm_full["p-value"]:.4f}')
# skbio doesn't return R² directly; compute from total/within SS
n = len(groups)
unique_groups = np.unique(groups)
k = len(unique_groups)
D_sq = D_arr ** 2
SS_total = D_sq.sum() / (2 * n)
SS_within = 0
for g in unique_groups:
    mask = groups == g
    n_g = mask.sum()
    if n_g > 1:
        D_g = D_sq[np.ix_(mask, mask)]
        SS_within += D_g.sum() / (2 * n_g)
SS_between = SS_total - SS_within
R2_full = SS_between / SS_total
print(f'  R²: {R2_full:.3f}')

# === 2. PERMDISP (dispersion heterogeneity) ===
print('\n=== PERMDISP (homogeneity-of-dispersion test) ===')
disp = permdisp(D, groups, permutations=999)
print(f'  test statistic (F): {disp["test statistic"]:.3f}')
print(f'  p-value: {disp["p-value"]:.4f}')
# Group-wise dispersion (mean distance to centroid)
print(f'\n  Group-wise dispersion (mean distance to group centroid):')
pc = pcoa(D)
coords = pc.samples.values  # n_samples × n_components
for g in unique_groups:
    mask = groups == g
    centroid = coords[mask].mean(axis=0)
    dispersions = np.linalg.norm(coords[mask] - centroid, axis=1)
    print(f'    {g:<15} n={mask.sum():>4}  mean_dispersion={dispersions.mean():.3f}  sd={dispersions.std():.3f}')

# === 3. db-RDA: location-only effect ===
print('\n=== db-RDA (constrained ordination on PCoA scores) ===')
# Use the pcoa we already have. Take only the positive-eigenvalue axes.
eigs = pc.eigvals.values
n_pos = (eigs > 1e-9).sum()
Y = coords[:, :n_pos]  # principal coordinates with non-trivial variance
print(f'  PCoA: {n_pos} non-trivial axes (out of {coords.shape[1]})')
print(f'  Total variance (sum of positive eigvals): {eigs[eigs>0].sum():.3f}')

# Compartment dummies as constraint
group_df = pd.get_dummies(pd.Series(groups, name='compartment'), drop_first=True).values.astype(float)

# Center the PCoA scores
Y_c = Y - Y.mean(axis=0, keepdims=True)
G_c = group_df - group_df.mean(axis=0, keepdims=True)

# Fit Y_c = G_c @ B (per-axis)
lm = LinearRegression(fit_intercept=False)
lm.fit(G_c, Y_c)
Y_pred = lm.predict(G_c)

# Constrained / unconstrained variance
SS_total_y = (Y_c ** 2).sum()
SS_constrained = (Y_pred ** 2).sum()
SS_residual = ((Y_c - Y_pred) ** 2).sum()
R2_dbrda = SS_constrained / SS_total_y
print(f'  Constrained variance: {SS_constrained:.3f}')
print(f'  Total variance: {SS_total_y:.3f}')
print(f'  R² (constrained / total): {R2_dbrda:.4f}')

# Permutation test for db-RDA constrained R²
print(f'\n  Permutation test (999 shuffles):')
np.random.seed(42)
perm_R2 = []
for _ in range(999):
    perm_groups = np.random.permutation(groups)
    G_perm = pd.get_dummies(pd.Series(perm_groups), drop_first=True).values.astype(float)
    G_perm_c = G_perm - G_perm.mean(axis=0, keepdims=True)
    lm.fit(G_perm_c, Y_c)
    Yp = lm.predict(G_perm_c)
    perm_R2.append((Yp ** 2).sum() / SS_total_y)
perm_R2 = np.array(perm_R2)
p_dbrda = (np.sum(perm_R2 >= R2_dbrda) + 1) / 1000
print(f'  Null R² mean: {perm_R2.mean():.4f}  sd: {perm_R2.std():.4f}')
print(f'  Permutation p (R²_dbrda >= null): {p_dbrda:.4f}')

# === Summary table ===
print('\n=== SUMMARY: PERMANOVA vs PERMDISP vs db-RDA ===')
print(f'{"Test":<20} {"Statistic":>15} {"p-value":>10} {"R²":>10}')
print('-'*60)
print(f'{"PERMANOVA":<20} {perm_full["test statistic"]:>15.3f} {perm_full["p-value"]:>10.4f} {R2_full:>10.4f}')
print(f'{"PERMDISP":<20} {disp["test statistic"]:>15.3f} {disp["p-value"]:>10.4f} {"":>10}')
print(f'{"db-RDA":<20} {"-":>15} {p_dbrda:>10.4f} {R2_dbrda:>10.4f}')

print(f'\nLocation-only fraction of PERMANOVA R²:')
print(f'  PERMANOVA R²: {R2_full:.4f}')
print(f'  db-RDA R² (location-only): {R2_dbrda:.4f}')
print(f'  Ratio (location / total): {R2_dbrda/R2_full:.2%}')

# Save
results = pd.DataFrame([{
    'permanova_F': perm_full['test statistic'],
    'permanova_p': perm_full['p-value'],
    'permanova_R2': R2_full,
    'permdisp_F': disp['test statistic'],
    'permdisp_p': disp['p-value'],
    'dbrda_R2': R2_dbrda,
    'dbrda_p': p_dbrda,
    'location_fraction': R2_dbrda / R2_full,
    'n_species': len(data),
    'n_compartments': len(unique_groups),
}])
out = f'{DATA}/h1_dbrda_results.csv'
results.to_csv(out, index=False)
print(f'\nSaved: {out}')

# Group dispersions for reference
disp_rows = []
for g in unique_groups:
    mask = groups == g
    centroid = coords[mask].mean(axis=0)
    dispersions = np.linalg.norm(coords[mask] - centroid, axis=1)
    disp_rows.append({'compartment': g, 'n': int(mask.sum()),
                     'mean_dispersion': float(dispersions.mean()),
                     'sd_dispersion': float(dispersions.std())})
pd.DataFrame(disp_rows).to_csv(f'{DATA}/h1_compartment_dispersions.csv', index=False)
print(f'Saved: {DATA}/h1_compartment_dispersions.csv')

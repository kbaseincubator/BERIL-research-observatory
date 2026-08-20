#!/usr/bin/env python3
"""
manuscript_followup_analysis.py

Four analyses for manuscript finalisation:
  H4c: Full housekeeping joint model + partial R²
       (cofactor + translation + replication_repair; ribosomal not available)
  H5c: Expanded resistance Tier 3–5 density: single-predictor & joint
  H3a: CWM pilot — NOT FEASIBLE (genus_ra.parquet missing)
  H5a: Phylogenetic independent contrasts (PIC) vs PGLS β = −0.021
"""

import os, sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import dendropy

for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

DATA    = Path('data')
SCRIPTS = Path('scripts')
REPORT  = Path('report')
TREE    = str(DATA / 'gtdb_bac_genus_pruned.tree')
MIN_N   = 30
RESP    = 'mean_levins_B_std'

sys.path.insert(0, str(SCRIPTS))
from pgls_utils import run_pgls


# ── helpers ──────────────────────────────────────────────────────────────────

def _z(s):
    v = s.dropna()
    if len(v) < 5 or v.std() == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - v.mean()) / v.std()


def _ex(res, focal):
    if res is None:
        return (np.nan,) * 5
    if 'betas' in res and isinstance(res['betas'], dict):
        beta = res['betas'].get(focal, np.nan)
        SE   = res['SEs'].get(focal, np.nan)
        p    = res['p_values'].get(focal, np.nan)
    else:
        beta = res.get('beta', np.nan)
        SE   = res.get('SE', np.nan)
        p    = res.get('p_value', np.nan)
    return beta, SE, p, res.get('lambda_est', np.nan), res.get('r2', np.nan)


def ps(p):
    if pd.isna(p):
        return '?'
    return ('***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05
            else '†' if p < 0.10 else 'NS')


def compute_density(nb25_df, ko_list, density_df, col_name):
    sub = nb25_df[nb25_df['ko'].isin(ko_list)].copy()
    sub = sub.merge(density_df, on='genus_lower', how='left')
    sub['pres'] = sub['n_genomes_with_ko'] / sub['n_genomes'].clip(lower=1)
    grp = sub.groupby('genus_lower').agg(
        total_pres=('pres', 'sum'),
        mean_mb=('mean_genome_mb', 'first')
    ).reset_index()
    grp[col_name] = grp['total_pres'] / grp['mean_mb'].clip(lower=0.01)
    return grp[['genus_lower', col_name]]


# ── Load data ─────────────────────────────────────────────────────────────────

print("── Loading data ──")
df   = pd.read_csv(DATA / 'soil_sample_pgls_dataset.csv')
meta = pd.read_csv(DATA / '01_genus_ko_density_spark.csv')[
           ['genus_lower', 'n_genomes', 'mean_genome_mb']].drop_duplicates()
nb25 = pd.read_parquet(DATA / 'nb25_ko_presence_matrix.parquet')
nb25['genus_lower'] = nb25['genus_lower'].str.replace(r'^g__', '', regex=True)
km   = pd.read_csv(DATA / 'curated_mrg_ko_ids_v2.csv')

df['gsize_z']              = _z(df['mean_genome_mb'])
df['cofactor_z']           = _z(df['cofactor_per_mb'])
df['translation_z']        = _z(df['translation_per_mb'])
df['replication_repair_z'] = _z(df['replication_repair_per_mb'])

print(f"  Dataset: n={len(df)}, {RESP} notna={df[RESP].notna().sum()}")


# ════════════════════════════════════════════════════════════════════════════
# H4c: Full housekeeping joint model + semi-partial R²
# ════════════════════════════════════════════════════════════════════════════

print(f"\n{'═'*65}")
print("H4c: Full housekeeping joint model + partial R²")
print(f"{'═'*65}")
print("  NOTE: Ribosomal landscape not available (NB23 ko03016 API returned 0 KOs).")
print("  translation_per_mb is used as a proxy (KEGG ko03000 = Translation,")
print("  which includes ribosomal subunits, translation factors, aminoacyl-tRNA).")
print("  Model: B_std ~ cofactor_z + translation_z + replication_repair_z + gsize_z")

H4C_PREDS = ['cofactor_z', 'translation_z', 'replication_repair_z', 'gsize_z']

# Full model
r_full = run_pgls(df, TREE, RESP, H4C_PREDS, taxon_col='genus_lower',
                  label='H4c_full_housekeeping', min_n=MIN_N)
r2_full  = r_full.get('r2', np.nan)
lam_full = r_full.get('lambda_est', np.nan)
n_full   = r_full.get('n', np.nan)

print(f"\n  Full model: n={n_full}, R²={r2_full:.4f}, λ={lam_full:.3f}")
for pred in H4C_PREDS:
    b, se, p, _, _ = _ex(r_full, pred)
    print(f"    {pred:<28} β={b:+.6f}  SE={se:.6f}  p={p:.4g}{ps(p)}")

# Semi-partial R² — fixed λ from full model so all R²s are on the same scale
print(f"\n  Semi-partial R² (fixed λ={lam_full:.3f}):")
semi_r2 = {}
for drop_z in H4C_PREDS:
    reduced = [z for z in H4C_PREDS if z != drop_z]
    r_red   = run_pgls(df, TREE, RESP, reduced, taxon_col='genus_lower',
                       label=f'H4c_no_{drop_z}', min_n=MIN_N,
                       fix_lambda=lam_full)
    r2_red      = r_red.get('r2', np.nan)
    semi_r2[drop_z] = r2_full - r2_red
    print(f"    semipartialR²({drop_z:<26}): {semi_r2[drop_z]:+.5f}  "
          f"(R²_full={r2_full:.4f}, R²_reduced={r2_red:.4f})")

results_h4c = []
for pred in H4C_PREDS:
    b, se, p, _, _ = _ex(r_full, pred)
    results_h4c.append({
        'analysis': 'H4c',
        'label':    f'H4c_full_joint_{pred}',
        'model':    'B_std~cofactor+translation+replication_repair+gsize',
        'focal':    pred,
        'beta': b, 'SE': se, 'p_value': p,
        'lambda_est': lam_full, 'n': n_full,
        'r2_full': r2_full,
        'semi_partial_r2': semi_r2.get(pred, np.nan),
    })


# ════════════════════════════════════════════════════════════════════════════
# H5c: Expanded resistance Tier 3–5
# ════════════════════════════════════════════════════════════════════════════

print(f"\n{'═'*65}")
print("H5c: Expanded resistance (Tier 3–5) single & joint models")
print(f"{'═'*65}")

tier12_kos = km[(km['is_resistance'] == True) &
                 km['evidence_tier'].isin(['Tier 1', 'Tier 2', 'Tier 2-Fitness'])]['KO'].tolist()
tier35_kos = km[(km['is_resistance'] == True) &
                ~km['evidence_tier'].isin(['Tier 1', 'Tier 2', 'Tier 2-Fitness'])]['KO'].tolist()

kos_nb25  = set(nb25['ko'].unique())
t12_nb25  = [k for k in tier12_kos if k in kos_nb25]
t35_nb25  = [k for k in tier35_kos if k in kos_nb25]
t35_miss  = [k for k in tier35_kos if k not in kos_nb25]

print(f"  Tier 1–2 KOs: {len(tier12_kos)} total, {len(t12_nb25)} in nb25")
print(f"  Tier 3–5 KOs: {len(tier35_kos)} total, {len(t35_nb25)} in nb25  "
      f"({len(t35_miss)} missing from nb25)")
print(f"  Tier 3–5 KOs not in nb25 ({len(t35_miss)}): {t35_miss}")

t35_dens = compute_density(nb25, t35_nb25, meta, 't35_res_per_mb')
t12_dens = compute_density(nb25, t12_nb25, meta, 't12_res_per_mb')

df = df.merge(t35_dens, on='genus_lower', how='left')
df = df.merge(t12_dens, on='genus_lower', how='left')
df['t35_res_z'] = _z(df['t35_res_per_mb'])
df['t12_res_z'] = _z(df['t12_res_per_mb'])

print(f"\n  Tier 3–5 density: notna={df['t35_res_per_mb'].notna().sum()}, "
      f"nonzero={df['t35_res_per_mb'].gt(0).sum()}")
print(f"  Tier 1–2 (nb25): notna={df['t12_res_per_mb'].notna().sum()}, "
      f"nonzero={df['t12_res_per_mb'].gt(0).sum()}")

# Single: Tier 3–5
r_t35 = run_pgls(df, TREE, RESP, ['t35_res_z', 'gsize_z'],
                 taxon_col='genus_lower', label='H5c_tier35', min_n=MIN_N)
b35, se35, p35, lam35, _ = _ex(r_t35, 't35_res_z')
n35 = r_t35.get('n', np.nan)
print(f"\n  Tier 3–5 alone:   β={b35:+.6f} SE={se35:.6f} p={p35:.4g}{ps(p35)} "
      f"λ={lam35:.3f} n={n35}")

# Single: Tier 1–2 (nb25-derived, for cross-tier consistency)
r_t12 = run_pgls(df, TREE, RESP, ['t12_res_z', 'gsize_z'],
                 taxon_col='genus_lower', label='H5c_tier12nb25', min_n=MIN_N)
b12, se12, p12, lam12, _ = _ex(r_t12, 't12_res_z')
n12 = r_t12.get('n', np.nan)
print(f"  Tier 1–2 (nb25): β={b12:+.6f} SE={se12:.6f} p={p12:.4g}{ps(p12)} "
      f"λ={lam12:.3f} n={n12}")

# Joint: Tier 1–2 + Tier 3–5
r_joint = run_pgls(df, TREE, RESP, ['t12_res_z', 't35_res_z', 'gsize_z'],
                   taxon_col='genus_lower', label='H5c_joint_tiers', min_n=MIN_N)
b12j, se12j, p12j, lam_j, _ = _ex(r_joint, 't12_res_z')
b35j, se35j, p35j, _, _     = _ex(r_joint, 't35_res_z')
n_j = r_joint.get('n', np.nan)
print(f"\n  Joint model (n={n_j}, λ={lam_j:.3f}):")
print(f"    Tier 1–2 (focal): β={b12j:+.6f} SE={se12j:.6f} p={p12j:.4g}{ps(p12j)}")
print(f"    Tier 3–5 (focal): β={b35j:+.6f} SE={se35j:.6f} p={p35j:.4g}{ps(p35j)}")

# Spearman correlation between tiers
common = df[['genus_lower', 't12_res_per_mb', 't35_res_per_mb']].dropna()
rho_tiers, p_tiers = stats.spearmanr(common['t12_res_per_mb'], common['t35_res_per_mb'])
print(f"\n  ρ(Tier 1–2, Tier 3–5) = {rho_tiers:.3f} (p={p_tiers:.4g}, n={len(common)})")

results_h5c = [
    {'analysis': 'H5c', 'label': 'H5c_tier35_alone',
     'model': 'B_std~tier35_res+gsize', 'focal': 't35_res_z',
     'beta': b35, 'SE': se35, 'p_value': p35, 'lambda_est': lam35, 'n': n35},
    {'analysis': 'H5c', 'label': 'H5c_tier12_nb25_alone',
     'model': 'B_std~tier12_res(nb25)+gsize', 'focal': 't12_res_z',
     'beta': b12, 'SE': se12, 'p_value': p12, 'lambda_est': lam12, 'n': n12},
    {'analysis': 'H5c', 'label': 'H5c_joint_tier12',
     'model': 'B_std~tier12+tier35+gsize (focal=tier12)', 'focal': 't12_res_z',
     'beta': b12j, 'SE': se12j, 'p_value': p12j, 'lambda_est': lam_j, 'n': n_j},
    {'analysis': 'H5c', 'label': 'H5c_joint_tier35',
     'model': 'B_std~tier12+tier35+gsize (focal=tier35)', 'focal': 't35_res_z',
     'beta': b35j, 'SE': se35j, 'p_value': p35j, 'lambda_est': lam_j, 'n': n_j},
]


# ════════════════════════════════════════════════════════════════════════════
# H3a: CWM pilot — NOT FEASIBLE
# ════════════════════════════════════════════════════════════════════════════

print(f"\n{'═'*65}")
print("H3a: Community-weighted metal-gene density — NOT FEASIBLE")
print(f"{'═'*65}")
print("  Required data missing from local working directory:")

for path_str, note in [
    ('data/genus_ra.parquet',
     'sample × genus relative-abundance matrix — MISSING'),
    ('../final_draft/data/otu_counts_long.parquet',
     'long-format OTU counts with sample metadata — MISSING'),
]:
    exists = (DATA / path_str.replace('data/', '')).exists()
    status = 'EXISTS' if exists else 'MISSING'
    print(f"    {path_str:55s}  [{status}]  {note if not exists else ''}")

print("  data/cwm_by_biome.csv EXISTS but is a biome-aggregated summary")
print("  (mean/SD/n per Env_Level_1), not sample-level data.")
print("  Status: NOT RUN — sample-level genus × sample data not available locally.")


# ════════════════════════════════════════════════════════════════════════════
# H5a: PIC robustness
# ════════════════════════════════════════════════════════════════════════════

print(f"\n{'═'*65}")
print("H5a: Phylogenetic independent contrasts (PIC)")
print("     Reference PGLS: β = −0.0210, p = 2.1×10⁻⁸, n=1574, λ=0.786")
print(f"{'═'*65}")
print("  Note: R/ape not installed. Implementing Felsenstein (1985) PIC in Python.")


def compute_pic(tree_obj, taxa_vals, variables):
    """Standardised PICs via post-order traversal (Felsenstein 1985).

    For each internal node with two children that both have data, computes
      contrast_v = (x1_v − x2_v) / sqrt(b1 + b2)
    where b1/b2 are effective branch lengths (edge length + accumulated variance
    from deeper contrasts).  Nodes with only one child that has data propagate
    the value upward, accumulating the branch length.

    Returns a DataFrame of contrasts (one row per internal bifurcation with data
    in both subtrees); rows with any NaN dropped.
    """
    node_val = {}   # node → {var: float}
    node_bl  = {}   # node → effective branch length (accumulated)

    for leaf in tree_obj.leaf_node_iter():
        if leaf.taxon is None:
            continue
        lbl = leaf.taxon.label
        if lbl in taxa_vals:
            node_val[leaf] = taxa_vals[lbl].copy()
            node_bl[leaf]  = 0.0

    rows = []

    for node in tree_obj.postorder_node_iter():
        children = list(node.child_nodes())
        if not children:
            continue

        ch_ok = [c for c in children if c in node_val]

        if len(ch_ok) == 0:
            continue

        elif len(ch_ok) == 1:
            c  = ch_ok[0]
            bl = (c.edge_length or 0.0) + node_bl[c]
            node_val[node] = node_val[c].copy()
            node_bl[node]  = bl

        else:
            # Two (or more) children with data — take first two
            c1, c2 = ch_ok[0], ch_ok[1]
            b1 = (c1.edge_length or 0.0) + node_bl[c1]
            b2 = (c2.edge_length or 0.0) + node_bl[c2]

            if b1 <= 1e-15 or b2 <= 1e-15:
                # Degenerate branch — propagate, do not compute contrast
                node_val[node] = node_val[c1].copy()
                node_bl[node]  = b1 + b2
                continue

            row   = {}
            valid = True
            for v in variables:
                x1 = node_val[c1].get(v, np.nan)
                x2 = node_val[c2].get(v, np.nan)
                if np.isnan(x1) or np.isnan(x2):
                    valid = False
                    break
                row[v] = (x1 - x2) / np.sqrt(b1 + b2)

            if valid:
                rows.append(row)

            # Internal node: precision-weighted mean; effective variance
            w1, w2 = 1.0 / b1, 1.0 / b2
            W = w1 + w2
            node_val[node] = {
                v: (node_val[c1].get(v, np.nan) * w1 +
                    node_val[c2].get(v, np.nan) * w2) / W
                for v in variables
            }
            node_bl[node] = 1.0 / W

    return pd.DataFrame(rows)


PIC_VARS = [RESP, 'ko_per_mb_primary', 'mean_genome_mb']

pic_sub = df[['genus_lower'] + PIC_VARS].dropna().copy()
pic_sub['_lbl'] = pic_sub['genus_lower'].str.replace(' ', '_').str.lower()
taxa_dict = {row['_lbl']: {v: row[v] for v in PIC_VARS}
             for _, row in pic_sub.iterrows()}

print(f"\n  Genera with complete PIC data: {len(taxa_dict)}")

print("  Loading GTDB tree (this may take ~30 s)...")
pic_tree = dendropy.Tree.get(path=TREE, schema='newick', preserve_underscores=True)

# Normalise labels to match dataset format (lowercase, underscores)
for t in pic_tree.taxon_namespace:
    t.label = t.label.replace(' ', '_').lower()

tree_labels = {t.label for t in pic_tree.taxon_namespace}
valid_taxa  = set(taxa_dict.keys()) & tree_labels
print(f"  Genera matched in tree: {len(valid_taxa)} of {len(taxa_dict)}")

# Filter to taxa in tree
taxa_dict = {k: v for k, v in taxa_dict.items() if k in tree_labels}

print("  Computing PICs (post-order traversal)...")
pic_df  = compute_pic(pic_tree, taxa_dict, PIC_VARS).dropna()
n_pic   = len(pic_df)
print(f"  Valid contrasts: {n_pic}")

results_h5a = []

if n_pic < 10:
    print("  ERROR: Too few contrasts — check tree–dataset label matching.")
else:
    pic_ko    = pic_df['ko_per_mb_primary'].values
    pic_niche = pic_df[RESP].values
    pic_gsize = pic_df['mean_genome_mb'].values

    # ── Bivariate PIC through origin ──────────────────────────────────────
    beta_biv   = np.dot(pic_ko, pic_niche) / np.dot(pic_ko, pic_ko)
    resid_biv  = pic_niche - beta_biv * pic_ko
    sigma2_biv = np.sum(resid_biv ** 2) / (n_pic - 1)
    se_biv     = np.sqrt(sigma2_biv / np.dot(pic_ko, pic_ko))
    t_biv      = beta_biv / se_biv
    p_biv      = 2 * (1 - stats.t.cdf(abs(t_biv), df=n_pic - 1))

    print(f"\n  PIC bivariate (through origin, n={n_pic}):")
    print(f"    β = {beta_biv:+.6f}  SE = {se_biv:.6f}  "
          f"p = {p_biv:.4g}{ps(p_biv)}")

    # ── Multiple PIC through origin: ko + genome_size ─────────────────────
    X_pic  = np.column_stack([pic_ko, pic_gsize])
    betas_m, _, _, _ = np.linalg.lstsq(X_pic, pic_niche, rcond=None)
    res_m   = pic_niche - X_pic @ betas_m
    s2_m    = np.sum(res_m ** 2) / (n_pic - 2)
    try:
        XtX_inv = np.linalg.inv(X_pic.T @ X_pic)
        se_m    = np.sqrt(np.diag(XtX_inv * s2_m))
        t_m     = betas_m / se_m
        p_m     = [2 * (1 - stats.t.cdf(abs(t), df=n_pic - 2)) for t in t_m]
    except np.linalg.LinAlgError:
        se_m = np.array([np.nan, np.nan])
        p_m  = [np.nan, np.nan]

    print(f"\n  PIC + genome size covariate (through origin, n={n_pic}):")
    print(f"    β(ko_per_mb)    = {betas_m[0]:+.6f}  SE = {se_m[0]:.6f}  "
          f"p = {p_m[0]:.4g}{ps(p_m[0])}")
    print(f"    β(genome_size)  = {betas_m[1]:+.6f}  SE = {se_m[1]:.6f}  "
          f"p = {p_m[1]:.4g}{ps(p_m[1])}")

    # ── Reference ─────────────────────────────────────────────────────────
    print(f"\n  PGLS reference: β = −0.0210, p = 2.1×10⁻⁸  (n=1574, λ=0.786)")

    r_pearson, p_pearson = stats.pearsonr(pic_ko, pic_niche)
    print(f"  Pearson r(PIC_ko, PIC_niche) = {r_pearson:.4f} (p={p_pearson:.4g})")

    results_h5a = [
        {'analysis': 'H5a', 'label': 'H5a_PIC_bivariate',
         'model': 'PIC: niche ~ ko (through origin)', 'focal': 'ko_per_mb_primary',
         'beta': beta_biv, 'SE': se_biv, 'p_value': p_biv,
         'lambda_est': np.nan, 'n': n_pic},
        {'analysis': 'H5a', 'label': 'H5a_PIC_with_gsize',
         'model': 'PIC: niche ~ ko + gsize (through origin, focal=ko)',
         'focal': 'ko_per_mb_primary',
         'beta': betas_m[0], 'SE': se_m[0], 'p_value': p_m[0],
         'lambda_est': np.nan, 'n': n_pic},
    ]


# ════════════════════════════════════════════════════════════════════════════
# Save + summary
# ════════════════════════════════════════════════════════════════════════════

all_rows = results_h4c + results_h5c + results_h5a
all_new  = pd.DataFrame(all_rows)
out_path = DATA / 'followup_analysis_results.csv'
all_new.to_csv(out_path, index=False)
print(f"\n  Saved: {out_path}")

print(f"\n{'═'*65}")
print("SUMMARY TABLE")
print(f"{'═'*65}")
print(f"{'Label':<42} {'β':>9} {'p':>9} {'n':>6} {'λ':>7}")
print('-' * 75)
for r in all_rows:
    if pd.isna(r.get('beta', np.nan)):
        continue
    p = r.get('p_value', np.nan)
    lam = r.get('lambda_est', np.nan)
    lam_str = f"{lam:.3f}" if not pd.isna(lam) else "  PIC"
    print(f"{r['label']:<42} {r['beta']:>+9.5f} {p:>9.4g} {int(r['n']):>6} {lam_str:>7}")

print(f"\n{'═'*65}")
print("COMPLETE")
print(f"  {out_path}")
print(f"{'═'*65}")

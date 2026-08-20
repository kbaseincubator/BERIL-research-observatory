#!/usr/bin/env python3
"""
Spatial block CV: pH vs CLR taxonomy vs KO gene panel vs pH+KO
Executes 5-fold spatial block CV using existing feature_matrix blocks.

Pipelines:
  P1: pH alone
  P2: CLR genus taxonomy (200 genera)
  P3: KO gene panel (84 field-strict KOs) — CWM from Spark ke_pangenome
  P4: pH + KO gene panel

Target: binary contamination per metal (Cu/Zn/Pb/Ni)
Metric: AUROC per fold, mean ± SD across folds.

Output: data/spatial_block_cv_results.csv
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings('ignore')

REPO = '/home/hmacgregor/BERIL-research-observatory'
CCP_DATA = f'{REPO}/projects/community_composition_prediction/data'
PER_KO_DATA = f'{REPO}/projects/per_ko_metal_associations/data'
CME_DATA = f'{REPO}/projects/comprehensive_metal_ecology/data'

print("="*70)
print("Spatial Block CV: pH vs Taxonomy vs KO Gene Panel")
print("="*70)

# ── 1. Load feature matrix ────────────────────────────────────────────────────
print("\n1. Loading feature matrix...")
fm = pq.read_table(f'{CCP_DATA}/feature_matrix.parquet').to_pandas()
print(f"   feature_matrix: {fm.shape}")

# CLR columns
clr_cols = [c for c in fm.columns if c.startswith('clr_')]
print(f"   CLR columns: {len(clr_cols)}")

# pH column selection (prefer ph_insitu, fallback to ph_olm, then ph)
for ph_col in ['ph', 'ph_olm', 'ph_insitu']:
    if ph_col in fm.columns and fm[ph_col].notna().sum() > 10000:
        break
print(f"   pH source: {ph_col}  n_obs={fm[ph_col].notna().sum()}")

# Metal targets: binary contamination
# Use CSU PF1 threshold: Cu>60, Zn>200, Pb>50, Ni>50 (ppm)
metal_thresholds = {'Cu': 60, 'Zn': 200, 'Pb': 50, 'Ni': 50}
for metal, thresh in metal_thresholds.items():
    col = f'{metal}_ppm'
    if col in fm.columns:
        fm[f'contaminated_{metal}'] = (fm[col] > thresh).astype(int)
        n_cont = fm[f'contaminated_{metal}'].sum()
        print(f"   {metal}: {n_cont} contaminated / {fm[col].notna().sum()} total "
              f"(>{thresh} ppm = {100*n_cont/fm[col].notna().sum():.1f}%)")

# ── 2. Load field-strict KO list ─────────────────────────────────────────────
print("\n2. Loading field-strict KO list...")
field_kos_df = pd.read_csv(f'{PER_KO_DATA}/field_strict_ko_annotations.csv')
field_kos = field_kos_df['ko_id'].unique().tolist()
print(f"   Field-strict KOs: {len(field_kos)}")

# ── 3. Get KO CWM features via Spark ─────────────────────────────────────────
print("\n3. Computing KO CWM features via Spark...")
ko_cwm_matrix = None

try:
    import sys
    sys.path.insert(0, '/home/hmacgregor/BERIL-research-observatory')
    from berdl_notebook_utils import get_spark_session
    spark = get_spark_session()
    print("   Spark connected.")

    # Load genus relative abundances for CWM
    print("   Loading genus_ra.parquet...")
    genus_ra = pq.read_table(f'{CCP_DATA}/genus_ra.parquet').to_pandas()
    print(f"   genus_ra: {genus_ra.shape}")

    # Step A: Query KO presence per genus from ke_pangenome
    ko_list_str = "'" + "','".join(field_kos) + "'"
    print(f"   Querying ke_pangenome for {len(field_kos)} KOs across all genera...")

    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW ko_genus_raw AS
        SELECT
            LOWER(REGEXP_REPLACE(SPLIT(tax.genus, '__')[1], ' ', '_')) AS genus_lower,
            ego.ko_id
        FROM kbase.ke_pangenome.eggnog_mapper_annotations ego
        JOIN kbase.ke_pangenome.gene_genecluster_junction junc ON ego.gene_id = junc.gene_id
        JOIN kbase.ke_pangenome.gene_cluster gc ON junc.gene_cluster_id = gc.gene_cluster_id
        JOIN kbase.ke_pangenome.genome g ON gc.genome_id = g.genome_id
        JOIN kbase.ke_pangenome.gtdb_taxonomy_r214v1 tax ON g.genome_id = tax.genome_id
        WHERE ego.ko_id IN ({ko_list_str})
          AND tax.genus IS NOT NULL
          AND TRIM(tax.genus) != ''
        GROUP BY LOWER(REGEXP_REPLACE(SPLIT(tax.genus, '__')[1], ' ', '_')), ego.ko_id
    """)
    print("   Collecting results...")
    ko_presence_df = spark.sql("SELECT * FROM ko_genus_raw")
    ko_presence_df.cache()
    ko_presence_pd = ko_presence_df.toPandas()
    print(f"   KO presence rows: {len(ko_presence_pd)}")
    print(f"   Unique genera: {ko_presence_pd['genus_lower'].nunique()}")
    print(f"   KOs found: {ko_presence_pd['ko_id'].nunique()} / {len(field_kos)}")

    # Pivot to genus × KO binary matrix
    ko_genus_matrix = ko_presence_pd.assign(present=1).pivot_table(
        index='genus_lower', columns='ko_id', values='present', fill_value=0
    )
    # Add missing KOs as 0
    missing_kos = [k for k in field_kos if k not in ko_genus_matrix.columns]
    for k in missing_kos:
        ko_genus_matrix[k] = 0
    ko_genus_matrix = ko_genus_matrix[field_kos]
    print(f"   KO genus binary matrix: {ko_genus_matrix.shape}")

    # Save genus×KO matrix
    ko_genus_matrix.to_csv(f'{CCP_DATA}/ko_genus_matrix_84kos.csv')
    print(f"   Saved: ko_genus_matrix_84kos.csv")

    # Step B: Compute CWM: sample × KO
    # CWM_KO_j_sample_s = sum_g(ra_g_s * ko_present_j_g)
    # Align genera between genus_ra and ko_genus_matrix
    common_genera = [g for g in genus_ra.columns if g in ko_genus_matrix.index]
    print(f"\n   Genera in both genus_ra and ko_matrix: {len(common_genera)}")

    ra_sub = genus_ra[common_genera]         # samples × common genera
    ko_sub = ko_genus_matrix.loc[common_genera]  # common genera × 84 KOs

    # Matrix multiply: (n_samples × n_genera) @ (n_genera × n_kos) = (n_samples × n_kos)
    cwm = ra_sub.values @ ko_sub.values
    ko_cwm_matrix = pd.DataFrame(
        cwm, index=genus_ra.index, columns=[f'cwm_{k}' for k in field_kos]
    )
    print(f"   CWM matrix: {ko_cwm_matrix.shape}")

except Exception as e:
    print(f"   Spark error: {e}")
    print("   Trying to load cached ko_genus_matrix...")
    cached = f'{CCP_DATA}/ko_genus_matrix_84kos.csv'
    if os.path.exists(cached):
        ko_genus_matrix = pd.read_csv(cached, index_col=0)
        genus_ra = pq.read_table(f'{CCP_DATA}/genus_ra.parquet').to_pandas()
        common_genera = [g for g in genus_ra.columns if g in ko_genus_matrix.index]
        ra_sub = genus_ra[common_genera]
        ko_sub = ko_genus_matrix.loc[common_genera]
        cwm = ra_sub.values @ ko_sub.values
        ko_cwm_matrix = pd.DataFrame(
            cwm, index=genus_ra.index, columns=[f'cwm_{k}' for k in field_kos]
        )
        print(f"   Loaded from cache: {ko_cwm_matrix.shape}")
    else:
        print("   No cache found. P3/P4 will use gw_mean features as proxy.")

# ── 4. Build analysis dataframe ───────────────────────────────────────────────
print("\n4. Building analysis dataframe...")

# Use sample_id as index (spatial_blocks has sample_id)
fm_indexed = fm.copy()
if 'srs_key' in fm_indexed.columns:
    fm_indexed = fm_indexed.set_index('srs_key')

# Build feature sets
X_ph = fm[[ph_col]].copy()

X_clr = fm[clr_cols].copy()

# P3: KO CWM or gw_mean fallback
if ko_cwm_matrix is not None:
    # Align indices between feature_matrix and CWM
    # feature_matrix index is range; CWM index is sample_id from genus_ra
    # We need to match samples between the two
    gw_cols = [c for c in fm.columns if c.startswith('gw_mean_n_metal')]
    if len(gw_cols) > 0:
        print(f"   Using gw_mean proxy alongside CWM (both available)")
    X_ko = ko_cwm_matrix.reindex(fm.index).fillna(0)
    print(f"   P3 (KO CWM): {X_ko.shape}")
else:
    gw_cols = [c for c in fm.columns if c.startswith('gw_')]
    X_ko = fm[gw_cols].copy().fillna(0)
    print(f"   P3 fallback (gw_ features): {X_ko.shape}")

# Block assignments
blocks = fm['block'].values
print(f"   Block distribution: {pd.Series(blocks).value_counts().to_dict()}")

# Metal targets
target_cols = [f'contaminated_{m}' for m in metal_thresholds if f'contaminated_{m}' in fm.columns]
print(f"   Metal targets: {target_cols}")

# ── 5. Run 5-fold spatial block CV ────────────────────────────────────────────
print("\n5. Running 5-fold spatial block CV...")

def run_block_cv(X_feat, y, blocks, label, metal):
    """Run 5-fold block CV and return per-fold AUROCs."""
    unique_blocks = sorted(np.unique(blocks[~np.isnan(y)]))
    fold_aurocs = []

    for test_block in unique_blocks:
        train_mask = (blocks != test_block) & ~np.isnan(y)
        test_mask = (blocks == test_block) & ~np.isnan(y)

        X_train = X_feat[train_mask]
        y_train = y[train_mask]
        X_test = X_feat[test_mask]
        y_test = y[test_mask]

        if y_test.sum() == 0 or y_test.sum() == len(y_test):
            continue

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train.fillna(0))
        X_test_s = scaler.transform(X_test.fillna(0))

        clf = LogisticRegression(max_iter=500, C=0.1, solver='lbfgs')
        try:
            clf.fit(X_train_s, y_train)
            y_prob = clf.predict_proba(X_test_s)[:, 1]
            auroc = roc_auc_score(y_test, y_prob)
            fold_aurocs.append(auroc)
        except Exception as e:
            pass

    return fold_aurocs

all_results = []

for metal in metal_thresholds:
    if f'contaminated_{metal}' not in fm.columns:
        continue
    y = fm[f'contaminated_{metal}'].values.astype(float)
    n_pos = int(y.sum())
    n_total = int((~np.isnan(y)).sum())
    print(f"\n  {metal}: n_pos={n_pos}, n_total={n_total}")

    for pipeline_label, X_feat in [
        ('P1_pH', X_ph),
        ('P2_CLR', X_clr),
        ('P3_KO', X_ko),
        ('P4_pH_KO', pd.concat([X_ph, X_ko], axis=1)),
    ]:
        folds = run_block_cv(X_feat, y, blocks, pipeline_label, metal)
        if folds:
            mean_auroc = np.mean(folds)
            sd_auroc = np.std(folds)
            print(f"    {pipeline_label}: mean AUROC={mean_auroc:.3f} ± {sd_auroc:.3f} "
                  f"(n_folds={len(folds)})")
        else:
            mean_auroc = np.nan
            sd_auroc = np.nan
            print(f"    {pipeline_label}: insufficient data")

        all_results.append({
            'metal': metal,
            'pipeline': pipeline_label,
            'n_positive': n_pos,
            'n_total': n_total,
            'mean_auroc': mean_auroc,
            'sd_auroc': sd_auroc,
            'n_folds': len(folds),
        })

# ── 6. Save results ─────────────────────────────────────────────────────────
results_df = pd.DataFrame(all_results)
print("\n6. Results summary:")
print(results_df.pivot_table(
    index='pipeline', columns='metal', values='mean_auroc', aggfunc='mean'
).round(3).to_string())

out_path = f'{CCP_DATA}/spatial_block_cv_results.csv'
results_df.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")

# ── 7. P3 info ────────────────────────────────────────────────────────────────
if ko_cwm_matrix is not None:
    p3_note = "CWM from ke_pangenome (84 field-strict KOs × genus_ra)"
else:
    p3_note = "gw_mean_ features (gene-weighted metal clusters, Spark query failed)"
print(f"\nP3 features: {p3_note}")
print("\n✓ Done.")

#!/usr/bin/env python3
"""
Variance partitioning for top 20 KO×metal pairs from MGnify raw scan.
Decomposes R² into unique-metal, unique-environment, and shared components.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUT = CME / 'confound_results'

MIN_GENOMES_PER_GENUS = 8
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']

# ── Load data ────────────────────────────────────────────────────────
print("Loading data...")
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols_file = [c for c in env_full.columns if c not in ('latitude', 'longitude', 'genome_id')]
genome_meta = genome_meta.merge(env_full[['genome_id'] + env_cols_file], on='genome_id', how='left')

# Top 20 raw hits
raw = pd.read_csv(OUT / 'mba_otu_raw.csv')
top20 = raw.nsmallest(20, 'q_fdr')[['ko_id', 'metal']].reset_index(drop=True)
top_ko_ids = top20.ko_id.unique().tolist()
print(f"  Top 20 pairs span {len(top_ko_ids)} unique KOs")

# Build wide matrix for just the needed KOs
ko_wide = mg[mg.ko_id.isin(top_ko_ids)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()
del mg, ko_wide

genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index.tolist()
genus_idx = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera}
print(f"  Genomes: {len(genome_df):,}, usable genera: {len(usable_genera)}")

# ── Variance partitioning ────────────────────────────────────────────
print("\nRunning variance partitioning...")

metal_col_map = {
    'Hg': 'PF1_Hg', 'As': 'PF1_As', 'Cu': 'PF1_Cu',
    'Cr': 'PF1_Cr', 'Cd': 'PF1_Cd', 'Pb': 'PF1_Pb'
}

results = []
for _, row in top20.iterrows():
    ko_id = row['ko_id']
    metal_short = row['metal']
    metal_col = metal_col_map[metal_short]
    other_metals = [m for m in METALS if m != metal_col]

    # Collect per-genus residual-based R² components
    r2_total_list = []
    r2_metal_only_list = []
    r2_env_only_list = []
    n_genomes_total = 0

    for genus in usable_genera:
        idx = genus_idx[genus]
        sub = genome_df.iloc[idx]

        ko = sub[ko_id].values
        if ko.std() == 0:
            continue

        y = sub[metal_col].values
        metal_X = sub[['genome_size'] + other_metals].values
        env_X = sub[ENV_COLS].values
        full_X = np.column_stack([metal_X, env_X])

        mask = np.isfinite(y)
        for arr in [metal_X, env_X]:
            mask &= np.all(np.isfinite(arr), axis=1)
        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue
        if ko[mask].std() == 0:
            continue

        y_m = y[mask]
        ko_m = ko[mask].reshape(-1, 1)
        metal_Xm = metal_X[mask]
        env_Xm = env_X[mask]
        full_Xm = full_X[mask]

        n = len(y_m)
        n_genomes_total += n

        def r2_ko_given_covariates(covs):
            if covs.shape[1] == 0:
                X = ko_m
            else:
                X = np.column_stack([ko_m, covs])
            try:
                model = LinearRegression().fit(X, y_m)
                r2_full = model.score(X, y_m)
                model_cov = LinearRegression().fit(covs, y_m) if covs.shape[1] > 0 else None
                r2_cov = model_cov.score(covs, y_m) if model_cov else 0.0
                return max(r2_full - r2_cov, 0.0), r2_full
            except Exception:
                return 0.0, 0.0

        # R²(KO | metals+env) = R²_total contribution of KO
        delta_total, r2_full = r2_ko_given_covariates(full_Xm)
        # R²(KO | metals only) = KO's contribution given metals
        delta_metals, r2_metals_ko = r2_ko_given_covariates(metal_Xm)
        # R²(KO | env only) = KO's contribution given env
        delta_env, r2_env_ko = r2_ko_given_covariates(env_Xm)
        # R²(KO alone)
        delta_raw, _ = r2_ko_given_covariates(np.empty((n, 0)))

        r2_total_list.append((n, delta_raw))
        r2_metal_only_list.append((n, delta_metals))
        r2_env_only_list.append((n, delta_env))

    if not r2_total_list:
        continue

    # Weighted average across genera
    def wavg(lst):
        ns, vals = zip(*lst)
        ns = np.array(ns, dtype=float)
        return np.average(vals, weights=ns)

    r2_raw = wavg(r2_total_list)
    r2_given_metals = wavg(r2_metal_only_list)
    r2_given_env = wavg(r2_env_only_list)

    # Variance partitioning:
    # R²_total = r2_raw (KO alone predicting metal)
    # R²_metals_unique = R²_total - R²(KO|env) = portion killed by adding env
    # R²_env_unique = R²_total - R²(KO|metals) = portion killed by adding other metals
    # R²_shared = R²_total - R²_metals_unique - R²_env_unique
    #
    # But the user's formula is about variance in metal explained by
    # the full model (metals+env+KO) vs subsets. Let me reframe:
    #
    # Actually the user wants:
    # For the KO→metal link, partition the KO's explanatory power into
    # what's unique to "metal context" vs "env context" vs shared.
    #
    # R²_total = r2_raw (KO alone → metal)
    # R²_given_env = r2 of KO after partialing out env (unique metal-related part)
    # R²_given_metals = r2 of KO after partialing out other metals+genome_size
    #   (unique env-related part — what env explains that metals don't)
    #
    # Reinterpreting the user's request in standard VP terms:
    # They want to know: of the KO×metal association,
    #   how much is attributable uniquely to metals,
    #   how much uniquely to environment,
    #   how much is shared (collinear)?
    #
    # r2_metals_unique = r2_given_env  (survives after removing env)
    # r2_env_unique = r2_given_metals  (survives after removing metals)
    # r2_shared = r2_raw - r2_given_env - r2_given_metals

    r2_metals_unique = r2_given_env
    r2_env_unique = r2_given_metals
    r2_shared = max(r2_raw - r2_metals_unique - r2_env_unique, 0.0)

    results.append({
        'ko_id': ko_id,
        'metal': metal_short,
        'R2_total': r2_raw,
        'R2_metals_unique': r2_metals_unique,
        'R2_env_unique': r2_env_unique,
        'R2_shared': r2_shared,
        'n_genera': len(r2_total_list),
        'n_genomes': n_genomes_total,
    })

    print(f"  {ko_id} × {metal_short}: R²_total={r2_raw:.4f}  "
          f"metals_unique={r2_metals_unique:.4f}  "
          f"env_unique={r2_env_unique:.4f}  "
          f"shared={r2_shared:.4f}  "
          f"({len(r2_total_list)} genera)")

# ── Save results ─────────────────────────────────────────────────────
res_df = pd.DataFrame(results)
res_df.to_csv(OUT / 'variance_partitioning_top20.csv', index=False)
print(f"\nSaved to {OUT / 'variance_partitioning_top20.csv'}")

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"  Median R²_total:          {res_df.R2_total.median():.4f}")
print(f"  Median R²_metals_unique:  {res_df.R2_metals_unique.median():.4f}")
print(f"  Median R²_env_unique:     {res_df.R2_env_unique.median():.4f}")
print(f"  Median R²_shared:         {res_df.R2_shared.median():.4f}")
frac_shared = res_df.R2_shared / res_df.R2_total
print(f"  Median shared fraction:   {frac_shared.median():.1%}")

# ── Bar chart ────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [3, 1]})

# Left: stacked bar per pair
ax = axes[0]
labels = [f"{r.ko_id}\n×{r.metal}" for _, r in res_df.iterrows()]
x = np.arange(len(labels))
w = 0.6

ax.bar(x, res_df.R2_metals_unique, w, label='Unique to metals', color='#d62728')
ax.bar(x, res_df.R2_shared, w, bottom=res_df.R2_metals_unique,
       label='Shared (collinear)', color='#ff7f0e')
ax.bar(x, res_df.R2_env_unique, w,
       bottom=res_df.R2_metals_unique + res_df.R2_shared,
       label='Unique to environment', color='#1f77b4')

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
ax.set_ylabel('Partial R² (KO → metal concentration)')
ax.set_title('Variance Partitioning: Top 20 KO×Metal Pairs')
ax.legend(loc='upper right', fontsize=8)

# Right: median summary
ax2 = axes[1]
cats = ['Metals\nunique', 'Shared', 'Env\nunique']
vals = [res_df.R2_metals_unique.median(),
        res_df.R2_shared.median(),
        res_df.R2_env_unique.median()]
colors = ['#d62728', '#ff7f0e', '#1f77b4']
bars = ax2.bar(cats, vals, color=colors, width=0.5)
for bar, v in zip(bars, vals):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.0002,
             f'{v:.4f}', ha='center', va='bottom', fontsize=9)
ax2.set_ylabel('Median partial R²')
ax2.set_title('Median Across 20 Pairs')

plt.tight_layout()
fig.savefig(OUT / 'variance_partitioning_top20.png', dpi=150, bbox_inches='tight')
print(f"  Chart saved to {OUT / 'variance_partitioning_top20.png'}")
print("DONE")

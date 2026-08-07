#!/usr/bin/env python3
"""
Do KOs track pH (and other env vars) after accounting for metals?
Streamlined version — raw + kitchen-sink only. Unbuffered output.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data')
CME = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')

MIN_GENOMES_PER_GENUS = 8
MIN_GENERA = 10
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']

TARGET_KOS = {
    'K01546': 'kdpA', 'K01547': 'kdpB', 'K01548': 'kdpC',
    'K07646': 'kdpD', 'K07667': 'kdpE',
    'K04651': 'hypA', 'K04652': 'hypB', 'K04653': 'hypC',
    'K04654': 'hypD', 'K04655': 'hypE', 'K04656': 'hypF',
    'K06188': 'aqpZ', 'K01531': 'mgtA', 'K07241': 'hoxN/nixA',
    'K08364': 'merP', 'K01535': 'PMA1/PMA2', 'K01114': 'plc',
    'K05275': 'pdxDH', 'K06215': 'pdxS/pdx1',
    'K07497': 'IS_transposase1', 'K07486': 'IS_transposase2',
    'K07481': 'IS5_transposase',
    'K15461': 'mnmC', 'K06213': 'mgtE', 'K02863': 'rplA', 'K03498': 'trkH',
}

print("Loading data...")
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols = [c for c in env_full.columns if c not in ('latitude', 'longitude', 'genome_id')]
genome_meta = genome_meta.merge(env_full[['genome_id'] + env_cols], on='genome_id', how='left')

ko_counts = mg.groupby('ko_id')['genome_id'].nunique()
n_genomes = mg.genome_id.nunique()
ko_prev = ko_counts / n_genomes
variable_kos = ko_prev[(ko_prev >= 0.05) & (ko_prev <= 0.95)].index.tolist()
print(f"  Genomes: {len(genome_meta):,}, variable KOs: {len(variable_kos):,}")

# Build wide matrix
print("Building pivot table...")
ko_wide = mg[mg.ko_id.isin(variable_kos)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()
del mg, ko_wide
import gc; gc.collect()

genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS]
genus_idx = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera.index}
print(f"  Usable genera: {len(usable_genera)}")

# ──────────────────────────────────────────────────────────────────────
# For each env variable as response, run raw and kitchen-sink scans
# ──────────────────────────────────────────────────────────────────────
env_responses = ['ph_h2o', 'mean_annual_temp_C', 'mean_annual_precip_mm',
                 'organic_carbon_density', 'elevation_m']

for env_var in env_responses:
    print(f"\n{'='*60}")
    print(f"Response: {env_var}")
    print(f"{'='*60}")

    resp_vals = genome_df[env_var].values
    n_valid = np.isfinite(resp_vals).sum()
    print(f"  Valid values: {n_valid}/{len(resp_vals)}")
    if n_valid < 100:
        print("  Too few valid — skipping")
        continue

    # Covariates: everything except this response
    other_env = [c for c in ENV_COLS if c != env_var]
    kitchen_sink_covs = ['genome_size'] + METALS + other_env

    for cov_label, covariates in [('Raw', None), ('Kitchen sink', kitchen_sink_covs)]:
        results = []
        for i, ko_id in enumerate(variable_kos):
            if (i + 1) % 1000 == 0:
                print(f"    {cov_label}: KO {i+1}/{len(variable_kos)}...")
            if ko_id not in genome_df.columns:
                continue
            ko_vals = genome_df[ko_id].values

            effects = []
            for genus, idx in genus_idx.items():
                ko = ko_vals[idx]
                resp = resp_vals[idx]
                mask = np.isfinite(resp)

                if covariates:
                    for c in covariates:
                        if c in genome_df.columns:
                            cv = pd.to_numeric(genome_df[c], errors='coerce').values[idx]
                            cm = np.isfinite(cv)
                            if cm[mask].sum() >= mask.sum() * 0.5:
                                mask &= cm

                if mask.sum() < MIN_GENOMES_PER_GENUS:
                    continue
                ko_m = ko[mask]
                if ko_m.std() == 0:
                    continue
                prev = ko_m.mean()
                if prev < 0.05 or prev > 0.95:
                    continue

                if covariates:
                    avail_cols = []
                    for c in covariates:
                        if c in genome_df.columns:
                            cv = pd.to_numeric(genome_df[c], errors='coerce').values[idx][mask]
                            if np.isfinite(cv).all() and cv.std() > 0:
                                avail_cols.append(cv)
                    if avail_cols:
                        X = np.column_stack(avail_cols)
                        try:
                            Xf = np.column_stack([np.ones(X.shape[0]), X])
                            b, _, _, _ = np.linalg.lstsq(Xf, resp[mask], rcond=None)
                            resid = resp[mask] - Xf @ b
                            rho, _ = stats.pointbiserialr(ko_m, resid)
                            if np.isfinite(rho):
                                effects.append((mask.sum(), rho))
                            continue
                        except:
                            continue

                try:
                    rho, _ = stats.pointbiserialr(ko_m, resp[mask])
                    if np.isfinite(rho):
                        effects.append((mask.sum(), rho))
                except:
                    continue

            if len(effects) < MIN_GENERA:
                continue
            ns = np.array([e[0] for e in effects])
            rhos = np.array([e[1] for e in effects])
            w = (ns - 3).clip(min=1)
            z = np.arctanh(np.clip(rhos, -0.999, 0.999))
            mz = np.average(z, weights=w)
            se = 1.0 / np.sqrt(w.sum())
            zs = mz / se
            p = 2 * stats.norm.sf(abs(zs))
            results.append({
                'ko_id': ko_id, 'response': env_var,
                'is_target': ko_id in TARGET_KOS,
                'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects)
            })

        if results:
            rdf = pd.DataFrame(results)
            _, q_vals, _, _ = multipletests(rdf.meta_p.values, method='fdr_bh')
            rdf['q_fdr'] = q_vals
            n_sig = (rdf.q_fdr < 0.05).sum()
            print(f"  {cov_label:15s}: {n_sig:>5d}/{len(rdf)} significant (FDR<0.05)")

            if cov_label == 'Raw':
                rdf.to_csv(CME / 'confound_results' / f'ko_{env_var}_raw_scan.csv', index=False)
            else:
                rdf.to_csv(CME / 'confound_results' / f'ko_{env_var}_kitchensink_scan.csv', index=False)

                if n_sig > 0:
                    print(f"\n    Top surviving hits:")
                    for _, r in rdf[rdf.q_fdr < 0.05].nsmallest(10, 'meta_p').iterrows():
                        gene = TARGET_KOS.get(r.ko_id, r.ko_id)
                        tag = '*' if r.is_target else ' '
                        print(f"      {tag} {gene:18s}: ρ={r.meta_rho:+.4f} "
                              f"p={r.meta_p:.2e} q={r.q_fdr:.4f} ({r.n_genera} genera)")

# ──────────────────────────────────────────────────────────────────────
# Comparison: metals vs env signal strength
# ──────────────────────────────────────────────────────────────────────
print(f"\n\n{'='*60}")
print("SUMMARY: KOs tracking each variable after kitchen-sink control")
print(f"{'='*60}\n")

metal_scan = pd.read_csv(CME / 'confound_results' / 'mgnify_genomewide_raw_scan.csv')
n_metal_raw = (metal_scan.q_fdr < 0.05).sum()
print(f"  Metals (raw):              {n_metal_raw:>5d}/{len(metal_scan)}")

for env_var in env_responses:
    raw_path = CME / 'confound_results' / f'ko_{env_var}_raw_scan.csv'
    ks_path = CME / 'confound_results' / f'ko_{env_var}_kitchensink_scan.csv'
    if raw_path.exists():
        raw = pd.read_csv(raw_path)
        n_raw = (raw.q_fdr < 0.05).sum()
        print(f"  {env_var:25s} raw:    {n_raw:>5d}/{len(raw)}")
    if ks_path.exists():
        ks = pd.read_csv(ks_path)
        n_ks = (ks.q_fdr < 0.05).sum()
        print(f"  {env_var:25s} k.sink: {n_ks:>5d}/{len(ks)}")

print("\nDONE")

#!/usr/bin/env python3
"""
Do KOs track pH after accounting for all env variables + metals?

This flips the question: instead of "does KO presence correlate with metal
after controlling for env", we ask "does KO presence correlate with pH
after controlling for everything else including metals?"

Uses the MGnify dataset (already has all covariates).
"""
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
# All possible covariates except pH (since pH is the response)
ALL_COVARIATES_NO_PH = [
    'genome_size',
    'organic_carbon_density', 'clay_pct',
    'mean_annual_temp_C', 'mean_annual_precip_mm',
    'elevation_m', 'litho_mafic_score',
] + METALS

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


def run_meta(df, ko_id, response_col, covariates=None):
    """Within-genus meta-analysis: KO presence vs response, optionally residualized."""
    genus_cts = df.genus.value_counts()
    genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index
    effects = []

    for genus in genera:
        gdf = df[df.genus == genus]
        ko = gdf[ko_id].values
        resp = gdf[response_col].values

        if ko.std() == 0 or np.isnan(resp).all():
            continue
        prev = ko.mean()
        if prev < 0.05 or prev > 0.95:
            continue

        mask = np.isfinite(resp)
        if covariates:
            avail = []
            for c in covariates:
                if c in gdf.columns:
                    cv = pd.to_numeric(gdf[c], errors='coerce').values
                    cm = np.isfinite(cv)
                    if cm[mask].sum() >= mask.sum() * 0.5:
                        avail.append(c)
                        mask &= cm

            if mask.sum() < MIN_GENOMES_PER_GENUS:
                continue
            ko_sub = ko[mask]
            if ko_sub.std() == 0:
                continue

            if len(avail) > 0:
                X = np.column_stack([pd.to_numeric(gdf[c], errors='coerce').values[mask]
                                    for c in avail])
                keep = [i for i in range(X.shape[1]) if X[:, i].std() > 0]
                if len(keep) > 0:
                    X = X[:, keep]
                    try:
                        Xf = np.column_stack([np.ones(X.shape[0]), X])
                        b, _, _, _ = np.linalg.lstsq(Xf, resp[mask], rcond=None)
                        resid = resp[mask] - Xf @ b
                        rho, _ = stats.pointbiserialr(ko_sub, resid)
                        if np.isfinite(rho):
                            effects.append((mask.sum(), rho, len(keep)))
                        continue
                    except:
                        continue

            try:
                rho, _ = stats.pointbiserialr(ko_sub, resp[mask])
                if np.isfinite(rho):
                    effects.append((mask.sum(), rho, 0))
            except:
                pass
            continue

        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue
        ko_sub = ko[mask]
        if ko_sub.std() == 0:
            continue
        try:
            rho, _ = stats.pointbiserialr(ko_sub, resp[mask])
            if np.isfinite(rho):
                effects.append((mask.sum(), rho, 0))
        except:
            continue

    if len(effects) < MIN_GENERA:
        return None

    ns = np.array([e[0] for e in effects])
    rhos = np.array([e[1] for e in effects])
    ncovs = np.array([e[2] for e in effects])
    med_c = int(np.median(ncovs))
    weights = (ns - med_c - 3).clip(min=1)
    z_vals = np.arctanh(np.clip(rhos, -0.999, 0.999))
    mz = np.average(z_vals, weights=weights)
    se = 1.0 / np.sqrt(weights.sum())
    zs = mz / se
    p = 2 * stats.norm.sf(abs(zs))
    return {'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects),
            'n_genomes': int(ns.sum())}


# ── Load data ────────────────────────────────────────────────────────
print("Loading MGnify data...", flush=True)
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus', 'phylum',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'phylum', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

# Add env covariates
env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols = [c for c in env_full.columns if c not in ('latitude', 'longitude', 'genome_id')]
genome_meta = genome_meta.merge(env_full[['genome_id'] + env_cols], on='genome_id', how='left')

# Find variable KOs
ko_counts = mg.groupby('ko_id')['genome_id'].nunique()
n_genomes = mg.genome_id.nunique()
ko_prev = ko_counts / n_genomes
variable_kos = ko_prev[(ko_prev >= 0.05) & (ko_prev <= 0.95)].index.tolist()
print(f"  Genomes: {len(genome_meta):,}, variable KOs: {len(variable_kos):,}")
print(f"  pH coverage: {genome_meta.ph_h2o.notna().sum():,}/{len(genome_meta):,} "
      f"({genome_meta.ph_h2o.notna().mean():.0%})")

# Pivot to wide for variable KOs
ko_wide = mg[mg.ko_id.isin(variable_kos)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()

genus_cts = genome_df.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS]
genus_idx = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera.index}

# ══════════════════════════════════════════════════════════════════════
# 1. KO × pH — raw (no covariates)
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("KO × pH ANALYSIS")
print(f"{'='*80}\n")

# Also test other env variables as response
env_responses = {
    'ph_h2o': 'pH',
    'mean_annual_temp_C': 'Temperature',
    'mean_annual_precip_mm': 'Precipitation',
    'organic_carbon_density': 'Organic Carbon',
    'elevation_m': 'Elevation',
}

for env_var, env_name in env_responses.items():
    print(f"\n--- Response: {env_name} ({env_var}) ---")

    # Define covariate sets (everything EXCEPT the response variable)
    other_env = [c for c in ENV_COLS if c != env_var]
    cov_sets = {
        'Raw': None,
        'GS only': ['genome_size'],
        'GS + metals': ['genome_size'] + METALS,
        'GS + other env': ['genome_size'] + other_env,
        'GS + metals + other env': ['genome_size'] + METALS + other_env,
    }

    for cov_name, covs in cov_sets.items():
        results = []
        resp_vals = genome_df[env_var].values

        for ko_id in variable_kos:
            if ko_id not in genome_df.columns:
                continue
            ko_vals = genome_df[ko_id].values

            effects = []
            for genus, idx in genus_idx.items():
                ko = ko_vals[idx]
                resp = resp_vals[idx]
                mask = np.isfinite(resp)

                if covs:
                    for c in covs:
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

                if covs:
                    avail = [c for c in covs if c in genome_df.columns]
                    X_cols = []
                    for c in avail:
                        cv = pd.to_numeric(genome_df[c], errors='coerce').values[idx][mask]
                        if np.isfinite(cv).all() and cv.std() > 0:
                            X_cols.append(cv)
                    if X_cols:
                        X = np.column_stack(X_cols)
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
            print(f"  {cov_name:30s}: {n_sig:>5d}/{len(rdf):>5d} significant (FDR<0.05)")

            if cov_name == 'Raw' and env_var == 'ph_h2o':
                rdf.to_csv(CME / 'confound_results' / 'ko_ph_raw_scan.csv', index=False)
            if cov_name == 'GS + metals + other env':
                rdf.to_csv(CME / 'confound_results' / f'ko_{env_var}_kitchensink_scan.csv', index=False)

                # Show top hits
                if n_sig > 0:
                    print(f"\n    Top surviving {env_name} hits (after metals + env control):")
                    for _, r in rdf[rdf.q_fdr < 0.05].nsmallest(10, 'meta_p').iterrows():
                        gene = TARGET_KOS.get(r.ko_id, r.ko_id)
                        tag = '*' if r.is_target else ' '
                        print(f"      {tag} {gene:18s}: ρ={r.meta_rho:+.4f} "
                              f"p={r.meta_p:.2e} q={r.q_fdr:.4f} ({r.n_genera} genera)")


# ══════════════════════════════════════════════════════════════════════
# 2. Comparison: metals vs pH signal strength
# ══════════════════════════════════════════════════════════════════════
print(f"\n\n{'='*80}")
print("COMPARISON: How many KOs track each variable?")
print(f"{'='*80}\n")

# Raw (no covariates) for all response variables
print("Raw (no covariates):")
for env_var, env_name in env_responses.items():
    scan_path = CME / 'confound_results' / f'ko_{env_var}_kitchensink_scan.csv'
    if scan_path.exists():
        scan = pd.read_csv(scan_path)
        n_sig = (scan.q_fdr < 0.05).sum()
        print(f"  {env_name:25s}: {n_sig:>5d}/{len(scan)} survive kitchen sink")

# Load metal scan for comparison
metal_scan = pd.read_csv(CME / 'confound_results' / 'mgnify_genomewide_raw_scan.csv')
if 'q_fdr' in metal_scan.columns:
    n_metal_sig = (metal_scan.q_fdr < 0.05).sum()
    print(f"\n  Metals (raw, any):         {n_metal_sig:>5d}/{len(metal_scan)} significant")

print("\nDONE")

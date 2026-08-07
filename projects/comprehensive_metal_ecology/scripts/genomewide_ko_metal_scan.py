#!/usr/bin/env python3
"""
Genome-wide KO × metal scan: two-phase approach.

Phase 1: Fast raw scan (no covariates) over ALL variable KOs × 6 metals.
Phase 2: Run genome_size and full env-controlled models only on FDR<0.05 pairs.

Compares: are metal-annotated KOs enriched among significant hits?
Does genome_size control change the picture?
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

METAL_KOS = {
    'K01546', 'K01547', 'K01548', 'K07646', 'K07667',
    'K04651', 'K04652', 'K04653', 'K04654', 'K04655', 'K04656',
    'K08364', 'K01531', 'K06213', 'K07241', 'K06188', 'K01535',
    'K03498', 'K10945', 'K10946', 'K07787', 'K07798',
    'K19592', 'K19593', 'K19594', 'K00537', 'K01551',
    'K03325', 'K07243', 'K07667', 'K07662', 'K17686',
    'K02040', 'K02041',
    'K01114', 'K05275', 'K06215',
    'K07497', 'K07486', 'K07481',
    'K15461', 'K02863',
}

# ── Load ───────────────────────────────────────────────────────────────
print("Loading data...", flush=True)
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)

genome_meta = mg.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()
total_genomes = len(genome_meta)

ko_counts = mg.groupby('ko_id')['genome_id'].nunique()
ko_prev = ko_counts / total_genomes
variable_kos = ko_prev[(ko_prev >= 0.05) & (ko_prev <= 0.95)]
print(f"  {total_genomes:,} genomes, {len(variable_kos):,} variable KOs (5-95%)", flush=True)

# Build presence matrix
print("Building presence matrix...", flush=True)
mg_var = mg[mg.ko_id.isin(variable_kos.index)]
ko_wide = mg_var.pivot_table(index='genome_id', columns='ko_id',
                             values='present', fill_value=0)
genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()

# Precompute genus masks
genus_counts = genome_df.genus.value_counts()
usable_genera = genus_counts[genus_counts >= MIN_GENOMES_PER_GENUS].index
genus_indices = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera}
print(f"  {len(usable_genera)} usable genera", flush=True)


def fast_raw_meta(ko_vals, metal_vals, genus_indices):
    """Vectorized within-genus raw (uncorrected) meta-analysis."""
    effects = []
    for genus, idx in genus_indices.items():
        ko = ko_vals[idx]
        met = metal_vals[idx]

        mask = np.isfinite(met)
        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue
        ko_m = ko[mask]
        met_m = met[mask]
        if ko_m.std() == 0:
            continue
        prev = ko_m.mean()
        if prev < 0.05 or prev > 0.95:
            continue
        try:
            rho, _ = stats.pointbiserialr(ko_m, met_m)
            if np.isfinite(rho):
                effects.append((mask.sum(), rho))
        except:
            continue

    if len(effects) < MIN_GENERA:
        return None, None, None

    ns = np.array([e[0] for e in effects])
    rhos = np.array([e[1] for e in effects])
    weights = (ns - 3).clip(min=1)
    z_vals = np.arctanh(np.clip(rhos, -0.999, 0.999))
    meta_z = np.average(z_vals, weights=weights)
    meta_se = 1.0 / np.sqrt(weights.sum())
    z_stat = meta_z / meta_se
    p = 2 * stats.norm.sf(abs(z_stat))
    return np.tanh(meta_z), p, len(effects)


def controlled_meta(genome_df, ko_id, metal_pf1, genus_indices, covariates):
    """Within-genus partial correlation with covariates."""
    effects = []
    ko_all = genome_df[ko_id].values
    met_all = genome_df[metal_pf1].values

    cov_arrays = {}
    for c in covariates:
        if c in genome_df.columns:
            cov_arrays[c] = pd.to_numeric(genome_df[c], errors='coerce').values

    for genus, idx in genus_indices.items():
        ko = ko_all[idx]
        met = met_all[idx]

        if ko.std() == 0 or np.isnan(met).all():
            continue
        prev = ko.mean()
        if prev < 0.05 or prev > 0.95:
            continue

        mask = np.isfinite(met)
        available = []
        for c, arr in cov_arrays.items():
            c_vals = arr[idx]
            c_mask = np.isfinite(c_vals)
            if c_mask[mask].sum() >= mask.sum() * 0.5:
                available.append(c)
                mask &= c_mask

        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue

        ko_sub = ko[mask]
        if ko_sub.std() == 0:
            continue

        if len(available) == 0:
            try:
                rho, _ = stats.pointbiserialr(ko_sub, met[mask])
                if np.isfinite(rho):
                    effects.append((mask.sum(), rho, 0))
            except:
                pass
            continue

        X = np.column_stack([cov_arrays[c][idx][mask] for c in available])
        keep = [i for i in range(X.shape[1]) if X[:, i].std() > 0]
        if len(keep) == 0:
            try:
                rho, _ = stats.pointbiserialr(ko_sub, met[mask])
                if np.isfinite(rho):
                    effects.append((mask.sum(), rho, 0))
            except:
                pass
            continue

        X = X[:, keep]
        try:
            X_full = np.column_stack([np.ones(X.shape[0]), X])
            betas, _, _, _ = np.linalg.lstsq(X_full, met[mask], rcond=None)
            resid = met[mask] - X_full @ betas
            rho, _ = stats.pointbiserialr(ko_sub, resid)
            if np.isfinite(rho):
                effects.append((mask.sum(), rho, len(keep)))
        except:
            continue

    if len(effects) < MIN_GENERA:
        return None

    ns = np.array([e[0] for e in effects])
    rhos = np.array([e[1] for e in effects])
    ncovs = np.array([e[2] for e in effects])
    med_covs = int(np.median(ncovs))
    weights = (ns - med_covs - 3).clip(min=1)
    z_vals = np.arctanh(np.clip(rhos, -0.999, 0.999))
    meta_z = np.average(z_vals, weights=weights)
    meta_se = 1.0 / np.sqrt(weights.sum())
    z_stat = meta_z / meta_se
    p = 2 * stats.norm.sf(abs(z_stat))
    return {'meta_rho': np.tanh(meta_z), 'meta_p': p, 'n_genera': len(effects)}


# ════════════════════════════════════════════════════════════════════════
# PHASE 1: Raw genome-wide scan
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*100}", flush=True)
print(f"PHASE 1: RAW GENOME-WIDE SCAN ({len(variable_kos)} KOs × {len(METALS)} metals)", flush=True)
print(f"{'='*100}\n", flush=True)

ko_list = sorted(variable_kos.index)
ko_arrays = {ko: genome_df[ko].values for ko in ko_list if ko in genome_df.columns}
metal_arrays = {m: genome_df[m].values for m in METALS}

raw_results = []
for i, ko_id in enumerate(ko_list):
    if (i + 1) % 500 == 0:
        print(f"  KO {i+1}/{len(ko_list)}...", flush=True)
    if ko_id not in ko_arrays:
        continue
    ko_vals = ko_arrays[ko_id]
    for metal in METALS:
        rho, p, n_gen = fast_raw_meta(ko_vals, metal_arrays[metal], genus_indices)
        if rho is not None:
            raw_results.append({
                'ko_id': ko_id, 'metal': metal.replace('PF1_', ''),
                'prevalence': ko_prev[ko_id],
                'is_metal_gene': ko_id in METAL_KOS,
                'raw_rho': rho, 'raw_p': p, 'raw_n_genera': n_gen,
            })

raw_df = pd.DataFrame(raw_results)
_, q_vals, _, _ = multipletests(raw_df.raw_p.values, method='fdr_bh')
raw_df['raw_q'] = q_vals

n_sig = (raw_df.raw_q < 0.05).sum()
n_tested = len(raw_df)
print(f"\nPhase 1 complete: {n_tested:,} testable pairs, {n_sig} significant (FDR<0.05)")

# Metal gene enrichment
metal_tested = raw_df[raw_df.is_metal_gene]
nonmetal_tested = raw_df[~raw_df.is_metal_gene]
m_sig = (metal_tested.raw_q < 0.05).sum()
nm_sig = (nonmetal_tested.raw_q < 0.05).sum()
m_rate = m_sig / max(len(metal_tested), 1)
nm_rate = nm_sig / max(len(nonmetal_tested), 1)

a, b = m_sig, len(metal_tested) - m_sig
c, d = nm_sig, len(nonmetal_tested) - nm_sig
odds, fisher_p = stats.fisher_exact([[a, b], [c, d]])

print(f"\n  Metal-gene pairs:    {m_sig}/{len(metal_tested)} significant ({m_rate:.1%})")
print(f"  Non-metal pairs:     {nm_sig}/{len(nonmetal_tested)} significant ({nm_rate:.1%})")
print(f"  Enrichment: {m_rate/max(nm_rate,1e-6):.1f}× (Fisher p={fisher_p:.2e}, OR={odds:.1f})")

# Per-metal
print(f"\n  Per-metal (Raw):")
for ms in ['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb']:
    sub = raw_df[raw_df.metal == ms]
    n_s = (sub.raw_q < 0.05).sum()
    mg_s = (sub[sub.is_metal_gene].raw_q < 0.05).sum() if sub.is_metal_gene.any() else 0
    nmg_s = (sub[~sub.is_metal_gene].raw_q < 0.05).sum() if (~sub.is_metal_gene).any() else 0
    print(f"    {ms}: {n_s}/{len(sub)} sig | metal-gene: {mg_s} | non-metal: {nmg_s}")


# ════════════════════════════════════════════════════════════════════════
# PHASE 2: Controlled models on significant pairs only
# ════════════════════════════════════════════════════════════════════════
sig_pairs = raw_df[raw_df.raw_q < 0.05].copy()
print(f"\n{'='*100}", flush=True)
print(f"PHASE 2: CONTROLLED MODELS ON {len(sig_pairs)} SIGNIFICANT PAIRS", flush=True)
print(f"{'='*100}\n", flush=True)

# Load env covariates
env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols = [c for c in env_full.columns if c not in ('latitude', 'longitude', 'genome_id')]
genome_df = genome_df.merge(env_full[['genome_id'] + env_cols], on='genome_id', how='left',
                            suffixes=('', '_env'))

COV_GS = ['genome_size']
COV_ENV = ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
           'mean_annual_temp_C', 'mean_annual_precip_mm',
           'elevation_m', 'litho_mafic_score']
COV_ALL_BASE = COV_ENV + [
    'georoc_Cu', 'georoc_Ni', 'georoc_Zn', 'georoc_Co', 'georoc_Cr',
    'georoc_Pb', 'georoc_As', 'georoc_Cd', 'georoc_U',
    'gemas_Cu', 'gemas_Pb', 'gemas_Ni', 'gemas_Cr', 'gemas_Co',
    'gemas_Zn', 'gemas_As', 'gemas_Cd', 'gemas_Hg',
    'sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr',
    'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb',
    'tri_facility_count_50km', 'mine_min_dist_km',
    'cmmi_min_dist_km', 'mine_count_50km', 'cs137_bq_m2',
]
COV_ALL = [c for c in COV_ALL_BASE if c in genome_df.columns
           and genome_df[c].notna().sum() > 100]

# Re-compute genus indices after merge
genus_indices = {g: genome_df.index[genome_df.genus == g].values for g in usable_genera}

controlled_models = [('gs', COV_GS), ('env', COV_ENV), ('all', COV_ALL)]

for i, (_, row) in enumerate(sig_pairs.iterrows()):
    if (i + 1) % 50 == 0:
        print(f"  Pair {i+1}/{len(sig_pairs)}...", flush=True)

    for model_name, covs in controlled_models:
        res = controlled_meta(genome_df, row.ko_id, 'PF1_' + row.metal,
                              genus_indices, covs)
        if res:
            sig_pairs.loc[_, f'{model_name}_rho'] = res['meta_rho']
            sig_pairs.loc[_, f'{model_name}_p'] = res['meta_p']
            sig_pairs.loc[_, f'{model_name}_n_genera'] = res['n_genera']
            sig_pairs.loc[_, f'{model_name}_atten'] = (
                1.0 - abs(res['meta_rho']) / max(abs(row.raw_rho), 1e-6))
        else:
            sig_pairs.loc[_, f'{model_name}_rho'] = np.nan
            sig_pairs.loc[_, f'{model_name}_p'] = np.nan
            sig_pairs.loc[_, f'{model_name}_n_genera'] = 0
            sig_pairs.loc[_, f'{model_name}_atten'] = np.nan

# FDR per model
for model_name, _ in controlled_models:
    p_col = f'{model_name}_p'
    valid = sig_pairs[p_col].notna()
    if valid.sum() > 0:
        _, q_vals, _, _ = multipletests(sig_pairs.loc[valid, p_col].values, method='fdr_bh')
        sig_pairs.loc[valid, f'{model_name}_q'] = q_vals


# ── Results ───────────────────────────────────────────────────────────
print(f"\n{'='*100}", flush=True)
print("PHASE 2 RESULTS: ATTENUATION COMPARISON", flush=True)
print(f"{'='*100}\n", flush=True)

for model_name in ['gs', 'env', 'all']:
    q_col = f'{model_name}_q'
    att_col = f'{model_name}_atten'
    desc = {'gs': '+Genome size only',
            'env': '+Genome size + ENV',
            'all': '+GS + ENV + soil metals + anthropo'}[model_name]

    valid = sig_pairs[q_col].notna()
    n_surv = (sig_pairs.loc[valid, q_col] < 0.05).sum()
    n_surv_10 = (sig_pairs.loc[valid, q_col] < 0.10).sum()

    metal_g = sig_pairs[valid & sig_pairs.is_metal_gene]
    nonmetal_g = sig_pairs[valid & ~sig_pairs.is_metal_gene]

    m_surv = (metal_g[q_col] < 0.05).sum() if len(metal_g) > 0 else 0
    nm_surv = (nonmetal_g[q_col] < 0.05).sum() if len(nonmetal_g) > 0 else 0
    m_att = metal_g[att_col].mean() if len(metal_g) > 0 else np.nan
    nm_att = nonmetal_g[att_col].mean() if len(nonmetal_g) > 0 else np.nan

    print(f"\n  Model: {desc}")
    print(f"    Overall: {n_surv}/{valid.sum()} survive FDR<0.05, {n_surv_10} at FDR<0.10")
    print(f"    Metal genes:     {m_surv}/{len(metal_g)} survive | mean atten={m_att:+.0%}")
    print(f"    Non-metal genes: {nm_surv}/{len(nonmetal_g)} survive | mean atten={nm_att:+.0%}")

    if n_surv > 0 and n_surv <= 40:
        survivors = sig_pairs[valid & (sig_pairs[q_col] < 0.05)].sort_values(f'{model_name}_p')
        print(f"    Survivors:")
        for _, r in survivors.iterrows():
            tag = '*METAL*' if r.is_metal_gene else ''
            print(f"      {r.ko_id} × {r.metal}: raw_ρ={r.raw_rho:+.4f} → "
                  f"ctrl_ρ={r[f'{model_name}_rho']:+.4f} (atten={r[att_col]:+.0%}, "
                  f"q={r[q_col]:.4f}) {tag}")


# ── Final comparison ─────────────────────────────────────────────────
print(f"\n{'='*100}", flush=True)
print("FINAL SUMMARY: GENOME SIZE AS CONFOUNDER", flush=True)
print(f"{'='*100}\n", flush=True)

# Genome size correlation with KO presence for significant pairs
print("Genome size × KO presence correlation (significant raw pairs):")
gs = genome_df.genome_size.values
for _, r in sig_pairs.nsmallest(20, 'raw_p').iterrows():
    ko = genome_df[r.ko_id].values
    mask = np.isfinite(gs) & np.isfinite(ko)
    rho_gs, p_gs = stats.pointbiserialr(ko[mask], gs[mask])
    print(f"  {r.ko_id} × {r.metal}: raw_ρ(KO,metal)={r.raw_rho:+.4f}, "
          f"ρ(KO,genome_size)={rho_gs:+.4f} (p={p_gs:.2e}) "
          f"{'*METAL*' if r.is_metal_gene else ''}")


sig_pairs.to_csv(CME / 'genomewide_ko_metal_scan.csv', index=False)
raw_df.to_csv(CME / 'genomewide_raw_scan.csv', index=False)
print(f"\nSaved results to data/")
print("DONE.")

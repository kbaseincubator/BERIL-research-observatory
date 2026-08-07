#!/usr/bin/env python3
"""
Expanded env-controlled KO × metal analysis using ALL arkinlab.envdbs layers.

Covariates:
  ENV: pH, OC, clay, temp, precip, elevation, soil_temp, lithology, landcover
  METAL: GeoROC bedrock metals, GEMAS soil metals, Science 2025 HQ
  ANTHROPO: EPA TRI releases, mine proximity, CMMI ore distance, Cs-137

Three models per KO×metal pair:
  A. ENV-only control (non-metal confounders)
  B. ENV + matching bedrock/soil metal (is KO signal independent of local metal?)
  C. All covariates (kitchen-sink)

Method: within-genus partial correlation with inverse-variance meta-analysis.
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

# ── Covariate groups ─────────────────────────────────────────────────────

ENV_BASIC = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
             'mean_annual_temp_C', 'mean_annual_precip_mm']

ENV_EXTENDED = ENV_BASIC + [
    'elevation_m', 'litho_mafic_score']

GEOROC_COLS = {
    'Hg': 'georoc_Hg', 'As': 'georoc_As', 'Cu': 'georoc_Cu',
    'Cr': 'georoc_Cr', 'Cd': 'georoc_Cd', 'Pb': 'georoc_Pb',
    'Ni': 'georoc_Ni', 'Zn': 'georoc_Zn', 'Co': 'georoc_Co',
}

GEMAS_COLS = {
    'Hg': 'gemas_Hg', 'As': 'gemas_As', 'Cu': 'gemas_Cu',
    'Cr': 'gemas_Cr', 'Cd': 'gemas_Cd', 'Pb': 'gemas_Pb',
    'Ni': 'gemas_Ni', 'Zn': 'gemas_Zn', 'Co': 'gemas_Co',
}

SCI_HQ_COLS = {
    'As': 'sci_hq_As', 'Cd': 'sci_hq_Cd', 'Cu': 'sci_hq_Cu',
    'Cr': 'sci_hq_Cr', 'Co': 'sci_hq_Co', 'Ni': 'sci_hq_Ni',
    'Pb': 'sci_hq_Pb',
}

ANTHROPO_COLS = ['tri_facility_count_50km', 'mine_min_dist_km',
                 'cmmi_min_dist_km', 'mine_count_50km', 'cs137_bq_m2']

TARGET_KOS = {
    'K01546': 'kdpA', 'K01547': 'kdpB', 'K01548': 'kdpC',
    'K07646': 'kdpD', 'K07667': 'kdpE',
    'K03498': 'trkH',
    'K04651': 'hypA', 'K04652': 'hypB', 'K04653': 'hypC',
    'K04654': 'hypD', 'K04655': 'hypE', 'K04656': 'hypF',
    'K06188': 'aqpZ',
    'K01531': 'mgtA', 'K07241': 'hoxN/nixA', 'K08364': 'merP',
    'K01535': 'PMA1/PMA2',
    'K01114': 'plc',
    'K05275': 'pdxDH', 'K06215': 'pdxS/pdx1',
    'K07497': 'IS_transposase1', 'K07486': 'IS_transposase2',
    'K07481': 'IS5_transposase',
    'K15461': 'mnmC', 'K06213': 'mgtE',
    'K02863': 'rplA',
}
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']

# ── 1. Load data ─────────────────────────────────────────────────────────
print("Loading genome-level KO matrix...", flush=True)
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)
mg = mg[mg.ko_id.isin(TARGET_KOS)].copy()

genome_meta = mg.groupby('genome_id').first()[
    ['genus', 'genome_size', 'latitude', 'longitude'] + METALS
].reset_index()
ko_wide = mg.pivot_table(index='genome_id', columns='ko_id',
                         values='present', fill_value=0).reset_index()
genome_df = genome_meta.merge(ko_wide, on='genome_id')
print(f"  Genomes: {len(genome_df):,}, KOs: {len(TARGET_KOS)}", flush=True)

print("Loading FULL environmental covariates...", flush=True)
env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
print(f"  Full env data: {len(env_full):,} genomes, {len(env_full.columns)} columns", flush=True)

env_cols_to_merge = [c for c in env_full.columns
                     if c not in ('latitude', 'longitude') and c != 'genome_id']
genome_df = genome_df.merge(env_full[['genome_id'] + env_cols_to_merge],
                            on='genome_id', how='left')

# Report coverage
print("\nCovariate coverage:", flush=True)
all_covs = (list(set(ENV_EXTENDED)) +
            list(set(GEOROC_COLS.values())) +
            list(set(GEMAS_COLS.values())) +
            list(set(SCI_HQ_COLS.values())) +
            ANTHROPO_COLS)
for c in sorted(set(all_covs)):
    if c in genome_df.columns:
        n = genome_df[c].notna().sum()
        print(f"  {c:35s}: {n:,}/{len(genome_df):,} ({100*n/len(genome_df):.1f}%)", flush=True)
    else:
        print(f"  {c:35s}: NOT AVAILABLE", flush=True)

# Load uncorrected results for comparison
wg1 = pd.read_csv(CME / 'within_genus_ko_metal_results.csv')
wg2 = pd.read_csv(CME / 'within_genus_extended_results.csv')
uncorrected = pd.concat([wg1, wg2]).query("status == 'tested'")

genus_counts = genome_df.genus.value_counts()
usable_genera = genus_counts[genus_counts >= MIN_GENOMES_PER_GENUS]
print(f"\nGenera with ≥{MIN_GENOMES_PER_GENUS} genomes: {len(usable_genera)}", flush=True)


# ── 2. Analysis engine ──────────────────────────────────────────────────

def run_controlled_analysis(genome_df, ko_id, metal_pf1, covariates, usable_genera):
    """Within-genus env-controlled partial correlation with meta-analysis."""
    metal_col_name = metal_pf1
    genus_effects = []

    for genus in usable_genera.index:
        gdf = genome_df[genome_df.genus == genus]
        ko_col = gdf[ko_id].values
        metal_col = gdf[metal_col_name].values

        if ko_col.std() == 0 or np.isnan(metal_col).all():
            continue
        prev = ko_col.mean()
        if prev < 0.05 or prev > 0.95:
            continue

        mask = np.isfinite(metal_col)
        available_covs = []
        for c in covariates:
            if c in gdf.columns:
                c_vals = gdf[c].values
                c_mask = np.isfinite(c_vals)
                if c_mask[mask].sum() >= mask.sum() * 0.5:
                    available_covs.append(c)
                    mask &= c_mask

        if mask.sum() < MIN_GENOMES_PER_GENUS:
            continue

        if len(available_covs) == 0:
            y_metal = metal_col[mask]
            ko_sub = ko_col[mask]
            if ko_sub.std() == 0:
                continue
            try:
                rho, _ = stats.pointbiserialr(ko_sub, y_metal)
                if np.isfinite(rho):
                    genus_effects.append({'genus': genus, 'n': mask.sum(),
                                          'rho': rho, 'n_covs': 0})
            except:
                pass
            continue

        X_env = np.column_stack([gdf[c].values[mask] for c in available_covs])
        keep = [i for i in range(X_env.shape[1]) if X_env[:, i].std() > 0]
        if len(keep) == 0:
            y_metal = metal_col[mask]
            ko_sub = ko_col[mask]
            if ko_sub.std() == 0:
                continue
            try:
                rho, _ = stats.pointbiserialr(ko_sub, y_metal)
                if np.isfinite(rho):
                    genus_effects.append({'genus': genus, 'n': mask.sum(),
                                          'rho': rho, 'n_covs': 0})
            except:
                pass
            continue

        X_env = X_env[:, keep]
        y_metal = metal_col[mask]
        ko_sub = ko_col[mask]

        if ko_sub.std() == 0:
            continue

        try:
            X_full = np.column_stack([np.ones(len(X_env)), X_env])
            betas, _, _, _ = np.linalg.lstsq(X_full, y_metal, rcond=None)
            metal_resid = y_metal - X_full @ betas

            rho, _ = stats.pointbiserialr(ko_sub, metal_resid)
            if np.isfinite(rho):
                n_eff = mask.sum() - len(keep) - 1
                genus_effects.append({'genus': genus, 'n': mask.sum(),
                                      'rho': rho, 'n_covs': len(keep)})
        except:
            continue

    if len(genus_effects) < MIN_GENERA:
        return None

    cdf = pd.DataFrame(genus_effects)
    median_covs = int(cdf.n_covs.median())
    weights = (cdf.n - median_covs - 3).clip(lower=1)
    z_vals = np.arctanh(cdf.rho.clip(-0.999, 0.999))
    meta_z = np.average(z_vals, weights=weights)
    meta_se = 1.0 / np.sqrt(weights.sum())
    meta_z_stat = meta_z / meta_se
    meta_p = 2 * stats.norm.sf(abs(meta_z_stat))
    meta_rho = np.tanh(meta_z)

    frac_pos = (cdf.rho > 0).mean()
    n_pos = int((cdf.rho > 0).sum())
    sign_p = stats.binomtest(n_pos, len(cdf), 0.5).pvalue

    return {
        'n_genera': len(cdf),
        'n_genomes': int(cdf.n.sum()),
        'meta_rho': meta_rho,
        'meta_z': meta_z_stat,
        'meta_p': meta_p,
        'frac_positive': frac_pos,
        'sign_p': sign_p,
        'median_covs': median_covs,
    }


# ── 3. Run three models per pair ────────────────────────────────────────
print(f"\n{'='*100}", flush=True)
print("MULTI-MODEL ENV-CONTROLLED ANALYSIS (A: ENV, B: ENV+metal, C: all)", flush=True)
print(f"{'='*100}\n", flush=True)

results = []
n_pairs = 0

for ko_id, gene_name in TARGET_KOS.items():
    if ko_id not in genome_df.columns:
        continue

    for metal in METALS:
        metal_short = metal.replace('PF1_', '')

        uc = uncorrected[(uncorrected.ko_id == ko_id) & (uncorrected.metal == metal_short)]
        if len(uc) == 0 or uc.iloc[0].get('q_fdr', 1.0) >= 0.05:
            continue

        uc_rho = uc.iloc[0]['meta_rho']
        n_pairs += 1

        if n_pairs % 10 == 0:
            print(f"  Processing pair {n_pairs}...", flush=True)

        # Model A: ENV-only (extended set: pH, OC, clay, temp, precip, elev, soil_temp, litho, landcover)
        env_covs = [c for c in ENV_EXTENDED if c in genome_df.columns
                    and genome_df[c].notna().sum() > 100]
        res_a = run_controlled_analysis(genome_df, ko_id, metal, env_covs, usable_genera)

        # Model B: ENV + matching bedrock/soil metal (GeoROC + GEMAS + Sci2025 for this metal)
        metal_covs = []
        if metal_short in GEOROC_COLS and GEOROC_COLS[metal_short] in genome_df.columns:
            metal_covs.append(GEOROC_COLS[metal_short])
        if metal_short in GEMAS_COLS and GEMAS_COLS[metal_short] in genome_df.columns:
            metal_covs.append(GEMAS_COLS[metal_short])
        if metal_short in SCI_HQ_COLS and SCI_HQ_COLS[metal_short] in genome_df.columns:
            metal_covs.append(SCI_HQ_COLS[metal_short])
        covs_b = env_covs + metal_covs
        res_b = run_controlled_analysis(genome_df, ko_id, metal, covs_b, usable_genera)

        # Model C: Kitchen sink (all available)
        all_metal_covs = [c for c in list(set(GEOROC_COLS.values())) +
                          list(set(GEMAS_COLS.values())) +
                          list(set(SCI_HQ_COLS.values()))
                          if c in genome_df.columns and genome_df[c].notna().sum() > 100]
        anthro_covs = [c for c in ANTHROPO_COLS
                       if c in genome_df.columns and genome_df[c].notna().sum() > 100]
        covs_c = env_covs + all_metal_covs + anthro_covs
        covs_c = list(dict.fromkeys(covs_c))
        res_c = run_controlled_analysis(genome_df, ko_id, metal, covs_c, usable_genera)

        row = {
            'ko_id': ko_id, 'gene_name': gene_name, 'metal': metal_short,
            'rho_uncorrected': uc_rho,
        }

        for label, res in [('A_env', res_a), ('B_env_metal', res_b), ('C_all', res_c)]:
            if res:
                row[f'{label}_rho'] = res['meta_rho']
                row[f'{label}_p'] = res['meta_p']
                row[f'{label}_n_genera'] = res['n_genera']
                row[f'{label}_n_genomes'] = res['n_genomes']
                row[f'{label}_atten'] = 1.0 - abs(res['meta_rho']) / max(abs(uc_rho), 1e-6)
                row[f'{label}_median_covs'] = res['median_covs']
                row[f'{label}_frac_pos'] = res['frac_positive']
            else:
                row[f'{label}_rho'] = np.nan
                row[f'{label}_p'] = np.nan
                row[f'{label}_n_genera'] = 0
                row[f'{label}_n_genomes'] = 0
                row[f'{label}_atten'] = np.nan
                row[f'{label}_median_covs'] = 0
                row[f'{label}_frac_pos'] = np.nan

        results.append(row)

results_df = pd.DataFrame(results)
print(f"\nTotal pairs tested: {len(results_df)}", flush=True)

# FDR correction per model
for label in ['A_env', 'B_env_metal', 'C_all']:
    p_col = f'{label}_p'
    valid = results_df[p_col].notna()
    if valid.sum() > 0:
        _, q_vals, _, _ = multipletests(results_df.loc[valid, p_col].values, method='fdr_bh')
        results_df.loc[valid, f'{label}_q'] = q_vals
    else:
        results_df[f'{label}_q'] = np.nan


# ── 4. Print results ────────────────────────────────────────────────────
print(f"\n{'='*120}", flush=True)
print(f"RESULTS: THREE-MODEL COMPARISON", flush=True)
print(f"{'='*120}", flush=True)

for label, desc in [('A_env', 'ENV-only'),
                    ('B_env_metal', 'ENV + matching metal'),
                    ('C_all', 'Kitchen-sink (all covariates)')]:
    q_col = f'{label}_q'
    rho_col = f'{label}_rho'
    att_col = f'{label}_atten'
    valid = results_df[q_col].notna()

    n_survive_05 = (results_df.loc[valid, q_col] < 0.05).sum()
    n_survive_10 = (results_df.loc[valid, q_col] < 0.10).sum()
    n_tested = valid.sum()
    mean_atten = results_df.loc[valid, att_col].mean()

    print(f"\n  Model {desc}:", flush=True)
    print(f"    Tested: {n_tested} | Survive FDR<0.05: {n_survive_05} | "
          f"FDR<0.10: {n_survive_10} | Mean attenuation: {mean_atten:+.0%}", flush=True)

    if n_survive_05 > 0:
        survivors = results_df[valid & (results_df[q_col] < 0.05)].sort_values(f'{label}_p')
        for _, r in survivors.iterrows():
            print(f"      {r.gene_name:18s} × {r.metal:3s}: "
                  f"ρ_raw={r.rho_uncorrected:+.4f} → ρ_ctrl={r[rho_col]:+.4f} "
                  f"(atten={r[att_col]:+.0%}, q={r[q_col]:.4f})", flush=True)


# ── 5. Detailed per-pair table ──────────────────────────────────────────
print(f"\n{'='*120}", flush=True)
print(f"DETAILED PER-PAIR TABLE (sorted by Model C p-value)", flush=True)
print(f"{'='*120}", flush=True)

print(f"\n{'KO':10s} {'Gene':18s} {'Met':3s} {'ρ_raw':>7s} | "
      f"{'ρ_A':>7s} {'atten_A':>7s} {'q_A':>8s} | "
      f"{'ρ_B':>7s} {'atten_B':>7s} {'q_B':>8s} | "
      f"{'ρ_C':>7s} {'atten_C':>7s} {'q_C':>8s}", flush=True)
print('-' * 130, flush=True)

sort_col = 'C_all_p' if results_df['C_all_p'].notna().any() else 'A_env_p'
for _, r in results_df.sort_values(sort_col).iterrows():
    def fmt_q(q):
        if pd.isna(q): return '     N/A'
        return f'{q:8.4f}'
    def fmt_rho(rho):
        if pd.isna(rho): return '    N/A'
        return f'{rho:+7.4f}'
    def fmt_att(a):
        if pd.isna(a): return '    N/A'
        return f'{a:+6.0%} '

    print(f"{r.ko_id:10s} {r.gene_name:18s} {r.metal:3s} {r.rho_uncorrected:+7.4f} | "
          f"{fmt_rho(r.get('A_env_rho'))} {fmt_att(r.get('A_env_atten'))} {fmt_q(r.get('A_env_q'))} | "
          f"{fmt_rho(r.get('B_env_metal_rho'))} {fmt_att(r.get('B_env_metal_atten'))} {fmt_q(r.get('B_env_metal_q'))} | "
          f"{fmt_rho(r.get('C_all_rho'))} {fmt_att(r.get('C_all_atten'))} {fmt_q(r.get('C_all_q'))}",
          flush=True)


# ── 6. Summary by gene family ──────────────────────────────────────────
print(f"\n{'='*120}", flush=True)
print("SUMMARY BY GENE FAMILY (Model C — full kitchen-sink)", flush=True)
print(f"{'='*120}", flush=True)

families = {
    'KDP operon': ['K01546', 'K01547', 'K01548', 'K07646', 'K07667'],
    'Hydrogenase (hyp)': ['K04651', 'K04652', 'K04653', 'K04654', 'K04655', 'K04656'],
    'Transposases': ['K07497', 'K07486', 'K07481'],
    'PMA1/PMA2': ['K01535'],
    'Phospholipase C': ['K01114'],
    'Ribosomal L1': ['K02863'],
    'Vitamin B6': ['K05275', 'K06215'],
    'trkH': ['K03498'],
    'mgtA/mgtE': ['K01531', 'K06213'],
    'merP': ['K08364'],
    'Aquaporin': ['K06188'],
    'hoxN/nixA': ['K07241'],
}

for family, kos in families.items():
    sub = results_df[results_df.ko_id.isin(kos)]
    if len(sub) == 0:
        continue

    for label, desc in [('A_env', 'ENV'), ('B_env_metal', 'ENV+metal'), ('C_all', 'All')]:
        q_col = f'{label}_q'
        att_col = f'{label}_atten'
        valid = sub[q_col].notna()
        if valid.sum() == 0:
            continue
        n_surv = (sub.loc[valid, q_col] < 0.05).sum()
        mean_att = sub.loc[valid, att_col].mean()
        best_idx = sub.loc[valid, f'{label}_p'].idxmin()
        best = sub.loc[best_idx]
        status = f"{n_surv}/{valid.sum()}"

        if label == 'A_env':
            print(f"\n  {family:25s}:", flush=True)
        print(f"    {desc:12s}: {status:6s} survive | atten={mean_att:+.0%} | "
              f"best: {best.gene_name}×{best.metal} ρ={best[f'{label}_rho']:+.4f}", flush=True)


# ── 7. Per-variable attenuation (top 15 pairs, all variables) ───────────
print(f"\n{'='*120}", flush=True)
print("PER-VARIABLE ATTENUATION (top 15 pairs by Model A p-value)", flush=True)
print(f"{'='*120}", flush=True)

all_covariates = [c for c in ENV_EXTENDED + list(set(GEOROC_COLS.values())) +
                  list(set(SCI_HQ_COLS.values())) + ANTHROPO_COLS
                  if c in genome_df.columns and genome_df[c].notna().sum() > 100]

top_pairs = results_df.dropna(subset=['A_env_p']).nsmallest(15, 'A_env_p')

var_effects = []
for env_var in all_covariates:
    attenuations = []
    for _, row in top_pairs.iterrows():
        res = run_controlled_analysis(genome_df, row.ko_id, 'PF1_' + row.metal,
                                      [env_var], usable_genera)
        if res:
            atten = 1.0 - abs(res['meta_rho']) / max(abs(row.rho_uncorrected), 1e-6)
            attenuations.append(atten)

    if attenuations:
        var_effects.append({
            'variable': env_var,
            'mean_atten': np.mean(attenuations),
            'median_atten': np.median(attenuations),
            'n_tested': len(attenuations),
        })

if var_effects:
    vdf = pd.DataFrame(var_effects).sort_values('mean_atten', ascending=False)
    print(f"\n{'Variable':40s} {'Mean atten':>10s} {'Median':>10s} {'n':>4s}", flush=True)
    print('-' * 70, flush=True)
    for _, v in vdf.iterrows():
        print(f"  {v.variable:40s} {v.mean_atten:+10.0%} {v.median_atten:+10.0%} {v.n_tested:4.0f}",
              flush=True)


# ── 8. Save ─────────────────────────────────────────────────────────────
out_path = CME / 'env_controlled_full_results.csv'
results_df.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}", flush=True)
print("DONE.", flush=True)

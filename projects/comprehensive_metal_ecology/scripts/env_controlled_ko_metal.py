#!/usr/bin/env python3
"""
Multi-environmental-variable controlled KO × metal analysis.

Question: Do within-genus KO-metal associations survive after controlling
for pH, soil organic carbon, clay content, temperature, and precipitation?

Method:
  For each KO × metal pair that survived within-genus FDR:
    1. Within each genus, regress metal on env covariates → metal_residual
    2. Point-biserial correlation: KO presence vs metal_residual
    3. Meta-analyze across genera (inverse-variance weighted)
    4. Compare to uncorrected within-genus effect

This answers: "After removing the portion of metal variation explained by
soil/climate gradients, does KO still covary with metal?"
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
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct', 'mean_annual_temp_C', 'mean_annual_precip_mm']

# KOs that survived within-genus FDR<0.05 (from both original and extended analyses)
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

# ── 1. Load data ──────────────────────────────────────────────────────────
print("Loading genome-level KO matrix...")
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
print(f"  Genomes: {len(genome_df):,}, KOs: {len(TARGET_KOS)}")

print("Loading environmental covariates...")
env = pd.read_csv(CME / 'genome_env_covariates.csv')
print(f"  Env data: {len(env):,} genomes")
for col in ENV_COLS:
    if col in env.columns:
        n = env[col].notna().sum()
        print(f"    {col}: {n:,} non-null")

genome_df = genome_df.merge(env[['genome_id'] + [c for c in ENV_COLS if c in env.columns]],
                            on='genome_id', how='left')

avail_env = [c for c in ENV_COLS if c in genome_df.columns and genome_df[c].notna().sum() > 100]
print(f"\n  Available env covariates: {avail_env}")
env_coverage = genome_df[avail_env].notna().all(axis=1).sum()
print(f"  Genomes with ALL env data: {env_coverage:,}/{len(genome_df):,}")

# ── 2. Within-genus env-controlled analysis ───────────────────────────────
print(f"\n{'='*90}")
print("ENVIRONMENT-CONTROLLED WITHIN-GENUS ANALYSIS")
print(f"{'='*90}")

# Load uncorrected results for comparison
wg1 = pd.read_csv(CME / 'within_genus_ko_metal_results.csv')
wg2 = pd.read_csv(CME / 'within_genus_extended_results.csv')
uncorrected = pd.concat([wg1, wg2]).query("status == 'tested'")

genus_counts = genome_df.genus.value_counts()
usable_genera = genus_counts[genus_counts >= MIN_GENOMES_PER_GENUS]
print(f"Genera with ≥{MIN_GENOMES_PER_GENUS} genomes: {len(usable_genera)}")

results = []
for ko_id, gene_name in TARGET_KOS.items():
    if ko_id not in genome_df.columns:
        continue

    for metal in METALS:
        metal_short = metal.replace('PF1_', '')

        # Check if this pair survived uncorrected within-genus
        uc = uncorrected[(uncorrected.ko_id == ko_id) & (uncorrected.metal == metal_short)]
        if len(uc) == 0 or uc.iloc[0].get('q_fdr', 1.0) >= 0.05:
            continue

        uc_rho = uc.iloc[0]['meta_rho']
        uc_q = uc.iloc[0]['q_fdr']

        genus_effects_raw = []
        genus_effects_ctrl = []

        for genus, n_genomes in usable_genera.items():
            gdf = genome_df[genome_df.genus == genus].copy()
            ko_col = gdf[ko_id].values
            metal_col = gdf[metal].values

            if ko_col.std() == 0 or np.isnan(metal_col).all():
                continue
            prev = ko_col.mean()
            if prev < 0.05 or prev > 0.95:
                continue

            mask_metal = np.isfinite(metal_col)
            if mask_metal.sum() < MIN_GENOMES_PER_GENUS:
                continue

            # RAW (uncorrected) within-genus
            try:
                rho_raw, _ = stats.pointbiserialr(ko_col[mask_metal], metal_col[mask_metal])
                if np.isfinite(rho_raw):
                    se = 1.0 / np.sqrt(mask_metal.sum() - 3) if mask_metal.sum() > 3 else np.nan
                    genus_effects_raw.append({'genus': genus, 'n': mask_metal.sum(),
                                             'rho': rho_raw, 'se': se})
            except:
                pass

            # ENV-CONTROLLED: regress metal on env covariates, correlate residual with KO
            env_mask = mask_metal.copy()
            env_vals = []
            for ec in avail_env:
                ec_vals = gdf[ec].values
                env_mask &= np.isfinite(ec_vals)
                env_vals.append(ec_vals)

            if env_mask.sum() < MIN_GENOMES_PER_GENUS:
                continue

            # Build env matrix for this genus
            X_env = np.column_stack([ev[env_mask] for ev in env_vals])
            # Check for constant columns
            keep_cols = [i for i in range(X_env.shape[1]) if X_env[:, i].std() > 0]
            if len(keep_cols) == 0:
                continue
            X_env = X_env[:, keep_cols]

            y_metal = metal_col[env_mask]
            ko_sub = ko_col[env_mask]

            if ko_sub.std() == 0:
                continue

            # Regress metal on env covariates
            try:
                X_with_const = np.column_stack([np.ones(len(X_env)), X_env])
                betas, residuals, rank, sv = np.linalg.lstsq(X_with_const, y_metal, rcond=None)
                metal_resid = y_metal - X_with_const @ betas

                rho_ctrl, p_ctrl = stats.pointbiserialr(ko_sub, metal_resid)
                if np.isfinite(rho_ctrl):
                    n_eff = env_mask.sum() - len(keep_cols) - 1
                    se = 1.0 / np.sqrt(max(n_eff - 3, 1))
                    genus_effects_ctrl.append({'genus': genus, 'n': env_mask.sum(),
                                              'rho': rho_ctrl, 'se': se,
                                              'n_env_used': len(keep_cols)})
            except:
                continue

        # Meta-analyze CONTROLLED effects
        n_genera_ctrl = len(genus_effects_ctrl)
        if n_genera_ctrl < MIN_GENERA:
            continue

        cdf = pd.DataFrame(genus_effects_ctrl)
        weights = (cdf.n - len(avail_env) - 3).clip(lower=1)
        z_vals = np.arctanh(cdf.rho.clip(-0.999, 0.999))
        meta_z = np.average(z_vals, weights=weights)
        meta_se = 1.0 / np.sqrt(weights.sum())
        meta_z_stat = meta_z / meta_se
        meta_p = 2 * stats.norm.sf(abs(meta_z_stat))
        meta_rho_ctrl = np.tanh(meta_z)

        frac_pos = (cdf.rho > 0).mean()
        n_pos = (cdf.rho > 0).sum()
        sign_p = stats.binomtest(n_pos, n_genera_ctrl, 0.5).pvalue

        # Also re-meta-analyze RAW effects for matched comparison
        rdf = pd.DataFrame(genus_effects_raw)
        if len(rdf) >= MIN_GENERA:
            w_raw = (rdf.n - 3).clip(lower=1)
            z_raw = np.arctanh(rdf.rho.clip(-0.999, 0.999))
            meta_rho_raw = np.tanh(np.average(z_raw, weights=w_raw))
        else:
            meta_rho_raw = uc_rho

        results.append({
            'ko_id': ko_id, 'gene_name': gene_name, 'metal': metal_short,
            'n_genera_raw': len(genus_effects_raw),
            'n_genera_ctrl': n_genera_ctrl,
            'n_genomes_ctrl': int(cdf.n.sum()),
            'meta_rho_raw': meta_rho_raw,
            'meta_rho_ctrl': meta_rho_ctrl,
            'attenuation': 1.0 - abs(meta_rho_ctrl) / max(abs(meta_rho_raw), 1e-6),
            'meta_z_ctrl': meta_z_stat,
            'meta_p_ctrl': meta_p,
            'frac_positive_ctrl': frac_pos,
            'sign_test_p_ctrl': sign_p,
            'uc_q_fdr': uc_q,
            'n_env_covariates': int(cdf.n_env_used.median()),
        })

results_df = pd.DataFrame(results)

if len(results_df) > 0:
    _, q_vals, _, _ = multipletests(results_df.meta_p_ctrl.values, method='fdr_bh')
    results_df['q_fdr_ctrl'] = q_vals

# ── 3. Print results ─────────────────────────────────────────────────────
print(f"\n{'='*100}")
print(f"RESULTS: ENV-CONTROLLED vs UNCORRECTED WITHIN-GENUS")
print(f"{'='*100}")
print(f"Pairs tested: {len(results_df)}")
if len(results_df) > 0:
    print(f"Survive FDR<0.05 after env control: {(results_df.q_fdr_ctrl < 0.05).sum()}")
    print(f"Survive FDR<0.10 after env control: {(results_df.q_fdr_ctrl < 0.10).sum()}")

    print(f"\n{'KO':10s} {'Gene':18s} {'Met':3s} {'n_gen':>5s} {'ρ_raw':>7s} {'ρ_ctrl':>7s} "
          f"{'atten':>6s} {'p_ctrl':>10s} {'q_ctrl':>10s} {'%pos':>5s} {'verdict':>12s}")
    print(f"{'-'*105}")

    for _, r in results_df.sort_values('meta_p_ctrl').iterrows():
        atten_pct = f"{r.attenuation:+.0%}" if np.isfinite(r.attenuation) else "N/A"
        if r.q_fdr_ctrl < 0.001:
            verdict = 'SURVIVES***'
        elif r.q_fdr_ctrl < 0.01:
            verdict = 'SURVIVES**'
        elif r.q_fdr_ctrl < 0.05:
            verdict = 'SURVIVES*'
        elif r.q_fdr_ctrl < 0.10:
            verdict = 'marginal†'
        else:
            verdict = 'FAILS'

        print(f"{r.ko_id:10s} {r.gene_name:18s} {r.metal:3s} {r.n_genera_ctrl:5.0f} "
              f"{r.meta_rho_raw:+7.4f} {r.meta_rho_ctrl:+7.4f} {atten_pct:>6s} "
              f"{r.meta_p_ctrl:10.2e} {r.q_fdr_ctrl:10.4f} {r.frac_positive_ctrl:5.1%} {verdict:>12s}")

# ── 4. Summary by gene family ────────────────────────────────────────────
print(f"\n{'='*90}")
print("SUMMARY BY GENE FAMILY")
print(f"{'='*90}")

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
    'mnmC': ['K15461'],
}

for family, kos in families.items():
    sub = results_df[results_df.ko_id.isin(kos)]
    if len(sub) == 0:
        continue
    n_survive = (sub.q_fdr_ctrl < 0.05).sum()
    n_total = len(sub)

    if n_total == 0:
        continue

    best = sub.loc[sub.meta_p_ctrl.idxmin()]
    mean_atten = sub.attenuation.mean()

    status = "ALL SURVIVE" if n_survive == n_total else \
             f"{n_survive}/{n_total} survive" if n_survive > 0 else "NONE survive"

    print(f"  {family:25s}: {status:20s} | mean attenuation: {mean_atten:+.0%} | "
          f"best: {best.gene_name} × {best.metal} ρ_ctrl={best.meta_rho_ctrl:+.4f}")

# ── 5. Per-environmental-variable analysis ────────────────────────────────
print(f"\n{'='*90}")
print("PER-ENVIRONMENT-VARIABLE ATTENUATION")
print(f"{'='*90}")
print("Testing each env variable individually to identify the dominant confounder...\n")

top_pairs = results_df.nsmallest(15, 'meta_p_ctrl')

for env_var in avail_env:
    print(f"\n--- Controlling for {env_var} ONLY ---")
    single_results = []

    for _, row in top_pairs.iterrows():
        ko_id = row.ko_id
        metal = 'PF1_' + row.metal

        genus_effects = []
        for genus, _ in usable_genera.items():
            gdf = genome_df[genome_df.genus == genus].copy()
            ko_col = gdf[ko_id].values
            metal_col = gdf[metal].values
            env_col = gdf[env_var].values

            if ko_col.std() == 0:
                continue
            prev = ko_col.mean()
            if prev < 0.05 or prev > 0.95:
                continue

            mask = np.isfinite(metal_col) & np.isfinite(env_col)
            if mask.sum() < MIN_GENOMES_PER_GENUS:
                continue

            try:
                X = np.column_stack([np.ones(mask.sum()), env_col[mask]])
                betas, _, _, _ = np.linalg.lstsq(X, metal_col[mask], rcond=None)
                resid = metal_col[mask] - X @ betas

                if ko_col[mask].std() == 0:
                    continue
                rho, _ = stats.pointbiserialr(ko_col[mask], resid)
                if np.isfinite(rho):
                    genus_effects.append({'rho': rho, 'n': mask.sum()})
            except:
                continue

        if len(genus_effects) >= MIN_GENERA:
            edf = pd.DataFrame(genus_effects)
            w = (edf.n - 3).clip(lower=1)
            z = np.arctanh(edf.rho.clip(-0.999, 0.999))
            meta_rho = np.tanh(np.average(z, weights=w))
            atten = 1.0 - abs(meta_rho) / max(abs(row.meta_rho_raw), 1e-6)
            single_results.append({
                'ko_id': row.ko_id, 'gene_name': row.gene_name,
                'metal': row.metal, 'rho_raw': row.meta_rho_raw,
                'rho_ctrl': meta_rho, 'attenuation': atten
            })

    if single_results:
        sdf = pd.DataFrame(single_results)
        mean_att = sdf.attenuation.mean()
        print(f"  Mean attenuation: {mean_att:+.0%}")
        for _, s in sdf.iterrows():
            print(f"    {s.ko_id} ({s.gene_name}) × {s.metal}: "
                  f"ρ_raw={s.rho_raw:+.4f} → ρ_ctrl={s.rho_ctrl:+.4f} "
                  f"(atten={s.attenuation:+.0%})")

# ── 6. Save ───────────────────────────────────────────────────────────────
results_df.to_csv(CME / 'env_controlled_ko_metal_results.csv', index=False)
print(f"\nSaved to {CME / 'env_controlled_ko_metal_results.csv'}")
print("DONE.")

#!/usr/bin/env python3
"""
Negative control: run the same env-controlled KO×metal analysis on
non-metal housekeeping/metabolic genes. If these also show significant
uncorrected associations that attenuate with env covariates, it confirms
ecological confounding drives the signal.

Strategy:
  1. Select ~40 KOs with NO known metal function, covering diverse functions
     (amino acid metabolism, nucleotide metabolism, lipid metabolism, sugar
     transport, flagella, secretion, cell wall, vitamin biosynthesis, etc.)
  2. Run uncorrected within-genus meta-analysis for each × 6 metals
  3. Run Model A (ENV) and Model C (kitchen-sink) on those that pass FDR<0.05
  4. Compare attenuation to metal genes
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

# Non-metal KOs — clearly unrelated to metal metabolism
NONMETAL_KOS = {
    # Amino acid metabolism
    'K01689': 'eno',          # enolase (glycolysis)
    'K01624': 'fbaA',         # fructose-bisphosphate aldolase
    'K00872': 'homoserine_kinase',
    'K01858': 'ipp_isomerase', # isopentenyl-diphosphate isomerase (terpenoid)
    'K01715': 'enoyl_CoA_hydratase',
    'K00432': 'glutathione_perox',  # glutathione peroxidase
    # Nucleotide metabolism
    'K01012': 'biotin_synthase',
    'K00042': 'gluconate_dehydrog',
    'K01610': 'pepck',        # PEP carboxykinase (gluconeogenesis)
    'K01443': 'N_acetylglucosaminidase',
    # Cell wall / membrane
    'K03592': 'mraW',         # S-adenosyl-methyltransferase
    'K03273': 'tolC',         # outer membrane channel
    'K03286': 'TC_OOP',       # outer membrane protein
    'K05838': 'lipid_transfer',
    # Motility / chemotaxis
    'K03327': 'TC_MFS',       # major facilitator superfamily transporter
    'K03182': 'ubiE',         # ubiquinone biosynthesis methyltransferase
    # Sugar transport / metabolism
    'K02028': 'ABC_sugar_perm',  # ABC transporter permease
    'K00684': 'glycosyltransf',
    'K04762': 'sensor_kinase',   # two-component sensor
    # Secretion / regulatory
    'K06346': 'DNA_mismatch_repair',
    'K09001': 'anhydrase',    # carbonic anhydrase
    'K16092': 'beta_lactamase_like',
    'K05592': 'rRNA_methyltransf',
    'K12510': 'yajC',         # preprotein translocase
    'K06183': 'rsuA',         # ribosomal small subunit pseudouridine synthase
    'K13940': 'nrdD_related',
    'K09691': 'ABC_transporter',
    'K18707': 'lactonase',
    'K21449': 'aminotransferase',
    'K05846': 'opp_perm',     # oligopeptide permease
}

METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']

ENV_EXTENDED = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
                'mean_annual_temp_C', 'mean_annual_precip_mm',
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


# ── Load data ──────────────────────────────────────────────────────────
print("Loading genome-level KO matrix for non-metal KOs...", flush=True)
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus',
                              'genome_size', 'latitude', 'longitude'] + METALS)
mg = mg[mg.ko_id.isin(NONMETAL_KOS)].copy()
print(f"  Found {mg.ko_id.nunique()} non-metal KOs, {len(mg):,} rows", flush=True)

genome_meta = mg.groupby('genome_id').first()[
    ['genus', 'genome_size', 'latitude', 'longitude'] + METALS
].reset_index()

# Build wide KO presence matrix (fill absent = 0)
all_genomes = genome_meta.genome_id.unique()
ko_wide = mg.pivot_table(index='genome_id', columns='ko_id',
                         values='present', fill_value=0).reset_index()
ko_wide = ko_wide.reindex(columns=['genome_id'] + list(NONMETAL_KOS.keys()), fill_value=0)
genome_df = genome_meta.merge(ko_wide, on='genome_id')

print(f"  Genomes: {len(genome_df):,}", flush=True)
for ko_id, name in list(NONMETAL_KOS.items())[:5]:
    if ko_id in genome_df.columns:
        prev = genome_df[ko_id].mean()
        print(f"    {ko_id} ({name}): prevalence={prev:.1%}", flush=True)

print("\nLoading env covariates...", flush=True)
env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols_to_merge = [c for c in env_full.columns
                     if c not in ('latitude', 'longitude') and c != 'genome_id']
genome_df = genome_df.merge(env_full[['genome_id'] + env_cols_to_merge],
                            on='genome_id', how='left')

genus_counts = genome_df.genus.value_counts()
usable_genera = genus_counts[genus_counts >= MIN_GENOMES_PER_GENUS]
print(f"Genera with ≥{MIN_GENOMES_PER_GENUS} genomes: {len(usable_genera)}", flush=True)


# ── Analysis engine ────────────────────────────────────────────────────

def run_within_genus(genome_df, ko_id, metal_pf1, usable_genera, covariates=None):
    genus_effects = []
    for genus in usable_genera.index:
        gdf = genome_df[genome_df.genus == genus]
        ko_col = gdf[ko_id].values
        metal_col = gdf[metal_pf1].values

        if ko_col.std() == 0 or np.isnan(metal_col).all():
            continue
        prev = ko_col.mean()
        if prev < 0.05 or prev > 0.95:
            continue

        mask = np.isfinite(metal_col)

        if covariates:
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
                    genus_effects.append({'genus': genus, 'n': mask.sum(),
                                          'rho': rho, 'n_covs': len(keep)})
            except:
                continue
        else:
            if mask.sum() < MIN_GENOMES_PER_GENUS:
                continue
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

    return {
        'n_genera': len(cdf),
        'n_genomes': int(cdf.n.sum()),
        'meta_rho': meta_rho,
        'meta_z': meta_z_stat,
        'meta_p': meta_p,
        'median_covs': median_covs,
    }


# ── Step 1: Uncorrected analysis ──────────────────────────────────────
print(f"\n{'='*100}", flush=True)
print("STEP 1: UNCORRECTED WITHIN-GENUS META-ANALYSIS (non-metal genes)", flush=True)
print(f"{'='*100}\n", flush=True)

uncorrected_results = []
for ko_id, gene_name in NONMETAL_KOS.items():
    if ko_id not in genome_df.columns:
        continue
    prev = genome_df[ko_id].mean()
    if prev < 0.05 or prev > 0.95:
        continue

    for metal in METALS:
        res = run_within_genus(genome_df, ko_id, metal, usable_genera, covariates=None)
        if res:
            uncorrected_results.append({
                'ko_id': ko_id, 'gene_name': gene_name, 'metal': metal.replace('PF1_', ''),
                'prevalence': prev, **res
            })

uc_df = pd.DataFrame(uncorrected_results)
if len(uc_df) > 0:
    _, q_vals, _, _ = multipletests(uc_df.meta_p.values, method='fdr_bh')
    uc_df['q_fdr'] = q_vals
    n_sig = (uc_df.q_fdr < 0.05).sum()
    n_sig_10 = (uc_df.q_fdr < 0.10).sum()
    print(f"Tested: {len(uc_df)} pairs | Significant at FDR<0.05: {n_sig} | FDR<0.10: {n_sig_10}")
    print(f"\nMean |ρ| of significant pairs: {uc_df[uc_df.q_fdr < 0.05].meta_rho.abs().mean():.4f}" if n_sig > 0 else "")

    if n_sig > 0:
        print(f"\nSignificant non-metal KO × metal pairs:")
        for _, r in uc_df[uc_df.q_fdr < 0.05].sort_values('q_fdr').iterrows():
            print(f"  {r.ko_id} {r.gene_name:25s} × {r.metal:3s}: "
                  f"ρ={r.meta_rho:+.4f}, p={r.meta_p:.2e}, q={r.q_fdr:.4f}, "
                  f"prev={r.prevalence:.1%}, n_gen={r.n_genera}")
else:
    print("No testable pairs found.")
    import sys; sys.exit(0)


# ── Step 2: Env-controlled analysis on significant pairs ──────────────
print(f"\n{'='*100}", flush=True)
print("STEP 2: ENV-CONTROLLED ANALYSIS (non-metal genes, FDR<0.05 pairs only)", flush=True)
print(f"{'='*100}\n", flush=True)

sig_pairs = uc_df[uc_df.q_fdr < 0.05].copy()

env_covs = [c for c in ENV_EXTENDED if c in genome_df.columns
            and genome_df[c].notna().sum() > 100]

all_metal_covs = [c for c in list(set(GEOROC_COLS.values())) +
                  list(set(GEMAS_COLS.values())) +
                  list(set(SCI_HQ_COLS.values()))
                  if c in genome_df.columns and genome_df[c].notna().sum() > 100]
anthro_covs = [c for c in ANTHROPO_COLS
               if c in genome_df.columns and genome_df[c].notna().sum() > 100]
covs_c = list(dict.fromkeys(env_covs + all_metal_covs + anthro_covs))

controlled_results = []
for _, row in sig_pairs.iterrows():
    res_a = run_within_genus(genome_df, row.ko_id, 'PF1_' + row.metal,
                             usable_genera, covariates=env_covs)
    res_c = run_within_genus(genome_df, row.ko_id, 'PF1_' + row.metal,
                             usable_genera, covariates=covs_c)

    entry = {
        'ko_id': row.ko_id, 'gene_name': row.gene_name, 'metal': row.metal,
        'rho_uncorrected': row.meta_rho, 'p_uncorrected': row.meta_p,
    }
    for label, res in [('A_env', res_a), ('C_all', res_c)]:
        if res:
            entry[f'{label}_rho'] = res['meta_rho']
            entry[f'{label}_p'] = res['meta_p']
            entry[f'{label}_n_genera'] = res['n_genera']
            entry[f'{label}_atten'] = 1.0 - abs(res['meta_rho']) / max(abs(row.meta_rho), 1e-6)
        else:
            entry[f'{label}_rho'] = np.nan
            entry[f'{label}_p'] = np.nan
            entry[f'{label}_n_genera'] = 0
            entry[f'{label}_atten'] = np.nan

    controlled_results.append(entry)

ctrl_df = pd.DataFrame(controlled_results)

for label in ['A_env', 'C_all']:
    p_col = f'{label}_p'
    valid = ctrl_df[p_col].notna()
    if valid.sum() > 0:
        _, q_vals, _, _ = multipletests(ctrl_df.loc[valid, p_col].values, method='fdr_bh')
        ctrl_df.loc[valid, f'{label}_q'] = q_vals


# ── Print comparison ──────────────────────────────────────────────────
print(f"\n{'='*100}", flush=True)
print("COMPARISON: METAL GENES vs NON-METAL GENES", flush=True)
print(f"{'='*100}\n", flush=True)

print("NON-METAL genes (negative control):")
for label, desc in [('A_env', 'ENV-only'), ('C_all', 'Kitchen-sink')]:
    q_col = f'{label}_q'
    att_col = f'{label}_atten'
    valid = ctrl_df[q_col].notna()
    if valid.sum() == 0:
        print(f"  Model {desc}: no testable pairs")
        continue
    n_survive = (ctrl_df.loc[valid, q_col] < 0.05).sum()
    n_tested = valid.sum()
    mean_att = ctrl_df.loc[valid, att_col].mean()
    median_att = ctrl_df.loc[valid, att_col].median()
    print(f"  Model {desc}: {n_survive}/{n_tested} survive FDR<0.05 | "
          f"mean atten={mean_att:+.0%} | median atten={median_att:+.0%}")

    if n_survive > 0:
        survivors = ctrl_df[valid & (ctrl_df[q_col] < 0.05)].sort_values(f'{label}_p')
        for _, r in survivors.iterrows():
            print(f"    {r.gene_name:25s} × {r.metal:3s}: "
                  f"ρ_raw={r.rho_uncorrected:+.4f} → ρ_ctrl={r[f'{label}_rho']:+.4f} "
                  f"(atten={r[att_col]:+.0%}, q={r[q_col]:.4f})")

# Load metal-gene results for comparison
print("\nMETAL genes (from env_controlled_full_results.csv):")
metal_results = pd.read_csv(CME / 'env_controlled_full_results.csv')
for label, desc in [('A_env', 'ENV-only'), ('C_all', 'Kitchen-sink')]:
    q_col = f'{label}_q'
    att_col = f'{label}_atten'
    valid = metal_results[q_col].notna()
    if valid.sum() == 0:
        continue
    n_survive = (metal_results.loc[valid, q_col] < 0.05).sum()
    n_tested = valid.sum()
    mean_att = metal_results.loc[valid, att_col].mean()
    median_att = metal_results.loc[valid, att_col].median()
    print(f"  Model {desc}: {n_survive}/{n_tested} survive FDR<0.05 | "
          f"mean atten={mean_att:+.0%} | median atten={median_att:+.0%}")

# Detailed table for non-metal genes
print(f"\n{'='*100}", flush=True)
print("DETAILED NON-METAL GENE TABLE", flush=True)
print(f"{'='*100}\n", flush=True)

print(f"{'KO':10s} {'Gene':25s} {'Met':3s} {'ρ_raw':>7s} | "
      f"{'ρ_A':>7s} {'att_A':>6s} {'q_A':>8s} | "
      f"{'ρ_C':>7s} {'att_C':>6s} {'q_C':>8s}")
print('-' * 100)

sort_col = 'A_env_p' if ctrl_df['A_env_p'].notna().any() else 'p_uncorrected'
for _, r in ctrl_df.sort_values(sort_col).iterrows():
    def fmt(v, w=7):
        return f'{v:>{w}.4f}' if pd.notna(v) else f'{"N/A":>{w}s}'
    def fmt_att(a):
        return f'{a:+5.0%} ' if pd.notna(a) else '  N/A '

    print(f"{r.ko_id:10s} {r.gene_name:25s} {r.metal:3s} {r.rho_uncorrected:+7.4f} | "
          f"{fmt(r.get('A_env_rho'))} {fmt_att(r.get('A_env_atten'))} {fmt(r.get('A_env_q'), 8)} | "
          f"{fmt(r.get('C_all_rho'))} {fmt_att(r.get('C_all_atten'))} {fmt(r.get('C_all_q'), 8)}")


# ── Summary statistics ────────────────────────────────────────────────
print(f"\n{'='*100}", flush=True)
print("SUMMARY STATISTICS", flush=True)
print(f"{'='*100}\n", flush=True)

print(f"Non-metal KOs tested (uncorrected): {uc_df.ko_id.nunique()}")
print(f"Non-metal pairs tested: {len(uc_df)}")
print(f"Non-metal pairs significant (FDR<0.05): {(uc_df.q_fdr < 0.05).sum()}")
print(f"Fraction significant: {(uc_df.q_fdr < 0.05).mean():.1%}")
print(f"Mean |ρ| significant: {uc_df[uc_df.q_fdr < 0.05].meta_rho.abs().mean():.4f}")

# Compare to metal genes
metal_uc = pd.concat([
    pd.read_csv(CME / 'within_genus_ko_metal_results.csv'),
    pd.read_csv(CME / 'within_genus_extended_results.csv')
]).query("status == 'tested'")
print(f"\nMetal KOs tested (uncorrected): {metal_uc.ko_id.nunique()}")
print(f"Metal pairs tested: {len(metal_uc)}")
print(f"Metal pairs significant (FDR<0.05): {(metal_uc.q_fdr < 0.05).sum()}")
print(f"Fraction significant: {(metal_uc.q_fdr < 0.05).mean():.1%}")
print(f"Mean |ρ| significant: {metal_uc[metal_uc.q_fdr < 0.05].meta_rho.abs().mean():.4f}")

ctrl_df.to_csv(CME / 'env_controlled_nonmetal_results.csv', index=False)
uc_df.to_csv(CME / 'nonmetal_uncorrected_results.csv', index=False)
print(f"\nSaved results to data/")
print("DONE.")

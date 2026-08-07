#!/usr/bin/env python3
"""
Unified confound dissection across all genome databases.

Runs the same within-genus partial-correlation → inverse-variance meta-analysis
pipeline on each database's KO matrix parquet, then produces a cross-database
comparison table.

Databases processed:
  - MGnify (8,585 genomes, from per_ko_metal_associations)
  - SPIRE (4,782 genomes, from db_ko_matrices)
  - ke_pangenome (83K genomes, from db_ko_matrices)
  - carbon_source_phenotypes (from db_ko_matrices, if available)
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

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUTDIR = DATA / 'confound_results'
OUTDIR.mkdir(exist_ok=True)

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


def run_meta(df, ko_id, metal_col, covariates=None):
    """Within-genus meta-analysis with optional partial correlation."""
    genus_cts = df.genus.value_counts()
    genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index

    effects = []
    for genus in genera:
        gdf = df[df.genus == genus]
        ko = gdf[ko_id].values
        met = gdf[metal_col].values

        if ko.std() == 0 or np.isnan(met).all():
            continue
        prev = ko.mean()
        if prev < 0.05 or prev > 0.95:
            continue

        mask = np.isfinite(met)
        n_covs = 0

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
                        b, _, _, _ = np.linalg.lstsq(Xf, met[mask], rcond=None)
                        resid = met[mask] - Xf @ b
                        rho, _ = stats.pointbiserialr(ko_sub, resid)
                        if np.isfinite(rho):
                            effects.append((mask.sum(), rho, len(keep)))
                        continue
                    except:
                        continue

            try:
                rho, _ = stats.pointbiserialr(ko_sub, met[mask])
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
            rho, _ = stats.pointbiserialr(ko_sub, met[mask])
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


def genome_wide_raw_scan(genome_df, ko_cols, metals=METALS, min_genera=MIN_GENERA):
    """Raw within-genus meta-analysis across all variable KOs."""
    genus_cts = genome_df.genus.value_counts()
    usable = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index
    genus_idx = {g: genome_df.index[genome_df.genus == g].values for g in usable}

    results = []
    for i, ko_id in enumerate(ko_cols):
        if (i + 1) % 500 == 0:
            print(f"    KO {i+1}/{len(ko_cols)}...", flush=True)
        ko_vals = genome_df[ko_id].values
        for metal in metals:
            met_vals = genome_df[metal].values
            effects = []
            for genus, idx in genus_idx.items():
                ko = ko_vals[idx]
                met = met_vals[idx]
                mask = np.isfinite(met)
                if mask.sum() < MIN_GENOMES_PER_GENUS:
                    continue
                ko_m = ko[mask]
                if ko_m.std() == 0:
                    continue
                prev = ko_m.mean()
                if prev < 0.05 or prev > 0.95:
                    continue
                try:
                    rho, _ = stats.pointbiserialr(ko_m, met[mask])
                    if np.isfinite(rho):
                        effects.append((mask.sum(), rho))
                except:
                    continue
            if len(effects) < min_genera:
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
                'ko_id': ko_id, 'metal': metal.replace('PF1_', ''),
                'is_target': ko_id in TARGET_KOS,
                'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects)
            })

    if not results:
        return pd.DataFrame()
    rdf = pd.DataFrame(results)
    _, q_vals, _, _ = multipletests(rdf.meta_p.values, method='fdr_bh')
    rdf['q_fdr'] = q_vals
    return rdf


def process_database(db_name, parquet_path, is_long_format=True):
    """Run full confound dissection on one database."""
    print(f"\n{'#'*100}", flush=True)
    print(f"DATABASE: {db_name}", flush=True)
    print(f"{'#'*100}\n", flush=True)

    df = pd.read_parquet(parquet_path)
    print(f"  Loaded: {len(df):,} rows, {df.genome_id.nunique():,} genomes")
    print(f"  Columns: {sorted(df.columns.tolist())}")

    # Determine which metals are available
    avail_metals = [m for m in METALS if m in df.columns and df[m].notna().sum() > 100]
    print(f"  Available metals: {avail_metals}")
    if not avail_metals:
        print("  ERROR: No metals with sufficient data!")
        return None

    # Build genome-level DataFrame
    if is_long_format:
        genome_meta = df.groupby('genome_id').first()[
            [c for c in ['genus', 'phylum', 'genome_size', 'latitude', 'longitude']
             + avail_metals + ENV_COLS if c in df.columns]
        ].reset_index()

        # Find variable KOs
        ko_counts = df.groupby('ko_id')['genome_id'].nunique()
        n_genomes = df.genome_id.nunique()
        ko_prev = ko_counts / n_genomes
        variable_kos = ko_prev[(ko_prev >= 0.05) & (ko_prev <= 0.95)].index.tolist()
        target_kos_present = [k for k in TARGET_KOS if k in set(df.ko_id)]
        print(f"  Variable KOs: {len(variable_kos):,} (target KOs present: {len(target_kos_present)})")

        # Pivot to wide
        ko_wide = df[df.ko_id.isin(set(variable_kos) | set(TARGET_KOS.keys()))].pivot_table(
            index='genome_id', columns='ko_id', values='present', fill_value=0)
        genome_df = genome_meta.set_index('genome_id').join(ko_wide, how='left').fillna(0).reset_index()
    else:
        genome_df = df.copy()
        variable_kos = [c for c in df.columns if c.startswith('K') and c[1:].isdigit()
                        and 0.05 <= df[c].mean() <= 0.95]
        target_kos_present = [k for k in TARGET_KOS if k in df.columns]

    # Genus stats
    genus_cts = genome_df.genus.value_counts()
    usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS]
    print(f"  Total genera: {genome_df.genus.nunique()}")
    print(f"  Usable genera (≥{MIN_GENOMES_PER_GENUS}): {len(usable_genera)}")

    if len(usable_genera) < MIN_GENERA:
        print(f"  SKIP: Too few usable genera ({len(usable_genera)} < {MIN_GENERA})")
        return None

    # ── 1. Genome-wide raw scan ──
    print(f"\n  Running genome-wide raw scan ({len(variable_kos)} KOs × {len(avail_metals)} metals)...",
          flush=True)
    raw_scan = genome_wide_raw_scan(genome_df, variable_kos, avail_metals)
    n_sig = (raw_scan.q_fdr < 0.05).sum() if len(raw_scan) > 0 else 0
    print(f"  Raw scan: {n_sig}/{len(raw_scan)} pairs significant (FDR<0.05)")

    raw_scan_path = OUTDIR / f'{db_name}_genomewide_raw_scan.csv'
    raw_scan.to_csv(raw_scan_path, index=False)

    # ── 2. Target KO ablation ──
    # Use raw-significant target KO pairs for ablation
    sig_targets = raw_scan[(raw_scan.q_fdr < 0.05) & raw_scan.is_target].copy()
    if len(sig_targets) == 0:
        sig_targets = raw_scan[raw_scan.is_target].nsmallest(20, 'meta_p').copy()
    if len(sig_targets) == 0:
        print("  No target KOs testable — skipping ablation")
        ablation_summary = pd.DataFrame()
    else:
        print(f"\n  Covariate ablation on {len(sig_targets)} target pairs...", flush=True)
        avail_env = [c for c in ENV_COLS if c in genome_df.columns
                     and genome_df[c].notna().sum() > len(genome_df) * 0.3]

        covariate_sets = {
            'Raw (none)': [],
            'Genome size only': ['genome_size'],
        }
        if avail_env:
            for ec in avail_env:
                covariate_sets[f'{ec} only'] = [ec]
            covariate_sets['GS + all ENV'] = ['genome_size'] + avail_env

        ablation_rows = []
        for cov_name, covs in covariate_sets.items():
            covs_use = [c for c in covs if c in genome_df.columns] if covs else None
            results = []
            for _, row in sig_targets.iterrows():
                res = run_meta(genome_df, row.ko_id, 'PF1_' + row.metal, covs_use)
                if res:
                    atten = 1.0 - abs(res['meta_rho']) / max(abs(row.meta_rho), 1e-6)
                    results.append({'ko_id': row.ko_id, 'metal': row.metal,
                                    'rho': res['meta_rho'], 'p': res['meta_p'],
                                    'atten': atten, 'n_genera': res['n_genera']})

            if results:
                rdf = pd.DataFrame(results)
                _, q_vals, _, _ = multipletests(rdf.p.values, method='fdr_bh')
                rdf['q'] = q_vals
                n_survive = (rdf.q < 0.05).sum()
                ablation_rows.append({
                    'covariate_set': cov_name, 'n_tested': len(rdf),
                    'n_survive': n_survive, 'mean_atten': rdf.atten.mean()
                })

        ablation_summary = pd.DataFrame(ablation_rows)
        print(f"\n  {'Covariate set':40s} {'Tested':>6s} {'Survive':>7s} {'Mean att':>9s}")
        print('  ' + '-' * 65)
        for _, r in ablation_summary.iterrows():
            print(f"  {r.covariate_set:40s} {r.n_tested:6.0f} {r.n_survive:7.0f} {r.mean_atten:+8.0%}")

    # ── 3. Per-metal breakdown ──
    print(f"\n  Per-metal raw scan summary:")
    for m in [ms.replace('PF1_', '') for ms in avail_metals]:
        sub = raw_scan[raw_scan.metal == m]
        n = (sub.q_fdr < 0.05).sum()
        print(f"    {m:4s}: {n:>5d}/{len(sub):>5d} significant ({n/max(len(sub),1):.1%})")

    # ── 4. Top hits ──
    if len(raw_scan) > 0:
        print(f"\n  Top 20 raw hits:")
        top = raw_scan.nsmallest(20, 'meta_p')
        for _, r in top.iterrows():
            tag = '*' if r.is_target else ' '
            gene = TARGET_KOS.get(r.ko_id, r.ko_id)
            sig = 'Y' if r.q_fdr < 0.05 else 'n'
            print(f"   {tag} {gene:18s} × {r.metal:3s}: ρ={r.meta_rho:+.4f} "
                  f"p={r.meta_p:.2e} q={r.q_fdr:.4f} [{sig}] ({r.n_genera} genera)")

    return {
        'db_name': db_name, 'n_genomes': genome_df.genome_id.nunique(),
        'n_genera': len(usable_genera),
        'n_variable_kos': len(variable_kos), 'n_metals': len(avail_metals),
        'n_tested': len(raw_scan), 'n_sig_raw': n_sig,
        'pct_sig': n_sig / max(len(raw_scan), 1),
        'n_target_present': len(target_kos_present),
        'raw_scan': raw_scan, 'ablation': ablation_summary,
    }


# ════════════════════════════════════════════════════════════════════════
# MAIN — process all databases
# ════════════════════════════════════════════════════════════════════════

databases = {}

# 1. MGnify (original)
mgnify_path = Path('/home/hmacgregor/BERIL-research-observatory/projects/per_ko_metal_associations/data/mgnify_all_ko_matrix.parquet')
if mgnify_path.exists():
    databases['mgnify'] = mgnify_path

# 2-4. From db_ko_matrices
ko_dir = DATA / 'db_ko_matrices'
for pq in sorted(ko_dir.glob('*.parquet')):
    db_name = pq.stem.replace('_ko_matrix', '')
    databases[db_name] = pq

print(f"Found {len(databases)} databases to process:")
for name, path in databases.items():
    print(f"  {name}: {path}")

all_results = {}
for db_name, path in databases.items():
    try:
        result = process_database(db_name, path)
        if result:
            all_results[db_name] = result
    except Exception as e:
        print(f"\n  ERROR processing {db_name}: {e}")
        import traceback
        traceback.print_exc()
        continue


# ════════════════════════════════════════════════════════════════════════
# CROSS-DATABASE COMPARISON
# ════════════════════════════════════════════════════════════════════════
print(f"\n\n{'#'*100}", flush=True)
print("CROSS-DATABASE COMPARISON", flush=True)
print(f"{'#'*100}\n", flush=True)

# Summary table
print(f"{'Database':25s} {'Genomes':>8s} {'Genera':>7s} {'KOs':>7s} {'Metals':>7s} "
      f"{'Tested':>7s} {'Sig':>5s} {'%Sig':>6s}")
print('-' * 85)
for name, r in all_results.items():
    print(f"  {name:25s} {r['n_genomes']:>8,d} {r['n_genera']:>7d} "
          f"{r['n_variable_kos']:>7,d} {r['n_metals']:>7d} "
          f"{r['n_tested']:>7,d} {r['n_sig_raw']:>5d} {r['pct_sig']:>5.1%}")

# Cross-database replication: which KO×metal pairs are significant in ≥2 databases?
if len(all_results) >= 2:
    print(f"\n\nCross-database replication:")
    all_sig = []
    for name, r in all_results.items():
        scan = r['raw_scan']
        sig = scan[scan.q_fdr < 0.05][['ko_id', 'metal', 'meta_rho']].copy()
        sig['db'] = name
        all_sig.append(sig)

    if all_sig:
        combined = pd.concat(all_sig)
        pair_counts = combined.groupby(['ko_id', 'metal']).agg(
            n_dbs=('db', 'nunique'),
            dbs=('db', lambda x: ','.join(sorted(x))),
            rhos=('meta_rho', lambda x: list(x.round(4)))
        ).reset_index()

        replicated = pair_counts[pair_counts.n_dbs >= 2].sort_values('n_dbs', ascending=False)
        print(f"  Pairs significant in ≥2 databases: {len(replicated)}")

        if len(replicated) > 0:
            # Check direction concordance
            concordant = 0
            for _, row in replicated.iterrows():
                rhos = row.rhos
                if all(r > 0 for r in rhos) or all(r < 0 for r in rhos):
                    concordant += 1

            print(f"  Direction concordance: {concordant}/{len(replicated)} "
                  f"({concordant/len(replicated):.0%})")

            print(f"\n  Top replicated pairs:")
            for _, row in replicated.head(30).iterrows():
                gene = TARGET_KOS.get(row.ko_id, row.ko_id)
                tag = '*' if row.ko_id in TARGET_KOS else ' '
                rhos_str = ', '.join(f'{r:+.4f}' for r in row.rhos)
                print(f"   {tag} {gene:18s} × {row.metal:3s}: {row.n_dbs} dbs "
                      f"({row.dbs}) ρ=[{rhos_str}]")

        replicated.to_csv(OUTDIR / 'cross_database_replicated.csv', index=False)

print("\nDONE — All results saved to", OUTDIR)

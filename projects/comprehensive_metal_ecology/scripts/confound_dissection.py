#!/usr/bin/env python3
"""
Systematic confound dissection for KO × metal associations.

Questions addressed:
  1. Which individual covariates cause the most attenuation?
  2. What's the biome composition and does biome drive associations?
  3. Does soil-only subsetting change results?
  4. Is phylum a confounder?
  5. Does genome size matter after biome/phylum control?
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
GEO_CSV = Path('/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/final_mags_geospatial_traits.csv')

MIN_GENOMES_PER_GENUS = 8
MIN_GENERA = 10
METALS = ['PF1_Hg', 'PF1_As', 'PF1_Cu', 'PF1_Cr', 'PF1_Cd', 'PF1_Pb']

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

# ── Load ───────────────────────────────────────────────────────────────
print("Loading data...", flush=True)
mg = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                     columns=['genome_id', 'ko_id', 'present', 'genus', 'phylum',
                              'genome_size', 'latitude', 'longitude'] + METALS)
mg = mg[mg.ko_id.isin(TARGET_KOS)].copy()

genome_meta = mg.groupby('genome_id').first()[
    ['genus', 'phylum', 'genome_size', 'latitude', 'longitude'] + METALS
].reset_index()
ko_wide = mg.pivot_table(index='genome_id', columns='ko_id',
                         values='present', fill_value=0).reset_index()
genome_df = genome_meta.merge(ko_wide, on='genome_id')

# Add biome
geo = pd.read_csv(GEO_CSV, usecols=['genome_id', 'biome_name'])
genome_df = genome_df.merge(geo, on='genome_id', how='left')
genome_df['is_soil'] = genome_df.biome_name.str.lower().str.contains('soil|rhizo', na=False)
genome_df['biome_broad'] = genome_df.biome_name.fillna('Unknown').apply(
    lambda x: 'Soil' if 'soil' in x.lower() else
              'Rhizosphere' if 'rhizo' in x.lower() else
              'Marine Sediment' if 'sediment' in x.lower() else
              'Marine' if 'marine' in x.lower() else 'Other')

# Add env covariates
env_full = pd.read_csv(CME / 'genome_env_covariates_full.csv')
env_cols = [c for c in env_full.columns if c not in ('latitude', 'longitude', 'genome_id')]
genome_df = genome_df.merge(env_full[['genome_id'] + env_cols], on='genome_id', how='left')

# Get uncorrected significant pairs
wg1 = pd.read_csv(CME / 'within_genus_ko_metal_results.csv')
wg2 = pd.read_csv(CME / 'within_genus_extended_results.csv')
uncorrected = pd.concat([wg1, wg2]).query("status == 'tested'")
sig_pairs = uncorrected[uncorrected.q_fdr < 0.05][['ko_id', 'gene_name', 'metal', 'meta_rho']].copy()
sig_pairs = sig_pairs.rename(columns={'meta_rho': 'rho_raw'})

print(f"  Genomes: {len(genome_df):,}", flush=True)
print(f"  Significant uncorrected pairs: {len(sig_pairs)}", flush=True)


# ════════════════════════════════════════════════════════════════════════
# SECTION 1: Biome composition and confounding
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*100}", flush=True)
print("SECTION 1: BIOME COMPOSITION AND CONFOUNDING", flush=True)
print(f"{'='*100}\n", flush=True)

print("Biome distribution:")
biome_counts = genome_df.biome_broad.value_counts()
for b, n in biome_counts.items():
    print(f"  {b:20s}: {n:,} ({n/len(genome_df):.1%})")

print("\nMetal concentrations by biome:")
for m in METALS:
    ms = m.replace('PF1_', '')
    print(f"\n  {ms}:")
    for b in ['Soil', 'Rhizosphere', 'Marine Sediment', 'Marine']:
        sub = genome_df[genome_df.biome_broad == b]
        vals = sub[m].dropna()
        if len(vals) > 0:
            print(f"    {b:20s}: median={vals.median():+.4f}, mean={vals.mean():+.4f}, n={len(vals)}")

    # ANOVA across biomes
    groups = [genome_df.loc[genome_df.biome_broad == b, m].dropna().values
              for b in ['Soil', 'Marine Sediment', 'Marine']]
    groups = [g for g in groups if len(g) > 10]
    if len(groups) >= 2:
        F, p = stats.f_oneway(*groups)
        print(f"    ANOVA F={F:.1f}, p={p:.2e}")

print("\nGenome size by biome:")
for b in ['Soil', 'Rhizosphere', 'Marine Sediment', 'Marine']:
    sub = genome_df[genome_df.biome_broad == b]
    print(f"  {b:20s}: median={sub.genome_size.median()/1e6:.1f}M, "
          f"mean={sub.genome_size.mean()/1e6:.1f}M")

print("\nKO prevalence by biome (target KOs):")
for ko_id in ['K01546', 'K04655', 'K08364', 'K07497', 'K02863']:
    if ko_id not in genome_df.columns:
        continue
    gene = TARGET_KOS[ko_id]
    prev_all = genome_df[ko_id].mean()
    line = f"  {gene:18s} (all={prev_all:.1%})"
    for b in ['Soil', 'Marine Sediment', 'Marine']:
        sub = genome_df[genome_df.biome_broad == b]
        if len(sub) > 0:
            p = sub[ko_id].mean()
            line += f" | {b[:6]}={p:.1%}"
    print(line)

print("\nPhylum distribution by biome:")
for b in ['Soil', 'Marine Sediment', 'Marine']:
    sub = genome_df[genome_df.biome_broad == b]
    top = sub.phylum.value_counts().head(5)
    print(f"\n  {b} (n={len(sub):,}):")
    for ph, n in top.items():
        print(f"    {ph:30s}: {n:,} ({n/len(sub):.1%})")


# ════════════════════════════════════════════════════════════════════════
# SECTION 2: Covariate ablation — which covariates drive attenuation?
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*100}", flush=True)
print("SECTION 2: COVARIATE ABLATION", flush=True)
print(f"{'='*100}\n", flush=True)

genus_counts = genome_df.genus.value_counts()
usable_genera = genus_counts[genus_counts >= MIN_GENOMES_PER_GENUS]


def run_meta(df, ko_id, metal_pf1, covariates=None):
    """Within-genus meta-analysis with optional covariates."""
    genus_cts = df.genus.value_counts()
    genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS].index
    effects = []

    for genus in genera:
        gdf = df[df.genus == genus]
        ko = gdf[ko_id].values
        met = gdf[metal_pf1].values

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

            # Fallback: no valid covariates
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


# Test each covariate set systematically
covariate_sets = {
    'Raw (none)': [],
    'Genome size only': ['genome_size'],
    'pH only': ['ph_h2o'],
    'Temperature only': ['mean_annual_temp_C'],
    'Precipitation only': ['mean_annual_precip_mm'],
    'Elevation only': ['elevation_m'],
    'OC only': ['organic_carbon_density'],
    'Clay only': ['clay_pct'],
    'Lithology only': ['litho_mafic_score'],
    'GS + pH + OC + clay': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct'],
    'GS + temp + precip': ['genome_size', 'mean_annual_temp_C', 'mean_annual_precip_mm'],
    'GS + all soil': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                       'mean_annual_temp_C', 'mean_annual_precip_mm'],
    'GS + all ENV': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                     'mean_annual_temp_C', 'mean_annual_precip_mm',
                     'elevation_m', 'litho_mafic_score'],
    'GS + ENV + Sci2025': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                            'mean_annual_temp_C', 'mean_annual_precip_mm',
                            'elevation_m', 'litho_mafic_score',
                            'sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr',
                            'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb'],
    'Kitchen sink': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                     'mean_annual_temp_C', 'mean_annual_precip_mm',
                     'elevation_m', 'litho_mafic_score',
                     'georoc_Cu', 'georoc_Ni', 'georoc_Zn', 'georoc_Co', 'georoc_Cr',
                     'georoc_Pb', 'georoc_As', 'georoc_Cd', 'georoc_U',
                     'gemas_Cu', 'gemas_Pb', 'gemas_Ni', 'gemas_Cr', 'gemas_Co',
                     'gemas_Zn', 'gemas_As', 'gemas_Cd', 'gemas_Hg',
                     'sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr',
                     'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb',
                     'tri_facility_count_50km', 'mine_min_dist_km',
                     'cmmi_min_dist_km', 'mine_count_50km'],
}

ablation_results = {}
for cov_name, covs in covariate_sets.items():
    covs_avail = [c for c in covs if c in genome_df.columns] if covs else None
    results = []
    for _, row in sig_pairs.iterrows():
        res = run_meta(genome_df, row.ko_id, 'PF1_' + row.metal, covs_avail)
        if res:
            atten = 1.0 - abs(res['meta_rho']) / max(abs(row.rho_raw), 1e-6)
            results.append({'ko_id': row.ko_id, 'metal': row.metal,
                            'rho': res['meta_rho'], 'p': res['meta_p'],
                            'atten': atten, 'n_genera': res['n_genera']})

    if results:
        rdf = pd.DataFrame(results)
        _, q_vals, _, _ = multipletests(rdf.p.values, method='fdr_bh')
        rdf['q'] = q_vals
        n_survive = (rdf.q < 0.05).sum()
        mean_att = rdf.atten.mean()
        ablation_results[cov_name] = {'n_tested': len(rdf), 'n_survive': n_survive,
                                       'mean_atten': mean_att, 'detail': rdf}

print(f"{'Covariate set':40s} {'Tested':>6s} {'Survive':>7s} {'Mean att':>9s}")
print('-' * 65)
for name, info in ablation_results.items():
    print(f"  {name:40s} {info['n_tested']:6d} {info['n_survive']:7d} {info['mean_atten']:+8.0%}")


# ════════════════════════════════════════════════════════════════════════
# SECTION 3: Soil-only analysis
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*100}", flush=True)
print("SECTION 3: SOIL-ONLY SUBSET", flush=True)
print(f"{'='*100}\n", flush=True)

soil_df = genome_df[genome_df.is_soil].copy()
soil_genus_cts = soil_df.genus.value_counts()
soil_genera = soil_genus_cts[soil_genus_cts >= MIN_GENOMES_PER_GENUS]
print(f"Soil genomes: {len(soil_df):,} | Usable genera: {len(soil_genera)}")

soil_models = {
    'Soil raw': [],
    'Soil + GS': ['genome_size'],
    'Soil + GS + ENV': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                        'mean_annual_temp_C', 'mean_annual_precip_mm',
                        'elevation_m', 'litho_mafic_score'],
    'Soil + kitchen sink': ['genome_size', 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                            'mean_annual_temp_C', 'mean_annual_precip_mm',
                            'elevation_m', 'litho_mafic_score',
                            'sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr',
                            'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb',
                            'georoc_Cu', 'georoc_Ni', 'georoc_Zn', 'georoc_Co', 'georoc_Cr',
                            'georoc_Pb', 'georoc_As', 'georoc_Cd', 'georoc_U',
                            'gemas_Cu', 'gemas_Pb', 'gemas_Ni', 'gemas_Cr', 'gemas_Co',
                            'gemas_Zn', 'gemas_As', 'gemas_Cd', 'gemas_Hg',
                            'tri_facility_count_50km', 'mine_min_dist_km',
                            'cmmi_min_dist_km', 'mine_count_50km'],
}

soil_results = {}
for name, covs in soil_models.items():
    covs_avail = [c for c in covs if c in soil_df.columns] if covs else None
    results = []
    for _, row in sig_pairs.iterrows():
        res = run_meta(soil_df, row.ko_id, 'PF1_' + row.metal, covs_avail)
        if res:
            atten = 1.0 - abs(res['meta_rho']) / max(abs(row.rho_raw), 1e-6)
            results.append({'ko_id': row.ko_id, 'metal': row.metal,
                            'gene_name': row.gene_name,
                            'rho_raw_all': row.rho_raw,
                            'rho': res['meta_rho'], 'p': res['meta_p'],
                            'atten': atten, 'n_genera': res['n_genera']})

    if results:
        rdf = pd.DataFrame(results)
        _, q_vals, _, _ = multipletests(rdf.p.values, method='fdr_bh')
        rdf['q'] = q_vals
        n_survive = (rdf.q < 0.05).sum()
        soil_results[name] = {'n_tested': len(rdf), 'n_survive': n_survive,
                               'mean_atten': rdf.atten.mean(), 'detail': rdf}

print(f"\n{'Model':40s} {'Tested':>6s} {'Survive':>7s} {'Mean att':>9s}")
print('-' * 65)
for name, info in soil_results.items():
    print(f"  {name:40s} {info['n_tested']:6d} {info['n_survive']:7d} {info['mean_atten']:+8.0%}")

# Show survivors in soil raw
if 'Soil raw' in soil_results and soil_results['Soil raw']['n_survive'] > 0:
    print(f"\nSoil raw survivors (FDR<0.05):")
    rdf = soil_results['Soil raw']['detail']
    for _, r in rdf[rdf.q < 0.05].sort_values('p').iterrows():
        print(f"  {r.gene_name:18s} × {r.metal:3s}: ρ_all={r.rho_raw_all:+.4f} → "
              f"ρ_soil={r.rho:+.4f} (q={r.q:.4f}, {r.n_genera} genera)")


# ════════════════════════════════════════════════════════════════════════
# SECTION 4: Biome as explicit covariate vs subsetting
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*100}", flush=True)
print("SECTION 4: BIOME AS COVARIATE vs SUBSETTING", flush=True)
print(f"{'='*100}\n", flush=True)

# Encode biome as dummy variables
genome_df['biome_marine'] = (genome_df.biome_broad == 'Marine').astype(float)
genome_df['biome_marine_sed'] = (genome_df.biome_broad == 'Marine Sediment').astype(float)
genome_df['biome_rhizo'] = (genome_df.biome_broad == 'Rhizosphere').astype(float)

biome_models = {
    'All + biome dummies': ['genome_size', 'biome_marine', 'biome_marine_sed', 'biome_rhizo'],
    'All + biome + ENV': ['genome_size', 'biome_marine', 'biome_marine_sed', 'biome_rhizo',
                          'ph_h2o', 'organic_carbon_density', 'clay_pct',
                          'mean_annual_temp_C', 'mean_annual_precip_mm',
                          'elevation_m', 'litho_mafic_score'],
}

for name, covs in biome_models.items():
    covs_avail = [c for c in covs if c in genome_df.columns]
    results = []
    for _, row in sig_pairs.iterrows():
        res = run_meta(genome_df, row.ko_id, 'PF1_' + row.metal, covs_avail)
        if res:
            atten = 1.0 - abs(res['meta_rho']) / max(abs(row.rho_raw), 1e-6)
            results.append({'rho': res['meta_rho'], 'p': res['meta_p'], 'atten': atten})
    if results:
        rdf = pd.DataFrame(results)
        _, q_vals, _, _ = multipletests(rdf.p.values, method='fdr_bh')
        rdf['q'] = q_vals
        n_surv = (rdf.q < 0.05).sum()
        print(f"  {name:40s}: {n_surv}/{len(rdf)} survive, atten={rdf.atten.mean():+.0%}")


# ════════════════════════════════════════════════════════════════════════
# SECTION 5: Phylum as confound
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*100}", flush=True)
print("SECTION 5: PHYLUM AS CONFOUND", flush=True)
print(f"{'='*100}\n", flush=True)

# Within our within-genus approach, phylum is already largely controlled
# (genera belong to single phyla). But let's verify.
print("Phylum breakdown in within-genus analysis:")
for genus in list(usable_genera.index)[:5]:
    sub = genome_df[genome_df.genus == genus]
    phyla = sub.phylum.unique()
    print(f"  {genus:25s}: {len(sub)} genomes, phylum={phyla}")

# Check if any genus spans multiple phyla
multi_phylum = 0
for genus in usable_genera.index:
    sub = genome_df[genome_df.genus == genus]
    if sub.phylum.nunique() > 1:
        multi_phylum += 1
print(f"\nGenera spanning multiple phyla: {multi_phylum}/{len(usable_genera)}")

# Phylum-level metal correlations
print("\nPhylum-level metal means (top 5 phyla):")
top_phyla = genome_df.phylum.value_counts().head(5).index
for m in ['PF1_Hg', 'PF1_Cu', 'PF1_Pb']:
    ms = m.replace('PF1_', '')
    print(f"\n  {ms}:")
    for ph in top_phyla:
        sub = genome_df[genome_df.phylum == ph]
        vals = sub[m].dropna()
        if len(vals) > 0:
            print(f"    {ph:25s}: mean={vals.mean():+.4f}, n={len(vals)}")


# ════════════════════════════════════════════════════════════════════════
# SECTION 6: Genome-wide non-metal scan on SOIL ONLY
# ════════════════════════════════════════════════════════════════════════
print(f"\n{'='*100}", flush=True)
print("SECTION 6: GENOME-WIDE RAW SCAN — ALL vs SOIL ONLY", flush=True)
print(f"{'='*100}\n", flush=True)

# Load full KO matrix for genome-wide comparison
print("Loading full KO matrix for genome-wide soil comparison...", flush=True)
mg_full = pd.read_parquet(DATA / 'mgnify_all_ko_matrix.parquet',
                          columns=['genome_id', 'ko_id', 'present', 'genus',
                                   'genome_size', 'latitude', 'longitude'] + METALS)

genome_full = mg_full.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()
genome_full = genome_full.merge(geo, on='genome_id', how='left')
genome_full['is_soil'] = genome_full.biome_name.str.lower().str.contains('soil|rhizo', na=False)

# Use the raw scan results we already have
raw_scan = pd.read_csv(CME / 'genomewide_raw_scan.csv')
n_sig_all = (raw_scan.raw_q < 0.05).sum()
print(f"All biomes: {n_sig_all}/{len(raw_scan)} pairs significant (FDR<0.05)")

# Run raw scan on soil only for a sample of KOs
print("Running soil-only raw scan on variable KOs...", flush=True)
soil_full_ids = set(genome_full[genome_full.is_soil].genome_id)
mg_soil = mg_full[mg_full.genome_id.isin(soil_full_ids)]

soil_genome_meta = mg_soil.drop_duplicates('genome_id')[
    ['genome_id', 'genus', 'genome_size', 'latitude', 'longitude'] + METALS
].copy()

ko_counts_soil = mg_soil.groupby('ko_id')['genome_id'].nunique()
ko_prev_soil = ko_counts_soil / len(soil_full_ids)
variable_soil = ko_prev_soil[(ko_prev_soil >= 0.05) & (ko_prev_soil <= 0.95)]
print(f"  Soil genomes: {len(soil_full_ids):,}, variable KOs: {len(variable_soil):,}")

# Build presence matrix for soil
ko_wide_soil = mg_soil[mg_soil.ko_id.isin(variable_soil.index)].pivot_table(
    index='genome_id', columns='ko_id', values='present', fill_value=0)
soil_gdf = soil_genome_meta.set_index('genome_id').join(ko_wide_soil, how='left').fillna(0).reset_index()

soil_genus_cts2 = soil_gdf.genus.value_counts()
soil_genera2 = soil_genus_cts2[soil_genus_cts2 >= MIN_GENOMES_PER_GENUS].index
soil_genus_idx = {g: soil_gdf.index[soil_gdf.genus == g].values for g in soil_genera2}

print(f"  Soil usable genera: {len(soil_genera2)}")

soil_raw_results = []
ko_list_soil = sorted(variable_soil.index)
for i, ko_id in enumerate(ko_list_soil):
    if (i + 1) % 500 == 0:
        print(f"    KO {i+1}/{len(ko_list_soil)}...", flush=True)
    if ko_id not in soil_gdf.columns:
        continue
    ko_vals = soil_gdf[ko_id].values
    for metal in METALS:
        met_vals = soil_gdf[metal].values
        # Fast inline meta
        effects = []
        for genus, idx in soil_genus_idx.items():
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
        soil_raw_results.append({
            'ko_id': ko_id, 'metal': metal.replace('PF1_', ''),
            'is_metal_gene': ko_id in set(TARGET_KOS.keys()),
            'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects)
        })

soil_scan = pd.DataFrame(soil_raw_results)
if len(soil_scan) > 0:
    _, q_vals, _, _ = multipletests(soil_scan.meta_p.values, method='fdr_bh')
    soil_scan['q'] = q_vals
    n_sig_soil = (soil_scan.q < 0.05).sum()
    n_tested_soil = len(soil_scan)
    print(f"\n  Soil-only raw: {n_sig_soil}/{n_tested_soil} pairs significant (FDR<0.05)")
    print(f"  All-biome raw: {n_sig_all}/{len(raw_scan)} pairs significant (FDR<0.05)")
    print(f"  Ratio: {n_sig_soil/max(n_tested_soil,1):.1%} (soil) vs "
          f"{n_sig_all/max(len(raw_scan),1):.1%} (all)")

    # Per-metal soil comparison
    print(f"\n  Per-metal comparison (soil vs all):")
    for ms in ['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb']:
        sub_all = raw_scan[raw_scan.metal == ms]
        sub_soil = soil_scan[soil_scan.metal == ms]
        n_all = (sub_all.raw_q < 0.05).sum() if 'raw_q' in sub_all.columns else 0
        n_soil = (sub_soil.q < 0.05).sum() if len(sub_soil) > 0 else 0
        print(f"    {ms}: all={n_all}/{len(sub_all)} ({n_all/max(len(sub_all),1):.1%}), "
              f"soil={n_soil}/{len(sub_soil)} ({n_soil/max(len(sub_soil),1):.1%})")

    soil_scan.to_csv(CME / 'genomewide_soil_raw_scan.csv', index=False)


# ── Save summary ──────────────────────────────────────────────────────
print(f"\n{'='*100}", flush=True)
print("FINAL SUMMARY", flush=True)
print(f"{'='*100}\n", flush=True)

print("Covariate ablation summary (62 target pairs):")
print(f"{'Model':40s} {'Survive FDR<0.05':>15s} {'Mean attenuation':>16s}")
print('-' * 75)
for name, info in ablation_results.items():
    print(f"  {name:40s} {info['n_survive']:>15d} {info['mean_atten']:>+15.0%}")

print(f"\nSoil-only analysis:")
for name, info in soil_results.items():
    print(f"  {name:40s} {info['n_survive']:>15d} {info['mean_atten']:>+15.0%}")

print("\nDONE.")

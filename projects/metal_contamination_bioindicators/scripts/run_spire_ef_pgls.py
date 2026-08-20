"""
SPIRE × USGS PGLS with full controls.

Direct per-MAG lat/lon → USGS soil geochemistry spatial join (25km).
Tests all USGS elements with sufficient per-genus coverage.
Controls:
  1. Levins' B (coreness/ubiquity proxy from CME)
  2. Mean lat/lon (geography)
  3. SoilGrids pH, SOC, clay (already in SPIRE feature matrix)
Runs base (genome_mb only) and full model.
"""
import os, sys
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.neighbors import BallTree
from statsmodels.stats.multitest import multipletests

ROOT  = Path('/home/hmacgregor/BERIL-research-observatory')
DATA  = ROOT / 'projects/metal_contamination_bioindicators/data'
FIGS  = ROOT / 'projects/metal_contamination_bioindicators/figures'
TREE  = ROOT / 'projects/comprehensive_metal_ecology/data/gtdb_bac_genus_pruned.tree'
CME_DATA = ROOT / 'projects/comprehensive_metal_ecology/data'
MEP_DATA = ROOT / 'projects/metagenomic_environment_prediction/data'
BERDL = Path.home() / 'data/envdbs'

sys.path.insert(0, str(ROOT / 'tools'))
from figure_style import apply_style, save, PALETTE, FIGW, ROW_H
apply_style()

sys.path.insert(0, str(ROOT / 'projects/comprehensive_metal_ecology/scripts'))
from pgls_utils import run_pgls

MIN_MAGS    = 5    # min MAGs per genus with USGS match to compute mean log-ppm
RADIUS_KM   = 25.0
MIN_GENERA  = 15   # min genera per element to run PGLS
# SPIRE uses gridded lat/lon (165 unique cells for ~10K MAGs) → max 76 unique
# USGS sites. MIN_SITES must be << 76 to keep any elements.
MIN_SITES   = 10   # min unique USGS sites with data for an element

# ── 1. Load SPIRE feature matrix — USA bacteria ───────────────────────────────
print('Loading SPIRE feature matrix …')
spire = pd.read_parquet(MEP_DATA / 'mag_feature_matrix.parquet')
usa = spire[
    spire['latitude'].between(24.0, 50.0) &
    spire['longitude'].between(-125.0, -65.0) &
    (spire['domain'] == 'Bacteria') &
    (spire['completeness'] >= 50.0) &
    (spire['contamination'] <= 10.0)
].copy()
usa['genus_lower'] = usa['genus'].str.lower().str.strip()
print(f'  USA bacteria MAGs: {len(usa):,}  ({usa["genus_lower"].nunique():,} genera)')

# ── 2. Spatial join: SPIRE → nearest USGS soil site ≤25km ────────────────────
# usgs_geochem.parquet: lab_id, group_id, lat/lon, primary_class
# usgs_geochem_joined.parquet: group_id, species, qualified_value  (the measurements)
print('Loading USGS soil sites …')
sites = pd.read_parquet(BERDL / 'usgs_geochem.parquet',
                        columns=['group_id', 'latitude', 'longitude', 'primary_class'])
soil = sites[sites['primary_class'] == 'soil'].dropna(
    subset=['latitude', 'longitude']).copy()
print(f'  USGS soil sites: {len(soil):,}')

soil_rad = np.radians(soil[['latitude', 'longitude']].values)
tree = BallTree(soil_rad, metric='haversine')

mag_rad = np.radians(usa[['latitude', 'longitude']].values)
dist_rad, idx = tree.query(mag_rad, k=1)
dist_km = dist_rad[:, 0] * 6371.0

usa['usgs_dist_km']  = dist_km
usa['usgs_group_id'] = soil['group_id'].iloc[idx[:, 0]].values
matched = usa[usa['usgs_dist_km'] <= RADIUS_KM].copy()
print(f'  MAGs with USGS ≤{RADIUS_KM:.0f}km: {len(matched):,} / {len(usa):,} '
      f'({100*len(matched)/len(usa):.1f}%)')
print(f'  Genera with ≥1 USGS match: {matched["genus_lower"].nunique():,}')

# ── 3. Load all chemical species for matched sites ────────────────────────────
# Measurements are in usgs_geochem_joined.parquet keyed by group_id
print('Loading usgs_geochem_joined for matched group_ids …')
matched_gids = set(matched['usgs_group_id'])
chem = pd.read_parquet(BERDL / 'usgs_geochem_joined.parquet',
                       columns=['group_id', 'species', 'qualified_value'])
chem = chem[
    chem['group_id'].isin(matched_gids) &
    chem['qualified_value'].notna() &
    chem['qualified_value'].gt(0)
].copy()
print(f'  Measurement rows for matched sites: {len(chem):,}')

# Determine which species have enough unique-site coverage
species_coverage = chem.groupby('species')['group_id'].nunique()
keep_species = sorted(species_coverage[species_coverage >= MIN_SITES].index)
print(f'  Species with ≥{MIN_SITES} covered sites: {len(keep_species)}')
print(f'  Examples: {keep_species[:15]}')

chem = chem[chem['species'].isin(keep_species)].copy()
chem_agg = (chem.groupby(['group_id', 'species'])['qualified_value']
            .median().reset_index())
chem_wide = (chem_agg.pivot(index='group_id', columns='species',
                             values='qualified_value')
             .reset_index())
chem_wide.columns.name = None
print(f'  USGS sites × species table: {chem_wide.shape}')

# ── 4. Merge metal ppm → MAGs ─────────────────────────────────────────────────
matched = matched.merge(chem_wide, left_on='usgs_group_id',
                        right_on='group_id', how='left')
print(f'  Merged MAG table: {matched.shape}')

# Log-transform all chemical species columns
for sp in keep_species:
    if sp in matched.columns:
        matched[f'logppm_{sp}'] = np.log1p(matched[sp].clip(lower=0))

# ── 5. Per-genus aggregation ──────────────────────────────────────────────────
print('\nAggregating per genus …')
logppm_cols = [f'logppm_{sp}' for sp in keep_species if f'logppm_{sp}' in matched.columns]

genus_rows = []
for genus, grp in matched.groupby('genus_lower'):
    row = {
        'genus_lower': genus,
        'n_mags_total': len(grp),
        'ko_per_mb_cofactor':   grp['ko_per_mb_cofactor'].mean(),
        'ko_per_mb_resistance': grp['ko_per_mb_resistance'].mean(),
        'mean_genome_mb': (grp['genome_size_bp'] / 1e6).mean(),
        'mean_lat':   grp['latitude'].mean(),
        'mean_lon':   grp['longitude'].mean(),
        'mean_sg_pH':  grp['ph_h2o'].mean(),
        'mean_sg_SOC': grp['organic_carbon_density'].mean(),
        'mean_sg_clay':grp['clay_content'].mean(),
    }
    for lc in logppm_cols:
        vals = grp[lc].dropna()
        row[lc] = vals.mean() if len(vals) >= MIN_MAGS else np.nan
    genus_rows.append(row)

genus_table = pd.DataFrame(genus_rows)
print(f'Genus table: {genus_table.shape}')

# Report coverage per element
coverage_ok = {}
for sp in keep_species:
    lc = f'logppm_{sp}'
    if lc in genus_table.columns:
        n = genus_table[lc].notna().sum()
        coverage_ok[sp] = n
        if n >= MIN_GENERA:
            print(f'  {sp:5s}: {n} genera')

elements_to_test = [sp for sp in keep_species
                    if coverage_ok.get(sp, 0) >= MIN_GENERA]
print(f'\nElements with ≥{MIN_GENERA} genera: {len(elements_to_test)}')

# ── 6. Merge Levins' B and z-score ───────────────────────────────────────────
cme_input = pd.read_csv(CME_DATA / '01_pgls_input_bacteria.csv',
    usecols=['genus_lower', 'mean_levins_B_std'])
genus_table = genus_table.merge(cme_input, on='genus_lower', how='left')
print(f'Genera with Levins B: {genus_table["mean_levins_B_std"].notna().sum()}')

for col in ['ko_per_mb_cofactor', 'ko_per_mb_resistance', 'mean_genome_mb',
            'mean_levins_B_std', 'mean_lat', 'mean_lon',
            'mean_sg_pH', 'mean_sg_SOC', 'mean_sg_clay']:
    μ, σ = genus_table[col].mean(), genus_table[col].std()
    genus_table[f'{col}_z'] = (genus_table[col] - μ) / σ if σ > 0 else 0.0

genus_table.to_csv(DATA / 'spire_ef_pgls_input.csv', index=False)
print('Saved: spire_ef_pgls_input.csv')

# ── 7. PGLS ───────────────────────────────────────────────────────────────────
tree_path = str(TREE.resolve())

BASE_COVS = ['mean_genome_mb_z']
FULL_COVS = ['mean_genome_mb_z', 'mean_levins_B_std_z',
             'mean_lat_z', 'mean_lon_z',
             'mean_sg_pH_z', 'mean_sg_SOC_z', 'mean_sg_clay_z']

results_rows = []
for element in elements_to_test:
    resp_col = f'logppm_{element}'
    all_cols  = (['genus_lower', resp_col,
                  'ko_per_mb_cofactor_z', 'ko_per_mb_resistance_z'] + FULL_COVS)
    df_sub = genus_table[all_cols].dropna().copy()
    print(f'\n{element}: n_genera={len(df_sub)}')
    if len(df_sub) < MIN_GENERA:
        print('  Skipping')
        continue

    for model_name, extra_covs in [('base', BASE_COVS), ('full', FULL_COVS)]:
        for tier, pred in [('Cofactor', 'ko_per_mb_cofactor_z'),
                            ('Resistance', 'ko_per_mb_resistance_z')]:
            try:
                res = run_pgls(df_sub, tree_path,
                               response=resp_col,
                               predictors=[pred] + extra_covs,
                               taxon_col='genus_lower')
                beta = res['betas'][pred]
                se   = res['SEs'][pred]
                pval = res['p_values'][pred]
                lam  = res.get('lambda_est', float('nan'))
                print(f'  {model_name:4s} {tier:10s}: β={beta:+.4f} p={pval:.3g} λ={lam:.3f}')
                results_rows.append(dict(element=element, tier=tier,
                                         model=model_name, beta=beta, se=se,
                                         p_value=pval, lambda_est=lam,
                                         n_genera=res['n']))
            except Exception as e:
                print(f'  {model_name:4s} {tier:10s}: FAILED — {e}')
                results_rows.append(dict(element=element, tier=tier,
                                         model=model_name,
                                         beta=np.nan, se=np.nan,
                                         p_value=np.nan, lambda_est=np.nan,
                                         n_genera=np.nan))

results_df = pd.DataFrame(results_rows)

if len(results_df) == 0 or 'model' not in results_df.columns:
    print('No PGLS results produced — check data pipeline above.')
    sys.exit(0)

# FDR correction within each (model × tier) block
for model_name in ['base', 'full']:
    for tier in ['Cofactor', 'Resistance']:
        mask = (results_df['model'] == model_name) & (results_df['tier'] == tier)
        pv   = results_df.loc[mask, 'p_value'].values
        valid = ~np.isnan(pv)
        fdr   = np.full(len(pv), np.nan)
        if valid.sum() > 1:
            _, fdr[valid], _, _ = multipletests(pv[valid], method='fdr_bh')
        results_df.loc[mask, 'fdr_q'] = fdr

results_df.to_csv(DATA / 'spire_ef_pgls_results.csv', index=False)
print('\n' + '='*65)
print('SPIRE PGLS — full model summary')
print('='*65)
full = results_df[results_df['model'] == 'full'].sort_values('p_value')
print(full.to_string(index=False, float_format='{:.4f}'.format))

# ── 8. Forest plot (full model, elements sorted by cofactor β) ────────────────
full_cof = results_df[(results_df['model']=='full') &
                       (results_df['tier']=='Cofactor')].dropna(subset=['beta'])
el_order = full_cof.sort_values('beta')['element'].tolist()
n_el = len(el_order)

if n_el > 0:
    fig, axs = plt.subplots(1, 2,
                             figsize=(FIGW['2col'], max(ROW_H, 0.30 * n_el + 0.8)),
                             sharey=True, gridspec_kw={'wspace': 0.05})

    for ax, tier in zip(axs, ['Cofactor', 'Resistance']):
        sub = results_df[(results_df['model']=='full') &
                         (results_df['tier']==tier)].set_index('element')
        col = PALETTE[0] if tier == 'Cofactor' else PALETTE[1]

        for yi, el in enumerate(el_order):
            if el not in sub.index or np.isnan(sub.loc[el, 'beta']):
                continue
            b   = sub.loc[el, 'beta']
            ci  = 1.96 * sub.loc[el, 'se']
            pv  = sub.loc[el, 'p_value']
            qv  = sub.loc[el, 'fdr_q']
            n   = int(sub.loc[el, 'n_genera'])
            sig = '†' if pv < 0.05 else ''
            fdr_sig = '*' if (not np.isnan(qv) and qv < 0.2) else ''
            ax.errorbar(b, yi, xerr=ci, fmt='o', color=col,
                        capsize=3, capthick=1.2, lw=1.5, ms=5)
            ax.text(b + ci + 0.005, yi,
                    f'{sig}{fdr_sig} p={pv:.2g} n={n}',
                    va='center', fontsize=6)

        ax.axvline(0, color='gray', lw=0.8, ls='--')
        ax.set_yticks(range(n_el))
        ax.set_yticklabels(el_order, fontsize=8)
        ax.set_xlabel('PGLS β (full model)', fontsize=9)
        ax.set_title(f'{tier} KO density\n(SPIRE MAGs, n≥{MIN_GENERA} genera)', fontsize=9)

    fig.suptitle('SPIRE MAGs × USGS: KO density → element log-ppm\n'
                 '(full controls: genome, Levins B, lat/lon, soil chemistry)',
                 y=1.02, fontsize=10, fontweight='bold')
    save(fig, FIGS / 'fig_spire_ef_pgls_forest')
    print('Saved: fig_spire_ef_pgls_forest.pdf')

print('\nDone.')

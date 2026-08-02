"""
Generate individual dataset-overview panels (A–F) for Supplementary Figure S1.
Each panel saved as a separate PDF in figures/.

Panel A: Dataset counts (EMP shown as subset of MicrobeAtlas) + biome breakdown
Panel B: World map — LatitudeParsed/LongitudeParsed filter 'Unknown' before float coercion
Panel C: MGnify environmental MAGs biome breakdown + KBase MAG quality distributions
Panel D: Genera per phylum in main PGLS dataset with dataset membership
Panel E: Soil pH + ERA5 temp (genus_lat_env_covariates) + NGSA metals + ENIGMA
Panel F: KO density by phylum + Levins B_std rug
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
FIGS = ROOT / 'figures'
PNG  = FIGS / 'png'
PNG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 9,
    'axes.titlesize': 10,
    'axes.titleweight': 'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

DATASET_COLORS = {
    'MicrobeAtlas 16S':  '#2C7BB6',
    'KBase pangenome':   '#1A9641',
    'MGnify MAGs':       '#D7191C',
    'EMP 16S':           '#F46D43',
    'NGSA soils':        '#b2182b',   # dark crimson — Australian red earth
    'ENIGMA ORFRC':      '#7F5A2A',
    'GeoROC bedrock':    '#4DAC26',
    'CSU PF1':           '#2166ac',   # steel blue — global coverage
}

BIOME_COLORS = {
    'aquatic':       '#2a78d6',   # reference slot 1, blue
    'soil':          '#eb6834',   # reference slot 8, orange
    'plant':         '#1baf7a',   # reference slot 2, aqua
    'forest':        '#008300',   # reference slot 4, green
    'agricultural':  '#eda100',   # reference slot 3, yellow
    'field':         '#4a3aa7',   # reference slot 5, indigo/violet
    'farm':          '#e87ba4',   # reference slot 7, magenta
    'other':         '#cccccc',   # intentional recessive neutral (non-categorical)
}

SMALL_BIOMES = {'desert', 'paddy', 'peatland', 'leaf', 'shrub', 'flower', 'mangrove'}

def clean_axes(*axes_list):
    for ax in axes_list:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

def save(fig, stem):
    fig.savefig(FIGS / f'{stem}.pdf', bbox_inches='tight')
    fig.savefig(PNG / f'{stem}.png', bbox_inches='tight', dpi=200)
    plt.close(fig)
    print(f'  Saved {stem}')


# ═══════════════════════════════════════════════════════════════════════════
# PANEL A  –  dataset counts (EMP as MicrobeAtlas subset) + biome breakdown
# ═══════════════════════════════════════════════════════════════════════════
print('Panel A …')

sample_env = pd.read_csv(DATA / 'sample_latlon_env.csv',
                         usecols=['sample_id', 'Env_Level_1'])
biome_counts = sample_env['Env_Level_1'].value_counts()
other_sum   = biome_counts[biome_counts.index.isin(SMALL_BIOMES)].sum()
biome_plot  = biome_counts[~biome_counts.index.isin(SMALL_BIOMES)].copy()
biome_plot['other'] = biome_plot.get('other', 0) + other_sum
biome_plot  = biome_plot.sort_values(ascending=True)

# EMP is a subset of MicrobeAtlas — do not list separately.
# Sorted ascending by value so barh places largest at top (y = max index).
dataset_info = [
    ('ENIGMA ORFRC',                                109, 'MAGs',    DATASET_COLORS['ENIGMA ORFRC']),
    ('NGSA soils',                                1_315, 'Samples', DATASET_COLORS['NGSA soils']),
    ('KBase pangenome',                           1_574, 'Genera',  DATASET_COLORS['KBase pangenome']),
    ('CSU PF1',                                  10_040, 'Genera',  DATASET_COLORS['CSU PF1']),
    ('GeoROC bedrock',                           26_000, 'Sites',   DATASET_COLORS['GeoROC bedrock']),
    ('MGnify MAGs\n(30,497 env. used)',          260_652, 'Genomes', DATASET_COLORS['MGnify MAGs']),
    ('MicrobeAtlas 16S\n(incl. EMP subset)',     462_716, 'Samples', DATASET_COLORS['MicrobeAtlas 16S']),
]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5),
                          gridspec_kw={'width_ratios': [1.3, 1]})

ax = axes[0]
names  = [d[0] for d in dataset_info]
vals   = [d[1] for d in dataset_info]
labels = [d[2] for d in dataset_info]
colors = [d[3] for d in dataset_info]
y_pos  = list(range(len(names)))

bars = ax.barh(y_pos, vals, color=colors, height=0.6)
ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=8.5)
ax.set_xscale('log')
ax.set_xlabel('Count (log scale)')

for bar, v, lbl, name in zip(bars, vals, labels, names):
    x = bar.get_width() * 1.04
    suffix = '~' if name.startswith('GeoROC') else ''
    ax.text(x, bar.get_y() + bar.get_height() / 2,
            f'{suffix}{v:,} {lbl}', va='center', fontsize=7.5)
# Annotation: EMP is a subset of MicrobeAtlas (MicrobeAtlas is now at y=6, top)
ax.annotate('539 EMP-linked genera\nused for niche PGLS',
            xy=(539, 6), xytext=(600, 4.5),
            fontsize=7, color='#555555',
            arrowprops=dict(arrowstyle='->', color='#888888', lw=0.8))

ax2 = axes[1]
biomes = biome_plot.index.tolist()
cnts   = biome_plot.values
bcols  = [BIOME_COLORS.get(b, '#AAAAAA') for b in biomes]
ax2.barh(biomes, cnts, color=bcols, height=0.6)
ax2.set_xlabel('Sample count')
for b, v in zip(biomes, cnts):
    ax2.text(v * 1.01, biomes.index(b), f'{v / 1000:.0f}k', va='center', fontsize=7.5)

clean_axes(*axes)
fig.tight_layout()
save(fig, 'figS1_panelA_overview')


# ═══════════════════════════════════════════════════════════════════════════
# PANEL B  –  world map: KDE density blobs per biome + sample scatter on top
# ═══════════════════════════════════════════════════════════════════════════
print('Panel B …')

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from scipy.ndimage import gaussian_filter, zoom as ndizoom
    import matplotlib.colors as mcolors

    # --- Load and clean coordinates -------------------------------------------
    ma_latlon = pd.read_csv(DATA / 'sample_latlon_env.csv',
                            usecols=['sample_id', 'LatitudeParsed',
                                     'LongitudeParsed', 'Env_Level_1'],
                            dtype={'LatitudeParsed': str, 'LongitudeParsed': str})
    ma_latlon = ma_latlon[
        (ma_latlon['LatitudeParsed'] != 'Unknown') &
        (ma_latlon['LongitudeParsed'] != 'Unknown')
    ].copy()
    ma_latlon['lat'] = pd.to_numeric(ma_latlon['LatitudeParsed'], errors='coerce')
    ma_latlon['lon'] = pd.to_numeric(ma_latlon['LongitudeParsed'], errors='coerce')
    ma_latlon = ma_latlon.dropna(subset=['lat', 'lon'])
    ma_latlon = ma_latlon[ma_latlon['lat'].abs() <= 90]
    ma_latlon = ma_latlon[ma_latlon['lon'].abs() <= 180]
    n_valid = len(ma_latlon)
    n_total = len(sample_env)
    print(f'  MicrobeAtlas lat/lon valid: {n_valid:,} / {n_total:,}')

    # --- Density blobs: 1° histogram + Gaussian smooth per dataset -----------
    NLON, NLAT = 360, 180
    lon_bins = np.linspace(-180, 180, NLON + 1)
    lat_bins = np.linspace(-90,  90,  NLAT + 1)
    SIGMA = 7  # degrees of smoothing

    geo = ccrs.PlateCarree()
    proj = ccrs.Robinson()
    fig, ax = plt.subplots(1, 1, figsize=(11, 5.5),
                            subplot_kw={'projection': proj})

    ax.set_global()
    ax.add_feature(cfeature.LAND,      facecolor='#F5F3EE', edgecolor='none', zorder=0)
    ax.add_feature(cfeature.OCEAN,     facecolor='#E8F4F8', edgecolor='none', zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.4, edgecolor='#999999', zorder=5)
    # No graticule lines — coastlines provide sufficient geographic reference,
    # and semi-transparent overlays bleed through any gridlines underneath.

    def _kde(lons, lats, sigma=SIGMA, thresh_pct=20, norm_pct=98):
        """Return a normalised (0–1) KDE grid for the given coordinates."""
        H, _, _ = np.histogram2d(lons, lats, bins=[lon_bins, lat_bins])
        H_sm = gaussian_filter(H.T.astype(float), sigma=sigma)
        nz = H_sm[H_sm > 0]
        if len(nz) == 0:
            return np.zeros((NLAT, NLON), dtype=np.float32)
        thresh = np.percentile(nz, thresh_pct)
        norm_max = np.percentile(nz, norm_pct)
        return np.where(H_sm > thresh, np.clip(H_sm / norm_max, 0, 1), 0.0).astype(np.float32)

    def _render(ax, H_norm, hex_color, alpha_max, zorder=1):
        """Render a pre-computed normalised grid as a smooth blob."""
        r, g, bv = mcolors.to_rgb(hex_color)
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'blob', [(r, g, bv, 0.0), (r, g, bv, alpha_max)])
        H_up = ndizoom(H_norm, 4, order=1)
        lon_f = np.linspace(-180, 180, H_up.shape[1] + 1)
        lat_f = np.linspace( -90,  90, H_up.shape[0] + 1)
        ax.pcolormesh(lon_f, lat_f, H_up, cmap=cmap, vmin=0, vmax=1,
                      transform=geo, zorder=zorder, rasterized=True)

    def _blob(ax, lons, lats, hex_color, alpha_max, sigma=SIGMA,
              thresh_pct=20, norm_pct=98, zorder=2):
        H_norm = _kde(lons, lats, sigma=sigma, thresh_pct=thresh_pct, norm_pct=norm_pct)
        _render(ax, H_norm, hex_color, alpha_max, zorder=zorder)

    # MicrobeAtlas 16S: individual sample points coloured by biome; SMALL_BIOMES → other
    ma_biome = ma_latlon['Env_Level_1'].apply(
        lambda x: 'other' if x in SMALL_BIOMES else x)
    ma_colors = ma_biome.map(lambda b: BIOME_COLORS.get(b, '#cccccc'))
    ax.scatter(ma_latlon['lon'].values, ma_latlon['lat'].values,
               s=0.6, c=ma_colors.values, alpha=0.12,
               linewidths=0, transform=geo, zorder=4)

    # CSU PF1: MicrobeAtlas samples with PF1 fitness scores (global)
    csu_ids = pd.read_parquet(DATA / 'csu_sample_lookup.parquet',
                               columns=['accession_id'])
    csu_latlon = csu_ids.merge(
        ma_latlon[['sample_id', 'lat', 'lon']],
        left_on='accession_id', right_on='sample_id', how='inner')
    print(f'  CSU samples with valid lat/lon: {len(csu_latlon):,}')
    H_csu = _kde(csu_latlon['lon'].values, csu_latlon['lat'].values, thresh_pct=1)
    _render(ax, H_csu, DATASET_COLORS['CSU PF1'], alpha_max=0.50, zorder=1)

    # NGSA soils: Australian geochemical survey (Australia only)
    ngsa_coords = pd.read_csv(DATA / 'ngsa_geochemistry.csv',
                              usecols=['lat', 'lon']).dropna()
    H_ngsa = _kde(ngsa_coords['lon'].values, ngsa_coords['lat'].values, thresh_pct=10)
    _render(ax, H_ngsa, DATASET_COLORS['NGSA soils'], alpha_max=0.75, zorder=2)

    # Overlap: pixel-wise minimum of both grids → amber blob where both datasets co-occur
    H_ov = np.minimum(H_csu, H_ngsa)
    if H_ov.max() > 0:
        _render(ax, H_ov / H_ov.max(), '#e8a818', alpha_max=0.90, zorder=2.5)

    # Ocean erase: repaint ocean on top of blobs so they are constrained to land
    ax.add_feature(cfeature.OCEAN, facecolor='#E8F4F8', edgecolor='none', zorder=3)

    # ENIGMA ORFRC star
    ax.scatter([-84.34], [35.93], s=100,
               color=DATASET_COLORS['ENIGMA ORFRC'],
               marker='*', linewidths=0.5, edgecolors='white',
               transform=geo, zorder=6)

    # --- Legends --------------------------------------------------------------
    # Biome legend for MicrobeAtlas points (upper-left)
    biome_order = ['aquatic', 'soil', 'plant', 'forest',
                   'agricultural', 'field', 'farm', 'other']
    biome_handles = [
        Line2D([0], [0], marker='o', color='w', markersize=6,
               markerfacecolor=BIOME_COLORS[b], label=b)
        for b in biome_order if b in BIOME_COLORS
    ]
    biome_leg = ax.legend(handles=biome_handles, loc='upper left',
                          framealpha=0.85, fontsize=7, ncol=2,
                          title=f'MicrobeAtlas 16S ({n_valid:,} samples)',
                          title_fontsize=7.5)
    ax.add_artist(biome_leg)

    # Dataset legend (lower-left): blobs + ENIGMA star
    legend_elements = [
        Patch(facecolor=DATASET_COLORS['CSU PF1'],
              label=f'CSU PF1 ({len(csu_latlon):,} georef. samples)', alpha=0.70),
        Patch(facecolor=DATASET_COLORS['NGSA soils'],
              label=f'NGSA soils ({len(ngsa_coords):,} sites, Australia)', alpha=0.85),
        Patch(facecolor='#e8a818',
              label='CSU PF1 × NGSA overlap', alpha=0.90),
        Line2D([0], [0], marker='*', color='w',
               markerfacecolor=DATASET_COLORS['ENIGMA ORFRC'],
               markersize=11, label='ENIGMA ORFRC (Oak Ridge TN)'),
    ]
    ax.legend(handles=legend_elements, loc='lower left',
              framealpha=0.88, fontsize=8, ncol=1,
              title='Overlay datasets', title_fontsize=8.5)


    fig.tight_layout()
    save(fig, 'figS1_panelB_map')

except Exception as e:
    print(f'  Panel B failed: {e}')
    import traceback; traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════
# PANEL C  –  MGnify environmental MAG breakdown + KBase MAG quality
# ═══════════════════════════════════════════════════════════════════════════
print('Panel C …')

traits = pd.read_csv(DATA / 'mgnify_mag_metal_traits.csv',
                     usecols=['genome_id', 'biome_name', 'biome_lineage'])
env_mask    = traits['biome_lineage'].str.contains('Environmental', na=False)
traits_env  = traits[env_mask]
n_total_mg  = len(traits)
n_env_mg    = len(traits_env)

env_biome_vc  = traits_env['biome_name'].value_counts()
all_biome_top = traits['biome_name'].value_counts().head(8)

mag_q = pd.read_csv(DATA / 'genus_mag_quality.csv')

fig, axes = plt.subplots(1, 3, figsize=(14, 5))

# (i) All MAGs biome distribution — show contrast host vs. env
ax = axes[0]
top_names   = all_biome_top.index.tolist()[::-1]
top_vals    = all_biome_top.values[::-1]
host_set    = {'Human Gut', 'Mouse Gut', 'Chicken Gut', 'Pig Gut',
               'Cow Rumen', 'Sheep Rumen', 'Human Skin'}
bar_colors  = ['#CCCCCC' if n in host_set else DATASET_COLORS['MGnify MAGs']
               for n in top_names]
ax.barh(top_names, top_vals, color=bar_colors, height=0.65)
ax.set_xlabel('Number of MAGs')
for i, (n, v) in enumerate(zip(top_names, top_vals)):
    ax.text(v * 1.01, i, f'{v / 1000:.0f}k', va='center', fontsize=7.5)

# (ii) Environmental MAGs only
ax = axes[1]
env_names = env_biome_vc.index.tolist()[::-1]
env_vals  = env_biome_vc.values[::-1]
env_cols  = plt.cm.viridis(np.linspace(0.2, 0.9, len(env_names)))
ax.barh(env_names, env_vals, color=env_cols, height=0.65)
ax.set_xlabel('Number of MAGs')
for i, v in enumerate(env_vals):
    ax.text(v * 1.01, i, f'{v:,}', va='center', fontsize=7.5)

# (iii) KBase MAG completeness & contamination violin
ax = axes[2]
comp = mag_q['mean_completeness'].dropna().values
cont = mag_q['mean_contamination'].dropna().values
vp = ax.violinplot([comp, cont], positions=[1, 2], showmedians=True,
                   showextrema=True)
for body, c in zip(vp['bodies'], [DATASET_COLORS['KBase pangenome'],
                                   DATASET_COLORS['ENIGMA ORFRC']]):
    body.set_facecolor(c)
    body.set_alpha(0.6)
vp['cmedians'].set_color('#333333')
vp['cbars'].set_color('#333333')
vp['cmaxes'].set_color('#333333')
vp['cmins'].set_color('#333333')
ax.set_xticks([1, 2])
ax.set_xticklabels(['Completeness', 'Contamination'], fontsize=9)
ax.set_ylabel('Mean per genus (%)')
ax.text(1, mag_q['mean_completeness'].median(),
        f' {mag_q["mean_completeness"].median():.0f}%', va='center', fontsize=8)
ax.text(2, mag_q['mean_contamination'].median(),
        f' {mag_q["mean_contamination"].median():.1f}%', va='center', fontsize=8)

clean_axes(*axes)
fig.tight_layout()
save(fig, 'figS1_panelC_quality')


# ═══════════════════════════════════════════════════════════════════════════
# PANEL D  –  Genera per phylum + dataset membership
# ═══════════════════════════════════════════════════════════════════════════
print('Panel D …')

pgls_df  = pd.read_csv(DATA / '01_pgls_input_bacteria.csv',
                       usecols=['genus_lower', 'phylum', 'kingdom'])
emp_df   = pd.read_csv(DATA / 'emp_niche_pgls_input.csv',
                       usecols=['genus_lower'])
mgnify_d = pd.read_csv(DATA / 'mgnify_pgls_input.csv',
                       usecols=['genus_lower'])

pgls_df['in_emp']    = pgls_df['genus_lower'].isin(set(emp_df['genus_lower']))
pgls_df['in_mgnify'] = pgls_df['genus_lower'].isin(set(mgnify_d['genus_lower']))

phylum_counts = pgls_df['phylum'].value_counts()
TOP_N = 15
top_phyla = phylum_counts.head(TOP_N).index.tolist()
sub = pgls_df[pgls_df['phylum'].isin(top_phyla)].copy()
phylum_order = phylum_counts.head(TOP_N).index[::-1].tolist()

fig, axes = plt.subplots(1, 2, figsize=(12, 5.5),
                          gridspec_kw={'width_ratios': [1.6, 1]})

ax = axes[0]
for p in phylum_order:
    y   = phylum_order.index(p)
    tot = (sub['phylum'] == p).sum()
    e   = ((sub['phylum'] == p) & sub['in_emp']).sum()
    m   = ((sub['phylum'] == p) & sub['in_mgnify']).sum()
    ax.barh(y, tot, color='#DDDDDD', height=0.65)
    ax.barh(y, e, color=DATASET_COLORS['EMP 16S'], height=0.65, alpha=0.85)
    ax.barh(y, m, left=e, color=DATASET_COLORS['MGnify MAGs'], height=0.65, alpha=0.75)
    ax.text(tot * 1.01, y, str(tot), va='center', fontsize=7.5)

ax.set_yticks(range(len(phylum_order)))
ax.set_yticklabels([p.replace('_', ' ') for p in phylum_order], fontsize=8.5)
ax.set_xlabel('Number of genera')
legend_patches = [
    Patch(color='#DDDDDD', label='KBase only'),
    Patch(color=DATASET_COLORS['EMP 16S'], alpha=0.85, label='+ EMP 16S niche'),
    Patch(color=DATASET_COLORS['MGnify MAGs'], alpha=0.75, label='+ MGnify PGLS'),
]
ax.legend(handles=legend_patches, fontsize=8)

ax2 = axes[1]
sets = {
    'KBase only':             ((~pgls_df['in_emp']) & (~pgls_df['in_mgnify'])).sum(),
    'KBase + EMP':            (pgls_df['in_emp']    & ~pgls_df['in_mgnify']).sum(),
    'KBase + MGnify':         (~pgls_df['in_emp']   &  pgls_df['in_mgnify']).sum(),
    'All three\ndatasets':    (pgls_df['in_emp']    &  pgls_df['in_mgnify']).sum(),
}
set_colors = ['#CCCCCC', DATASET_COLORS['EMP 16S'],
              DATASET_COLORS['MGnify MAGs'], '#555555']
ax2.bar(range(4), list(sets.values()), color=set_colors, width=0.6)
ax2.set_xticks(range(4))
ax2.set_xticklabels(list(sets.keys()), fontsize=8)
ax2.set_ylabel('Number of genera')
for i, v in enumerate(sets.values()):
    ax2.text(i, v + 3, str(v), ha='center', fontsize=8)

clean_axes(*axes)
fig.tight_layout()
save(fig, 'figS1_panelD_taxonomy')


# ═══════════════════════════════════════════════════════════════════════════
# PANEL E  –  Environmental variable distributions
# ═══════════════════════════════════════════════════════════════════════════
print('Panel E …')

ngsa = pd.read_csv(DATA / 'ngsa_geochemistry.csv')
enigma_wg = pd.read_csv(DATA / 'enigma_frc_well_geochemistry.csv')
# genus_lat_env_covariates carries median_soil_ph (SoilGrids, stored as pH×10)
# and ERA5 temperature
env_cov = pd.read_csv(DATA / 'genus_lat_env_covariates.csv',
                      usecols=['median_soil_ph', 'median_era5_temp_C'])
ph_vals   = env_cov['median_soil_ph'].dropna() / 10.0
temp_vals = env_cov['median_era5_temp_C'].dropna()

ngsa_metals = [c for c in ['Cu_ppm', 'Zn_ppm', 'Ni_ppm', 'Pb_ppm', 'As_ppm', 'Co_ppm']
               if c in ngsa.columns]

fig, axes = plt.subplots(2, 4, figsize=(14, 7))
axes = axes.flatten()

# (0) Soil pH (genus-level medians, all MicrobeAtlas genera)
ax = axes[0]
ax.hist(ph_vals, bins=30, color='#9B59B6', edgecolor='white', linewidth=0.3)
ax.axvline(ph_vals.median(), color='#D7191C', lw=1.5, linestyle='--',
           label=f'Median {ph_vals.median():.1f}')
ax.set_xlabel('Soil pH')
ax.set_ylabel('Genera')
ax.legend(fontsize=8)

# (1) ERA5 temperature
ax = axes[1]
ax.hist(temp_vals, bins=30, color='#E74C3C', edgecolor='white', linewidth=0.3)
ax.axvline(temp_vals.median(), color='#333333', lw=1.5, linestyle='--',
           label=f'Median {temp_vals.median():.1f} °C')
ax.set_xlabel('Mean air temperature (°C)')
ax.set_ylabel('Genera')
ax.legend(fontsize=8)

# (2–7) NGSA metal log-distributions
ngsa_palette = plt.cm.tab10(np.linspace(0, 0.8, len(ngsa_metals)))
for i, col in enumerate(ngsa_metals[:6]):
    ax = axes[i + 2]
    vals = ngsa[col].dropna()
    vals = vals[vals > 0]
    ax.hist(np.log10(vals), bins=30, color=ngsa_palette[i],
            edgecolor='white', linewidth=0.3)
    ax.axvline(np.log10(vals.median()), color='#333333', lw=1.4, linestyle='--',
               label=f'Median {vals.median():.1f} ppm')
    short = col.replace('_ppm', '')
    ax.set_xlabel(f'log₁₀({short}, ppm)')
    ax.set_ylabel('Sites')
    ax.legend(fontsize=8)

clean_axes(*axes)
fig.tight_layout()
save(fig, 'figS1_panelE_environment')


# ═══════════════════════════════════════════════════════════════════════════
# PANEL F  –  KO density by phylum + Levins B_std rug
# ═══════════════════════════════════════════════════════════════════════════
print('Panel F …')

pgls = pd.read_csv(DATA / '01_pgls_input_bacteria.csv',
                   usecols=['genus_lower', 'ko_per_mb_primary',
                             'mean_levins_B_std', 'phylum'])
pgls = pgls.dropna(subset=['ko_per_mb_primary', 'phylum'])

phylum_order_F = (pgls.groupby('phylum')['ko_per_mb_primary']
                  .median().sort_values(ascending=False)
                  .index[:12].tolist())

fig, axes = plt.subplots(3, 4, figsize=(14, 9))
axes = axes.flatten()

phylum_palette = plt.cm.tab20(np.linspace(0, 1, len(phylum_order_F)))

for i, phylum in enumerate(phylum_order_F):
    ax = axes[i]
    sub2  = pgls[pgls['phylum'] == phylum]['ko_per_mb_primary'].dropna()
    b_sub = pgls[(pgls['phylum'] == phylum) &
                 pgls['mean_levins_B_std'].notna()]['mean_levins_B_std']

    ax.hist(sub2, bins=25, color=phylum_palette[i],
            edgecolor='white', linewidth=0.3, density=True, alpha=0.85)
    ax.axvline(sub2.median(), color='#333333', lw=1.2, linestyle='--')

    # Rug: Levins B_std scaled to x-axis range of KO density
    if len(b_sub) > 0:
        xmin, xmax = sub2.min(), sub2.max()
        b_x = xmin + b_sub.values * (xmax - xmin)
        ax.plot(b_x, np.zeros(len(b_x)) - 0.001,
                '|', color='#D7191C', alpha=0.55, ms=5, mew=0.8)

    n = len(sub2)
    ax.set_title(f'{phylum.replace("_", " ")}\n(n={n})', fontsize=8.5,
                 fontweight='bold')
    ax.set_xlabel('Metal-gene KO density (per Mb)', fontsize=7.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if i % 4 == 0:
        ax.set_ylabel('Density', fontsize=7.5)

for j in range(len(phylum_order_F), len(axes)):
    axes[j].set_visible(False)

legend_elements = [
    Patch(color='#999999', alpha=0.85, label='KO density distribution'),
    Line2D([0], [0], color='#333333', lw=1.2, linestyle='--', label='Median'),
    Line2D([0], [0], marker='|', color='#D7191C', lw=0, ms=6, mew=0.8,
           label='Levins B_std (scaled to x range)'),
]
fig.legend(handles=legend_elements, loc='lower right',
           bbox_to_anchor=(0.98, 0.02), fontsize=8.5, framealpha=0.9)
fig.tight_layout()
save(fig, 'figS1_panelF_density')

# ═══════════════════════════════════════════════════════════════════════════
# PANEL G  –  t-SNE coloured by biome
# ═══════════════════════════════════════════════════════════════════════════
print('Panel G …')

tsne = pd.read_csv(DATA / 'tsne_embedding.csv')

fig, ax = plt.subplots(1, 1, figsize=(7, 6))

for biome, grp in tsne.groupby('biome'):
    c = BIOME_COLORS.get(biome, '#AAAAAA')
    ax.scatter(grp['tsne_x'], grp['tsne_y'],
               s=3, color=c, alpha=0.55, linewidths=0,
               label=biome.capitalize(), rasterized=True)

ax.set_xlabel('t-SNE dimension 1')
ax.set_ylabel('t-SNE dimension 2')
ax.set_xticks([])
ax.set_yticks([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

handles = [Patch(facecolor=BIOME_COLORS.get(b, '#AAAAAA'), label=b.capitalize())
           for b in sorted(tsne['biome'].unique())]
ax.legend(handles=handles, loc='upper right', fontsize=9,
          framealpha=0.85, markerscale=2, title='Biome', title_fontsize=9)

fig.tight_layout()
save(fig, 'figS1_panelG_tsne')

print('\nAll panels done.')

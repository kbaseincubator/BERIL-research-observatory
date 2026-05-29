"""NB02: 5° grid hotspot identification, biome prevalence, and ENA gap quantification."""
import os
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests

PROJ = Path(__file__).resolve().parent.parent
# Data lives in the shared exploratory store; override with BERDL_DATA_DIR env var.
_data_dir = Path(os.environ.get('BERDL_DATA_DIR',
                                str(PROJ.parent / 'misc_exploratory/exploratory/data')))

df = pd.read_csv(_data_dir / 'final_mags_geospatial_traits.csv')
# Guard against string-typed numeric columns (pitfalls.md)
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
df = df.dropna(subset=['lat','lon'])
df = df[(df['lat'].between(-90,90)) & (df['lon'].between(-180,180))]
df['lat_bin'] = (df['lat'] // 5) * 5
df['lon_bin'] = (df['lon'] // 5) * 5
global_prev   = (df['n_metal_types'] > 0).mean()
global_resist = int((df['n_metal_types'] > 0).sum())
global_total  = len(df)
print(f"MAGs with coords: {global_total:,}  metal-resistant: {global_resist:,}  global prev: {global_prev:.3f}")

grid = df.groupby(['lat_bin','lon_bin']).agg(
    n_total=('genome_id','count'), n_resist=('n_metal_types', lambda x: (x>0).sum())
).reset_index()
grid = grid[grid['n_total'] >= 5]

ors, ps = [], []
for _, row in grid.iterrows():
    a,b = int(row['n_resist']), int(row['n_total'])-int(row['n_resist'])
    c = max(global_resist - a, 0); d = max(global_total - global_resist - b, 0)
    OR, p = fisher_exact([[a,b],[c,d]])
    ors.append(OR); ps.append(p)
grid['OR'] = ors; grid['p_raw'] = ps
_, grid['q'], _, _ = multipletests(grid['p_raw'].fillna(1), method='fdr_bh')
grid['prevalence'] = grid['n_resist'] / grid['n_total']

hotspots  = grid[(grid['OR']>2)  & (grid['q']<0.05)].sort_values('OR', ascending=False)
coldspots = grid[(grid['OR']<0.5)& (grid['q']<0.05)].sort_values('OR')
print(f"Hotspots (OR>2, q<0.05): {len(hotspots)}  Coldspots: {len(coldspots)}")
print(hotspots[['lat_bin','lon_bin','n_total','prevalence','OR','q']].head(10).to_string(index=False))

def broad_biome(b):
    b = str(b).lower()
    if 'marine' in b: return 'Marine'
    if 'soil' in b or 'terrestrial' in b: return 'Soil'
    if 'freshwater' in b or 'river' in b or 'lake' in b: return 'Freshwater'
    if 'wastewater' in b or 'engineered' in b: return 'Wastewater'
    if 'rhizosphere' in b or 'plant' in b: return 'Rhizosphere'
    return 'Other'
df['broad_biome'] = df['biome_name'].apply(broad_biome)
biome_stats = []
for bm, grp in df.groupby('broad_biome'):
    n_t, n_r = len(grp), (grp['n_metal_types']>0).sum()
    OR, p = fisher_exact([[n_r, n_t-n_r],[global_resist-n_r, global_total-global_resist-(n_t-n_r)]])
    biome_stats.append({'biome':bm,'n':n_t,'prevalence':n_r/n_t,'OR':OR,'p':p})
bdf = pd.DataFrame(biome_stats).sort_values('prevalence', ascending=False)
_, bdf['q'], _, _ = multipletests(bdf['p'], method='fdr_bh')
print("\nBiome-stratified prevalence:")
# Report 'Other' size so it isn't treated as a meaningful ecological stratum
other_row = bdf[bdf['biome']=='Other']
if not other_row.empty:
    print(f"  [Other biome catch-all: n={int(other_row['n'].values[0]):,} — excluded from interpretation]")
print(bdf[['biome','n','prevalence','OR','q']].to_string(index=False))

# Figures
fig, ax = plt.subplots(figsize=(14,7))
# vmax=0.25 rather than 1.0: global prevalence is 2.8%, so 0–100% scale compresses all signal
sc = ax.scatter(grid['lon_bin']+2.5, grid['lat_bin']+2.5, c=grid['prevalence'],
                cmap='RdYlGn_r', s=grid['n_total']/2, alpha=0.7, vmin=0, vmax=0.25)
plt.colorbar(sc, ax=ax, label='Metal resistance prevalence')
ax.set_xlim(-180,180); ax.set_ylim(-90,90)
ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
ax.set_title(f'Metal resistance prevalence by 5° grid (global={global_prev:.3f})')
plt.tight_layout(); plt.savefig(PROJ / 'figures/fig_nb02_global_hotspot_map.png', dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(8,4))
ax.barh(bdf['biome'], bdf['prevalence'], color=['#d62728' if q<0.05 else '#aec7e8' for q in bdf['q']])
ax.axvline(global_prev, color='k', ls='--', lw=1.2, label=f'Global={global_prev:.3f}')
ax.set_xlabel('Metal resistance prevalence'); ax.set_title('Biome-stratified prevalence (red=q<0.05)')
ax.legend(); plt.tight_layout()
plt.savefig(PROJ / 'figures/fig_nb02_biome_prevalence.png', dpi=150); plt.close()
print("Figures saved.")

# ENA coordinate coverage vs MAG grid cells
ena = pd.read_csv(_data_dir / 'ena_sample_coordinates.csv')
ena['lat'] = pd.to_numeric(ena['lat'], errors='coerce')
ena['lon'] = pd.to_numeric(ena['lon'], errors='coerce')
ena = ena.dropna(subset=['lat','lon'])
ena = ena[(ena['lat'].between(-90,90)) & (ena['lon'].between(-180,180))]
ena['lat_bin'] = (ena['lat'] // 5) * 5
ena['lon_bin'] = (ena['lon'] // 5) * 5
ena_cells = set(zip(ena['lat_bin'], ena['lon_bin']))
mag_cells  = set(zip(grid['lat_bin'], grid['lon_bin']))
cells_with_no_ena = mag_cells - ena_cells
print(f"\nENA coordinate gap analysis:")
print(f"  ENA samples with valid coords: {len(ena):,}")
print(f"  MAG grid cells (≥5 MAGs): {len(mag_cells)}")
print(f"  MAG grid cells with no ENA coverage: {len(cells_with_no_ena)}")
if cells_with_no_ena:
    print(f"  Blind cells: {sorted(cells_with_no_ena)[:5]} ...")

# Expedition-level clustering check: are top hotspots driven by single studies?
# Uses sample_accession column if present; first 6 chars give study-level prefix (e.g. ERP001).
print("\nExpedition clustering check (top 5 hotspots):")
if 'sample_accession' in df.columns:
    df['study_prefix'] = df['sample_accession'].str[:6]
    for _, row in hotspots.head(5).iterrows():
        cell = df[(df['lat_bin']==row['lat_bin']) & (df['lon_bin']==row['lon_bin'])]
        n_studies = cell['study_prefix'].nunique()
        flag = " ⚠ single-study" if n_studies == 1 else ""
        print(f"  ({row['lat_bin']:.0f}°,{row['lon_bin']:.0f}°) OR={row['OR']:.1f}: {n_studies} distinct study prefix(es){flag}")
else:
    print("  [skipped — no sample_accession column in source CSV; verify manually]")

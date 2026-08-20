#!/usr/bin/env python3
"""
Query SoilGrids v2.0 REST API for pH at 634 spatially-independent thinned cells.
Then test partial Spearman correlations controlling for pH for 6 target CWM × metal pairs.

Background: 6 FDR-sig CWM × USGS metal pairs in 634 thinned cells are all redox/anaerobic genes.
Test whether soil pH (SoilGrids v2.0 0-5cm) mediates these associations.
Prior attempt limited to n=62-103 (sparse sample-level pH); SoilGrids covers all n=634.

Output:
  - projects/microbeatlas_metal_ecology/data/usa_cwm/soilgrids_ph_thinned_cells.csv
  - projects/microbeatlas_metal_ecology/data/cwm_per_ko_usa_ph_soilgrids.csv
"""

import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
import requests
import time
from scipy import stats
from scipy.stats import rankdata
from pathlib import Path

BASE = Path('/home/hmacgregor/BERIL-research-observatory')

print("=" * 80)
print("STEP 1: Load 634 thinned cell centroids from joined parquet")
print("=" * 80)

joined = pd.read_parquet(
    BASE / 'projects/microbeatlas_metal_ecology/data/usa_cwm/usa_cwm_usgs_joined.parquet'
)
print(f"Loaded joined dataset: {len(joined)} rows")
print(f"Columns: {list(joined.columns)}")

# Determine lat/lon column names
lat_col = 'lat_x' if 'lat_x' in joined.columns else 'lat'
lon_col = 'lon_x' if 'lon_x' in joined.columns else 'lon'
print(f"Using lat/lon columns: {lat_col}, {lon_col}")

# Apply 50 km thinning (DEG=0.45, seed=42)
DEG = 0.45
rng = np.random.default_rng(42)

locs = joined[['sample_id', lat_col, lon_col]].drop_duplicates('sample_id').copy()
locs = locs.rename(columns={lat_col: 'lat', lon_col: 'lon'})
print(f"Unique samples: {len(locs)}")

locs['cell_lat'] = np.floor(locs['lat'] / DEG)
locs['cell_lon'] = np.floor(locs['lon'] / DEG)

kept_ids = set()
for _, grp in locs.groupby(['cell_lat', 'cell_lon']):
    kept_ids.add(rng.choice(grp['sample_id'].values))

thin_locs = locs[locs['sample_id'].isin(kept_ids)].copy()
print(f"Thinned cells (one per 0.45°×0.45° cell): {len(thin_locs)}")

# Get unique cell centroids
cell_centroids = (thin_locs.groupby(['cell_lat', 'cell_lon'])
                           .agg({'lat': 'mean', 'lon': 'mean', 'sample_id': 'first'})
                           .reset_index())
print(f"Cell centroids: {len(cell_centroids)}")

print("\n" + "=" * 80)
print("STEP 2: Query SoilGrids v2.0 REST API for pH at each centroid")
print("=" * 80)

def get_soilgrids_ph(lat, lon, retries=3):
    """Query SoilGrids v2.0 REST API for pH (0-5cm depth, mean)."""
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    for attempt in range(retries):
        try:
            resp = requests.get(
                url,
                params={
                    "lon": round(lon, 4),
                    "lat": round(lat, 4),
                    "property": "phh2o",
                    "depth": "0-5cm",
                    "value": "mean"
                },
                timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                val = data['properties']['layers'][0]['depths'][0]['values']['mean']
                return val / 10 if val is not None else None
            elif resp.status_code == 429:
                # Rate limited; exponential backoff
                wait = 2 ** attempt
                print(f"    Rate limited; waiting {wait}s")
                time.sleep(wait)
        except Exception as e:
            print(f"    Exception on attempt {attempt+1}: {e}")
            time.sleep(1)
    return None

ph_results = []
for i, row in cell_centroids.iterrows():
    ph = get_soilgrids_ph(row['lat'], row['lon'])
    ph_results.append({
        'cell_lat': row['cell_lat'],
        'cell_lon': row['cell_lon'],
        'lat': row['lat'],
        'lon': row['lon'],
        'ph_soilgrids': ph
    })
    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(cell_centroids)} done")
    time.sleep(0.15)  # ~150ms between requests to avoid rate limiting

ph_df = pd.DataFrame(ph_results)
n_ok = ph_df['ph_soilgrids'].notna().sum()
print(f"\nPH retrieved: {n_ok}/{len(ph_df)} cells ({100*n_ok/len(ph_df):.1f}%)")
print(f"pH range: {ph_df['ph_soilgrids'].min():.2f} – {ph_df['ph_soilgrids'].max():.2f}")

# Save pH data
out_ph = BASE / 'projects/microbeatlas_metal_ecology/data/usa_cwm/soilgrids_ph_thinned_cells.csv'
ph_df.to_csv(out_ph, index=False)
print(f"Saved: {out_ph}")

print("\n" + "=" * 80)
print("STEP 3: Join pH to thinned CWM-metal dataset")
print("=" * 80)

# Add cell coords to thin_locs
thin_locs_ph = thin_locs.merge(
    ph_df[['cell_lat', 'cell_lon', 'ph_soilgrids']],
    on=['cell_lat', 'cell_lon'],
    how='left'
)

# Join to full joined parquet for thinned samples
joined_thin = joined[joined['sample_id'].isin(kept_ids)].copy()
print(f"Thinned joined dataset: {len(joined_thin)} rows")

joined_thin_ph = joined_thin.merge(
    thin_locs_ph[['sample_id', 'ph_soilgrids']],
    on='sample_id',
    how='left'
)

pH_coverage = joined_thin_ph['ph_soilgrids'].notna().mean() * 100
print(f"pH coverage in thinned dataset: {pH_coverage:.1f}%")

print("\n" + "=" * 80)
print("STEP 4: Partial Spearman for 6 target CWM × metal pairs")
print("=" * 80)

TARGET_PAIRS = [
    ('K16014', 'Hg'),  # hydrogenase maturation factor, Hg
    ('K04655', 'Hg'),  # hydrogenase maturation factor, Hg
    ('K03605', 'Hg'),  # hydrogenase maturation factor, Hg
    ('K04654', 'Hg'),  # microaerobic transporter, Hg
    ('K04654', 'As'),  # microaerobic transporter, As
    ('K00859', 'Pb'),  # peroxidase/oxidoreductase, Pb
]

def partial_spearman(x, y, z):
    """Spearman correlation of x and y residuals after regressing out z."""
    def resid(a, b):
        slope, intercept, _, _, _ = stats.linregress(b, a)
        return a - (slope * b + intercept)
    return stats.spearmanr(resid(x, z), resid(y, z))

rows = []
for ko_id, metal in TARGET_PAIRS:
    # Get rows with all three variables present
    sub = joined_thin_ph[
        (joined_thin_ph['ko_id'] == ko_id) &
        (joined_thin_ph[metal].notna()) &
        (joined_thin_ph['ph_soilgrids'].notna())
    ][['cwm', metal, 'ph_soilgrids']].dropna()

    n = len(sub)
    if n < 20:
        print(f"  {ko_id} × {metal}: too few pH-complete rows ({n})")
        continue

    # Raw Spearman
    rho_r, p_r = stats.spearmanr(sub[metal], sub['cwm'])

    # Partial Spearman (controlling for pH)
    rho_p, p_p = partial_spearman(sub['cwm'].values, sub[metal].values, sub['ph_soilgrids'].values)

    rows.append({
        'ko_id': ko_id,
        'metal': metal,
        'rho_raw': rho_r,
        'p_raw': p_r,
        'rho_partial': rho_p,
        'p_partial': p_p,
        'n': n
    })
    print(f"  {ko_id} × {metal}: n={n}, rho_raw={rho_r:.3f} (p={p_r:.4f}), "
          f"rho_pH={rho_p:.3f} (p={p_p:.4f})")

res = pd.DataFrame(rows)

# BH-FDR on both raw and partial p-values
if len(res) > 0:
    ranks = rankdata(res['p_partial'])
    res['q_partial'] = np.minimum(res['p_partial'] * len(res) / ranks, 1.0)

    ranks_r = rankdata(res['p_raw'])
    res['q_raw'] = np.minimum(res['p_raw'] * len(res) / ranks_r, 1.0)

    print("\n" + "=" * 80)
    print("=== PARTIAL SPEARMAN (SoilGrids pH control, full n) ===")
    print("=" * 80)

    # Create display table
    display = res[['ko_id', 'metal', 'rho_raw', 'p_raw', 'q_raw', 'rho_partial', 'p_partial', 'q_partial', 'n']].copy()

    # Format for readability
    print("\nRaw (unadjusted) Spearman:")
    print(display[['ko_id', 'metal', 'rho_raw', 'p_raw', 'q_raw', 'n']].to_string(index=False))

    print("\nPartial Spearman (controlling for SoilGrids pH 0-5cm):")
    print(display[['ko_id', 'metal', 'rho_partial', 'p_partial', 'q_partial', 'n']].to_string(index=False))

    print("\nFDR-significant pairs (q < 0.05):")
    sig_raw = display[display['q_raw'] < 0.05]
    sig_partial = display[display['q_partial'] < 0.05]

    if len(sig_raw) > 0:
        print("  Raw:", list(sig_raw['ko_id'] + ' × ' + sig_raw['metal']))
    else:
        print("  Raw: none")

    if len(sig_partial) > 0:
        print("  Partial (pH-adjusted):", list(sig_partial['ko_id'] + ' × ' + sig_partial['metal']))
    else:
        print("  Partial (pH-adjusted): none")

    # Save results
    out_res = BASE / 'projects/microbeatlas_metal_ecology/data/cwm_per_ko_usa_ph_soilgrids.csv'
    res.to_csv(out_res, index=False)
    print(f"\nSaved: {out_res}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("=== SUMMARY ===")
    print("=" * 80)
    print(f"Sample sizes: min={res['n'].min()}, max={res['n'].max()}, mean={res['n'].mean():.0f}")
    print(f"Raw Spearman p-values: min={res['p_raw'].min():.4f}, max={res['p_raw'].max():.4f}")
    print(f"pH-partial p-values: min={res['p_partial'].min():.4f}, max={res['p_partial'].max():.4f}")
    print(f"pH-mediated collapse (K16014×Hg microaerobic): {res[res['ko_id']=='K04654']['p_partial'].values[0] if len(res[res['ko_id']=='K04654']) > 0 else 'N/A'}")

#!/usr/bin/env python3
"""
Sensitivity check NB29: MicrobeAtlas spatial join to NGSA (replacing AusMicrobiome).

Strategy:
  1. Load sample_latlon_env.csv; filter to Australian bounding box.
  2. Haversine nearest-neighbour join to ngsa_geochemistry.csv (≤200 km).
  3. Spark query: join otu_counts_long to Australian sample_ids; extract genus
     from Tax string in otu_metadata.
  4. Compute genus-level mean NGSA metal concentrations (z-scored).
  5. Merge with MicrobeAtlas Levins' B_std from genus_trait_table.csv.
  6. Run PGLS per metal (Cu, Zn, Pb, Ni, Co as in NB16 NGSA analysis).
  7. Save results to data/sensitivity_microbeatlas_ngsa_pgls.csv.
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.neighbors import BallTree

PROJECT_DIR = Path(__file__).parent.parent
DATA        = PROJECT_DIR / 'data'
SCRIPTS     = PROJECT_DIR / 'scripts'
CACHE_DIR   = DATA / 'nb29_aus_cache'
CACHE_DIR.mkdir(exist_ok=True)

MAX_DIST_KM = 200   # same threshold as NB16

# ── Step 1: Load MicrobeAtlas sample metadata; filter to Australia ─────────────
print('Step 1: Loading MicrobeAtlas samples...')
samples = pd.read_csv(DATA / 'sample_latlon_env.csv')
samples = samples[
    (samples['LatitudeParsed'] != 'Unknown') &
    samples['LatitudeParsed'].notna() &
    samples['LongitudeParsed'].notna()
].copy()
samples['lat'] = pd.to_numeric(samples['LatitudeParsed'], errors='coerce')
samples['lon'] = pd.to_numeric(samples['LongitudeParsed'], errors='coerce')
samples = samples.dropna(subset=['lat', 'lon'])

# Australian bounding box
aus = samples[
    (samples['lat'] >= -44) & (samples['lat'] <= -10) &
    (samples['lon'] >= 112) & (samples['lon'] <= 154)
].copy()
print(f'  MicrobeAtlas Australian samples: {len(aus):,}')

# ── Step 2: Haversine join to NGSA ───────────────────────────────────────────
print('\nStep 2: Joining MicrobeAtlas Australian samples to NGSA...')
ngsa = pd.read_csv(DATA / 'ngsa_geochemistry.csv')
ngsa = ngsa.dropna(subset=['lat', 'lon'])
print(f'  NGSA sites: {len(ngsa):,}')

# BallTree haversine join
ngsa_rad = np.radians(ngsa[['lat', 'lon']].values)
aus_rad  = np.radians(aus[['lat', 'lon']].values)

tree_ngsa = BallTree(ngsa_rad, metric='haversine')
distances, indices = tree_ngsa.query(aus_rad, k=1)
dist_km = distances[:, 0] * 6371

aus['ngsa_dist_km'] = dist_km
aus['ngsa_idx']     = indices[:, 0]

matched = aus[aus['ngsa_dist_km'] <= MAX_DIST_KM].copy()
print(f'  Matched within {MAX_DIST_KM} km: {len(matched):,} samples')

# Attach NGSA metal concentrations to matched samples
metal_cols = ['Cu_ppm', 'Zn_ppm', 'Pb_ppm', 'Ni_ppm', 'Co_ppm', 'As_ppm', 'Cr_ppm', 'Hg_ppm']
ngsa_sub = ngsa[['lat', 'lon'] + metal_cols].copy()
ngsa_sub.index = range(len(ngsa_sub))

matched = matched.copy()
for col in metal_cols:
    matched[col] = ngsa_sub.loc[matched['ngsa_idx'].values, col].values

# ── Step 3: Spark — genus detections for Australian samples ───────────────────
GENUS_DET_CACHE = CACHE_DIR / 'aus_genus_detections.parquet'

if GENUS_DET_CACHE.exists():
    print('\nLoading cached genus detections...')
    genus_det = pd.read_parquet(GENUS_DET_CACHE)
else:
    print('\nStep 3: Querying Spark for genus detections in Australian samples...')

    try:
        import berdl_notebook_utils
        spark = berdl_notebook_utils.get_spark_session()
    except Exception:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
    print(f'  Spark {spark.version} connected.')

    aus_sample_ids = matched['sample_id'].tolist()
    print(f'  Registering {len(aus_sample_ids):,} Australian sample IDs...')

    aus_sdf = spark.createDataFrame(
        pd.DataFrame({'sample_id': aus_sample_ids})
    )
    aus_sdf.createOrReplaceTempView('aus_samples')

    print('  Joining otu_counts_long with Australian samples and otu_metadata...')
    genus_det_sdf = spark.sql("""
        SELECT
            oc.sample_id,
            om.Tax,
            SUM(oc.count) AS total_count
        FROM arkinlab.microbeatlas.otu_counts_long oc
        JOIN aus_samples   as_ids ON oc.sample_id = as_ids.sample_id
        JOIN arkinlab.microbeatlas.otu_metadata om ON oc.otu_id = om.otu_id
        WHERE oc.count > 0
        GROUP BY oc.sample_id, om.Tax
    """)
    genus_det = genus_det_sdf.toPandas()
    print(f'  Sample×Tax rows: {len(genus_det):,}')
    genus_det.attrs = {}  # Clear non-JSON-serializable metadata
    genus_det.to_parquet(GENUS_DET_CACHE, index=False)

# ── Step 4: extract genus from Tax string ────────────────────────────────────
print('\nStep 4: Extracting genus from Tax string...')

def extract_genus(tax):
    if not isinstance(tax, str):
        return None
    parts = [p.strip() for p in tax.split(';') if p.strip()]
    if not parts:
        return None
    g = parts[-1]
    return g if g else None

genus_det['genus_lower'] = genus_det['Tax'].apply(extract_genus).str.lower().str.strip()
genus_det = genus_det[
    genus_det['genus_lower'].notna() &
    (genus_det['genus_lower'] != '') &
    ~genus_det['genus_lower'].str.startswith('bacteria', na=True)
]
print(f'  After genus extraction: {genus_det["genus_lower"].nunique():,} unique genera')

# ── Step 5: join NGSA metals to sample-genus rows ────────────────────────────
print('\nStep 5: Joining NGSA metals to sample-genus detections...')

# Create sample → NGSA metals lookup
sample_ngsa = matched.set_index('sample_id')[metal_cols].copy()
genus_det2  = genus_det.merge(
    sample_ngsa.reset_index().rename(columns={'index': 'sample_id'}),
    on='sample_id', how='inner'
)
print(f'  Sample-genus rows with NGSA: {len(genus_det2):,}')

# Genus-level mean NGSA concentrations
genus_ngsa = genus_det2.groupby('genus_lower')[metal_cols].mean().reset_index()
genus_ngsa['n_samples'] = genus_det2.groupby('genus_lower')['sample_id'].nunique().values
print(f'  Genera with NGSA concentrations: {len(genus_ngsa):,}')

# ── Step 6: merge with Levins' B and run PGLS per metal ─────────────────────
print('\nStep 6: Merging with Levins\' B_std and running PGLS...')

traits  = pd.read_csv(DATA / 'genus_trait_table.csv')
pgls_in = genus_ngsa.merge(
    traits[['gtdb_genus_lower', 'mean_levins_B_std', 'n_otus']],
    left_on='genus_lower', right_on='gtdb_genus_lower',
    how='inner'
).dropna(subset=['mean_levins_B_std'])
pgls_in = pgls_in[pgls_in['n_otus'] >= 3].copy()
print(f'  PGLS input genera (n_otus ≥ 3): {len(pgls_in):,}')

results = []
primary_metals = ['Cu_ppm', 'Zn_ppm', 'Pb_ppm', 'Ni_ppm', 'Co_ppm']
all_metals     = metal_cols

for metal in all_metals:
    sub = pgls_in[['genus_lower', 'mean_levins_B_std', metal]].dropna(subset=[metal]).copy()
    if len(sub) < 50:
        print(f'  {metal}: only {len(sub)} genera, skipping')
        continue
    sub['metal_z'] = (sub[metal] - sub[metal].mean()) / sub[metal].std()
    sub = sub.dropna(subset=['metal_z'])

    input_csv  = CACHE_DIR / f'pgls_input_{metal}.csv'
    output_csv = CACHE_DIR / f'pgls_result_{metal}.csv'
    sub[['genus_lower', 'mean_levins_B_std', 'metal_z']].to_csv(input_csv, index=False)

    # Activate r_env and run Rscript
    shell_cmd = f"""
source /opt/conda/etc/profile.d/conda.sh && conda activate r_env && \\
Rscript {SCRIPTS / 'pgls_generic.R'} \\
  --input     {input_csv} \\
  --tree      {DATA / 'gtdb_bac_genus_pruned.tree'} \\
  --response  mean_levins_B_std \\
  --predictor metal_z \\
  --output    {output_csv} \\
  --label     'MicrobeAtlas+NGSA {metal} (NB29)'
"""
    r = subprocess.run(['bash', '-c', shell_cmd], capture_output=True, text=True, cwd=str(PROJECT_DIR))
    if r.returncode != 0:
        print(f'  {metal}: R error — {r.stderr[-500:]}')
        continue
    row = pd.read_csv(output_csv)
    row['metal'] = metal
    row['primary'] = metal in primary_metals
    row['n_genera'] = len(sub)
    results.append(row)
    beta = row['beta'].iloc[0]
    p    = row['p_value'].iloc[0]
    print(f'  {metal}: n={len(sub)}, β={beta:+.4f}, p={p:.4g}')

if not results:
    print('ERROR: No PGLS results produced.')
    sys.exit(1)

# ── Step 7: combine results and apply BH-FDR ─────────────────────────────────
print('\nStep 7: Combining results and applying BH-FDR...')
from scipy.stats import false_discovery_control

combined = pd.concat(results, ignore_index=True)
combined = combined.sort_values('p_value').reset_index(drop=True)

p_vals = combined['p_value'].values
q_vals = false_discovery_control(p_vals, method='bh')
combined['q_bh'] = q_vals

output_final = DATA / 'sensitivity_microbeatlas_ngsa_pgls.csv'
combined.to_csv(output_final, index=False)
print(f'\nSaved: {output_final}')
print('\n=== RESULTS ===')
print(combined[['metal', 'primary', 'n_genera', 'n', 'lambda', 'beta', 'SE', 'p_value', 'q_bh']].to_string(index=False))

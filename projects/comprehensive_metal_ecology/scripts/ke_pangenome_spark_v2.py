#!/usr/bin/env python3
"""
ke_pangenome analysis v2 — query KO genomes one at a time.

Strategy: For each KO, run a simple COUNT query in Spark to get
the list of genomes that have it. The 3-way join is unavoidable,
but querying one KO at a time keeps results small.
"""
import sys
sys.stdout.reconfigure(line_buffering=True)

import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.spatial import cKDTree
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

DATA = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
OUTDIR = DATA / 'confound_results'
OUTDIR.mkdir(exist_ok=True)
PROJECTS = Path('/home/hmacgregor/BERIL-research-observatory/projects')

MIN_GENOMES_PER_GENUS = 8
MIN_GENERA = 10
METALS = ['PF1_As', 'PF1_Cd', 'PF1_Cr', 'PF1_Cu', 'PF1_Hg', 'PF1_Pb']
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

# ── CSU metal grid ────────────────────────────────────────────────────
print("Loading metal grid...")
csu_grid = pd.read_parquet(PROJECTS / 'microbeatlas_metal_ecology' / 'data' / 'csu_metal_mobility_grid.parquet')
csu_tree = cKDTree(csu_grid[['lat', 'lon']].values)

env_full = pd.read_csv(DATA / 'genome_env_covariates_full.csv')
env_locs = env_full[['latitude', 'longitude']].dropna()
env_tree = cKDTree(env_locs.values)

from berdl_notebook_utils import get_spark_session
spark = get_spark_session()

# ── Spatial genomes ───────────────────────────────────────────────────
print("Getting spatial genomes...")
spatial_genomes = spark.sql("""
    SELECT genome_id, cleaned_lat AS latitude, cleaned_lon AS longitude,
           genus, phylum
    FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
    WHERE cleaned_lat IS NOT NULL AND cleaned_lon IS NOT NULL
      AND genus IS NOT NULL AND genus != ''
""").toPandas()
print(f"  {len(spatial_genomes):,} genomes")

# Genome size
try:
    gsizes = spark.sql("""
        SELECT accession AS genome_id, TRY_CAST(genome_size AS BIGINT) AS genome_size
        FROM kbase.ke_pangenome.gtdb_metadata WHERE genome_size IS NOT NULL
    """).toPandas()
    spatial_genomes = spatial_genomes.merge(gsizes, on='genome_id', how='left')
except:
    spatial_genomes['genome_size'] = np.nan

# Assign metals + env
for c in METALS + ENV_COLS:
    spatial_genomes[c] = np.nan
valid = spatial_genomes.latitude.notna() & spatial_genomes.longitude.notna()
locs = spatial_genomes.loc[valid, ['latitude', 'longitude']].values
dd, ii = csu_tree.query(locs, k=1)
for c in METALS:
    vals = csu_grid[c].values[ii].copy()
    vals[dd > 0.5] = np.nan
    spatial_genomes.loc[valid, c] = vals
dd2, ii2 = env_tree.query(locs, k=1)
for c in ENV_COLS:
    if c in env_full.columns:
        vals2 = env_full[c].values[ii2].copy()
        vals2[dd2 > 0.5] = np.nan
        spatial_genomes.loc[valid, c] = vals2

# Filter to usable genera
genus_cts = spatial_genomes.genus.value_counts()
usable_genera = genus_cts[genus_cts >= MIN_GENOMES_PER_GENUS]
spatial_genomes = spatial_genomes[spatial_genomes.genus.isin(usable_genera.index)].copy()
spatial_genomes = spatial_genomes.reset_index(drop=True)
print(f"  Usable genera: {len(usable_genera)}, genomes in usable: {len(spatial_genomes):,}")

spatial_set = set(spatial_genomes.genome_id)
genome_id_arr = spatial_genomes.genome_id.values
genus_groups = {g: spatial_genomes.index[spatial_genomes.genus == g].values
                for g in usable_genera.index}

# ── Get variable KOs ─────────────────────────────────────────────────
# First: create a Spark view for the pre-joined KO→genome mapping
# This avoids repeating the 3-way join for each KO query
print("\nCreating materialized KO→genome view in Spark...")
print("  (This is a single 3-way join — will take a few minutes)")

# Use CREATE OR REPLACE TEMP VIEW to cache the join result
spark.sql("""
    CREATE OR REPLACE TEMPORARY VIEW ko_genome_map AS
    SELECT DISTINCT REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id, g.genome_id
    FROM kbase.ke_pangenome.gene g
    JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
        ON g.gene_id = ggc.gene_id
    JOIN kbase.ke_pangenome.eggnog_mapper_annotations e
        ON ggc.gene_cluster_id = e.query_name
    WHERE e.KEGG_ko IS NOT NULL
      AND e.KEGG_ko != ''
      AND e.KEGG_ko != '-'
""")
print("  View created")

# Cache it for faster subsequent queries
spark.sql("CACHE TABLE ko_genome_map")
print("  View cached")

# Get KO prevalence
print("  Getting KO prevalence...")
ko_prev = spark.sql("""
    SELECT ko_id, COUNT(DISTINCT genome_id) AS n_genomes
    FROM ko_genome_map
    GROUP BY ko_id
""").toPandas()
print(f"  Total KOs: {len(ko_prev):,}")

total_g = len(spatial_genomes)
ko_prev['prevalence'] = ko_prev.n_genomes / total_g
variable_kos = ko_prev[
    (ko_prev.prevalence >= 0.05) & (ko_prev.prevalence <= 0.95)
].ko_id.tolist()
print(f"  Variable KOs (5-95%): {len(variable_kos):,}")

# ── Per-KO meta-analysis ─────────────────────────────────────────────
print(f"\nRunning per-KO queries ({len(variable_kos)} KOs)...")
results = []

for i, ko_id in enumerate(variable_kos):
    if (i + 1) % 100 == 0:
        print(f"  KO {i+1}/{len(variable_kos)} ({len(results):,} pairs found)...")

    try:
        genomes_df = spark.sql(f"""
            SELECT DISTINCT genome_id FROM ko_genome_map
            WHERE ko_id = '{ko_id}'
        """).toPandas()
    except:
        continue

    genomes_with_ko = set(genomes_df.genome_id) & spatial_set
    if not genomes_with_ko:
        continue

    ko_vec = np.isin(genome_id_arr, list(genomes_with_ko)).astype(float)
    overall_prev = ko_vec.mean()
    if overall_prev < 0.05 or overall_prev > 0.95:
        continue

    for metal in METALS:
        met_vals = spatial_genomes[metal].values
        effects = []
        for genus, idx in genus_groups.items():
            ko = ko_vec[idx]
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
        results.append({
            'ko_id': ko_id, 'metal': metal.replace('PF1_', ''),
            'is_target': ko_id in TARGET_KOS,
            'meta_rho': np.tanh(mz), 'meta_p': p, 'n_genera': len(effects)
        })

spark.stop()

# ── Results ───────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("RESULTS: ke_pangenome")
print(f"{'='*60}")

if not results:
    print("No results!")
    exit(1)

raw_scan = pd.DataFrame(results)
_, q_vals, _, _ = multipletests(raw_scan.meta_p.values, method='fdr_bh')
raw_scan['q_fdr'] = q_vals
raw_scan.to_csv(OUTDIR / 'ke_pangenome_genomewide_raw_scan.csv', index=False)

n_sig = (raw_scan.q_fdr < 0.05).sum()
print(f"  Genomes: {len(spatial_genomes):,}, Genera: {len(usable_genera)}")
print(f"  Tested: {len(raw_scan):,} pairs")
print(f"  Significant: {n_sig} ({n_sig/len(raw_scan):.1%})")

print(f"\n  Per-metal:")
for m in ['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb']:
    sub = raw_scan[raw_scan.metal == m]
    n = (sub.q_fdr < 0.05).sum()
    print(f"    {m:4s}: {n:>5d}/{len(sub):>5d} ({n/max(len(sub),1):.1%})")

print(f"\n  Top 30 hits:")
for _, r in raw_scan.nsmallest(30, 'meta_p').iterrows():
    tag = '*' if r.is_target else ' '
    gene = TARGET_KOS.get(r.ko_id, r.ko_id)
    sig = 'Y' if r.q_fdr < 0.05 else 'n'
    print(f"    {tag} {gene:18s} × {r.metal:3s}: ρ={r.meta_rho:+.4f} "
          f"p={r.meta_p:.2e} q={r.q_fdr:.4f} [{sig}] ({r.n_genera}g)")

print(f"\n  Target KO results:")
for _, r in raw_scan[raw_scan.is_target].nsmallest(20, 'meta_p').iterrows():
    gene = TARGET_KOS.get(r.ko_id, r.ko_id)
    sig = '**' if r.q_fdr < 0.05 else '  '
    print(f"    {sig} {gene:18s} × {r.metal:3s}: ρ={r.meta_rho:+.4f} "
          f"q={r.q_fdr:.4f} ({r.n_genera}g)")

print("\nDONE")

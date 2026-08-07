#!/usr/bin/env python3
"""
ke_pangenome confound analysis — computed entirely in Spark.

Instead of pulling the full KO matrix to Python (which OOMs),
we compute within-genus correlations as Spark SQL aggregations
and only pull summary stats.

Pipeline:
  1. Build genome → KO presence view in Spark
  2. Join with spatial/metal/env data
  3. Compute per-genus point-biserial ρ for each (KO, metal) pair
  4. Pull genus-level summaries to Python for meta-analysis
"""
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
print("Loading CSU metal mobility grid...", flush=True)
csu_grid = pd.read_parquet(PROJECTS / 'microbeatlas_metal_ecology' / 'data' / 'csu_metal_mobility_grid.parquet')
csu_tree = cKDTree(csu_grid[['lat', 'lon']].values)

# ── Env covariates ────────────────────────────────────────────────────
env_full = pd.read_csv(DATA / 'genome_env_covariates_full.csv')
env_locs = env_full[['latitude', 'longitude']].dropna()
env_tree = cKDTree(env_locs.values)
ENV_COLS = ['ph_h2o', 'organic_carbon_density', 'clay_pct',
            'mean_annual_temp_C', 'mean_annual_precip_mm',
            'elevation_m', 'litho_mafic_score']

from berdl_notebook_utils import get_spark_session
spark = get_spark_session()

# ══════════════════════════════════════════════════════════════════════
# Step 1: Get spatial genome metadata — this is small enough for Python
# ══════════════════════════════════════════════════════════════════════
print("\nStep 1: Getting spatial genome metadata...", flush=True)
spatial_genomes = spark.sql("""
    SELECT genome_id, cleaned_lat AS latitude, cleaned_lon AS longitude,
           genus, phylum
    FROM kbase.ke_pangenome.alphaearth_embeddings_all_years
    WHERE cleaned_lat IS NOT NULL AND cleaned_lon IS NOT NULL
      AND genus IS NOT NULL AND genus != ''
""").toPandas()
print(f"  {len(spatial_genomes):,} genomes with lat/lon + genus")

# Get genome_size
try:
    gsizes = spark.sql("""
        SELECT accession AS genome_id,
               TRY_CAST(genome_size AS BIGINT) AS genome_size
        FROM kbase.ke_pangenome.gtdb_metadata
        WHERE genome_size IS NOT NULL
    """).toPandas()
    spatial_genomes = spatial_genomes.merge(gsizes, on='genome_id', how='left')
except:
    spatial_genomes['genome_size'] = np.nan

# Assign metals and env covariates via KD-tree
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
print(f"  Usable genera (≥{MIN_GENOMES_PER_GENUS}): {len(usable_genera)}")
spatial_genomes = spatial_genomes[spatial_genomes.genus.isin(usable_genera.index)].copy()
spatial_genomes = spatial_genomes.reset_index(drop=True)
print(f"  Genomes in usable genera: {len(spatial_genomes):,}")

# ══════════════════════════════════════════════════════════════════════
# Step 2: Get KO presence per genome from Spark — but per-KO at a time
# For each target KO or high-interest KO, query which genomes have it
# ══════════════════════════════════════════════════════════════════════
print("\nStep 2: Getting KO prevalence per genome from Spark...", flush=True)

# First get all KOs and their genome counts to find variable ones
print("  Getting KO prevalence summary...", flush=True)
ko_prevalence = spark.sql("""
    SELECT REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id,
           COUNT(DISTINCT g.genome_id) AS n_genomes
    FROM kbase.ke_pangenome.gene g
    JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
        ON g.gene_id = ggc.gene_id
    JOIN kbase.ke_pangenome.eggnog_mapper_annotations e
        ON ggc.gene_cluster_id = e.query_name
    WHERE e.KEGG_ko IS NOT NULL
      AND e.KEGG_ko != ''
      AND e.KEGG_ko != '-'
    GROUP BY REPLACE(e.KEGG_ko, 'ko:', '')
""").toPandas()
print(f"  Total KOs in ke_pangenome: {len(ko_prevalence):,}")

# Estimate total genome count from gene table
total_genomes_approx = len(spatial_genomes)  # Use spatial genomes as denominator
ko_prevalence['prevalence'] = ko_prevalence.n_genomes / total_genomes_approx
variable_kos = ko_prevalence[
    (ko_prevalence.prevalence >= 0.05) & (ko_prevalence.prevalence <= 0.95)
].ko_id.tolist()
print(f"  Variable KOs (5-95% prevalence): {len(variable_kos):,}")

# ══════════════════════════════════════════════════════════════════════
# Step 3: For each KO, get the set of genomes that have it
# Then compute within-genus meta-analysis locally
# Key insight: we only need genome_ids per KO, not the full matrix
# ══════════════════════════════════════════════════════════════════════
print("\nStep 3: Per-KO genome queries and meta-analysis...", flush=True)

spatial_set = set(spatial_genomes.genome_id)
genome_idx = spatial_genomes.set_index('genome_id')

# Pre-compute genus indices
genus_groups = {}
for genus in usable_genera.index:
    mask = spatial_genomes.genus == genus
    genus_groups[genus] = spatial_genomes.index[mask].values

results = []
batch_size = 50  # Query 50 KOs at a time
ko_list = variable_kos
genome_id_arr = spatial_genomes.genome_id.values

for batch_start in range(0, len(ko_list), batch_size):
    batch_kos = ko_list[batch_start:batch_start + batch_size]
    batch_num = batch_start // batch_size + 1
    total_batches = (len(ko_list) + batch_size - 1) // batch_size

    if batch_num % 10 == 1:
        print(f"  Batch {batch_num}/{total_batches} ({len(results):,} pairs found)...", flush=True)

    ko_str = "','".join(batch_kos)
    try:
        # Get genome_ids that have each KO
        ko_genomes = spark.sql(f"""
            SELECT DISTINCT REPLACE(e.KEGG_ko, 'ko:', '') AS ko_id,
                   g.genome_id
            FROM kbase.ke_pangenome.gene g
            JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
                ON g.gene_id = ggc.gene_id
            JOIN kbase.ke_pangenome.eggnog_mapper_annotations e
                ON ggc.gene_cluster_id = e.query_name
            WHERE REPLACE(e.KEGG_ko, 'ko:', '') IN ('{ko_str}')
        """).toPandas()

        # Filter to spatial genomes
        ko_genomes = ko_genomes[ko_genomes.genome_id.isin(spatial_set)]

        if len(ko_genomes) == 0:
            continue

        # For each KO in this batch, run within-genus meta-analysis
        for ko_id in ko_genomes.ko_id.unique():
            genomes_with_ko = set(ko_genomes[ko_genomes.ko_id == ko_id].genome_id)

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

    except Exception as ex:
        err = str(ex)[:150]
        if 'maxResultSize' in err:
            # Try one KO at a time
            for ko_id in batch_kos:
                try:
                    single = spark.sql(f"""
                        SELECT DISTINCT g.genome_id
                        FROM kbase.ke_pangenome.gene g
                        JOIN kbase.ke_pangenome.gene_genecluster_junction ggc
                            ON g.gene_id = ggc.gene_id
                        JOIN kbase.ke_pangenome.eggnog_mapper_annotations e
                            ON ggc.gene_cluster_id = e.query_name
                        WHERE REPLACE(e.KEGG_ko, 'ko:', '') = '{ko_id}'
                    """).toPandas()

                    single = single[single.genome_id.isin(spatial_set)]
                    if len(single) == 0:
                        continue

                    genomes_with_ko = set(single.genome_id)
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
                except:
                    continue
        else:
            print(f"    Batch error: {err}")
        continue

spark.stop()

# ══════════════════════════════════════════════════════════════════════
# Step 4: Results
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*80}")
print("RESULTS")
print(f"{'='*80}\n")

if not results:
    print("No results found!")
    exit(1)

raw_scan = pd.DataFrame(results)
_, q_vals, _, _ = multipletests(raw_scan.meta_p.values, method='fdr_bh')
raw_scan['q_fdr'] = q_vals
raw_scan.to_csv(OUTDIR / 'ke_pangenome_genomewide_raw_scan.csv', index=False)

n_sig = (raw_scan.q_fdr < 0.05).sum()
print(f"ke_pangenome: {len(spatial_genomes):,} genomes, {len(usable_genera)} genera")
print(f"Tested: {len(raw_scan):,} KO×metal pairs")
print(f"Significant (FDR<0.05): {n_sig}")
print(f"Fraction: {n_sig/len(raw_scan):.1%}")

print(f"\nPer-metal:")
for m in ['Hg', 'As', 'Cu', 'Cr', 'Cd', 'Pb']:
    sub = raw_scan[raw_scan.metal == m]
    n = (sub.q_fdr < 0.05).sum()
    print(f"  {m:4s}: {n:>5d}/{len(sub):>5d} ({n/max(len(sub),1):.1%})")

print(f"\nTop 30 hits:")
top = raw_scan.nsmallest(30, 'meta_p')
for _, r in top.iterrows():
    tag = '*' if r.is_target else ' '
    gene = TARGET_KOS.get(r.ko_id, r.ko_id)
    sig = 'Y' if r.q_fdr < 0.05 else 'n'
    print(f"  {tag} {gene:18s} × {r.metal:3s}: ρ={r.meta_rho:+.4f} "
          f"p={r.meta_p:.2e} q={r.q_fdr:.4f} [{sig}] ({r.n_genera} genera)")

# Target KOs specifically
print(f"\nTarget KO results:")
target_results = raw_scan[raw_scan.is_target].sort_values('meta_p')
for _, r in target_results.head(30).iterrows():
    gene = TARGET_KOS.get(r.ko_id, r.ko_id)
    sig = '**' if r.q_fdr < 0.05 else '  '
    print(f"  {sig} {gene:18s} × {r.metal:3s}: ρ={r.meta_rho:+.4f} "
          f"p={r.meta_p:.2e} q={r.q_fdr:.4f} ({r.n_genera} genera)")

print("\nDONE")

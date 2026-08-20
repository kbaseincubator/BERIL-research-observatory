#!/usr/bin/env python3
"""
Run NB24 pangenome core/accessory analysis end-to-end from the command line.
Saves intermediate genus_clusters to parquet so re-runs are fast.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

DATA    = Path(__file__).parent.parent / 'data'
FIGURES = Path(__file__).parent.parent / 'figures'
FIGURES.mkdir(exist_ok=True)
CACHE   = DATA / 'nb24_genus_clusters_cache.parquet'

# ── Spark ──────────────────────────────────────────────────────────────────
try:
    import berdl_notebook_utils
    spark = berdl_notebook_utils.get_spark_session()
except Exception:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
print(f'Spark {spark.version} connected.')

# ── KO lists ───────────────────────────────────────────────────────────────
metal_kos = pd.read_csv(DATA / 'curated_mrg_ko_ids_final.csv')['ko_id'].tolist()
metal_kos_prefixed = ['ko:' + k for k in metal_kos]
all_metal_forms = metal_kos + metal_kos_prefixed
ko_sql_set = "(" + ", ".join(f"'{k}'" for k in all_metal_forms) + ")"
print(f'Metal KOs: {len(metal_kos)}')

# ── Load or compute genus_clusters ─────────────────────────────────────────
if CACHE.exists():
    print(f'Loading cached genus_clusters from {CACHE}')
    genus_clusters = pd.read_parquet(CACHE)
    print(f'  Rows: {len(genus_clusters):,}, genera: {genus_clusters["genus_lower"].nunique():,}')
else:
    print('Running Spark queries (this takes 10-20 min)...')

    print('  Step 1/4: metal_annotated_genes...')
    spark.sql(f"""
    CREATE OR REPLACE TEMP VIEW metal_annotated_genes AS
    SELECT DISTINCT ego.query_name
    FROM kbase.ke_pangenome.eggnog_mapper_annotations ego
    LATERAL VIEW explode(split(ego.KEGG_ko, '[|,]')) t AS ko_single
    WHERE trim(ko_single) IN {ko_sql_set}
    """)
    n_genes = spark.sql('SELECT COUNT(*) FROM metal_annotated_genes').collect()[0][0]
    print(f'    Genes with metal KO: {n_genes:,}')

    print('  Step 2/4: metal_clusters_core...')
    spark.sql("""
    CREATE OR REPLACE TEMP VIEW metal_clusters_core AS
    SELECT DISTINCT
        junc.gene_cluster_id,
        gc.is_core,
        gc.gtdb_species_clade_id
    FROM metal_annotated_genes mag
    JOIN kbase.ke_pangenome.gene_genecluster_junction junc ON mag.query_name = junc.gene_id
    JOIN kbase.ke_pangenome.gene_cluster gc ON junc.gene_cluster_id = gc.gene_cluster_id
    """)
    n_cl = spark.sql('SELECT COUNT(DISTINCT gene_cluster_id) FROM metal_clusters_core').collect()[0][0]
    print(f'    Metal clusters: {n_cl:,}')

    print('  Step 3/4: clade_genus lookup...')
    spark.sql("""
    CREATE OR REPLACE TEMP VIEW clade_genus AS
    SELECT DISTINCT
        g.gtdb_species_clade_id,
        lower(tax.genus) AS genus_lower,
        tax.phylum
    FROM kbase.ke_pangenome.genome g
    JOIN kbase.ke_pangenome.gtdb_taxonomy_r214v1 tax ON g.genome_id = tax.genome_id
    WHERE tax.genus IS NOT NULL AND tax.genus != ''
    """)

    print('  Step 4/4: genus-level join (slowest step)...')
    genus_clusters = spark.sql("""
    SELECT
        cg.genus_lower,
        cg.phylum,
        mcc.gene_cluster_id,
        FIRST(mcc.is_core) AS is_core
    FROM metal_clusters_core mcc
    JOIN clade_genus cg ON mcc.gtdb_species_clade_id = cg.gtdb_species_clade_id
    GROUP BY cg.genus_lower, cg.phylum, mcc.gene_cluster_id
    """).toPandas()

    print(f'  genus_clusters rows: {len(genus_clusters):,}, genera: {genus_clusters["genus_lower"].nunique():,}')
    genus_clusters.attrs = {}  # Clear Spark metadata to allow parquet serialization
    genus_clusters.to_parquet(CACHE, index=False)
    print(f'  Cached to {CACHE}')

# ── Genus-level aggregation ────────────────────────────────────────────────
genus_agg_full = (
    genus_clusters
    .groupby(['genus_lower', 'phylum'])
    .agg(
        n_metal_clusters=('gene_cluster_id', 'nunique'),
        n_core_metal=('is_core', 'sum'),
    )
    .reset_index()
)
genus_agg_full['core_fraction_metal'] = genus_agg_full['n_core_metal'] / genus_agg_full['n_metal_clusters']
print(f'\nGenera with any metal clusters: {len(genus_agg_full):,}')

# Strip GTDB g__ prefix to match trait table's bare lowercase gtdb_genus_lower
genus_agg_full['genus_key'] = genus_agg_full['genus_lower'].str.replace(r'^g__', '', regex=True)

# Filter: ≥3 metal clusters per genus
genus_filt = genus_agg_full[genus_agg_full['n_metal_clusters'] >= 3].copy()
print(f'Genera with ≥3 metal clusters: {len(genus_filt):,}')

# ── Merge with trait table ─────────────────────────────────────────────────
traits = pd.read_csv(DATA / 'genus_trait_table.csv')
print(f'Trait table: {len(traits):,} genera')
print(f'Sample genus_key: {genus_filt["genus_key"].head(3).tolist()}')
print(f'Sample gtdb_genus_lower: {traits["gtdb_genus_lower"].dropna().head(3).tolist()}')

pgls_df = genus_filt.merge(
    traits[['gtdb_genus_lower', 'mean_levins_B_std', 'n_otus', 'phylum']],
    left_on='genus_key', right_on='gtdb_genus_lower',
    how='inner',
    suffixes=('_kbase', '_traits')
).dropna(subset=['core_fraction_metal', 'mean_levins_B_std'])

print(f'\nMatched genera: {len(pgls_df):,}')

if len(pgls_df) == 0:
    print('ERROR: zero genera matched. Checking overlap manually...')
    trait_set = set(traits['gtdb_genus_lower'].dropna().str.lower())
    kbase_set = set(genus_filt['genus_key'].str.lower())
    overlap = trait_set & kbase_set
    print(f'  Trait genera: {len(trait_set)}, KBase genera: {len(kbase_set)}, overlap: {len(overlap)}')
    print(f'  Sample trait: {list(trait_set)[:5]}')
    print(f'  Sample kbase: {list(kbase_set)[:5]}')
    sys.exit(1)

# ── Primary Spearman ρ ─────────────────────────────────────────────────────
sub_all = pgls_df.dropna(subset=['core_fraction_metal', 'mean_levins_B_std'])
sub_3   = sub_all[sub_all['n_otus'] >= 3]

rho_all, p_all = spearmanr(sub_all['mean_levins_B_std'], sub_all['core_fraction_metal'])
rho_3,   p_3   = spearmanr(sub_3['mean_levins_B_std'],   sub_3['core_fraction_metal'])

print('\n=== PRIMARY RESULT ===')
print(f'Pre-specified direction: NEGATIVE (specialists → higher core_fraction_metal)')
print(f'All genera:  ρ={rho_all:+.4f}, p={p_all:.4g}, n={len(sub_all)}')
print(f'n_otus ≥ 3:  ρ={rho_3:+.4f}, p={p_3:.4g}, n={len(sub_3)}')
print(f'Direction correct: {"YES" if rho_3 < 0 else "NO (positive or null)"}')

# ── Permutation test ───────────────────────────────────────────────────────
np.random.seed(42)
null_rhos = []
for _ in range(1000):
    perm_df = sub_3.copy()
    perm_df['core_fraction_perm'] = np.random.permutation(perm_df['core_fraction_metal'].values)
    r, _ = spearmanr(perm_df['mean_levins_B_std'], perm_df['core_fraction_perm'])
    null_rhos.append(r)
null_rhos = np.array(null_rhos)
p_perm = (null_rhos <= rho_3).mean()

print(f'\nNull ρ: {null_rhos.mean():+.4f} ± {null_rhos.std():.4f}')
print(f'Permutation p (one-tailed): {p_perm:.4g}')

# ── AMR negative control ───────────────────────────────────────────────────
AMR_KOS = [
    'K07816', 'K18305', 'K18307', 'K18308',
    'K03543', 'K03544', 'K03545',
    'K18228', 'K18229', 'K18230',
    'K02545', 'K02546', 'K02547',
    'K04687', 'K04688',
    'K01132', 'K01133',
]
amr_prefixed = ['ko:' + k for k in AMR_KOS]
amr_all = AMR_KOS + amr_prefixed
amr_sql_set = "(" + ", ".join(f"'{k}'" for k in amr_all) + ")"

AMR_CACHE = DATA / 'nb24_amr_clusters_cache.parquet'
if AMR_CACHE.exists():
    print('\nLoading cached AMR clusters...')
    amr_clusters = pd.read_parquet(AMR_CACHE)
else:
    print('\nRunning AMR Spark queries...')
    spark.sql(f"""
    CREATE OR REPLACE TEMP VIEW amr_annotated_genes AS
    SELECT DISTINCT ego.query_name
    FROM kbase.ke_pangenome.eggnog_mapper_annotations ego
    LATERAL VIEW explode(split(ego.KEGG_ko, '[|,]')) t AS ko_single
    WHERE trim(ko_single) IN {amr_sql_set}
    """)
    spark.sql("""
    CREATE OR REPLACE TEMP VIEW amr_clusters_core AS
    SELECT DISTINCT
        junc.gene_cluster_id,
        gc.is_core,
        gc.gtdb_species_clade_id
    FROM amr_annotated_genes ag
    JOIN kbase.ke_pangenome.gene_genecluster_junction junc ON ag.query_name = junc.gene_id
    JOIN kbase.ke_pangenome.gene_cluster gc ON junc.gene_cluster_id = gc.gene_cluster_id
    """)
    amr_clusters = spark.sql("""
    SELECT cg.genus_lower, acc.gene_cluster_id, FIRST(acc.is_core) AS is_core
    FROM amr_clusters_core acc
    JOIN clade_genus cg ON acc.gtdb_species_clade_id = cg.gtdb_species_clade_id
    WHERE cg.genus_lower IS NOT NULL AND cg.genus_lower != ''
    GROUP BY cg.genus_lower, acc.gene_cluster_id
    """).toPandas()
    amr_clusters.attrs = {}  # Clear Spark metadata to allow parquet serialization
    amr_clusters.to_parquet(AMR_CACHE, index=False)

print(f'AMR gene clusters: {len(amr_clusters):,}')
rho_amr, p_amr, n_amr = np.nan, np.nan, 0
if len(amr_clusters) > 0:
    amr_clusters['genus_key'] = amr_clusters['genus_lower'].str.replace(r'^g__', '', regex=True)
    amr_agg = (
        amr_clusters.groupby('genus_key')
        .agg(n_amr=('gene_cluster_id','nunique'), n_core_amr=('is_core','sum'))
        .reset_index()
    )
    amr_agg['core_fraction_amr'] = amr_agg['n_core_amr'] / amr_agg['n_amr']
    amr_merged = sub_3.merge(amr_agg, on='genus_key', how='inner').dropna(subset=['core_fraction_amr'])
    n_amr = len(amr_merged)
    if n_amr >= 10:
        rho_amr, p_amr = spearmanr(amr_merged['mean_levins_B_std'], amr_merged['core_fraction_amr'])
        print(f'AMR control: ρ={rho_amr:+.4f}, p={p_amr:.4g}, n={n_amr}')
    else:
        print(f'AMR: insufficient matches ({n_amr} genera)')

# ── Save primary result ────────────────────────────────────────────────────
result = pd.DataFrame([{
    'analysis': 'NB24_pangenome_core_accessory',
    'n_all': len(sub_all), 'n_otu3': len(sub_3),
    'rho_all': rho_all, 'p_all': p_all,
    'rho_otu3': rho_3, 'p_otu3': p_3,
    'p_perm_onetail': p_perm,
    'null_rho_mean': null_rhos.mean(), 'null_rho_sd': null_rhos.std(),
    'rho_amr': rho_amr, 'p_amr': p_amr, 'n_amr': n_amr,
    'direction_correct': rho_3 < 0,
    'significant': p_3 < 0.05,
}])
result.to_csv(DATA / 'nb24_primary_result.csv', index=False)
print(f'\nSaved: data/nb24_primary_result.csv')

print('\n=== SUMMARY ===')
print(f'  n_all={len(sub_all)}, n_otu3={len(sub_3)}')
print(f'  rho_otu3={rho_3:+.4f}, p_otu3={p_3:.4g}')
print(f'  p_perm={p_perm:.4g}')
print(f'  AMR control: rho={rho_amr:+.4f}, p={p_amr:.4g}, n={n_amr}')
print(f'  Consistent with hypothesis: {rho_3 < 0 and p_3 < 0.05}')

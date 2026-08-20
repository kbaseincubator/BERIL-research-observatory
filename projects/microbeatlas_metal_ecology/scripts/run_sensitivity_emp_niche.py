#!/usr/bin/env python3
"""
Sensitivity check NB28: EMP-derived niche breadth vs. MGnify ko_per_mb.

Strategy:
  1. Connect to Spark; query arkinlab.microbeatlas.sample_metadata schema.
  2. Identify EMP samples: look for an EMPO column first; if absent, filter
     by Project accessions known to belong to EMP Phase 1/2 studies, OR
     fall back to samples from ALL projects but with ≥8 Env_Level_1
     categories represented — then compute OTU-level Levins' B from those
     samples using Env_Level_1 as the habitat axis.
  3. Compute per-OTU Levins' B_std from EMP samples × Env_Level_1.
  4. Aggregate to genus level (mean over OTUs in the genus).
  5. Merge with MGnify ko_per_mb from data/mgnify_mag_ko_density.csv
     (the same predictor used in the primary PGLS, n=997, β=−0.022).
  6. Write PGLS input CSV and run scripts/pgls_generic.R.
  7. Save results to data/sensitivity_emp_niche_pgls.csv.
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DATA        = PROJECT_DIR / 'data'
SCRIPTS     = PROJECT_DIR / 'scripts'
CACHE_DIR   = DATA / 'nb28_emp_cache'
CACHE_DIR.mkdir(exist_ok=True)

# ── Spark ─────────────────────────────────────────────────────────────────────
try:
    import berdl_notebook_utils
    spark = berdl_notebook_utils.get_spark_session()
except Exception:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
print(f'Spark {spark.version} connected.')

# ── Step 1: inspect sample_metadata schema ────────────────────────────────────
print('\nStep 1: Inspecting sample_metadata schema...')
schema_df = spark.sql('DESCRIBE arkinlab.microbeatlas.sample_metadata').toPandas()
all_cols  = schema_df['col_name'].str.lower().tolist()
print('Columns:', all_cols[:30])

empo_col = None
for candidate in ['empo_3', 'empo_2', 'empo_1', 'empo', 'env_material', 'env_biome', 'env_feature']:
    if candidate in all_cols:
        empo_col = candidate
        print(f'EMPO column found: {empo_col}')
        break

# ── Step 2: identify EMP samples ─────────────────────────────────────────────
EMP_PROJECTS_CACHE = CACHE_DIR / 'emp_sample_ids.parquet'

if EMP_PROJECTS_CACHE.exists():
    print('\nLoading cached EMP sample list...')
    emp_samples_df = pd.read_parquet(EMP_PROJECTS_CACHE)
else:
    print('\nStep 2: Identifying EMP samples...')

    if empo_col:
        # EMPO column exists — use it directly; any sample with non-null EMPO is EMP
        emp_samples_sdf = spark.sql(f"""
            SELECT sample_id, {empo_col} AS empo_category, Env_Level_1
            FROM arkinlab.microbeatlas.sample_metadata
            WHERE {empo_col} IS NOT NULL AND trim({empo_col}) != ''
        """)
        n_empo = emp_samples_sdf.count()
        print(f'  Samples with EMPO category: {n_empo:,}')
        emp_samples_df = emp_samples_sdf.toPandas()
        emp_samples_df.attrs.clear()  # Clear non-JSON-serializable metadata
        emp_samples_df.to_parquet(EMP_PROJECTS_CACHE, index=False)
    else:
        # No EMPO column — identify EMP studies by Project accession.
        # EMP Phase 1 (Thompson et al. 2017 Science) primary SRA project: ERP012803.
        # EMP2 / collaborative studies: many. Use a broad filter on known EMP patterns.
        # Fallback: find projects where ≥12 of 13 Env_Level_1 categories are represented
        # (EMP has broad environment coverage), then take the top-N most diverse projects.
        print('  No EMPO column. Finding broadly-sampled projects (EMP proxy)...')

        # Get project × environment diversity
        # MicrobeAtlas stores EMP samples under individual SRA project accessions that
        # are typically habitat-specific; the maximum env diversity per project is 7.
        # Use threshold ≥4 Env_Level_1 categories AND ≥100 samples as an EMP proxy
        # (multi-environment projects that span the broad habitat space).
        proj_env = spark.sql("""
            SELECT Project,
                   COUNT(DISTINCT Env_Level_1) AS n_envs,
                   COUNT(*) AS n_samples
            FROM arkinlab.microbeatlas.sample_metadata
            WHERE Project IS NOT NULL AND Env_Level_1 IS NOT NULL
            GROUP BY Project
            HAVING COUNT(DISTINCT Env_Level_1) >= 4
               AND COUNT(*) >= 100
            ORDER BY n_envs DESC, n_samples DESC
        """).toPandas()

        print(f'  Projects with ≥4 Env categories and ≥100 samples: {len(proj_env)}')
        print(proj_env.to_string(index=False))

        if len(proj_env) == 0:
            raise ValueError("No multi-environment projects found — check sample_metadata.Project column")

        # Use all qualifying multi-environment projects as EMP proxy
        top_projects = proj_env['Project'].tolist()
        proj_list    = ", ".join(f"'{p}'" for p in top_projects)

        emp_samples_sdf = spark.sql(f"""
            SELECT sample_id, Project, Env_Level_1
            FROM arkinlab.microbeatlas.sample_metadata
            WHERE Project IN ({proj_list})
        """)
        emp_samples_df = emp_samples_sdf.toPandas()
        print(f'  EMP-proxy samples: {len(emp_samples_df):,}')
        print(f'  Env_Level_1 distribution:\n{emp_samples_df["Env_Level_1"].value_counts()}')
        emp_samples_df.attrs.clear()  # Clear non-JSON-serializable metadata
        emp_samples_df.to_parquet(EMP_PROJECTS_CACHE, index=False)

print(f'EMP samples: {len(emp_samples_df):,}')
print(f'Environments: {emp_samples_df["Env_Level_1"].nunique()}')

# ── Step 3: OTU × environment occurrence in EMP samples ──────────────────────
OTU_ENV_CACHE = CACHE_DIR / 'emp_otu_env_counts.parquet'

if OTU_ENV_CACHE.exists():
    print('\nLoading cached OTU×env counts...')
    otu_env = pd.read_parquet(OTU_ENV_CACHE)
else:
    print('\nStep 3: Computing OTU×environment occurrence from EMP samples...')
    emp_sample_ids = emp_samples_df['sample_id'].tolist()
    print(f'  Registering {len(emp_sample_ids):,} EMP sample IDs as temp view...')

    emp_sdf = spark.createDataFrame(emp_samples_df[['sample_id', 'Env_Level_1']])
    emp_sdf.createOrReplaceTempView('emp_samples')

    print('  Joining otu_counts_long with EMP samples...')
    otu_env_sdf = spark.sql("""
        SELECT
            oc.otu_id,
            es.Env_Level_1,
            COUNT(*) AS n_samples_detected
        FROM arkinlab.microbeatlas.otu_counts_long oc
        JOIN emp_samples es ON oc.sample_id = es.sample_id
        WHERE oc.count > 0
        GROUP BY oc.otu_id, es.Env_Level_1
    """)
    otu_env = otu_env_sdf.toPandas()
    print(f'  OTU×env rows: {len(otu_env):,}')
    otu_env.attrs.clear()  # Clear non-JSON-serializable metadata
    otu_env.to_parquet(OTU_ENV_CACHE, index=False)

# ── Step 4: Compute Levins' B_std per OTU ─────────────────────────────────────
print('\nStep 4: Computing EMP Levins\' B_std per OTU...')

n_envs_total = emp_samples_df['Env_Level_1'].nunique()
print(f'  J (number of environments): {n_envs_total}')

# Total detections per OTU across all EMP environments
otu_total = otu_env.groupby('otu_id')['n_samples_detected'].sum().rename('total_det')
otu_env2  = otu_env.merge(otu_total, on='otu_id')
otu_env2['p_i'] = otu_env2['n_samples_detected'] / otu_env2['total_det']

# Levins' B = 1 / sum(p_i^2); B_std = (B-1)/(J-1)
otu_levins = (
    otu_env2.groupby('otu_id')
    .apply(lambda x: 1.0 / (x['p_i']**2).sum(), include_groups=False)
    .rename('levins_B')
    .reset_index()
)
otu_levins['levins_B_std'] = (otu_levins['levins_B'] - 1) / (n_envs_total - 1)
otu_levins['levins_B_std'] = otu_levins['levins_B_std'].clip(0, 1)
print(f'  OTUs with EMP niche breadth: {len(otu_levins):,}')
print(f'  Mean B_std: {otu_levins["levins_B_std"].mean():.4f}')

# ── Step 5: aggregate to genus ────────────────────────────────────────────────
print('\nStep 5: Aggregating to genus level...')

otu_tax = pd.read_csv(DATA / 'otu_niche_breadth.csv',
                      usecols=['otu_id', 'Tax', 'kingdom'])

# Extract genus from Tax string (last semicolon-delimited field that's non-empty)
def extract_genus(tax):
    if not isinstance(tax, str):
        return None
    parts = [p.strip() for p in tax.split(';') if p.strip()]
    return parts[-1] if parts else None

otu_tax['genus_lower'] = otu_tax['Tax'].apply(extract_genus).str.lower().str.strip()
# Filter to Bacteria only, drop unmapped/empty
otu_tax = otu_tax[
    (otu_tax['kingdom'] == 'Bacteria') &
    otu_tax['genus_lower'].notna() &
    (otu_tax['genus_lower'] != '') &
    ~otu_tax['genus_lower'].str.contains(r'^bacteria', regex=True)
]

otu_merged = otu_levins.merge(otu_tax[['otu_id', 'genus_lower']], on='otu_id', how='inner')
genus_emp  = (
    otu_merged.groupby('genus_lower')
    .agg(
        emp_levins_B_std=('levins_B_std', 'mean'),
        n_otus_emp=('otu_id', 'count')
    )
    .reset_index()
)
print(f'  Genera with EMP niche breadth: {len(genus_emp):,}')

# ── Step 6: merge with MGnify ko_per_mb ───────────────────────────────────────
print('\nStep 6: Merging with MGnify ko_per_mb...')

# Load mgnify genus ko_per_mb (same predictor as primary PGLS)
mgnify = pd.read_csv(DATA / 'mgnify_mag_ko_density.csv')
# Genus from lineage string
mgnify['genus_lower'] = mgnify['lineage'].str.extract(r'g__([^;]+)').iloc[:, 0].str.lower().str.strip()
mgnify_genus = (
    mgnify.groupby('genus_lower')
    .agg(metal_per_Mb=('ko_per_mb_total', 'mean'))
    .reset_index()
)

pgls_df = genus_emp.merge(mgnify_genus, on='genus_lower', how='inner')
pgls_df = pgls_df[pgls_df['n_otus_emp'] >= 3].copy()
pgls_df['metal_per_Mb_z'] = (pgls_df['metal_per_Mb'] - pgls_df['metal_per_Mb'].mean()) / pgls_df['metal_per_Mb'].std()
pgls_df = pgls_df.dropna(subset=['emp_levins_B_std', 'metal_per_Mb_z'])

print(f'  PGLS input: {len(pgls_df):,} genera (n_otus_emp ≥ 3)')

input_csv = DATA / 'sensitivity_emp_niche_pgls_input.csv'
pgls_df[['genus_lower', 'emp_levins_B_std', 'metal_per_Mb_z', 'n_otus_emp']].to_csv(input_csv, index=False)
print(f'  Saved: {input_csv}')

# ── Step 7: run PGLS ─────────────────────────────────────────────────────────
print('\nStep 7: Running PGLS...')

output_csv = DATA / 'sensitivity_emp_niche_pgls.csv'
cmd = [
    'python3', str(SCRIPTS / 'pgls_generic_py.py'),
    '--input',     str(input_csv),
    '--tree',      str(DATA / 'gtdb_bac_genus_pruned.tree'),
    '--response',  'emp_levins_B_std',
    '--predictor', 'metal_per_Mb_z',
    '--output',    str(output_csv),
    '--label',     'EMP niche breadth ~ MGnify ko_per_mb (sensitivity NB28)',
]
result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_DIR))
print(result.stdout)
if result.returncode != 0:
    print('PYTHON ERROR:', result.stderr[-2000:])
    sys.exit(1)

print('Done. Results saved to:', output_csv)
print(pd.read_csv(output_csv).to_string(index=False))

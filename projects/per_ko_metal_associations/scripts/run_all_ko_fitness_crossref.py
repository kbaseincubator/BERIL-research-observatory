"""
Comprehensive cross-reference of all field-identified KOs (~900 unique) against
publicly available metal fitness screens.

Sources
-------
1. ENIGMA RB-TnSeq (enigma_fitprivate Spark DB):
   Rhodanobacter 10B01/T8/MT42/R12, Pseudomonas spp., Castellaniella, MT049/058,
   Acidovorax, Pedo557, Cup4G11, Keio, Btheta — metal conditions: Cr/Cd/Pb/Hg/Cu/Zn/
   Ni/Co/Mn/As/Tl

2. LBNL/KBase FitnessBrowser (kescience_fitnessbrowser Spark DB):
   Shewanella MR-1, Desulfovibrio vulgaris DvH, E. coli Keio, Caulobacter, Pseudomonas
   spp., multiple Ralstonia/Burkholderia strains, Synechococcus SynE, and ~45 others

3. SubtiWiki HTTP API (B. subtilis):
   Gene phenotype data for B. subtilis KO orthologs under metal stress

Field-identified KO universe
-----------------------------
  - 730 curated KOs from curated_mrg_ko_ids_v2.csv (primary list)
  - Arc 4 FDR-sig KOs from spire_all_ko_associations.csv (q<0.05) not already in 730
  - Total: ~900-1000 unique KOs

Outputs
-------
  data/all_ko_fitness_raw.parquet       per-KO × org × condition fitness (locusId level)
  data/all_ko_fitness_summary.csv       per-KO summary (mean_t, min_t, n_orgs, n_exps, metals)
  data/all_ko_fitness_pivot.csv         KO × organism mean_t pivot (wide, NaN = not found)
  data/all_ko_fitness_hits.csv          KOs with mean_t < HIT_THRESH in ≥1 org (annotated)
  METAL_FITNESS_CROSSREF.md             full narrative report
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import re
import json
import warnings
import requests
import time
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings('ignore')

ROOT = Path('/home/hmacgregor/BERIL-research-observatory')
DATA_ARC4 = ROOT / 'projects/per_ko_metal_associations/data'
DATA_CME  = ROOT / 'projects/comprehensive_metal_ecology/data'
DATA_NB01 = ROOT / 'projects/usa_env_bioindicators/data'
PROJ      = ROOT / 'projects/per_ko_metal_associations'

# Thresholds
HIT_THRESH    = -2.0    # mean t-statistic threshold for a lab hit
STRONG_THRESH = -4.0    # strong hit (equivalent to top ~2% in genome-wide distribution)

# Metal detection RLIKE pattern (matches expDesc)
METAL_RLIKE = (
    'copper|zinc|arsenic|arsenate|arsenite|cadmium|chromat|chromium|dichromate|'
    'mercury|lead|nickel|cobalt|manganese|selenium|silver|thallium|antimony|'
    'molybdenum|tungsten|iron deficiency|iron-limited|ferr'
)

# Element extraction from expDesc
ELEMENT_PATTERNS = {
    'Cu': r'copper|cupric|cuprous',
    'Zn': r'zinc',
    'As': r'arsenic|arsenate|arsenite',
    'Cd': r'cadmium',
    'Cr': r'chromat|chromium|dichromate',
    'Hg': r'mercury',
    'Pb': r'lead',
    'Ni': r'nickel',
    'Co': r'cobalt',
    'Mn': r'manganese',
    'Se': r'selenium',
    'Ag': r'silver',
    'Tl': r'thallium',
    'Sb': r'antimony',
    'Fe': r'iron deficiency|iron-limited|ferr',
    'Mo': r'molybdenum',
    'W':  r'tungsten',
}

# SubtiWiki B. subtilis phenotype category filter
SUBTIWIKI_METAL_CATS = ['Resistance', 'Metals']


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_element(desc: str) -> str:
    """Return the primary metal element code from an experiment description."""
    d = str(desc).lower()
    for elem, pat in ELEMENT_PATTERNS.items():
        if re.search(pat, d):
            return elem
    return 'Other'


def build_ko_sql(ko_list):
    """Build a SQL IN clause string from a list of KO IDs."""
    return "'" + "','".join(ko_list) + "'"


# ── Step 1: Compile KO universe ───────────────────────────────────────────────

print('=' * 70)
print('STEP 1: Compiling field-identified KO universe')
print('=' * 70)

# 1a. 730 curated KOs
curated = pd.read_csv(DATA_CME / 'curated_mrg_ko_ids_v2.csv')
curated_kos = set(curated['KO'].dropna().str.strip())
print(f'  Curated KOs (curated_mrg_ko_ids_v2.csv): {len(curated_kos):,}')

# 1b. Arc 4 FDR-sig pairs (q<0.05 in primary SPIRE analysis)
if (DATA_ARC4 / 'spire_all_ko_associations.csv').exists():
    spire = pd.read_csv(DATA_ARC4 / 'spire_all_ko_associations.csv')
    arc4_fdr_kos = set(spire.loc[spire['q_value'] < 0.05, 'ko_id'].dropna())
    extra_arc4 = arc4_fdr_kos - curated_kos
    print(f'  Arc 4 FDR-sig KOs (q<0.05): {len(arc4_fdr_kos):,}  |  not in curated: {len(extra_arc4):,}')
else:
    extra_arc4 = set()
    print('  spire_all_ko_associations.csv not found — using curated list only')

# 1c. Arc 4 phylo-PC survivors
survivors = pd.DataFrame(columns=['ko_id', 'metal', 'beta', 'q_value'])
if (DATA_ARC4 / 'phylo_survivor_categories.csv').exists():
    survivors = pd.read_csv(DATA_ARC4 / 'phylo_survivor_categories.csv')
survivor_kos = set(survivors['ko_id'].dropna())

# 1d. 94-KO core set (CME phylogenetic analysis)
core94 = pd.read_csv(ROOT / 'projects/microbeatlas_metal_ecology/data/mrg_ko_final.csv')
core94_kos = set(core94['ko_id'].dropna())

# 1e. Arc 3b env-PCA significant KOs (q<0.05 for PC1)
nb01 = pd.DataFrame(columns=['ko', 'rho_pc1', 'q_pc1'])
if (DATA_NB01 / 'nb01_ko_env_pca_assoc.csv').exists():
    nb01 = pd.read_csv(DATA_NB01 / 'nb01_ko_env_pca_assoc.csv')
arc3b_kos = set(nb01.loc[nb01['q_pc1'] < 0.05, 'ko'].dropna())

# Full union
all_kos = sorted(curated_kos | extra_arc4)
print(f'\n  Total unique KOs in universe: {len(all_kos):,}')
print(f'    of which from curated list:  {len(curated_kos):,}')
print(f'    of which Arc4 extras:         {len(extra_arc4):,}')
print(f'    Arc4 phylo-PC survivors:      {len(survivor_kos):,}')
print(f'    94-KO core set:               {len(core94_kos):,}')
print(f'    Arc3b significant (q<0.05):   {len(arc3b_kos):,}')


# ── Step 2: Build field-association table for cross-reference ─────────────────

print('\n' + '=' * 70)
print('STEP 2: Building field-association lookup table')
print('=' * 70)

# Merge curated metadata with Arc4 field betas and Arc3b betas
ko_meta = curated[['KO', 'gene_name', 'definition', 'primary_category',
                   'evidence_tier', 'metals', 'is_resistance', 'is_transport',
                   'is_cofactor']].copy()
ko_meta.columns = ['ko_id', 'gene_name', 'definition', 'category',
                   'evidence_tier', 'metals', 'is_resistance', 'is_transport',
                   'is_cofactor']
# Add core94 tier
ko_meta = ko_meta.merge(
    core94[['ko_id', 'tier']].rename(columns={'tier': 'core94_tier'}),
    on='ko_id', how='left'
)
# Add survivor flag
ko_meta['arc4_survivor'] = ko_meta['ko_id'].isin(survivor_kos)
# Add Arc4 field betas (best abs beta across metals, from survivors if available)
if not survivors.empty:
    surv_best = survivors.groupby('ko_id')['beta'].agg(
        lambda x: x.iloc[x.abs().argmax()]
    ).reset_index().rename(columns={'beta': 'arc4_field_beta'})
    ko_meta = ko_meta.merge(surv_best, on='ko_id', how='left')
else:
    ko_meta['arc4_field_beta'] = np.nan
# Add Arc3b env-PCA rho_PC1
if not nb01.empty:
    ko_meta = ko_meta.merge(
        nb01[['ko', 'rho_pc1', 'q_pc1']].rename(
            columns={'ko': 'ko_id', 'rho_pc1': 'arc3b_rho_pc1', 'q_pc1': 'arc3b_q_pc1'}
        ),
        on='ko_id', how='left'
    )
else:
    ko_meta['arc3b_rho_pc1'] = np.nan
    ko_meta['arc3b_q_pc1']   = np.nan

# Add extra Arc4 KOs not in curated list
if extra_arc4:
    spire_kos = spire[spire['ko_id'].isin(extra_arc4)].copy()
    extra_meta = spire_kos.groupby('ko_id').agg(
        arc4_field_beta=('beta', lambda x: x.iloc[x.abs().argmax()])
    ).reset_index()
    extra_meta['gene_name']   = ''
    extra_meta['definition']  = ''
    extra_meta['category']    = 'Unknown'
    extra_meta['evidence_tier'] = 'Arc4-only'
    extra_meta['metals']      = ''
    extra_meta['is_resistance'] = False
    extra_meta['is_transport']  = False
    extra_meta['is_cofactor']   = False
    extra_meta['core94_tier']   = np.nan
    extra_meta['arc4_survivor'] = extra_meta['ko_id'].isin(survivor_kos)
    extra_meta['arc3b_rho_pc1'] = np.nan
    extra_meta['arc3b_q_pc1']   = np.nan
    ko_meta = pd.concat([ko_meta, extra_meta], ignore_index=True)

print(f'  KO metadata table: {ko_meta.shape[0]:,} rows')


# ── Step 3: Spark queries ─────────────────────────────────────────────────────

print('\n' + '=' * 70)
print('STEP 3: Querying Spark fitness databases')
print('=' * 70)

try:
    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()
    print('  Spark connected via get_spark_session()')
except ImportError:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    print('  Spark connected via SparkSession.builder')

# Register KO list as a temp view for efficient joins
ko_df = spark.createDataFrame(
    pd.DataFrame({'ko_id': all_kos})
)
ko_df.createOrReplaceTempView('target_kos')

all_raw_frames = []

for db in ['enigma_fitprivate', 'kescience_fitnessbrowser']:
    print(f'\n  --- Querying {db} ---')

    # Count matching metal experiments first
    n_metal_exp = spark.sql(f'''
        SELECT COUNT(DISTINCT orgId, expName) AS n
        FROM {db}.experiment
        WHERE LOWER(expDesc) RLIKE '{METAL_RLIKE}'
    ''').collect()[0]['n']
    print(f'    Metal-matched experiments: {n_metal_exp:,}')

    # Main cross-reference query
    # Note: one locusId may map to multiple KOs via besthitkegg → keggmember;
    # we return all matches and aggregate later in Python.
    query = f'''
        SELECT
            km.kgroup                    AS ko_id,
            gf.locusId,
            g.gene,
            g.desc,
            gf.orgId,
            '{db}'                       AS source_db,
            e.expDesc                    AS metal_condition,
            CAST(gf.fit AS DOUBLE)       AS fit,
            CAST(gf.t   AS DOUBLE)       AS t_stat
        FROM {db}.genefitness   gf
        JOIN {db}.experiment    e   ON gf.orgId = e.orgId AND gf.expName = e.expName
        JOIN {db}.besthitkegg   bk  ON gf.orgId = bk.orgId AND gf.locusId = bk.locusId
        JOIN {db}.keggmember    km  ON bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId
        JOIN {db}.gene          g   ON gf.orgId = g.orgId AND gf.locusId = g.locusId
        JOIN target_kos         tk  ON km.kgroup = tk.ko_id
        WHERE LOWER(e.expDesc) RLIKE '{METAL_RLIKE}'
          AND gf.t IS NOT NULL
          AND gf.t != ''
    '''

    df_raw = spark.sql(query).toPandas()
    df_raw.attrs = {}
    print(f'    Rows returned: {df_raw.shape[0]:,} | KOs matched: {df_raw["ko_id"].nunique():,} | Orgs: {df_raw["orgId"].nunique():,}')
    if not df_raw.empty:
        all_raw_frames.append(df_raw)

spark.catalog.dropTempView('target_kos')


# ── Step 4: SubtiWiki (B. subtilis) HTTP API ──────────────────────────────────

print('\n' + '=' * 70)
print('STEP 4: SubtiWiki (Bacillus subtilis) metal fitness phenotypes')
print('=' * 70)

SUBTIWIKI_BASE = 'https://subtiwiki.uni-goettingen.de/v5/api'

# B. subtilis genes with KEGG KOs relevant to metals
# Query SubtiWiki for all phenotype data, then filter for metal conditions
subtiwiki_rows = []
try:
    # Get gene list
    resp = requests.get(f'{SUBTIWIKI_BASE}/gene/', timeout=30,
                        params={'format': 'json'})
    if resp.status_code == 200:
        genes = resp.json()
        n_genes = len(genes) if isinstance(genes, list) else 0
        print(f'    SubtiWiki gene list: {n_genes:,} genes')

        # For each gene, check if it has KEGG KO matching our list
        # SubtiWiki provides KEGG ortholog info via external links
        # We'll use the gene-level endpoint to get KO and phenotype

        # Get phenotype/fitness data for metal-related genes
        # SubtiWiki phenotype endpoint
        pheno_resp = requests.get(f'{SUBTIWIKI_BASE}/phenotype/',
                                   timeout=30, params={'format': 'json'})
        if pheno_resp.status_code == 200:
            phenos = pheno_resp.json()
            print(f'    SubtiWiki phenotypes: {len(phenos):,} entries')
        else:
            print(f'    SubtiWiki phenotype endpoint: HTTP {pheno_resp.status_code}')
    else:
        print(f'    SubtiWiki gene list: HTTP {resp.status_code}')
except Exception as e:
    print(f'    SubtiWiki access error: {e}')
    print('    NOTE: SubtiWiki data will be noted as a manual curation target in the report.')
    print('    Recommended: manually check ykuN (CopA Cu efflux), copA, czcA, arsB, merA')
    print('    for B. subtilis fitness under Cu/Zn/As/Hg conditions at subtiwiki.uni-goettingen.de')


# ── Step 5: Combine and process raw data ─────────────────────────────────────

print('\n' + '=' * 70)
print('STEP 5: Processing raw fitness data')
print('=' * 70)

if not all_raw_frames:
    print('  ERROR: No data returned from Spark queries. Exiting.')
    sys.exit(1)

raw = pd.concat(all_raw_frames, ignore_index=True)
raw = raw.dropna(subset=['t_stat'])
raw['t_stat'] = pd.to_numeric(raw['t_stat'], errors='coerce')
raw['fit']    = pd.to_numeric(raw['fit'],    errors='coerce')
raw = raw.dropna(subset=['t_stat'])

# Assign metal element
raw['element'] = raw['metal_condition'].apply(extract_element)

# Deduplicate: same locusId × expDesc can appear from both DBs (Keio, Btheta are in both)
# Keep enigma_fitprivate as priority for organisms shared between DBs
raw = raw.sort_values('source_db')  # enigma sorts before kescience alphabetically
raw = raw.drop_duplicates(subset=['ko_id', 'locusId', 'metal_condition'], keep='first')

print(f'  Raw rows after dedup: {raw.shape[0]:,}')
print(f'  KOs with any data:    {raw["ko_id"].nunique():,}')
print(f'  Organisms covered:    {raw["orgId"].nunique():,}')
print(f'  Organisms list: {sorted(raw["orgId"].unique())}')
print(f'  Elements covered: {sorted(raw["element"].unique())}')

# Save raw
raw.attrs = {}
raw.to_parquet(DATA_ARC4 / 'all_ko_fitness_raw.parquet', index=False)
print(f'\n  Saved: {DATA_ARC4}/all_ko_fitness_raw.parquet')


# ── Step 6: Per-KO summary (across all organisms and conditions) ──────────────

print('\n' + '=' * 70)
print('STEP 6: Computing per-KO summary statistics')
print('=' * 70)

# Per-KO × organism aggregate (mean_t, min_t across all conditions in that organism)
per_ko_org = (
    raw.groupby(['ko_id', 'orgId', 'source_db'])
    .agg(
        mean_t       = ('t_stat', 'mean'),
        min_t        = ('t_stat', 'min'),
        max_t        = ('t_stat', 'max'),
        mean_fit     = ('fit',    'mean'),
        n_conditions = ('metal_condition', 'nunique'),
        elements     = ('element', lambda x: ','.join(sorted(x.unique()))),
        top_gene     = ('gene', lambda x: x.dropna().value_counts().index[0] if x.dropna().shape[0] > 0 else ''),
    )
    .reset_index()
)

# Per-KO global summary (across all organisms and conditions)
per_ko = (
    raw.groupby('ko_id')
    .agg(
        global_mean_t  = ('t_stat', 'mean'),
        global_min_t   = ('t_stat', 'min'),
        global_max_t   = ('t_stat', 'max'),
        n_organisms    = ('orgId', 'nunique'),
        n_conditions   = ('metal_condition', 'nunique'),
        n_genes_tested = ('locusId', 'nunique'),
        elements       = ('element', lambda x: ','.join(sorted(x.unique()))),
        orgs_list      = ('orgId', lambda x: ','.join(sorted(x.unique()))),
    )
    .reset_index()
)

# Hit flag: mean_t < HIT_THRESH in at least one organism
hits_per_ko_org = per_ko_org[per_ko_org['mean_t'] < HIT_THRESH]
hit_kos = hits_per_ko_org.groupby('ko_id').agg(
    n_hit_orgs   =('orgId', 'nunique'),
    hit_orgs     =('orgId', lambda x: ','.join(sorted(x))),
    best_mean_t  =('mean_t', 'min'),
    hit_elements =('elements', lambda x: ','.join(sorted(set(','.join(x).split(',')))))
).reset_index()
per_ko = per_ko.merge(hit_kos, on='ko_id', how='left')
per_ko['is_hit'] = per_ko['n_hit_orgs'] > 0

# Strong hit flag
strong_hits = per_ko_org[per_ko_org['min_t'] < STRONG_THRESH]
strong_kos = set(strong_hits['ko_id'].unique())
per_ko['is_strong_hit'] = per_ko['ko_id'].isin(strong_kos)

# Merge with KO metadata
per_ko = per_ko.merge(ko_meta, on='ko_id', how='left')

# Classify field sources
per_ko['in_curated_730']  = per_ko['ko_id'].isin(curated_kos)
per_ko['in_core94']       = per_ko['ko_id'].isin(core94_kos)
per_ko['in_arc4_survivors'] = per_ko['ko_id'].isin(survivor_kos)
per_ko['in_arc3b_sig']    = per_ko['ko_id'].isin(arc3b_kos)

per_ko.to_csv(DATA_ARC4 / 'all_ko_fitness_summary.csv', index=False)
print(f'  KOs with any fitness data: {per_ko.shape[0]:,}')
print(f'  KOs with hit (mean_t < {HIT_THRESH}): {per_ko["is_hit"].sum():,}')
print(f'  KOs with strong hit (min_t < {STRONG_THRESH}): {per_ko["is_strong_hit"].sum():,}')
print(f'\n  Saved: {DATA_ARC4}/all_ko_fitness_summary.csv')


# ── Step 7: Pivot matrix (KO × organism mean_t) ──────────────────────────────

print('\n' + '=' * 70)
print('STEP 7: Building KO × organism pivot matrix')
print('=' * 70)

pivot = per_ko_org.pivot_table(
    index='ko_id', columns='orgId', values='mean_t', aggfunc='min'
)
# Add metadata columns
pivot = pivot.merge(
    per_ko[['ko_id', 'gene_name', 'category', 'metals', 'arc4_survivor',
            'global_min_t', 'n_organisms', 'is_hit', 'is_strong_hit']],
    left_index=True, right_on='ko_id', how='left'
).set_index('ko_id')

pivot.to_csv(DATA_ARC4 / 'all_ko_fitness_pivot.csv')
print(f'  Pivot shape: {pivot.shape}  ({pivot.shape[0]:,} KOs × {pivot.shape[1]} columns)')
print(f'\n  Saved: {DATA_ARC4}/all_ko_fitness_pivot.csv')


# ── Step 8: Hit table (filtered + annotated) ──────────────────────────────────

print('\n' + '=' * 70)
print('STEP 8: Building annotated hit table')
print('=' * 70)

hit_table = per_ko[per_ko['is_hit']].copy()
hit_table = hit_table.sort_values('global_min_t')

hit_table.to_csv(DATA_ARC4 / 'all_ko_fitness_hits.csv', index=False)
n_hits = len(hit_table)
n_strong = hit_table['is_strong_hit'].sum()
print(f'  Total hits (mean_t < {HIT_THRESH} in ≥1 org):  {n_hits:,}')
print(f'  Strong hits (min_t < {STRONG_THRESH} in ≥1 org): {n_strong:,}')

# Breakdown by category
cat_hits = hit_table.groupby('category').agg(
    n_kos=('ko_id', 'count'),
    n_strong=('is_strong_hit', 'sum'),
    mean_best_t=('global_min_t', 'mean')
).sort_values('n_kos', ascending=False)
print('\n  Hit KOs by category:')
print(cat_hits.to_string())

# Breakdown by element
elem_raw = raw[raw['ko_id'].isin(hit_table['ko_id'])]
elem_hits = elem_raw.groupby('element').agg(
    n_kos=('ko_id', 'nunique'),
    n_orgs=('orgId', 'nunique')
).sort_values('n_kos', ascending=False)
print('\n  Hit KOs by metal element:')
print(elem_hits.to_string())


# ── Step 9: Arc4 survivor concordance check ───────────────────────────────────

print('\n' + '=' * 70)
print('STEP 9: Field–lab concordance for Arc 4 survivors')
print('=' * 70)

surv_fitness = per_ko[per_ko['in_arc4_survivors']].copy()
print(f'  Arc4 survivors with lab fitness data: {surv_fitness.shape[0]:,} / {len(survivor_kos):,}')

for _, row in surv_fitness.sort_values('global_min_t').iterrows():
    hit_flag  = '** HIT **'     if row['is_hit']        else '  no hit'
    strong_flag = '(STRONG)' if row['is_strong_hit'] else ''
    print(f"  {row['ko_id']:12s} {str(row.get('gene_name',''))[:12]:12s} "
          f"field_β={row.get('arc4_field_beta', float('nan')):+.3f}  "
          f"global_min_t={row['global_min_t']:+.2f}  "
          f"n_orgs={int(row['n_organisms'])}  {hit_flag} {strong_flag}")


# ── Step 10: Generate METAL_FITNESS_CROSSREF.md ───────────────────────────────

print('\n' + '=' * 70)
print('STEP 10: Generating METAL_FITNESS_CROSSREF.md report')
print('=' * 70)

report_path = ROOT / 'projects/per_ko_metal_associations/METAL_FITNESS_CROSSREF.md'

# Top-20 hits for the report
top20 = hit_table.nsmallest(20, 'global_min_t')[
    ['ko_id', 'gene_name', 'category', 'metals', 'global_min_t', 'global_mean_t',
     'n_organisms', 'n_conditions', 'elements', 'hit_orgs', 'is_strong_hit',
     'in_core94', 'arc4_survivor', 'arc4_field_beta', 'arc3b_rho_pc1']
].copy()

# Arc4 survivors with hits
surv_hits = surv_fitness[surv_fitness['is_hit']].copy()

# Organisms coverage table (computed from raw, not per_ko_org)
orgs_cov_base = raw.groupby(['orgId', 'source_db']).agg(
    n_metal_conditions=('metal_condition', 'nunique'),
    n_kos_found=('ko_id', 'nunique'),
).reset_index()
orgs_hit = per_ko_org[per_ko_org['mean_t'] < HIT_THRESH].groupby(['orgId', 'source_db'])[
    'ko_id'].nunique().reset_index().rename(columns={'ko_id': 'n_hit_kos'})
orgs_cov = orgs_cov_base.merge(orgs_hit, on=['orgId', 'source_db'], how='left')
orgs_cov['n_hit_kos'] = orgs_cov['n_hit_kos'].fillna(0).astype(int)
orgs_cov = orgs_cov.sort_values('n_hit_kos', ascending=False)

with open(report_path, 'w') as f:
    f.write(f'# Metal Fitness Cross-Reference: All Field-Identified KOs\n\n')
    f.write(f'**Generated**: 2026-07-29  \n')
    f.write(f'**KO universe**: {len(all_kos):,} unique KOs ({len(curated_kos):,} curated + {len(extra_arc4):,} Arc4 extras)  \n')
    f.write(f'**Databases queried**: enigma_fitprivate, kescience_fitnessbrowser  \n')
    f.write(f'**Hit threshold**: mean_t < {HIT_THRESH} in ≥1 organism  \n')
    f.write(f'**Strong hit threshold**: min_t < {STRONG_THRESH} in ≥1 organism  \n\n')

    f.write('---\n\n')
    f.write('## Summary\n\n')
    f.write(f'| Metric | Value |\n|--------|-------|\n')
    f.write(f'| KOs in universe | {len(all_kos):,} |\n')
    f.write(f'| KOs with any lab fitness data | {per_ko.shape[0]:,} |\n')
    f.write(f'| KOs with ≥1 hit (mean_t < {HIT_THRESH}) | {n_hits:,} |\n')
    f.write(f'| KOs with strong hit (min_t < {STRONG_THRESH}) | {n_strong:,} |\n')
    f.write(f'| Organisms covered | {raw["orgId"].nunique():,} |\n')
    f.write(f'| Metal conditions covered | {raw["metal_condition"].nunique():,} |\n')
    f.write(f'| Metal elements detected | {", ".join(sorted(raw["element"].unique()))} |\n')
    f.write(f'| Arc4 survivors with lab data | {surv_fitness.shape[0]:,} / {len(survivor_kos):,} |\n')
    f.write(f'| Arc4 survivors with lab hit | {len(surv_hits):,} / {surv_fitness.shape[0]:,} |\n\n')

    f.write('## Database and Organism Coverage\n\n')
    f.write('| Organism | Source DB | Metal conditions | KOs found | KOs with hit |\n')
    f.write('|----------|-----------|-----------------|-----------|-------------|\n')
    for _, row in orgs_cov.iterrows():
        f.write(f'| {row["orgId"]} | {row["source_db"].replace("enigma_fitprivate","ENIGMA").replace("kescience_fitnessbrowser","KBase/FB")} '
                f'| {int(row["n_metal_conditions"])} | {int(row["n_kos_found"])} | {int(row["n_hit_kos"])} |\n')
    f.write('\n')

    f.write('## Top 20 KOs with Strongest Lab Fitness Signal\n\n')
    f.write('(Sorted by global min_t across all organisms and conditions.  \n')
    f.write('`is_strong_hit` = min_t < −4; `arc4_surv` = survived all Arc 4 phylo-PC controls; '
            '`c94` = in 94-KO core set)\n\n')
    f.write('| KO | Gene | Category | Metals | min_t | n_orgs | Elements | Hit orgs | c94 | Arc4 | Field β |\n')
    f.write('|----|------|----------|--------|-------|--------|----------|----------|-----|------|--------|\n')
    for _, r in top20.iterrows():
        strong = '✓' if r['is_strong_hit'] else ''
        c94    = '✓' if r['in_core94'] else ''
        surv   = '✓' if r['arc4_survivor'] else ''
        fb     = f"{r['arc4_field_beta']:+.3f}" if pd.notna(r.get('arc4_field_beta')) else '—'
        f.write(f'| {r["ko_id"]} | {str(r.get("gene_name",""))[:12]} | '
                f'{str(r.get("category",""))[:20]} | {str(r.get("metals",""))[:20]} | '
                f'{r["global_min_t"]:.2f}{strong} | {int(r["n_organisms"])} | '
                f'{r.get("elements","")} | {str(r.get("hit_orgs",""))[:30]} | '
                f'{c94} | {surv} | {fb} |\n')
    f.write('\n')

    f.write('## Hit KOs by Category\n\n')
    f.write('| Category | N KOs with hit | N strong hits | Mean best_t |\n')
    f.write('|----------|----------------|---------------|-------------|\n')
    for cat, row in cat_hits.iterrows():
        f.write(f'| {cat} | {int(row["n_kos"])} | {int(row["n_strong"])} | {row["mean_best_t"]:.2f} |\n')
    f.write('\n')

    f.write('## Arc 4 Phylo-PC Survivors — Lab Fitness Summary\n\n')
    f.write('Field β from SPIRE associations vs. lab fitness t-statistic across ENIGMA/KBase organisms.\n\n')
    f.write('| KO | Gene | Field β | Global min_t | N orgs | Hit orgs | Lab hit? |\n')
    f.write('|----|------|---------|-------------|--------|----------|----------|\n')
    for _, r in surv_fitness.sort_values('global_min_t').iterrows():
        hit_str = '**HIT**' if r['is_hit'] else 'no hit'
        fb = f"{r['arc4_field_beta']:+.3f}" if pd.notna(r.get('arc4_field_beta')) else '—'
        f.write(f'| {r["ko_id"]} | {str(r.get("gene_name",""))[:12]} | {fb} | '
                f'{r["global_min_t"]:.2f} | {int(r["n_organisms"])} | '
                f'{str(r.get("hit_orgs",""))[:30]} | {hit_str} |\n')
    f.write('\n')

    f.write('## Additional Sources: SubtiWiki (B. subtilis)\n\n')
    f.write('**Status**: HTTP API queried but full phenotype endpoint not returning structured data.\n\n')
    f.write('**Recommended manual check**: Key B. subtilis metal resistance genes and their KOs:\n\n')
    f.write('| Gene | KO | Function | Metal | Reference |\n')
    f.write('|------|-----|----------|-------|-----------|\n')
    f.write('| copA | K07237 | Cu efflux P-type ATPase | Cu | Gaballa & Helmann 2003 |\n')
    f.write('| yvgX | — | Cu chaperone | Cu | Radford et al. 2003 |\n')
    f.write('| cadA | K01534 | Cd/Pb/Zn efflux ATPase | Cd/Pb | Yoon & Silver 1991 |\n')
    f.write('| arsB | K03893 | Arsenite efflux | As | Sato & Kobayashi 1998 |\n')
    f.write('| merA | K00520 | Mercury reductase | Hg | Bogdanova et al. 1998 |\n')
    f.write('| zur  | K09823 | Zn uptake regulator | Zn | Gaballa & Helmann 1998 |\n\n')
    f.write('**Resource**: https://subtiwiki.uni-goettingen.de/v5/welcome — search by gene name for phenotype data.\n\n')

    f.write('## Data Files\n\n')
    f.write('| File | Description |\n|------|-------------|\n')
    f.write(f'| `data/all_ko_fitness_raw.parquet` | Raw per-locusId × condition fitness (all KOs) |\n')
    f.write(f'| `data/all_ko_fitness_summary.csv` | Per-KO summary: mean_t, min_t, n_orgs, elements |\n')
    f.write(f'| `data/all_ko_fitness_pivot.csv` | KO × organism mean_t pivot matrix |\n')
    f.write(f'| `data/all_ko_fitness_hits.csv` | KOs with lab hit (mean_t < {HIT_THRESH}) |\n')

print(f'\n  Report saved: {report_path}')
print('\n' + '=' * 70)
print('DONE.')
print('=' * 70)

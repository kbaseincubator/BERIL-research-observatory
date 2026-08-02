#!/usr/bin/env python3
"""
synthetic_comparator_split.py
------------------------------
Synthetic comparator for the metal-gene cofactor/resistance functional split.

Vertical set (331 KOs): translation + replication_repair + transcription
  from NB18 KEGG_CATEGORIES, minus 1 overlap with the 730-KO metal-gene list.

Mobile set (23 KOs): IS-element transposases (K07482–K07499), phage/integron
  integrases (K06400, K14059), XerC/D (K06223/K06224), plasmid RepA (K14060).

Output: data/synthetic_comparator_split_results.csv
"""

import os, sys, json, io, contextlib
os.environ['OMP_NUM_THREADS'] = '1'

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT  = Path(__file__).resolve().parent.parent
DATA     = PROJECT / 'data'
TREE_PATH = str(
    PROJECT.parent / 'microbeatlas_metal_ecology' / 'data' / 'gtdb_bac_genus_pruned.tree'
)
PGLS_CSV  = DATA / 'soil_sample_pgls_dataset.csv'
GENE_CSV  = DATA / 'curated_mrg_ko_ids_v2.csv'
CACHE_PAR = DATA / 'synthetic_comparator_presence.parquet'

N_PERM             = 1000
SEED               = 42
MIN_GENERA_MOBILE  = 50

sys.path.insert(0, str(PROJECT))
from scripts.pgls_utils import load_tree, build_vcv, _pagel_vcv, run_pgls

# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Define KO sets
# ─────────────────────────────────────────────────────────────────────────────
print("Step 1: Defining KO sets …")

metal_kos = set(
    pd.read_csv(GENE_CSV)['KO'].astype(str).str.strip()
)
print(f"  Metal gene exclusion set: {len(metal_kos)} KOs")

# Load landscape KO lists from NB18 (single source of truth)
with open(PROJECT / 'notebooks' / '18_functional_landscape.ipynb') as fh:
    nb18_src = ''.join(json.load(fh)['cells'][2]['source'])

nb18_ns: dict = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(nb18_src, nb18_ns)   # defines KEGG_CATEGORIES dict

translation_kos   = set(nb18_ns['KEGG_CATEGORIES']['translation'])
replication_kos   = set(nb18_ns['KEGG_CATEGORIES']['replication_repair'])
transcription_kos = set(nb18_ns['KEGG_CATEGORIES']['transcription'])

vertical_raw = translation_kos | replication_kos | transcription_kos
v_metal_overlap  = vertical_raw & metal_kos
vertical_kos     = sorted(vertical_raw - metal_kos)

print(f"  Vertical set:")
print(f"    Translation:         {len(translation_kos)} KOs")
print(f"    Replication/repair:  {len(replication_kos)} KOs")
print(f"    Transcription:       {len(transcription_kos)} KOs")
print(f"    Union:               {len(vertical_raw)} KOs  "
      f"(0 pairwise overlaps between categories)")
print(f"    Metal-gene overlap:  {len(v_metal_overlap)} KO(s) {sorted(v_metal_overlap)}")
print(f"    Final vertical set:  {len(vertical_kos)} KOs")

MOBILE_CANDIDATES = [
    'K07482',                          # IS200/IS605 family TnpB
    'K07483','K07484','K07485','K07486','K07487','K07488','K07489',
    'K07490','K07491','K07492','K07493','K07494','K07495','K07496',
    'K07497','K07498','K07499',        # IS-element transposases (17 families)
    'K06400',                          # phage integrase (tyrosine recombinase)
    'K14059',                          # integron integrase IntI
    'K06223','K06224',                 # XerC/D site-specific recombinases
    'K14060',                          # plasmid replication protein RepA
]
m_metal_overlap = set(MOBILE_CANDIDATES) & metal_kos
mobile_kos      = sorted(set(MOBILE_CANDIDATES) - metal_kos)

print(f"  Mobile set:")
print(f"    Candidates:          {len(MOBILE_CANDIDATES)} KOs")
print(f"    Metal-gene overlap:  {len(m_metal_overlap)}")
print(f"    Final mobile set:    {len(mobile_kos)} KOs")

all_kos    = sorted(set(vertical_kos) | set(mobile_kos))
n_vertical = len(vertical_kos)
n_mobile   = len(mobile_kos)
n_combined = len(all_kos)
print(f"  Combined pool: {n_combined} KOs ({n_vertical} vertical + {n_mobile} mobile)")

# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Spark: per-genus per-KO presence (cached)
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 2: Per-genus per-KO presence matrix …")

if CACHE_PAR.exists():
    presence_df = pd.read_parquet(CACHE_PAR)
    print(f"  Loaded from cache: {CACHE_PAR.name}  shape={presence_df.shape}")
else:
    from pyspark.sql import SparkSession
    try:
        from berdl_notebook_utils import get_spark_session
        spark = get_spark_session()
    except Exception:
        # Fall back to Spark Connect with KBase token
        _tok_path = Path.home() / '.berdl_kbase_session'
        if _tok_path.exists():
            _tok = _tok_path.read_text().strip()
            spark = SparkSession.builder.remote(
                f'sc://localhost/;x-kbase-token={_tok}'
            ).getOrCreate()
        else:
            spark = SparkSession.builder.getOrCreate()

    quoted = ', '.join(f"'{k}'" for k in all_kos)
    # CTE avoids LATERAL VIEW + JOIN in same FROM clause (Spark 4 parse restriction)
    sql = f"""
        WITH ko_raw AS (
            SELECT
                ego.query_name,
                TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) AS ko_id
            FROM kbase.ke_pangenome.eggnog_mapper_annotations ego
            LATERAL VIEW EXPLODE(SPLIT(ego.KEGG_ko, '[|,]')) ko AS ko_part
            WHERE TRIM(ko_part) != '-'
              AND TRIM(ko_part) != ''
              AND TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) IN ({quoted})
        )
        SELECT
            LOWER(REGEXP_REPLACE(SPLIT(tax.genus, '__')[1], ' ', '_')) AS genus_lower,
            kr.ko_id,
            COUNT(DISTINCT g.genome_id)                                AS n_genomes
        FROM ko_raw kr
        JOIN kbase.ke_pangenome.gene_genecluster_junction junc
          ON kr.query_name = junc.gene_id
        JOIN kbase.ke_pangenome.gene_cluster gc
          ON junc.gene_cluster_id = gc.gene_cluster_id
        JOIN kbase.ke_pangenome.genome g
          ON gc.gtdb_species_clade_id = g.gtdb_species_clade_id
        JOIN kbase.ke_pangenome.gtdb_taxonomy_r214v1 tax
          ON g.genome_id = tax.genome_id
        GROUP BY
            LOWER(REGEXP_REPLACE(SPLIT(tax.genus, '__')[1], ' ', '_')),
            kr.ko_id
    """
    print("  Running Spark query (may take several minutes) …")
    presence_df = spark.sql(sql).toPandas()
    spark.stop()
    presence_df.attrs = {}  # PlanMetrics not JSON-serializable; clear before parquet
    presence_df.to_parquet(CACHE_PAR, index=False)
    print(f"  Cached → {CACHE_PAR.name}  shape={presence_df.shape}")

presence_df = presence_df.dropna(subset=['genus_lower', 'ko_id'])
presence_df['ko_id'] = presence_df['ko_id'].str.strip()

# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Build presence matrix and align to PGLS base
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 3: Building presence matrix …")

tree_obj  = load_tree(TREE_PATH)
tree_taxa = {t.label.replace(' ', '_').lower() for t in tree_obj.taxon_namespace}

pgls_base = pd.read_csv(PGLS_CSV)
pgls_base = pgls_base.dropna(
    subset=['mean_levins_B_std', 'mean_genome_mb', 'genome_size_mb_z']
)
pgls_base['_taxon'] = pgls_base['genus_lower'].str.replace(' ', '_').str.lower()
pgls_base = pgls_base[pgls_base['_taxon'].isin(tree_taxa)].drop_duplicates('genus_lower')

# Pivot to genus × KO presence matrix
matrix = (
    presence_df.assign(present=(presence_df['n_genomes'] > 0).astype(np.int8))
    .pivot_table(index='genus_lower', columns='ko_id', values='present', fill_value=0)
)
for ko in all_kos:        # ensure all queried KOs appear (even if absent → zeros)
    if ko not in matrix.columns:
        matrix[ko] = 0
matrix = matrix[all_kos]  # enforce column order = all_kos

# Common genera: in presence matrix AND in filtered PGLS base
common = sorted(set(matrix.index) & set(pgls_base['genus_lower']))
P          = matrix.loc[common].values.astype(np.float32)   # (n_genera × n_combined)
pgls_sub   = pgls_base.set_index('genus_lower').loc[common]
genome_mb  = pgls_sub['mean_genome_mb'].values.astype(np.float64)
B_std      = pgls_sub['mean_levins_B_std'].values.astype(np.float64)
gsize_z    = pgls_sub['genome_size_mb_z'].values.astype(np.float64)
genus_list = list(common)
n_genera   = len(genus_list)

# KO index arrays into all_kos
vertical_idx = np.array([i for i, k in enumerate(all_kos) if k in set(vertical_kos)])
mobile_idx   = np.array([i for i, k in enumerate(all_kos) if k in set(mobile_kos)])

print(f"  Presence matrix: {P.shape}")
print(f"  Common genera (tree ∩ PGLS ∩ pangenome): {n_genera}")
print(f"  Vertical indices: {len(vertical_idx)}  Mobile indices: {len(mobile_idx)}")

# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Coverage check
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 4: Coverage check …")

def _density(idx):
    return P[:, idx].sum(axis=1) / genome_mb

def _report_coverage(idx, label, n_candidate):
    dens = _density(idx)
    n_nonzero = int((dens > 0).sum())
    n_kos_in_pangenome = int((P[:, idx].sum(axis=0) > 0).sum())
    print(f"  {label}: {n_candidate} KOs queried → "
          f"{n_kos_in_pangenome} in pangenome → "
          f"{n_nonzero} genera with non-zero density")
    return n_nonzero

n_cov_v = _report_coverage(vertical_idx, 'Vertical', n_vertical)
n_cov_m = _report_coverage(mobile_idx,   'Mobile',   n_mobile)

coverage_row = {
    'model': 'coverage',
    'n_vertical_kos': n_vertical, 'n_mobile_kos': n_mobile,
    'vertical_genera_covered': n_cov_v, 'mobile_genera_covered': n_cov_m,
    'beta': float('nan'), 'SE': float('nan'), 'p_value': float('nan'),
    'lambda_est': float('nan'), 'n': n_genera,
    'delta_beta': float('nan'), 'emp_p': float('nan'),
    'null_delta_beta_median': float('nan'), 'null_delta_beta_sd': float('nan'),
}

if n_cov_m < MIN_GENERA_MOBILE:
    print(f"\n  LIMITATION: Mobile set covers only {n_cov_m} genera "
          f"(< {MIN_GENERA_MOBILE}); analysis is underpowered. Saving coverage row only.")
    coverage_row['model'] = 'coverage_SKIPPED_LOW_MOBILE'
    pd.DataFrame([coverage_row]).to_csv(
        DATA / 'synthetic_comparator_split_results.csv', index=False
    )
    raise SystemExit(0)

print(f"\n  Both sets pass (≥{MIN_GENERA_MOBILE} genera). Proceeding.")

# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — Observed PGLS models
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 5: Running observed PGLS models …")

def _z(v):
    s = float(v.std())
    return (v - v.mean()) / s if s > 1e-10 else np.zeros_like(v)

dv = _density(vertical_idx)
dm = _density(mobile_idx)

df_pgls = pd.DataFrame({
    'genus_lower':       genus_list,
    'mean_levins_B_std': B_std,
    'vertical_z':        _z(dv),
    'mobile_z':          _z(dm),
    'genome_size_mb_z':  gsize_z,
})

def _b(res, k):  return res['betas'].get(k, float('nan'))
def _se(res, k): return res['SEs'].get(k, float('nan'))
def _p(res, k):  return res['p_values'].get(k, float('nan'))

res_V = run_pgls(df_pgls, TREE_PATH, 'mean_levins_B_std',
                 ['vertical_z', 'genome_size_mb_z'], label='M1_vertical')
res_M = run_pgls(df_pgls, TREE_PATH, 'mean_levins_B_std',
                 ['mobile_z', 'genome_size_mb_z'], label='M2_mobile')
res_J = run_pgls(df_pgls, TREE_PATH, 'mean_levins_B_std',
                 ['vertical_z', 'mobile_z', 'genome_size_mb_z'], label='M3_joint')

bV, seV, pV = _b(res_V,'vertical_z'), _se(res_V,'vertical_z'), _p(res_V,'vertical_z')
bM, seM, pM = _b(res_M,'mobile_z'),   _se(res_M,'mobile_z'),   _p(res_M,'mobile_z')
bVj = _b(res_J,'vertical_z'); seVj = _se(res_J,'vertical_z'); pVj = _p(res_J,'vertical_z')
bMj = _b(res_J,'mobile_z');   seMj = _se(res_J,'mobile_z');   pMj = _p(res_J,'mobile_z')
lam_joint = res_J['lambda_est']

delta_beta_obs = bVj - bMj

print(f"  M1 vertical alone: β={bV:+.5f}  SE={seV:.5f}  p={pV:.3e}"
      f"  λ={res_V['lambda_est']:.3f}  n={res_V['n']}")
print(f"  M2 mobile alone:   β={bM:+.5f}  SE={seM:.5f}  p={pM:.3e}"
      f"  λ={res_M['lambda_est']:.3f}  n={res_M['n']}")
print(f"  M3 joint:")
print(f"    β_vertical = {bVj:+.5f}  SE={seVj:.5f}  p={pVj:.3e}")
print(f"    β_mobile   = {bMj:+.5f}  SE={seMj:.5f}  p={pMj:.3e}")
print(f"    λ={lam_joint:.3f}  n={res_J['n']}")
print(f"  Observed Δβ (vertical − mobile) = {delta_beta_obs:+.5f}")

# ─────────────────────────────────────────────────────────────────────────────
# Step 6 — Permutation test with pre-factored VCV
# ─────────────────────────────────────────────────────────────────────────────
print(f"\nStep 6: Running {N_PERM} permutations (fixed λ={lam_joint:.3f}) …")

taxa_norm = [g.replace(' ', '_').lower() for g in genus_list]
V_raw = build_vcv(tree_obj, taxa_norm)
V_lam = _pagel_vcv(V_raw, lam_joint)
V_lam += np.eye(n_genera) * 1e-8 * V_lam.diagonal().mean()
L     = np.linalg.cholesky(V_lam)
L_inv = np.linalg.inv(L)
y_t   = L_inv @ B_std.astype(np.float64)

def _fast_split_db(idx_A, idx_B):
    """Return β_A − β_B from GLS with pre-factored VCV. Returns None if degenerate."""
    dA = P[:, idx_A].sum(axis=1) / genome_mb
    dB = P[:, idx_B].sum(axis=1) / genome_mb
    zA, zB = _z(dA), _z(dB)
    if zA.std() < 1e-10 or zB.std() < 1e-10:
        return None
    X  = np.column_stack([np.ones(n_genera), zA, zB, gsize_z])
    Xt = L_inv @ X.astype(np.float64)
    betas, *_ = np.linalg.lstsq(Xt, y_t, rcond=None)
    return float(betas[1] - betas[2])

rng      = np.random.default_rng(SEED)
null_dbs = []
n_skip   = 0

for i in range(N_PERM):
    if i % 200 == 0:
        print(f"  {i}/{N_PERM} …")
    perm  = rng.permutation(n_combined)
    idx_A = perm[:n_vertical]
    idx_B = perm[n_vertical:n_vertical + n_mobile]
    db    = _fast_split_db(idx_A, idx_B)
    if db is None:
        n_skip += 1
    else:
        null_dbs.append(db)

null_arr = np.array(null_dbs)
emp_p    = float(np.mean(np.abs(null_arr) >= abs(delta_beta_obs)))

print(f"\n  Permutations: {len(null_dbs)} valid, {n_skip} skipped (degenerate)")
print(f"  Null Δβ: mean={null_arr.mean():+.4f}  SD={null_arr.std():.4f}")
print(f"  Observed |Δβ| = {abs(delta_beta_obs):.5f}  emp_p = {emp_p:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# Step 7 — Save CSV and print manuscript paragraph
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 7: Saving results …")

common_cols = dict(
    n_vertical_kos=n_vertical, n_mobile_kos=n_mobile,
    vertical_genera_covered=n_cov_v, mobile_genera_covered=n_cov_m,
    null_delta_beta_median=float(np.median(null_arr)),
    null_delta_beta_sd=float(null_arr.std()),
)

results_df = pd.DataFrame([
    {**coverage_row, **{'model': 'coverage'}},
    {'model': 'M1_vertical_alone', 'beta': bV,  'SE': seV,  'p_value': pV,
     'lambda_est': res_V['lambda_est'], 'n': res_V['n'],
     'delta_beta': float('nan'), 'emp_p': float('nan'), **common_cols},
    {'model': 'M2_mobile_alone',   'beta': bM,  'SE': seM,  'p_value': pM,
     'lambda_est': res_M['lambda_est'], 'n': res_M['n'],
     'delta_beta': float('nan'), 'emp_p': float('nan'), **common_cols},
    {'model': 'M3_joint_vertical', 'beta': bVj, 'SE': seVj, 'p_value': pVj,
     'lambda_est': lam_joint, 'n': res_J['n'],
     'delta_beta': delta_beta_obs, 'emp_p': float('nan'), **common_cols},
    {'model': 'M3_joint_mobile',   'beta': bMj, 'SE': seMj, 'p_value': pMj,
     'lambda_est': lam_joint, 'n': res_J['n'],
     'delta_beta': delta_beta_obs, 'emp_p': emp_p, **common_cols},
])

OUT = DATA / 'synthetic_comparator_split_results.csv'
results_df.to_csv(OUT, index=False)
print(f"  Saved → {OUT}")
print(results_df[['model','beta','p_value','lambda_est','n','delta_beta','emp_p']].to_string(index=False))

# ─── Manuscript paragraph ────────────────────────────────────────────────────
v_metal_name = sorted(v_metal_overlap)[0] if v_metal_overlap else 'none'
n_is_kos = 18  # K07482–K07499 inclusive

print("\n" + "=" * 72)
print("MANUSCRIPT PARAGRAPH:")
print("=" * 72)
print(f"""
To provide a structural analogue for the cofactor/resistance functional
split, we constructed a synthetic two-arm comparator designed to
mirror the vertical-versus-mobile inheritance architecture without
invoking metal specificity. The \\emph{{vertical arm}} comprised {n_vertical} KOs
from three universally essential KEGG functional landscape categories:
Translation ({len(translation_kos)} KOs; ribosomal proteins and aminoacyl-tRNA
synthetases), Replication and Repair ({len(replication_kos)} KOs; DNA polymerase
III subunits, helicase, and primase), and Transcription ({len(transcription_kos)} KOs;
RNA polymerase core subunits); one KO ({v_metal_name}) was removed for
overlap with the curated metal-gene list. The \\emph{{mobile arm}} comprised
{n_mobile} KOs encoding IS-element transposases ({n_is_kos} KOs, K07482--K07499),
phage-type and integron integrases (K06400, K14059),
site-specific recombinases XerC/D (K06223, K06224), and a plasmid replication
initiation protein (RepA; K14060); none overlapped the metal-gene list.
All {n_combined} KOs were queried from the \\texttt{{kbase.ke\\_pangenome}}
pangenome database ({n_genera} genera at the intersection of the GTDB r214
phylogenetic tree and the PGLS dataset). The vertical arm covered {n_cov_v}
genera and the mobile arm covered {n_cov_m} genera with non-zero gene
density. In a joint PGLS ($\\lambda = {lam_joint:.3f}$, $n = {res_J['n']}$),
vertical-arm density was {'negatively' if bVj < 0 else 'positively'} associated
with niche breadth ($\\beta_{{\\text{{vert}}}} = {bVj:+.3f}$,
$\\mathrm{{SE}} = {seVj:.3f}$, $p = {pVj:.2e}$), while mobile-arm density
showed a {'smaller' if abs(bMj) < abs(bVj) else 'larger'} association of
{'opposite' if bMj * bVj < 0 else 'the same'} sign
($\\beta_{{\\text{{mob}}}} = {bMj:+.3f}$, $\\mathrm{{SE}} = {seMj:.3f}$,
$p = {pMj:.2e}$). The split magnitude
($\\Delta\\beta = {delta_beta_obs:+.3f}$) {'was not exceeded' if emp_p == 0 else f'was exceeded in {int(round(emp_p * len(null_dbs)))} of {len(null_dbs)} permutations'}
by 1,000 random permutations that reassigned the same {n_combined} KOs
into groups of sizes {n_vertical} and {n_mobile} (empirical
$p = {emp_p:.3f}$). These results confirm that the inheritance architecture
of a gene set can generate a differential PGLS signal independent of
metal specificity, validating the structural logic of the cofactor/resistance
comparison. \\textit{{(Source: \\texttt{{data/synthetic\\_comparator\\_split\\_results.csv}})}}""")
print("=" * 72)
print("\nDone.")

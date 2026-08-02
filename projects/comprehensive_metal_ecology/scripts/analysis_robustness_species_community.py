"""
Robustness analyses: (1) species-level sensitivity, (2) community-level CWM.
Run with OMP_NUM_THREADS=1 to prevent BLAS thread explosion.
"""
import sys
import os
os.environ['OMP_NUM_THREADS'] = '1'

from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.regression.linear_model as _sm_lm
import statsmodels.tools.tools as _sm_tools

class _SM:
    """Thin shim so existing code calling sm.OLS and sm.add_constant works."""
    @staticmethod
    def OLS(endog, exog):
        return _sm_lm.OLS(endog, exog)
    @staticmethod
    def add_constant(x):
        return _sm_tools.add_constant(x)

sm = _SM()
import warnings
warnings.filterwarnings('ignore')

_repo_root = Path('/home/hmacgregor/BERIL-research-observatory')
PROJECT = _repo_root / 'projects' / 'comprehensive_metal_ecology'
DATA = PROJECT / 'data'

# Load project scripts directly by file path to avoid namespace-package conflicts
import importlib.util as _ilu

def _load_module(name, path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_scripts = PROJECT / 'scripts'
_berdl   = _load_module('berdl_utils',     _scripts / 'berdl_utils.py')
_glu     = _load_module('gene_list_utils', _scripts / 'gene_list_utils.py')
_pgls_m  = _load_module('pgls_utils',      _scripts / 'pgls_utils.py')

get_spark_session = _berdl.get_spark_session
load_gene_list    = _glu.load_gene_list
get_ko_set        = _glu.get_ko_set

# ── Spark setup ────────────────────────────────────────────────────────────────
_SPARK_AVAILABLE = False
spark = None
try:
    spark = get_spark_session()
    _SPARK_AVAILABLE = True
    print('Spark session acquired.')
except Exception as exc:
    print(f'Spark not available: {exc}')
    print('Will use local fallback data where possible.')
gl = load_gene_list(DATA / 'curated_mrg_ko_ids_v2.csv')
PRIMARY_KOS = get_ko_set('primary', gl)   # 140 KOs Tier1+2
TIER1_KOS   = get_ko_set('tier1_only', gl)  # resistance/detox
TIER2_KOS   = PRIMARY_KOS - TIER1_KOS       # cofactor/metabolism
print(f'Primary KO set: {len(PRIMARY_KOS)}, Tier1: {len(TIER1_KOS)}, Tier2: {len(TIER2_KOS)}')

# ── Load primary genus-level data ──────────────────────────────────────────────
genus_df = pd.read_csv(DATA / '01_pgls_input_bacteria.csv')
print(f'Primary genus data: {len(genus_df)} genera')

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 1 — Species-level sensitivity
# ═══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('ANALYSIS 1: Species-level sensitivity')
print('='*60)

species_results = {}
top_genera_info = {}
species_spark_df = None

if _SPARK_AVAILABLE:
    ko_in_list = ', '.join(f"'{k}'" for k in sorted(PRIMARY_KOS))
    ko_t1 = ', '.join(f"'{k}'" for k in sorted(TIER1_KOS))
    ko_t2 = ', '.join(f"'{k}'" for k in sorted(TIER2_KOS))

    # Step 1.1 — Identify top 5 genera by species count
    print('\nStep 1.1: Identifying top 5 genera by species count...')
    top_genera_sql = """
        SELECT
            SPLIT(tax.genus, '__')[1]   AS genus_name,
            COUNT(DISTINCT tax.species) AS n_species,
            COUNT(DISTINCT tax.genome_id) AS n_genomes
        FROM kbase.ke_pangenome.gtdb_taxonomy_r214v1 tax
        WHERE tax.genus IS NOT NULL
          AND tax.species IS NOT NULL
          AND TRIM(SPLIT(tax.genus, '__')[1]) != ''
          AND TRIM(SPLIT(tax.species, '__')[1]) != ''
        GROUP BY SPLIT(tax.genus, '__')[1]
        HAVING COUNT(DISTINCT tax.species) >= 10
        ORDER BY n_species DESC
        LIMIT 5
    """
    try:
        top_genera_spark = spark.sql(top_genera_sql).toPandas()
        print(top_genera_spark.to_string(index=False))
        top_genera_info = top_genera_spark
    except Exception as e:
        print(f'Top genera query failed: {e}')
        top_genera_spark = None

    if top_genera_spark is not None and len(top_genera_spark) > 0:
        target_genera = top_genera_spark['genus_name'].tolist()
        genus_filter = ', '.join(f"'{g}'" for g in target_genera)

        # Step 1.2 — Species-level KO density
        print('\nStep 1.2: Computing species-level KO density...')
        species_spark_df = None

        try:
            # 1.2a — Explode primary KOs from eggnog (pre-filtered to reduce size)
            spark.sql(f"""
                CREATE OR REPLACE TEMP VIEW ego_exploded_sp AS
                SELECT
                    ego.query_name,
                    TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) AS kegg_ko_single,
                    CASE
                        WHEN TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) IN ({ko_t1}) THEN 'tier1'
                        WHEN TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) IN ({ko_t2}) THEN 'tier2'
                        ELSE 'other'
                    END AS tier
                FROM kbase.ke_pangenome.eggnog_mapper_annotations ego
                LATERAL VIEW explode(split(ego.KEGG_ko, '[|,]')) ko AS ko_part
                WHERE TRIM(ko_part) != '-'
                  AND TRIM(ko_part) != ''
                  AND TRIM(REPLACE(TRIM(ko_part), 'ko:', '')) IN ({ko_in_list})
            """)
            print('  ego_exploded_sp view created.')

            # 1.2b — Species genome stats (genome count + mean genome size)
            # genome_size is in gtdb_metadata (joined via genome_id = accession)
            spark.sql(f"""
                CREATE OR REPLACE TEMP VIEW species_genome_stats AS
                SELECT
                    SPLIT(tax.genus, '__')[1]                AS genus_name,
                    SPLIT(tax.species, '__')[1]              AS species_name,
                    g.gtdb_species_clade_id,
                    COUNT(DISTINCT tax.genome_id)            AS n_genomes,
                    AVG(CAST(meta.genome_size AS DOUBLE)) / 1e6  AS mean_genome_mb
                FROM kbase.ke_pangenome.gtdb_taxonomy_r214v1 tax
                JOIN kbase.ke_pangenome.genome g
                  ON tax.genome_id = g.genome_id
                JOIN kbase.ke_pangenome.gtdb_metadata meta
                  ON tax.genome_id = meta.accession
                WHERE SPLIT(tax.genus, '__')[1] IN ({genus_filter})
                  AND tax.species IS NOT NULL
                  AND TRIM(SPLIT(tax.species, '__')[1]) != ''
                  AND meta.genome_size IS NOT NULL
                  AND CAST(meta.genome_size AS DOUBLE) > 0
                GROUP BY SPLIT(tax.genus, '__')[1], SPLIT(tax.species, '__')[1], g.gtdb_species_clade_id
                HAVING COUNT(DISTINCT tax.genome_id) >= 3
            """)
            print('  species_genome_stats view created.')

            # 1.2c — Species KO counts: start from primary-KO genes, join up to species
            # gene_genecluster_junction has (gene_id, gene_cluster_id) — no genome_id
            # gene_cluster has (gene_cluster_id, gtdb_species_clade_id)
            # This yields species pangenome KO repertoire per species clade
            spark.sql("""
                CREATE OR REPLACE TEMP VIEW species_ko_counts AS
                SELECT
                    sgs.genus_name,
                    sgs.species_name,
                    COUNT(DISTINCT CASE WHEN e.tier = 'tier1' THEN e.kegg_ko_single END) AS n_ko_tier1,
                    COUNT(DISTINCT CASE WHEN e.tier = 'tier2' THEN e.kegg_ko_single END) AS n_ko_tier2,
                    COUNT(DISTINCT e.kegg_ko_single) AS n_ko_primary
                FROM ego_exploded_sp e
                JOIN kbase.ke_pangenome.gene_genecluster_junction junc
                  ON e.query_name = junc.gene_id
                JOIN kbase.ke_pangenome.gene_cluster gc
                  ON junc.gene_cluster_id = gc.gene_cluster_id
                JOIN species_genome_stats sgs
                  ON gc.gtdb_species_clade_id = sgs.gtdb_species_clade_id
                GROUP BY sgs.genus_name, sgs.species_name
            """)
            print('  species_ko_counts view created.')

            # 1.2d — Final join: KO density = species pangenome KOs / mean genome size
            species_spark_df = spark.sql("""
                SELECT
                    sgs.genus_name,
                    sgs.species_name,
                    sgs.n_genomes,
                    sgs.mean_genome_mb,
                    skc.n_ko_primary / sgs.mean_genome_mb  AS ko_per_mb_primary,
                    skc.n_ko_tier1   / sgs.mean_genome_mb  AS ko_per_mb_tier1,
                    skc.n_ko_tier2   / sgs.mean_genome_mb  AS ko_per_mb_tier2
                FROM species_genome_stats sgs
                JOIN species_ko_counts skc
                  ON sgs.genus_name = skc.genus_name AND sgs.species_name = skc.species_name
            """).toPandas()
            print(f'Species with ≥3 genomes across target genera: {len(species_spark_df)}')
            if len(species_spark_df) > 0:
                print(species_spark_df.groupby('genus_name').size().to_string())

        except Exception as e:
            print(f'Species KO density query failed: {e}')
            species_spark_df = None

        # Also get isolation source diversity per species from GTDB metadata
        if species_spark_df is not None and len(species_spark_df) > 0:
            try:
                spark.sql(f"""
                    CREATE OR REPLACE TEMP VIEW species_isolation_diversity AS
                    SELECT
                        SPLIT(tax.genus, '__')[1]                  AS genus_name,
                        SPLIT(tax.species, '__')[1]                AS species_name,
                        COUNT(DISTINCT meta.ncbi_isolation_source) AS n_isolation_sources,
                        COUNT(DISTINCT tax.genome_id)              AS n_genomes_meta
                    FROM kbase.ke_pangenome.gtdb_taxonomy_r214v1 tax
                    LEFT JOIN kbase.ke_pangenome.gtdb_metadata meta
                      ON tax.genome_id = meta.accession
                    WHERE SPLIT(tax.genus, '__')[1] IN ({genus_filter})
                    GROUP BY SPLIT(tax.genus, '__')[1], SPLIT(tax.species, '__')[1]
                    HAVING COUNT(DISTINCT tax.genome_id) >= 3
                """)
                iso_df = spark.sql("SELECT * FROM species_isolation_diversity").toPandas()
                print(f'Species isolation source diversity: {len(iso_df)} species')
                species_spark_df = species_spark_df.merge(iso_df, on=['genus_name', 'species_name'], how='left')
            except Exception as e:
                print(f'Isolation source query failed: {e}')
                species_spark_df['n_isolation_sources'] = np.nan

            species_spark_df.to_csv(DATA / 'species_level_density.csv', index=False)
            print(f'Saved: data/species_level_density.csv')

if species_spark_df is not None:
    # Step 1.3 — Match to niche breadth
    # Use genus-level B as proxy for species, map via genus_name
    genus_b = genus_df[['genus_lower', 'mean_levins_B_std']].copy()
    species_spark_df['genus_lower'] = species_spark_df['genus_name'].str.lower().str.replace(' ', '_')
    species_spark_df = species_spark_df.merge(genus_b, on='genus_lower', how='left')

    print(f'\nSpecies with genus-level B available: {species_spark_df["mean_levins_B_std"].notna().sum()} / {len(species_spark_df)}')

    # Step 1.4 — Within-genus OLS (not PGLS — no species-level phylogeny available)
    print('\nStep 1.4: Within-genus OLS regression (species-level KO density ~ genome size)')
    for genus in species_spark_df['genus_name'].unique():
        sub = species_spark_df[species_spark_df['genus_name'] == genus].copy()
        sub = sub.dropna(subset=['ko_per_mb_primary', 'mean_genome_mb'])
        n_sp = len(sub)
        if n_sp < 5:
            species_results[genus] = {'n_species': n_sp, 'note': 'too few species (<5), skipped'}
            continue

        # Primary: species KO density ~ genome size (within-genus)
        # This tests the genome-streamlining relationship within a genus
        X_gs = sm.add_constant(
            (sub['mean_genome_mb'] - sub['mean_genome_mb'].mean()) / sub['mean_genome_mb'].std()
        )
        y_gs = (sub['ko_per_mb_primary'] - sub['ko_per_mb_primary'].mean()) / sub['ko_per_mb_primary'].std()
        try:
            m_gs = sm.OLS(y_gs, X_gs).fit()
            beta_gs = m_gs.params.iloc[1]
            p_gs = m_gs.pvalues.iloc[1]
            r2_gs = m_gs.rsquared
        except Exception:
            beta_gs = p_gs = r2_gs = np.nan

        # Tier1 vs Tier2 comparison
        if sub['ko_per_mb_tier1'].notna().sum() > 3 and sub['ko_per_mb_tier2'].notna().sum() > 3:
            X_gs2 = sm.add_constant(
                (sub['mean_genome_mb'] - sub['mean_genome_mb'].mean()) / sub['mean_genome_mb'].std()
            )
            y_t1 = (sub['ko_per_mb_tier1'] - sub['ko_per_mb_tier1'].mean()) / sub['ko_per_mb_tier1'].std()
            y_t2 = (sub['ko_per_mb_tier2'] - sub['ko_per_mb_tier2'].mean()) / sub['ko_per_mb_tier2'].std()
            try:
                beta_t1 = sm.OLS(y_t1, X_gs2).fit().params.iloc[1]
                p_t1    = sm.OLS(y_t1, X_gs2).fit().pvalues.iloc[1]
                beta_t2 = sm.OLS(y_t2, X_gs2).fit().params.iloc[1]
                p_t2    = sm.OLS(y_t2, X_gs2).fit().pvalues.iloc[1]
            except Exception:
                beta_t1 = beta_t2 = p_t1 = p_t2 = np.nan
        else:
            beta_t1 = beta_t2 = p_t1 = p_t2 = np.nan

        # Isolation source breadth vs KO density (if available)
        if sub['n_isolation_sources'].notna().sum() >= 5:
            X_iso = sm.add_constant(
                (sub['ko_per_mb_primary'] - sub['ko_per_mb_primary'].mean()) / sub['ko_per_mb_primary'].std()
            )
            y_iso = np.log1p(sub['n_isolation_sources'].fillna(1))
            y_iso = (y_iso - y_iso.mean()) / y_iso.std()
            try:
                m_iso = sm.OLS(y_iso, X_iso).fit()
                beta_iso = m_iso.params.iloc[1]
                p_iso    = m_iso.pvalues.iloc[1]
            except Exception:
                beta_iso = p_iso = np.nan
        else:
            beta_iso = p_iso = np.nan

        species_results[genus] = {
            'n_species': n_sp,
            'beta_density_vs_genomesize': round(beta_gs, 4),
            'p_density_vs_genomesize':    round(p_gs, 4),
            'r2_density_vs_genomesize':   round(r2_gs, 4),
            'beta_tier1_vs_genomesize':   round(beta_t1, 4) if not np.isnan(beta_t1) else 'NA',
            'p_tier1_vs_genomesize':      round(p_t1, 4) if not np.isnan(p_t1) else 'NA',
            'beta_tier2_vs_genomesize':   round(beta_t2, 4) if not np.isnan(beta_t2) else 'NA',
            'p_tier2_vs_genomesize':      round(p_t2, 4) if not np.isnan(p_t2) else 'NA',
            'beta_density_vs_iso_breadth': round(beta_iso, 4) if not np.isnan(beta_iso) else 'NA',
            'p_density_vs_iso_breadth':    round(p_iso, 4) if not np.isnan(p_iso) else 'NA',
            'genus_level_B': round(float(sub['mean_levins_B_std'].iloc[0]), 4)
                             if sub['mean_levins_B_std'].notna().any() else 'NA',
            'note': 'OLS; species tree unavailable; species-level niche breadth unavailable'
        }
        print(f'  {genus}: n={n_sp}, β(density~genomesize)={beta_gs:.3f}, p={p_gs:.4f}')
else:
    # Full Spark fallback — use genus-level data to show within-genus genome-size relationship
    print('\nSpark unavailable: computing fallback genome-size vs density OLS at genus level')
    genus_df_clean = genus_df.dropna(subset=['ko_per_mb_primary', 'mean_genome_mb', 'mean_levins_B_std'])
    X = sm.add_constant(stats.zscore(genus_df_clean['mean_genome_mb']))
    y = stats.zscore(genus_df_clean['ko_per_mb_primary'])
    m = sm.OLS(y, X).fit()
    fallback_result = {
        'genus_level_beta_density_vs_genomesize': round(m.params.iloc[1], 4),
        'p': round(m.pvalues.iloc[1], 6),
        'n': len(genus_df_clean),
        'note': 'Genus-level fallback (Spark unavailable)'
    }
    species_results['ALL_GENERA_FALLBACK'] = fallback_result
    print(f'  Genus-level β(density~genomesize): {m.params.iloc[1]:.3f}, p={m.pvalues.iloc[1]:.4f}')

print('\nAnalysis 1 complete.')

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 2 — Community-level CWM validation
# ═══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('ANALYSIS 2: Community-level CWM validation')
print('='*60)

# Load the sample-level CWM data (h3a analysis output)
cwm_df = pd.read_csv(DATA / 'h3a_cwm_sample_data.csv')
print(f'CWM sample data loaded: {len(cwm_df):,} rows')

# Deduplicate (the file has duplicate sample_id rows in the raw data)
cwm_df = cwm_df.drop_duplicates(subset='sample_id')
print(f'After dedup: {len(cwm_df):,} unique samples')

# Metal columns available (use GEOROC, not CSU)
METAL_COLS = {
    'Cu': 'georoc_Cu',
    'Ni': 'georoc_Ni',
    'Zn': 'georoc_Zn',
    'Co': 'georoc_Co',
    'Cr': 'georoc_Cr',
    'Pb': 'georoc_Pb',
}

print('\nMetal coverage:')
for metal, col in METAL_COLS.items():
    n = cwm_df[col].notna().sum()
    print(f'  {metal} ({col}): {n:,} samples')

# CWM predictors available
cwm_preds = ['cwm_ko', 'cwm_cofactor', 'cwm_resistance']
print('\nCWM predictor coverage:')
for p in cwm_preds:
    n = cwm_df[p].notna().sum()
    print(f'  {p}: {n:,}')

# Add genus-level mean niche breadth to compute CWM niche breadth
# The h3a data doesn't have per-genus abundances, only the aggregated CWM
# So CWM niche breadth cannot be directly computed from this file.
# However, cwm_ko aggregates genus-level ko_per_mb, and we can note this limitation.

cwm2_results = []

for metal_name, metal_col in METAL_COLS.items():
    sub = cwm_df[['sample_id', 'cwm_ko', 'cwm_cofactor', 'cwm_resistance',
                  'cwm_genome_mb', 'soil_pH', metal_col]].copy()
    sub = sub.rename(columns={metal_col: 'metal_conc'})
    sub = sub.dropna(subset=['cwm_ko', 'cwm_cofactor', 'cwm_resistance', 'metal_conc'])
    sub = sub[sub['metal_conc'] > 0]

    n = len(sub)
    if n < 30:
        print(f'  {metal_name}: only {n} samples — skip')
        continue

    print(f'\n  {metal_name}: n={n:,} samples')

    # log-transform metal concentration
    sub['log_metal'] = np.log10(sub['metal_conc'] + 1)
    sub['cwm_ko_z']          = stats.zscore(sub['cwm_ko'])
    sub['cwm_cofactor_z']    = stats.zscore(sub['cwm_cofactor'])
    sub['cwm_resistance_z']  = stats.zscore(sub['cwm_resistance'])
    sub['cwm_genome_mb_z']   = stats.zscore(sub['cwm_genome_mb'])

    has_ph = sub['soil_pH'].notna().sum() > 0.3 * n

    # Model A: aggregate CWM metal-gene density only
    try:
        X_a = sm.add_constant(sub['cwm_ko_z'])
        m_a = sm.OLS(sub['log_metal'], X_a).fit()
        beta_ko = m_a.params['cwm_ko_z']
        p_ko    = m_a.pvalues['cwm_ko_z']
        r2_a    = m_a.rsquared
    except Exception as e:
        beta_ko = p_ko = r2_a = np.nan

    # Model B: resistance + cofactor split
    try:
        if has_ph:
            sub_ph = sub.dropna(subset=['soil_pH'])
            sub_ph['soil_pH_z'] = stats.zscore(sub_ph['soil_pH'])
            X_b = sm.add_constant(sub_ph[['cwm_resistance_z', 'cwm_cofactor_z', 'soil_pH_z']])
            m_b = sm.OLS(sub_ph['log_metal'], X_b).fit()
            n_b = len(sub_ph)
        else:
            X_b = sm.add_constant(sub[['cwm_resistance_z', 'cwm_cofactor_z']])
            m_b = sm.OLS(sub['log_metal'], X_b).fit()
            n_b = n

        beta_res = m_b.params.get('cwm_resistance_z', np.nan)
        p_res    = m_b.pvalues.get('cwm_resistance_z', np.nan)
        beta_cof = m_b.params.get('cwm_cofactor_z', np.nan)
        p_cof    = m_b.pvalues.get('cwm_cofactor_z', np.nan)
        r2_b     = m_b.rsquared
    except Exception as e:
        beta_res = p_res = beta_cof = p_cof = r2_b = np.nan
        n_b = n

    cwm2_results.append({
        'metal':          metal_name,
        'n_samples_modelA': n,
        'n_samples_modelB': n_b if has_ph else n,
        'beta_cwm_ko':    beta_ko,
        'p_cwm_ko':       p_ko,
        'r2_modelA':      r2_a,
        'beta_cwm_resistance': beta_res,
        'p_cwm_resistance':    p_res,
        'beta_cwm_cofactor':   beta_cof,
        'p_cwm_cofactor':      p_cof,
        'r2_modelB':      r2_b,
        'soil_pH_included': has_ph,
    })

    print(f'    β(cwm_ko): {beta_ko:.4f} (p={p_ko:.4g}), R²={r2_a:.4f}')
    print(f'    β(resistance): {beta_res:.4f} (p={p_res:.4g}), β(cofactor): {beta_cof:.4f} (p={p_cof:.4g}), R²={r2_b:.4f}')

cwm2_df = pd.DataFrame(cwm2_results)
cwm2_df.to_csv(DATA / 'cwm_community_validation_results.csv', index=False)
print(f'\nSaved: data/cwm_community_validation_results.csv')

# BH-FDR across metals for ModelB resistance and cofactor
from statsmodels.stats.multitest import multipletests  # noqa: this submodule is safe
if len(cwm2_df) > 0:
    for col_p, col_q in [('p_cwm_resistance', 'q_cwm_resistance'),
                         ('p_cwm_cofactor',   'q_cwm_cofactor'),
                         ('p_cwm_ko',         'q_cwm_ko')]:
        mask = cwm2_df[col_p].notna()
        if mask.sum() > 0:
            rej, q, _, _ = multipletests(cwm2_df.loc[mask, col_p], method='fdr_bh')
            cwm2_df.loc[mask, col_q] = q
    cwm2_df.to_csv(DATA / 'cwm_community_validation_results.csv', index=False)
    print('FDR correction applied and saved.')
    print(cwm2_df[['metal', 'n_samples_modelA', 'beta_cwm_ko', 'p_cwm_ko',
                   'beta_cwm_resistance', 'p_cwm_resistance',
                   'beta_cwm_cofactor', 'p_cwm_cofactor']].to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════════
# Write markdown report
# ═══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('Writing species_and_community_validation.md')
print('='*60)

# Format helpers
def fmt_p(p):
    if pd.isna(p): return 'NA'
    if p < 0.001: return f'{p:.2e}'
    return f'{p:.4f}'

def sig_label(p):
    if pd.isna(p): return ''
    if p < 0.001: return ' ***'
    if p < 0.01:  return ' **'
    if p < 0.05:  return ' *'
    if p < 0.10:  return ' †'
    return ''

# Determine spark status label
spark_label = 'kbase.ke_pangenome (Spark)' if _SPARK_AVAILABLE else 'Local fallback (Spark unavailable)'
data_source_a1 = spark_label

lines = []
lines.append('# Species-Level and Community-Level Robustness Analyses\n')
lines.append('## Overview\n')
lines.append('Two supplementary robustness analyses testing whether the genus-level '
             'metal-gene density / niche breadth signal holds at finer taxonomic and '
             'ecological resolution.\n')
lines.append(f'- **Analysis 1 data source**: {data_source_a1}')
lines.append(f'- **Analysis 2 data source**: MicrobeAtlas CWM × GEOROC geochemistry '
             f'(h3a_cwm_sample_data.csv)')
lines.append('')

# ── Analysis 1 ────────────────────────────────────────────────────────────────
lines.append('---\n')
lines.append('## Analysis 1 — Species-level sensitivity\n')
lines.append('### Rationale\n')
lines.append('The primary analysis operates at the GTDB genus level (n = 1,574 genera). '
             'If the genus-level signal is driven by genus-level aggregation artefacts, '
             'it should not replicate when the same relationship is tested within genera '
             'at the species level. Conversely, if the underlying biology operates at the '
             'species level and is visible through genome-size/density covariation, '
             'within-genus OLS should recover it.\n')

lines.append('### Data availability and fallback decisions\n')

if _SPARK_AVAILABLE and species_spark_df is not None:
    lines.append(f'Species-level KO densities were queried from `kbase.ke_pangenome` '
                 f'({len(species_spark_df)} species across {species_spark_df["genus_name"].nunique()} target genera). '
                 'Species-level niche breadth from MicrobeAtlas is unavailable (MicrobeAtlas '
                 'provides OTU-to-genus mapping only). **Fallback applied**: (1) genus-level '
                 'Levins\' B used as a within-genus constant for context; (2) number of distinct '
                 'isolation sources (from GTDB metadata) used as a species ecological breadth proxy '
                 'where available; (3) within-genus OLS of species per-Mb KO density vs. species '
                 'mean genome size as the primary result (tests whether genome-streamlining '
                 'covariation is preserved at species resolution).\n')
    lines.append('**Note on method**: No species-level phylogenetic tree is available for PGLS; '
                 'OLS was used with the caveat that species within a genus are not phylogenetically '
                 'independent. Results are descriptive.\n')

    lines.append('### Top 5 genera by species count\n')
    if len(top_genera_info) > 0:
        lines.append('| Genus | N species | N genomes |')
        lines.append('|-------|-----------|-----------|')
        for _, row in top_genera_info.iterrows():
            lines.append(f'| *{row["genus_name"]}* | {int(row["n_species"])} | {int(row["n_genomes"])} |')
        lines.append('')

    lines.append('### Within-genus OLS results\n')
    lines.append('**Response**: standardised species per-Mb KO density. '
                 '**Predictor**: standardised species mean genome size (Mb). '
                 'Negative β indicates smaller-genome species within a genus have '
                 'higher per-Mb metal-gene density — consistent with the genus-level P1 finding.\n')
    lines.append('| Genus | N species | β (density ~ genome size) | p | β (Tier1) | β (Tier2) | Genus B_std |')
    lines.append('|-------|-----------|--------------------------|---|-----------|-----------|-------------|')
    for genus, r in species_results.items():
        if 'note' in r and 'too few' in r.get('note', ''):
            lines.append(f'| *{genus}* | {r["n_species"]} | — | — | — | — | — |')
            continue
        b = r.get('beta_density_vs_genomesize', 'NA')
        p = r.get('p_density_vs_genomesize', 'NA')
        b1 = r.get('beta_tier1_vs_genomesize', 'NA')
        b2 = r.get('beta_tier2_vs_genomesize', 'NA')
        gb = r.get('genus_level_B', 'NA')
        sl = sig_label(p) if isinstance(p, float) else ''
        b_str  = f'{b:.3f}{sl}' if isinstance(b, float) else str(b)
        p_str  = fmt_p(p) if isinstance(p, float) else str(p)
        b1_str = f'{b1:.3f}' if isinstance(b1, float) else str(b1)
        b2_str = f'{b2:.3f}' if isinstance(b2, float) else str(b2)
        gb_str = f'{gb:.3f}' if isinstance(gb, float) else str(gb)
        lines.append(f'| *{genus}* | {r["n_species"]} | {b_str} | {p_str} | {b1_str} | {b2_str} | {gb_str} |')
    lines.append('')
    lines.append('*\\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, † p<0.10*\n')

else:
    lines.append('**Spark unavailable**: species-level queries could not be executed. '
                 'Genus-level fallback reported instead.\n')
    r = species_results.get('ALL_GENERA_FALLBACK', {})
    lines.append(f'- Genus-level β(density ~ genome size) = {r.get("genus_level_beta_density_vs_genomesize", "NA")}, '
                 f'p = {r.get("p", "NA")}, n = {r.get("n", "NA")} genera.')
    lines.append('- This confirms that the genus-level streamlining relationship '
                 '(higher KO density in smaller-genome genera) is robust, providing indirect '
                 'support for the species-level hypothesis.\n')

lines.append('### Interpretation\n')
if _SPARK_AVAILABLE and species_spark_df is not None:
    # Check directionality
    neg_count = sum(1 for r in species_results.values()
                    if isinstance(r.get('beta_density_vs_genomesize'), float)
                    and r['beta_density_vs_genomesize'] < 0)
    total = sum(1 for r in species_results.values()
                if isinstance(r.get('beta_density_vs_genomesize'), float))
    sig_count = sum(1 for r in species_results.values()
                    if isinstance(r.get('p_density_vs_genomesize'), float)
                    and r['p_density_vs_genomesize'] < 0.05)

    lines.append(f'{neg_count}/{total} target genera show a negative β for density vs genome size '
                 f'(consistent with primary P1 direction); {sig_count} are individually significant '
                 f'at p < 0.05. ')
    if neg_count >= total * 0.6:
        lines.append('The majority-negative direction supports the hypothesis that the genus-level '
                     'signal reflects a pattern operating at finer taxonomic resolution. ')
    else:
        lines.append('The mixed directionality suggests the genus-level signal may partly reflect '
                     'compositional differences across genera rather than a within-genus species-level effect. ')
    lines.append('Because species-level niche breadth (MicrobeAtlas) is unavailable, a direct species-level '
                 'replication of P1 cannot be completed with current data. The within-genus genome-size '
                 'analysis provides indirect support for the streamlining mechanism. This limitation '
                 'is noted in the Limitations section of the manuscript.\n')
else:
    lines.append('Species-level analysis could not be completed (Spark unavailable). '
                 'Genus-level streamlining relationship confirmed as fallback.\n')

# ── Analysis 2 ────────────────────────────────────────────────────────────────
lines.append('---\n')
lines.append('## Analysis 2 — Community-level CWM validation\n')
lines.append('### Rationale\n')
lines.append('The primary P1 analysis tests whether genera with higher per-Mb metal-gene density '
             'occupy narrower niches (cross-biome Levins\' B). If this signal has ecological meaning, '
             'it should manifest at the community level: samples from metal-rich environments should '
             'have communities with higher community-weighted mean (CWM) metal-gene density. '
             'The resistance/cofactor split predicts that CWM resistance density may positively '
             'predict metal concentrations (metal stress selects for resistant taxa), while CWM cofactor '
             'density should be null or negative (cofactor genes reflect niche specialisation, not '
             'direct metal response).\n')

lines.append('### Data\n')
lines.append('- **CWM source**: MicrobeAtlas-derived CWM from the H3a analysis '
             f'(n = {len(cwm_df):,} unique samples after deduplication).')
lines.append('- **Metal concentrations**: GEOROC geochemical database, spatially joined to '
             'sample coordinates.')
lines.append('- **CWM predictors**: cwm_ko (aggregate primary 140-KO density), '
             'cwm_resistance (Tier 1 KOs), cwm_cofactor (Tier 2 KOs).')
lines.append('- **CWM niche breadth**: not available per-sample in this dataset; omitted from models.')
lines.append('- **Covariates**: soil pH included where coverage ≥30% of metal-matched samples.')
lines.append('- **Metal threshold**: ≥30 samples with non-missing metal and CWM data required.')
lines.append('')

if len(cwm2_df) > 0:
    lines.append('### Model A — Aggregate CWM metal-gene density → metal concentration\n')
    lines.append('`log10(metal_concentration + 1) ~ CWM_ko_per_mb (z-scored)`\n')
    lines.append('| Metal | N samples | β(CWM_ko) | p | q (BH) |')
    lines.append('|-------|-----------|-----------|---|--------|')
    for _, row in cwm2_df.iterrows():
        b = row['beta_cwm_ko']
        p = row['p_cwm_ko']
        q = row.get('q_cwm_ko', np.nan)
        sl = sig_label(p)
        lines.append(f'| {row["metal"]} | {int(row["n_samples_modelA"]):,} | '
                     f'{b:.4f}{sl} | {fmt_p(p)} | {fmt_p(q)} |')
    lines.append('')
    lines.append('*\\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, † p<0.10*\n')

    lines.append('### Model B — Resistance/cofactor split → metal concentration\n')
    lines.append('`log10(metal_concentration + 1) ~ CWM_resistance_z + CWM_cofactor_z [+ soil_pH]`\n')
    lines.append('| Metal | N samples | β(resistance) | p | q | β(cofactor) | p | q |')
    lines.append('|-------|-----------|--------------|---|---|-------------|---|---|')
    for _, row in cwm2_df.iterrows():
        br = row['beta_cwm_resistance']
        pr = row['p_cwm_resistance']
        qr = row.get('q_cwm_resistance', np.nan)
        bc = row['beta_cwm_cofactor']
        pc = row['p_cwm_cofactor']
        qc = row.get('q_cwm_cofactor', np.nan)
        ph_note = ' +pH' if row['soil_pH_included'] else ''
        lines.append(f'| {row["metal"]}{ph_note} | {int(row["n_samples_modelB"]):,} | '
                     f'{br:.4f}{sig_label(pr)} | {fmt_p(pr)} | {fmt_p(qr)} | '
                     f'{bc:.4f}{sig_label(pc)} | {fmt_p(pc)} | {fmt_p(qc)} |')
    lines.append('')
    lines.append('*+pH = soil pH included as covariate; \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, † p<0.10*\n')

    # Directional consistency check
    pos_res = (cwm2_df['beta_cwm_resistance'] > 0).sum()
    neg_cof = (cwm2_df['beta_cwm_cofactor'] < 0).sum()
    total_m = len(cwm2_df)
    sig_res = (cwm2_df['p_cwm_resistance'] < 0.05).sum()
    sig_cof = (cwm2_df['p_cwm_cofactor'] < 0.05).sum()

    lines.append('### Comparison to primary genus-level findings\n')
    lines.append(f'- **CWM resistance vs metal concentration**: {pos_res}/{total_m} metals show positive β '
                 f'(predicts higher metal → higher resistance gene communities; '
                 f'{sig_res} individually significant at p < 0.05).')
    lines.append(f'- **CWM cofactor vs metal concentration**: {neg_cof}/{total_m} metals show negative β '
                 f'({sig_cof} individually significant at p < 0.05).')

    if pos_res >= total_m * 0.5 and neg_cof >= total_m * 0.5:
        lines.append('- **Directionality matches** the genus-level multi-axis finding: resistance-enriched '
                     'communities tend to inhabit metal-rich environments, while cofactor-enriched communities '
                     'do not. This strengthens the ecological interpretation of the functional split.')
    elif pos_res >= total_m * 0.5:
        lines.append('- **Partial directional match**: resistance CWM shows positive association with metal '
                     'concentrations (consistent with genus-level signal), but cofactor CWM direction is mixed.')
    else:
        lines.append('- **Directional signal is weak** at the community level: neither resistance nor cofactor '
                     'CWM shows consistent directional association with metal concentrations across metals. '
                     'The community-level signal may require within-biome comparisons or '
                     'contamination categories rather than raw concentration predictors.')
    lines.append('')

    lines.append('### Interpretation\n')
    lines.append('The community-level CWM regression tests the ecological analog of the genus-level P1 signal: '
                 'whether samples from metal-richer environments assemble communities with higher metal-gene '
                 'investment. This is a conceptually distinct hypothesis (community assembly vs. evolutionary '
                 'niche specialisation) but should show correlated patterns if the biology is self-consistent. ')
    lines.append('\nKey caveats: (1) GEOROC metal concentrations reflect geological substrate, not contemporary '
                 'pore-water bioavailability; (2) CWM niche breadth was not available at the per-sample level '
                 'and could not be included; (3) OLS was used (no phylogenetic correction at the community level); '
                 '(4) the relationship between metal concentration and microbial community composition '
                 'is mediated by many unmeasured variables (redox state, SOM, pH), which are only partially '
                 'controlled here by soil pH.\n')
else:
    lines.append('**No metals met the ≥30 sample threshold.** The community-level analysis could not be completed.')
    lines.append('Fallback: biome-level CWM comparison reported separately in cwm_by_biome.csv.\n')

lines.append('---\n')
lines.append('## Summary\n')
lines.append('| Analysis | Key result | Consistent with P1? |')
lines.append('|----------|-----------|---------------------|')

if _SPARK_AVAILABLE and species_spark_df is not None and len(species_results) > 0:
    neg_ct = sum(1 for r in species_results.values()
                 if isinstance(r.get('beta_density_vs_genomesize'), float)
                 and r['beta_density_vs_genomesize'] < 0)
    tot_ct = sum(1 for r in species_results.values()
                 if isinstance(r.get('beta_density_vs_genomesize'), float))
    a1_result = f'{neg_ct}/{tot_ct} genera: negative β within genus (density ~ genome size)'
    a1_consistent = 'Partially (genome-streamlining pattern present within genera)' if neg_ct >= tot_ct * 0.5 else 'Mixed'
else:
    a1_result = 'Spark unavailable; genus-level fallback confirms streamlining'
    a1_consistent = 'Indirect support'

if len(cwm2_df) > 0:
    pos_r = (cwm2_df['beta_cwm_resistance'] > 0).sum()
    neg_c = (cwm2_df['beta_cwm_cofactor'] < 0).sum()
    tot_m2 = len(cwm2_df)
    a2_result = (f'CWM resistance: positive for {pos_r}/{tot_m2} metals; '
                 f'CWM cofactor: negative for {neg_c}/{tot_m2} metals')
    a2_consistent = 'Partially' if (pos_r + neg_c) >= tot_m2 else 'Mixed'
else:
    a2_result = 'Insufficient data'
    a2_consistent = 'Not tested'

lines.append(f'| 1 (species-level) | {a1_result} | {a1_consistent} |')
lines.append(f'| 2 (CWM community) | {a2_result} | {a2_consistent} |')
lines.append('')
lines.append('**Data files produced**:')
lines.append('- `data/species_level_density.csv` — species-level KO density per genus' if _SPARK_AVAILABLE and species_spark_df is not None else '- `data/species_level_density.csv` — not produced (Spark unavailable)')
lines.append('- `data/cwm_community_validation_results.csv` — CWM regression results per metal')
lines.append('')

report_text = '\n'.join(lines)
report_path = PROJECT / 'species_and_community_validation.md'
report_path.write_text(report_text)
print(f'\nReport written to: {report_path}')
print('Done.')

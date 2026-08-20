#!/usr/bin/env python3
"""
h3a_cwm_analysis_v2.py

H3a CWM analysis — corrected version using arkinlab.envdbs for soil metals.

Changes from v1:
  - Fixes 10x row blowup from enriched_metadata_gee duplicate SRS_Join_Keys
    (now deduplicates with GROUP BY before joining)
  - Replaces GeoROC bedrock metals (geological background) with:
      * csu_metal_mobility_grid: bioavailable metal fractions (pf1 = BCR phase 1)
      * science_2025_global_soil_toxic_metals: total soil metals incl. Ni
  - Spatial join done entirely in Spark via 0.05° lat/lon rounding

CWM values reused from v1 (83,401 soil samples with ≥5% genus-density coverage).
"""

import sys
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

sys.path.insert(0, '/opt/conda/lib/python3.13/site-packages')
import berdl_notebook_utils
spark = berdl_notebook_utils.get_spark_session()

DATA   = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
REPORT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/report')

# ── Load clean CWM data (deduplicate v1 blowup) ──────────────────────────────
print("── Loading clean CWM data ──")
cwm_raw = pd.read_csv(DATA / 'h3a_cwm_sample_data.csv',
                      usecols=['sample_id', 'cwm_ko', 'cwm_cofactor',
                               'cwm_resistance', 'cwm_genome_mb',
                               'coverage', 'n_genera_matched'])
cwm = cwm_raw.drop_duplicates('sample_id').copy()
print(f"  Unique CWM samples: {len(cwm):,}")
print(f"  Coverage: mean={cwm['coverage'].mean():.3f}, SD={cwm['coverage'].std():.3f}")

# Bring to Spark temp view
cwm_sdf = spark.createDataFrame(cwm)
cwm_sdf.createOrReplaceTempView("cwm_samples")

# ── Spatial join: CSU + science_2025 + pH via Spark ──────────────────────────
# All spatial joins use 0.05° rounding (≈5km). CSU grid spacing ~0.045°.

print("\n── Building spatial env joins in Spark (CSU + science_2025 + pH) ──")
print("   Rounding lat/lon to 0.05° for nearest-grid-cell matching...")

env_sdf = spark.sql("""
WITH csu_agg AS (
    SELECT
        ROUND(CAST(latitude  AS DOUBLE) / 0.05) * 0.05 AS lat_key,
        ROUND(CAST(longitude AS DOUBLE) / 0.05) * 0.05 AS lon_key,
        AVG(CAST(pf1_cu AS DOUBLE)) AS csu_cu_bio,
        AVG(CAST(pf1_cr AS DOUBLE)) AS csu_cr_bio,
        AVG(CAST(pf1_cd AS DOUBLE)) AS csu_cd_bio,
        AVG(CAST(pf1_as AS DOUBLE)) AS csu_as_bio,
        AVG(CAST(pf1_pb AS DOUBLE)) AS csu_pb_bio
    FROM arkinlab.envdbs.csu_metal_mobility_grid
    GROUP BY lat_key, lon_key
),
sci2025_agg AS (
    SELECT
        ROUND(CAST(latitude  AS DOUBLE) / 0.05) * 0.05 AS lat_key,
        ROUND(CAST(longitude AS DOUBLE) / 0.05) * 0.05 AS lon_key,
        AVG(CAST(cu AS DOUBLE)) AS sci_cu,
        AVG(CAST(ni AS DOUBLE)) AS sci_ni,
        AVG(CAST(co AS DOUBLE)) AS sci_co,
        AVG(CAST(cr AS DOUBLE)) AS sci_cr,
        AVG(CAST(pb AS DOUBLE)) AS sci_pb
    FROM arkinlab.envdbs.science_2025_global_soil_toxic_metals
    GROUP BY lat_key, lon_key
),
-- Clean sample coords: deduped from enriched_metadata (no dups on accession_id)
sample_coords AS (
    SELECT
        em.accession_id AS sample_id,
        ROUND(CAST(em.lat AS DOUBLE) / 0.05) * 0.05 AS lat_key,
        ROUND(CAST(em.lon AS DOUBLE) / 0.05) * 0.05 AS lon_key
    FROM arkinlab.microbeatlas.enriched_metadata em
    WHERE em.lat IS NOT NULL AND em.lon IS NOT NULL
),
-- Clean soil pH: aggregate to one row per sample (fixes gee duplication)
ph_clean AS (
    SELECT
        sm.sample_id,
        FIRST(g.olm_soil_ph_0cm_H2O)            AS soil_pH,
        FIRST(g.ERA5_mean_2m_air_temperature_K)  AS temp_K
    FROM arkinlab.microbeatlas.sample_metadata sm
    JOIN arkinlab.microbeatlas.enriched_metadata_gee g
         ON sm.SRS_Join_Key = g.SRS_Join_Key
    WHERE sm.Env_Level_1 IN ('soil', 'agricultural')
    GROUP BY sm.sample_id
),
-- Join everything to CWM samples
main AS (
    SELECT
        cs.sample_id,
        sc.lat_key, sc.lon_key,
        csu.csu_cu_bio, csu.csu_cr_bio, csu.csu_cd_bio, csu.csu_as_bio, csu.csu_pb_bio,
        s25.sci_cu, s25.sci_ni, s25.sci_co, s25.sci_cr, s25.sci_pb,
        ph.soil_pH, ph.temp_K
    FROM cwm_samples cs
    LEFT JOIN sample_coords sc ON cs.sample_id = sc.sample_id
    LEFT JOIN csu_agg   csu ON sc.lat_key = csu.lat_key AND sc.lon_key = csu.lon_key
    LEFT JOIN sci2025_agg s25 ON sc.lat_key = s25.lat_key AND sc.lon_key = s25.lon_key
    LEFT JOIN ph_clean  ph  ON cs.sample_id = ph.sample_id
)
SELECT * FROM main
""")

print("   Collecting env results...")
env_pdf = env_sdf.toPandas()
print(f"  Env rows: {len(env_pdf):,}  (expect ~83,401)")
if env_pdf['sample_id'].duplicated().any():
    print(f"  WARNING: {env_pdf['sample_id'].duplicated().sum()} duplicate sample_ids — deduplicating")
    env_pdf = env_pdf.drop_duplicates('sample_id')

print(f"  With lat/lon:      {env_pdf['lat_key'].notna().sum():,}")
print(f"  With CSU Cu:       {env_pdf['csu_cu_bio'].notna().sum():,}")
print(f"  With CSU Cr:       {env_pdf['csu_cr_bio'].notna().sum():,}")
print(f"  With sci_Ni:       {env_pdf['sci_ni'].notna().sum():,}")
print(f"  With sci_Cu:       {env_pdf['sci_cu'].notna().sum():,}")
print(f"  With soil_pH:      {env_pdf['soil_pH'].notna().sum():,}")

# Merge CWM with env
analysis_df = cwm.merge(env_pdf, on='sample_id', how='left')
assert len(analysis_df) == len(cwm), f"Row count changed: {len(cwm)} → {len(analysis_df)}"
print(f"\n  Final analysis rows: {len(analysis_df):,}")

out_path = DATA / 'h3a_cwm_analysis_v2_samples.csv'
analysis_df.to_csv(out_path, index=False)
print(f"  Saved: {out_path}")


# ── OLS regressions ───────────────────────────────────────────────────────────
print("\n── OLS regressions: CWM ~ CSU/science_2025 metals + soil pH ──")

PREDICTORS = [
    # CSU bioavailable fractions (BCR phase 1)
    ('csu_cu_bio', True,  'CSU_Cu_bio(pf1)'),
    ('csu_cr_bio', True,  'CSU_Cr_bio(pf1)'),
    ('csu_cd_bio', True,  'CSU_Cd_bio(pf1)'),
    ('csu_as_bio', True,  'CSU_As_bio(pf1)'),
    ('csu_pb_bio', True,  'CSU_Pb_bio(pf1)'),
    # science_2025 total soil metals
    ('sci_cu',     True,  'sci2025_Cu'),
    ('sci_ni',     True,  'sci2025_Ni'),
    ('sci_co',     True,  'sci2025_Co'),
    ('sci_cr',     True,  'sci2025_Cr'),
    ('sci_pb',     True,  'sci2025_Pb'),
    # Soil pH (continuous, no log)
    ('soil_pH',    False, 'soil_pH'),
]
RESPONSES = ['cwm_ko', 'cwm_cofactor', 'cwm_resistance']


def run_ols(y_col, x_col, df, log_x=True):
    sub = df[[y_col, x_col]].dropna()
    if log_x:
        sub = sub[sub[x_col] > 0]
    if len(sub) < 30:
        return None
    y = sub[y_col].values
    x_raw = np.log(sub[x_col].values) if log_x else sub[x_col].values
    x_z = (x_raw - x_raw.mean()) / x_raw.std()
    slope, intercept, r, p, se = stats.linregress(x_z, y)
    rho, p_rho = stats.spearmanr(x_raw, y)
    return {
        'response': y_col, 'predictor': x_col, 'label': None,
        'log_x': log_x, 'beta': slope, 'SE': se,
        'p_ols': p, 'r_pearson': r,
        'rho_spearman': rho, 'p_spearman': p_rho,
        'n': len(sub),
    }


def sig(p):
    return ('***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05
            else '†' if p < 0.10 else 'NS')


results = []
for y_col in RESPONSES:
    for x_col, use_log, label in PREDICTORS:
        r = run_ols(y_col, x_col, analysis_df, log_x=use_log)
        if r:
            r['label'] = label
            results.append(r)

res_df = pd.DataFrame(results)

print()
print(f"{'Response':<22} {'Predictor':<22} {'β_OLS':>9} {'p_OLS':>10} {'ρ_Spear':>8} {'p_rho':>10} {'n':>7}")
print('-' * 93)
for _, row in res_df.iterrows():
    if row['response'] == 'cwm_ko':
        sp = ''
    else:
        sp = '  '
    print(f"{row['response']:<22} {row['label']:<22} "
          f"{row['beta']:>+9.5f} {row['p_ols']:>10.4g}{sig(row['p_ols']):<3} "
          f"{row['rho_spearman']:>+8.4f} {row['p_spearman']:>10.4g}{sig(row['p_spearman']):<3} "
          f"{int(row['n']):>7}")

# ── Descriptive stats on key env variables ────────────────────────────────────
print("\n── Environmental variable coverage and ranges ──")
env_cols = ['csu_cu_bio', 'sci_ni', 'sci_cu', 'sci_co', 'soil_pH']
for col in env_cols:
    sub = analysis_df[col].dropna()
    if len(sub) > 0:
        print(f"  {col:<15}: n={len(sub):,}  mean={sub.mean():.4f}  "
              f"SD={sub.std():.4f}  range=[{sub.min():.4f}, {sub.max():.4f}]")

# ── Save results ──────────────────────────────────────────────────────────────
res_path = DATA / 'h3a_cwm_analysis_v2_results.csv'
res_df.to_csv(res_path, index=False)
print(f"\nSaved: {res_path}")

print("\n═══════════════════════════════════════")
print("H3a CWM v2 ANALYSIS COMPLETE")
print(f"  Samples: {len(analysis_df):,}")
print(f"  OLS models: {len(res_df)}")
print("═══════════════════════════════════════")

#!/usr/bin/env python3
"""
h3a_cwm_analysis.py

Community-weighted mean (CWM) metal-gene density analysis (H3a).
Tests whether sample-level CWM metal-gene density tracks environmental
bedrock metal concentrations (GeoROC) across soil/agricultural samples.

Taxonomy note: MicrobeAtlas OTUs use SILVA taxonomy; PGLS dataset uses GTDB.
Genus matching is by exact lowercase string — approximate, mismatch rate reported.

Spark compute: arkinlab.microbeatlas (OTU counts + metadata + environmental).
"""

import sys, os
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

sys.path.insert(0, '/opt/conda/lib/python3.13/site-packages')
import berdl_notebook_utils
spark = berdl_notebook_utils.get_spark_session()

DATA   = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data')
REPORT = Path('/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/report')

# ── Load genus density data ───────────────────────────────────────────────────
print("── Loading genus density data ──")
pgls_df = pd.read_csv(DATA / 'soil_sample_pgls_dataset.csv')
pgls_df['genus_lower'] = pgls_df['genus_lower'].str.lower().str.strip()
density_cols = ['ko_per_mb_primary', 'cofactor_per_mb', 'resistance_per_mb', 'mean_genome_mb']
pgls_sub = pgls_df[['genus_lower'] + density_cols].dropna(subset=['ko_per_mb_primary'])
print(f"  Genera with density data: {len(pgls_sub)}")

density_spark = spark.createDataFrame(pgls_sub)
density_spark.createOrReplaceTempView("genus_density")

# ── Compute CWM per sample (Spark) ────────────────────────────────────────────
print("── Computing genus-level relative abundances and CWM (Spark) ──")
print("   This aggregates 69M soil OTU rows — expect 3–8 minutes...")

cwm_sdf = spark.sql("""
WITH soil_samples AS (
    SELECT sample_id, SRS_Join_Key
    FROM arkinlab.microbeatlas.sample_metadata
    WHERE Env_Level_1 IN ('soil', 'agricultural')
),
-- Aggregate OTU counts to genus level per sample (SILVA taxonomy, field index 5)
otu_genus AS (
    SELECT
        ocl.sample_id,
        LOWER(TRIM(element_at(split(om.Tax, ';'), 6))) AS genus,
        SUM(ocl.count) AS genus_count
    FROM arkinlab.microbeatlas.otu_counts_long ocl
    JOIN arkinlab.microbeatlas.otu_metadata om ON ocl.otu_id = om.otu_id
    JOIN soil_samples ss ON ocl.sample_id = ss.sample_id
    WHERE size(split(om.Tax, ';')) >= 6
      AND TRIM(element_at(split(om.Tax, ';'), 6)) NOT IN
          ('', 'uncultured', 'unclassified', 'unknown', 'unidentified',
           'metagenome', 'Ambiguous_taxa', 'ambiguous_taxa')
      AND element_at(split(om.Tax, ';'), 6) IS NOT NULL
    GROUP BY ocl.sample_id,
             LOWER(TRIM(element_at(split(om.Tax, ';'), 6)))
),
sample_totals AS (
    SELECT sample_id, SUM(genus_count) AS total_count
    FROM otu_genus
    GROUP BY sample_id
),
-- Relative abundance (filter samples with >= 100 reads)
genus_ra AS (
    SELECT
        og.sample_id,
        og.genus,
        og.genus_count / st.total_count AS rel_abund
    FROM otu_genus og
    JOIN sample_totals st ON og.sample_id = st.sample_id
    WHERE st.total_count >= 100
),
-- CWM = sum over genera of (RA × density), for matched genera only
cwm_raw AS (
    SELECT
        ra.sample_id,
        SUM(ra.rel_abund * gd.ko_per_mb_primary)  AS cwm_ko,
        SUM(ra.rel_abund * gd.cofactor_per_mb)     AS cwm_cofactor,
        SUM(ra.rel_abund * gd.resistance_per_mb)   AS cwm_resistance,
        SUM(ra.rel_abund * gd.mean_genome_mb)      AS cwm_genome_mb,
        SUM(ra.rel_abund)                           AS coverage,
        COUNT(DISTINCT ra.genus)                    AS n_genera_matched
    FROM genus_ra ra
    JOIN genus_density gd ON ra.genus = gd.genus_lower
    GROUP BY ra.sample_id
)
SELECT * FROM cwm_raw
WHERE coverage >= 0.05   -- at least 5% of community matched to density data
""")

print("   Collecting CWM results...")
cwm_pdf = cwm_sdf.toPandas()
print(f"  Samples with CWM: {len(cwm_pdf)}")
if len(cwm_pdf) == 0:
    print("  ERROR: No CWM rows returned. Check join logic.")
    sys.exit(1)
print(f"  Coverage: mean={cwm_pdf['coverage'].mean():.3f}, "
      f"median={cwm_pdf['coverage'].median():.3f}, "
      f"SD={cwm_pdf['coverage'].std():.3f}")
print(f"  n_genera_matched: mean={cwm_pdf['n_genera_matched'].mean():.1f}")

# ── Join environmental metadata ───────────────────────────────────────────────
print("\n── Joining environmental metadata ──")

georoc_pdf = spark.sql("""
SELECT
    em.accession_id                     AS sample_id,
    em.lat,
    em.lon,
    em.GeoROC_Rocks_georoc_Cu_ppm       AS georoc_Cu,
    em.GeoROC_Rocks_georoc_Ni_ppm       AS georoc_Ni,
    em.GeoROC_Rocks_georoc_Zn_ppm       AS georoc_Zn,
    em.GeoROC_Rocks_georoc_Co_ppm       AS georoc_Co,
    em.GeoROC_Rocks_georoc_Cr_ppm       AS georoc_Cr,
    em.GeoROC_Rocks_georoc_Pb_ppm       AS georoc_Pb
FROM arkinlab.microbeatlas.enriched_metadata em
""").toPandas()

ph_pdf = spark.sql("""
SELECT
    sm.sample_id,
    g.olm_soil_ph_0cm_H2O               AS soil_pH,
    g.ERA5_mean_2m_air_temperature_K    AS temp_K
FROM arkinlab.microbeatlas.sample_metadata sm
JOIN arkinlab.microbeatlas.enriched_metadata_gee g ON sm.SRS_Join_Key = g.SRS_Join_Key
WHERE sm.Env_Level_1 IN ('soil', 'agricultural')
""").toPandas()

analysis_df = (cwm_pdf
               .merge(georoc_pdf, on='sample_id', how='left')
               .merge(ph_pdf, on='sample_id', how='left'))

print(f"  Total samples: {len(analysis_df)}")
print(f"  With GeoROC Cu: {analysis_df['georoc_Cu'].notna().sum()}")
print(f"  With GeoROC Ni: {analysis_df['georoc_Ni'].notna().sum()}")
print(f"  With GeoROC Zn: {analysis_df['georoc_Zn'].notna().sum()}")
print(f"  With soil pH:   {analysis_df['soil_pH'].notna().sum()}")
print(f"  With temp:      {analysis_df['temp_K'].notna().sum()}")

# Save sample-level data
sample_path = DATA / 'h3a_cwm_sample_data.csv'
analysis_df.to_csv(sample_path, index=False)
print(f"  Saved sample data: {sample_path}")


# ── OLS regressions: CWM ~ environmental metals ───────────────────────────────
print("\n── OLS regressions: CWM ~ log(metal) and CWM ~ soil_pH ──")


def run_ols(y_col, x_col, df, log_x=True):
    sub = df[[y_col, x_col, 'cwm_genome_mb']].dropna()
    if log_x:
        sub = sub[sub[x_col] > 0]
    if len(sub) < 30:
        return None
    y = sub[y_col].values
    x_raw = np.log(sub[x_col].values) if log_x else sub[x_col].values
    x_z = (x_raw - x_raw.mean()) / x_raw.std()
    slope, intercept, r, p, se = stats.linregress(x_z, y)
    # Spearman rho for robustness
    rho, p_rho = stats.spearmanr(x_raw, y)
    return {
        'response': y_col, 'predictor': x_col, 'log_x': log_x,
        'beta': slope, 'SE': se, 'p_ols': p, 'r_pearson': r,
        'rho_spearman': rho, 'p_spearman': p_rho,
        'n': len(sub),
    }


results = []
for y_col in ['cwm_ko', 'cwm_cofactor', 'cwm_resistance']:
    for x_col, use_log in [
        ('georoc_Cu', True), ('georoc_Ni', True), ('georoc_Zn', True),
        ('georoc_Co', True), ('georoc_Cr', True),
        ('soil_pH', False),
    ]:
        r = run_ols(y_col, x_col, analysis_df, log_x=use_log)
        if r:
            results.append(r)

res_df = pd.DataFrame(results)

def ps(p):
    return ('***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05
            else '†' if p < 0.10 else 'NS')

print()
print(f"{'Response':<22} {'Predictor':<12} {'β_OLS':>9} {'p_OLS':>10} {'ρ_Spear':>8} {'p_rho':>10} {'n':>7}")
print('-' * 80)
for _, row in res_df.iterrows():
    print(f"{row['response']:<22} {row['predictor']:<12} "
          f"{row['beta']:>+9.5f} {row['p_ols']:>10.4g}{ps(row['p_ols']):<3} "
          f"{row['rho_spearman']:>+8.4f} {row['p_spearman']:>10.4g}{ps(row['p_spearman']):<3} "
          f"{int(row['n']):>7}")

# ── Summary stats ─────────────────────────────────────────────────────────────
print("\n── CWM descriptive statistics ──")
for col in ['cwm_ko', 'cwm_cofactor', 'cwm_resistance']:
    sub = analysis_df[col].dropna()
    print(f"  {col}: mean={sub.mean():.4f} SD={sub.std():.4f} "
          f"median={sub.median():.4f} n={len(sub)}")

# ── Save results ─────────────────────────────────────────────────────────────
out_path = DATA / 'h3a_cwm_analysis_results.csv'
res_df.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Saved: {sample_path}")
print("\n═══════════════════════════════════════")
print("H3a CWM ANALYSIS COMPLETE")
print(f"  Samples analysed: {len(analysis_df)}")
print(f"  OLS models run: {len(res_df)}")
print("═══════════════════════════════════════")

#!/usr/bin/env python3
"""
cwm_eur_aus_replication.py — EUR and AUS CWM replication of USA V3 hits

Replication design:
  - Target KOs: 125 unique KOs from 75 USA V3 FDR-significant pairs (6-metal pool)
  - EUR: MicrobeAtlas soil samples + GEMAS measured metals (Cu,Pb,Ni,Cr,As,Cd,Hg + pH + TOC)
  - AUS: MicrobeAtlas soil samples + NGSA measured metals (Cu,Pb,Cr,As,Cd,Hg + field_pH + clay)
  - Simplified model vs V3: drops USA-specific covariates (SSURGO CEC/AWC/drainage/lith,
    EPA TRI, mine distance); keeps pH, clay, land cover, Shannon, phylum composition
  - Outputs: lm_input_EUR_{metal}.csv, lm_input_AUS_{metal}.csv
             lm_out_eur_{metal}.csv, lm_out_aus_{metal}.csv
             replication_summary.csv (EUR+AUS vs USA V3 agreement)

Run in JupyterHub with Spark Connect available.
"""
import os
import sys
import subprocess
import numpy as np
import pandas as pd
from pathlib import Path
from statsmodels.stats.multitest import multipletests

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO   = Path("/home/hmacgregor/BERIL-research-observatory")
PROJ   = REPO / "projects/microbeatlas_metal_ecology"
DATA   = PROJ / "data"
OUTDIR = DATA / "eur_aus_cwm"
USADIR = DATA / "usa_cwm"
SCRDIR = PROJ / "scripts"
LOG    = PROJ / "logs"
LOG.mkdir(exist_ok=True)

GEMAS_CSV = REPO / "projects/comprehensive_metal_ecology/data/env_cache/gemas.csv"
NGSA_CSV  = DATA / "ngsa_geochemistry.csv"
RSCRIPT   = "/home/hmacgregor/r_env/bin/Rscript"
R_MODEL   = SCRDIR / "lm_ns_full_model.R"

CACHE_EUR_SAMPLES = USADIR / "eur_soil_samples.csv"
CACHE_AUS_SAMPLES = USADIR / "aus_soil_samples.csv"

# ── 125 target KOs (union of 75 USA V3 FDR-sig pairs across 6 metals) ────────
TARGET_KOS = [
    'K00119','K00177','K00198','K00351','K00394','K00436','K00621','K00757',
    'K01163','K01271','K01598','K01615','K01699','K02082','K02190','K02241',
    'K02661','K02775','K03212','K03388','K03532','K03573','K03796','K03837',
    'K05739','K06001','K06039','K06212','K06219','K06323','K06860','K07026',
    'K07537','K07538','K07539','K07550','K08722','K09120','K09157','K09891',
    'K10108','K10194','K10535','K10670','K11261','K11358','K12264','K12529',
    'K13037','K13638','K13658','K13677','K13684','K13990','K14029','K14153',
    'K14196','K15022','K15063','K15066','K15527','K15534','K15657','K15896',
    'K15916','K16239','K16248','K16328','K16874','K17067','K17327','K17328',
    'K17382','K17474','K18355','K18356','K18357','K18371','K18652','K18653',
    'K18913','K18933','K19137','K19139','K19293','K19550','K19814','K19856',
    'K20218','K20327','K20432','K20436','K20489','K20497','K20509','K20850',
    'K21431','K21473','K21493','K21884','K21898','K22233','K22373','K22451',
    'K22553','K22928','K23086','K23371','K24694','K24695','K24696','K24697',
    'K25261','K25571','K25952','K25985','K26057','K26441','K26989','K27044',
    'K27191','K27196','K27264','K27265','K27882',
]
KO_LIST_SQL = "('" + "','".join(TARGET_KOS) + "')"
print(f"Target KOs: {len(TARGET_KOS)}")


# =============================================================================
# SECTION 1 — Spark session
# =============================================================================
import berdl_notebook_utils
spark = berdl_notebook_utils.get_spark_session()
print(f"Spark {spark.version} connected")


# =============================================================================
# SECTION 2 — Load pre-computed EUR/AUS sample lists and spatially thin
# =============================================================================
def thin_grid(df, lat_col='lat', lon_col='lon', cell_deg=0.45):
    """Keep one sample per 0.45° grid cell (same thinning as USA)."""
    df = df.copy()
    df['grid_lat'] = (df[lat_col] / cell_deg).round(0)
    df['grid_lon'] = (df[lon_col] / cell_deg).round(0)
    return df.drop_duplicates(subset=['grid_lat','grid_lon']).drop(
        columns=['grid_lat','grid_lon'])

eur_raw = pd.read_csv(CACHE_EUR_SAMPLES).rename(
    columns={'latitude':'lat','longitude':'lon'})
aus_raw = pd.read_csv(CACHE_AUS_SAMPLES).rename(
    columns={'latitude':'lat','longitude':'lon'})

eur_thin = thin_grid(eur_raw).reset_index(drop=True)
aus_thin = thin_grid(aus_raw).reset_index(drop=True)
print(f"EUR: {len(eur_raw)} raw → {len(eur_thin)} thinned (0.45°)")
print(f"AUS: {len(aus_raw)} raw → {len(aus_thin)} thinned (0.45°)")


# =============================================================================
# SECTION 3 — Compute CWM via Spark
# =============================================================================

def compute_cwm_region(spark, sample_ids, region_name, cache_path):
    """
    Compute CWM for 125 target KOs for a set of MicrobeAtlas sample_ids.
    Uses exact same join pattern as cwm_per_ko_usa_usgs.py.
    """
    if cache_path.exists():
        print(f"CWM {region_name}: loading from cache ({cache_path.name})")
        return pd.read_parquet(cache_path)

    ids_sql = "('" + "','".join(sample_ids) + "')"

    cwm_spark = spark.sql(f"""
        SELECT m.sample_id, m.lat, m.lon, kp.ko_id,
            SUM(CAST(o.count AS DOUBLE) * kp.prevalence)
              / SUM(CAST(o.count AS DOUBLE)) AS cwm,
            SUM(CAST(o.count AS DOUBLE)) AS matched_count
        FROM arkinlab.microbeatlas.otu_counts_long o
        JOIN (
            SELECT sample_id, lat, lon
            FROM arkinlab.microbeatlas.sample_metadata
            WHERE sample_id IN {ids_sql}
        ) m ON o.sample_id = m.sample_id
        JOIN arkinlab.microbeatlas.otu_metadata om ON o.otu_id = om.otu_id
        JOIN (
            SELECT num.genus_lower, num.ko_id,
                   CAST(num.n_with_ko AS DOUBLE) / CAST(den.n_total AS DOUBLE) AS prevalence
            FROM (
                SELECT LOWER(REGEXP_EXTRACT(sc.GTDB_taxonomy, 'g__([^;]+)', 1)) AS genus_lower,
                       x.accession AS ko_id,
                       COUNT(DISTINCT gc.gtdb_species_clade_id) AS n_with_ko
                FROM kbase.ke_pangenome.bakta_db_xrefs x
                JOIN kbase.ke_pangenome.gene_cluster gc
                    ON x.gene_cluster_id = gc.gene_cluster_id
                JOIN kbase.ke_pangenome.gtdb_species_clade sc
                    ON gc.gtdb_species_clade_id = sc.gtdb_species_clade_id
                WHERE x.db = 'KEGG' AND x.accession IN {KO_LIST_SQL}
                  AND sc.GTDB_taxonomy LIKE '%g__%'
                GROUP BY genus_lower, ko_id
            ) num
            JOIN (
                SELECT LOWER(REGEXP_EXTRACT(GTDB_taxonomy, 'g__([^;]+)', 1)) AS genus_lower,
                       COUNT(*) AS n_total
                FROM kbase.ke_pangenome.gtdb_species_clade
                WHERE GTDB_taxonomy LIKE '%g__%'
                GROUP BY genus_lower
            ) den ON num.genus_lower = den.genus_lower
        ) kp ON LOWER(element_at(SPLIT(om.tax, ';'), -1)) = kp.genus_lower
        WHERE om.tax IS NOT NULL AND SIZE(SPLIT(om.tax, ';')) >= 3
        GROUP BY m.sample_id, m.lat, m.lon, kp.ko_id
    """)

    cwm_long = cwm_spark.toPandas()
    cwm_long.attrs = {}
    cwm_long.to_parquet(cache_path, index=False)
    print(f"CWM {region_name}: {len(cwm_long):,} rows, {cwm_long['sample_id'].nunique()} samples")
    return cwm_long


CACHE_EUR_CWM = OUTDIR / "cwm_long_eur.parquet"
CACHE_AUS_CWM = OUTDIR / "cwm_long_aus.parquet"

eur_cwm = compute_cwm_region(spark, eur_thin['sample_id'].tolist(), "EUR", CACHE_EUR_CWM)
aus_cwm = compute_cwm_region(spark, aus_thin['sample_id'].tolist(), "AUS", CACHE_AUS_CWM)


# =============================================================================
# SECTION 4 — Shannon diversity and phylum composition
# =============================================================================

def get_diversity_phylum(spark, sample_ids, region_name, cache_path):
    """Shannon H and 8-phylum relative abundance for a set of samples."""
    if cache_path.exists():
        print(f"Diversity {region_name}: loading from cache")
        return pd.read_parquet(cache_path)

    ids_sql = "('" + "','".join(sample_ids) + "')"

    div_spark = spark.sql(f"""
        SELECT o.sample_id,
               -- Shannon H
               -SUM(p * LOG(p)) AS shannon,
               -- top phyla relative abundance
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%ACIDOBACTERIOTA%'
                        THEN p ELSE 0 END) AS phylum_Acidobacteriota,
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%ACTINOBACTERIOTA%'
                        THEN p ELSE 0 END) AS phylum_Actinobacteriota,
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%BACTEROIDOTA%'
                        THEN p ELSE 0 END) AS phylum_Bacteroidota,
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%CHLOROFLEXOTA%'
                        THEN p ELSE 0 END) AS phylum_Chloroflexota,
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%FIRMICUTES%'
                        THEN p ELSE 0 END) AS phylum_Firmicutes,
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%GAMMAPROTEOBACTERIA%'
                        OR UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%PROTEOBACTERIA%'
                        THEN p ELSE 0 END) AS phylum_Proteobacteria,
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%PLANCTOMYCETOTA%'
                        THEN p ELSE 0 END) AS phylum_Planctomycetota,
               SUM(CASE WHEN UPPER(SPLIT_PART(om.tax, ';', 2)) LIKE '%VERRUCOMICROBIOTA%'
                        THEN p ELSE 0 END) AS phylum_Verrucomicrobiota
        FROM (
            SELECT o.sample_id, o.otu_id,
                   CAST(o.count AS DOUBLE) / SUM(CAST(o.count AS DOUBLE))
                     OVER (PARTITION BY o.sample_id) AS p
            FROM arkinlab.microbeatlas.otu_counts_long o
            WHERE o.sample_id IN {ids_sql}
        ) o
        JOIN arkinlab.microbeatlas.otu_metadata om ON o.otu_id = om.otu_id
        WHERE om.tax IS NOT NULL
        GROUP BY o.sample_id
    """)

    div = div_spark.toPandas()
    div.attrs = {}
    div.to_parquet(cache_path, index=False)
    print(f"Diversity {region_name}: {len(div)} samples")
    return div


CACHE_EUR_DIV = OUTDIR / "diversity_eur.parquet"
CACHE_AUS_DIV = OUTDIR / "diversity_aus.parquet"

eur_div = get_diversity_phylum(spark, eur_thin['sample_id'].tolist(), "EUR", CACHE_EUR_DIV)
aus_div = get_diversity_phylum(spark, aus_thin['sample_id'].tolist(), "AUS", CACHE_AUS_DIV)


# =============================================================================
# SECTION 5 — EarthEnv land cover
# =============================================================================

def get_earthenv_lc(spark, sample_df, region_name, cache_path, lat_col='lat', lon_col='lon'):
    """
    Join to EarthEnv land cover at 0.25° grid.
    Classes: 1-4=forest, 7=cultivated, 9=urban, 11=barren.
    """
    if cache_path.exists():
        print(f"EarthEnv {region_name}: loading from cache")
        return pd.read_parquet(cache_path)

    # Build min/max bounds
    lat_min = float(sample_df[lat_col].min()) - 0.5
    lat_max = float(sample_df[lat_col].max()) + 0.5
    lon_min = float(sample_df[lon_col].min()) - 0.5
    lon_max = float(sample_df[lon_col].max()) + 0.5

    lc_spark = spark.sql(f"""
        SELECT lat, lon,
               CAST(landcover_class_1_pct AS DOUBLE)
                 + CAST(landcover_class_2_pct AS DOUBLE)
                 + CAST(landcover_class_3_pct AS DOUBLE)
                 + CAST(landcover_class_4_pct AS DOUBLE) AS lc_forest_pct,
               CAST(landcover_class_7_pct AS DOUBLE) AS lc_cultivated_pct,
               CAST(landcover_class_9_pct AS DOUBLE) AS lc_urban_pct,
               CAST(landcover_class_11_pct AS DOUBLE) AS lc_barren_pct
        FROM arkinlab.envdbs.earthenv_master
        WHERE lat BETWEEN {lat_min} AND {lat_max}
          AND lon BETWEEN {lon_min} AND {lon_max}
          AND landcover_class_7_pct IS NOT NULL
    """)
    lc = lc_spark.toPandas()
    lc.attrs = {}

    # Nearest-neighbour join at 0.25° (EarthEnv grid)
    from scipy.spatial import cKDTree
    tree = cKDTree(lc[['lat','lon']].values)
    dists, idxs = tree.query(sample_df[[lat_col, lon_col]].values, k=1)

    result = sample_df[['sample_id', lat_col, lon_col]].copy()
    for col in ['lc_forest_pct','lc_cultivated_pct','lc_urban_pct','lc_barren_pct']:
        result[col] = lc[col].values[idxs]
    result.loc[dists > 0.5, ['lc_forest_pct','lc_cultivated_pct',
                              'lc_urban_pct','lc_barren_pct']] = np.nan

    result.attrs = {}
    result.to_parquet(cache_path, index=False)
    print(f"EarthEnv {region_name}: {result['lc_forest_pct'].notna().sum()} / {len(result)} matched")
    return result


CACHE_EUR_LC = OUTDIR / "earthenv_eur.parquet"
CACHE_AUS_LC = OUTDIR / "earthenv_aus.parquet"

eur_lc = get_earthenv_lc(spark, eur_thin, "EUR", CACHE_EUR_LC)
aus_lc = get_earthenv_lc(spark, aus_thin, "AUS", CACHE_AUS_LC)


# =============================================================================
# SECTION 6 — SoilGrids clay for EUR (AUS has clay from NGSA directly)
# =============================================================================

def get_soilgrids_clay(spark, sample_df, region_name, cache_path, lat_col='lat', lon_col='lon'):
    """
    Estimate clay_pct from SoilGrids sand_0cm + silt_0cm for EUR samples.
    clay ≈ 100 - sand - silt. pH is not populated in soilgrids_master.
    """
    if cache_path.exists():
        print(f"SoilGrids {region_name}: loading from cache")
        return pd.read_parquet(cache_path)

    lat_min = float(sample_df[lat_col].min()) - 0.25
    lat_max = float(sample_df[lat_col].max()) + 0.25
    lon_min = float(sample_df[lon_col].min()) - 0.25
    lon_max = float(sample_df[lon_col].max()) + 0.25

    sg_spark = spark.sql(f"""
        SELECT lat, lon,
               CAST(sand_0cm AS DOUBLE) AS sand_0cm,
               CAST(silt_0cm AS DOUBLE) AS silt_0cm
        FROM arkinlab.envdbs.soilgrids_master
        WHERE lat BETWEEN {lat_min} AND {lat_max}
          AND lon BETWEEN {lon_min} AND {lon_max}
          AND sand_0cm IS NOT NULL
    """)
    sg = sg_spark.toPandas()
    sg.attrs = {}

    if len(sg) == 0:
        print(f"WARNING: SoilGrids {region_name}: no rows in bounds!")
        result = sample_df[['sample_id', lat_col, lon_col]].copy()
        result['clay_pct'] = np.nan
        result.attrs = {}
        result.to_parquet(cache_path, index=False)
        return result

    # clay ≈ 100 - sand - silt (clip to [0, 100])
    sg['clay_pct'] = (100.0 - sg['sand_0cm'] - sg['silt_0cm']).clip(0, 100)

    # Nearest-neighbour join (within 0.25° = ~28 km)
    from scipy.spatial import cKDTree
    tree = cKDTree(sg[['lat','lon']].values)
    dists, idxs = tree.query(sample_df[[lat_col, lon_col]].values, k=1)
    result = sample_df[['sample_id', lat_col, lon_col]].copy()
    result['clay_pct'] = sg['clay_pct'].values[idxs]
    result.loc[dists > 0.25, 'clay_pct'] = np.nan  # too far

    result.attrs = {}
    result.to_parquet(cache_path, index=False)
    print(f"SoilGrids {region_name}: clay_pct non-NA: {result['clay_pct'].notna().sum()} / {len(result)}")
    return result


CACHE_EUR_CLAY = OUTDIR / "soilgrids_clay_eur.parquet"
eur_clay = get_soilgrids_clay(spark, eur_thin, "EUR", CACHE_EUR_CLAY)


# =============================================================================
# SECTION 7 — Haversine spatial join to GEMAS (EUR) and NGSA (AUS)
# =============================================================================

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1))*np.cos(np.radians(lat2))*np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))


def join_nearest_metal(sample_df, metal_df, metal_cols, lat_col='lat', lon_col='lon',
                       metal_lat='lat', metal_lon='lon', max_km=25.0):
    """Join metal concentrations to samples by nearest neighbour within max_km."""
    from scipy.spatial import cKDTree
    tree = cKDTree(np.radians(metal_df[[metal_lat, metal_lon]].values))
    sample_rad = np.radians(sample_df[[lat_col, lon_col]].values)
    dists_rad, idxs = tree.query(sample_rad, k=1)
    dists_km = dists_rad * 6371.0
    result = sample_df[['sample_id', lat_col, lon_col]].copy()
    for col in metal_cols:
        result[col] = metal_df[col].values[idxs]
        result.loc[dists_km > max_km, col] = np.nan
    result['nearest_metal_km'] = dists_km
    n_matched = (dists_km <= max_km).sum()
    print(f"  Metal join: {n_matched}/{len(sample_df)} within {max_km} km "
          f"(median {np.median(dists_km[dists_km<=max_km]):.1f} km)")
    return result


# EUR — GEMAS (25 km radius)
gemas = pd.read_csv(GEMAS_CSV)
eur_metals_cols = ['gemas_Cu','gemas_Pb','gemas_Cr','gemas_As','gemas_Cd','gemas_Hg',
                   'gemas_pH','gemas_TOC']
eur_metals = join_nearest_metal(
    eur_thin, gemas, eur_metals_cols, max_km=25.0)

# AUS — NGSA (50 km radius)
ngsa = pd.read_csv(NGSA_CSV)
aus_metals_cols = ['Cu_ppm','Pb_ppm','Cr_ppm','As_ppm','Cd_ppm','Hg_ppm',
                   'field_pH','clay_pct','sand_pct']
aus_metals = join_nearest_metal(
    aus_thin, ngsa, aus_metals_cols, metal_lat='lat', metal_lon='lon', max_km=50.0)

# AUS pH — NGSA field_pH has 0% coverage; use MicrobeAtlas measured sample pH instead
aus_ids_sql = "('" + "','".join(aus_thin['sample_id'].tolist()) + "')"
CACHE_AUS_PH = OUTDIR / "aus_sample_ph.parquet"
if CACHE_AUS_PH.exists():
    print("AUS pH: loading from cache")
    aus_ph = pd.read_parquet(CACHE_AUS_PH)
else:
    aus_ph_spark = spark.sql(f"""
        SELECT sample_id, CAST(ph AS DOUBLE) AS ph_ssurgo
        FROM arkinlab.microbeatlas.sample_metadata
        WHERE sample_id IN {aus_ids_sql}
          AND ph IS NOT NULL
    """)
    aus_ph = aus_ph_spark.toPandas()
    aus_ph.attrs = {}
    aus_ph.to_parquet(CACHE_AUS_PH, index=False)
n_aus_ph = aus_ph['ph_ssurgo'].notna().sum()
print(f"AUS MicrobeAtlas pH: {n_aus_ph}/{len(aus_thin)} samples have measured pH")

# Merge MicrobeAtlas pH into aus_metals (overrides NGSA field_pH which is all-NA)
aus_metals = aus_metals.merge(aus_ph, on='sample_id', how='left')


# =============================================================================
# SECTION 8 — Assemble covariate matrices
# =============================================================================

def assemble_covariate(sample_thin, cwm_long, div_df, lc_df, metals_df,
                       ph_col, clay_col, region_name, extra_clay_df=None):
    """Build wide-format covariate matrix merged with CWM (one row per sample×KO)."""

    # Pivot CWM long → wide on sample_id
    cwm_wide = cwm_long.pivot_table(
        index='sample_id', columns='ko_id', values='cwm').reset_index()
    cwm_wide.columns.name = None

    # Base: sample coords
    base = sample_thin[['sample_id','lat','lon']].copy()

    # Merge diversity
    base = base.merge(div_df, on='sample_id', how='left')

    # Merge land cover
    base = base.merge(lc_df[['sample_id','lc_forest_pct','lc_cultivated_pct',
                               'lc_urban_pct','lc_barren_pct']], on='sample_id', how='left')

    # Merge metal concentrations and pH
    base = base.merge(metals_df.drop(columns=['lat','lon','nearest_metal_km'], errors='ignore'),
                      on='sample_id', how='left')

    # Standardize pH column name (R model looks for ph_ssurgo as primary source)
    if ph_col in base.columns and ph_col != 'ph_ssurgo':
        base['ph_ssurgo'] = base[ph_col]

    # Standardize clay column name
    if clay_col and clay_col in base.columns and clay_col != 'clay_pct':
        base['clay_pct'] = base[clay_col]

    # Extra clay (e.g. from SoilGrids for EUR)
    if extra_clay_df is not None and 'clay_pct' not in base.columns:
        base = base.merge(extra_clay_df[['sample_id','clay_pct']], on='sample_id', how='left')
    elif extra_clay_df is not None:
        base['clay_pct'] = base['clay_pct'].fillna(
            extra_clay_df.set_index('sample_id')['clay_pct'].reindex(base['sample_id']).values)

    # Merge CWM wide
    full = base.merge(cwm_wide, on='sample_id', how='inner')
    print(f"{region_name} covariate matrix: {len(full)} samples × {full.shape[1]} columns")
    return base, full


eur_base, eur_full = assemble_covariate(
    eur_thin, eur_cwm, eur_div, eur_lc, eur_metals,
    ph_col='gemas_pH', clay_col=None, region_name='EUR',
    extra_clay_df=eur_clay)

aus_base, aus_full = assemble_covariate(
    aus_thin, aus_cwm, aus_div, aus_lc, aus_metals,
    ph_col='ph_ssurgo', clay_col='clay_pct', region_name='AUS',
    extra_clay_df=None)

eur_base.attrs = {}; eur_base.to_parquet(OUTDIR / "covariate_eur.parquet", index=False)
aus_base.attrs = {}; aus_base.to_parquet(OUTDIR / "covariate_aus.parquet", index=False)


# =============================================================================
# SECTION 9 — Write lm_input CSVs per metal
# =============================================================================

def write_lm_inputs(full_wide, base_cov, metal_mapping, region_name, outdir,
                    min_matched=30):
    """
    Build long-format lm_input_*.csv per metal.
    Columns: sample_id, lat, lon, ko_id, cwm, log10_metal, ph_ssurgo, clay_pct,
             lc_*, shannon, phylum_*
    """
    ko_cols = [c for c in full_wide.columns if c.startswith('K')]
    cov_cols = ['sample_id','lat','lon','ph_ssurgo','clay_pct',
                'lc_forest_pct','lc_cultivated_pct','lc_urban_pct','lc_barren_pct',
                'shannon'] + [c for c in full_wide.columns if c.startswith('phylum_')]

    written = {}
    for metal_label, metal_col in metal_mapping.items():
        if metal_col not in full_wide.columns:
            print(f"  SKIP {metal_label}: no column {metal_col}")
            continue

        cov_subset = full_wide[cov_cols + [metal_col]].dropna(subset=[metal_col])
        if len(cov_subset) < min_matched:
            print(f"  SKIP {metal_label}: only {len(cov_subset)} matched samples")
            continue

        cov_subset = cov_subset.copy()
        cov_subset['log10_metal'] = np.log10(pd.to_numeric(
            cov_subset[metal_col], errors='coerce').clip(lower=1e-6))
        cov_subset = cov_subset.drop(columns=[metal_col])

        # Melt KO columns to long format
        lm_long_parts = []
        for ko in ko_cols:
            ko_vals = full_wide.set_index('sample_id')[ko].dropna()
            matched = cov_subset[cov_subset['sample_id'].isin(ko_vals.index)].copy()
            if len(matched) < min_matched:
                continue
            matched['ko_id'] = ko
            matched['cwm'] = ko_vals.reindex(matched['sample_id'].values).values
            lm_long_parts.append(matched)

        if not lm_long_parts:
            print(f"  SKIP {metal_label}: no KOs with ≥{min_matched} matched samples")
            continue

        lm_long = pd.concat(lm_long_parts, ignore_index=True)
        lm_long['metal'] = metal_label
        out_path = outdir / f"lm_input_{region_name}_{metal_label}.csv"
        lm_long.attrs = {}
        lm_long.to_csv(out_path, index=False)
        written[metal_label] = out_path
        n_ko = lm_long['ko_id'].nunique()
        n_samp = lm_long['sample_id'].nunique()
        print(f"  {metal_label}: {n_samp} samples × {n_ko} KOs → {out_path.name}")

    return written


EUR_METALS = {
    'As': 'gemas_As', 'Cd': 'gemas_Cd', 'Cr': 'gemas_Cr',
    'Cu': 'gemas_Cu', 'Hg': 'gemas_Hg', 'Pb': 'gemas_Pb',
}
AUS_METALS = {
    'As': 'As_ppm', 'Cd': 'Cd_ppm', 'Cr': 'Cr_ppm',
    'Cu': 'Cu_ppm', 'Hg': 'Hg_ppm', 'Pb': 'Pb_ppm',
}

print("\n--- Writing EUR lm_inputs ---")
eur_inputs = write_lm_inputs(eur_full, eur_base, EUR_METALS, "EUR", OUTDIR)

print("\n--- Writing AUS lm_inputs ---")
aus_inputs = write_lm_inputs(aus_full, aus_base, AUS_METALS, "AUS", OUTDIR)


# =============================================================================
# SECTION 10 — Run R model for each region/metal
# =============================================================================

def run_r_model(region, metal, in_path, out_path, mc_cores=4):
    """Run lm_ns_full_model.R via subprocess."""
    if out_path.exists():
        print(f"  {region} {metal}: already done")
        return True
    env = os.environ.copy()
    env['MC_CORES'] = str(mc_cores)
    cmd = [RSCRIPT, str(R_MODEL), str(in_path), metal, str(out_path)]
    log_path = LOG / f"lm_eur_aus_{region}_{metal}.log"
    print(f"  Running {region} {metal}...")
    with open(log_path, 'w') as logf:
        ret = subprocess.run(cmd, env=env, stdout=logf, stderr=logf)
    if ret.returncode != 0:
        print(f"  ERROR {region} {metal} — see {log_path}")
        return False
    print(f"  Done {region} {metal}")
    return True


print("\n--- Running EUR R models ---")
eur_outputs = {}
for metal, in_path in eur_inputs.items():
    out_path = OUTDIR / f"lm_out_EUR_{metal}.csv"
    ok = run_r_model("EUR", metal, in_path, out_path)
    if ok:
        eur_outputs[metal] = out_path

print("\n--- Running AUS R models ---")
aus_outputs = {}
for metal, in_path in aus_inputs.items():
    out_path = OUTDIR / f"lm_out_AUS_{metal}.csv"
    ok = run_r_model("AUS", metal, in_path, out_path)
    if ok:
        aus_outputs[metal] = out_path


# =============================================================================
# SECTION 11 — Replication analysis
# =============================================================================

def load_region_results(outputs_dict, region):
    dfs = []
    for metal, path in outputs_dict.items():
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df['metal'] = metal
        df['region'] = region
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


eur_res = load_region_results(eur_outputs, "EUR")
aus_res = load_region_results(aus_outputs, "AUS")

# Pool BH-FDR within each region
def pool_fdr(df, p_col='p_metal_full', q_col='q_BH', min_n=30):
    valid = df[df[p_col].notna() & (df.get('n', 9999) >= min_n)].copy()
    if len(valid) == 0:
        return df
    _, q, _, _ = multipletests(valid[p_col].values, method='fdr_bh')
    valid[q_col] = q
    return df.merge(valid[['ko_id','metal',q_col]], on=['ko_id','metal'], how='left')

if len(eur_res) > 0:
    eur_res = pool_fdr(eur_res)
    eur_sig = eur_res[eur_res['q_BH'].fillna(1) < 0.05]
    print(f"\nEUR FDR<0.05: {len(eur_sig)} hits")
    if len(eur_sig) > 0:
        print(eur_sig.groupby('metal')['ko_id'].count())

if len(aus_res) > 0:
    aus_res = pool_fdr(aus_res)
    aus_sig = aus_res[aus_res['q_BH'].fillna(1) < 0.05]
    print(f"AUS FDR<0.05: {len(aus_sig)} hits")
    if len(aus_sig) > 0:
        print(aus_sig.groupby('metal')['ko_id'].count())


# Load USA V3 results for comparison
usa_dfs = []
for metal in ['As','Cd','Cr','Cu','Hg','Pb']:
    p = USADIR / f"lm_out_v3_{metal}.csv"
    if p.exists():
        d = pd.read_csv(p); d['metal'] = metal; usa_dfs.append(d)
usa_res = pd.concat(usa_dfs, ignore_index=True)
valid_usa = usa_res[usa_res['p_metal_full'].notna() & (usa_res['n'] >= 30)].copy()
_, q_usa, _, _ = multipletests(valid_usa['p_metal_full'].values, method='fdr_bh')
valid_usa['q_BH'] = q_usa
usa_sig = valid_usa[valid_usa['q_BH'] < 0.05][['ko_id','metal','beta_sign']].copy()
print(f"\nUSA V3 FDR<0.05: {len(usa_sig)} pairs")

# Replication table: for each USA hit, check EUR and AUS
rows = []
for _, row in usa_sig.iterrows():
    ko, metal, usa_sign = row['ko_id'], row['metal'], row['beta_sign']
    r = {'ko_id': ko, 'metal': metal, 'usa_beta_sign': usa_sign}
    for region, res_df in [('EUR', eur_res), ('AUS', aus_res)]:
        if len(res_df) == 0:
            r[f'{region}_q'] = np.nan; r[f'{region}_sign'] = np.nan
            continue
        hit = res_df[(res_df['ko_id']==ko) & (res_df['metal']==metal)]
        if len(hit) == 0:
            r[f'{region}_q'] = np.nan; r[f'{region}_sign'] = np.nan
        else:
            r[f'{region}_q'] = hit['q_BH'].values[0] if 'q_BH' in hit else np.nan
            r[f'{region}_sign'] = hit['beta_sign'].values[0] if 'beta_sign' in hit else np.nan
    rows.append(r)

rep = pd.DataFrame(rows)
rep['EUR_rep'] = (rep['EUR_q'] < 0.05) & (rep['EUR_sign'] == rep['usa_beta_sign'])
rep['AUS_rep'] = (rep['AUS_q'] < 0.05) & (rep['AUS_sign'] == rep['usa_beta_sign'])
rep['any_rep'] = rep['EUR_rep'] | rep['AUS_rep']

rep.attrs = {}
rep.to_csv(OUTDIR / "replication_summary.csv", index=False)

print("\n=== REPLICATION SUMMARY ===")
print(f"USA V3 hits tested: {len(rep)}")
print(f"Replicated in EUR (same direction, q<0.05): {rep['EUR_rep'].sum()}")
print(f"Replicated in AUS (same direction, q<0.05): {rep['AUS_rep'].sum()}")
print(f"Replicated in either: {rep['any_rep'].sum()}")
print(f"\nTop replicated hits:")
any_rep = rep[rep['any_rep']].sort_values(['metal','ko_id'])
if len(any_rep) > 0:
    print(any_rep[['metal','ko_id','usa_beta_sign','EUR_q','AUS_q']].to_string(index=False))
print(f"\nSaved: {OUTDIR / 'replication_summary.csv'}")


# =============================================================================
# SECTION 12 — Spatial effective sample size (pESS) per region
# =============================================================================
# pESS corrects for spatial autocorrelation among geographic sites.
# Formula: n_eff = n × (1 - I) / (1 + I) [Griffith 2005, similar to Clifford 1989]
# Moran's I computed on Shannon diversity using binary spatial weights (W = 1 within
# 250 km, 0 beyond); row-standardised. Shannon used as proxy for community composition
# rather than computing per-KO — this gives the site-level spatial independence.

def compute_spatial_ess(sample_df, div_df, var_col='shannon', threshold_km=250.0,
                        lat_col='lat', lon_col='lon', label=''):
    """
    Compute spatial ESS (pESS) using Moran's I on a continuous community variable.
    Returns dict with n, Moran_I, n_eff, n_neighbours_mean.
    """
    from scipy.spatial import cKDTree

    merged = sample_df[['sample_id', lat_col, lon_col]].merge(
        div_df[['sample_id', var_col]], on='sample_id', how='inner').dropna(subset=[var_col])
    n = len(merged)
    if n < 4:
        return {'label': label, 'n': n, 'moran_I': np.nan, 'n_eff': np.nan}

    coords_rad = np.radians(merged[[lat_col, lon_col]].values)
    # Convert threshold to radians on sphere
    thresh_rad = threshold_km / 6371.0

    tree = cKDTree(coords_rad)
    pairs = tree.query_pairs(thresh_rad, output_type='ndarray')

    if len(pairs) == 0:
        return {'label': label, 'n': n, 'moran_I': 0.0, 'n_eff': n}

    z = merged[var_col].values - merged[var_col].mean()
    z2 = (z ** 2).sum()

    # Build row-standardised weight matrix as sparse accumulation
    W_row = np.zeros(n)  # row sums for standardisation
    WZ = np.zeros(n)     # Σ_j w_ij * z_j (to be row-standardised)

    for i, j in pairs:
        W_row[i] += 1
        W_row[j] += 1
    W_row = np.where(W_row == 0, 1, W_row)  # avoid /0 for isolated points

    for i, j in pairs:
        WZ[i] += z[j] / W_row[i]
        WZ[j] += z[i] / W_row[j]

    S0 = len(pairs) * 2  # sum of all weights before row-standardisation
    moran_I = (n / S0) * (z @ WZ) / z2

    n_eff = n * (1 - moran_I) / (1 + moran_I)
    n_eff = max(1.0, min(n_eff, n))

    n_nbrs_mean = (W_row * (W_row != 1)).mean()  # restore to raw counts
    # Re-fetch raw neighbour counts (W_row was raw counts before masking)
    raw_Wrow = np.zeros(n)
    for i, j in pairs:
        raw_Wrow[i] += 1; raw_Wrow[j] += 1
    n_nbrs_mean = raw_Wrow.mean()

    print(f"  {label}: n={n}, Moran I={moran_I:.3f}, n_eff={n_eff:.1f}, "
          f"mean neighbours={n_nbrs_mean:.1f}")
    return {'label': label, 'n': n, 'moran_I': round(moran_I, 4),
            'n_eff': round(n_eff, 1), 'n_neighbours_mean': round(n_nbrs_mean, 1)}


print("\n=== SPATIAL EFFECTIVE SAMPLE SIZE (pESS) ===")
pess_rows = []
# USA (634 thinned sites — compute from usa_cwm covariate matrix which has Shannon)
usa_cov = pd.read_csv(USADIR / "covariate_matrix_634_v2.csv")
usa_cov_thin = usa_cov[['sample_id','lat','lon','shannon']].dropna(subset=['shannon'])
pess_usa = compute_spatial_ess(
    usa_cov_thin, usa_cov_thin.rename(columns={'shannon':'shannon'}),
    var_col='shannon', threshold_km=250, label='USA')
pess_rows.append(pess_usa)

# EUR
pess_eur = compute_spatial_ess(eur_thin, eur_div, var_col='shannon',
                                threshold_km=250, label='EUR')
pess_rows.append(pess_eur)

# AUS
pess_aus = compute_spatial_ess(aus_thin, aus_div, var_col='shannon',
                                threshold_km=250, label='AUS')
pess_rows.append(pess_aus)

pess_df = pd.DataFrame(pess_rows)
pess_df.attrs = {}
pess_df.to_csv(OUTDIR / "spatial_ess.csv", index=False)
print(f"\nSaved: {OUTDIR / 'spatial_ess.csv'}")
print(pess_df.to_string(index=False))
print("\nDone.")

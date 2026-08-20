#!/usr/bin/env python3
"""
Fetch ALL arkinlab.envdbs spatial layers + GeoROC bedrock metals, spatially
join to 1,084 MAG genome locations, save expanded covariate file.

Tables used:
  - arkinlab.envdbs.gemas               (4,343)  — European soil metals (AR method)
  - arkinlab.envdbs.epa_tri_metals       (373K)  — US toxic releases
  - arkinlab.envdbs.science_2025_global_soil_toxic_metals (2M) — global soil metal HQ
  - arkinlab.envdbs.ecotapestry_lithology_0_25deg (339K) — bedrock lithology
  - arkinlab.envdbs.soiltemp             (381K)  — measured soil temperature
  - arkinlab.envdbs.etopo1_elevation     (2.1M)  — elevation
  - arkinlab.envdbs.cmmi_ores            (29K)   — ore deposit geochemistry
  - arkinlab.envdbs.mining_operations    (8.5K)  — mine locations
  - arkinlab.envdbs.usgs_ree_occurrences (3.1K)  — REE deposits
  - arkinlab.envdbs.ngsa_geochemistry    (1.3K)  — Australian soil metals
  - arkinlab.envdbs.global_landcover_esa_2_0deg (16K) — ESA land cover class
  - arkinlab.envdbs.igsd_137cs_inventory (711)  — Cs-137 soil deposition
  - arkinlab_microbeatlas.enriched_metadata      — GeoROC bedrock metals

Spatial join: KD-tree nearest-neighbor within MAX_DIST_KM.
Output: data/genome_env_covariates_full.csv
"""
import os
for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(var, '1')

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import cKDTree

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / 'data'
CACHE_DIR = DATA / 'env_cache'
CACHE_DIR.mkdir(exist_ok=True)

ENVDBS_CACHE = CACHE_DIR / 'envdbs_layers.npz'
OUT = DATA / 'genome_env_covariates_full.csv'

MAX_DIST_DEG = 0.5
EARTH_KM_PER_DEG = 111.0

def safe_double(col_name):
    return f"TRY_CAST({col_name} AS DOUBLE)"

# ── Load genome locations ────────────────────────────────────────────────
print("Loading genome locations...", flush=True)
mags = pd.read_csv(DATA / 'genome_coords.csv')
unique_locs = mags[['latitude', 'longitude']].drop_duplicates().reset_index(drop=True)
print(f"  {len(mags):,} MAGs, {len(unique_locs):,} unique locations", flush=True)

# ── Connect to Spark ────────────────────────────────────────────────────
print("\nConnecting to Spark...", flush=True)
from berdl_notebook_utils import get_spark_session
spark = get_spark_session()
print("  Spark connected.", flush=True)


def kd_nearest(locs_df, ref_df, ref_lat='lat', ref_lon='lon',
               value_cols=None, max_dist_deg=MAX_DIST_DEG, prefix=''):
    """KD-tree nearest-neighbor join from genome locs to reference grid."""
    ref = ref_df.dropna(subset=[ref_lat, ref_lon]).copy()
    if len(ref) == 0:
        print(f"    SKIP: no valid coords in reference", flush=True)
        for c in (value_cols or []):
            locs_df[prefix + c] = np.nan
        return locs_df

    kd = cKDTree(ref[[ref_lat, ref_lon]].values)
    dist, idx = kd.query(locs_df[['latitude', 'longitude']].values, k=1)
    for c in (value_cols or []):
        vals = ref[c].values[idx]
        locs_df[prefix + c] = np.where(dist <= max_dist_deg, vals, np.nan)
    n = locs_df[prefix + (value_cols[0] if value_cols else '')].notna().sum()
    print(f"    Matched {n}/{len(locs_df)} locs within {max_dist_deg}°", flush=True)
    return locs_df


def kd_count_within(locs_df, ref_df, ref_lat='lat', ref_lon='lon',
                    radius_deg=0.5, col_name='count'):
    """Count reference points within radius_deg of each genome location."""
    ref = ref_df.dropna(subset=[ref_lat, ref_lon])
    if len(ref) == 0:
        locs_df[col_name] = 0
        return locs_df
    kd = cKDTree(ref[[ref_lat, ref_lon]].values)
    counts = kd.query_ball_point(locs_df[['latitude', 'longitude']].values,
                                 r=radius_deg)
    locs_df[col_name] = [len(c) for c in counts]
    print(f"    {col_name}: mean={locs_df[col_name].mean():.1f}, "
          f"max={locs_df[col_name].max()}", flush=True)
    return locs_df


def kd_min_distance(locs_df, ref_df, ref_lat='lat', ref_lon='lon',
                    col_name='min_dist_deg'):
    """Minimum distance (in degrees) to nearest reference point."""
    ref = ref_df.dropna(subset=[ref_lat, ref_lon])
    if len(ref) == 0:
        locs_df[col_name] = np.nan
        return locs_df
    kd = cKDTree(ref[[ref_lat, ref_lon]].values)
    dist, _ = kd.query(locs_df[['latitude', 'longitude']].values, k=1)
    locs_df[col_name] = dist
    print(f"    {col_name}: median={np.median(dist):.2f}° "
          f"({np.median(dist)*EARTH_KM_PER_DEG:.0f} km)", flush=True)
    return locs_df


result = unique_locs.copy()

# ════════════════════════════════════════════════════════════════════════
# 1. GeoROC bedrock metals (via enriched_metadata spatial bins)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'georoc_grid.csv'
if cache_f.exists():
    print("\n[1/10] GeoROC: loading cache...", flush=True)
    georoc = pd.read_csv(cache_f)
else:
    print("\n[1/10] GeoROC: querying enriched_metadata...", flush=True)
    georoc_sql = f"""
        SELECT
            ROUND({safe_double('lat')} / 0.25) * 0.25 AS lat,
            ROUND({safe_double('lon')} / 0.25) * 0.25 AS lon,
            AVG({safe_double('GeoROC_Rocks_georoc_Cu_ppm')})  AS georoc_Cu,
            AVG({safe_double('GeoROC_Rocks_georoc_Ni_ppm')})  AS georoc_Ni,
            AVG({safe_double('GeoROC_Rocks_georoc_Zn_ppm')})  AS georoc_Zn,
            AVG({safe_double('GeoROC_Rocks_georoc_Co_ppm')})  AS georoc_Co,
            AVG({safe_double('GeoROC_Rocks_georoc_Cr_ppm')})  AS georoc_Cr,
            AVG({safe_double('GeoROC_Rocks_georoc_Pb_ppm')})  AS georoc_Pb,
            AVG({safe_double('GeoROC_Rocks_georoc_As_ppm')})  AS georoc_As,
            AVG({safe_double('GeoROC_Rocks_georoc_Cd_ppm')})  AS georoc_Cd,
            AVG({safe_double('GeoROC_Rocks_georoc_Hg_ppm')})  AS georoc_Hg,
            AVG({safe_double('GeoROC_Rocks_georoc_U_ppm')})   AS georoc_U,
            COUNT(*) AS n_samples
        FROM arkinlab_microbeatlas.enriched_metadata
        WHERE {safe_double('lat')} IS NOT NULL
          AND {safe_double('GeoROC_Rocks_georoc_Cu_ppm')} > 0
        GROUP BY
            ROUND({safe_double('lat')} / 0.25) * 0.25,
            ROUND({safe_double('lon')} / 0.25) * 0.25
    """
    georoc = spark.sql(georoc_sql).toPandas()
    georoc.to_csv(cache_f, index=False)
    print(f"  {len(georoc):,} grid bins, cached.", flush=True)

georoc_metals = ['georoc_Cu', 'georoc_Ni', 'georoc_Zn', 'georoc_Co', 'georoc_Cr',
                 'georoc_Pb', 'georoc_As', 'georoc_Cd', 'georoc_Hg', 'georoc_U']
result = kd_nearest(result, georoc, 'lat', 'lon', georoc_metals, prefix='')
for m in georoc_metals:
    n = result[m].notna().sum()
    print(f"    {m}: {n}/{len(result)}", flush=True)


# ════════════════════════════════════════════════════════════════════════
# 2. GEMAS European soil metals
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'gemas.csv'
if cache_f.exists():
    print("\n[2/10] GEMAS: loading cache...", flush=True)
    gemas = pd.read_csv(cache_f)
else:
    print("\n[2/10] GEMAS: querying...", flush=True)
    gemas_sql = f"""
        SELECT
            {safe_double('latitude')} AS lat,
            {safe_double('longitude')} AS lon,
            {safe_double('cu_ppm_ar')} AS gemas_Cu,
            {safe_double('pb_ppm_ar')} AS gemas_Pb,
            {safe_double('ni_ppm_ar')} AS gemas_Ni,
            {safe_double('cr_ppm_ar')} AS gemas_Cr,
            {safe_double('co_ppm_ar')} AS gemas_Co,
            {safe_double('zn_ppm_ar')} AS gemas_Zn,
            {safe_double('as_ppm_ar')} AS gemas_As,
            {safe_double('cd_ppm_ar')} AS gemas_Cd,
            {safe_double('hg_ppm_ar')} AS gemas_Hg,
            {safe_double('ph_cacl2')} AS gemas_pH,
            {safe_double('toc_pct')} AS gemas_TOC
        FROM arkinlab.envdbs.gemas
        WHERE {safe_double('latitude')} IS NOT NULL
    """
    gemas = spark.sql(gemas_sql).toPandas()
    gemas.to_csv(cache_f, index=False)
    print(f"  {len(gemas):,} samples, cached.", flush=True)

gemas_cols = ['gemas_Cu', 'gemas_Pb', 'gemas_Ni', 'gemas_Cr', 'gemas_Co',
              'gemas_Zn', 'gemas_As', 'gemas_Cd', 'gemas_Hg', 'gemas_pH', 'gemas_TOC']
result = kd_nearest(result, gemas, 'lat', 'lon', gemas_cols, prefix='')


# ════════════════════════════════════════════════════════════════════════
# 3. EPA TRI metal releases (aggregate per facility location)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'epa_tri.csv'
if cache_f.exists():
    print("\n[3/10] EPA TRI: loading cache...", flush=True)
    epa = pd.read_csv(cache_f)
else:
    print("\n[3/10] EPA TRI: querying...", flush=True)
    epa_sql = f"""
        SELECT
            {safe_double('lat')} AS lat,
            {safe_double('lon')} AS lon,
            SUM({safe_double('total_releases_lbs')}) AS total_release_lbs,
            COUNT(*) AS n_releases,
            SUM(CASE WHEN carcinogen = 'YES' THEN {safe_double('total_releases_lbs')} ELSE 0 END)
                AS carcinogen_release_lbs
        FROM arkinlab.envdbs.epa_tri_metals
        WHERE {safe_double('lat')} IS NOT NULL
        GROUP BY {safe_double('lat')}, {safe_double('lon')}
    """
    epa = spark.sql(epa_sql).toPandas()
    epa.to_csv(cache_f, index=False)
    print(f"  {len(epa):,} facility locations, cached.", flush=True)

result = kd_count_within(result, epa, 'lat', 'lon', radius_deg=0.5,
                         col_name='tri_facility_count_50km')
result = kd_nearest(result, epa, 'lat', 'lon',
                    ['total_release_lbs', 'carcinogen_release_lbs'],
                    max_dist_deg=0.5, prefix='tri_nearest_')


# ════════════════════════════════════════════════════════════════════════
# 4. Science 2025 global soil toxic metals (hazard quotients)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'science2025_grid.csv'
if cache_f.exists():
    print("\n[4/10] Science 2025: loading cache...", flush=True)
    sci = pd.read_csv(cache_f)
else:
    print("\n[4/10] Science 2025: querying...", flush=True)
    sci_sql = f"""
        SELECT
            ROUND({safe_double('latitude')} / 0.5) * 0.5 AS lat,
            ROUND({safe_double('longitude')} / 0.5) * 0.5 AS lon,
            AVG({safe_double('as')}) AS sci_hq_As,
            AVG({safe_double('cd')}) AS sci_hq_Cd,
            AVG({safe_double('co')}) AS sci_hq_Co,
            AVG({safe_double('cr')}) AS sci_hq_Cr,
            AVG({safe_double('cu')}) AS sci_hq_Cu,
            AVG({safe_double('ni')}) AS sci_hq_Ni,
            AVG({safe_double('pb')}) AS sci_hq_Pb,
            COUNT(*) AS n_cells
        FROM arkinlab.envdbs.science_2025_global_soil_toxic_metals
        WHERE threshold_type = 'HHET'
        GROUP BY
            ROUND({safe_double('latitude')} / 0.5) * 0.5,
            ROUND({safe_double('longitude')} / 0.5) * 0.5
    """
    sci = spark.sql(sci_sql).toPandas()
    sci.to_csv(cache_f, index=False)
    print(f"  {len(sci):,} grid bins, cached.", flush=True)

sci_cols = ['sci_hq_As', 'sci_hq_Cd', 'sci_hq_Co', 'sci_hq_Cr',
            'sci_hq_Cu', 'sci_hq_Ni', 'sci_hq_Pb']
result = kd_nearest(result, sci, 'lat', 'lon', sci_cols, prefix='')


# ════════════════════════════════════════════════════════════════════════
# 5. Ecotapestry lithology (mafic/felsic classification)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'ecotapestry.csv'
if cache_f.exists():
    print("\n[5/10] Ecotapestry lithology: loading cache...", flush=True)
    eco = pd.read_csv(cache_f)
else:
    print("\n[5/10] Ecotapestry lithology: querying...", flush=True)
    eco_sql = f"""
        SELECT
            {safe_double('lat')} AS lat,
            {safe_double('lon')} AS lon,
            lithology_name
        FROM arkinlab.envdbs.ecotapestry_lithology_0_25deg
        WHERE {safe_double('lat')} IS NOT NULL
    """
    eco = spark.sql(eco_sql).toPandas()
    eco.to_csv(cache_f, index=False)
    print(f"  {len(eco):,} grid cells, cached.", flush=True)

MAFIC_SCORE = {
    'Basic volcanic': 1.0, 'Intermediate volcanic': 0.7,
    'Basic plutonics': 1.0, 'Intermediate plutonics': 0.7,
    'Acid volcanic': 0.0, 'Acid plutonics': 0.0,
    'Ultrabasics': 1.0, 'Pyroclastics': 0.5,
    'Metamorphics': 0.5,
    'Mixed sedimentary rock': 0.3, 'Siliciclastic sedimentary rock': 0.2,
    'Carbonate sedimentary rock': 0.4, 'Evaporites': 0.1,
    'Unconsolidated sediment': 0.3,
    'Ice and glaciers': np.nan, 'Water bodies': np.nan,
    'No data': np.nan,
}
eco['mafic_score'] = eco['lithology_name'].map(MAFIC_SCORE)
result = kd_nearest(result, eco.dropna(subset=['mafic_score']),
                    'lat', 'lon', ['mafic_score'], prefix='litho_')


# ════════════════════════════════════════════════════════════════════════
# 6. Soil temperature (SoilTemp db, -10 cm depth)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'soiltemp_grid.csv'
if cache_f.exists():
    print("\n[6/10] SoilTemp: loading cache...", flush=True)
    st = pd.read_csv(cache_f)
else:
    print("\n[6/10] SoilTemp: querying...", flush=True)
    st_sql = f"""
        SELECT
            ROUND({safe_double('latitude')} / 0.5) * 0.5 AS lat,
            ROUND({safe_double('longitude')} / 0.5) * 0.5 AS lon,
            AVG({safe_double('meantemp')}) AS soil_temp_mean,
            MAX({safe_double('meantemp')}) - MIN({safe_double('meantemp')}) AS soil_temp_range,
            COUNT(DISTINCT plotcode) AS n_sites
        FROM arkinlab.envdbs.soiltemp
        WHERE {safe_double('height')} = -10.0
          AND {safe_double('meantemp')} IS NOT NULL
        GROUP BY
            ROUND({safe_double('latitude')} / 0.5) * 0.5,
            ROUND({safe_double('longitude')} / 0.5) * 0.5
    """
    st = spark.sql(st_sql).toPandas()
    st.to_csv(cache_f, index=False)
    print(f"  {len(st):,} grid bins, cached.", flush=True)

result = kd_nearest(result, st, 'lat', 'lon',
                    ['soil_temp_mean', 'soil_temp_range'], prefix='')


# ════════════════════════════════════════════════════════════════════════
# 7. ETOPO1 elevation
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'etopo1_grid.csv'
if cache_f.exists():
    print("\n[7/10] ETOPO1: loading cache...", flush=True)
    elev = pd.read_csv(cache_f)
else:
    print("\n[7/10] ETOPO1: querying...", flush=True)
    elev_sql = f"""
        SELECT
            ROUND({safe_double('lat')} / 0.25) * 0.25 AS lat,
            ROUND({safe_double('lon')} / 0.25) * 0.25 AS lon,
            AVG({safe_double('elevation')}) AS elevation_m
        FROM arkinlab.envdbs.etopo1_elevation
        WHERE {safe_double('elevation')} IS NOT NULL
        GROUP BY
            ROUND({safe_double('lat')} / 0.25) * 0.25,
            ROUND({safe_double('lon')} / 0.25) * 0.25
    """
    elev = spark.sql(elev_sql).toPandas()
    elev.to_csv(cache_f, index=False)
    print(f"  {len(elev):,} grid bins, cached.", flush=True)

result = kd_nearest(result, elev, 'lat', 'lon',
                    ['elevation_m'], prefix='')


# ════════════════════════════════════════════════════════════════════════
# 8. CMMI ore deposits (proximity + nearest metal concentrations)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'cmmi_ores.csv'
if cache_f.exists():
    print("\n[8/10] CMMI ores: loading cache...", flush=True)
    cmmi = pd.read_csv(cache_f)
else:
    print("\n[8/10] CMMI ores: querying...", flush=True)
    cmmi_sql = f"""
        SELECT
            {safe_double('latitude')} AS lat,
            {safe_double('longitude')} AS lon,
            {safe_double('cu_ppm')} AS cmmi_Cu,
            {safe_double('pb_ppm')} AS cmmi_Pb,
            {safe_double('ni_ppm')} AS cmmi_Ni,
            {safe_double('cr_ppm')} AS cmmi_Cr,
            {safe_double('co_ppm')} AS cmmi_Co,
            {safe_double('zn_ppm')} AS cmmi_Zn,
            {safe_double('as_ppm')} AS cmmi_As,
            {safe_double('ag_ppm')} AS cmmi_Ag,
            {safe_double('au_ppb')} AS cmmi_Au
        FROM arkinlab.envdbs.cmmi_ores
        WHERE {safe_double('latitude')} IS NOT NULL
    """
    cmmi = spark.sql(cmmi_sql).toPandas()
    cmmi.to_csv(cache_f, index=False)
    print(f"  {len(cmmi):,} ore samples, cached.", flush=True)

result = kd_min_distance(result, cmmi, 'lat', 'lon', col_name='cmmi_min_dist_deg')
result['cmmi_min_dist_km'] = result['cmmi_min_dist_deg'] * EARTH_KM_PER_DEG


# ════════════════════════════════════════════════════════════════════════
# 9. Mining operations (proximity)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'mining_ops.csv'
if cache_f.exists():
    print("\n[9/10] Mining operations: loading cache...", flush=True)
    mines = pd.read_csv(cache_f)
else:
    print("\n[9/10] Mining operations: querying...", flush=True)
    mines_sql = f"""
        SELECT
            {safe_double('latitude')} AS lat,
            {safe_double('longitude')} AS lon,
            mine_name, primary_commodity
        FROM arkinlab.envdbs.mining_operations
        WHERE {safe_double('latitude')} IS NOT NULL
    """
    mines = spark.sql(mines_sql).toPandas()
    mines.to_csv(cache_f, index=False)
    print(f"  {len(mines):,} mines, cached.", flush=True)

result = kd_min_distance(result, mines, 'lat', 'lon', col_name='mine_min_dist_deg')
result['mine_min_dist_km'] = result['mine_min_dist_deg'] * EARTH_KM_PER_DEG
result = kd_count_within(result, mines, 'lat', 'lon', radius_deg=0.5,
                         col_name='mine_count_50km')


# ════════════════════════════════════════════════════════════════════════
# 10. USGS REE occurrences (proximity)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'usgs_ree.csv'
if cache_f.exists():
    print("\n[10/10] USGS REE: loading cache...", flush=True)
    ree = pd.read_csv(cache_f)
else:
    print("\n[10/10] USGS REE: querying...", flush=True)
    ree_sql = f"""
        SELECT
            {safe_double('latitude')} AS lat,
            {safe_double('longitude')} AS lon
        FROM arkinlab.envdbs.usgs_ree_occurrences
        WHERE {safe_double('latitude')} IS NOT NULL
    """
    ree = spark.sql(ree_sql).toPandas()
    ree.to_csv(cache_f, index=False)
    print(f"  {len(ree):,} REE deposits, cached.", flush=True)

result = kd_min_distance(result, ree, 'lat', 'lon', col_name='ree_min_dist_deg')
result['ree_min_dist_km'] = result['ree_min_dist_deg'] * EARTH_KM_PER_DEG


# ════════════════════════════════════════════════════════════════════════
# 11. ESA Global Land Cover — SKIPPED (all landcover_class values null)
# ════════════════════════════════════════════════════════════════════════
print("\n[11] Landcover: SKIPPED (all values null in table)", flush=True)


# ════════════════════════════════════════════════════════════════════════
# 12. IGSD Cs-137 inventory (soil deposition Bq/m²)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'igsd_137cs.csv'
if cache_f.exists():
    print("\n[12/12] IGSD 137Cs: loading cache...", flush=True)
    cs = pd.read_csv(cache_f)
else:
    print("\n[12/12] IGSD 137Cs: querying...", flush=True)
    cs_sql = f"""
        SELECT
            {safe_double('latdecimal')} AS lat,
            {safe_double('longdecimal')} AS lon,
            {safe_double('activity_or_mda')} AS cs137_bq_m2
        FROM arkinlab.envdbs.igsd_137cs_inventory
        WHERE {safe_double('latdecimal')} IS NOT NULL
          AND {safe_double('activity_or_mda')} IS NOT NULL
          AND nuclide = 'Cs-137'
          AND sample_type = 'soil'
    """
    cs = spark.sql(cs_sql).toPandas()
    cs.to_csv(cache_f, index=False)
    print(f"  {len(cs):,} soil measurements, cached.", flush=True)

result = kd_nearest(result, cs, 'lat', 'lon',
                    ['cs137_bq_m2'], max_dist_deg=2.0, prefix='')
result = kd_min_distance(result, cs, 'lat', 'lon', col_name='cs137_min_dist_deg')


# ════════════════════════════════════════════════════════════════════════
# 13. WoSIS global soil properties (silt, sand, clay, pH, OC)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'wosis_global.csv'
if cache_f.exists():
    print("\n[13/14] WoSIS: loading cache...", flush=True)
    wosis = pd.read_csv(cache_f)
else:
    print("\n[13/14] WoSIS: querying (long→wide pivot)...", flush=True)
    wosis_sql = f"""
        SELECT
            ROUND({safe_double('latitude')} / 0.25) * 0.25 AS lat,
            ROUND({safe_double('longitude')} / 0.25) * 0.25 AS lon,
            AVG(CASE WHEN property = 'silt' THEN {safe_double('value_avg')} END) AS wosis_silt,
            AVG(CASE WHEN property = 'sand' THEN {safe_double('value_avg')} END) AS wosis_sand,
            AVG(CASE WHEN property = 'clay' THEN {safe_double('value_avg')} END) AS wosis_clay,
            AVG(CASE WHEN property = 'ph'   THEN {safe_double('value_avg')} END) AS wosis_ph,
            AVG(CASE WHEN property = 'orgc' THEN {safe_double('value_avg')} END) AS wosis_orgc,
            COUNT(*) AS wosis_n
        FROM arkinlab.envdbs.wosis_global
        WHERE {safe_double('latitude')} IS NOT NULL
          AND {safe_double('value_avg')} IS NOT NULL
        GROUP BY
            ROUND({safe_double('latitude')} / 0.25) * 0.25,
            ROUND({safe_double('longitude')} / 0.25) * 0.25
    """
    wosis = spark.sql(wosis_sql).toPandas()
    wosis.to_csv(cache_f, index=False)
    print(f"  {len(wosis):,} grid bins, cached.", flush=True)

wosis_cols = ['wosis_silt', 'wosis_sand', 'wosis_clay', 'wosis_ph', 'wosis_orgc']
result = kd_nearest(result, wosis, 'lat', 'lon', wosis_cols, prefix='')


# ════════════════════════════════════════════════════════════════════════
# 14. AVATAR soils (Cs-137, precipitation, elevation)
# ════════════════════════════════════════════════════════════════════════
cache_f = CACHE_DIR / 'avatar_soils.csv'
if cache_f.exists():
    print("\n[14/14] AVATAR soils: loading cache...", flush=True)
    avatar = pd.read_csv(cache_f)
else:
    print("\n[14/14] AVATAR soils: querying...", flush=True)
    avatar_sql = f"""
        SELECT
            {safe_double('latitude')} AS lat,
            {safe_double('longitude')} AS lon,
            {safe_double('decay_corrected_137cs_inventory')} AS avatar_cs137,
            {safe_double('precipitation')} AS avatar_precip,
            {safe_double('elevation')} AS avatar_elev
        FROM arkinlab.envdbs.avatar_soils
        WHERE {safe_double('latitude')} IS NOT NULL
    """
    avatar = spark.sql(avatar_sql).toPandas()
    avatar.to_csv(cache_f, index=False)
    print(f"  {len(avatar):,} soil samples, cached.", flush=True)

avatar_cols = ['avatar_cs137', 'avatar_precip', 'avatar_elev']
result = kd_nearest(result, avatar, 'lat', 'lon', avatar_cols, prefix='')


# ════════════════════════════════════════════════════════════════════════
# Merge with existing SoilGrids + Open-Meteo covariates
# ════════════════════════════════════════════════════════════════════════
print("\nMerging with existing env covariates...", flush=True)
existing = pd.read_csv(DATA / 'genome_env_covariates.csv')
existing_cols = ['genome_id', 'latitude', 'longitude',
                 'ph_h2o', 'organic_carbon_density', 'clay_pct',
                 'mean_annual_temp_C', 'mean_annual_precip_mm']
existing_locs = existing[existing_cols].drop_duplicates(subset=['latitude', 'longitude'])
loc_env = existing_locs.groupby(['latitude', 'longitude']).first().reset_index()
loc_env = loc_env.drop(columns=['genome_id'], errors='ignore')

full_locs = result.merge(loc_env, on=['latitude', 'longitude'], how='left')

# ── Join to MAGs ────────────────────────────────────────────────────────
print("\nJoining to MAGs...", flush=True)
final = mags[['genome_id', 'latitude', 'longitude']].merge(
    full_locs, on=['latitude', 'longitude'], how='left')

print(f"\n{'='*60}", flush=True)
print(f"FINAL: {len(final):,} genomes, {len(final.columns)} columns", flush=True)
print(f"\nCoverage per variable:", flush=True)
for col in sorted(final.columns):
    if col in ('genome_id', 'latitude', 'longitude'):
        continue
    n = final[col].notna().sum()
    if n > 0:
        print(f"  {col:40s}: {n:,}/{len(final):,} ({100*n/len(final):.1f}%)", flush=True)

final.to_csv(OUT, index=False)
print(f"\nSaved: {OUT}", flush=True)
print("DONE.", flush=True)

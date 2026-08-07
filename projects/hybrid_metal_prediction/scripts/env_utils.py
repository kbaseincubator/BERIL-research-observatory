"""Extract cheap environmental covariates and metal targets for hybrid metal prediction.

Table schema (verified 2026-07-07):
  arkinlab_microbeatlas.sample_metadata
    sample_id (string, e.g. 'ERR1159158.ERS992660')
    LatFieldValue (double), LonFieldValue (double)
    ph (string — may be 'Unknown')
    Environments (string, semicolon-delimited)

  arkinlab_microbeatlas.enriched_metadata
    sample_id (int) — geochemical measurement ID, NOT the 16S sample_id
    lat (double), lon (double)
    GeoROC_Rocks_georoc_Cu_ppm, ..._Zn_ppm, ..._Pb_ppm, ..._Ni_ppm, etc.
    (One 16S sample may match MULTIPLE enriched_metadata rows spatially)

  arkinlab_microbeatlas.enriched_metadata_gee
    Sample_ID_Matched (string, SRS accession, e.g. 'ERS992660')
    lat (double), lon (double)
    olm_soil_ph_0cm_H2O (double, ×10 — divide by 10)
    olm_soil_clay_0cm_pct (double)
    olm_soil_water_content_33kpa_0cm_pct (double)
    DEM_elevation_m, NDVI, ERA5_mean_2m_air_temperature_K, ERA5_total_precipitation_mm

  arkinlab_microbeatlas.otu_counts_long
    sample_id (string, matches sample_metadata.sample_id)
    otu_id (string), count (int)

Metal targets come from a SPATIAL JOIN of sample_metadata (16S samples) with
enriched_metadata (geochemical points), aggregated within SPATIAL_RADIUS_KM.

Usage
-----
from env_utils import get_soil_sample_ids, get_gee_features, get_metal_targets_by_spatial_join
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List

import pandas as pd
import numpy as np

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

# GeoROC columns in enriched_metadata
GEOROC_METAL_COLS = [
    "GeoROC_Rocks_georoc_Cu_ppm",
    "GeoROC_Rocks_georoc_Zn_ppm",
    "GeoROC_Rocks_georoc_Pb_ppm",
    "GeoROC_Rocks_georoc_Ni_ppm",
    "GeoROC_Rocks_georoc_Co_ppm",
    "GeoROC_Rocks_georoc_Cr_ppm",
    "GeoROC_Rocks_georoc_As_ppm",
]

# Short names for target columns after aggregation
METAL_SHORT_NAMES = {
    "GeoROC_Rocks_georoc_Cu_ppm": "Cu_ppm",
    "GeoROC_Rocks_georoc_Zn_ppm": "Zn_ppm",
    "GeoROC_Rocks_georoc_Pb_ppm": "Pb_ppm",
    "GeoROC_Rocks_georoc_Ni_ppm": "Ni_ppm",
    "GeoROC_Rocks_georoc_Co_ppm": "Co_ppm",
    "GeoROC_Rocks_georoc_Cr_ppm": "Cr_ppm",
    "GeoROC_Rocks_georoc_As_ppm": "As_ppm",
}

# Available env covariates from enriched_metadata_gee
ENV_FEATURES_GEE = [
    "ph_olm",          # olm_soil_ph_0cm_H2O / 10
    "clay_pct",        # olm_soil_clay_0cm_pct
    "water_content",   # olm_soil_water_content_33kpa_0cm_pct
    "ndvi",            # NDVI
    "elevation_m",     # DEM_elevation_m
    "temp_K",          # ERA5_mean_2m_air_temperature_K
    "precip_mm",       # ERA5_total_precipitation_mm
    "lat",
    "lon",
]

# Spatial join radius for matching 16S samples to geochemical measurements
SPATIAL_RADIUS_KM = 50.0

# Spatial bin resolution for the approximate join (degrees, ≈11 km at equator)
SPATIAL_BIN_DEG = 0.5

# CSU metal mobility grid columns (arkinlab.envdbs.csu_metal_mobility_grid)
# Phase Fraction 1 = mobile fraction (exchangeable + carbonate-bound), dimensionless 0–1
CSU_MOBILITY_COLS = {
    "PF1_Cu": "mob_cu",
    "PF1_Pb": "mob_pb",
    "PF1_As": "mob_as",
    "PF1_Cd": "mob_cd",
    "PF1_Cr": "mob_cr",
    "PF1_Hg": "mob_hg",
}
# Grid resolution of the CSU table (approx degrees)
CSU_GRID_RES_DEG = 0.045


# ---------------------------------------------------------------------------
# Sample ID utilities
# ---------------------------------------------------------------------------

def extract_srs_key(sample_id: str) -> str:
    """Extract SRS/ERS accession from MicrobeAtlas sample_id.

    'ERR1159158.ERS992660' → 'ERS992660'
    'SRR4240564.SRS1689702' → 'SRS1689702'
    """
    parts = str(sample_id).split(".")
    return parts[-1] if len(parts) > 1 else sample_id


def _coords_to_spark(spark, sample_coords: pd.DataFrame):
    """Create a Spark temp view '_sample_coords_tmp' from a pandas DataFrame.

    Handles the PyArrow ChunkedArray incompatibility that arises when
    sample_coords is backed by Arrow (as returned by spark.sql().toPandas()).
    """
    df = (
        sample_coords[["lat", "lon"]]
        .reset_index()
        .rename(columns={
            sample_coords.index.name or "sample_id": "sample_id",
            "lat": "sm_lat",
            "lon": "sm_lon",
        })
    )
    # Force numpy-backed columns to avoid ChunkedArray errors
    df = pd.DataFrame({
        "sample_id": df["sample_id"].astype(str).to_numpy(),
        "sm_lat": df["sm_lat"].astype(float).to_numpy(),
        "sm_lon": df["sm_lon"].astype(float).to_numpy(),
    })
    return spark.createDataFrame(df)


# ---------------------------------------------------------------------------
# Spark queries
# ---------------------------------------------------------------------------

def get_soil_sample_ids(
    spark,
    soil_keywords: Optional[list] = None,
) -> pd.DataFrame:
    """Pull soil sample_ids with lat/lon and in-situ pH from sample_metadata.

    Filters on Environments containing soil-related keywords.

    Returns DataFrame indexed by sample_id with columns:
        lat, lon, ph_insitu, srs_key, environments
    """
    if soil_keywords is None:
        soil_keywords = ["soil", "terrestrial", "rhizosphere", "sediment"]

    env_filter = " OR ".join(
        f"LOWER(Environments) LIKE '%{kw}%'" for kw in soil_keywords
    )

    sql = f"""
        SELECT sample_id,
               LatFieldValue                    AS lat,
               LonFieldValue                    AS lon,
               CASE WHEN ph = 'Unknown' OR ph IS NULL THEN NULL
                    ELSE TRY_CAST(ph AS DOUBLE) END AS ph_insitu,
               Environments                     AS environments
        FROM arkinlab.microbeatlas.sample_metadata
        WHERE ({env_filter})
          AND LatFieldValue IS NOT NULL
          AND LonFieldValue IS NOT NULL
    """
    df = spark.sql(sql).toPandas()
    df.attrs.clear()
    df = df.drop_duplicates("sample_id").set_index("sample_id")
    df["srs_key"] = [extract_srs_key(sid) for sid in df.index]
    return df


def get_gee_features(
    spark,
    srs_keys: Optional[list] = None,
) -> pd.DataFrame:
    """Pull GEE-derived environmental covariates from enriched_metadata_gee.

    Join key: enriched_metadata_gee.Sample_ID_Matched = SRS accession.

    Returns DataFrame indexed by srs_key with ENV_FEATURES_GEE columns.
    """
    sid_clause = ""
    if srs_keys is not None:
        sid_str = "', '".join(str(s) for s in srs_keys)
        sid_clause = f"WHERE Sample_ID_Matched IN ('{sid_str}')"

    sql = f"""
        SELECT Sample_ID_Matched                           AS srs_key,
               olm_soil_ph_0cm_H2O / 10.0                 AS ph_olm,
               olm_soil_clay_0cm_pct                      AS clay_pct,
               olm_soil_water_content_33kpa_0cm_pct       AS water_content,
               NDVI                                       AS ndvi,
               DEM_elevation_m                            AS elevation_m,
               ERA5_mean_2m_air_temperature_K             AS temp_K,
               ERA5_total_precipitation_mm                AS precip_mm
        FROM arkinlab.microbeatlas.enriched_metadata_gee
        {sid_clause}
    """
    df = spark.sql(sql).toPandas()
    df.attrs.clear()
    df = df.drop_duplicates("srs_key").set_index("srs_key")
    for col in ENV_FEATURES_GEE:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_metal_targets_by_spatial_join(
    spark,
    sample_coords: pd.DataFrame,
    radius_km: float = SPATIAL_RADIUS_KM,
    bin_deg: float = SPATIAL_BIN_DEG,
    agg_func: str = "median",
) -> pd.DataFrame:
    """Spatially join 16S sample coords with geochemical measurements.

    For each 16S sample, finds all enriched_metadata rows within radius_km
    and aggregates metal concentrations (median by default).

    Parameters
    ----------
    sample_coords : DataFrame indexed by sample_id with lat/lon columns
    radius_km : haversine distance cutoff (km)
    bin_deg : grid bin width for approximate pre-filter (degrees)
    agg_func : 'median' or 'mean'

    Returns
    -------
    DataFrame indexed by sample_id with log1p-transformed metal target columns.
    """
    # Upload sample coords as Spark table
    sample_spark = _coords_to_spark(spark, sample_coords)
    sample_spark.createOrReplaceTempView("_sample_coords")

    # Load enriched_metadata
    metal_sel = ", ".join(
        f"em.{c} AS {METAL_SHORT_NAMES[c]}" for c in GEOROC_METAL_COLS
    )
    em_sql = f"""
        SELECT em.lat AS em_lat, em.lon AS em_lon,
               {metal_sel}
        FROM arkinlab.microbeatlas.enriched_metadata em
        WHERE em.lat IS NOT NULL AND em.lon IS NOT NULL
          AND GREATEST(
              COALESCE(em.GeoROC_Rocks_georoc_Cu_ppm, 0),
              COALESCE(em.GeoROC_Rocks_georoc_Zn_ppm, 0),
              COALESCE(em.GeoROC_Rocks_georoc_Pb_ppm, 0),
              COALESCE(em.GeoROC_Rocks_georoc_Ni_ppm, 0)
          ) > 0
    """
    em_spark = spark.sql(em_sql)
    em_spark.createOrReplaceTempView("_geochemical")

    # Bin-approximate join, then filter by haversine
    n_bins = max(1, int(radius_km / (bin_deg * 111.0)) + 1)
    join_sql = f"""
        SELECT sc.sample_id,
               AVG(gc.Cu_ppm)  AS Cu_ppm,
               AVG(gc.Zn_ppm)  AS Zn_ppm,
               AVG(gc.Pb_ppm)  AS Pb_ppm,
               AVG(gc.Ni_ppm)  AS Ni_ppm,
               AVG(gc.Co_ppm)  AS Co_ppm,
               AVG(gc.Cr_ppm)  AS Cr_ppm,
               AVG(gc.As_ppm)  AS As_ppm,
               COUNT(*)        AS n_geochem_pts,
               AVG(2 * 6371 * ASIN(SQRT(
                   POWER(SIN(RADIANS((gc.em_lat - sc.sm_lat) / 2)), 2) +
                   COS(RADIANS(sc.sm_lat)) * COS(RADIANS(gc.em_lat)) *
                   POWER(SIN(RADIANS((gc.em_lon - sc.sm_lon) / 2)), 2)
               ))) AS mean_dist_km
        FROM _sample_coords sc
        JOIN _geochemical gc
          ON FLOOR(sc.sm_lat / {bin_deg}) BETWEEN FLOOR(gc.em_lat / {bin_deg}) - {n_bins}
                                               AND FLOOR(gc.em_lat / {bin_deg}) + {n_bins}
         AND FLOOR(sc.sm_lon / {bin_deg}) BETWEEN FLOOR(gc.em_lon / {bin_deg}) - {n_bins}
                                               AND FLOOR(gc.em_lon / {bin_deg}) + {n_bins}
         AND (2 * 6371 * ASIN(SQRT(
                POWER(SIN(RADIANS((gc.em_lat - sc.sm_lat) / 2)), 2) +
                COS(RADIANS(sc.sm_lat)) * COS(RADIANS(gc.em_lat)) *
                POWER(SIN(RADIANS((gc.em_lon - sc.sm_lon) / 2)), 2)
         ))) <= {radius_km}
        GROUP BY sc.sample_id
    """
    result = spark.sql(join_sql).toPandas()
    result.attrs.clear()
    result = result.set_index("sample_id")

    # Log-transform targets
    for col in ["Cu_ppm", "Zn_ppm", "Pb_ppm", "Ni_ppm", "Co_ppm", "Cr_ppm", "As_ppm"]:
        if col in result.columns:
            result[f"log_{col}"] = np.log1p(
                pd.to_numeric(result[col], errors="coerce").clip(lower=0)
            )

    n_matched = result.index.isin(sample_coords.index).sum()
    pct = 100 * n_matched / len(sample_coords)
    log.info(
        "Spatial join (radius=%g km): %d / %d (%.1f%%) samples have ≥1 geochemical match.",
        radius_km, n_matched, len(sample_coords), pct,
    )
    return result


def get_csu_mobility_features(
    spark,
    sample_coords: pd.DataFrame,
    bin_deg: float = CSU_GRID_RES_DEG,
) -> pd.DataFrame:
    """Snap each sample to the nearest CSU metal mobility grid cell.

    The CSU grid (arkinlab.envdbs.csu_metal_mobility_grid) stores Phase
    Fraction 1 (PF1) values: the mobile fraction (exchangeable + carbonate-
    bound), a dimensionless index 0–1. Grid resolution ≈ 0.045°.

    Uses a ±0.5-cell tolerance join on rounded lat/lon bins, then averages
    any multiple matches within the bin.

    Returns DataFrame indexed by sample_id with columns:
        mob_cu, mob_pb, mob_as, mob_cd, mob_cr, mob_hg
    """
    # Use a bin size slightly larger than the grid resolution so samples and
    # grid cells snap to the same key via equality join (avoids range join over 7.4M rows).
    snap_deg = bin_deg * 2  # 0.09° ≈ 2 grid cells; all samples find a bin

    # Upload sample coords
    sample_spark = _coords_to_spark(spark, sample_coords)
    sample_spark.createOrReplaceTempView("_csu_sample_coords")

    pf1_agg = ", ".join(
        f"AVG(CAST(c.{src} AS DOUBLE)) AS {dst}"
        for src, dst in CSU_MOBILITY_COLS.items()
    )

    sql = f"""
        WITH csu_binned AS (
            SELECT ROUND(CAST(latitude  AS DOUBLE) / {snap_deg}) * {snap_deg} AS lat_bin,
                   ROUND(CAST(longitude AS DOUBLE) / {snap_deg}) * {snap_deg} AS lon_bin,
                   {", ".join(
                       f"AVG(CAST({src} AS DOUBLE)) AS {dst}"
                       for src, dst in CSU_MOBILITY_COLS.items()
                   )}
            FROM arkinlab.envdbs.csu_metal_mobility_grid
            GROUP BY lat_bin, lon_bin
        ),
        sample_binned AS (
            SELECT sample_id,
                   ROUND(sm_lat / {snap_deg}) * {snap_deg} AS lat_bin,
                   ROUND(sm_lon / {snap_deg}) * {snap_deg} AS lon_bin
            FROM _csu_sample_coords
        )
        SELECT s.sample_id, {", ".join(f"c.{dst}" for dst in CSU_MOBILITY_COLS.values())}
        FROM sample_binned s
        LEFT JOIN csu_binned c ON s.lat_bin = c.lat_bin AND s.lon_bin = c.lon_bin
    """
    df = spark.sql(sql).toPandas()
    df.attrs.clear()
    df = df.set_index("sample_id")
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    n_matched = df[list(CSU_MOBILITY_COLS.values())].dropna(how="all").shape[0]
    pct = 100 * n_matched / len(sample_coords)
    log.info(
        "CSU mobility join: %d / %d (%.1f%%) samples matched.",
        n_matched, len(sample_coords), pct,
    )
    return df


def merge_ph(row: pd.Series) -> float:
    """Return best available pH: in-situ > OLM."""
    for col in ("ph_insitu", "ph_olm"):
        v = row.get(col, np.nan)
        if pd.notna(v) and 2.0 <= float(v) <= 12.0:
            return float(v)
    return np.nan


def build_feature_table(
    sample_coords: pd.DataFrame,
    gee_features: pd.DataFrame,
    metal_targets: pd.DataFrame,
    cwm_df: pd.DataFrame,
    csu_df: Optional[pd.DataFrame] = None,
    soilgrids_api_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Merge all features into one table indexed by sample_id.

    Parameters
    ----------
    sample_coords : indexed by sample_id, has lat/lon/ph_insitu/srs_key
    gee_features : indexed by srs_key, has ph_olm/clay_pct/etc.
    metal_targets : indexed by sample_id, has log_Cu_ppm/etc. + n_geochem_pts
    cwm_df : indexed by sample_id, has CWM_* columns
    csu_df : optional, indexed by sample_id, has mob_cu/mob_pb/mob_as/etc.
    soilgrids_api_df : optional, indexed by sample_id, has sg_cec/sg_bdod for
                       samples not covered by OLM (e.g. holdout datasets)
    """
    # Join gee_features on srs_key
    coords_with_srs = sample_coords.copy()
    if "srs_key" in coords_with_srs.columns:
        gee_indexed = gee_features.copy()
        # Re-index gee by sample_id via srs_key lookup
        srs_to_sid = coords_with_srs["srs_key"].reset_index()
        srs_to_sid.columns = ["sample_id", "srs_key"]
        gee_merged = srs_to_sid.merge(
            gee_features.reset_index(), on="srs_key", how="left"
        ).set_index("sample_id").drop(columns=["srs_key"], errors="ignore")
        df = coords_with_srs.join(gee_merged, how="left")
    else:
        df = coords_with_srs.copy()

    df = df.join(metal_targets, how="left")
    df = df.join(cwm_df, how="left")

    if csu_df is not None and not csu_df.empty:
        df = df.join(csu_df, how="left")

    if soilgrids_api_df is not None and not soilgrids_api_df.empty:
        df = df.join(soilgrids_api_df, how="left", rsuffix="_sg")

    # Best pH
    df["ph"] = df.apply(merge_ph, axis=1)
    df["ph_source"] = "missing"
    df.loc[df["ph_insitu"].notna(), "ph_source"] = "insitu"
    df.loc[df["ph_insitu"].isna() & df["ph_olm"].notna(), "ph_source"] = "olm"

    return df


def report_feature_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Report missingness per feature column."""
    n = len(df)
    records = []
    for col in df.columns:
        n_missing = df[col].isna().sum()
        records.append({
            "column": col,
            "n_available": n - n_missing,
            "n_missing": n_missing,
            "coverage_pct": round(100 * (1 - n_missing / n), 1),
        })
    return pd.DataFrame(records).sort_values("coverage_pct", ascending=True)

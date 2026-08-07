"""
confounder_discovery.py
=======================
Functions to search BERDL namespaces for potential confounders and evaluate
coverage of discovered datasets against the sample locations used in analysis.

Workflow
--------
1. list_all_berdl_tables()   — enumerate all tables in all namespaces
2. screen_table_for_env_vars() — check if a table has lat/lon + potential confounders
3. evaluate_coverage()        — haversine join with analysis sample locations;
                                report fraction matched within distance threshold
4. summarise_candidate_confounders() — aggregate findings into a report DataFrame

Usage
-----
>>> from scripts.confounder_discovery import list_all_berdl_tables, screen_table_for_env_vars
>>> spark = get_spark_session()
>>> tables = list_all_berdl_tables(spark)
>>> candidates = [t for t in tables if screen_table_for_env_vars(spark, t)]
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# BERDL namespace enumeration
# ---------------------------------------------------------------------------

def list_all_berdl_tables(spark) -> List[str]:
    """Return all 'namespace.table_name' strings visible in this Spark session.

    Parameters
    ----------
    spark:
        Active SparkSession.

    Returns
    -------
    List of strings like ``['mgnify.mag_metal_traits', 'ngsa.geochemistry', ...]``.
    """
    from scripts.berdl_utils import list_namespaces, list_tables

    all_tables: List[str] = []
    for ns in list_namespaces(spark):
        try:
            tables = list_tables(spark, ns)
            all_tables.extend(f"{ns}.{t}" for t in tables)
        except Exception as exc:
            warnings.warn(f"Could not list tables in namespace '{ns}': {exc}")
    return sorted(all_tables)


# ---------------------------------------------------------------------------
# Table screening
# ---------------------------------------------------------------------------

# Columns that suggest environmental data
_ENV_KEYWORDS = {
    "lat", "lon", "latitude", "longitude",
    "depth", "ph", "temperature", "temp",
    "moisture", "precipitation", "rainfall",
    "carbon", "nitrogen", "phosphorus", "organic",
    "salinity", "conductivity",
    "elevation", "altitude",
    "sand", "silt", "clay", "texture",
    "biome", "landuse", "land_use", "ecosystem",
}

_LAT_SYNONYMS = {"lat", "latitude", "y", "lat_dd", "latitude_dd"}
_LON_SYNONYMS = {"lon", "longitude", "x", "lon_dd", "longitude_dd"}


def screen_table_for_env_vars(
    spark,
    full_table_name: str,
    min_env_cols: int = 2,
) -> Dict[str, Any]:
    """Check whether a table has lat/lon plus environmental columns.

    Parameters
    ----------
    spark:
        Active SparkSession.
    full_table_name:
        E.g. ``'ngsa.geochemistry'``.
    min_env_cols:
        Minimum number of environmental keyword matches required (beyond lat/lon).

    Returns
    -------
    dict with keys: table, has_latlon, env_cols, n_env_cols, n_rows,
    is_candidate (bool), error (str or None).  Always returns all keys so
    that downstream pd.DataFrame() calls produce consistent columns even
    when every table errors.
    """
    # Base dict — complete column set, safe defaults.  Always returned.
    result: Dict[str, Any] = {
        "table": full_table_name,
        "has_latlon": False,
        "env_cols": [],
        "n_env_cols": 0,
        "n_rows": None,
        "is_candidate": False,
        "error": None,
    }

    try:
        schema_df = spark.sql(f"DESCRIBE {full_table_name}").toPandas()
        cols = schema_df.iloc[:, 0].str.lower().tolist()
    except BaseException as exc:
        result["error"] = str(exc)[:200]
        return result

    cols_set = set(cols)
    has_lat = bool(cols_set & _LAT_SYNONYMS)
    has_lon = bool(cols_set & _LON_SYNONYMS)
    has_latlon = has_lat and has_lon

    env_cols = [c for c in cols if c in _ENV_KEYWORDS and c not in _LAT_SYNONYMS | _LON_SYNONYMS]
    is_candidate = has_latlon and len(env_cols) >= min_env_cols

    # Skip COUNT(*) — full table scan is too slow and generates noisy error
    # output for tables the user can DESCRIBE but not SELECT from.

    result.update({
        "has_latlon": has_latlon,
        "env_cols": env_cols,
        "n_env_cols": len(env_cols),
        "is_candidate": is_candidate,
    })
    return result


def screen_all_tables(
    spark,
    tables: List[str],
    min_env_cols: int = 2,
) -> pd.DataFrame:
    """Screen a list of tables and return a summary DataFrame.

    Parameters
    ----------
    spark:
        Active SparkSession.
    tables:
        List of 'namespace.table' strings (from :func:`list_all_berdl_tables`).
    min_env_cols:
        Passed to :func:`screen_table_for_env_vars`.

    Returns
    -------
    pd.DataFrame sorted by is_candidate (True first), then n_env_cols.
    Every row is guaranteed to have the full column set (has_latlon, env_cols,
    n_env_cols, n_rows, is_candidate, error) so downstream display calls
    never raise KeyError regardless of how many tables are inaccessible.
    """
    rows = []
    for tbl in tables:
        try:
            result = screen_table_for_env_vars(spark, tbl, min_env_cols=min_env_cols)
        except BaseException as exc:
            result = {
                "table": tbl, "has_latlon": False, "env_cols": [], "n_env_cols": 0,
                "n_rows": None, "is_candidate": False, "error": str(exc)[:200],
            }
        rows.append(result)

    if not rows:
        # Return empty DataFrame with the expected schema
        return pd.DataFrame(columns=["table", "has_latlon", "env_cols", "n_env_cols",
                                     "n_rows", "is_candidate", "error"])

    df = pd.DataFrame(rows)
    df = df.sort_values(["is_candidate", "n_env_cols"], ascending=[False, False])
    return df


# ---------------------------------------------------------------------------
# Coverage evaluation
# ---------------------------------------------------------------------------

def evaluate_coverage(
    candidate_df: pd.DataFrame,
    analysis_points: pd.DataFrame,
    cand_lat: str = "lat",
    cand_lon: str = "lon",
    analysis_lat: str = "lat",
    analysis_lon: str = "lon",
    max_dist_km: float = 200.0,
) -> Dict[str, Any]:
    """Measure how well *candidate_df* covers the analysis sample locations.

    Uses haversine nearest-neighbour matching (from spatial_utils).

    Parameters
    ----------
    candidate_df:
        Environmental dataset to evaluate (pandas DataFrame with lat/lon).
    analysis_points:
        Sample locations used in the primary analysis.
    cand_lat, cand_lon:
        Coordinate column names in *candidate_df*.
    analysis_lat, analysis_lon:
        Coordinate column names in *analysis_points*.
    max_dist_km:
        Distance threshold for declaring a match.

    Returns
    -------
    dict with: n_analysis, n_candidate, n_matched, pct_matched, median_dist_km,
    max_dist_km_used.
    """
    from scripts.spatial_utils import haversine_join

    joined = haversine_join(
        left=analysis_points,
        right=candidate_df,
        left_lat=analysis_lat,
        left_lon=analysis_lon,
        right_lat=cand_lat,
        right_lon=cand_lon,
        max_dist_km=max_dist_km,
    )

    matched = joined["_dist_km"] <= max_dist_km
    return {
        "n_analysis": len(analysis_points),
        "n_candidate": len(candidate_df),
        "n_matched": int(matched.sum()),
        "pct_matched": round(100.0 * matched.mean(), 1),
        "median_dist_km": round(float(joined["_dist_km"].median()), 1),
        "max_dist_km_used": max_dist_km,
    }


# ---------------------------------------------------------------------------
# External dataset evaluator
# ---------------------------------------------------------------------------

def evaluate_external_dataset(
    csv_path: str,
    analysis_points: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    max_dist_km: float = 200.0,
) -> Dict[str, Any]:
    """Load a CSV dataset and evaluate its geographic coverage.

    Parameters
    ----------
    csv_path:
        Path to a CSV with latitude/longitude columns.
    analysis_points:
        Analysis sample locations for coverage evaluation.
    lat_col, lon_col:
        Coordinate column names in the CSV.
    max_dist_km:
        Matching threshold.

    Returns
    -------
    dict merging :func:`evaluate_coverage` output with dataset metadata:
    path, n_rows_total, columns.
    """
    df = pd.read_csv(csv_path)
    if lat_col not in df.columns or lon_col not in df.columns:
        return {
            "path": csv_path,
            "error": f"lat/lon columns '{lat_col}'/'{lon_col}' not found. "
                     f"Available: {list(df.columns)}"
        }

    coverage = evaluate_coverage(
        df, analysis_points,
        cand_lat=lat_col, cand_lon=lon_col,
        max_dist_km=max_dist_km,
    )
    coverage.update({
        "path": csv_path,
        "n_rows_total": len(df),
        "columns": list(df.columns),
    })
    return coverage


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def summarise_candidate_confounders(
    screen_results: pd.DataFrame,
    coverage_results: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    """Produce a concise confounder candidate report.

    Parameters
    ----------
    screen_results:
        Output of :func:`screen_all_tables`.
    coverage_results:
        Optional list of coverage dicts from :func:`evaluate_coverage`, keyed
        by 'table' matching screen_results.

    Returns
    -------
    pd.DataFrame with is_candidate=True rows, enriched with coverage data
    if provided.
    """
    candidates = screen_results[screen_results["is_candidate"]].copy()

    if coverage_results:
        coverage_df = pd.DataFrame(coverage_results)
        if "table" in coverage_df.columns:
            candidates = candidates.merge(
                coverage_df[["table", "pct_matched", "median_dist_km"]],
                on="table", how="left",
            )

    return candidates.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Correlation-based redundancy filter
# ---------------------------------------------------------------------------

def flag_redundant_confounders(
    trait_df: pd.DataFrame,
    candidate_cols: List[str],
    primary_predictor: str,
    r2_threshold: float = 0.5,
) -> pd.DataFrame:
    """Flag candidate confounders that are highly collinear with the predictor.

    Collinear confounders (r² > *r2_threshold* with *primary_predictor*) are
    likely capturing the same variance — note them but do not exclude
    automatically.

    Parameters
    ----------
    trait_df:
        DataFrame containing *primary_predictor* and *candidate_cols*.
    candidate_cols:
        Column names of potential confounders.
    primary_predictor:
        The main predictor of interest (e.g. 'ko_per_mb_z').
    r2_threshold:
        r² above which a confounder is flagged as redundant.

    Returns
    -------
    pd.DataFrame: columns = [confounder, r_with_predictor, r2, is_redundant, n_obs].
    """
    rows = []
    if primary_predictor not in trait_df.columns:
        raise ValueError(f"primary_predictor '{primary_predictor}' not in trait_df")

    pred = trait_df[primary_predictor].dropna()

    for col in candidate_cols:
        if col not in trait_df.columns:
            continue
        both = trait_df[[primary_predictor, col]].dropna()
        if len(both) < 10:
            continue
        r = float(both.corr().iloc[0, 1])
        rows.append({
            "confounder": col,
            "r_with_predictor": round(r, 3),
            "r2": round(r ** 2, 3),
            "is_redundant": bool(r ** 2 > r2_threshold),
            "n_obs": len(both),
        })

    return pd.DataFrame(rows).sort_values("r2", ascending=False)

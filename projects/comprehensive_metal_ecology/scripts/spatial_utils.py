"""
spatial_utils.py
================
Haversine nearest-neighbour joins and extraction of gridded environmental
data at point locations.

All coordinate inputs are expected in decimal degrees (WGS84).

Dependencies: numpy, sklearn (BallTree), rasterio (optional, for raster extraction).
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

EARTH_RADIUS_KM = 6_371.0


# ---------------------------------------------------------------------------
# Haversine join
# ---------------------------------------------------------------------------

def haversine_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_lat: str = "lat",
    left_lon: str = "lon",
    right_lat: str = "lat",
    right_lon: str = "lon",
    max_dist_km: float = 200.0,
    k: int = 1,
    right_prefix: str = "",
) -> pd.DataFrame:
    """Nearest-neighbour join from *left* to *right* using haversine distance.

    Parameters
    ----------
    left:
        Query points (e.g. sample locations).
    right:
        Reference points (e.g. geochemistry stations).
    left_lat, left_lon:
        Column names for coordinates in *left*.
    right_lat, right_lon:
        Column names for coordinates in *right*.
    max_dist_km:
        Maximum allowed distance; rows exceeding this threshold are set to NaN
        in all joined columns.
    k:
        Number of nearest neighbours to return.  k=1 returns a single match
        per query point; k>1 not yet fully supported.
    right_prefix:
        Optional prefix applied to all *right* columns in the output
        (avoids name collisions).

    Returns
    -------
    pd.DataFrame with all left columns plus *right* columns (prefixed if
    *right_prefix*) and ``_dist_km`` column.  Rows beyond *max_dist_km*
    have NaN in all right columns.
    """
    left = left.copy()
    right = right.copy()

    # Drop rows with missing coordinates
    left_valid = left.dropna(subset=[left_lat, left_lon]).copy()
    right_valid = right.dropna(subset=[right_lat, right_lon]).copy()

    left_rad = np.radians(left_valid[[left_lat, left_lon]].values)
    right_rad = np.radians(right_valid[[right_lat, right_lon]].values)

    tree = BallTree(right_rad, metric="haversine")
    distances, indices = tree.query(left_rad, k=k)

    dist_km = distances[:, 0] * EARTH_RADIUS_KM
    best_idx = indices[:, 0]

    # Build joined columns
    right_cols = [c for c in right_valid.columns
                  if c not in (right_lat, right_lon)]
    right_sub = right_valid.iloc[best_idx][right_cols].reset_index(drop=True)
    if right_prefix:
        right_sub = right_sub.rename(
            columns={c: f"{right_prefix}{c}" for c in right_sub.columns}
        )

    joined = left_valid.reset_index(drop=True).copy()
    joined["_dist_km"] = dist_km
    for col in right_sub.columns:
        joined[col] = right_sub[col].values

    # Null out matches beyond threshold
    beyond = joined["_dist_km"] > max_dist_km
    for col in right_sub.columns:
        joined.loc[beyond, col] = np.nan

    # Re-merge with unmatched left rows (those with missing coords)
    unmatched_mask = left[left_lat].isna() | left[left_lon].isna()
    if unmatched_mask.any():
        missing_rows = left[unmatched_mask].copy()
        missing_rows["_dist_km"] = np.nan
        for col in right_sub.columns:
            missing_rows[col] = np.nan
        joined = pd.concat([joined, missing_rows], ignore_index=True)

    n_matched = int((~beyond).sum())
    n_total = len(left_valid)
    print(f"haversine_join: {n_matched}/{n_total} query points matched within {max_dist_km} km")
    return joined


# ---------------------------------------------------------------------------
# Raster extraction
# ---------------------------------------------------------------------------

def extract_raster_at_points(
    points: pd.DataFrame,
    raster_path: str | Path,
    band: int = 1,
    lat_col: str = "lat",
    lon_col: str = "lon",
    out_col: str = "raster_value",
    nodata: Optional[float] = None,
) -> pd.DataFrame:
    """Extract raster values at point locations using bilinear sampling.

    Parameters
    ----------
    points:
        DataFrame with latitude/longitude columns.
    raster_path:
        Path to a GeoTIFF (or any rasterio-supported format).
    band:
        Raster band index (1-based).
    lat_col, lon_col:
        Coordinate column names.
    out_col:
        Name of the new column added to *points*.
    nodata:
        Value to treat as no-data (replace with NaN).  If None, uses the
        raster's native nodata value.

    Returns
    -------
    pd.DataFrame with *out_col* appended.
    """
    try:
        import rasterio
        from rasterio.sample import sample_gen
    except ImportError:
        raise ImportError(
            "rasterio is required for raster extraction: "
            "pip install rasterio"
        )

    pts = points.copy()
    coords = list(zip(pts[lon_col], pts[lat_col]))   # (x, y) = (lon, lat)

    with rasterio.open(str(raster_path)) as src:
        nd = nodata if nodata is not None else src.nodata
        values = np.array([v[band - 1] for v in src.sample(coords)])

    if nd is not None:
        values = values.astype(float)
        values[values == nd] = np.nan

    pts[out_col] = values
    return pts


# ---------------------------------------------------------------------------
# Bounding-box filter
# ---------------------------------------------------------------------------

def filter_bbox(
    df: pd.DataFrame,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> pd.DataFrame:
    """Return rows within a geographic bounding box.

    Parameters
    ----------
    df:
        DataFrame with lat/lon columns.
    lat_min, lat_max, lon_min, lon_max:
        Bounding box in decimal degrees.

    Returns
    -------
    Filtered DataFrame (copy).
    """
    mask = (
        df[lat_col].between(lat_min, lat_max)
        & df[lon_col].between(lon_min, lon_max)
    )
    n_in = mask.sum()
    print(f"filter_bbox: {n_in}/{len(df)} rows within "
          f"lat [{lat_min},{lat_max}], lon [{lon_min},{lon_max}]")
    return df[mask].copy()


# ---------------------------------------------------------------------------
# Convenience: Australia bounding box
# ---------------------------------------------------------------------------

AUSTRALIA_BBOX = (-44.0, -10.0, 112.0, 154.0)


def filter_australia(df: pd.DataFrame, lat_col: str = "lat",
                     lon_col: str = "lon") -> pd.DataFrame:
    """Filter *df* to the Australian bounding box."""
    lat_min, lat_max, lon_min, lon_max = AUSTRALIA_BBOX
    return filter_bbox(df, lat_min, lat_max, lon_min, lon_max,
                       lat_col=lat_col, lon_col=lon_col)


# ---------------------------------------------------------------------------
# Z-score utility
# ---------------------------------------------------------------------------

def zscore(series: pd.Series, ddof: int = 1) -> pd.Series:
    """Return z-scored series, returning NaN where sd=0."""
    mu = series.mean()
    sd = series.std(ddof=ddof)
    if sd == 0:
        warnings.warn(f"zscore: sd=0 for series '{series.name}', returning zeros")
        return (series - mu)
    return (series - mu) / sd

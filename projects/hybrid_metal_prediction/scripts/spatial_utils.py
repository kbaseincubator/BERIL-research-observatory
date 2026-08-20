"""Spatial utilities for hybrid metal prediction.

Provides:
  - Spatial block cross-validation (k-means on lat/lon)
  - Haversine distance computation
  - Ordinary kriging baseline via pykrige
  - Geographic cluster assignment for holdout sets

Usage
-----
from spatial_utils import make_spatial_blocks, haversine_km, KrigingBaseline
"""

from __future__ import annotations

import logging
import warnings
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.utils import check_random_state

log = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


# ---------------------------------------------------------------------------
# Haversine
# ---------------------------------------------------------------------------

def haversine_km(
    lat1: np.ndarray, lon1: np.ndarray,
    lat2: np.ndarray, lon2: np.ndarray,
) -> np.ndarray:
    """Return great-circle distances in km between paired lat/lon arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------------------
# Spatial block CV
# ---------------------------------------------------------------------------

def make_spatial_blocks(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    n_blocks: int = 5,
    random_state: int = 42,
) -> np.ndarray:
    """Assign each sample to a geographic block using k-means on lat/lon.

    Parameters
    ----------
    df : DataFrame with lat/lon columns (and optionally index=sample_id)
    n_blocks : number of geographic blocks (spatial CV folds)

    Returns
    -------
    np.ndarray of integer block labels (0..n_blocks-1), same length as df.
    """
    rng = check_random_state(random_state)
    coords = df[[lat_col, lon_col]].values.astype(float)
    nan_mask = np.isnan(coords).any(axis=1)
    if nan_mask.any():
        log.warning("%d samples have NaN lat/lon and will be assigned block −1.", nan_mask.sum())

    labels = np.full(len(df), -1, dtype=int)
    valid = ~nan_mask
    km = KMeans(n_clusters=n_blocks, n_init=20, random_state=rng).fit(coords[valid])
    labels[valid] = km.labels_
    return labels


def spatial_cv_splits(
    block_labels: np.ndarray,
    n_blocks: Optional[int] = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return list of (train_idx, test_idx) for spatial leave-one-block-out CV.

    Parameters
    ----------
    block_labels : array of integer block assignments (from make_spatial_blocks)
    n_blocks : if None, inferred from unique values in block_labels (excl. −1)

    Returns
    -------
    List of (train_indices, test_indices) tuples.
    """
    unique = np.unique(block_labels[block_labels >= 0])
    splits = []
    for block in unique:
        test_idx = np.where(block_labels == block)[0]
        train_idx = np.where((block_labels != block) & (block_labels >= 0))[0]
        splits.append((train_idx, test_idx))
    return splits


def report_block_sizes(df: pd.DataFrame, block_labels: np.ndarray) -> pd.DataFrame:
    """Return a summary DataFrame of samples per block."""
    records = []
    for b in np.unique(block_labels):
        mask = block_labels == b
        records.append({
            "block": b,
            "n_samples": mask.sum(),
            "lat_mean": df["lat"].values[mask].mean() if "lat" in df.columns else np.nan,
            "lon_mean": df["lon"].values[mask].mean() if "lon" in df.columns else np.nan,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Nearest-sample join for holdout datasets
# ---------------------------------------------------------------------------

def nearest_sample_join(
    query_df: pd.DataFrame,
    reference_df: pd.DataFrame,
    query_lat: str = "lat",
    query_lon: str = "lon",
    ref_lat: str = "lat",
    ref_lon: str = "lon",
    max_dist_km: float = 50.0,
) -> pd.DataFrame:
    """Join query_df to the nearest sample in reference_df by haversine distance.

    Returns query_df with appended columns from nearest reference row, plus
    `join_dist_km`. Rows without a neighbour within max_dist_km get NaN.
    """
    q_lat = query_df[query_lat].values
    q_lon = query_df[query_lon].values
    r_lat = reference_df[ref_lat].values
    r_lon = reference_df[ref_lon].values

    results = []
    for i in range(len(q_lat)):
        dists = haversine_km(q_lat[i], q_lon[i], r_lat, r_lon)
        best = int(np.argmin(dists))
        results.append({
            "query_idx": query_df.index[i],
            "ref_idx": reference_df.index[best],
            "join_dist_km": dists[best],
        })

    join_table = pd.DataFrame(results).set_index("query_idx")
    join_table = join_table[join_table["join_dist_km"] <= max_dist_km]

    out = query_df.copy()
    out = out.join(join_table)
    ref_cols = [c for c in reference_df.columns if c not in (ref_lat, ref_lon)]
    nearest = reference_df.loc[
        join_table["ref_idx"].values,
        ref_cols,
    ].set_index(join_table.index)
    out = out.join(nearest, rsuffix="_ref")
    return out


# ---------------------------------------------------------------------------
# Ordinary kriging baseline
# ---------------------------------------------------------------------------

class KrigingBaseline:
    """Ordinary kriging regressor wrapping pykrige.OrdinaryKriging.

    Treats lat and lon as spatial coordinates. Fit on train set, predict
    on test set. One model per target variable.
    """

    def __init__(self, variogram_model: str = "spherical", verbose: bool = False):
        self.variogram_model = variogram_model
        self.verbose = verbose
        self._models: dict = {}

    def fit(
        self,
        lats: np.ndarray,
        lons: np.ndarray,
        targets: pd.DataFrame,
    ) -> "KrigingBaseline":
        """Fit one kriging model per column in targets."""
        try:
            from pykrige.ok import OrdinaryKriging
        except ImportError:
            raise ImportError("pykrige required for KrigingBaseline: pip install pykrige")

        for col in targets.columns:
            y = targets[col].values
            valid = ~np.isnan(y)
            ok = OrdinaryKriging(
                lons[valid], lats[valid], y[valid],
                variogram_model=self.variogram_model,
                verbose=self.verbose,
                enable_plotting=False,
            )
            self._models[col] = ok
            log.info("Kriging fit for %s (n=%d)", col, valid.sum())
        return self

    def predict(
        self,
        lats: np.ndarray,
        lons: np.ndarray,
    ) -> pd.DataFrame:
        """Return predictions for all fitted targets."""
        preds = {}
        for col, ok in self._models.items():
            z, _ = ok.execute("points", lons, lats)
            preds[col] = np.asarray(z)
        return pd.DataFrame(preds)

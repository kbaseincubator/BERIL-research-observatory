"""Extract environmental data at MAG sampling coordinates.

Two data sources:
  1. CSU metal mobility fractions — spatial join to a pre-loaded grid DataFrame
     via BallTree haversine; ≤50 km radius.
  2. SoilGrids pH / OC / clay — via soilgrids_api.SoilGridsClient (REST, cached).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

EARTH_RADIUS_KM = 6371.0

CSU_TARGETS = ["PF1_As", "PF1_Cd", "PF1_Cr", "PF1_Cu", "PF1_Hg", "PF1_Pb"]

# Columns to pull from SoilGrids
SOILGRIDS_COLS = ["ph_h2o", "organic_carbon_density", "clay_content"]


def _rad(degrees: np.ndarray) -> np.ndarray:
    return np.radians(degrees)


def build_csu_tree(
    csu_grid: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> tuple[BallTree, pd.DataFrame]:
    """Return a BallTree (haversine) and the cleaned grid DataFrame."""
    csu_clean = csu_grid.dropna(subset=[lat_col, lon_col]).copy()
    coords_rad = _rad(csu_clean[[lat_col, lon_col]].values)
    tree = BallTree(coords_rad, metric="haversine")
    return tree, csu_clean


def nearest_csu(
    lat: float,
    lon: float,
    tree: BallTree,
    csu_clean: pd.DataFrame,
    max_km: float = 50.0,
    target_cols: list[str] = CSU_TARGETS,
) -> dict[str, float]:
    """Return the nearest CSU mobility values within max_km, or NaN if none."""
    query = _rad(np.array([[lat, lon]]))
    dists, idxs = tree.query(query, k=1)
    dist_km = float(dists[0, 0]) * EARTH_RADIUS_KM
    if dist_km > max_km:
        return {col: np.nan for col in target_cols}
    row = csu_clean.iloc[idxs[0, 0]]
    return {col: float(row[col]) if col in csu_clean.columns else np.nan
            for col in target_cols}


def batch_csu_join(
    coords_df: pd.DataFrame,
    csu_grid: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    max_km: float = 50.0,
    target_cols: list[str] = CSU_TARGETS,
) -> pd.DataFrame:
    """Join CSU mobility values to every row of *coords_df*.

    Returns coords_df with additional target columns appended.
    Each unmatched row gets NaN for all target columns.
    """
    tree, csu_clean = build_csu_tree(csu_grid, lat_col=lat_col, lon_col=lon_col)
    results = []
    for _, row in coords_df.iterrows():
        vals = nearest_csu(
            row[lat_col], row[lon_col], tree, csu_clean,
            max_km=max_km, target_cols=target_cols,
        )
        results.append(vals)
    env_cols = pd.DataFrame(results, index=coords_df.index)
    return pd.concat([coords_df, env_cols], axis=1)


def batch_soilgrids_join(
    coords_df: pd.DataFrame,
    client,  # soilgrids_api.SoilGridsClient
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> pd.DataFrame:
    """Fetch SoilGrids data for every coordinate in *coords_df*.

    Parameters
    ----------
    client : SoilGridsClient
        Initialised client with a local JSON cache.

    Returns
    -------
    DataFrame with SoilGrids columns merged in.
    """
    sg_df = client.batch_query(coords_df, lat_col=lat_col, lon_col=lon_col)
    # batch_query returns a DataFrame indexed like coords_df
    keep_cols = [c for c in SOILGRIDS_COLS if c in sg_df.columns]
    return pd.concat([coords_df, sg_df[keep_cols]], axis=1)


def envo_is_environmental(envo_terms: str | float) -> bool:
    """Return True if the ENVO terms indicate a non-host-associated environment.

    Accepts terrestrial, soil, aquatic, sediment; rejects host-associated.
    """
    if not isinstance(envo_terms, str):
        return False
    lower = envo_terms.lower()
    accepted = ("terrestrial", "soil", "aquatic", "sediment",
                "freshwater", "marine", "river", "lake", "wetland")
    rejected = ("host", "gut", "oral", "skin", "blood", "lung",
                "placenta", "feces", "faeces", "clinical")
    if any(r in lower for r in rejected):
        return False
    return any(a in lower for a in accepted)

"""Model training and cross-validation for metagenomic environment prediction.

Hypotheses tested:
  H1: XGBoost on metal-gene density (M1) out-predicts null baseline (B0).
  H2: Metal features alone (M1) out-predict non-metal features alone (M2).
  H3: Combined model (M3) out-predicts M1 alone.
  H4: Geographic holdout performance ≥ 80% of in-distribution block CV.

Baselines
---------
  B0: mean-predictor (predicts training-set mean for every test sample)
  B1: SoilGrids pH + OC only (non-metal soil properties)
  B2: climate-only (MAT, MAP, temperature seasonality)
  B3: all non-metal env features combined

Metal models
------------
  M1: XGBoost on MAG metal-gene density (ko_per_mb_primary)
  M2: XGBoost on non-metal env features (same as B3 features)
  M3: XGBoost on all features (M1 + M2 combined)

Spatial CV
----------
  k-means on lat/lon with k=5; each fold is a geographic cluster.
  CV metric: RMSE (primary), R² (secondary).
  PGLS validation delegated to pgls_utils.run_pgls (see NB04).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor

# Allow importing from sibling project scripts
_REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(_REPO_ROOT / "comprehensive_metal_ecology" / "scripts"))

# Genomic predictor column (computed in NB01 by batch_compute_densities)
MAG_DENSITY_FEATURES = ["ko_per_mb_primary"]

# Non-metal environmental baselines (SoilGrids; climate not fetched)
NON_METAL_FEATURES = ["ph_h2o", "organic_carbon_density", "clay_content"]

# Combined feature set for M3
ALL_FEATURES = MAG_DENSITY_FEATURES + NON_METAL_FEATURES

# CSU metal mobility target columns (predicted, not used as features)
# Grid available: As, Cd, Cr, Cu, Hg, Pb (Zn and Ni not in grid)
CSU_TARGETS = ["PF1_As", "PF1_Cd", "PF1_Cr", "PF1_Cu", "PF1_Hg", "PF1_Pb"]

RANDOM_STATE = 42
N_SPATIAL_FOLDS = 5

XGB_DEFAULTS = dict(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=RANDOM_STATE,
    n_jobs=-1,
    verbosity=0,
)


# ---------------------------------------------------------------------------
# Spatial fold assignment
# ---------------------------------------------------------------------------

def make_spatial_folds(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    k: int = N_SPATIAL_FOLDS,
    random_state: int = RANDOM_STATE,
) -> np.ndarray:
    """Return fold labels (0 … k-1) assigned by k-means on lat/lon."""
    coords = df[[lat_col, lon_col]].values
    km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    return km.fit_predict(coords)


# ---------------------------------------------------------------------------
# Single-fold evaluation helpers
# ---------------------------------------------------------------------------

def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(r2_score(y_true, y_pred))


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def _b0_predict(y_train: np.ndarray, n_test: int) -> np.ndarray:
    return np.full(n_test, y_train.mean())


# ---------------------------------------------------------------------------
# XGBoost wrapper
# ---------------------------------------------------------------------------

def build_xgboost(**overrides) -> XGBRegressor:
    params = {**XGB_DEFAULTS, **overrides}
    return XGBRegressor(**params)


# ---------------------------------------------------------------------------
# Spatial block CV
# ---------------------------------------------------------------------------

def spatial_block_cv(
    df: pd.DataFrame,
    feature_sets: dict[str, list[str]],
    target_col: str,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    k: int = N_SPATIAL_FOLDS,
    xgb_kwargs: Optional[dict] = None,
) -> pd.DataFrame:
    """Run spatial k-fold CV for each feature set.

    Parameters
    ----------
    df : DataFrame
        Must contain all feature columns, target_col, lat_col, lon_col.
    feature_sets : dict
        {model_name: [feature_col, ...]}. Model 'B0' is run automatically.
    target_col : str
        Column to predict.
    k : int
        Number of spatial folds.
    xgb_kwargs : dict | None
        Additional kwargs passed to XGBRegressor.

    Returns
    -------
    DataFrame with columns: model, fold, n_test, rmse, r2.
    """
    xgb_kwargs = xgb_kwargs or {}
    folds = make_spatial_folds(df, lat_col=lat_col, lon_col=lon_col, k=k)
    y = df[target_col].values

    records = []
    for fold_id in range(k):
        test_mask = folds == fold_id
        train_mask = ~test_mask
        y_train, y_test = y[train_mask], y[test_mask]

        # B0 baseline
        y_pred_b0 = _b0_predict(y_train, test_mask.sum())
        records.append(dict(
            model="B0", fold=fold_id, n_test=int(test_mask.sum()),
            rmse=_rmse(y_test, y_pred_b0), r2=_r2(y_test, y_pred_b0),
        ))

        # XGBoost models
        for model_name, feature_cols in feature_sets.items():
            valid_cols = [c for c in feature_cols if c in df.columns]
            if not valid_cols:
                continue
            X_train = df.loc[train_mask, valid_cols].values
            X_test = df.loc[test_mask, valid_cols].values
            model = build_xgboost(**xgb_kwargs)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            records.append(dict(
                model=model_name, fold=fold_id, n_test=int(test_mask.sum()),
                rmse=_rmse(y_test, y_pred), r2=_r2(y_test, y_pred),
            ))

    return pd.DataFrame(records)


def summarise_cv(cv_df: pd.DataFrame) -> pd.DataFrame:
    """Return mean ± SD RMSE and R² per model, ordered by mean RMSE."""
    grp = cv_df.groupby("model")
    summary = pd.DataFrame({
        "mean_rmse": grp["rmse"].mean(),
        "sd_rmse": grp["rmse"].std(),
        "mean_r2": grp["r2"].mean(),
        "sd_r2": grp["r2"].std(),
        "n_folds": grp["fold"].count(),
    }).reset_index()
    return summary.sort_values("mean_rmse").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Geographic holdout
# ---------------------------------------------------------------------------

def geographic_holdout_eval(
    df: pd.DataFrame,
    holdout_mask: np.ndarray,
    feature_cols: list[str],
    target_col: str,
    xgb_kwargs: Optional[dict] = None,
) -> dict:
    """Train on ~holdout_mask, evaluate on holdout_mask.

    Returns dict: rmse_holdout, r2_holdout, n_holdout, n_train.
    """
    xgb_kwargs = xgb_kwargs or {}
    train_mask = ~holdout_mask
    valid_feature_cols = [c for c in feature_cols if c in df.columns]
    X_train = df.loc[train_mask, valid_feature_cols].values
    X_test = df.loc[holdout_mask, valid_feature_cols].values
    y_train = df.loc[train_mask, target_col].values
    y_test = df.loc[holdout_mask, target_col].values

    model = build_xgboost(**xgb_kwargs)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return dict(
        rmse_holdout=_rmse(y_test, y_pred),
        r2_holdout=_r2(y_test, y_pred),
        n_holdout=int(holdout_mask.sum()),
        n_train=int(train_mask.sum()),
    )

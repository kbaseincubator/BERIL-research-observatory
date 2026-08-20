"""Model training, nested spatial CV, and uncertainty quantification.

Models:
  M1: pH + CWM (ridge)
  M2: All cheap env + CWM (XGBoost)
  M3: CWM only (XGBoost)
  M4: Env only (XGBoost)
  M5: Multi-output XGBoost (all 4 targets jointly)

Baselines (B0–B5) are fit separately in notebook 01.

Usage
-----
from modelling import fit_model, nested_spatial_cv, ConformalPredictor
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

log = logging.getLogger(__name__)

# Feature column groups
CWM_FEATURE_PREFIX = "CWM_"
# CSU mobility grid provides PF1 for Cu, Pb, As, Cd, Cr, Hg (no Zn/Ni column exists)
ENV_FEATURES = [
    "ph",           # best available pH (insitu > OLM)
    "clay_pct",     # OLM clay 0–5 cm
    "water_content",# OLM volumetric water content at 33 kPa
    "ndvi",         # GEE NDVI
    "elevation_m",  # DEM elevation
    "temp_K",       # ERA5 mean air temperature
    "precip_mm",    # ERA5 total precipitation
    "mob_cu",       # CSU PF1_Cu (mobile fraction)
    "mob_pb",       # CSU PF1_Pb
    "mob_as",       # CSU PF1_As
    "mob_cd",       # CSU PF1_Cd
    "mob_cr",       # CSU PF1_Cr
    "mob_hg",       # CSU PF1_Hg
]
TARGET_COLS = ["Cu_ppm", "Zn_ppm", "Pb_ppm", "Ni_ppm"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_cwm_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(CWM_FEATURE_PREFIX)]


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def _drop_nan_rows(X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
    """Drop rows where X or y has NaN."""
    mask = ~(X.isna().any(axis=1) | y.isna())
    return X[mask], y[mask]


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------

def build_ridge(alpha: float = 1.0) -> Pipeline:
    return Pipeline([("scaler", StandardScaler()), ("model", Ridge(alpha=alpha))])


def build_xgboost(
    n_estimators: int = 400,
    max_depth: int = 5,
    learning_rate: float = 0.05,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    random_state: int = 42,
    **kwargs,
):
    try:
        from xgboost import XGBRegressor
    except ImportError:
        raise ImportError("xgboost required: pip install xgboost")
    return XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        random_state=random_state,
        tree_method="hist",
        n_jobs=-1,
        **kwargs,
    )


def build_lightgbm(
    n_estimators: int = 400,
    max_depth: int = 5,
    learning_rate: float = 0.05,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    random_state: int = 42,
    **kwargs,
):
    try:
        import lightgbm as lgb
    except ImportError:
        raise ImportError("lightgbm required: pip install lightgbm")
    return lgb.LGBMRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        random_state=random_state,
        n_jobs=-1,
        verbose=-1,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Feature selection per model
# ---------------------------------------------------------------------------

def get_features(feature_df: pd.DataFrame, model_name: str) -> pd.DataFrame:
    """Return the feature columns appropriate for model_name.

    model_name ∈ {"M1", "M2", "M3", "M4", "M5"}.
    """
    cwm_cols = _get_cwm_cols(feature_df)
    env_cols = [c for c in ENV_FEATURES if c in feature_df.columns]

    mapping = {
        "M1": ["ph"] + cwm_cols,
        "M2": env_cols + cwm_cols,
        "M3": cwm_cols,
        "M4": env_cols,
        "M5": env_cols + cwm_cols,  # multi-output uses same feature set as M2
    }
    use = mapping.get(model_name, cwm_cols)
    return feature_df[[c for c in use if c in feature_df.columns]]


# ---------------------------------------------------------------------------
# Nested spatial CV
# ---------------------------------------------------------------------------

def nested_spatial_cv(
    feature_df: pd.DataFrame,
    target_series: pd.Series,
    block_labels: np.ndarray,
    model_name: str = "M2",
    model_type: str = "xgboost",
    n_inner_folds: int = 3,
    alpha_grid: Optional[list] = None,
    random_state: int = 42,
) -> Dict:
    """Nested spatial leave-one-block-out CV with inner random-fold hyperparameter tuning.

    Outer: geographic block holdout (leave-one-block-out).
    Inner: random k-fold within the remaining blocks, used for hyperparameter
           selection (here only α for Ridge; XGBoost uses early stopping proxy).

    Returns
    -------
    dict with keys:
        "oof_preds": pd.Series of out-of-fold predictions indexed like target_series
        "oof_true": pd.Series of out-of-fold truths
        "fold_rmse": list of per-fold RMSE values
        "overall_rmse": float
        "model_name": str
    """
    from spatial_utils import spatial_cv_splits
    from sklearn.model_selection import KFold

    X = get_features(feature_df, model_name)
    y = target_series

    splits = spatial_cv_splits(block_labels)
    oof_preds = pd.Series(np.nan, index=y.index)
    fold_rmse = []

    if alpha_grid is None:
        alpha_grid = [0.01, 0.1, 1.0, 10.0, 100.0]

    for train_idx, test_idx in splits:
        X_tr_outer, y_tr_outer = X.iloc[train_idx], y.iloc[train_idx]
        X_te, y_te = X.iloc[test_idx], y.iloc[test_idx]

        X_tr_clean, y_tr_clean = _drop_nan_rows(X_tr_outer, y_tr_outer)
        X_te_clean, y_te_clean = _drop_nan_rows(X_te, y_te)
        if X_te_clean.empty:
            continue

        if model_type == "ridge":
            # Inner loop: pick alpha by CV
            inner_kf = KFold(n_splits=n_inner_folds, shuffle=True, random_state=random_state)
            best_alpha, best_rmse = alpha_grid[0], np.inf
            for alpha in alpha_grid:
                fold_scores = []
                for in_tr, in_val in inner_kf.split(X_tr_clean):
                    m = build_ridge(alpha=alpha).fit(
                        X_tr_clean.iloc[in_tr], y_tr_clean.iloc[in_tr]
                    )
                    fold_scores.append(rmse(
                        y_tr_clean.iloc[in_val],
                        m.predict(X_tr_clean.iloc[in_val]),
                    ))
                if np.mean(fold_scores) < best_rmse:
                    best_alpha = alpha
                    best_rmse = np.mean(fold_scores)
            model = build_ridge(alpha=best_alpha).fit(X_tr_clean, y_tr_clean)

        elif model_type in ("xgboost", "lightgbm"):
            builder = build_xgboost if model_type == "xgboost" else build_lightgbm
            model = builder(random_state=random_state)
            model.fit(X_tr_clean, y_tr_clean, verbose=False)
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        preds = model.predict(X_te_clean)
        # Assign predictions to the correct positions: rows from test_idx that
        # were kept by _drop_nan_rows (i.e., had no NaN in X or y).
        valid_te_mask = (~X_te.isna().any(axis=1) & ~y_te.isna()).values
        valid_te_positions = np.array(test_idx)[valid_te_mask]
        oof_preds.iloc[valid_te_positions] = preds
        fold_rmse.append(rmse(y_te_clean.values, preds))

    valid_mask = oof_preds.notna() & y.notna()
    overall = rmse(y[valid_mask].values, oof_preds[valid_mask].values)

    return {
        "oof_preds": oof_preds,
        "oof_true": y,
        "fold_rmse": fold_rmse,
        "overall_rmse": overall,
        "model_name": model_name,
    }


# ---------------------------------------------------------------------------
# Bootstrap ΔRMSE for hypothesis testing
# ---------------------------------------------------------------------------

def bootstrap_delta_rmse(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    n_boot: int = 1000,
    ci: float = 0.95,
    random_state: int = 42,
) -> Dict:
    """Bootstrap 95% CI for RMSE(A) − RMSE(B).

    Positive delta means A is worse (larger RMSE) than B.
    """
    rng = np.random.default_rng(random_state)
    n = len(y_true)
    observed_delta = rmse(y_true, y_pred_a) - rmse(y_true, y_pred_b)
    boot_deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_deltas.append(
            rmse(y_true[idx], y_pred_a[idx]) - rmse(y_true[idx], y_pred_b[idx])
        )
    boot_deltas = np.array(boot_deltas)
    alpha = 1 - ci
    lo, hi = np.percentile(boot_deltas, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    # Proportion of bootstrap samples where delta > 0 (A worse than B)
    p_a_worse = float(np.mean(boot_deltas > 0))
    return {
        "observed_delta_rmse": observed_delta,
        "boot_ci_lo": lo,
        "boot_ci_hi": hi,
        "p_a_worse_than_b": p_a_worse,
        "n_boot": n_boot,
    }


# ---------------------------------------------------------------------------
# Conformal prediction
# ---------------------------------------------------------------------------

class ConformalPredictor:
    """Split conformal prediction intervals for a fitted point estimator.

    Usage:
        cp = ConformalPredictor(alpha=0.1)
        cp.calibrate(fitted_model, X_cal, y_cal)
        lo, hi = cp.predict_interval(X_test)
    """

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha  # miscoverage level; 1-alpha = coverage
        self._q_hat: Optional[float] = None
        self._model = None

    def calibrate(self, model, X_cal: pd.DataFrame, y_cal: pd.Series) -> None:
        """Compute calibration residuals to set conformal threshold."""
        preds = model.predict(X_cal)
        residuals = np.abs(y_cal.values - preds)
        n = len(residuals)
        level = np.ceil((1 - self.alpha) * (n + 1)) / n
        level = min(level, 1.0)
        self._q_hat = float(np.quantile(residuals, level))
        self._model = model
        log.info(
            "Conformal calibration: q̂ = %.4f (%.0f%% coverage)", self._q_hat, (1 - self.alpha) * 100
        )

    def predict_interval(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Return (lower, upper) prediction intervals."""
        if self._q_hat is None:
            raise RuntimeError("Call calibrate() before predict_interval().")
        preds = self._model.predict(X)
        return preds - self._q_hat, preds + self._q_hat


# ---------------------------------------------------------------------------
# Summary table builder
# ---------------------------------------------------------------------------

def make_results_table(cv_results: list[Dict]) -> pd.DataFrame:
    """Combine a list of nested_spatial_cv result dicts into a summary table."""
    rows = []
    for r in cv_results:
        rows.append({
            "model": r["model_name"],
            "overall_rmse": r["overall_rmse"],
            "fold_rmse_mean": np.mean(r["fold_rmse"]),
            "fold_rmse_sd": np.std(r["fold_rmse"]),
            "n_folds": len(r["fold_rmse"]),
        })
    return pd.DataFrame(rows).sort_values("overall_rmse")

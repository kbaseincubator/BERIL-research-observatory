"""Evaluation utilities: SHAP, RMSE/R², geographic holdout comparison.

Companion to modelling.py. Runs after CV is complete.
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from xgboost import XGBRegressor


# ---------------------------------------------------------------------------
# SHAP
# ---------------------------------------------------------------------------

def compute_shap_values(
    model: XGBRegressor,
    X: pd.DataFrame | np.ndarray,
    feature_names: Optional[list[str]] = None,
) -> tuple[np.ndarray, pd.Series]:
    """Compute SHAP values; return (shap_matrix, mean_abs_shap Series).

    Parameters
    ----------
    model : fitted XGBRegressor
    X : array-like of shape (n_samples, n_features)
    feature_names : list[str] | None
        If None, uses X.columns when X is a DataFrame.

    Returns
    -------
    shap_values : ndarray shape (n_samples, n_features)
    mean_shap : pd.Series sorted descending by mean |SHAP|
    """
    if isinstance(X, pd.DataFrame):
        feature_names = feature_names or list(X.columns)
        X_arr = X.values
    else:
        X_arr = X
        feature_names = feature_names or [f"f{i}" for i in range(X_arr.shape[1])]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_arr)

    mean_shap = pd.Series(
        np.abs(shap_values).mean(axis=0),
        index=feature_names,
    ).sort_values(ascending=False)

    return shap_values, mean_shap


def plot_shap_bar(
    mean_shap: pd.Series,
    title: str = "SHAP feature importance",
    metal_features: Optional[list[str]] = None,
    output_path: Optional[str] = None,
    figsize: tuple[int, int] = (8, 6),
) -> None:
    """Horizontal bar chart of mean |SHAP| coloured by metal vs non-metal."""
    metal_features = set(metal_features or [])
    colours = [
        "#d62728" if feat in metal_features else "#1f77b4"
        for feat in mean_shap.index
    ]
    fig, ax = plt.subplots(figsize=figsize)
    bars = mean_shap.sort_values().plot(
        kind="barh", color=list(reversed(colours)), ax=ax,
    )
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(title)
    ax.axvline(0, color="black", linewidth=0.8)

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(color="#d62728", label="Metal mobility (CSU PF1)"),
        Patch(color="#1f77b4", label="Non-metal env"),
    ]
    ax.legend(handles=legend_handles, loc="lower right")

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=150)
    plt.show()


def shap_metal_fraction(
    mean_shap: pd.Series,
    metal_features: list[str],
) -> float:
    """Return the fraction of total |SHAP| attributable to metal features."""
    metal_mask = mean_shap.index.isin(metal_features)
    total = mean_shap.sum()
    if total == 0:
        return np.nan
    return float(mean_shap[metal_mask].sum() / total)


# ---------------------------------------------------------------------------
# Delta-RMSE bootstrap (M1 vs B0)
# ---------------------------------------------------------------------------

def bootstrap_delta_rmse(
    y_true: np.ndarray,
    y_pred_model: np.ndarray,
    y_pred_baseline: np.ndarray,
    n_boot: int = 1000,
    random_state: int = 42,
) -> dict:
    """Bootstrap 95% CI for ΔRMSE = RMSE(model) − RMSE(baseline).

    Negative ΔRMSE means the model beats the baseline.

    Returns
    -------
    dict: delta_rmse, ci_lower, ci_upper, p_value (one-tailed: delta < 0)
    """
    rng = np.random.default_rng(random_state)
    n = len(y_true)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        rmse_m = float(np.sqrt(np.mean((y_true[idx] - y_pred_model[idx]) ** 2)))
        rmse_b = float(np.sqrt(np.mean((y_true[idx] - y_pred_baseline[idx]) ** 2)))
        deltas.append(rmse_m - rmse_b)
    deltas = np.array(deltas)
    obs_delta = (
        float(np.sqrt(np.mean((y_true - y_pred_model) ** 2)))
        - float(np.sqrt(np.mean((y_true - y_pred_baseline) ** 2)))
    )
    p_val = float((deltas >= 0).mean())
    return dict(
        delta_rmse=obs_delta,
        ci_lower=float(np.percentile(deltas, 2.5)),
        ci_upper=float(np.percentile(deltas, 97.5)),
        p_value=p_val,
    )


# ---------------------------------------------------------------------------
# Geographic holdout vs block CV comparison
# ---------------------------------------------------------------------------

def holdout_vs_cv_ratio(
    holdout_rmse: float,
    cv_mean_rmse: float,
) -> float:
    """Return holdout_rmse / cv_mean_rmse; values ≤ 1.25 pass H4."""
    if cv_mean_rmse == 0:
        return np.nan
    return holdout_rmse / cv_mean_rmse


# ---------------------------------------------------------------------------
# Summary tables
# ---------------------------------------------------------------------------

def format_cv_table(
    cv_summary: pd.DataFrame,
    model_order: Optional[list[str]] = None,
) -> pd.DataFrame:
    """Return a formatted summary table for display in a notebook."""
    if model_order:
        cv_summary = (
            cv_summary.set_index("model")
            .reindex(model_order)
            .reset_index()
        )
    cv_summary["RMSE (mean ± SD)"] = cv_summary.apply(
        lambda r: f"{r['mean_rmse']:.3f} ± {r['sd_rmse']:.3f}", axis=1
    )
    cv_summary["R² (mean ± SD)"] = cv_summary.apply(
        lambda r: f"{r['mean_r2']:.3f} ± {r['sd_r2']:.3f}", axis=1
    )
    return cv_summary[["model", "RMSE (mean ± SD)", "R² (mean ± SD)", "n_folds"]]

"""Model evaluation, SHAP analysis, PDP plots, and threshold metrics.

Usage
-----
from evaluation import (
    shap_summary, pdp_plot, threshold_metrics,
    plot_prediction_scatter, save_evaluation_report,
)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

FIGURES_DIR = Path(__file__).parent.parent / "figures"


# ---------------------------------------------------------------------------
# SHAP analysis
# ---------------------------------------------------------------------------

def compute_shap_values(
    model,
    X: pd.DataFrame,
    model_type: str = "tree",
    n_background: int = 100,
    random_state: int = 42,
) -> "shap.Explanation":
    """Return SHAP explanation object for model on X.

    model_type: "tree" for XGBoost/LightGBM, "linear" for Ridge,
                "kernel" for arbitrary sklearn (slow).
    """
    try:
        import shap
    except ImportError:
        raise ImportError("shap required: pip install shap")

    if model_type == "tree":
        explainer = shap.TreeExplainer(model)
        return explainer(X)
    elif model_type == "linear":
        explainer = shap.LinearExplainer(model, X)
        return explainer(X)
    elif model_type == "kernel":
        rng = np.random.default_rng(random_state)
        bg_idx = rng.choice(len(X), size=min(n_background, len(X)), replace=False)
        bg = X.iloc[bg_idx]
        explainer = shap.KernelExplainer(model.predict, bg)
        return explainer.shap_values(X)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def shap_summary(
    shap_values: "shap.Explanation",
    X: pd.DataFrame,
    target_name: str = "target",
    top_n: int = 20,
    save_path: Optional[Path] = None,
    show: bool = False,
) -> pd.DataFrame:
    """Plot SHAP beeswarm summary and return mean |SHAP| per feature."""
    try:
        import shap
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("shap and matplotlib required")

    fig, ax = plt.subplots(figsize=(8, max(4, top_n * 0.3)))
    shap.summary_plot(shap_values, X, max_display=top_n, show=False)
    plt.title(f"SHAP summary — {target_name}")
    plt.tight_layout()
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)

    # Mean absolute SHAP per feature
    if hasattr(shap_values, "values"):
        sv = shap_values.values
    else:
        sv = np.array(shap_values)
    mean_abs = pd.Series(np.abs(sv).mean(axis=0), index=X.columns, name="mean_abs_shap")
    return mean_abs.sort_values(ascending=False).head(top_n).to_frame()


def shap_feature_importance_table(
    shap_values_dict: Dict[str, "shap.Explanation"],
    X: pd.DataFrame,
) -> pd.DataFrame:
    """Combine mean |SHAP| across multiple targets into one table."""
    rows = {}
    for target, sv in shap_values_dict.items():
        if hasattr(sv, "values"):
            arr = sv.values
        else:
            arr = np.array(sv)
        rows[target] = pd.Series(np.abs(arr).mean(axis=0), index=X.columns)
    df = pd.DataFrame(rows)
    df["mean_across_targets"] = df.mean(axis=1)
    return df.sort_values("mean_across_targets", ascending=False)


# ---------------------------------------------------------------------------
# Partial dependence plots
# ---------------------------------------------------------------------------

def pdp_plot(
    model,
    X: pd.DataFrame,
    feature: str,
    n_grid: int = 50,
    target_name: str = "target",
    save_path: Optional[Path] = None,
    show: bool = False,
) -> pd.DataFrame:
    """Compute and plot 1D partial dependence for a single feature.

    Returns DataFrame with columns [feature_value, pdp_mean, pdp_lo, pdp_hi].
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required")

    vals = np.linspace(X[feature].quantile(0.01), X[feature].quantile(0.99), n_grid)
    pdp_means, pdp_los, pdp_his = [], [], []

    X_copy = X.copy()
    for v in vals:
        X_copy[feature] = v
        preds = model.predict(X_copy)
        pdp_means.append(np.mean(preds))
        pdp_los.append(np.percentile(preds, 10))
        pdp_his.append(np.percentile(preds, 90))

    result = pd.DataFrame({
        feature: vals,
        "pdp_mean": pdp_means,
        "pdp_lo": pdp_los,
        "pdp_hi": pdp_his,
    })

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(vals, pdp_means, lw=2)
    ax.fill_between(vals, pdp_los, pdp_his, alpha=0.25)
    ax.set_xlabel(feature)
    ax.set_ylabel(f"Predicted {target_name}")
    ax.set_title(f"PDP — {feature}")
    plt.tight_layout()
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return result


# ---------------------------------------------------------------------------
# Threshold metrics (regulatory relevance)
# ---------------------------------------------------------------------------

# Common soil regulatory thresholds (mg/kg = ppm)
REGULATORY_THRESHOLDS = {
    "Cu_ppm": 100.0,   # EU soil quality guideline (indicative)
    "Zn_ppm": 300.0,
    "Pb_ppm": 100.0,
    "Ni_ppm":  50.0,
}


def threshold_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    target_col: str,
    threshold: Optional[float] = None,
    log_transformed: bool = True,
) -> Dict:
    """Sensitivity/specificity at a regulatory threshold.

    Parameters
    ----------
    y_true : true values (log-transformed if log_transformed=True)
    y_pred : predicted values (same scale as y_true)
    threshold : threshold in original ppm units; if None, uses REGULATORY_THRESHOLDS
    log_transformed : if True, applies np.log1p(threshold) before comparison
    """
    if threshold is None:
        threshold = REGULATORY_THRESHOLDS.get(target_col)
        if threshold is None:
            raise ValueError(f"No default threshold for {target_col}; pass threshold=")

    t = float(np.log1p(threshold)) if log_transformed else float(threshold)
    pos_true = y_true.values >= t
    pos_pred = y_pred >= t

    tp = int((pos_true & pos_pred).sum())
    fn = int((pos_true & ~pos_pred).sum())
    fp = int((~pos_true & pos_pred).sum())
    tn = int((~pos_true & ~pos_pred).sum())

    sens = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    spec = tn / (tn + fp) if (tn + fp) > 0 else np.nan
    ppv = tp / (tp + fp) if (tp + fp) > 0 else np.nan
    npv = tn / (tn + fn) if (tn + fn) > 0 else np.nan

    return {
        "target": target_col,
        "threshold_ppm": threshold,
        "n_above": int(pos_true.sum()),
        "n_below": int((~pos_true).sum()),
        "sensitivity": round(sens, 4),
        "specificity": round(spec, 4),
        "ppv": round(ppv, 4),
        "npv": round(npv, 4),
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
    }


# ---------------------------------------------------------------------------
# Prediction scatter plot
# ---------------------------------------------------------------------------

def plot_prediction_scatter(
    y_true: pd.Series,
    y_pred: np.ndarray,
    target_name: str = "target",
    colour_by: Optional[pd.Series] = None,
    save_path: Optional[Path] = None,
    show: bool = False,
) -> None:
    """Observed-vs-predicted scatter with RMSE annotation."""
    try:
        import matplotlib.pyplot as plt
        from sklearn.metrics import r2_score
    except ImportError:
        raise ImportError("matplotlib and sklearn required")

    y_pred_arr = np.asarray(y_pred, dtype=float)
    y_true_arr = np.asarray(y_true, dtype=float)
    valid = ~np.isnan(y_pred_arr) & ~np.isnan(y_true_arr)
    yt, yp = y_true_arr[valid], y_pred_arr[valid]

    from modelling import rmse
    r2 = r2_score(yt, yp)
    err = rmse(yt, yp)

    fig, ax = plt.subplots(figsize=(5, 5))
    if colour_by is not None:
        sc = ax.scatter(yt, yp, c=colour_by[valid].values, cmap="viridis", alpha=0.5, s=15)
        plt.colorbar(sc, ax=ax, label=colour_by.name)
    else:
        ax.scatter(yt, yp, alpha=0.4, s=15)

    lo, hi = min(yt.min(), yp.min()), max(yt.max(), yp.max())
    ax.plot([lo, hi], [lo, hi], "k--", lw=1)
    ax.set_xlabel(f"Observed log({target_name})")
    ax.set_ylabel(f"Predicted log({target_name})")
    ax.set_title(f"{target_name}: RMSE={err:.3f}, R²={r2:.3f} (n={valid.sum()})")
    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Evaluation report
# ---------------------------------------------------------------------------

def save_evaluation_report(
    results: Dict,
    path: Path,
) -> None:
    """Save a dict of evaluation metrics to CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([results]).to_csv(path, index=False)
    log.info("Saved evaluation report to %s", path)

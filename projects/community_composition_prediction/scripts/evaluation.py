"""Evaluation utilities: SHAP, category aggregation, threshold metrics, plots."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


# ── SHAP ─────────────────────────────────────────────────────────────────────

def compute_shap_importance(model, X: pd.DataFrame, target: str) -> pd.DataFrame:
    """Mean |SHAP| per feature for a tree model (XGBoost or LightGBM).

    Args:
        model: fitted XGBRegressor or LGBMRegressor.
        X: feature DataFrame used for prediction.
        target: label for the 'target' column in the output.

    Returns:
        DataFrame with columns [feature, target, mean_abs_shap] sorted descending.
    """
    import shap
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X)
    importance = pd.DataFrame({
        'feature': X.columns,
        'target': target,
        'mean_abs_shap': np.abs(shap_vals).mean(axis=0),
    }).sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)
    return importance


def aggregate_shap_by_category(shap_df: pd.DataFrame) -> pd.DataFrame:
    """Sum SHAP importance by broad feature category (CLR, GW_*, Env_*, Geochem).

    Category inference from column name prefixes:
        clr_{genus}                         → 'CLR (taxonomy)'
        gw_pca_{i}                          → 'GW_PCA'
        gw_mean_n_metal_clusters_{genus}    → 'GW_metal_clusters'
        gw_mean_n_defense_clusters_{genus}  → 'GW_defense_clusters'
        gw_mean_n_metabolism_clusters_{g}   → 'GW_metabolism_clusters'
        gw_mean_n_homeostasis_clusters_{g}  → 'GW_homeostasis_clusters'
        gw_mean_metal_core_fraction_{genus} → 'GW_metal_core_fraction'
        mob_{metal}                         → 'Env_mobility'
        ph, clay_*, ...                     → 'Env_soil/climate'
        lat, lon                            → 'Geochem'
        CWM_*                               → 'CWM'
    """
    SOIL_ENV = {'ph', 'clay_pct', 'water_content', 'ndvi', 'elevation_m', 'temp_K', 'precip_mm'}
    GW_CATS = [
        ('gw_mean_n_metal_clusters_', 'GW_metal_clusters'),
        ('gw_mean_n_defense_clusters_', 'GW_defense_clusters'),
        ('gw_mean_n_metabolism_clusters_', 'GW_metabolism_clusters'),
        ('gw_mean_n_homeostasis_clusters_', 'GW_homeostasis_clusters'),
        ('gw_mean_metal_core_fraction_', 'GW_metal_core_fraction'),
    ]

    def _cat(feat: str) -> str:
        if feat.startswith('clr_'):
            return 'CLR (taxonomy)'
        if feat.startswith('gw_pca_'):
            return 'GW_PCA'
        for prefix, label in GW_CATS:
            if feat.startswith(prefix):
                return label
        if feat.startswith('gw_'):
            return 'GW_other'
        if feat.startswith('mob_'):
            return 'Env_mobility'
        if feat in SOIL_ENV:
            return 'Env_soil/climate'
        if feat in ('lat', 'lon'):
            return 'Geochem'
        if feat.startswith('CWM_'):
            return 'CWM'
        return 'Other'

    shap_df = shap_df.copy()
    shap_df['category'] = shap_df['feature'].apply(_cat)
    return (
        shap_df.groupby(['target', 'category'])['mean_abs_shap']
        .sum()
        .reset_index()
        .sort_values('mean_abs_shap', ascending=False)
    )


def top_clr_genera(shap_df: pd.DataFrame, target: str, top_n: int = 20) -> pd.DataFrame:
    """Extract top-N CLR genera by mean |SHAP| for a given target."""
    clr = shap_df[(shap_df['target'] == target) & shap_df['feature'].str.startswith('clr_')].copy()
    clr['genus'] = clr['feature'].str.replace('clr_', '', regex=False)
    return clr.nlargest(top_n, 'mean_abs_shap')[['genus', 'mean_abs_shap']].reset_index(drop=True)


# ── Threshold metrics ─────────────────────────────────────────────────────────

REGULATORY_THRESHOLDS = {
    'log_Cu_ppm': np.log1p(100),
    'log_Zn_ppm': np.log1p(300),
    'log_Pb_ppm': np.log1p(100),
    'log_Ni_ppm': np.log1p(50),
}


def threshold_metrics(y_true: np.ndarray, y_pred: np.ndarray, target: str) -> dict:
    """Sensitivity and specificity at the pre-specified regulatory threshold."""
    if target not in REGULATORY_THRESHOLDS:
        return {}
    thresh = REGULATORY_THRESHOLDS[target]
    pos = y_true >= thresh
    pred_pos = y_pred >= thresh
    tp = int((pos & pred_pos).sum())
    fn = int((pos & ~pred_pos).sum())
    tn = int((~pos & ~pred_pos).sum())
    fp = int((~pos & pred_pos).sum())
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else float('nan')
    specificity = tn / (tn + fp) if (tn + fp) > 0 else float('nan')
    return {'tp': tp, 'fn': fn, 'tn': tn, 'fp': fp,
            'sensitivity': sensitivity, 'specificity': specificity, 'threshold': thresh}


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_rmse_comparison(
    cv_results: pd.DataFrame,
    models: list[str],
    targets: list[str],
    out_path: Path | None = None,
) -> None:
    """Bar chart of mean spatial-CV RMSE per model × target."""
    mean_rmse = (
        cv_results[cv_results['model'].isin(models)]
        .groupby(['model', 'target'])['rmse']
        .mean()
        .reset_index()
    )
    fig, axes = plt.subplots(1, len(targets), figsize=(4 * len(targets), 4), sharey=False)
    if len(targets) == 1:
        axes = [axes]
    for ax, target in zip(axes, targets):
        sub = mean_rmse[mean_rmse['target'] == target]
        ax.bar(sub['model'], sub['rmse'])
        ax.set_title(target.replace('log_', '').replace('_ppm', ''))
        ax.set_xlabel('Model')
        ax.set_ylabel('RMSE (log1p)')
        ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_shap_category_bar(
    shap_cat: pd.DataFrame,
    target: str,
    out_path: Path | None = None,
) -> None:
    """Horizontal bar chart of SHAP importance by category for one target."""
    sub = shap_cat[shap_cat['target'] == target].sort_values('mean_abs_shap')
    fig, ax = plt.subplots(figsize=(7, 0.5 * len(sub) + 1))
    ax.barh(sub['category'], sub['mean_abs_shap'])
    ax.set_xlabel('Sum mean |SHAP|')
    ax.set_title(f'SHAP by category — {target}')
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.show()

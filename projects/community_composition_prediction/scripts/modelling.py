"""Model definitions and spatial CV for community_composition_prediction."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# ── Feature set definitions ──────────────────────────────────────────────────

CWM_COLS = [
    'CWM_mean_n_metal_clusters',
    'CWM_mean_n_defense_clusters',
    'CWM_mean_n_metabolism_clusters',
    'CWM_mean_n_homeostasis_clusters',
    'CWM_mean_metal_core_fraction',
]
ENV_COLS = [
    'ph', 'clay_pct', 'water_content', 'ndvi', 'elevation_m',
    'temp_K', 'precip_mm', 'mob_cu', 'mob_pb', 'mob_as', 'mob_cd', 'mob_cr', 'mob_hg',
]
MINE_COLS = [
    'log_mine_prox_km', 'log_tri_prox_km', 'log_npl_prox_km',
    'has_mine_prox_data',   # binary: 1 = within 10 km of a site_classification point
]
GEOCHEM_COLS = ['ph', 'lat', 'lon']  # B2 cheap geochem proxy

TARGETS = ['log_Cu_ppm', 'log_Zn_ppm', 'log_Pb_ppm', 'log_Ni_ppm']

MODEL_DESCRIPTIONS = {
    'B0': 'Intercept-only (training mean)',
    'B1': 'CLR-transformed genus RA only (XGBoost)',
    'B2': 'pH + lat/lon only (ridge)',
    'B3': 'CLR + pH + lat/lon (XGBoost)',
    'B4': 'CWM only (XGBoost)',
    'M1': 'CLR + genus-weighted functional (XGBoost)',
    'M2': 'CLR + genus-weighted functional + env (XGBoost)',
    'M2_mine': 'CLR + GW + env + mine proximity (XGBoost)',
    'M3': 'CLR + CWM + env (XGBoost)',
}


def _clr_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith('clr_')]


def _gw_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith('gw_')]


def _env_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c in ENV_COLS]


def _cwm_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c in CWM_COLS]


def _mine_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c in MINE_COLS]


def get_features(feature_df: pd.DataFrame, model_name: str) -> pd.DataFrame:
    """Return the feature sub-DataFrame for the named model.

    Models:
        B0  — no features (intercept-only; handled separately in CV loop)
        B1  — CLR genus RA columns
        B2  — pH + lat + lon
        B3  — CLR + pH + lat + lon
        B4  — CWM columns
        M1  — CLR + genus-weighted functional
        M2  — CLR + genus-weighted functional + env
        M3  — CLR + CWM + env
    """
    col_getters = {
        'B1': lambda df: df[_clr_cols(df)],
        'B2': lambda df: df[[c for c in GEOCHEM_COLS if c in df.columns]],
        'B3': lambda df: df[_clr_cols(df) + [c for c in GEOCHEM_COLS if c in df.columns]],
        'B4': lambda df: df[_cwm_cols(df)],
        'M1': lambda df: df[_clr_cols(df) + _gw_cols(df)],
        'M2': lambda df: df[_clr_cols(df) + _gw_cols(df) + _env_cols(df)],
        'M2_mine': lambda df: df[_clr_cols(df) + _gw_cols(df) + _env_cols(df) + _mine_cols(df)],
        'M3': lambda df: df[_clr_cols(df) + _cwm_cols(df) + _env_cols(df)],
    }
    if model_name not in col_getters:
        raise ValueError(f'Unknown model: {model_name!r}. Options: {sorted(col_getters)}')
    return col_getters[model_name](feature_df)


# ── Model constructors ────────────────────────────────────────────────────────

def build_xgboost(n_estimators: int = 500, learning_rate: float = 0.05, max_depth: int = 6):
    from xgboost import XGBRegressor
    return XGBRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method='hist',
        random_state=42,
        n_jobs=-1,
    )


def build_lightgbm(n_estimators: int = 500, learning_rate: float = 0.05, num_leaves: int = 63):
    from lightgbm import LGBMRegressor
    return LGBMRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        num_leaves=num_leaves,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )


def build_ridge():
    return Pipeline([('scaler', StandardScaler()), ('ridge', Ridge(alpha=1.0))])


# ── Evaluation ────────────────────────────────────────────────────────────────

def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def _drop_nan_rows(X: pd.DataFrame, y: pd.Series):
    mask = ~(X.isna().any(axis=1) | y.isna())
    return X[mask], y[mask]


# ── Spatial block CV ──────────────────────────────────────────────────────────

def run_spatial_block_cv(
    feature_df: pd.DataFrame,
    target: str,
    model_name: str,
    blocks: pd.Series,
    model_type: str = 'xgboost',
    return_oof: bool = False,
) -> tuple[pd.DataFrame, pd.Series | None]:
    """Leave-one-spatial-block-out cross-validation.

    Args:
        feature_df: sample × feature matrix (must include target column and columns
            needed by model_name).
        target: column name of the log-transformed metal target.
        model_name: one of B1, B2, B3, B4, M1, M2, M3.
        blocks: Series indexed by sample_id with block labels (e.g. from spatial_blocks.csv).
        model_type: 'xgboost', 'lightgbm', or 'ridge'.
        return_oof: if True, also return a Series of OOF predictions.

    Returns:
        (results_df, oof_preds) where oof_preds is None if return_oof=False.
    """
    if model_name == 'B0':
        raise ValueError('B0 is intercept-only; compute RMSE from training mean directly')

    y = feature_df[target]
    X = get_features(feature_df, model_name)
    blocks_aligned = blocks.reindex(feature_df.index)

    oof = pd.Series(np.nan, index=feature_df.index, name=f'{model_name}_{target}')
    results = []

    for test_block in blocks_aligned.dropna().unique():
        test_mask = blocks_aligned == test_block
        train_mask = ~test_mask & blocks_aligned.notna()

        X_train, y_train = _drop_nan_rows(X[train_mask], y[train_mask])
        X_test, y_test = _drop_nan_rows(X[test_mask], y[test_mask])

        if len(X_train) < 20 or len(X_test) < 5:
            continue

        if model_type == 'xgboost':
            m = build_xgboost()
        elif model_type == 'lightgbm':
            m = build_lightgbm()
        elif model_type == 'ridge':
            m = build_ridge()
        else:
            raise ValueError(f'Unknown model_type: {model_type!r}')

        m.fit(X_train, y_train)
        preds = m.predict(X_test)
        oof.loc[X_test.index] = preds

        results.append({
            'model': model_name,
            'target': target,
            'block': test_block,
            'n_train': len(X_train),
            'n_test': len(X_test),
            'rmse': rmse(y_test.values, preds),
        })

    results_df = pd.DataFrame(results)
    return results_df, (oof if return_oof else None)


def fit_final_model(
    feature_df: pd.DataFrame,
    target: str,
    model_name: str,
    model_type: str = 'xgboost',
):
    """Fit a final model on all non-NaN rows of the training set."""
    y = feature_df[target]
    if model_name == 'B0':
        return float(y.dropna().mean())
    X = get_features(feature_df, model_name)
    Xc, yc = _drop_nan_rows(X, y)
    if model_type == 'xgboost':
        m = build_xgboost()
    elif model_type == 'lightgbm':
        m = build_lightgbm()
    elif model_type == 'ridge':
        m = build_ridge()
    else:
        raise ValueError(f'Unknown model_type: {model_type!r}')
    m.fit(Xc, yc)
    return m

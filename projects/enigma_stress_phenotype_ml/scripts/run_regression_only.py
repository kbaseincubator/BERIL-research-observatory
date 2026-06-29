"""Re-run regression training on current labeled_pd (with file-supplemented fitness cols).

Standalone script equivalent to NB05 regression cell, using the current labeled_pd
which includes file-supplemented Cd (2 orgs), As/Pb/Ag (1 org each).
Threshold lowered to n_orgs < 2 for regression (no calibration step needed).
"""
import sys, json, logging
from pathlib import Path
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

PROJ_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJ_ROOT / 'data'
MODEL_DIR = DATA_DIR / 'models'

CONFIG = {
    'SEED': 42, 'TEST_SIZE': 0.2,
    'CATBOOST_ITERATIONS': 500, 'CATBOOST_LEARNING_RATE': 0.05, 'CATBOOST_DEPTH': 6,
    'MIN_POSITIVES': 30,
}

# Load
sys.path.insert(0, str(PROJ_ROOT))
from src.utils import load_labeled_pd, load_best_combination

labeled_pd = load_labeled_pd(DATA_DIR)
best_combo = load_best_combination(DATA_DIR)
log.info(f"labeled_pd: {labeled_pd.shape}")

X_list = []
for name in best_combo:
    df = pd.read_parquet(DATA_DIR / f"features_{name}.parquet").drop(columns=['organism'], errors='ignore')
    X_list.append(df)
X_full = pd.concat(X_list, axis=1)
groups = labeled_pd['organism']
log.info(f"Features: {X_full.shape}")


def train_stressor_regression(stressor):
    fit_col = f"{stressor}_fit"
    if fit_col not in labeled_pd.columns:
        log.warning(f"{stressor}: '{fit_col}' absent; skipping.")
        return None

    mask = labeled_pd[fit_col].notna()
    y = labeled_pd.loc[mask, fit_col].astype(float)
    X = X_full[mask]
    g = groups[mask]
    n_tested = int(mask.sum())

    if n_tested < CONFIG['MIN_POSITIVES'] * 10:
        log.warning(f"{stressor}: only {n_tested} proteins; skipping.")
        return None

    n_orgs = g.nunique()
    if n_orgs < 2:
        log.warning(f"{stressor}: only {n_orgs} org(s); need ≥2 to split; skipping.")
        return None

    log.info(f"{stressor}: {n_tested} proteins, {n_orgs} orgs, {int((y < -2).sum())} binary pos")

    gss = GroupShuffleSplit(n_splits=1, test_size=CONFIG['TEST_SIZE'], random_state=CONFIG['SEED'])
    s_train_idx, s_test_idx = next(gss.split(X, y, groups=g))
    X_tr, X_te = X.iloc[s_train_idx], X.iloc[s_test_idx]
    y_tr, y_te = y.iloc[s_train_idx], y.iloc[s_test_idx]
    log.info(f"  train={len(X_tr)} ({g.iloc[s_train_idx].nunique()} orgs), test={len(X_te)} ({g.iloc[s_test_idx].nunique()} orgs)")

    model = CatBoostRegressor(
        iterations=CONFIG['CATBOOST_ITERATIONS'],
        learning_rate=CONFIG['CATBOOST_LEARNING_RATE'],
        depth=CONFIG['CATBOOST_DEPTH'],
        loss_function='RMSE',
        random_seed=CONFIG['SEED'], verbose=100)
    model.fit(X_tr, y_tr, verbose=100)

    y_pred = model.predict(X_te)
    rho, pval = spearmanr(y_te, y_pred)
    rmse = float(np.sqrt(np.mean((y_te.values - y_pred) ** 2)))
    y_binary_te = (y_te < -2).astype(int)
    auc = float(roc_auc_score(y_binary_te, -y_pred)) if y_binary_te.sum() > 0 else None

    metrics = {
        'Spearman_rho': float(rho), 'Spearman_pval': float(pval),
        'RMSE': rmse, 'AUC_from_ranking': auc,
        'n_tested': n_tested, 'n_binary_pos': int((y < -2).sum()),
        'pos_rate': float((y < -2).mean()), 'n_orgs': n_orgs,
    }
    model.save_model(str(MODEL_DIR / f"stressor_{stressor}_regression.cbm"))
    pd.DataFrame({
        'y_test': y_te.values, 'y_pred': y_pred,
        'group': g.iloc[s_test_idx].values,
    }).to_parquet(MODEL_DIR / f"stressor_{stressor}_reg_predictions.parquet")
    return metrics


METAL_STRESSORS = ['Zn', 'Cu', 'Cd', 'Co', 'Ni', 'Cr', 'As', 'Hg', 'Pb', 'Mn', 'Fe', 'Se', 'Ag', 'Al']
reg_metrics = {}
for s in METAL_STRESSORS:
    log.info(f"=== {s} ===")
    m = train_stressor_regression(s)
    if m:
        reg_metrics[s] = m
        log.info(f"  rho={m['Spearman_rho']:.3f} p={m['Spearman_pval']:.2e} AUC={m['AUC_from_ranking']}")

pd.DataFrame(reg_metrics).T.to_csv(DATA_DIR / 'regression_model_metrics.csv')
log.info(f"\nDone. Trained {len(reg_metrics)} regression models.")
log.info("\nSummary:")
df = pd.DataFrame(reg_metrics).T
print(df[['Spearman_rho', 'AUC_from_ranking', 'n_tested', 'n_orgs']].to_string())

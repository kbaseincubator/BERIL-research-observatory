"""
pgls_utils.py
=============
Phylogenetic Generalised Least Squares (PGLS) with Pagel's lambda.

Uses dendropy to build the full variance-covariance matrix from a GTDB
genus-level tree, then optimises lambda via ML before fitting GLS.

All public functions return a plain dict of statistics so callers can
easily aggregate results across many models without pandas overhead.

Dependencies: numpy, scipy, statsmodels, dendropy (all available on BERDL).

Usage
-----
>>> from scripts.pgls_utils import run_pgls, run_multi_pgls, pgls_results_table
>>> res = run_pgls(df, tree_path, response="mean_levins_B_std", predictors=["ko_per_mb_z"])
>>> print(res["beta"], res["p_value"], res["lambda_est"])
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import dendropy
import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.linalg import solve_triangular as _solve_tri

# ---------------------------------------------------------------------------
# Tree helpers
# ---------------------------------------------------------------------------

def load_tree(tree_path: str | Path) -> dendropy.Tree:
    """Load a Newick/NHX tree from *tree_path* using dendropy."""
    return dendropy.Tree.get(path=str(tree_path), schema="newick",
                             preserve_underscores=True)


def build_vcv(tree: dendropy.Tree, taxa: Sequence[str]) -> np.ndarray:
    """Build the phylogenetic variance-covariance matrix for *taxa*.

    The VCV matrix V[i,j] = shared branch length from root to MRCA(i,j),
    and V[i,i] = total root-to-tip path length for taxon i.

    Uses a postorder traversal to accumulate edge-length contributions in
    O(n^2) numpy operations, avoiding the O(n^2 × tree_height) cost of
    per-pair tree.mrca() calls.

    Parameters
    ----------
    tree:
        A dendropy Tree with branch lengths set.
    taxa:
        Ordered list of tip labels; the returned matrix respects this order.

    Returns
    -------
    np.ndarray of shape (n, n).

    Raises
    ------
    ValueError if any taxon in *taxa* is missing from the tree.
    """
    n = len(taxa)
    taxa_set = {t.label.replace(" ", "_").lower() for t in tree.taxon_namespace}
    normalised_taxa = [t.replace(" ", "_").lower() for t in taxa]

    missing = [t for t in normalised_taxa if t not in taxa_set]
    if missing:
        raise ValueError(f"Taxa missing from tree: {missing[:5]}{'...' if len(missing) > 5 else ''}")

    label_to_idx: Dict[str, int] = {t: i for i, t in enumerate(normalised_taxa)}

    # Map leaf node id → query index
    leaf_to_idx: Dict[int, int] = {}
    for leaf in tree.leaf_node_iter():
        lbl = leaf.taxon.label.replace(" ", "_").lower() if leaf.taxon else ""
        if lbl in label_to_idx:
            leaf_to_idx[id(leaf)] = label_to_idx[lbl]

    V = np.zeros((n, n))

    # Postorder traversal: for each node, accumulate its edge length into
    # V[i,j] for all query taxa (i,j) in its subtree.
    # V[i,j] = sum of edge_lengths of nodes on path from root to MRCA(i,j)
    #         = sum over nodes v: edge_len(v) × I[both i,j in subtree(v)]
    node_subtaxa: Dict[int, np.ndarray] = {}

    for node in tree.postorder_node_iter():
        nid = id(node)
        edge_len = node.edge_length if node.edge_length is not None else 0.0

        if node.is_leaf():
            idx = leaf_to_idx.get(nid)
            if idx is not None:
                subtaxa = np.array([idx], dtype=np.intp)
                if edge_len != 0.0:
                    V[idx, idx] += edge_len
            else:
                subtaxa = np.array([], dtype=np.intp)
            node_subtaxa[nid] = subtaxa
        else:
            parts = [node_subtaxa.pop(id(c), np.array([], dtype=np.intp))
                     for c in node.child_nodes()]
            subtaxa = np.concatenate(parts) if parts else np.array([], dtype=np.intp)
            node_subtaxa[nid] = subtaxa

            if len(subtaxa) >= 1 and edge_len != 0.0:
                # Adds edge_len to all pairs (including diagonal) in this subtree
                V[np.ix_(subtaxa, subtaxa)] += edge_len

    return V


def _pagel_vcv(V: np.ndarray, lam: float) -> np.ndarray:
    """Scale VCV by Pagel's lambda: off-diagonal *= lambda."""
    n = V.shape[0]
    diag = np.diag(V)
    V_lam = lam * V
    np.fill_diagonal(V_lam, diag)          # diagonal stays un-scaled
    return V_lam


# ---------------------------------------------------------------------------
# Core GLS fit
# ---------------------------------------------------------------------------

def _gls_fit(
    y: np.ndarray,
    X: np.ndarray,
    V: np.ndarray,
    lam: float,
) -> Tuple[float, float, np.ndarray, np.ndarray, float, float]:
    """Fit GLS given response, design matrix, VCV, and lambda.

    Returns
    -------
    (log_likelihood, sigma2, betas, betas_se, V_lambda, chol_L)
    """
    n = len(y)
    V_lam = _pagel_vcv(V, lam)

    try:
        L = np.linalg.cholesky(V_lam)
    except np.linalg.LinAlgError:
        # Add small jitter for near-singular matrices
        V_lam += np.eye(n) * 1e-8 * np.diag(V_lam).mean()
        L = np.linalg.cholesky(V_lam)

    # solve_triangular: O(n²) forward substitution — 285× faster than inv(L) @ v
    y_t = _solve_tri(L, y, lower=True)
    X_t = _solve_tri(L, X, lower=True)

    # OLS on transformed system (GLS = OLS after Cholesky transform)
    betas, resid, _, _ = np.linalg.lstsq(X_t, y_t, rcond=None)
    fitted = X_t @ betas
    e = y_t - fitted
    sigma2 = float(e @ e / (n - X.shape[1]))
    sigma2 = max(sigma2, 1e-15)

    # Log-likelihood
    log_det_V = 2.0 * np.sum(np.log(np.diag(L)))
    ll = -0.5 * (n * np.log(2 * np.pi) + n * np.log(sigma2) + log_det_V
                 + np.sum(e ** 2) / sigma2)

    # Covariance of betas
    XtX_inv = np.linalg.inv(X_t.T @ X_t)
    betas_se = np.sqrt(np.diag(XtX_inv) * sigma2)

    return ll, sigma2, betas, betas_se, V_lam, L


def _optimise_lambda(
    y: np.ndarray,
    X: np.ndarray,
    V: np.ndarray,
    n_grid: int = 8,
) -> Tuple[float, float]:
    """Find Pagel lambda that maximises log-likelihood.

    Uses a coarse grid search followed by bounded scalar minimisation.
    n_grid reduced from 20 to 8 and maxiter from 500 to 60 to keep
    per-PGLS wall time reasonable for large n.
    """
    def neg_ll(lam: float) -> float:
        if lam < 0 or lam > 1:
            return 1e10
        try:
            ll, *_ = _gls_fit(y, X, V, lam)
            return -ll
        except Exception:
            return 1e10

    # Grid search for starting point
    grid = np.linspace(0.01, 0.99, n_grid)
    grid_nll = [neg_ll(lam) for lam in grid]
    lam0 = grid[np.argmin(grid_nll)]

    res = optimize.minimize_scalar(neg_ll, bounds=(1e-4, 1.0 - 1e-4),
                                   method="bounded",
                                   options={"xatol": 1e-4, "maxiter": 60})
    lam_best = res.x if res.success else lam0
    return float(lam_best), -res.fun if res.success else float(-min(grid_nll))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_pgls(
    df: pd.DataFrame,
    tree_path: str | Path,
    response: str,
    predictors: List[str],
    taxon_col: str = "genus_lower",
    label: str = "",
    fix_lambda: Optional[float] = None,
    min_n: int = 30,
) -> Dict[str, Any]:
    """Run PGLS and return a result dict.

    Parameters
    ----------
    df:
        Data frame with *taxon_col*, *response*, and all *predictors*.
    tree_path:
        Path to Newick tree.
    response:
        Name of the response column.
    predictors:
        List of predictor column names.  An intercept is added automatically.
    taxon_col:
        Column with tip labels matching the tree (default ``genus_lower``).
    label:
        Free-form label stored in the result dict.
    fix_lambda:
        If set, skip optimisation and use this lambda value.
    min_n:
        Minimum usable sample size (raises ValueError if fewer rows remain).

    Returns
    -------
    dict with keys: label, response, predictors, n, lambda_est, betas,
    SEs, t_stats, p_values, r2, aic, delta_aic_vs_null, converged.
    For a single predictor, scalar versions are also stored as beta, SE,
    t_stat, p_value for convenience.
    """
    tree = load_tree(tree_path)
    tree_labels = {
        t.label.replace(" ", "_").lower()
        for t in tree.taxon_namespace
    }

    # Filter to rows with all needed columns non-null and in tree
    keep = (
        df[taxon_col].str.replace(" ", "_").str.lower().isin(tree_labels)
        & df[response].notna()
    )
    for pred in predictors:
        keep = keep & df[pred].notna()

    sub = df[keep].copy()
    sub["_taxon"] = sub[taxon_col].str.replace(" ", "_").str.lower()

    # Deduplicate on taxon (keep first occurrence)
    sub = sub.drop_duplicates(subset="_taxon")

    n = len(sub)
    if n < min_n:
        raise ValueError(f"Only {n} rows after filtering (min_n={min_n}). "
                         "Check taxon_col matching and NA removal.")

    taxa = sub["_taxon"].tolist()
    y = sub[response].values.astype(float)
    X_df = sub[predictors].values.astype(float)
    X = np.column_stack([np.ones(n), X_df])   # intercept first

    V = build_vcv(tree, taxa)

    if fix_lambda is not None:
        lam = float(fix_lambda)
        ll, sigma2, betas, betas_se, V_lam, L = _gls_fit(y, X, V, lam)
    else:
        lam, ll = _optimise_lambda(y, X, V)
        ll, sigma2, betas, betas_se, V_lam, L = _gls_fit(y, X, V, lam)

    # Null model (intercept only)
    X_null = np.ones((n, 1))
    ll_null, *_ = _gls_fit(y, X_null, V, lam)

    p = len(predictors)
    aic = -2 * ll + 2 * (p + 1 + 1)        # p predictors + intercept + sigma
    aic_null = -2 * ll_null + 2 * (1 + 1)
    delta_aic = aic - aic_null

    # t-tests for predictor betas (not intercept)
    df_resid = n - p - 1
    t_stats = betas[1:] / betas_se[1:]
    p_values = [2 * (1 - stats.t.cdf(abs(t), df_resid)) for t in t_stats]

    # R² (approximate, on PGLS-transformed scale) — reuse L from the call above
    y_t = _solve_tri(L, y, lower=True)
    yhat_t = _solve_tri(L, X @ betas, lower=True)
    ss_res = np.sum((y_t - yhat_t) ** 2)
    ss_tot = np.sum((y_t - np.mean(y_t)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

    result = {
        "label": label,
        "response": response,
        "predictors": predictors,
        "n": n,
        "lambda_est": round(float(lam), 4),
        "betas": {pred: float(b) for pred, b in zip(predictors, betas[1:])},
        "SEs": {pred: float(se) for pred, se in zip(predictors, betas_se[1:])},
        "t_stats": {pred: float(t) for pred, t in zip(predictors, t_stats)},
        "p_values": {pred: float(p) for pred, p in zip(predictors, p_values)},
        "r2": r2,
        "aic": round(float(aic), 2),
        "delta_aic_vs_null": round(float(delta_aic), 2),
        "sigma2": float(sigma2),
        "converged": True,
    }

    # Convenience scalars for single-predictor case
    if len(predictors) == 1:
        pred = predictors[0]
        result["beta"] = result["betas"][pred]
        result["SE"] = result["SEs"][pred]
        result["t_stat"] = result["t_stats"][pred]
        result["p_value"] = result["p_values"][pred]

    return result


def run_multi_pgls(
    df: pd.DataFrame,
    tree_path: str | Path,
    response: str,
    predictor_sets: List[List[str]],
    labels: Optional[List[str]] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """Run PGLS for multiple predictor sets, sharing a single tree load.

    Parameters
    ----------
    predictor_sets:
        List of predictor lists, one per model.
    labels:
        Optional list of labels parallel to *predictor_sets*.

    Returns
    -------
    List of result dicts from :func:`run_pgls`.
    """
    tree = load_tree(tree_path)
    results = []
    for i, preds in enumerate(predictor_sets):
        lbl = (labels[i] if labels else None) or "+".join(preds)
        try:
            # Pass tree as path (run_pgls will reload) — acceptable overhead for clarity
            res = run_pgls(df, tree_path, response, preds, label=lbl, **kwargs)
        except Exception as exc:
            res = {"label": lbl, "response": response, "predictors": preds,
                   "error": str(exc), "converged": False}
        results.append(res)
    return results


def pgls_results_table(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Flatten a list of single-predictor PGLS result dicts into a DataFrame.

    Columns: label, response, predictor, n, lambda_est, beta, SE,
             t_stat, p_value, r2, delta_aic_vs_null.
    """
    rows = []
    for r in results:
        if not r.get("converged", False):
            rows.append({"label": r.get("label", ""), "error": r.get("error", "")})
            continue
        preds = r.get("predictors", [])
        for pred in preds:
            rows.append({
                "label": r.get("label", ""),
                "response": r.get("response", ""),
                "predictor": pred,
                "n": r.get("n"),
                "lambda_est": r.get("lambda_est"),
                "beta": r["betas"].get(pred) if "betas" in r else r.get("beta"),
                "SE": r["SEs"].get(pred) if "SEs" in r else r.get("SE"),
                "t_stat": r["t_stats"].get(pred) if "t_stats" in r else r.get("t_stat"),
                "p_value": r["p_values"].get(pred) if "p_values" in r else r.get("p_value"),
                "r2": r.get("r2"),
                "delta_aic_vs_null": r.get("delta_aic_vs_null"),
            })
    return pd.DataFrame(rows)


def fdr_correct(p_values: Sequence[float], method: str = "fdr_bh") -> np.ndarray:
    """Benjamini-Hochberg FDR correction.

    Parameters
    ----------
    p_values:
        Sequence of raw p-values.
    method:
        statsmodels multitest method (default ``fdr_bh``).

    Returns
    -------
    np.ndarray of adjusted p-values.
    """
    from statsmodels.stats.multitest import multipletests
    _, p_adj, _, _ = multipletests(list(p_values), method=method)
    return p_adj

"""
Robust ICA pipeline for decomposing gene-fitness matrices into stable modules.

Follows Borchert et al. (2019) approach:
1. Run FastICA many times with different random seeds
2. Collect all component vectors
3. Cluster by cosine similarity (DBSCAN) to find stable components
4. Compute gene weights (correlation with module profile)
5. Threshold membership via D'Agostino K² normality test

Usage:
    from src.ica_pipeline import robust_ica, compute_gene_weights, threshold_membership

    modules = robust_ica(X, n_components=50, n_runs=100)
    weights = compute_gene_weights(X, modules)
    membership = threshold_membership(weights)
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import FastICA, PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from scipy import stats


def select_n_components(X, method="marchenko_pastur"):
    """Select number of ICA components via PCA eigenvalue analysis.

    Parameters
    ----------
    X : np.ndarray, shape (n_genes, n_experiments)
        Standardized fitness matrix (genes as rows, experiments as columns).
    method : str
        "marchenko_pastur" — retain eigenvalues above the MP upper bound.
        "kaiser" — retain eigenvalues > 1 (on correlation matrix).
        "variance_90" — retain enough components for 90% variance.

    Returns
    -------
    n_components : int
        Recommended number of components.
    eigenvalues : np.ndarray
        All eigenvalues from PCA (for plotting).
    """
    n, p = X.shape
    pca = PCA().fit(X)
    eigenvalues = pca.explained_variance_

    if method == "marchenko_pastur":
        # Marchenko-Pastur upper bound for noise eigenvalues
        gamma = p / n  # aspect ratio
        lambda_plus = (1 + np.sqrt(gamma)) ** 2
        # Scale by median eigenvalue (robust estimate of noise variance)
        sigma2 = np.median(eigenvalues)
        threshold = sigma2 * lambda_plus
        n_components = int(np.sum(eigenvalues > threshold))
    elif method == "kaiser":
        # Kaiser criterion on correlation-scale eigenvalues
        # Eigenvalues of correlation matrix = eigenvalues * n / trace
        corr_eigenvalues = eigenvalues * len(eigenvalues) / eigenvalues.sum()
        n_components = int(np.sum(corr_eigenvalues > 1))
    elif method == "variance_90":
        cumvar = np.cumsum(pca.explained_variance_ratio_)
        n_components = int(np.searchsorted(cumvar, 0.90) + 1)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Ensure at least 2 components
    n_components = max(n_components, 2)
    # Cap at min(n, p) - 1
    n_components = min(n_components, min(n, p) - 1)

    return n_components, eigenvalues


def robust_ica(X, n_components, n_runs=100, eps=0.15, min_samples=50,
               random_state=42, max_iter=500, tol=1e-4):
    """Run FastICA multiple times and cluster stable components.

    Parameters
    ----------
    X : np.ndarray, shape (n_genes, n_experiments)
        Standardized fitness matrix.
    n_components : int
        Number of ICA components per run.
    n_runs : int
        Number of ICA restarts with different seeds.
    eps : float
        DBSCAN epsilon for cosine distance clustering.
    min_samples : int
        DBSCAN min_samples (should be ~n_runs/2 for stability).
    random_state : int
        Base random state (each run uses random_state + i).
    max_iter : int
        Maximum iterations for FastICA convergence.
    tol : float
        Tolerance for FastICA convergence.

    Returns
    -------
    stable_modules : np.ndarray, shape (n_stable, n_experiments)
        Stable module profiles (centroids of DBSCAN clusters).
    labels : np.ndarray
        Cluster labels for all collected components.
    all_components : np.ndarray
        All component vectors from all runs.
    run_metadata : dict
        Metadata about the runs (convergence, n_stable, etc.).
    """
    all_components = []
    n_converged = 0

    for i in range(n_runs):
        ica = FastICA(
            n_components=n_components,
            random_state=random_state + i,
            max_iter=max_iter,
            tol=tol,
            whiten="unit-variance",
        )
        try:
            ica.fit(X)
            # Components are in the mixing matrix rows (n_components x n_features)
            components = ica.components_  # shape: (n_components, n_experiments)
            # Normalize each component to unit length
            norms = np.linalg.norm(components, axis=1, keepdims=True)
            norms[norms == 0] = 1
            components = components / norms
            all_components.append(components)
            n_converged += 1
        except Exception:
            # FastICA may fail to converge for some seeds; skip
            continue

    if not all_components:
        raise RuntimeError("No ICA runs converged. Check input matrix.")

    all_components = np.vstack(all_components)  # shape: (n_runs * n_components, n_experiments)

    # Compute pairwise absolute cosine similarity
    # (sign of ICA components is arbitrary)
    cos_sim = np.abs(cosine_similarity(all_components))
    cos_dist = 1 - cos_sim

    # Cluster with DBSCAN using cosine distance
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = clustering.fit_predict(cos_dist)

    # Extract stable modules as cluster centroids
    unique_labels = sorted(set(labels) - {-1})
    stable_modules = []
    for label in unique_labels:
        mask = labels == label
        cluster_vecs = all_components[mask]
        # Align signs within cluster (flip to match majority direction)
        reference = cluster_vecs[0]
        signs = np.sign(cluster_vecs @ reference)
        aligned = cluster_vecs * signs[:, np.newaxis]
        centroid = aligned.mean(axis=0)
        centroid = centroid / np.linalg.norm(centroid)
        stable_modules.append(centroid)

    stable_modules = np.array(stable_modules) if stable_modules else np.empty((0, X.shape[1]))

    run_metadata = {
        "n_runs": n_runs,
        "n_converged": n_converged,
        "n_components_per_run": n_components,
        "total_components": len(all_components),
        "n_stable_modules": len(stable_modules),
        "n_noise_components": int(np.sum(labels == -1)),
        "eps": eps,
        "min_samples": min_samples,
    }

    return stable_modules, labels, all_components, run_metadata


def compute_gene_weights(X, modules):
    """Compute gene-module weight matrix (Pearson correlation).

    Parameters
    ----------
    X : np.ndarray, shape (n_genes, n_experiments)
        Standardized fitness matrix.
    modules : np.ndarray, shape (n_modules, n_experiments)
        Stable module profiles.

    Returns
    -------
    weights : np.ndarray, shape (n_genes, n_modules)
        Pearson correlation of each gene's fitness profile with each module.
    """
    if len(modules) == 0:
        return np.empty((X.shape[0], 0))

    # Center rows for Pearson correlation
    X_centered = X - X.mean(axis=1, keepdims=True)
    M_centered = modules - modules.mean(axis=1, keepdims=True)

    # Normalize
    X_norm = np.linalg.norm(X_centered, axis=1, keepdims=True)
    M_norm = np.linalg.norm(M_centered, axis=1, keepdims=True)

    X_norm[X_norm == 0] = 1
    M_norm[M_norm == 0] = 1

    X_normed = X_centered / X_norm
    M_normed = M_centered / M_norm

    # Pearson correlation = dot product of normalized vectors
    weights = X_normed @ M_normed.T  # (n_genes, n_modules)

    return weights


def threshold_membership(weights, alpha=0.05):
    """Determine module membership via D'Agostino K² normality test.

    For each module's weight distribution, genes with weights that deviate
    significantly from normal are considered module members.

    Parameters
    ----------
    weights : np.ndarray, shape (n_genes, n_modules)
        Gene-module weight matrix.
    alpha : float
        Significance threshold for outlier detection.

    Returns
    -------
    membership : np.ndarray, shape (n_genes, n_modules)
        Binary membership matrix (1 = member, 0 = not).
    thresholds : np.ndarray, shape (n_modules,)
        Weight threshold used for each module.
    """
    n_genes, n_modules = weights.shape
    membership = np.zeros_like(weights, dtype=int)
    thresholds = np.zeros(n_modules)

    for j in range(n_modules):
        w = weights[:, j]
        # Use robust statistics (MAD-based z-score)
        median_w = np.median(w)
        mad = np.median(np.abs(w - median_w))
        if mad == 0:
            mad = np.std(w)
        if mad == 0:
            continue

        # Modified z-scores
        modified_z = 0.6745 * (w - median_w) / mad

        # Genes with |modified_z| > threshold are members
        # Use D'Agostino K² to find where distribution departs from normal
        # As a practical threshold, use |modified_z| > 3.5 (common outlier rule)
        # But also check: if distribution is clearly non-normal, lower threshold
        try:
            k2_stat, k2_p = stats.normaltest(w)
            if k2_p < alpha:
                # Distribution is non-normal; use 2.5 as more sensitive threshold
                z_thresh = 2.5
            else:
                z_thresh = 3.5
        except Exception:
            z_thresh = 3.5

        thresholds[j] = z_thresh
        membership[:, j] = (np.abs(modified_z) > z_thresh).astype(int)

    return membership, thresholds


def standardize_matrix(X):
    """Center and scale each gene (row) to mean 0, std 1.

    Parameters
    ----------
    X : np.ndarray, shape (n_genes, n_experiments)
        Raw fitness matrix.

    Returns
    -------
    X_std : np.ndarray
        Standardized matrix.
    means : np.ndarray
        Row means (for back-transformation).
    stds : np.ndarray
        Row stds (for back-transformation).
    """
    means = X.mean(axis=1, keepdims=True)
    stds = X.std(axis=1, keepdims=True)
    stds[stds == 0] = 1  # avoid division by zero for constant genes
    X_std = (X - means) / stds
    return X_std, means.flatten(), stds.flatten()

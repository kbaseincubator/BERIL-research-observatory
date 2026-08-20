#!/usr/bin/env python3
"""
build_spatial_covariates.py

Extends covariate_matrix_634_v2.csv with spatial trend surface terms:
    sp_lat, sp_lon, sp_lat2, sp_lon2, sp_latlon
    (centered and unit-scaled for numerical stability)

Also computes the first 30 Moran eigenvector map (MEM/PCNM) eigenvectors
as sp_mem01 .. sp_mem30 — positive eigenvalue only.

Output: covariate_matrix_634_spatial.csv

Usage: python3 build_spatial_covariates.py
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial.distance import cdist

DATA = Path("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/usa_cwm")

cov = pd.read_csv(DATA / "covariate_matrix_634_v2.csv", keep_default_na=False, na_values=[''])
print(f"Loaded: {cov.shape[0]} rows × {cov.shape[1]} cols")

lat = cov['lat'].values.copy()
lon = cov['lon'].values.copy()

# ── Polynomial spatial trend surface ─────────────────────────────────────────
# Center and scale so that lat² and lat*lon don't swamp linear terms
lat_c = (lat - lat.mean()) / lat.std()
lon_c = (lon - lon.mean()) / lon.std()

cov['sp_lat']    = lat_c
cov['sp_lon']    = lon_c
cov['sp_lat2']   = lat_c ** 2
cov['sp_lon2']   = lon_c ** 2
cov['sp_latlon'] = lat_c * lon_c

print("Spatial trend surface terms added: sp_lat, sp_lon, sp_lat2, sp_lon2, sp_latlon")

# ── Moran Eigenvector Maps (MEM / PCNM) ──────────────────────────────────────
# Build truncated spatial weights matrix W:
#   w_ij = 1 - (d_ij / d_max)^2  if d_ij <= d_thresh
#         = 0                      otherwise
# d_thresh: ~4 × median NN distance (captures regional autocorrelation)
print("\nComputing MEM eigenvectors...")
coords = np.column_stack([lat_c, lon_c])
D = cdist(coords, coords)

# Nearest-neighbour distances for threshold selection
nn_dists = np.sort(D, axis=1)[:, 1]  # skip self (column 0)
d_thresh = 4.0 * np.median(nn_dists)
print(f"  NN distance median: {np.median(nn_dists):.3f} (scaled units)")
print(f"  Truncation threshold d_thresh: {d_thresh:.3f}")

W = np.where(D <= d_thresh, 1.0 - (D / d_thresh) ** 2, 0.0)
np.fill_diagonal(W, 0.0)

# Double-centre W to get Ω = (I - 11'/n) W (I - 11'/n)
n = len(lat)
H = np.eye(n) - np.ones((n, n)) / n
Omega = H @ W @ H

# Symmetric eigendecomposition
eigvals, eigvecs = np.linalg.eigh(Omega)
# eigh returns ascending order — reverse
eigvals = eigvals[::-1]
eigvecs = eigvecs[:, ::-1]

# Select positive eigenvalue vectors (carry positive Moran's I)
pos_mask = eigvals > 1e-8
n_pos = pos_mask.sum()
print(f"  Positive eigenvalues: {n_pos} / {n} total")

n_mem = min(30, n_pos)
mem_vecs = eigvecs[:, :n_mem]
for k in range(n_mem):
    col = f"sp_mem{k+1:02d}"
    cov[col] = mem_vecs[:, k]

print(f"  MEM columns added: sp_mem01 .. sp_mem{n_mem:02d}")
print(f"  Cumulative variance explained: {100*eigvals[:n_mem].sum()/eigvals[eigvals>0].sum():.1f}%")

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = DATA / "covariate_matrix_634_spatial.csv"
cov.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}  ({cov.shape[0]} × {cov.shape[1]} cols)")

sp_cols = [c for c in cov.columns if c.startswith('sp_')]
print(f"Spatial columns ({len(sp_cols)}): {', '.join(sp_cols)}")

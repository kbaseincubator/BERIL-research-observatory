"""Compute phylogenetic PCs from GTDB taxonomy for MGnify KO-matrix MAGs.

Encodes GTDB taxonomy (phylum, class, order, family, genus) as a binary matrix,
runs TruncatedSVD to extract top N principal components, and saves the PC scores
as mgnify_phylo_pcs.csv. These PCs serve as continuous proxies for phylogenetic
structure in the NB05 phylo-PC logistic regression model.

Usage:
    python compute_phylo_pcs.py

Output:
    data/mgnify_phylo_pcs.csv  (genome_id index, columns phylo_pc1..phylo_pcN)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
GEO_PATH = (
    PROJECT_DIR.parent / 'microbeatlas_metal_ecology' / 'data'
    / 'final_mags_geospatial_traits.csv'
)
KO_PARQUET = DATA_DIR / 'mgnify_all_ko_matrix.parquet'
OUTPUT = DATA_DIR / 'mgnify_phylo_pcs.csv'
N_PCS = 20


def main() -> None:
    print('Loading KO matrix MAG IDs...', flush=True)
    ko_mags = pd.read_parquet(KO_PARQUET, columns=['genome_id'])['genome_id'].unique()
    print(f'  {len(ko_mags):,} MAGs in KO matrix')

    print('Loading GTDB taxonomy from geospatial traits...', flush=True)
    geo = pd.read_csv(
        GEO_PATH,
        usecols=['genome_id', 'phylum', 'class', 'order', 'family', 'genus'],
    )
    geo = geo[geo['genome_id'].isin(ko_mags)].copy()
    geo = geo.set_index('genome_id')
    print(f'  {len(geo):,} MAGs matched; {geo.isnull().any(axis=1).sum()} have ≥1 null tax level')

    tax_cols = ['phylum', 'class', 'order', 'family', 'genus']
    for col in tax_cols:
        geo[col] = geo[col].fillna('Unknown_' + col)

    print('One-hot encoding taxonomy levels...', flush=True)
    dummies = pd.get_dummies(geo[tax_cols], dtype=float)
    print(f'  Binary matrix: {dummies.shape[0]:,} × {dummies.shape[1]:,}')

    print(f'Running TruncatedSVD for top {N_PCS} PCs...', flush=True)
    svd = TruncatedSVD(n_components=N_PCS, random_state=42)
    pcs = svd.fit_transform(dummies)
    explained = svd.explained_variance_ratio_
    cumvar = np.cumsum(explained)
    print(f'  PC1 explains {explained[0]:.1%}; PC1–{N_PCS} cumulative: {cumvar[-1]:.1%}')
    for i in [4, 9, 14, 19]:
        print(f'  PC1–{i+1}: {cumvar[i]:.1%}')

    pc_df = pd.DataFrame(
        pcs,
        index=geo.index,
        columns=[f'phylo_pc{i + 1}' for i in range(N_PCS)],
    )
    pc_df.index.name = 'genome_id'
    pc_df.to_csv(OUTPUT)
    print(f'Saved: {OUTPUT}  ({len(pc_df):,} rows × {N_PCS} PCs)', flush=True)


if __name__ == '__main__':
    main()

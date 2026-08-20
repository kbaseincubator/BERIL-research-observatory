"""CLR transform and genus-weighted functional feature computation."""
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


def clr_transform(genus_ra_wide: pd.DataFrame, pseudocount: float = 1e-6) -> pd.DataFrame:
    """CLR-transform a sample × genus relative abundance matrix.

    Adds a uniform pseudocount before log to handle zeros, renormalises, then
    subtracts the per-sample log geometric mean (CLR centre).

    Args:
        genus_ra_wide: DataFrame (samples × genera), rows should sum to ~1.
        pseudocount: small value added to every entry before computing log.

    Returns:
        DataFrame same shape with prefix 'clr_' added to column names.
    """
    X = genus_ra_wide.fillna(0).astype(float) + pseudocount
    X = X.div(X.sum(axis=1), axis=0)
    log_X = np.log(X)
    clr = log_X.subtract(log_X.mean(axis=1), axis=0)
    clr.columns = [f'clr_{g}' for g in genus_ra_wide.columns]
    return clr


def select_top_genera(
    genus_ra_wide: pd.DataFrame,
    top_n: int = 200,
    by: str = 'mean_ra',
) -> pd.DataFrame:
    """Return genus_ra_wide restricted to top-N genera.

    Args:
        genus_ra_wide: samples × genera RA DataFrame.
        top_n: number of genera to keep.
        by: 'mean_ra' (rank by mean RA) or 'prevalence' (rank by non-zero fraction).
    """
    if by == 'mean_ra':
        scores = genus_ra_wide.mean(axis=0)
    elif by == 'prevalence':
        scores = (genus_ra_wide > 0).mean(axis=0)
    else:
        raise ValueError(f"by must be 'mean_ra' or 'prevalence', got {by!r}")
    top = scores.nlargest(top_n).index
    return genus_ra_wide[top]


def compute_genus_weighted_features(
    genus_ra_wide: pd.DataFrame,
    densities: pd.DataFrame,
    top_n_per_cat: int = 20,
    n_pca: int = 10,
) -> pd.DataFrame:
    """Genus-weighted functional features (top-N per category + PCA).

    Unlike CWM (which collapses each category to a single sample-level scalar),
    this preserves genus-level resolution: each feature is RA_g × density_gk for
    the top-contributing genera per functional category k.

    Args:
        genus_ra_wide: samples × genera RA (values in [0, 1]).
        densities: genera × categories density matrix (genus_trait_table.csv DENSITY_COLS).
        top_n_per_cat: number of top genera to retain per category (ranked by mean
            contribution across samples).
        n_pca: number of PCA components of the full genus×category contribution matrix.
            Set to 0 to skip PCA.

    Returns:
        DataFrame (samples × [top_n_per_cat × n_categories + n_pca]) named
        'gw_{category}_{genus}' and 'gw_pca_{i}'.
    """
    common_genera = genus_ra_wide.columns.intersection(densities.index)
    if len(common_genera) == 0:
        raise ValueError('No genera in common between genus_ra_wide and densities')

    ra = genus_ra_wide[common_genera].fillna(0)
    dens = densities.loc[common_genera]

    # Process one category at a time to avoid holding 5 × (n_samples × n_genera) matrices
    # simultaneously in memory (~900 MB each for 42k samples × 2.8k genera).
    feature_parts = []
    pca_top_parts = []

    for cat in dens.columns:
        contrib = ra.multiply(dens[cat], axis=1)          # n_samples × n_common_genera
        mean_contrib = contrib.mean(axis=0)
        top_genera = mean_contrib.nlargest(top_n_per_cat).index
        top_df = contrib[top_genera].rename(columns=lambda g: f'gw_{cat}_{g}')
        feature_parts.append(top_df)
        if n_pca > 0:
            pca_top_parts.append(top_df)                  # only keep top-N columns for PCA
        del contrib                                        # free the large matrix immediately

    gw_feats = pd.concat(feature_parts, axis=1)

    if n_pca > 0:
        # PCA on the already-extracted top-N columns (top_n_per_cat × n_cats features)
        # instead of the full genus × category matrix, to keep memory tractable.
        pca_input = pd.concat(pca_top_parts, axis=1).fillna(0)
        n_comp = min(n_pca, pca_input.shape[1], pca_input.shape[0] - 1)
        if n_comp > 0:
            pca = PCA(n_components=n_comp)
            pca_vals = pca.fit_transform(pca_input)
            pca_df = pd.DataFrame(
                pca_vals,
                index=genus_ra_wide.index,
                columns=[f'gw_pca_{i}' for i in range(n_comp)],
            )
            gw_feats = pd.concat([gw_feats, pca_df], axis=1)

    return gw_feats


def get_genus_ra_from_spark(spark, otu_bridge: pd.DataFrame, sample_ids=None) -> pd.DataFrame:
    """Load genus-level RA from MicrobeAtlas OTU data via Spark.

    Uses the pangenome OTU bridge (otu_pangenome_link_v2.csv) for OTU→genus mapping,
    the same bridge used for CWM computation. This covers ~2,781 genera with pangenome
    representatives. The `otu_metadata.Genus` column has sparse coverage (~7% of OTUs)
    so the bridge is preferred.

    Args:
        spark: active SparkSession.
        otu_bridge: DataFrame with columns [otu_id, genus_lower] from otu_pangenome_link_v2.csv.
        sample_ids: optional list of sample_ids to filter (all if None).

    Returns:
        genus_ra_wide: pd.DataFrame indexed by sample_id, columns are genus names,
            values are relative abundances (row sums = 1 where total > 0).
    """
    from cwm_utils import load_genus_ra_from_spark
    return load_genus_ra_from_spark(spark, sample_ids=sample_ids, otu_bridge=otu_bridge)


def cwm_coverage_fraction(genus_ra_wide: pd.DataFrame, densities: pd.DataFrame) -> pd.Series:
    """Fraction of relative abundance covered by genera in the density table."""
    common = genus_ra_wide.columns.intersection(densities.index)
    covered_ra = genus_ra_wide[common].sum(axis=1)
    return covered_ra.rename('coverage_fraction')

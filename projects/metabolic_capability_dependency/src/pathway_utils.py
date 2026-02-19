"""
Utility functions for metabolic capability vs dependency analysis.

This module provides helper functions for:
- Loading and processing GapMind pathway data
- Mapping pathways to fitness genes
- Computing pathway-level fitness aggregates
- Classification logic for active dependencies vs latent capabilities
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple


def load_gapmind_data(data_dir: Path) -> pd.DataFrame:
    """
    Load GapMind genome-pathway data.

    Parameters
    ----------
    data_dir : Path
        Path to data directory

    Returns
    -------
    pd.DataFrame
        GapMind pathway data with columns: genome_id, species, pathway, best_score, is_complete
    """
    gapmind_path = data_dir / 'gapmind_genome_pathways.csv'
    if not gapmind_path.exists():
        raise FileNotFoundError(
            f"GapMind data not found at {gapmind_path}. "
            "Run NB01 on JupyterHub first."
        )
    return pd.read_csv(gapmind_path)


def load_fitness_matrix(matrix_path: Path) -> pd.DataFrame:
    """
    Load a fitness matrix file.

    Parameters
    ----------
    matrix_path : Path
        Path to fitness matrix TSV file

    Returns
    -------
    pd.DataFrame
        Fitness matrix with genes as rows, conditions as columns
    """
    return pd.read_csv(matrix_path, sep='\t', index_col=0)


def compute_pathway_fitness_metrics(
    pathway_genes: List[str],
    fitness_matrix: pd.DataFrame,
    essential_genes: set = None
) -> Dict[str, float]:
    """
    Compute fitness aggregates for a pathway.

    Parameters
    ----------
    pathway_genes : List[str]
        List of gene IDs (loci) in the pathway
    fitness_matrix : pd.DataFrame
        Fitness matrix (genes × conditions)
    essential_genes : set, optional
        Set of essential gene IDs (no fitness data)

    Returns
    -------
    Dict[str, float]
        Dictionary with metrics:
        - n_genes: Total genes in pathway
        - n_with_fitness: Genes with fitness data
        - n_essential: Putatively essential genes
        - pct_essential: Percentage essential
        - mean_abs_t: Mean |t-score| across all genes and conditions
        - max_abs_t: Maximum |t-score| observed
        - median_abs_t: Median |t-score|
    """
    if essential_genes is None:
        essential_genes = set()

    # Genes with fitness data
    genes_with_fitness = [g for g in pathway_genes if g in fitness_matrix.index]
    essentials_in_pathway = [g for g in pathway_genes if g in essential_genes]

    metrics = {
        'n_genes': len(pathway_genes),
        'n_with_fitness': len(genes_with_fitness),
        'n_essential': len(essentials_in_pathway),
        'pct_essential': 100 * len(essentials_in_pathway) / len(pathway_genes) if pathway_genes else 0
    }

    if genes_with_fitness:
        # Extract fitness values for pathway genes
        pathway_fitness = fitness_matrix.loc[genes_with_fitness]
        abs_t = pathway_fitness.abs()

        metrics['mean_abs_t'] = abs_t.values.flatten().mean()
        metrics['max_abs_t'] = abs_t.values.max()
        metrics['median_abs_t'] = np.median(abs_t.values.flatten())
    else:
        metrics['mean_abs_t'] = np.nan
        metrics['max_abs_t'] = np.nan
        metrics['median_abs_t'] = np.nan

    return metrics


def classify_pathway_dependency(
    mean_abs_t: float,
    pct_essential: float,
    active_t_threshold: float = 2.0,
    active_essential_threshold: float = 20.0,
    latent_t_threshold: float = 1.0,
    latent_essential_threshold: float = 5.0
) -> str:
    """
    Classify a pathway as active dependency, latent capability, or intermediate.

    Parameters
    ----------
    mean_abs_t : float
        Mean absolute t-score for pathway genes
    pct_essential : float
        Percentage of pathway genes that are essential
    active_t_threshold : float
        Threshold for active classification (default: 2.0)
    active_essential_threshold : float
        Essential % threshold for active classification (default: 20%)
    latent_t_threshold : float
        Threshold for latent classification (default: 1.0)
    latent_essential_threshold : float
        Essential % threshold for latent classification (default: 5%)

    Returns
    -------
    str
        Classification: 'active_dependency', 'latent_capability', or 'intermediate'
    """
    # Handle missing data
    if pd.isna(mean_abs_t) and pd.isna(pct_essential):
        return 'unknown'

    # Active dependency: high fitness importance OR high essentiality
    if (not pd.isna(mean_abs_t) and mean_abs_t > active_t_threshold) or \
       (not pd.isna(pct_essential) and pct_essential > active_essential_threshold):
        return 'active_dependency'

    # Latent capability: low fitness importance AND low essentiality
    if (pd.isna(mean_abs_t) or mean_abs_t < latent_t_threshold) and \
       (pd.isna(pct_essential) or pct_essential < latent_essential_threshold):
        return 'latent_capability'

    # Intermediate
    return 'intermediate'


def categorize_pathway(pathway_name: str) -> str:
    """
    Categorize a GapMind pathway into functional groups.

    Parameters
    ----------
    pathway_name : str
        GapMind pathway name

    Returns
    -------
    str
        Category: 'amino_acid', 'carbon', 'cofactor', 'nucleotide', 'other'
    """
    pathway_lower = pathway_name.lower()

    # Amino acid biosynthesis/catabolism
    amino_acids = [
        'arg', 'his', 'ile', 'leu', 'lys', 'met', 'phe', 'thr', 'trp', 'val',
        'ala', 'asn', 'asp', 'cys', 'gln', 'glu', 'gly', 'pro', 'ser', 'tyr'
    ]
    if any(aa in pathway_lower for aa in amino_acids):
        return 'amino_acid'

    # Carbon source utilization
    carbon_sources = [
        'glucose', 'fructose', 'galactose', 'lactose', 'maltose', 'sucrose',
        'arabinose', 'xylose', 'ribose', 'mannose', 'acetate', 'lactate',
        'pyruvate', 'citrate', 'succinate', 'fumarate', 'malate'
    ]
    if any(carbon in pathway_lower for carbon in carbon_sources):
        return 'carbon'

    # Cofactor biosynthesis
    cofactors = [
        'thiamin', 'riboflavin', 'niacin', 'biotin', 'folate', 'cobalamin',
        'nad', 'fad', 'coenzyme', 'vitamin', 'pyridoxal', 'pantothenate'
    ]
    if any(cof in pathway_lower for cof in cofactors):
        return 'cofactor'

    # Nucleotide metabolism
    if any(nuc in pathway_lower for nuc in ['purine', 'pyrimidine', 'nucleotide']):
        return 'nucleotide'

    return 'other'


def build_pathway_matrix(
    gapmind_data: pd.DataFrame,
    species: str,
    value_column: str = 'is_complete'
) -> pd.DataFrame:
    """
    Build a genome × pathway matrix for a species.

    Parameters
    ----------
    gapmind_data : pd.DataFrame
        GapMind genome-pathway data
    species : str
        Species name (gtdb_species_clade_id)
    value_column : str
        Column to use for matrix values (default: 'is_complete')

    Returns
    -------
    pd.DataFrame
        Matrix with genomes as rows, pathways as columns
    """
    species_data = gapmind_data[gapmind_data['species'] == species]

    matrix = species_data.pivot_table(
        index='genome_id',
        columns='pathway',
        values=value_column,
        fill_value=0
    )

    return matrix


def compute_pathway_heterogeneity(pathway_matrix: pd.DataFrame) -> pd.Series:
    """
    Compute heterogeneity metrics for each pathway.

    A pathway with 10-90% completion is highly heterogeneous (good for ecotype analysis).
    A pathway with 0% or 100% completion is homogeneous (not informative).

    Parameters
    ----------
    pathway_matrix : pd.DataFrame
        Genome × pathway matrix (binary: 0/1)

    Returns
    -------
    pd.Series
        Heterogeneity score (0-1) for each pathway, where:
        - 0 = all genomes same (0% or 100%)
        - 1 = maximum heterogeneity (50% complete)
    """
    completion_rate = pathway_matrix.mean()

    # Heterogeneity = 4 * p * (1 - p), maximized at p = 0.5
    heterogeneity = 4 * completion_rate * (1 - completion_rate)

    return heterogeneity

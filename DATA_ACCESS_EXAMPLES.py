"""
BERIL Research Observatory - Data Access Examples
April 24, 2026 (initial); refreshed April 25, 2026 for Phase 2b

This script demonstrates common data access patterns for working with the
plant_microbiome_ecotypes dataset (post-Phase-2b: 73 CSV files, 873 MB) and
cross-project reusable data.

Phase 2b refresh notes:
- Examples updated to use `species_cohort_refined.csv` (Phase 2 preferred)
  alongside the legacy `cohort_assignments.csv` (Phase 1, kept for comparison).
- Examples updated to use `complementarity_v2.csv` (prevalence-weighted,
  formula-corrected) instead of `complementarity_network.csv` (Phase 1, has
  Cohen's d formula error — kept for legacy comparison).
- New example #10: read canonical Phase 2b hypothesis verdicts.
- New example #11: Pfam-query cross-check (bakta vs InterProScan) — closes
  the cross-project gotcha documented in docs/pitfalls.md.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ==============================================================================
# SETUP
# ==============================================================================

BASE_DIR = Path("/home/aparkin/BERIL-research-observatory")
PME_DATA = BASE_DIR / "projects" / "plant_microbiome_ecotypes" / "data"


# ==============================================================================
# 1. LOAD CORE REFERENCE DATASETS
# ==============================================================================

def load_core_datasets():
    """Load the core datasets, preferring Phase 2 refined where available."""

    # Phase 2 refined cohort assignments (preferred for new analyses)
    refined = pd.read_csv(PME_DATA / "species_cohort_refined.csv")
    print(f"species_cohort_refined.csv: {refined.shape}")
    print(refined[['gtdb_species_clade_id', 'cohort_refined',
                   'n_pgp_refined', 'n_pathogen_refined']].head())
    print("\nPhase 2 cohort distribution:")
    print(refined['cohort_refined'].value_counts())

    # Phase 1 composite-scoring cohorts (legacy; useful for direct comparison)
    cohorts_p1 = pd.read_csv(PME_DATA / "cohort_assignments.csv")
    print(f"\ncohort_assignments.csv (Phase 1, legacy): {cohorts_p1.shape}")
    print("Phase 1 cohort distribution:")
    print(cohorts_p1['cohort'].value_counts())

    # Genome-to-environment mapping (293,059 genomes)
    genome_env = pd.read_csv(PME_DATA / "genome_environment.csv")
    print(f"\ngenome_environment.csv: {genome_env.shape}")
    print("\nPlant-associated breakdown:")
    print(genome_env['is_plant_associated'].value_counts())

    # Metabolic pathway completeness (2.2M rows; filter before loading in production)
    print("\nFor gapmind_plant_species.csv (137 MB), filter first:")
    print("  species_of_interest = refined.query('cohort_refined == \"beneficial\"')['gtdb_species_clade_id'].unique()")
    print("  gapmind = pd.read_csv('gapmind_plant_species.csv')")
    print("  gapmind_filt = gapmind[gapmind['gtdb_species_clade_id'].isin(species_of_interest)]")

    return refined, cohorts_p1, genome_env


def load_filtered_gapmind(species_ids):
    """Efficiently load GapMind data for specific species.

    Parameters
    ----------
    species_ids : array-like
        List of gtdb_species_clade_id values to filter on

    Returns
    -------
    DataFrame with metabolic pathway completeness for specified species
    """
    gapmind = pd.read_csv(PME_DATA / "gapmind_plant_species.csv")
    return gapmind[gapmind['gtdb_species_clade_id'].isin(species_ids)]


# ==============================================================================
# 2. FILTER BY PLANT ASSOCIATION
# ==============================================================================

def get_plant_associated_species():
    """Get all plant-associated species (genome-level flag)."""
    genome_env = pd.read_csv(PME_DATA / "genome_environment.csv")
    plant_genomes = genome_env[genome_env['is_plant_associated'] == True]
    plant_species = plant_genomes['gtdb_species_clade_id'].unique()
    return plant_species, plant_genomes


def get_compartment_species(compartment):
    """Get species dominant in a specific plant compartment.

    Parameters
    ----------
    compartment : str
        One of: rhizosphere, phyllosphere, endosphere, root, host_clinical,
        soil, plant_other, other

    Note: species_compartment.csv uses `dominant_compartment` (not `compartment`)
    """
    species_comp = pd.read_csv(PME_DATA / "species_compartment.csv")
    return species_comp[species_comp['dominant_compartment'] == compartment]


# ==============================================================================
# 3. JOIN DATASETS FOR INTEGRATED ANALYSIS
# ==============================================================================

def create_species_matrix(use_refined=True):
    """Create integrated species × feature matrix for ML.

    Parameters
    ----------
    use_refined : bool, default True
        If True, use Phase 2 refined cohorts and 17-marker matrix.
        If False, use Phase 1 cohorts and 25-marker matrix (legacy).
    """

    if use_refined:
        cohorts = pd.read_csv(PME_DATA / "species_cohort_refined.csv")
        marker_matrix = pd.read_csv(PME_DATA / "species_marker_matrix_v2.csv")
        cohort_col = 'cohort_refined'
    else:
        cohorts = pd.read_csv(PME_DATA / "cohort_assignments.csv")
        marker_matrix = pd.read_csv(PME_DATA / "species_marker_matrix.csv")
        cohort_col = 'cohort'

    integrated = cohorts.merge(marker_matrix, on='gtdb_species_clade_id', how='inner')

    # Optionally join with compartment distribution
    comp = pd.read_csv(PME_DATA / "species_compartment.csv")
    integrated = integrated.merge(comp, on='gtdb_species_clade_id', how='left')

    print(f"Integrated dataset ({'Phase 2 refined' if use_refined else 'Phase 1 legacy'}): {integrated.shape}")
    print(f"Cohort column: {cohort_col}")
    print(f"Class balance:\n{integrated[cohort_col].value_counts()}")

    return integrated, cohort_col


def join_with_environmental_data():
    """Link species phenotypes with genome-level environmental context."""

    refined = pd.read_csv(PME_DATA / "species_cohort_refined.csv")
    genome_env = pd.read_csv(PME_DATA / "genome_environment.csv")

    species_env = genome_env.merge(
        refined[['gtdb_species_clade_id', 'cohort_refined',
                 'n_pgp_refined', 'n_pathogen_refined']],
        on='gtdb_species_clade_id',
        how='left'
    )

    print(f"Species-environment matrix: {species_env.shape}")
    print("Environmental distribution by Phase 2 cohort:")
    print(species_env.groupby(['cohort_refined', 'compartment']).size())

    return species_env


# ==============================================================================
# 4. VALIDATE WITH REAL-WORLD ABUNDANCE DATA (NMDC)
# ==============================================================================

def validate_ecotypes_with_abundance():
    """Test if predicted beneficial genera are actually abundant in soil."""

    refined = pd.read_csv(PME_DATA / "species_cohort_refined.csv")
    nmdc_abundance = pd.read_csv(PME_DATA / "nmdc_genus_abundance.csv")

    # Phase 2 refined: distinguish beneficial / pathogenic / dual-nature / neutral
    beneficial = refined.query("cohort_refined == 'beneficial'")['genus'].dropna().unique()
    pathogenic = refined.query("cohort_refined == 'pathogenic'")['genus'].dropna().unique()

    nmdc_abundance['genus'] = nmdc_abundance['taxon'].astype(str).str.split('__').str[1]

    beneficial_abund = nmdc_abundance[nmdc_abundance['genus'].isin(beneficial)]['abundance']
    pathogenic_abund = nmdc_abundance[nmdc_abundance['genus'].isin(pathogenic)]['abundance']

    print("\nAbundance validation (Phase 2 refined cohorts):")
    print(f"Beneficial genera mean abundance: {beneficial_abund.mean():.6f}")
    print(f"Pathogenic genera mean abundance: {pathogenic_abund.mean():.6f}")
    if pathogenic_abund.mean() > 0:
        print(f"Beneficial/Pathogenic ratio: {beneficial_abund.mean() / pathogenic_abund.mean():.2f}x")

    return beneficial_abund, pathogenic_abund


# ==============================================================================
# 5. IDENTIFY FUNCTIONALLY COMPLEMENTARY CONSORTIA
# ==============================================================================

def find_consortia():
    """Find genus pairs with strong metabolic complementarity.

    Phase 2b note: use complementarity_v2.csv (prevalence-weighted, formula-
    corrected). The original complementarity_network.csv reported Cohen's
    d = -7.54 due to a formula error (divided by null SD instead of raw pair
    SD); the true magnitude is |d| ≈ 0.4. Both files are retained, but the v2
    file is the canonical source for new analyses.
    """

    comp = pd.read_csv(PME_DATA / "complementarity_v2.csv")

    # Filter for high prevalence-weighted complementarity
    co_occurring = comp[comp['is_cooccurring']].sort_values(
        'complementarity_prev', ascending=False)

    print("\nTop synergistic co-occurring pairs (prevalence-weighted):")
    cols = [c for c in ['genus_A', 'genus_B', 'complementarity_prev',
                         'complementarity_max', 'is_cooccurring'] if c in co_occurring.columns]
    print(co_occurring[cols].head(10))

    return co_occurring


# ==============================================================================
# 6. ENRICHMENT ANALYSIS (GWAS-STYLE)
# ==============================================================================

def get_plant_enriched_genes(q_threshold=0.05):
    """Get genes/COGs significantly enriched in plant-associated species."""

    enrichment = pd.read_csv(PME_DATA / "enrichment_results.csv")
    plant_enriched = enrichment[
        (enrichment['q_value'] < q_threshold) &
        (enrichment['odds_ratio'] > 1)
    ].sort_values('odds_ratio', ascending=False)

    print(f"\nPlant-enriched OGs (q < {q_threshold}): {len(plant_enriched)}")
    print(plant_enriched[['og_id', 'odds_ratio', 'prev_plant', 'prev_nonplant']].head(10))

    # Phase 2b refinement: 48/50 of the top plant-enriched OGs survive real
    # per-species genome-size + phylum control at q<0.05 BH-FDR
    gs_control = pd.read_csv(PME_DATA / "genome_size_control.csv")
    print(f"\nOGs surviving Phase 2b real per-species genome-size control: "
          f"{int(gs_control['survives_strict'].sum())}/{len(gs_control)}")

    return plant_enriched


# ==============================================================================
# 7. CROSS-PROJECT DATA: CONSERVATION vs. FITNESS
# ==============================================================================

def load_fitness_data():
    """Load pangenome ↔ fitness browser linkage (conservation_vs_fitness project)."""

    fb_link = BASE_DIR / "projects" / "conservation_vs_fitness" / "data" / "fb_pangenome_link.tsv"
    fitness = pd.read_csv(fb_link, sep='\t')

    print(f"Fitness browser linkage: {fitness.shape}")
    print(fitness.head())

    return fitness


def validate_with_fitness():
    """Cross-validate plant-microbiome predictions with measured fitness."""

    refined = pd.read_csv(PME_DATA / "species_cohort_refined.csv")
    fitness = load_fitness_data()

    # Note: requires manual species ID mapping; shown conceptually
    validated = refined.merge(fitness,
                               left_on='gtdb_species_clade_id',
                               right_on='pangenome_species', how='inner')

    print(f"Organisms with both Phase 2 cohort labels and fitness data: {len(validated)}")

    return validated


# ==============================================================================
# 8. MACHINE LEARNING SETUP
# ==============================================================================

def prepare_ml_features(use_refined=True):
    """Prepare features for ML.

    Phase 2b note: per the species-level validation in NB13, the categorical
    cohort label is uninformative at species level — all known beneficial and
    pathogenic species collapse to dual-nature. The continuous pathogen ratio
    is the discriminative target. This function returns both options.
    """

    df, cohort_col = create_species_matrix(use_refined=use_refined)

    # Categorical target
    feature_cols = [c for c in df.columns if c not in
                    ['gtdb_species_clade_id', 'genus', 'phylum', cohort_col,
                     'dominant_compartment', 'is_plant_associated', 'cohort',
                     'n_classified_genomes', 'majority_frac', 'dominant_count',
                     'dominant_host', 'all_hosts', 'n_hosts', 'n_host_genomes']]

    X = df[feature_cols].fillna(0)
    y_cat = df[cohort_col]

    # Continuous target (Phase 2b preferred for species-level discrimination)
    if use_refined and 'n_pgp_refined' in df.columns:
        total_markers = (df['n_pgp_refined'] + df['n_pathogen_refined']).replace(0, np.nan)
        y_cont = df['n_pathogen_refined'] / total_markers
        print(f"Continuous pathogen_ratio target available (Phase 2b): "
              f"{y_cont.notna().sum()} species with non-zero markers")
    else:
        y_cont = None

    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Categorical target classes: {sorted(y_cat.dropna().unique())}")
    print(f"Class balance:\n{y_cat.value_counts()}")

    return X, y_cat, y_cont


# ==============================================================================
# 9. PANGENOME ANALYSIS: CORE vs. ACCESSORY
# ==============================================================================

def analyze_hgt_burden():
    """Analyze HGT burden (accessory vs. core genes) by cohort."""

    pangenome = pd.read_csv(PME_DATA / "pangenome_stats.csv")
    refined = pd.read_csv(PME_DATA / "species_cohort_refined.csv")

    # pangenome_stats has no_singleton_gene_clusters; compute openness if absent
    if 'openness' not in pangenome.columns and 'no_gene_clusters' in pangenome.columns:
        pangenome['openness'] = (pangenome['no_singleton_gene_clusters']
                                  / pangenome['no_gene_clusters'])

    merged = pangenome.merge(refined, on='gtdb_species_clade_id', how='inner')

    print("\nPangenome openness by Phase 2 cohort:")
    print(merged.groupby('cohort_refined')['openness'].describe())

    print("\nHigh-HGT beneficial species (openness > 0.5, cohort_refined=='beneficial'):")
    high_hgt = merged.query("openness > 0.5 and cohort_refined == 'beneficial'")
    print(high_hgt[['genus', 'gtdb_species_clade_id', 'openness',
                     'n_pgp_refined']].head(10))

    return merged


# ==============================================================================
# 10. (NEW) READ CANONICAL PHASE 2B HYPOTHESIS VERDICTS
# ==============================================================================

def load_hypothesis_verdicts():
    """Read the canonical post-Phase-2b verdicts for H0–H7.

    Use this as the authoritative source rather than parsing chronological
    notebook outputs. Each row gives the Phase 1 verdict, the Phase 2b
    evidence layered on top, and the final verdict.
    """
    verdicts = pd.read_csv(PME_DATA / "hypothesis_verdicts_final.csv")
    print(f"Hypothesis verdicts: {verdicts.shape}\n")
    for _, r in verdicts.iterrows():
        print(f"{r['id']}: {r['final_verdict']}")
    return verdicts


# ==============================================================================
# 11. (NEW) PFAM QUERY CROSS-CHECK (Phase 2b cross-project pitfall)
# ==============================================================================

def check_pfam_coverage(pfam_ids):
    """Cross-check whether the requested Pfam IDs are present in
    `bakta_pfam_domains` versus `interproscan_domains`.

    Phase 2b finding: 12 of 22 marker Pfams in this project (especially
    T3SS/T4SS/T6SS components) are silently absent from `bakta_pfam_domains`
    despite being abundant in `interproscan_domains`. ALWAYS cross-check
    before drawing conclusions about absent functions.

    Parameters
    ----------
    pfam_ids : list of str
        e.g., ['PF00771', 'PF01313', 'PF00142']

    Returns
    -------
    DataFrame with per-Pfam IPS hits, bakta hits, and a `silent_gap` flag.
    """
    audit = pd.read_csv(PME_DATA / "pfam_bakta_ips_audit.csv")
    requested = audit[audit['pfam_id'].isin(pfam_ids)]
    if len(requested) < len(pfam_ids):
        missing = set(pfam_ids) - set(requested['pfam_id'])
        print(f"Note: {len(missing)} Pfam IDs not in pre-computed audit "
              f"(re-run notebooks/_audit_pfam_coverage.py to extend): {sorted(missing)[:5]}")

    print("\nPfam coverage:")
    print(requested[['pfam_id', 'ips_hits', 'ips_species',
                      'bakta_hits', 'bakta_species', 'silent_gap']])

    silent = requested[requested['silent_gap']]
    if len(silent) > 0:
        print(f"\n⚠ WARNING: {len(silent)} Pfam(s) silently missing from bakta_pfam_domains:")
        for _, r in silent.iterrows():
            print(f"  {r['pfam_id']}: {r['ips_hits']} IPS hits, 0 bakta hits "
                  f"— use interproscan_domains.signature_acc for queries")

    return requested


# ==============================================================================
# MAIN: RUN EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("BERIL Research Observatory - Data Access Examples (Phase 2b refresh)")
    print("=" * 80)

    # 1. Load core data
    print("\n1. LOADING CORE DATASETS")
    print("-" * 80)
    refined, cohorts_p1, genome_env = load_core_datasets()

    # 2. Filter by plant association
    print("\n2. PLANT-ASSOCIATED SPECIES")
    print("-" * 80)
    plant_species, plant_genomes = get_plant_associated_species()
    print(f"Plant-associated species: {len(plant_species)}")
    print(f"Plant-associated genomes: {len(plant_genomes)}")

    # 3. Create integrated matrix
    print("\n3. INTEGRATED SPECIES MATRIX (Phase 2 refined)")
    print("-" * 80)
    integrated, _ = create_species_matrix(use_refined=True)

    # 4. Validate with abundance
    print("\n4. ABUNDANCE VALIDATION")
    print("-" * 80)
    beneficial_abund, pathogenic_abund = validate_ecotypes_with_abundance()

    # 5. Find consortia
    print("\n5. CONSORTIA IDENTIFICATION (prevalence-weighted complementarity)")
    print("-" * 80)
    consortia = find_consortia()

    # 6. Enrichment analysis
    print("\n6. PLANT-ENRICHED GENES")
    print("-" * 80)
    enriched = get_plant_enriched_genes()

    # 7. HGT analysis
    print("\n7. HORIZONTAL GENE TRANSFER BURDEN")
    print("-" * 80)
    hgt = analyze_hgt_burden()

    # 10. Hypothesis verdicts (NEW)
    print("\n10. CANONICAL PHASE 2B HYPOTHESIS VERDICTS")
    print("-" * 80)
    verdicts = load_hypothesis_verdicts()

    # 11. Pfam coverage cross-check (NEW)
    print("\n11. PFAM COVERAGE CROSS-CHECK")
    print("-" * 80)
    # Example: are the T3SS Pfams accessible via bakta_pfam_domains?
    check_pfam_coverage(['PF00771', 'PF01313', 'PF00142', 'PF00150'])

    print("\n" + "=" * 80)
    print("Examples completed. See DATA_INVENTORY.md for full documentation.")
    print("=" * 80)

# Research Plan: Ecotype Reanalysis — Environmental-Only Samples

## Research Question

Does the environment effect on gene content become stronger when analysis is restricted to genuinely environmental samples (excluding human-associated genomes)?

## Hypothesis

- **H0**: Environment partial correlations are the same for environmental and human-associated species
- **H1**: Environmental species show stronger environment–gene content correlations because their AlphaEarth embeddings carry more meaningful geographic signal

## Literature Context

The original `ecotype_analysis` project found that phylogeny dominates over environment in predicting gene content similarity (median partial correlation 0.003 for environment vs 0.014 for phylogeny). It also tested whether "environmental" bacteria show stronger effects than host-associated ones — and found no significant difference (p=0.66).

However, that test used a coarse species-level ecological categorization (manual assignment to Commensal-Gut, Pathogen-Human, etc.) with only 97 species as "Unknown" (56% of the 172 tested). The `env_embedding_explorer` project subsequently showed that classifying genomes by isolation_source (keyword-based harmonization) reveals a strong bias: 38% of genomes are human-associated, and their AlphaEarth embeddings have 70% weaker geographic signal (2.0x ratio vs 3.4x for environmental samples).

This reanalysis uses the more comprehensive genome-level classification to re-test the hypothesis that environment effects are masked by the clinical sample bias.

## Query Strategy

**No new BERDL queries.** All data comes from two parent projects:

| Source | File | Purpose |
|--------|------|---------|
| `ecotype_analysis` | Notebook 02 outputs | Partial correlation results for 172 species |
| `env_embedding_explorer` | `data/alphaearth_with_env.csv` | Harmonized env_category per genome |

## Analysis Plan

### Notebook 1: Environmental-Only Reanalysis

1. Parse the 172-species partial correlation results from `ecotype_analysis/notebooks/02_ecotype_correlation_analysis.ipynb` output cells
2. Load env_category mapping from `env_embedding_explorer/data/alphaearth_with_env.csv`
3. For each species, classify as "environmental" vs "human-associated" based on majority env_category of its genomes
4. Compare environment partial correlations between groups (Mann-Whitney U)
5. Visualize: box plots, overlaid distributions, scatter of env vs phylo effects by group

## Expected Outcomes

- **If H1 supported**: Environmental species have significantly higher environment partial correlations, and the original weak signal was diluted by clinical samples. Implies the AlphaEarth embeddings are more useful for environmental microbiology than the original ecotype analysis suggested.
- **If H0 not rejected**: The clinical bias doesn't explain the weak environment signal. The original conclusion (phylogeny dominates) holds even for environmental samples. Alternative explanations: embeddings don't capture ecologically relevant variation, or environment acts on specific gene subsets rather than the whole genome.

## Revision History

- **v1** (2026-02-16): Initial plan

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory

# Metal Cross-Resistance Research Plan Review

**Overall**: This is a well-designed and feasible plan that fills an important gap in cross-resistance analysis. The approach is scientifically sound and builds appropriately on existing Metal Fitness Atlas work.

## Critical (likely to cause failures or wasted effort):

1. **Fitness matrix locusId type mismatch**: The fitness matrices from `fitness_modules/data/matrices/` use integer-typed locusId indices while the Metal Atlas `metal_important_genes.csv` stores locusIds as strings. This silent type mismatch caused complete organism dropout in the metal_specificity project. Always convert both sides to strings before matching: `fit_mat.index = fit_mat.index.astype(str)`.

2. **String-typed numeric columns**: All Fitness Browser columns are stored as strings. The query strategy correctly mentions CAST to FLOAT, but this pitfall should be emphasized more prominently since fitness correlations are the core analysis.

## Recommended (would improve the plan):

1. **Leverage existing Metal Atlas data products**: The plan could build more directly on the Metal Fitness Atlas data products (e.g., `projects/metal_fitness_atlas/data/metal_important_genes.csv`, `metal_experiments.csv`) rather than re-extracting from Fitness Browser. This would ensure consistency and save extraction time.

2. **Performance optimization**: For NB04 pangenome lookups, consider using BROADCAST hints for ortholog group temp views when joining billion-row tables, as demonstrated in the cofitness_coinheritance project.

3. **Cross-resistance validation**: Consider validating cross-resistance predictions against known biochemical relationships (e.g., Co-Ni-Zn efflux systems) mentioned in the literature context.

## Optional (nice-to-have):

1. **Handle organism coverage gaps**: Document expected organism dropout due to insufficient metal coverage (<3 metals) and fitness matrix availability issues.

2. **BacDive validation scope**: Note that species name matching between GTDB and BacDive achieves only ~43% coverage after prefix handling, which may limit validation power for H3.

## Relevant pitfalls from docs/pitfalls.md:

- **String-typed numeric columns**: Fitness Browser stores all values as strings — critical for correlation calculations
- **Fitness Matrix locusId Type Mismatch**: Integer vs string index mismatches cause silent failures
- **genefitness Table is Large**: 27M rows — always filter by orgId at minimum  
- **REST API Reliability**: Complex multi-organism queries should use direct Spark SQL
- **ICA Module z-Normalization**: If using pre-computed module data, use existing z-scores rather than re-normalizing

---

Plan reviewed by Claude (claude-sonnet-4-20250514).

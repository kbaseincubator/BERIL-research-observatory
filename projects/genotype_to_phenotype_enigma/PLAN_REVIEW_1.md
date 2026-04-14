# Research Plan Review: Genotype × Condition → Phenotype Prediction from ENIGMA Growth Curves

**Overall**: Exceptionally well-structured plan with clear hypotheses, detailed methodology, and proper experimental design. The multi-paradigm comparison approach (GapMind/FBA/GBDT) is novel and the biological meaningfulness metric via FB concordance is a valuable methodological contribution.

## Critical (likely to cause failures or wasted effort):

1. **Fitness Browser string-typed numeric columns**: Plan correctly notes to cast `fit`, `t` to FLOAT, but be aware this applies to ALL FB numeric columns. Use `CAST(fit AS FLOAT)` consistently in queries.

2. **ENIGMA condition alignment uncertainty**: The plan assumes ENIGMA `sdt_condition` names (format `set1IT001`) will match FB experiment names, but this is unverified. NB02 is correctly designed to validate this, but if alignment fails, the entire anchor set strategy needs a fallback.

3. **Only 5 direct anchor strains**: The statistical power for Phase 2-3 comparisons is quite limited. Consider extending the anchor set via species-level GTDB matches (mentioned briefly but not detailed in the query strategy).

## Recommended (would improve the plan):

1. **Execution environment clarity**: The plan mentions both on-cluster and local execution but doesn't clearly specify which notebooks require which environment. Recommend adding a table: NB01-02 (BERDL JupyterHub required), NB03-11 (can run locally from cached data).

2. **Growth curve QC expectations**: Plan mentions ~20-30% rejection rate but Phase 1 success depends heavily on curve fitting quality. Consider adding a contingency plan if rejection rates are higher.

3. **Feature engineering scope**: NB06a appears to be the most computationally expensive notebook and may need to be split. Consider prioritizing feature families by expected signal strength (GapMind pathways, COG categories) before investing in regulatory proxies.

## Optional (nice-to-have):

1. **Cross-validation strategy details**: The leave-one-strain-out CV on 5 strains is quite limited. Consider nested CV or bootstrap resampling for more robust error estimates.

2. **FBA model availability**: The plan acknowledges FBA models may not exist for all anchor strains. Consider prioritizing strains by ModelSEED reconstruction feasibility early in Phase 1.

## Relevant pitfalls from docs/pitfalls.md:

- **Spark DECIMAL columns**: Wrap `AVG()` aggregates in `CAST(... AS DOUBLE)` for GapMind pathway scoring (NB04/NB06a)
- **Brick table iteration**: 303 ddt_brick reads are acceptable via Spark but slow via REST API — correctly planned for Spark
- **Species clade IDs contain `--`**: Fine in quoted Spark literals but problematic for REST API — plan correctly uses Spark
- **Gene clusters are species-specific**: Cannot be used for cross-species features — plan correctly uses UniRef/KO/Pfam for cross-species comparisons
- **Large species blow up ANI queries**: For >500 genome species, chunk the genome list or use subsampling
- **Unnecessary `.toPandas()` calls**: Plan correctly keeps data as Spark DataFrames until final results

## Existing project relationships:

The plan builds excellently on existing work:
- **fw300_metabolic_consistency**: Uses the same FW300-N2E3 strain as a primary test case — good continuity
- **conservation_vs_fitness**: Plan correctly references the existing `fb_pangenome_link.tsv` rather than rebuilding it
- **No significant overlap**: This project's genotype→phenotype prediction focus is distinct from existing community ecology (enigma_contamination_functional_potential) and conservation (conservation_vs_fitness) work

The research plan demonstrates strong scientific rigor, appropriate statistical design, and good integration with existing BERDL assets. The main risk is condition alignment (H1), but the plan properly validates this early.

---
Plan reviewed by Claude (claude-sonnet-4-20250514).

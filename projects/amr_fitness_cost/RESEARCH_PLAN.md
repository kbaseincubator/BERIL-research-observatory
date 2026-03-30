# Research Plan: Fitness Cost of Antimicrobial Resistance Genes

## Research Question

Do antimicrobial resistance (AMR) genes impose a measurable fitness cost in the absence of antibiotic selection pressure? Using genome-wide RB-TnSeq fitness data from 28 bacteria with identified AMR genes, we test whether transposon knockouts of AMR genes show systematically positive fitness (mutant outgrows wildtype) under standard growth conditions, indicating the intact AMR gene is a metabolic burden.

## Hypotheses

- **H0**: AMR gene knockouts show no fitness difference from non-AMR gene knockouts under non-antibiotic conditions (mean fitness ~ 0)
- **H1**: AMR gene knockouts show positive fitness under non-antibiotic conditions (cost of resistance)
- **H2**: Fitness cost varies by AMR mechanism — efflux pumps (continuous membrane cost) > enzymatic inactivation (expression cost only) > target modification (minimal cost). Within efflux, narrow-spectrum drug pumps may be costlier than general RND systems (e.g., AcrAB-TolC) that are constitutively expressed and likely compensated.
- **H3**: Accessory genome AMR genes are more costly than core genome AMR genes (core genes have been ameliorated by compensatory mutations)
- **Validation (H4)**: The same AMR genes show negative fitness under matching antibiotic conditions (demonstrating they are genuinely protective when needed)

## Literature Context

The "cost of resistance" hypothesis is central to antimicrobial resistance evolution: if AMR genes impose a fitness burden without antibiotics, resistance should decline when selection is removed. However:

- **Andersson & Hughes (2010, Nature Reviews Microbiology)** showed compensatory mutations can reduce or eliminate fitness costs, making resistance effectively cost-free in adapted strains
- **Melnyk et al. (2015, Evolutionary Applications)** meta-analyzed ~600 measurements and found fitness costs are common (~70% of mutations) but highly variable (CV > 100%)
- **Vogwill & MacLean (2015)** showed costs depend on genetic background, environment, and specific resistance mechanism
- **San Millan & MacLean (2017)** distinguished chromosomal vs plasmid-borne resistance costs

**Gap**: Most fitness cost studies use pairwise comparisons of resistant vs sensitive strains in single organisms. No systematic pan-bacterial analysis has been performed using genome-wide transposon fitness data across dozens of organisms simultaneously. This project leverages 27M fitness measurements across 28 organisms to test the cost hypothesis at unprecedented scale.

**Related BERDL projects**: `counter_ion_effects` found 39.8% overlap between metal-important genes and NaCl stress genes, reflecting shared cellular stress biology rather than counter-ion contamination. This is relevant to interpreting the metal resistance subset (230 genes) — their fitness signal under non-stress conditions may partially reflect general stress response. `metal_fitness_atlas` characterized metal-specific fitness across FB organisms; our metal resistance genes can be cross-referenced against those results as a secondary validation.

## Data Sources

### Primary Data Assets

| Source | Table/File | Scale | Purpose |
|--------|-----------|-------|---------|
| bakta_amr | `kbase_ke_pangenome.bakta_amr` | 83K rows (171 in FB-linked clusters) | Tier 1: strict AMR gene calls |
| bakta_annotations | `kbase_ke_pangenome.bakta_annotations` | 132M rows (1,083 new clusters by keyword) | Tier 2: AMR-related product annotations |
| FB-pangenome link | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | 177,863 links | Bridge FB genes to pangenome clusters |
| Fitness Browser | `kescience_fitnessbrowser.genefitness` | 27M rows | Per-gene, per-experiment fitness scores |
| FB experiments | `fitness_modules/data/annotations/*_experiments.csv` | 6,804 experiments | Experiment metadata for condition classification |
| FB gene table | `kescience_fitnessbrowser.gene` | ~228K genes | Gene metadata, type classification |

### Derived Data (from NB01)

| File | Rows | Description |
|------|------|-------------|
| `data/amr_genes_fb.csv` | 1,352 | AMR genes with class, mechanism, conservation, tier |
| `data/experiment_classification.csv` | 6,804 | Experiments classified by type (antibiotic, metal, stress, standard, etc.) |

### Key Numbers

- **28 organisms** with AMR genes + fitness matrices (26 also have antibiotic experiments)
- **1,352 AMR genes** (178 Tier 1 from bakta_amr, 1,174 Tier 2 from keyword matching; 114 Tier 2 genes are "unclassified" — need spot-checking for false positives)
- **443 antibiotic experiments** across 13 compounds (tetracycline, chloramphenicol, polymyxin B, etc.)
- **~3,600 standard/carbon-nitrogen experiments** for baseline fitness
- **Minimum organism inclusion**: require >= 5 AMR genes per organism for per-organism tests (excludes Pedo557=1, Methanococcus_JJ=2, Methanococcus_S2=2; these are reported in supplementary tables)

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|-------|---------|----------------|-----------------|
| `genefitness` | Fitness scores for AMR and non-AMR genes | ~27M | Filter by `orgId` per organism |
| `gene` | Gene metadata for non-AMR background | ~228K | Filter by `orgId`, `type='1'` (CDS) |
| Fitness matrices (cached) | Pre-pivoted fitness matrices from fitness_modules | 32 matrices | Load from `fitness_modules/data/matrices/` |

### Key Queries

1. **AMR gene fitness under non-antibiotic conditions**:
```python
# For each organism: load fitness matrix, select AMR genes, select non-antibiotic experiments
# Compute mean fitness per AMR gene across standard/carbon/nitrogen experiments
fit_mat = pd.read_csv(f"fitness_modules/data/matrices/{org}_fitness_matrix.csv", index_col=0)
fit_mat.index = fit_mat.index.astype(str)  # Pitfall: integer vs string locusId
non_abx_exps = exps_classified[
    (exps_classified['orgId'] == org) &
    (exps_classified['exp_category'].isin(['standard', 'carbon_nitrogen']))
]['expName'].tolist()
amr_fitness = fit_mat.loc[amr_loci, non_abx_exps]
```

2. **Background fitness for comparison** (non-AMR genes in same experiments):
```python
non_amr_loci = [l for l in fit_mat.index if l not in amr_loci]
bg_fitness = fit_mat.loc[non_amr_loci, non_abx_exps]
```

3. **Antibiotic validation** (fitness under matching antibiotic):
```python
abx_exps = exps_classified[
    (exps_classified['orgId'] == org) &
    (exps_classified['antibiotic_class'] == amr_class)
]['expName'].tolist()
amr_abx_fitness = fit_mat.loc[amr_loci, abx_exps]
```

### Performance Plan

- **Tier**: Local computation — all data pre-cached in fitness matrices and NB01 outputs
- **Estimated complexity**: Moderate (many organisms × conditions, but small matrices per organism)
- **Known pitfalls**:
  - locusId type mismatch (integer vs string) — always `.astype(str)` (from `metal_specificity` pitfall)
  - All FB numeric values are strings — use `pd.to_numeric()` on fitness matrices
  - Essential genes are invisible in genefitness — quantify and report (see Analysis Plan)
  - `fillna(False)` produces object dtype — always chain `.astype(bool)` when creating boolean flags from merges (from `essential_genome` pitfall)

## Analysis Plan

### Notebook 2: Fitness Cost Analysis (Core) + Exploratory QC

- **Goal**: Test H1 (AMR genes are costly under non-antibiotic conditions) and perform exploratory quality control
- **Test statistic**: Per-gene mean fitness averaged across all non-antibiotic experiments for that organism. This is the unit of analysis — not per-gene-per-experiment, which would inflate N and produce artificially low p-values.
- **Method**:
  1. Spot-check the 114 "unclassified" Tier 2 genes: sample 20, inspect product annotations for false positives (e.g., "desiccation resistance protein"). Report false positive rate.
  2. For each organism, compute the fraction of AMR genes absent from genefitness (putatively essential). Compare to the non-AMR background essential rate. Report direction of bias.
  3. For each of the 25 qualifying organisms (>= 5 AMR genes), compute per-gene mean fitness across standard/carbon-nitrogen experiments.
  4. **Sensitivity analysis**: Run the H1 test twice — Tier 1 only (178 genes) and Tier 1+2 (1,352 genes). If the results differ qualitatively, Tier 2 noise is a concern.
  5. Per-organism: Mann-Whitney U comparing AMR gene mean fitness vs non-AMR background. FDR correction (BH) across the 25 organism-level tests.
  6. Pan-bacterial meta-analysis: Random-effects model (DerSimonian-Laird) aggregating per-organism effect sizes with inverse-variance weighting. Report pooled effect size, 95% CI, I² heterogeneity, and forest plot.
  7. Exploratory plots: per-gene fitness distributions by organism (ridgeline plot), AMR gene count per organism bar chart, tier distribution, mechanism breakdown heatmap.
- **Expected output**: `data/amr_fitness_noabx.csv`, forest plot, volcano plot, exploratory QC figures
- **Note**: Organisms with < 5 AMR genes (Pedo557, Methanococcus_JJ, Methanococcus_S2) are included in the pooled gene-level analysis but excluded from per-organism tests and reported separately.

### --- CHECKPOINT: Evaluate before proceeding ---

After NB02 is complete, **pause and review results** before continuing to NB03–NB04. Key decision points:

1. **Is there a detectable signal?** If the pooled effect size CI includes zero and < 25% of organisms show nominally significant effects, the cost-of-resistance hypothesis may not be testable at this scale. In that case, pivot to characterizing the *distribution* of AMR fitness effects (are they noisier than background?) rather than testing for a directional shift.
2. **Does Tier 2 behave differently from Tier 1?** If the sensitivity analysis shows opposite directions, Tier 2 may be too noisy and NB03–04 should use Tier 1 only.
3. **Are there enough matched antibiotic experiments for NB03?** Enumerate AMR-class × antibiotic-compound matches and their sample sizes. If < 3 classes have >= 10 matched genes, NB03 may need to be restructured (e.g., test all AMR genes under any antibiotic, not just class-matched).
4. **Does the effect size landscape suggest meaningful stratification?** If the per-organism effects are all near zero with tight CIs, NB04 stratification is unlikely to reveal mechanism differences.

**Revise RESEARCH_PLAN.md** with a v2 revision tag documenting what was observed and how the remaining plan was adjusted.

### Notebook 3: Antibiotic Validation (Positive Control)

- **Goal**: Test H4 (AMR genes are protective under matching antibiotics)
- **Method**:
  1. Enumerate all AMR-class × antibiotic-compound matches with sample sizes. Pre-register minimum: >= 5 AMR genes and >= 3 experiments per match.
  2. For qualifying matches, extract AMR gene mean fitness under the matching antibiotic.
  3. Compare to non-AMR gene background under the same antibiotic (Mann-Whitney U).
  4. Compute the fitness flip: paired comparison of same genes under antibiotic vs non-antibiotic conditions (Wilcoxon signed-rank).
  5. Report the fraction of AMR genes that show the expected positive-to-negative fitness flip.
- **Expected output**: `data/amr_fitness_abx_validation.csv`, paired fitness comparison plot, heatmap of AMR gene × condition fitness
- **Note**: Only 26 organisms have both AMR genes and antibiotic experiments; matching between AMR class and antibiotic compound further restricts the testable set. Expected strongest matches: beta-lactam × carbenicillin (35 exps), chloramphenicol × chloramphenicol (51 exps, 16 genes), tetracycline × tetracycline (69 exps, 10 genes).

### Notebook 4: Stratification

- **Goal**: Test H2 (mechanism differences) and H3 (core vs accessory differences)
- **Minimum group size**: Pre-register N >= 20 genes per stratum for mechanism comparisons. Groups below this threshold are reported descriptively but not tested.
- **Method**:
  1. **By AMR mechanism**: Group genes by mechanism (efflux, enzymatic inactivation, target modification, metal resistance) and compare fitness distributions. Omnibus test: Kruskal-Wallis. Ordered alternative (efflux > enzymatic > target modification): Jonckheere-Terpstra trend test. Post-hoc: Dunn's test with BH correction.
  2. **By conservation status**: Compare core AMR genes (intrinsic proxy) vs accessory AMR genes (acquired proxy). Test H3: are accessory AMR genes more costly? (Mann-Whitney U)
  3. **By organism**: Identify organisms where AMR costs are highest/lowest. Correlate with total AMR gene count and phylogenetic group.
  4. **By AMR tier**: Compare Tier 1 (strict bakta_amr) vs Tier 2 (keyword annotation) to assess whether the more confident calls show different fitness patterns.
  5. **Antibiotic vs metal resistance**: Separate analysis for antibiotic resistance (1,122 genes) vs metal resistance (230 genes). Cross-reference metal resistance genes with `metal_fitness_atlas` results where organisms overlap.
  6. **Multiple testing scope**: FDR correction applied within each stratification dimension (mechanism: ~4 pairwise tests; conservation: 1 test; tier: 1 test; resistance type: 1 test). Per-organism tests corrected across the 25 organisms as in NB02.
- **Expected output**: `data/amr_fitness_stratified.csv`, box plots by mechanism/conservation/tier, interaction plots

## Expected Outcomes

- **If H1 supported** (AMR genes are costly): Provides pan-bacterial evidence for the cost of resistance at unprecedented scale. Mean fitness shift of +0.05 to +0.20 would be consistent with the literature (small but measurable costs). Would imply that resistance should decline without antibiotic pressure, supporting antibiotic stewardship policies.
- **If H0 not rejected** (no fitness cost): Suggests compensatory evolution has largely eliminated AMR costs in these lab-adapted strains, consistent with the Andersson & Hughes framework. Would imply resistance is more persistent than simple cost models predict.
- **If H2 supported** (mechanism-dependent costs): Identifies which resistance mechanisms are most costly (e.g., efflux pumps with continuous energy expenditure) vs cheapest (e.g., target modification with minimal expression cost). Directly actionable for drug design targeting costly resistance mechanisms.
- **If H3 supported** (accessory > core costs): Supports the model where recently acquired AMR genes impose larger costs that core genes have ameliorated over evolutionary time through compensatory mutations.

## Potential Confounders

1. **Polar effects**: Transposon insertions can disrupt downstream genes in operons, inflating apparent fitness effects. FB fitness scores are corrected for strand bias but not explicitly for polar effects. Mitigation: check whether AMR gene fitness correlates with operon position (5' genes more susceptible).
2. **Lab adaptation**: FB organisms are lab-adapted strains that may have already compensated for AMR costs. This biases toward H0 (no cost detected), making a positive result more convincing.
3. **Tier 2 classification noise**: Keyword-based AMR annotation (Tier 2) is less precise than bakta_amr (Tier 1). Tier 2 genes may include non-AMR genes (e.g., "desiccation resistance protein"). Mitigation: spot-check unclassified Tier 2 genes in NB02; run Tier 1-only sensitivity analysis.
4. **Multiple testing**: Scoped per-notebook — NB02: BH-FDR across 25 organism-level tests; NB03: BH-FDR across AMR-class × antibiotic pairs; NB04: BH-FDR within each stratification dimension separately.
5. **Unequal experiment counts**: Some organisms have many standard experiments (DvH: 363) while others have few (Ponti: 10). Mitigation: per-gene mean fitness (averaging over experiments) normalizes exposure; meta-analysis uses inverse-variance weighting.
6. **Essential AMR genes**: Truly essential AMR genes (no viable transposon mutants) are invisible in genefitness (~14.3% of CDS genes are putatively essential per `fitness_effects_conservation`). These may represent the most costly AMR genes, right-censoring the fitness distribution. Mitigation: NB02 reports AMR essential fraction vs background and discusses direction of bias.
7. **General RND efflux systems**: Constitutively expressed systems like AcrAB-TolC may already be compensated and show no cost, diluting the efflux category in H2. The `counter_ion_effects` project found 39.8% shared-stress overlap for metal genes. Mitigation: consider subclassifying efflux pumps if the data support it.

## Revision History

- **v3** (2026-03-19): NB02 checkpoint passed. H1 confirmed: pooled effect +0.086 [+0.074, +0.098], 25/25 organisms positive shift. Tier 1 and Tier 2 consistent (KS p=0.17). 4 antibiotic classes testable for NB03 (beta-lactam: 105 genes, aminoglycoside: 39, tetracycline: 7, chloramphenicol: 6). Proceeding with NB03-04 as planned.
- **v2** (2026-03-19): Incorporated review feedback — added Tier 1 sensitivity analysis, random-effects meta-analysis, minimum group sizes, essential gene quantification, NB02 checkpoint before proceeding, Jonckheere-Terpstra for ordered H2 test, multiple testing scoping, counter_ion_effects and metal_fitness_atlas cross-references
- **v1** (2026-03-19): Initial plan based on completed NB01 data assembly

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

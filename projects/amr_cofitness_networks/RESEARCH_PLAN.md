# Research Plan: AMR Co-Fitness Support Networks

## Research Question

What genes are co-regulated with antimicrobial resistance (AMR) genes across growth conditions, and do these "support networks" explain the uniform fitness cost of resistance? Using cofitness data and ICA fitness modules from 25 bacteria, we identify the functional context in which AMR genes operate — revealing whether resistance is an isolated function or embedded in broader cellular programs.

## Hypotheses

- **H0**: AMR genes have no distinctive cofitness partners; their cofitness neighborhoods are indistinguishable from random genes.
- **H1**: AMR genes have elevated cofitness with specific functional categories (stress response, membrane maintenance, energy metabolism), forming identifiable "resistance support networks."
- **H2**: Efflux pump AMR genes are embedded in general stress-response modules (explaining why they are overwhelmingly core), while enzymatic inactivation genes are in AMR-specific modules (explaining why they are more dispensable).
- **H3**: The size and functional composition of the support network predicts the fitness cost of an AMR gene — genes with larger or more essential support networks are costlier.
- **H4**: Support network genes overlap across organisms for the same AMR mechanism, indicating conserved co-regulatory architecture.

## Literature Context

- **Olivares Pacheco et al. (2017)** showed efflux pump costs in *P. aeruginosa* are metabolic (proton motive force drain) and compensated by metabolic rewiring — implying the support network is metabolic.
- **Melnyk et al. (2015)** found fitness costs are highly variable (CV > 100%), which our prior project narrowed to a uniform +0.086 at the organism level. The variability may reside in the support network rather than the AMR gene itself.
- **Our `aromatic_catabolism_network` project** demonstrated that ADP1's aromatic degradation requires a 51-gene support network (Complex I, iron, PQQ) identified via cofitness. This is the methodological template.
- **Our `amr_fitness_cost` project** found: (1) universal +0.086 cost across 25 organisms, (2) cost is mechanism-independent, (3) mechanism predicts conservation but not cost (χ²=69.3, p=1.4e-13), (4) efflux shows stronger antibiotic flip than enzymatic (MWU p=0.007).

**Gap**: No study has systematically mapped the co-fitness neighborhoods of AMR genes across multiple organisms. We know AMR genes are costly and that compensatory evolution reduces costs, but we don't know *which genes* constitute the compensatory/support network — or whether this network is conserved.

## Data Sources

### Primary Data Assets

| Source | Table/File | Scale | Purpose |
|--------|-----------|-------|---------|
| FB cofitness | `kescience_fitnessbrowser.cofit` | 13.6M pairs | Pairwise gene cofitness correlations |
| AMR gene catalog | `amr_fitness_cost/data/amr_genes_fb.csv` | 1,352 genes | AMR genes with mechanism/class/conservation |
| AMR fitness | `amr_fitness_cost/data/amr_fitness_noabx.csv` | 801 genes | Per-gene mean fitness under non-antibiotic conditions |
| ICA modules | `fitness_modules/data/modules/*_gene_membership.csv` | 1,116 modules | Module membership (binary) per organism |
| Module families | `fitness_modules/data/module_families/module_families.csv` | 156 families | Cross-organism module alignment |
| Family annotations | `fitness_modules/data/module_families/family_annotations.csv` | 156 families | Enriched functional terms |
| Fitness matrices | `fitness_modules/data/matrices/*_fitness_matrix.csv` | 32 organisms | Pre-cached fitness data |
| Experiment metadata | `amr_fitness_cost/data/experiment_classification.csv` | 6,804 exps | Condition labels |
| Gene annotations | `fitness_modules/data/annotations/*_gene_annotations.csv` | 32 organisms | SEED, KEGG, COG annotations |

### Key Numbers

- **25 organisms** with both AMR genes and fitness modules (intersection of amr_fitness_cost and fitness_modules)
- **801 AMR genes** with fitness data in those organisms
- **~1,116 ICA modules** across 32 organisms
- **13.6M cofitness pairs** in the `cofit` table (need to extract for our 25 organisms)

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|-------|---------|----------------|-----------------|
| `cofit` | Cofitness partners of AMR genes | ~13.6M total, ~500K per organism | Filter by `orgId` and `locusId IN (amr_loci)` |
| `gene` | Gene metadata (descriptions, type) | ~228K | Filter by `orgId` |

### Key Queries

1. **Extract cofitness partners of AMR genes** (per organism, via Spark):
```sql
SELECT orgId, locusId, hitId, CAST(cofit AS FLOAT) AS cofit, CAST(rank AS INT) AS rank
FROM kescience_fitnessbrowser.cofit
WHERE orgId = '{org}' AND locusId IN ({amr_loci})
ORDER BY CAST(cofit AS FLOAT) DESC
```

2. **Alternatively, compute cofitness from cached fitness matrices** (local, no Spark):
```python
# Pearson correlation of fitness profiles between AMR genes and all other genes
fit_mat = pd.read_csv(f'{org}_fitness_matrix.csv', index_col=0)
amr_corr = fit_mat.loc[amr_loci].T.corrwith(fit_mat.T)  # vectorized
```

### Performance Plan

- **Tier**: Hybrid — Spark for `cofit` table extraction (one query per organism), local computation for module analysis
- **Estimated complexity**: Moderate — the cofit table is large but well-indexed by orgId
- **Alternative**: Compute cofitness directly from cached fitness matrices (avoids Spark entirely, ~2 min per organism)
- **Known pitfalls**: All FB columns are strings — CAST before numeric operations; locusId type mismatch (always .astype(str))

## Analysis Plan

### Notebook 1: Data Assembly

- **Goal**: Merge AMR gene catalog with ICA module membership and extract cofitness data
- **Method**:
  1. Load AMR genes (801 with fitness data) and map to ICA modules
  2. For each organism, compute AMR gene cofitness from cached fitness matrices (faster than Spark cofit table)
  3. For each AMR gene, identify top-N cofitness partners (|r| > 0.5 threshold, or top 20)
  4. Annotate cofitness partners with functional categories (SEED, KEGG, COG)
- **Expected output**: `data/amr_cofitness_partners.csv`, `data/amr_module_membership.csv`

### Notebook 2: AMR Genes in ICA Modules

- **Goal**: Test H2 — are AMR genes in stress modules (efflux) vs isolated modules (enzymatic)?
- **Method**:
  1. For each AMR gene, identify which ICA module(s) it belongs to
  2. Characterize AMR-containing modules: size, functional annotations, % AMR genes, module family membership
  3. Compare module properties by AMR mechanism: are efflux modules larger/more broadly annotated than enzymatic modules?
  4. Test whether AMR-containing modules are enriched for stress response, membrane, or energy metabolism annotations
  5. Check whether AMR genes are in cross-organism conserved module families
- **Expected output**: `data/amr_modules_characterized.csv`, figures

### Notebook 3: Support Network Analysis

- **Goal**: Test H1 and H3 — characterize the co-fitness support network and test whether network size predicts cost
- **Method**:
  1. For each AMR gene, define the "support network" as genes with |cofitness r| > 0.5 (or top 20 partners)
  2. Functional enrichment of support networks: what COG/KEGG/SEED categories are overrepresented?
  3. Test whether AMR support networks are enriched for specific functions compared to random gene support networks (permutation test)
  4. Test H3: correlate support network size/essentiality with AMR gene fitness cost
  5. Identify "hub" support genes that appear in multiple AMR networks within an organism
- **Expected output**: `data/amr_support_networks.csv`, `data/support_network_enrichment.csv`, figures

### Notebook 4: Cross-Organism Conservation of Support Networks

- **Goal**: Test H4 — are support networks conserved across organisms for the same AMR mechanism?
- **Method**:
  1. For each AMR mechanism (efflux, enzymatic, metal), collect support network genes across all organisms
  2. Map support genes to ortholog groups (using FB `ortholog` table or KEGG KOs)
  3. Test whether the same functional categories appear in support networks for the same mechanism across organisms
  4. Identify the "core support network" — functions present in >50% of organisms for a given mechanism
  5. Compare to the `aromatic_catabolism_network` approach for methodological validation
- **Expected output**: `data/conserved_support_network.csv`, figures

## Expected Outcomes

- **If H1 supported**: AMR genes are embedded in functional neighborhoods enriched for energy metabolism, membrane maintenance, or stress response — explaining why their cost is metabolic (consistent with Olivares Pacheco et al.)
- **If H2 supported**: Efflux genes share modules with essential stress-response genes (explaining their core status and compensated cost), while enzymatic genes are in small, specialized modules (explaining their dispensability)
- **If H3 supported**: Support network size or essentiality predicts AMR cost — genes with essential support partners are costlier because knocking out the AMR gene disrupts the co-regulated network
- **If H4 supported**: The same support functions recur across organisms for the same mechanism — suggesting conserved co-regulatory architecture that could be targeted therapeutically

## Potential Confounders

1. **Genomic proximity confound**: Genes near AMR genes on the chromosome will have correlated fitness due to polar effects of transposon insertions, not true co-regulation. Mitigation: exclude genes within 5 kb of each AMR gene from the support network.
2. **Module size bias**: Larger modules are more likely to contain AMR genes by chance. Mitigation: permutation test comparing observed AMR module membership to random expectation.
3. **Annotation bias**: Well-annotated organisms may show stronger functional enrichment simply because more genes have annotations. Mitigation: report enrichment as fraction of annotated genes only.
4. **Multiple testing**: Many AMR genes × many organisms × multiple enrichment tests. Mitigation: BH-FDR within each analysis dimension.
5. **Cofitness threshold sensitivity**: The support network definition depends on the cofitness threshold. Mitigation: test multiple thresholds (|r| > 0.3, 0.4, 0.5) and report sensitivity.

## Revision History

- **v1** (2026-03-19): Initial plan

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

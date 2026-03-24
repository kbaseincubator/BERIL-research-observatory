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

### Co-fitness as functional genomics tool
- **Sagawa et al. (2017, PLoS ONE)** validated that cofitness recovers transcriptional regulatory relationships — at FDR 3%, identified significant cofitness for targets of 158 TFs in 24 bacteria. Directly supports our premise that cofitness between an AMR gene and another gene implies shared regulation. PMID: 28542589
- **Price et al. (2018, Nature)** demonstrated conserved cofitness associations provide high-confidence functional predictions for 2,316 genes across 32 bacteria. PMID: 29769716
- **Nichols et al. (2011, Cell)** pioneered chemical genomics in *E. coli*, showing condition-dependent fitness profiles reveal gene function — including insights into multiple antibiotic resistance genes. PMID: 21185072

### AMR regulatory networks and compensatory evolution
- **Patel & Matange (2021, eLife)** showed that AMR regulatory networks rewire under antibiotic selection, with compensatory rewiring that restores fitness while maintaining resistance. Cofitness could capture both original and compensatorily rewired regulatory context. PMID: 34591012
- **Eckartt et al. (2024, Nature)** identified compensatory mutations in NusG (transcription elongation factor) that restore fitness of rifampicin-resistant *M. tuberculosis* — compensatory evolution targets the same functional pathway disrupted by resistance. This predicts support networks are functionally related to the AMR gene. PMID: 38509362
- **Olivares Pacheco et al. (2017)** showed efflux pump costs in *P. aeruginosa* are metabolic (proton motive force drain) and compensated by metabolic rewiring. PMID: 28765215
- **Martinez & Rojo (2011, FEMS Microbiol Rev)** reviewed linkage between metabolism and resistance — global metabolic regulators modulate antibiotic susceptibility, supporting the hypothesis that AMR genes are embedded in broader metabolic/regulatory networks. PMID: 21645016

### The intrinsic resistome concept
- **Cox & Wright (2013)** defined the "intrinsic resistome" — genes that don't directly encode resistance but are required for it to function. This is exactly the support network we aim to map. PMID: 23499305

### Prior BERIL projects
- **`aromatic_catabolism_network`** demonstrated that ADP1's aromatic degradation requires a 51-gene support network (Complex I, iron, PQQ) identified via cofitness. This is the methodological template.
- **`amr_fitness_cost`** found: (1) universal +0.086 cost across 25 organisms, (2) cost is mechanism-independent, (3) mechanism predicts conservation but not cost (χ²=69.3, p=1.4e-13), (4) efflux shows stronger antibiotic flip than enzymatic (MWU p=0.007).
- **`fitness_modules`** decomposed fitness data into 1,116 ICA modules with 156 cross-organism families — ready to intersect with AMR genes.

**Gap**: No study has systematically mapped the co-fitness neighborhoods of AMR genes across multiple organisms. We know AMR genes are costly and that compensatory evolution reduces costs, but we don't know *which genes* constitute the compensatory/support network — or whether this network is conserved. Sagawa et al. validated cofitness as a regulatory inference tool, Eckartt et al. showed compensatory mutations target related pathways, and Cox & Wright defined the intrinsic resistome concept — but nobody has combined genome-wide cofitness with pan-bacterial AMR annotation to map these networks at scale.

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

- **~25 organisms** with both AMR genes and fitness modules (intersection to be verified in NB01)
- **801 AMR genes** with fitness data across 25 amr_fitness_cost organisms
- **~1,116 ICA modules** across 32 organisms
- **Cofitness computed locally** from cached fitness matrices (~2 min/organism, ~50 min total)

## Query Strategy

### Cofitness Computation (Primary Method)

The `cofit` table stores only top ~96 partners per gene (not all pairwise), making it unsuitable for threshold-based network definition. Instead, compute full pairwise cofitness from cached fitness matrices:

```python
# For each organism: compute Pearson correlation between each AMR gene
# and all other genes across all experiments
fit_mat = pd.read_csv(f'{org}_fitness_matrix.csv', index_col=0)
fit_mat.index = fit_mat.index.astype(str)
fit_mat = fit_mat.apply(pd.to_numeric, errors='coerce')

# Full pairwise correlation: AMR genes vs all genes
amr_profiles = fit_mat.loc[amr_loci]
all_corr = amr_profiles.T.corrwith(fit_mat.T)  # vectorized per AMR gene
```

### Tables Required (for annotation only)

| Table | Purpose | Estimated Rows | Filter Strategy |
|-------|---------|----------------|-----------------|
| Gene annotations | SEED, KEGG, COG for support network genes | Cached locally | Load from `fitness_modules/data/annotations/` |
| `ortholog` | Cross-organism gene mapping for H4 | ~1.15M | Cached in fitness_modules |

### Performance Plan

- **Tier**: Fully local — all data pre-cached in fitness matrices, ICA modules, and annotation files
- **No Spark required** for core analysis
- **Estimated runtime**: ~2 min/organism for cofitness computation, ~50 min total for 25 organisms
- **Known pitfalls**:
  - locusId type mismatch (integer vs string) — always `.astype(str)` and verify overlap before computation
  - All FB numeric values are strings — `pd.to_numeric(errors='coerce')` on fitness matrices
  - Essential genes invisible in genefitness — report fraction of AMR genes absent from matrices

## Analysis Plan

### Notebook 1: Data Assembly (~60 min runtime)

- **Goal**: Merge AMR gene catalog with ICA module membership and compute full cofitness
- **Method**:
  1. Verify organism intersection: which organisms have AMR genes AND fitness matrices AND ICA modules? Report exact count.
  2. Verify locusId overlap: for each organism, check that AMR gene locusIds exist in the fitness matrix index after `.astype(str)`. Report any 0%-overlap organisms.
  3. Report AMR gene ICA module coverage: what fraction of AMR genes are in any ICA module? If <50%, note that module analysis is supplementary.
  4. For each organism, compute full pairwise Pearson correlation between each AMR gene's fitness profile and all other genes' profiles. (~2 min/organism)
  5. For each AMR gene, extract support network at three thresholds: |r| > 0.3 (primary), |r| > 0.4, |r| > 0.5.
  6. Separate intra-operon from extra-operon partners: exclude genes within 5 ORFs on the same strand as the AMR gene (polar effect control).
  7. Annotate support network genes with functional categories (SEED, KEGG, COG from cached annotation files).
- **Expected output**: `data/amr_cofitness_partners.csv`, `data/amr_module_membership.csv`
- **Key figures**: AMR module coverage bar chart, cofitness threshold sensitivity plot

### Notebook 2: AMR Genes in ICA Modules (~10 min)

- **Goal**: Test H2 — are AMR genes in stress modules (efflux) vs isolated modules (enzymatic)?
- **Method**:
  1. For each AMR gene with module membership, characterize the module: size, functional annotations, % AMR genes, module family membership
  2. Compare module properties by AMR mechanism: are efflux modules larger/more broadly annotated than enzymatic modules? (Kruskal-Wallis)
  3. Test whether AMR-containing modules are enriched for stress response, membrane, or energy metabolism annotations vs non-AMR modules (Fisher's exact, BH-FDR across annotation categories within each organism)
  4. Check whether AMR genes are in cross-organism conserved module families (from `fitness_modules/data/module_families/`)
  5. For AMR genes NOT in any module, characterize their cofitness neighborhoods as a complementary analysis
- **Expected output**: `data/amr_modules_characterized.csv`, figures
- **Key figures**: Module annotation heatmap (AMR-containing vs all), mechanism × module type stacked bar

### Notebook 3: Support Network Analysis (~20 min)

- **Goal**: Test H1 and H3 — characterize the co-fitness support network and test whether network size predicts cost
- **Method**:
  1. For each AMR gene, define the "support network" as extra-operon genes with |cofitness r| > 0.3 (primary threshold)
  2. Functional enrichment: for each COG/KEGG/SEED category, test overrepresentation in AMR support networks vs genome background (Fisher's exact per organism, BH-FDR across categories)
  3. Permutation test for H1: select 1,000 random non-AMR gene sets matched by conservation class (core/auxiliary) and organism, compute their support networks identically, compare functional enrichment distributions. Report fraction of AMR enrichments that exceed 95th percentile of random.
  4. Test H3: correlate support network size with AMR gene fitness cost (Spearman, pooled across organisms with organism as a covariate). Acknowledge possible low power if cost variance is narrow.
  5. Identify "hub" support genes that appear in multiple AMR networks within an organism — these are candidate compensatory evolution targets.
- **Expected output**: `data/amr_support_networks.csv`, `data/support_network_enrichment.csv`, figures
- **Key figures**: Enrichment volcano plot, network size vs fitness cost scatter, hub gene frequency distribution

### Notebook 4: Cross-Organism Conservation of Support Networks (~15 min)

- **Goal**: Test H4 — are support networks conserved across organisms for the same AMR mechanism?
- **Method**:
  1. For each AMR mechanism (efflux, enzymatic, metal), collect extra-operon support network genes across all organisms
  2. Map support genes to KEGG KOs (from cached annotations) for cross-organism comparison
  3. Test H4: for each mechanism, are the same KO categories overrepresented in support networks across organisms more than expected by chance? Null model: support networks of random genes matched by conservation class show the same KO distribution. Compare to `cofitness_coinheritance` baseline (accessory modules: 36% significant after FDR).
  4. Identify the "core support network" — KO categories present in support networks of >50% of organisms for a given mechanism
  5. Compare efflux vs enzymatic vs metal support networks: do different mechanisms recruit different support functions?
- **Expected output**: `data/conserved_support_network.csv`, figures
- **Key figures**: Conservation heatmap (KO category × mechanism × organism), core support network summary

## Expected Outcomes

- **If H1 supported**: AMR genes are embedded in functional neighborhoods enriched for energy metabolism, membrane maintenance, or stress response — explaining why their cost is metabolic (consistent with Olivares Pacheco et al.)
- **If H2 supported**: Efflux genes share modules with essential stress-response genes (explaining their core status and compensated cost), while enzymatic genes are in small, specialized modules (explaining their dispensability)
- **If H3 supported**: Support network size or essentiality predicts AMR cost — genes with essential support partners are costlier because knocking out the AMR gene disrupts the co-regulated network
- **If H4 supported**: The same support functions recur across organisms for the same mechanism — suggesting conserved co-regulatory architecture that could be targeted therapeutically

## Potential Confounders

1. **Genomic proximity / operon confound**: Genes near AMR genes on the chromosome show correlated fitness from polar effects of transposon insertions, not true co-regulation. This is especially relevant for multi-gene efflux operons (regulator + inner membrane + outer membrane). Mitigation: exclude genes within 5 ORFs on the same strand; classify partners as intra-operon vs extra-operon.
2. **Module size bias**: Larger modules are more likely to contain AMR genes by chance. Mitigation: permutation test comparing observed AMR module membership to random expectation.
3. **Sparse module coverage**: ICA modules contain ~700 genes/organism, so many AMR genes may not be in any module. Mitigation: report coverage fraction; supplement module analysis with direct cofitness neighborhoods.
4. **Annotation bias**: Well-annotated organisms may show stronger functional enrichment. Mitigation: report enrichment as fraction of annotated genes only; compare across organisms with similar annotation rates.
5. **Multiple testing**: NB02: BH-FDR across annotation categories within each organism. NB03: BH-FDR across COG/KEGG/SEED categories per organism; permutation test provides a separate non-parametric control. NB04: BH-FDR across KO categories per mechanism. Target FDR = 0.05 throughout.
6. **Cofitness threshold sensitivity**: Support network definition depends on threshold. Mitigation: test |r| > 0.3 (primary), 0.4, 0.5 and report all three.
7. **H3 power concern**: Per-gene fitness cost variance may be narrow (most genes near −0.024 with tight distribution), limiting ability to detect a correlation with network size. Mitigation: report variance; consider pooling across organisms with organism as covariate.
8. **Essential AMR genes**: ~4.6% of AMR genes are absent from fitness matrices (putatively essential). These are excluded from support network analysis but may be the most interesting cases. Mitigation: report count and acknowledge.

## Revision History

- **v2** (2026-03-19): Incorporated plan review — switched to local cofitness computation (cofit table stores only top ~96 partners), lowered primary threshold to |r|>0.3, added operon separation, specified permutation design (1000 draws, conservation-matched), added FDR scope per notebook, added module coverage check, added runtime estimates
- **v1** (2026-03-19): Initial plan

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

# Research Plan: Aromatic Catabolism Support Network in ADP1

## Research Question
Why does aromatic catabolism in *Acinetobacter baylyi* ADP1 require Complex I (NADH dehydrogenase), iron acquisition, and PQQ biosynthesis when growth on other carbon sources does not? Is this a specific metabolic dependency network, or an artifact of the growth assay?

## Hypothesis
- **H0**: The quinate-specific growth defects of Complex I, iron acquisition, and PQQ genes are unrelated to aromatic catabolism — they reflect general housekeeping requirements that happen to be masked on other carbon sources by the assay's limited dynamic range.
- **H1**: Aromatic catabolism via the β-ketoadipate pathway creates specific metabolic dependencies on (a) Complex I for NADH reoxidation, (b) iron acquisition for the Fe²⁺-dependent protocatechuate 3,4-dioxygenase, and (c) PQQ for the quinoprotein quinate dehydrogenase, forming a coherent support network not required by non-aromatic carbon sources.

## Literature Context
- **Stanier & Ornston (1973)** established the β-ketoadipate pathway: quinate → 3-dehydroquinate → protocatechuate → β-carboxymuconate → β-ketoadipate → succinyl-CoA + acetyl-CoA → TCA cycle. The pathway feeds into central metabolism via TCA intermediates.
- **Dal et al. (2005)** mapped the transcriptional organization of the pca/qui gene cluster in ADP1, showing coordinate regulation by protocatechuate as inducer.
- **Stuani et al. (2014)** performed multi-omics (transcriptomics, metabolomics, proteomics) comparing ADP1 growth on quinate vs succinate. They found 4/5 PQQ biosynthesis genes upregulated on quinate and observed amino acid biosynthesis restructuring.
- **Erickson et al. (2022)** reviewed critical enzyme reactions in aromatic catabolism, noting that ring-cleavage dioxygenases require non-heme iron and that NADH/NADPH serve as electron donors in several pathway steps.
- **Fischer et al. (2008)** characterized carbon catabolite repression of aromatic degradation in ADP1, showing coordinate regulation of multiple catabolic operons.
- **Prior project (adp1_deletion_phenotypes)**: Identified 51 quinate-specific genes including 10 Complex I subunits, 6 pca/qui pathway genes, 3 iron acquisition genes, 2 PQQ biosynthesis genes, and 6 transcriptional regulators.

## Approach

### Data Overview

The analysis uses the 51 quinate-specific genes (specificity > 0.5, z-score < -1.0 on quinate) identified in `projects/adp1_deletion_phenotypes/`, categorized into functional groups:

| Category | Genes | Key members |
|----------|-------|-------------|
| Aromatic degradation pathway | 6 | pcaB, pcaC, pcaG, pcaH, quiA, quiB |
| Complex I (NADH dehydrogenase) | 10 | nuoA–N (chains A, E, F, G, H, I, J, K, M, N) |
| Iron acquisition | 3 | AcsD-like siderophore, ExbD/TolR, ferrichrome receptor |
| PQQ biosynthesis | 2 | pqqC, pqqD |
| Transcriptional regulation | 6 | LysR, Lrp, AraC, DeoR, IclR family regulators |
| Unknown/Other | 24 | Various — potential new pathway members |

### Aim 1: Metabolic Dependency Mapping
**Goal**: Trace the biochemical logic connecting aromatic catabolism to each support system.

**Methods**:
- Map the quinate → TCA pathway step-by-step, annotating each reaction's cofactor requirements (Fe²⁺, PQQ, NAD⁺/NADH)
- Count NADH produced per mole of quinate catabolized vs glucose, acetate, and other carbon sources using the ADP1 FBA model (`gene_reaction_data`, `genome_reactions` tables)
- Compare FBA-predicted essentiality of the 51 genes across 9 aromatic vs 5 non-aromatic carbon sources using `gene_phenotypes` (230 conditions available)
- Test: does FBA predict the quinate-specificity of Complex I, or is this a gap in the model?

### Aim 2: Operon and Regulon Structure
**Goal**: Determine whether the 51 quinate-specific genes are genomically clustered and co-regulated.

**Methods**:
- Plot gene positions along the ADP1 chromosome — are the support genes (Complex I, iron, PQQ) near the pca/qui cluster, or scattered?
- Identify operon structure from intergenic distances (<100 bp, same strand = likely same operon)
- Check whether the 6 transcriptional regulators control known aromatic degradation regulons
- Cross-reference with Dal et al. (2005) transcriptional organization

### Aim 3: Cross-Species Conservation
**Goal**: Test whether the Complex I/aromatic catabolism dependency is conserved beyond ADP1.

**Methods**:
- Query `kescience_fitnessbrowser` for experiments where organisms were grown on aromatic substrates (benzoate, 4-hydroxybenzoate, protocatechuate, quinate). Check if any of the 48 FB organisms have aromatic-condition fitness data. Note: ADP1 is NOT one of the 48 FB organisms. Survey FB experiments in NB01 as a feasibility check.
- For organisms with data: do Complex I genes (KOs K00330–K00343) show condition-specific fitness defects on aromatics?
- Cross-species pangenome comparison: gene cluster IDs are species-specific and cannot be compared across species. Instead, use **KO annotations** via `eggnog_mapper_annotations.KEGG_ko` (joined on `gene_cluster_id = query_name`) to identify pca pathway orthologs (K00448, K00449, K01607, K01857, K01055, K05358, K03785) and Complex I orthologs (K00330–K00343) across Acinetobacter species. Test whether genomes carrying pca pathway KOs are more likely to also carry Complex I.
- Reference `metal_fitness_atlas` project for FB-to-pangenome organism mapping methodology

### Aim 4: Characterize the "Other" Genes
**Goal**: Assign functions to the 24 quinate-specific genes without clear pathway assignments.

**Methods**:
- Build a co-fitness network using pairwise correlations across the 8-condition growth matrix: which of the 24 unknowns cluster with the pca pathway genes vs Complex I vs iron acquisition?
- Check if any of the 24 genes are in the same operons as known pathway genes
- Search for ortholog functions in other characterized aromatic-degrading bacteria
- Use the FBA model (`gene_reaction_data`) to check if any of the 24 genes map to reactions in the aromatic degradation subsystem

## Query Strategy

### Tables Required
| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `genome_features` (SQLite) | Gene positions, annotations, growth data | 5,852 | Full scan |
| `gene_phenotypes` (SQLite) | FBA predictions across 230 carbon sources | 239,584 | Filter by ADP1 gene IDs |
| `gene_reaction_data` (SQLite) | Gene-reaction mappings with flux | varies | Filter by ADP1 |
| `genome_reactions` (SQLite) | Full reaction details | varies | Filter by ADP1 |
| `kescience_fitnessbrowser.experiment` (BERDL) | Find aromatic-condition experiments | small | Filter by condition name |
| `kescience_fitnessbrowser.genefitness` (BERDL) | Fitness scores for aromatic conditions | 27M | Filter by orgId + condition |
| `kbase_ke_pangenome.eggnog_mapper_annotations` (BERDL) | KO annotations for cross-species comparison | 93M | Filter by KEGG_ko IN (pca KOs, nuo KOs) |
| `kbase_ke_pangenome.gene_cluster` (BERDL) | Link KO annotations to species | 132M | Join via gene_cluster_id = query_name |

### Performance Plan
- **Execution environment**: Local machine for SQLite analysis (NB01–03); BERDL JupyterHub for Spark queries (NB04 if needed)
- **Tier**: Mostly local Python; Spark only for cross-species queries
- **Known pitfalls**: FB all-string columns require CAST; genefitness filter by orgId

## Analysis Plan

### Notebook 1: Metabolic Dependency Mapping
- **Goal**: Trace cofactor requirements through the β-ketoadipate pathway, compare NADH yield across carbon sources using FBA, test FBA prediction of quinate-specificity
- **Expected output**: Pathway diagram annotations, FBA aromatic vs non-aromatic comparison table, `data/fba_aromatic_comparison.csv`

### Notebook 2: Genomic Organization and Operon Structure
- **Goal**: Map all 51 genes on the chromosome, identify operons, characterize regulatory network
- **Expected output**: Chromosome map figure, operon assignments, `data/operon_assignments.csv`

### Notebook 3: Co-fitness Network and Unknown Gene Assignment
- **Goal**: Build gene-gene correlation network from growth profiles, assign unknowns to support subsystems
- **Expected output**: Network figure, unknown gene assignments, `data/cofitness_network.csv`

### Notebook 4: Cross-Species Validation (if FB aromatic data exists)
- **Goal**: Test whether Complex I/aromatic dependency is conserved in other bacteria
- **Expected output**: Cross-species comparison table, conservation figure

## Expected Outcomes
- **If H1 supported**: The three support systems (Complex I, iron, PQQ) form a coherent metabolic dependency network around aromatic catabolism, each traceable to specific biochemical requirements. FBA may partially predict this (PQQ, iron) but likely misses Complex I, revealing a gap in the metabolic model. Some of the 24 unknown genes will cluster with specific support subsystems, suggesting new pathway members.
- **If H0 not rejected**: Complex I defects on quinate reflect general respiratory stress (quinate is an inherently low-energy substrate) rather than a specific pathway dependency. Iron and PQQ requirements are direct cofactor needs of known enzymes, not a network phenomenon.
- **Potential confounders**:
  - The growth ratio assay may have non-linear responses near zero, exaggerating defects on quinate
  - Quinate's mean growth ratio (1.36) is the highest of all conditions — "defect" means growth drops from above-WT to below-WT, which may reflect different biology than defects on demanding substrates
  - Complex I may be generally important for aerobic respiration and only appears quinate-specific because other conditions mask the defect

## Revision History
- **v2** (2026-02-19): Addressed plan reviewer feedback — specified KO-based cross-species comparison (gene clusters are species-specific), noted ADP1 not in FB, added FB feasibility check to NB01, referenced metal_fitness_atlas methodology
- **v1** (2026-02-19): Initial plan

## Authors
- Paramvir Dehal (ORCID: 0000-0001-5810-2497), Lawrence Berkeley National Laboratory

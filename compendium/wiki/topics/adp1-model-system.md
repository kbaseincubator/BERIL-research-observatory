# ADP1 Model System

*Acinetobacter baylyi* ADP1 is a naturally competent soil bacterium that this corpus treats as a workbench for asking a deceptively simple question: what does it mean for a gene to "matter"? The strain is metabolically versatile — most notably an avid degrader of aromatic compounds — and it has been characterized with an unusually dense stack of experimental and computational assays. This page exists because five separate projects in the compendium converge on the same ADP1 multi-omics resource and, from different angles, reach a shared conclusion: gene importance is not one property but several, and the methods we use to measure it (gene knockouts, transposon fitness, flux modeling, proteomics, condition-resolved growth) each see a different facet. ADP1 is where the wiki makes that disagreement concrete and quantitative.

## Overview

The anchor resource is a user-provided SQLite database integrated by the `acinetobacter_adp1_explorer` project: 15 tables, roughly 461,522 rows and 135 MB, whose central `genome_features` table holds 5,852 genes annotated across 51 columns spanning six data modalities. That breadth is the reason ADP1 earns its own page — it is one of the few organisms in this collection where lethality (knockout essentiality), metabolic necessity (flux balance analysis, or FBA), fitness cost (RB-TnSeq), expression requirement (proteomics), and condition-specific optimization (carbon-source growth assays) can all be examined for the same genes. Crucially, *A. baylyi* ADP1 is absent from the Fitness Browser, so the condition-specific mutant growth data assembled here is a unique fitness resource not duplicated elsewhere in BERDL (the BER Data Lakehouse).

The five contributing projects partition naturally. One characterizes and connects the database itself; one mines a deletion-collection growth matrix for phenotypic structure; one cross-compares five definitions of essentiality head-to-head; one dissects the gene network supporting aromatic (quinate) catabolism; and one reconstructs how the branched respiratory chain is wired condition by condition. The recurring protagonist that ties the metabolic projects together is Complex I (NADH:ubiquinone oxidoreductase) and the substrate quinate — an aromatic carbon source whose catabolism turns out to stress the cell's NADH-handling machinery in a way no other tested condition does.

## What the Corpus Shows

**Essentiality is media- and method-dependent, not a fixed label.** Even the simplest measure — which genes are essential — shifts with growth medium: 499 genes are essential on minimal media versus 346 on LB, the gap reflecting the extra biosynthetic burden minimal media imposes. The deeper finding from the `adp1_triple_essentiality` project is that the assays disagree systematically rather than noisily. Knockout, FBA, RB-TnSeq, proteomics, and growth assays each measure a distinct facet of gene importance, so none is ground truth. RB-TnSeq (randomly barcoded transposon sequencing, which reads out fitness cost from pooled mutant abundance) disagrees with knockout lethality across every threshold tested (negative Cohen's kappa): only 7.9% (18 of 229) of knockout-essential genes are flagged essential by RB-TnSeq, while hundreds of genes are called essential by one method and dispensable by the other. The lesson is that RB-TnSeq captures fitness cost, not lethality. Yet when the question is reframed as prediction rather than agreement, RB-TnSeq becomes the single best signal: continuous fitness scores predict essentiality at AUC 0.70–0.73, whereas the binarized `essentiality_fraction` performs worse than random (AUC < 0.5) — discretization throws away the information. Proteomics independently corroborates the picture: protein expression correlates with essentiality (r = 0.35, AUC = 0.74), with essential genes expressed about 6.5-fold higher than dispensable ones (Mann-Whitney p ≈ 1e-58).

**FBA has a specific, diagnosable blind spot.** Among 478 TnSeq-dispensable, triple-covered genes, FBA essentiality class shows no significant association with measured growth-defect status (chi-squared = 0.93, p = 0.63), a null result robust across growth-defect thresholds (Kruskal-Wallis H = 1.67, p = 0.43). The failure is not random: aromatic degradation genes, including β-ketoadipate pathway enzymes, are strongly enriched among FBA-discordant genes (odds ratio 9.70, q = 0.012). FBA's minimal-media definition simply does not encode the aromatic-degradation context these genes serve, so the model systematically mispredicts them.

**The phenotype landscape is continuous, with one sharp exception.** The `adp1_deletion_phenotypes` project clustered ~2,034 genes by their growth profiles across 8 carbon sources. Conditions sort into demanding, moderate, and robust tiers — urea most demanding (97.9% of genes defective), quinate most robust (only 1.6% defective). PCA shows 5 components capture 82% of the variance, so the 8 carbon sources supply roughly 5 independent dimensions of phenotypic information. But hierarchical clustering yields only a weak K=3 structure (silhouette 0.24) with no FDR-surviving functional enrichment, meaning gene importance varies continuously rather than falling into discrete modules. Against that continuum, 625 genes (31%) have a condition-specificity score ≥ 1.0, concentrating their importance on a single carbon source. The one genuinely discrete module is a set of 24 aromatic-degradation genes with extreme quinate-specific defects (mean z-score -7.28).

**Aromatic catabolism demands a large, distributed support network.** The `aromatic_catabolism_network` project found that quinate catabolism requires a 51-gene support network organized into four functional subsystems beyond the core β-ketoadipate pathway. These subsystems sit at distinct chromosomal locations with no cross-category operons, so the dependency is biochemical, not genomic co-localization — it emerges from the chemistry of aromatic ring cleavage. The dominant requirement is Complex I, which accounts for 21 of the 51 quinate-specific genes (41%).

**Respiratory wiring is a passive, flux-driven switch.** The `respiratory_chain_wiring` project resolved why quinate, despite yielding fewer NADH per carbon, makes Complex I more essential. ADP1 carries three parallel NADH dehydrogenases — Complex I, NDH-2, and ACIAD3522 — with distinct, non-overlapping condition profiles (ACIAD3522 is specifically lethal on acetate). All three are constitutively co-expressed at similar protein levels, so the chain is not switched transcriptionally; it operates as a passive, flux-based system at the metabolic level, choosing qualitatively different configurations per carbon source rather than scaling a single flux gradient. The quinate paradox resolves through NADH flux *rate*: ring cleavage via the β-ketoadipate pathway creates a concentrated TCA-cycle NADH burst that exceeds NDH-2's reoxidation capacity, forcing reliance on high-capacity Complex I. This is precisely the capacity constraint FBA cannot see — FBA predicts zero flux through NDH-2 and ACIAD3522 because it optimizes growth yield and routes NADH through the more ATP-efficient Complex I.

## Projects and Evidence

The `acinetobacter_adp1_explorer` project supplies the substrate and demonstrates that it is not an isolated dataset. A gene junction table bridged the database's mmseqs2-style cluster IDs to BERDL centroid gene IDs, mapping all 4,891 BERDL clusters to 4,081 unique ADP1 clusters despite a 0% direct string match — a reminder that integration here required an explicit identifier crosswalk, not naive joins. Four of five connection types to BERDL collections matched at over 90% (100% of genome IDs and compounds, 91% of reactions), demonstrating deep lakehouse integration. Proteomics across 7 engineered strains for 2,383 genes showed high cross-strain correlation, indicating the engineered modifications have targeted rather than global proteome effects.

The four downstream projects each take a slice of this resource. `adp1_deletion_phenotypes` and `adp1_triple_essentiality` work the gene-level statistics — the continuous phenotype landscape and the cross-method essentiality comparison, respectively. `aromatic_catabolism_network` and `respiratory_chain_wiring` zoom into the quinate/Complex I story, the former cataloguing the 51-gene support network and the latter explaining its mechanistic basis. The two metabolic projects independently arrive at NDH-2 as the missing piece: the aromatic-network project proposes that ADP1's apparent quinate-specificity of Complex I reflects an alternative NADH dehydrogenase compensating on simpler, lower-flux substrates (a low-confidence claim), and the wiring project confirms NDH-2 (KO K03885) is a standalone core-genome gene, TnSeq-dispensable, outside any respiratory operon.

## Connections

ADP1 sits at the intersection of several wiki topics. Its tightest link is to [Gene Fitness](gene-fitness.md): nearly every essentiality and condition-dependent result here is a statement about how fitness is measured and what it predicts, and ADP1's RB-TnSeq data is a fitness resource unavailable in the Fitness Browser. The metabolic backbone of this page — FBA's blind spot, the β-ketoadipate pathway, the three NADH dehydrogenases, the rate-versus-yield principle — belongs to [Metabolic Pathways](metabolic-pathways.md), which is the natural home for the broader claim that substrates concentrating reducing equivalents demand high-capacity NADH reoxidation regardless of total yield. The cluster-ID bridge and NDH-2's core-genome status connect to [Pangenome Architecture](pangenome-architecture.md), since placing ADP1 genes in a pangenome required reconciling distinct clustering schemes. The suggestion that ADP1's respiratory wiring may be species-specific rather than a universal rule links to [Microbial Ecotypes](microbial-ecotypes.md), and the proposal to construct an NDH-2 deletion mutant reaches into [Microbiome Engineering](microbiome-engineering.md). The page also relates to [Functional Dark Matter](functional-dark-matter.md) through the support-network genes whose roles only become visible under specific conditions.

The underlying data resources are themselves adjacent: the [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md) (notable here for *not* containing ADP1), the [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) and [Kbase Uniref](../data/kbase-uniref.md) collections used for cluster mapping, the [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md) reactions that matched at 91%, and the [Phagefoundry](../data/phagefoundry.md) collection. Contributing authors are tracked at [0000 0001 5810 2497](../authors/0000-0001-5810-2497.md) and [0009 0007 0287 2979](../authors/0009-0007-0287-2979.md).

## Caveats and Open Directions

Several results rest on acknowledged limitations. The growth matrix is built from single-timepoint ratios with unknown technical noise, so the condition-specificity analysis assumes cross-condition variation reflects biology rather than measurement error. The complete 2,034-gene matrix excludes 499 essential genes and 316 genes with incomplete data, biasing the analysis toward dispensable genes with successful deletion mutants. RB-TnSeq's value as a lethality proxy is intrinsically limited because transposon insertion is not gene deletion — some knockout-essential genes appear TnSeq-dispensable because partial or truncated protein function suffices. And no gene in the database carries data across all six modalities; sparse FBA flux coverage (15%) limits model-experiment concordance analysis to just 866 genes.

The biggest weakness is the centerpiece NDH-2 compensation hypothesis. NDH-2 is absent from the deletion collection and has no growth data, so the prediction that its loss would make Complex I essential on glucose cannot be directly tested — by the authors' own assessment, the weakest finding in the respiratory study, and the species-specificity of the wiring pattern remains an open question. Three concrete experiments would close these gaps: searching the ADP1 genome for NDH-2 genes and testing their deletion phenotype on quinate versus glucose; constructing an NDH-2 deletion mutant for the definitive test; and adding trace aromatic compounds to the FBA minimal-media definition to resolve the systematic β-ketoadipate discordance. On the analysis side, a machine-learning predictor integrating FBA, fitness, and proteomics may outperform any single method for essentiality — a natural follow-on given that each method demonstrably measures different biology.

## Sources

- [stmt:adp1-multiomics-database; acinetobacter_adp1_explorer]
- [stmt:adp1-fitness-unique-resource; acinetobacter_adp1_explorer]
- [stmt:cluster-id-bridge; acinetobacter_adp1_explorer]
- [stmt:berdl-connectivity; acinetobacter_adp1_explorer]
- [stmt:proteomics-targeted-effects; acinetobacter_adp1_explorer]
- [stmt:modality-overlap-limitation; acinetobacter_adp1_explorer]
- [stmt:essentiality-media-dependence; acinetobacter_adp1_explorer]
- [stmt:methods-measure-different-biology; adp1_triple_essentiality]
- [stmt:rbtnseq-systematic-discordance; adp1_triple_essentiality]
- [stmt:tnseq-misses-essential; adp1_triple_essentiality]
- [stmt:fitness-best-essentiality-predictor; adp1_triple_essentiality]
- [stmt:proteomics-validates-essentiality; adp1_triple_essentiality]
- [stmt:fba-no-growth-defect-prediction; adp1_triple_essentiality]
- [stmt:fba-null-robust-thresholds; adp1_triple_essentiality]
- [stmt:aromatic-fba-discordance; adp1_triple_essentiality]
- [stmt:adp1-three-tier-landscape; adp1_deletion_phenotypes]
- [stmt:conditions-five-independent-dimensions; adp1_deletion_phenotypes]
- [stmt:phenotype-landscape-continuum; adp1_deletion_phenotypes]
- [stmt:condition-specific-genes-fraction; adp1_deletion_phenotypes]
- [stmt:quinate-aromatic-module; adp1_deletion_phenotypes]
- [stmt:support-network-51-genes-finding; aromatic_catabolism_network]
- [stmt:genomic-independence-finding; aromatic_catabolism_network]
- [stmt:complex-i-dominant-subsystem-finding; aromatic_catabolism_network]
- [stmt:ndh2-compensation-claim; aromatic_catabolism_network]
- [stmt:three-parallel-nadh-dehydrogenases; respiratory_chain_wiring]
- [stmt:respiratory-wiring-is-metabolic-not-transcriptional; respiratory_chain_wiring]
- [stmt:condition-specific-respiratory-wiring; respiratory_chain_wiring]
- [stmt:quinate-complex-i-paradox-flux-rate; respiratory_chain_wiring]
- [stmt:fba-misses-capacity-constraints; respiratory_chain_wiring]
- [stmt:rate-vs-yield-principle; respiratory_chain_wiring]
- [stmt:ndh2-core-genome; respiratory_chain_wiring]
- [stmt:wiring-pattern-may-be-species-specific; respiratory_chain_wiring]
- [stmt:caveat-growth-ratios-noise; adp1_deletion_phenotypes]
- [stmt:caveat-dispensable-bias; adp1_deletion_phenotypes]
- [stmt:transposon-not-deletion-caveat; adp1_triple_essentiality]
- [stmt:caveat-ndh2-no-growth-data; respiratory_chain_wiring]
- [stmt:ndh2-search-opportunity; aromatic_catabolism_network]
- [stmt:opportunity-ndh2-deletion-mutant; respiratory_chain_wiring]
- [stmt:refine-fba-aromatic-media; adp1_triple_essentiality]
- [stmt:combined-predictor-opportunity; adp1_triple_essentiality]

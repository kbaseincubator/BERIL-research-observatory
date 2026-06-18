# Adp1 Model System

*Acinetobacter baylyi* ADP1 is a gram-negative soil bacterium that has become a workhorse model system for studying bacterial metabolism, gene function, and aromatic compound catabolism. It is naturally competent, grows rapidly on diverse carbon sources, and carries a well-annotated ~3.6 Mb chromosome. This page synthesizes findings from five projects in the corpus that collectively characterize ADP1's phenotype landscape, its multi-omics data infrastructure, the reliability of different methods for inferring gene essentiality, and the condition-specific wiring of its respiratory chain.

## Overview

The ADP1 model system occupies a unique place in this wiki because it is the only organism in the corpus for which the integrated BERDL data lakehouse currently lacks fitness data from the Fitness Browser—*A. baylyi* ADP1 is simply absent from that resource [\[1\]](#references). The projects assembled here therefore constitute a primary data source rather than a re-analysis of existing public data. Together they cover six complementary data modalities (TnSeq essentiality, flux balance analysis predictions, mutant growth fitness across eight carbon sources, proteomics across seven engineered strains, pangenome classification, and functional annotations) captured in a SQLite database with 5,852 genes across 15 tables totaling 135 MB [\[2\]](#references). The ADP1 database connects to BERDL at four of five connection types at over 90%, with 100% of genome IDs and compounds matched and 91% of metabolic reactions matched [\[3\]](#references). A complete bridge between the database's own cluster IDs (mmseqs2-style) and BERDL centroid gene IDs was constructed through the gene junction table, achieving 100% mapping of all 4,891 BERDL clusters to 4,081 unique ADP1 clusters despite zero direct string overlap [\[4\]](#references).

## What the Corpus Shows

### Phenotype landscape across carbon sources

The ADP1 deletion collection was grown on eight carbon sources and the results reveal a three-tier essentiality landscape: demanding conditions (urea, acetate, butanediol, with 95–100% of genes showing growth defects), moderate conditions (asparagine, lactate), and robust conditions (glucarate, glucose, quinate, with only 0.5–2.4% of genes defective) [\[5\]](#references). Importantly, the 8 conditions are not redundant—principal component analysis of the 2,034-by-8 growth matrix requires five PCs to explain 82% of the variance, meaning the panel provides roughly five independent dimensions of phenotypic information [\[6\]](#references). Despite this dimensionality, hierarchical clustering of gene growth profiles yields only a weak K=3 structure (silhouette 0.24) with no FDR-surviving functional enrichments, indicating that gene essentiality varies continuously across conditions rather than organizing into discrete functional modules [\[7\]](#references). The sole exception is a group of 24 aromatic degradation genes that forms the only discrete phenotypic module, showing extreme quinate-specific growth defects (mean z-score −7.28 on quinate, near-zero elsewhere) [\[8\]](#references). Overall, 625 genes (31% of the full matrix) concentrate their growth importance on a single carbon source, as measured by a condition-specificity score ≥ 1.0 [\[9\]](#references).

### Aromatic catabolism support network

The aromatic catabolism findings are particularly detailed. Aromatic (quinate) catabolism in ADP1 requires not just the core beta-ketoadipate pathway—a central route converting ring compounds through protocatechuate to TCA-cycle intermediates succinyl-CoA and acetyl-CoA—but a 51-gene support network spanning four metabolic subsystems: the core aromatic pathway itself (8 genes), Complex I/NADH dehydrogenase (21 genes), iron acquisition (7 genes), and PQQ biosynthesis (2 genes), plus six transcriptional regulators [\[10\]](#references). Complex I (the multi-subunit NADH:ubiquinone oxidoreductase that pumps protons while reoxidizing NADH) accounts for 21 of the 51 quinate-specific genes (41%), making it the dominant support requirement [\[11\]](#references). Crucially, the four subsystems reside at completely separate chromosomal locations with no cross-category operons, so the metabolic coupling is not encoded by genomic co-localization but emerges purely from the biochemical requirements of aromatic ring cleavage [\[12\]](#references).

### Respiratory chain wiring

The respiratory chain studies deepen this picture. ADP1's 62-gene branched respiratory chain uses qualitatively different configurations for different carbon sources—quinate requires only Complex I, while acetate demands Complex I plus cytochrome bo3 plus ACIAD3522 and more, and glucose requires no specific respiratory component at all [\[13\]](#references). Three parallel NADH dehydrogenases with non-overlapping condition requirements implement this: Complex I (13 subunits, proton-pumping), NDH-2 (a single-subunit, non-proton-pumping alternative dehydrogenase), and ACIAD3522 (an NADH-FMN oxidoreductase whose deletion is specifically lethal on acetate) [\[14\]](#references). NDH-2 is a core-genome, standalone gene that is TnSeq-dispensable but absent from the deletion collection, so it has no direct growth data [\[15\]](#references).

The apparent paradox that quinate (which yields fewer NADH per carbon, 0.57 versus 1.50 for glucose) makes Complex I more essential is resolved by considering the rate of NADH production rather than its total yield: aromatic ring cleavage via the beta-ketoadipate pathway releases succinyl-CoA and acetyl-CoA simultaneously, creating a concentrated NADH burst in the TCA cycle that exceeds NDH-2's reoxidation capacity, while glucose distributes NADH production across the Entner-Doudoroff pathway and TCA cycle, staying within NDH-2's capacity [\[16\]](#references). This rate-versus-yield principle—that substrates producing concentrated reducing equivalents demand high-capacity NADH reoxidation regardless of total NADH yield—is expected to generalize to other carbon sources with similar flux patterns [\[17\]](#references). Proteomics confirms that all three NADH dehydrogenases are constitutively expressed at similar protein levels under standard conditions, so condition-specific wiring operates as a passive flux-based system rather than an active transcriptional switch [\[18\]](#references). Flux balance analysis (FBA), which predicts metabolic fluxes from a stoichiometric model of the metabolic network, fails to capture this because it optimizes for growth rate and always routes NADH through the more ATP-efficient Complex I, predicting zero flux through NDH-2 and ACIAD3522 on all media [\[19\]](#references).

### Multi-method essentiality comparison

A recurring theme is that different methods measure different biological phenomena and therefore cannot be treated as interchangeable. Flux balance analysis (FBA) captures metabolic necessity; knockout (KO) experiments measure lethality; RB-TnSeq (random-barcode transposon sequencing, which surveys the fitness cost of random transposon insertions across thousands of mutants simultaneously) measures fitness cost; proteomics indicates expression requirement; and mutant growth assays capture condition-specific optimization [\[20\]](#references). The discordances are systematic: only 7.9% (18 of 229) of KO-essential ADP1 genes are flagged as essential by RB-TnSeq at the optimal threshold, and across all tested thresholds RB-TnSeq shows negative Cohen's kappa against KO experiments, indicating systematic disagreement worse than chance [\[21\]](#references) [\[22\]](#references). Continuous RB-TnSeq fitness scores are nevertheless the best predictor of essentiality (AUC 0.70–0.73), outperforming binary essentiality-fraction, which performs worse than random (AUC < 0.5) [\[23\]](#references). Protein expression provides an independent validation axis: essential genes are expressed 6.5-fold higher than dispensable genes (r=0.35, AUC=0.74, Mann-Whitney p=9.91×10⁻⁵⁹) [\[24\]](#references).

FBA achieves moderate concordance with knockout truth (κ≈0.49, F1≈0.62–0.67) but does not predict which TnSeq-dispensable genes have measurable growth defects—FBA essentiality class is not significantly associated with growth-defect status (chi-squared=0.93, p=0.63), and this null result is robust across thresholds Q10–Q35 [\[25\]](#references) [\[26\]](#references). Among the functional categories most discordant with FBA predictions, aromatic degradation genes are strongly enriched (OR=9.70, q=0.012), with 9 of 11 aromatic degradation genes showing FBA under-prediction [\[27\]](#references). The FBA model assigns zero flux to beta-ketoadipate pathway genes under its minimal-media assumptions, yet their deletions impair growth—a systematic gap between the in silico environmental conditions and the actual experimental media [\[28\]](#references).

Gene essentiality is also media-dependent, with 499 genes essential on minimal media versus only 346 on LB rich medium, reflecting the additional biosynthetic burden of defined minimal conditions [\[29\]](#references). Proteomics across seven engineered strains shows high cross-strain correlation, confirming that the targeted aromatic pathway modifications have specific rather than global proteome effects [\[30\]](#references).

## Projects and Evidence

Five projects contribute directly to the ADP1 model system:

**acinetobacter_adp1_explorer** — Built the multi-omics SQLite database and documented its BERDL connectivity. It established that ADP1 fitness data is unique to this resource and produced the pangenome cluster-ID bridge enabling joins to lakehouse annotations. The FBA/TnSeq concordance analysis and condition-specific fitness profiling are also part of this project.

**adp1_deletion_phenotypes** — Systematic analysis of the ADP1 deletion collection grown on eight carbon sources. Produced the three-tier landscape, the PCA showing five independent phenotypic dimensions, the finding that the phenotype landscape is a continuum rather than discrete modules, and the identification of the quinate/aromatic degradation module as the sole discrete exception.

**adp1_triple_essentiality** — Comprehensive comparison of FBA, RB-TnSeq, knockout experiments, and proteomics for predicting gene essentiality. Found that continuous fitness scores are the best single predictor, that FBA and TnSeq measure distinct biology and systematically disagree, and that aromatic degradation genes expose a systematic FBA model gap.

**aromatic_catabolism_network** — Mapped the full 51-gene support network required for quinate catabolism, identified Complex I as its largest component, showed that the four support subsystems are genomically independent, and used cross-species co-fitness to propose NDH-2 as the Complex I compensator on non-aromatic substrates.

**respiratory_chain_wiring** — Demonstrated condition-specific qualitative wiring of the respiratory chain, resolved the quinate-Complex I paradox via the rate-versus-yield principle, showed that all three NADH dehydrogenases are constitutively expressed (metabolic rather than transcriptional regulation), and showed that FBA misses capacity constraints by always routing NADH through the most ATP-efficient pathway.

## Connections

The ADP1 model system intersects with several other topics and datasets in this wiki:

[Gene Fitness](../topics/gene-fitness.md) is the closest adjacent topic. The deletion collection and RB-TnSeq analyses are the primary sources of gene fitness evidence in this system, and the finding that different fitness-related methods capture different biology is a central contribution to understanding what fitness data actually measures.

[Metabolic Pathways](../topics/metabolic-pathways.md) connects because the aromatic catabolism support network and the FBA discordances are inherently about pathway organization—specifically how the beta-ketoadipate pathway creates cofactor and NADH demands that propagate to unrelated genes on the chromosome.

[Pangenome Architecture](../topics/pangenome-architecture.md) is adjacent because the cluster-ID bridge enables any BERDL pangenome annotation to be joined to ADP1 genes, and because the 272 dispensable genes missing from the deletion collection are significantly less conserved across *Acinetobacter* species, linking gene dispensability to pangenome status through evolutionary retention pressure.

[Functional Dark Matter](../topics/functional-dark-matter.md) is relevant because co-fitness analysis assigned 16 previously unknown or uncharacterized ADP1 genes to specific subsystems within the quinate support network, and seven more quinate-specific genes remain unassigned.

[Microbial Ecotypes](../topics/microbial-ecotypes.md) connects through the question of whether the ADP1 respiratory wiring pattern (NDH-2 compensating for Complex I on low-NADH-flux substrates) is specific to ADP1 or a general cross-species rule. Cross-species ortholog analysis suggests it may be ADP1-specific [\[31\]](#references).

[Microbiome Engineering](../topics/microbiome-engineering.md) is adjacent because ADP1's well-characterized aromatic degradation capacity and its genetic tractability make it a candidate chassis for engineering, and the phenotype landscape provides a gene-by-carbon-source fitness map directly useful for metabolic engineering design.

## Caveats and Open Directions

Several methodological limitations should temper conclusions drawn from this body of work.

The deletion collection phenotype data relies on single-timepoint growth ratios with unknown technical noise, so the condition-specificity analysis assumes cross-condition variation reflects biology rather than measurement error [\[32\]](#references). The 2,034-gene matrix excludes 499 essential genes and 316 genes with incomplete data, biasing all matrix-level analyses toward dispensable genes that survived the deletion process [\[33\]](#references). The transposon-insertion technique used by RB-TnSeq is also not equivalent to gene deletion: some genes that are lethal to delete appear TnSeq-dispensable because truncated or partial protein function suffices, and this explains most of the 211 KO-essential/TnSeq-dispensable discordances [\[34\]](#references). The multi-omics database itself has a coverage ceiling: no gene carries data across all six modalities, and FBA flux data (covering only 15% of genes) is particularly sparse, limiting any model-experiment concordance analysis to 866 genes [\[35\]](#references).

For the respiratory chain work, the most important open question is that NDH-2—the gene predicted to compensate for Complex I on glucose—is absent from the deletion collection and therefore has no growth data, making the central compensation prediction untestable with existing resources [\[36\]](#references). An NDH-2 deletion mutant in ADP1 would provide a definitive test: if NDH-2 loss makes Complex I essential on glucose, the flux-rate hypothesis would be confirmed [\[37\]](#references). Searching the ADP1 genome for additional NDH-2 (type 2 NADH dehydrogenase, KO K03885) homologs and comparing their deletion phenotypes on quinate versus glucose would also be informative [\[38\]](#references).

On the modeling side, adding trace aromatic compounds to the FBA minimal-media definition may resolve the systematic discordance in beta-ketoadipate pathway genes, since the model's assumption of a purely inorganic minimal medium may not match the actual experimental media composition [\[28\]](#references). Finally, a machine-learning predictor integrating FBA, continuous fitness scores, and proteomics may achieve better essentiality prediction than any individual method [\[39\]](#references), though this has not yet been implemented.

## References

1. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "2. Strong BERDL Connectivity: 4 of 5 Connection Types at >90% Match".
2. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "1. Rich Multi-Omics Database with 6 Data Modalities".
3. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "2. Strong BERDL Connectivity: 4 of 5 Connection Types at >90% Match".
4. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "3. Pangenome Cluster ID Bridge: 100% Mapping via Gene Junction Table".
5. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "1. Carbon sources define a three-tier essentiality landscape".
6. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "2. Conditions are largely independent — 5 PCs capture 82% of variance".
7. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "3. The phenotype landscape is a continuum, not discrete modules".
8. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "3. The phenotype landscape is a continuum, not discrete modules".
9. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "4. Condition-specific genes reveal the metabolic architecture of ADP1".
10. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "1. Aromatic catabolism requires a 51-gene support network spanning 4 metabolic subsystems".
11. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "2. Complex I is the largest support subsystem — and invisible to FBA".
12. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "3. Support subsystems are genomically independent but metabolically coupled".
13. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "1. Each carbon source uses a distinct respiratory chain configuration".
14. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "2. ADP1 has three parallel NADH dehydrogenases with distinct condition profiles".
15. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "2. ADP1 has three parallel NADH dehydrogenases with distinct condition profiles".
16. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "3. The quinate-Complex I paradox is resolved by NADH flux rate, not total yield".
17. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "Novel Contribution".
18. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "5. Proteomics: respiratory wiring is metabolic, not transcriptional".
19. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "FBA Model Limitations".
20. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Executive Summary".
21. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "From Both Studies".
22. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Results".
23. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Executive Summary".
24. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Results".
25. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Key Findings".
26. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Key Findings".
27. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Key Findings".
28. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Aromatic Catabolism: A Case Study in Model Limitations".
29. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "4. FBA and TnSeq Essentiality Agree 74% of the Time".
30. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "Proteomics Cross-Strain Analysis".
31. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "Novel Contribution".
32. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "Limitations".
33. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "Limitations".
34. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Why Does RB-TnSeq Disagree with KO Experiments?".
35. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "Limitations".
36. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "Limitations".
37. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "Future Directions".
38. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "Future Directions".
39. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Future Work".

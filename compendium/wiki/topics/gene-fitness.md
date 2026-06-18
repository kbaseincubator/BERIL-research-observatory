# Gene Fitness

## Overview

Gene fitness, in the context of this corpus, refers to the quantitative effect on a microorganism's growth rate when a specific gene is disrupted — typically measured by Randomized Barcoded Transposon sequencing (RB-TnSeq), where tens of thousands of transposon-insertion mutants compete in a pool under defined conditions and the change in each mutant's barcode abundance over time is converted to a fitness score. A score near zero means the gene is dispensable under that condition; a strongly negative score means losing the gene is costly; a positive score means the gene was actually a drag on growth. This page exists as a hub for the largest single conceptual thread running through this wiki: that quantitative gene fitness measurements, aggregated across species and conditions, reveal how natural selection shapes the bacterial genome — which genes are kept, which are lost, and what they do.

The [Fitness Browser](https://fit.genomics.lbl.gov), a database maintained by the Arkin Lab and accessible through BERDL as the `kescience_fitnessbrowser` data collection, is the primary empirical anchor. It aggregates roughly 27 million fitness measurements across more than 40 diverse bacteria. Projects across this corpus variously mine, extend, validate, and critique that resource, connecting it to pangenome conservation, antibiotic resistance, metabolic modeling, environmental ecology, and functional annotation of dark genes.

## What the Corpus Shows

**The core genome is the most functionally active part of the genome.** A synthesis connecting the Fitness Browser (~194,000 genes across 43 bacteria) to the KBase pangenome (27,690 microbial species) shows that essential genes reside in the core at a rate of roughly 82–86%, and that this gradient between essential and always-neutral genes spans about 16 percentage points [\[1\]](#references). Core genes show the largest fitness effects in both directions — they are more beneficial when present and more costly when disrupted — because they are embedded in critical pathways [\[2\]](#references). The relationship is a continuous gradient across the full spectrum from essential to neutral, not a binary split [\[3\]](#references).

**Any fitness importance, regardless of condition, predicts conservation.** When fitness effects are stratified by whether a condition was ecologically relevant (field-like) versus a laboratory convenience, the dominant finding is that universally important genes — those with strong effects across many condition types — are significantly more core than neutral genes [\[4\]](#references). Field-stress genes are somewhat more conserved than lab-specific genes [\[5\]](#references), but the effect of condition type is weaker than the raw magnitude of the fitness effect [\[6\]](#references). This implies the core genome reflects general functional importance rather than niche-specific adaptation alone.

**Fitness modules reveal pan-bacterial co-regulation programs.** Robust Independent Component Analysis (ICA) — a matrix decomposition method that finds statistically independent axes of variation — applied to Fitness Browser gene-fitness matrices decomposes the data into latent modules of co-regulated genes [\[7\]](#references). Across organisms, 1,116 stable modules emerge, and the largest module family spans 21 organisms, pointing to a deeply conserved pan-bacterial co-regulation program [\[8\]](#references) [\[9\]](#references). These modules are significantly enriched in core genes (OR = 1.46, p = 1.6×10⁻⁸⁷), confirming that co-regulated functional units preferentially reside in the conserved genome [\[10\]](#references). Importantly, conservation is a property of individual genes rather than of the cross-organism scope of their regulatory module [\[11\]](#references).

**Gene co-fitness predicts co-inheritance in pangenomes.** Co-fitness — when two genes show correlated fitness effects across conditions — predicts whether those genes co-occur across genomes, and this effect is strongest for accessory genome gene pairs [\[12\]](#references) [\[13\]](#references). Coordinated regulation across multiple genes, rather than pairwise functional similarity alone, most strongly constrains co-inheritance [\[14\]](#references). The co-fitness signal anticorrelates with phylogenetic distance, partly because shared ancestry inflates apparent co-occurrence [\[15\]](#references).

**Core genes carry a metabolic burden paradox.** A counterintuitive finding emerges when the sign of fitness effects is examined: core genome genes are *more* likely than accessory genes to show positive fitness effects when deleted, meaning they are more often a metabolic drag in the lab [\[16\]](#references). This "burden paradox" resolves once lab conditions are recognized as an impoverished proxy for nature — core genes encode energetically expensive functions like motility, ribosomal biosynthesis, and RNA metabolism that are essential in soil, biofilm, or host tissue but costly in rich broth [\[17\]](#references) [\[18\]](#references). The 28,017 genes that are simultaneously costly in the lab yet broadly conserved constitute the strongest evidence for purifying selection maintaining genes despite their metabolic overhead [\[19\]](#references).

**AMR genes impose a real but small fitness cost.** The first pan-bacterial meta-analysis of antibiotic resistance gene (ARG) fitness costs, using 27 million measurements across 25 diverse bacteria, finds that the average cost is +0.086 fitness units — measurable but modest [\[20\]](#references) [\[21\]](#references). The cost is consistent across resistance mechanisms (efflux pumps, target modification, enzymatic inactivation), and there is no statistically significant difference between mechanisms [\[22\]](#references). Strikingly, fitness cost can flip sign in the presence of the cognate antibiotic — an efflux pump that is costly in drug-free media becomes beneficial when the drug is present [\[23\]](#references), and this flip is mechanism-dependent [\[24\]](#references).

**Condition-specific fitness effects dominate single-gene phenotypes.** In *Acinetobacter baylyi* ADP1 — a model organism with a comprehensive deletion library — fitness across 8 carbon sources is only moderately correlated (mean pairwise r = 0.44), and 625 genes (31% of the tested matrix) concentrate their importance on a single carbon source [\[25\]](#references). The 8 conditions provide roughly 5 independent dimensions of phenotypic variation [\[26\]](#references), and condition-specific genes map precisely to the expected metabolic pathways (urease subunits for urea catabolism, protocatechuate degradation genes for quinate) [\[27\]](#references). This organism-level dataset is unique because ADP1 is absent from the Fitness Browser [\[28\]](#references).

**Essential genes are annotation-rich but essentiality is context-dependent.** Across organisms, essential genes carry far more functional annotation than dispensable ones — in ADP1, 92% of essential genes carry KEGG KO assignments versus 53% of dispensable genes [\[29\]](#references). However, essentiality is strongly media-dependent: 499 ADP1 genes are essential on minimal media versus only 346 on rich LB [\[30\]](#references). At the pan-bacterial scale, only about 5% of gene families are universally essential across 48 organisms [\[31\]](#references), and this small universally essential set is smaller than computational minimal-gene-set estimates [\[32\]](#references). These pan-universal essential families are the only reliable broad-spectrum antibiotic targets [\[33\]](#references).

**Multiple measurement methods capture distinct facets of gene importance.** Knockout lethality (does removing the gene kill the cell?), FBA flux modeling (flux balance analysis — a stoichiometric model of which reactions must carry flux for growth), RB-TnSeq fitness (how much does a transposon insertion slow growth?), proteomics (is the protein expressed?), and condition-specific growth assays each measure something different [\[34\]](#references). In ADP1, continuous RB-TnSeq fitness scores are the best single predictor of gene essentiality (AUC = 0.70–0.73), outperforming FBA (Cohen's κ ≈ 0.49) and proteomics (AUC = 0.74 but using held-out expression data) [\[35\]](#references). FBA and TnSeq agree for 73.8% of the 866 genes tested in both [\[36\]](#references), and the discordant 26% are candidates for model refinement.

**Costly-and-dispensable genes mark ongoing gene loss.** A cross-organism characterization of 142,190 genes across 43 bacteria identifies genes that are simultaneously burdensome in the lab (positive deletion fitness) and poorly conserved in the pangenome — the first such pan-bacterial dataset [\[37\]](#references). These 5,526 genes carry hallmarks of recent acquisition: short, poorly annotated, taxonomically restricted, and enriched in singletons [\[38\]](#references). They are candidates for ongoing gene loss, having been acquired but imposing sufficient cost that they will likely be purged unless they confer a situational advantage [\[39\]](#references).

## Projects and Evidence

**Core fitness-conservation projects.** The [`fitness_effects_conservation`](../projects/fitness-effects-conservation.md) project provides the statistical backbone connecting fitness magnitude to pangenome conservation across 43 organisms, establishing the 16-percentage-point gradient and the claim that the core genome is functionally active rather than inert [\[40\]](#references). The [`conservation_vs_fitness`](../projects/conservation-vs-fitness.md) project cross-references essentiality against core/auxiliary status and finds that essential genes are enriched in the core (OR = 1.56) and that this enrichment is robust across clade sizes and lifestyles [\[41\]](#references). The [`conservation_fitness_synthesis`](../projects/conservation-fitness-synthesis.md) project combines both datasets into an integrated view and flags internal discrepancies in reported figures [\[42\]](#references).

**Single-organism deep dives (ADP1).** The [`acinetobacter_adp1_explorer`](../projects/acinetobacter-adp1-explorer.md), [`adp1_deletion_phenotypes`](../projects/adp1-deletion-phenotypes.md), and [`adp1_triple_essentiality`](../projects/adp1-triple-essentiality.md) projects together exploit the unique ADP1 deletion library (a complete set of single-gene knockouts for most non-essential genes) to map phenotypic landscapes across carbon sources, compare multiple measurement technologies, and identify the surprisingly poor overlap between RB-TnSeq and knockout essentiality calls [\[43\]](#references). Only 7.9% of knockout-essential genes are flagged as essential by RB-TnSeq at the optimal threshold [\[43\]](#references), because transposon insertion is not equivalent to gene deletion — truncated proteins can sometimes substitute [\[44\]](#references).

**AMR fitness projects.** The [`amr_fitness_cost`](../projects/amr-fitness-cost.md) project delivers the pan-bacterial AMR cost analysis across 25 organisms, while [`amr_cofitness_networks`](../projects/amr-cofitness-networks.md) maps the first pan-bacterial co-fitness neighborhoods of AMR genes across 28 organisms [\[45\]](#references). The co-fitness neighborhoods are enriched in flagellar biosynthesis and amino acid biosynthesis genes [\[46\]](#references), though this may partly reflect shared dispensability under lab conditions rather than true mechanistic co-regulation [\[47\]](#references). AMR genes show a low essential rate (~4.6%) [\[48\]](#references) and the [`amr_pangenome_atlas`](../projects/amr-pangenome-atlas.md) project separately confirms that AMR genes do not appear to impose a detectable fitness burden at the pangenome scale [\[49\]](#references).

**Fitness modules.** The [`fitness_modules`](../projects/fitness-modules.md) project applies ICA to fitness matrices from the Fitness Browser, identifying 1,116 stable modules and generating function predictions for hypothetical genes by guilt-by-association within modules [\[50\]](#references). Genomic adjacency enrichment confirms modules are not confounded by operon structure [\[51\]](#references). The [`module_conservation`](../projects/module-conservation.md) project then tests whether modules are enriched in core genes (they are) and finds that 59% of fitness modules are more than 90% core [\[52\]](#references).

**Field versus lab fitness.** The [`field_vs_lab_fitness`](../projects/field-vs-lab-fitness.md) project is the first to stratify RB-TnSeq fitness effects by ecological relevance, examining whether genes important under field-like stress conditions (metals, osmolarity) are more conserved than genes important only under lab conditions [\[53\]](#references). The [`lab_field_ecology`](../projects/lab-field-ecology.md) project takes the complementary approach of directly linking Fitness Browser lab fitness data with ENIGMA CORAL field community data across a geochemical gradient — the first such integration [\[54\]](#references). Importantly, lab fitness does not simply predict field abundance because field niches are multidimensional and involve community interactions [\[55\]](#references).

**Genotype-to-phenotype prediction.** The [`genotype_to_phenotype_enigma`](../projects/genotype-to-phenotype-enigma.md) project explores how well genome content (KEGG Ortholog presence/absence) predicts growth outcomes across ENIGMA strains. It finds that mechanistic condition-specific prediction requires on the order of 46,000 training pairs [\[56\]](#references), that binary growth is predictable for amino acids and nucleosides [\[57\]](#references), but that continuous growth parameters are not reliably predictable [\[58\]](#references).

**Essential metabolome and metabolic pathways.** The [`essential_metabolome`](../projects/essential-metabolome.md) project surveys which biosynthetic pathways are functionally essential across organisms, finding that complete amino acid biosynthesis pathways are present in 6 of 7 organisms — suggesting prototrophy is the ancestral state for free-living bacteria [\[59\]](#references). Amino acid biosynthesis genes show high conservation [\[60\]](#references). See the [Metabolic Pathways](../topics/metabolic-pathways.md) page for the pathway-level view of these dependencies.

**Functional dark matter.** The [`functional_dark_matter`](../projects/functional-dark-matter.md) project uses the Fitness Browser as a major resource for characterizing genes with no known function, finding cross-organism concordance in fitness signals for dark genes and proposing a dual-route experimental campaign [\[61\]](#references). Over half of dark gene ortholog groups are pan-bacterial [\[62\]](#references), meaning functional dark matter is a fundamental limit to understanding conserved biology, not a minor annotation gap. See the [Functional Dark Matter](../topics/functional-dark-matter.md) page for details.

## Connections

**Pangenome architecture.** Gene fitness is most interpretable in the context of what is present and absent across genomes. The [Pangenome Architecture](../topics/pangenome-architecture.md) page covers the core/accessory genome framework that underlies the conservation axis in fitness-conservation analyses.

**AMR resistome.** The [AMR Resistome](../topics/amr-resistome.md) page covers the ecology and spread of resistance genes; this page addresses the functional cost side of that equation and why resistance genes persist despite their overhead.

**Metabolic pathways.** The [Metabolic Pathways](../topics/metabolic-pathways.md) page is adjacent because many fitness effects are mediated by pathway membership — genes in essential pathways are essential, genes in latent pathways can be cost-neutral.

**Functional dark matter.** The [Functional Dark Matter](../topics/functional-dark-matter.md) page is directly coupled: the Fitness Browser is one of the primary evidence types for assigning function to unannotated genes, making fitness data the experimental bridge to reducing the dark matter fraction.

**Adp1 model system.** The [Adp1 Model System](../topics/adp1-model-system.md) page covers *Acinetobacter baylyi* ADP1 comprehensively; the fitness data from its deletion library is one of the most detailed single-organism phenotypic datasets in the corpus.

**Microbial ecotypes.** The [Microbial Ecotypes](../topics/microbial-ecotypes.md) page connects fitness to the question of how genotypic variation maps to ecological differentiation, relevant because field-vs-lab fitness comparisons are fundamentally asking whether lab phenotypes predict environmental niches.

**Metal resistance.** The [Metal Resistance](../topics/metal-resistance.md) page is adjacent because several projects explicitly test whether metal-resistance genes carry detectable fitness costs — the same analytical framework applied to antibiotic resistance.

## Caveats and Open Directions

**Measurement heterogeneity across methods.** No single assay is ground truth for gene importance. Binary essentiality from transposon screens, continuous fitness from RB-TnSeq, FBA lethality predictions, and deletion-based growth assays each capture a different facet [\[34\]](#references). RB-TnSeq systematically misses knockout-essential genes because partial protein function can sustain viability [\[44\]](#references). Binary essentiality fraction aggregated across conditions performs worse than random as an essentiality classifier (AUC = 0.34–0.40) [\[63\]](#references), highlighting that aggregation obscures condition-specific biology.

**Lab conditions are an impoverished proxy for nature.** The Fitness Browser organisms are lab-adapted, and the condition set is biased toward experimental convenience [\[64\]](#references). All 25 organisms in the AMR cost analysis are lab-adapted strains, and compensatory evolution during laboratory maintenance may have reduced measurable costs below what wild strains experience [\[65\]](#references). The fitness-conservation gradient, while robust (statistically significant), explains only a modest fraction of conservation variance, and single-gene-knockout measurements miss epistatic interactions [\[66\]](#references).

**Taxonomic and organism bias.** The Fitness Browser is biased toward Pseudomonas and other culturable Proteobacteria [\[67\]](#references) [\[68\]](#references). Key ecologically important lineages such as Rhodanobacter, which dominates contaminated Oak Ridge wells, are entirely absent [\[69\]](#references). Archaea are severely underrepresented [\[70\]](#references).

**Cofitness is not co-regulation.** High cofitness implies shared fitness phenotypes, not direct transcriptional co-regulation [\[71\]](#references). Enrichments in co-fitness neighborhoods can reflect shared experimental context or shared dispensability under lab conditions rather than mechanistic coupling [\[47\]](#references). A fitness-matched permutation test would help disentangle these [\[72\]](#references).

**Internal discrepancies in the synthesis layer.** The [`conservation_fitness_synthesis`](../projects/conservation-fitness-synthesis.md) project flags a figure-text discrepancy in which the reported 16-percentage-point gradient is inconsistent between the notebook and the prose due to different denominator choices for "percent core" [\[42\]](#references). The synthesis also reports two different essential-gene core rates (82% and 86%) without fully reconciling them [\[73\]](#references).

**Open directions.** A machine-learning predictor integrating FBA, fitness, and proteomics could outperform any single method for essentiality prediction [\[74\]](#references). Expanding the Fitness Browser to organisms from underrepresented environments (soil, subsurface, archaea) would test whether the fitness-conservation gradient generalizes beyond the current Proteobacteria-centric sample [\[75\]](#references). Connecting lab fitness data to AlphaEarth environmental genomics data could test whether organisms from more variable environments carry more trade-off genes [\[76\]](#references). A dual-route experimental campaign (evidence-weighted CRISPRi screens plus conservation-weighted broad transposon screens) offers the most tractable path to characterizing functional dark matter [\[77\]](#references).

## References

1. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — README.md › "Overview".
2. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Interpretation".
3. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Interpretation".
4. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Specificity Analysis: Lab-Specific Genes Are Surprisingly More Core".
5. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Genes Important for Field Conditions Are Significantly More Conserved (NB03)".
6. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Novel Contribution".
7. [Fitness Modules](../projects/fitness-modules.md) — README.md › "Overview".
8. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "ICA Decomposition (32 organisms)".
9. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Cross-Organism Alignment".
10. [Module Conservation](../projects/module-conservation.md) — REPORT.md › "Interpretation".
11. [Module Conservation](../projects/module-conservation.md) — REPORT.md › "Interpretation".
12. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Pairwise Co-fitness Weakly Predicts Co-occurrence".
13. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "ICA Modules Show Co-inheritance, Especially Accessory Modules".
14. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Interpretation".
15. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Co-fitness Strength Weakly Anti-correlates with Co-occurrence".
16. [Core Gene Tradeoffs](../projects/core-gene-tradeoffs.md) — README.md › "Overview".
17. [Core Gene Tradeoffs](../projects/core-gene-tradeoffs.md) — REPORT.md › "Interpretation".
18. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REPORT.md › "The Resolution".
19. [Core Gene Tradeoffs](../projects/core-gene-tradeoffs.md) — REPORT.md › "Interpretation".
20. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Novel Contribution".
21. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "The cost of resistance is universal but uniform".
22. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "3. Resistance mechanism does not predict fitness cost (H2 not supported)".
23. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "2. AMR genes become more important under antibiotic pressure (H4 partially supported)".
24. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "2. AMR genes become more important under antibiotic pressure (H4 partially supported)".
25. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "4. Condition-specific genes reveal the metabolic architecture of ADP1".
26. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "2. Conditions are largely independent — 5 PCs capture 82% of variance".
27. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "4. Condition-specific genes reveal the metabolic architecture of ADP1".
28. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "2. Strong BERDL Connectivity: 4 of 5 Connection Types at >90% Match".
29. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "6. Essential Genes Are 6x More Likely to Have COG Annotations".
30. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "4. FBA and TnSeq Essentiality Agree 74% of the Time".
31. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "Only 5% of Ortholog Families Are Universally Essential".
32. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "The Essential Genome Is Small and Deeply Conserved".
33. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "Variable Essentiality Is the Norm, Not the Exception".
34. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Executive Summary".
35. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Executive Summary".
36. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "4. FBA and TnSeq Essentiality Agree 74% of the Time".
37. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Novel Contribution".
38. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "They Are Poorly Characterized Recent Acquisitions".
39. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Interpretation".
40. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Breadth of Fitness Effects Predicts Conservation".
41. [Conservation Vs Fitness](../projects/conservation-vs-fitness.md) — REPORT.md › "Validation".
42. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REVIEW.md › "Methodology".
43. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "From Both Studies".
44. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Why Does RB-TnSeq Disagree with KO Experiments?".
45. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Novel Contribution".
46. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "2. AMR support networks are enriched for flagellar motility and amino acid biosynthesis (H1 supported)".
47. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "2. AMR support networks are enriched for flagellar motility and amino acid biosynthesis (H1 supported)".
48. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "1. Universal cost of resistance across 25 bacterial species (H1 supported)".
49. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "6. AMR Genes Are Not a Fitness Burden in Lab Conditions".
50. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Function Prediction".
51. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "ICA Decomposition (32 organisms)".
52. [Module Conservation](../projects/module-conservation.md) — REPORT.md › "Most Modules Are Core".
53. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Condition Classification (NB02)".
54. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Novel Contribution".
55. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Why Lab Fitness Doesn't Simply Predict Field Ecology".
56. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — README.md › "Key Lessons Learned".
57. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Executive Summary".
58. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Executive Summary".
59. [Essential Metabolome](../projects/essential-metabolome.md) — REPORT.md › "Near-Universal Amino Acid Biosynthesis".
60. [Essential Metabolome](../projects/essential-metabolome.md) — REPORT.md › "High Conservation of Amino Acid Biosynthesis Pathways".
61. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 4: Cross-organism fitness concordance identifies 65 ortholog groups with conserved dark gene phenotypes".
62. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 14: Pangenome-scale conservation × hypothesis classification reveals broadly conserved true knowledge gaps; conservation-weighted covering set orders experiments for maximum novel discovery".
63. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Results".
64. [Core Gene Tradeoffs](../projects/core-gene-tradeoffs.md) — REPORT.md › "Limitations".
65. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
66. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Limitations".
67. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Limitations".
68. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "Limitations".
69. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Future Directions".
70. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "R3. Archaeal PGLS and formal power analysis (exploratory, n = 48)".
71. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Limitations".
72. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Future Directions".
73. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REVIEW.md › "Methodology".
74. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Future Work".
75. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Limitations".
76. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REPORT.md › "Open Questions".
77. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Future Directions".

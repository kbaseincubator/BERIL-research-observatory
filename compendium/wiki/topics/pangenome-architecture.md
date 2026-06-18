# Pangenome Architecture

The **pangenome** of a bacterial species is the complete set of genes found in any member of that species — the union of all gene clusters across all sequenced strains. It divides naturally into a **core genome** (genes present in nearly every strain, typically ≥95% prevalence) and an **accessory genome** (genes present in some but not all strains). Pangenome architecture refers to how genes are distributed between these partitions, what functions they encode, how they got there, and what this tells us about bacterial ecology and evolution. This page synthesizes findings across dozens of projects in this corpus that all converge on the same question: *which genes are universal, which are variable, and why?*

## Overview

Every bacterial species carries far more genetic potential collectively than any single strain does individually. The KBase/BERDL pangenome resource — spanning 27,690 microbial species across 293,059 genomes — provides unprecedented statistical power to study this variation [\[1\]](#references). At this scale, the core/accessory partition is not merely a classification convenience; it reflects deep evolutionary forces.

The canonical "two-speed genome" model holds that core genes evolve slowly under purifying selection while accessory genes turn over rapidly through horizontal gene transfer (HGT) — the movement of DNA between organisms that are not parent and offspring. This corpus largely confirms that picture but adds crucial nuance: the core genome is not inert housekeeping machinery but the most *functionally active* part of the genome [\[2\]](#references), accessory genes are less burdensome than streamlining theory predicts [\[3\]](#references), and the open/closed distinction (how readily a species acquires new genes) does not predict ecological or phylogenetic drivers as cleanly as once hoped [\[4\]](#references).

## What the Corpus Shows

### The Two-Speed Genome Is Universal

Across 32 species spanning 9 bacterial phyla, COG (Clusters of Orthologous Groups) functional category analysis reveals a universal functional partitioning between core and novel genes [\[5\]](#references). Core genes are consistently enriched in translation (COG J, -4.65% novel-gene enrichment at 97% cross-species consistency), nucleotide metabolism (COG F), and coenzyme biosynthesis (COG H) [\[6\]](#references) [\[7\]](#references). Novel and singleton genes — those unique to one or a few strains — are overwhelmingly enriched in mobile element functions (COG L, +10.88% at 100% consistency) and defense mechanisms (COG V, +2.83% at 100% consistency) [\[8\]](#references) [\[9\]](#references). This partitioning holds universally across phyla, suggesting a deep evolutionary constraint [\[10\]](#references). In short, core genes are the ancient metabolic engine, while novel genes are recent acquisitions for ecological skirmishing.

### Core Genes Are the Most Functionally Active Part of the Genome

A common misconception frames the core genome as a boring housekeeping layer and the accessory genome as the interesting adaptive reservoir. The data here overturn this: core genes show the largest fitness effects in *both* directions — they are more likely to be growth-essential and more likely to be burdensome (growth-inhibiting) than accessory genes when disrupted [\[11\]](#references) [\[12\]](#references). Connecting ~194,000 genes in the Fitness Browser (RB-TnSeq fitness measurements, where pooled-transposon libraries quantify how each gene's disruption affects growth across diverse conditions) to the KBase pangenome reveals a quantitative fitness-conservation gradient: essential genes are 82% core, always-neutral genes 66% core [\[13\]](#references). The relationship is continuous rather than a sharp essential/non-essential cutoff [\[14\]](#references), and genes important under many experimental conditions are disproportionately core (conservation rises from 66% for zero-condition importance to 79% for 20+ conditions; Spearman rho = 0.086) [\[15\]](#references).

Intriguingly, condition type matters less than fitness magnitude for predicting conservation: genes with large fitness effects under lab conditions and under ecologically realistic field conditions are both enriched in the core genome at comparable rates [\[16\]](#references). Any fitness importance predicts conservation — field-stress genes are 83.6% core (OR=1.58), lab-nutrient genes are similarly enriched, and counterintuitively, lab-specific essential genes are 96% core, slightly *higher* than field-specific genes at 88.5% [\[17\]](#references) [\[18\]](#references).

### The Core-Burden Paradox

Perhaps the most striking finding across this corpus is the **core-burden paradox**: core genome genes are *more* likely than accessory genes to show positive fitness when deleted (i.e., to be burdens), with 24.4% of core genes burdensome versus 19.9% of accessory genes [\[19\]](#references). This contradicts the streamlining hypothesis, which predicts that accessory genes are the metabolic burden. The burden is function-specific: protein metabolism (+6.2 pp core excess), motility (+7.8 pp), and RNA metabolism (+12.9 pp) drive the pattern, while cell wall genes reverse it (-14.1 pp) [\[20\]](#references). The resolution is that core genes are embedded in critical pathways where disruption of one component imposes cost even in conditions where that component is unneeded — they are ecologically important trade-offs, not evolutionary dead weight [\[21\]](#references).

Consistent with this, true trade-off genes — important in some conditions, burdensome in others — number 25,271 (17.8% of the studied set) and are 1.29x more likely to be core (OR=1.29, p=1.2e-44) [\[22\]](#references).

### Co-Regulated Modules Are Predominantly Core

The two-speed partitioning extends from individual genes to co-regulated *modules* — sets of genes whose fitness effects rise and fall together across conditions, inferred by Independent Component Analysis (ICA) decomposition of fitness data. ICA fitness modules across 32 organisms are significantly enriched in core genes (86% core vs. 81.5% baseline; OR=1.46, p=1.6e-87), and 59% of modules are >90% core [\[23\]](#references) [\[24\]](#references). The median module is 93.4% core [\[25\]](#references). Conserved module families span organisms ranging from 2 to 21 species, including a pan-bacterial co-regulation program [\[26\]](#references) [\[27\]](#references). The co-inheritance signal (whether module members co-occur across pangenome strains) is strongest for accessory modules [\[28\]](#references), where the variance in gene presence/absence makes the signal detectable — but this is a statistical ceiling effect, not a biological reversal of the core-enrichment pattern [\[29\]](#references).

### Essential Genes: A Small, Deep Core

Experimentally defined universal essentials — genes where transposon disruption is lethal across all tested organisms — form a tiny, deeply conserved subset. Only 5% of cross-organism ortholog families (859/17,222) are universally essential, dominated by ribosomal proteins plus groEL, pyrG, fusA, and valS [\[30\]](#references) [\[31\]](#references). Universally essential genes are 91.7% core versus 80.7% for non-essential genes, while orphan essentials — essential only in a single organism — are just 49.5% core, reflecting strain-specific functions [\[32\]](#references). Essentiality is strain-dependent and evolvable: the same gene can be essential in one strain and dispensable in another, extending this principle across 48 phylogenetically diverse bacteria and archaea [\[33\]](#references).

### Openness: What It Measures and What It Does Not Predict

**Pangenome openness** — operationalized as the fraction of variable (auxiliary + singleton) genes, or equivalently 1 minus the core fraction — quantifies how readily a species acquires new genes. Across the corpus, open pangenome species exhibit broader ecological niche breadth (r=0.324, p=5.6e-47) [\[34\]](#references), and a high core fraction correlates *negatively* with niche breadth (r=-0.445, p=1.4e-91) [\[35\]](#references). The number of variable metabolic pathways correlates strongly with pangenome openness (partial Spearman rho=0.530 after controlling for genome count) [\[36\]](#references), and metabolic ecotype count per species also correlates with openness [\[37\]](#references).

Despite this, openness as a single metric is a poor predictor of the *driver* of gene content variation. Pangenome openness shows near-zero correlation with both environmental and phylogenetic effect sizes on gene content (environment rho=-0.05, phylogeny rho=0.03, both non-significant) [\[38\]](#references) [\[39\]](#references). This null result implies that whether a species has an open or closed pangenome does not determine whether environment or phylogeny dominates its gene-content variation [\[4\]](#references), and that HGT may be opportunistic rather than ecologically directed [\[40\]](#references).

### Costly Dispensable Genes: The Genomic Debris of HGT

A distinctive class identified across 43 bacteria — genes that are simultaneously fitness-costly in the lab and not conserved across the species pangenome — represents the **genomic debris of horizontal gene transfer**. These 5,526 costly-and-dispensable genes are 7.45x more likely to carry mobile element annotations, 11.7x enriched in the SEED Phage/Transposon/Plasmid category, poorly annotated (only 50.8% with SEED annotations vs. 74.9% for costly+conserved), and taxonomically restricted [\[41\]](#references) [\[42\]](#references) [\[43\]](#references). These are insertion sequences, prophage remnants, transposases, and defense systems acquired via HGT but not yet fixed or purged [\[44\]](#references) [\[45\]](#references). They are candidates for ongoing gene loss — acquired but imposing enough cost that purifying selection will eventually remove them unless a specific environment provides a compensating benefit [\[46\]](#references).

### AMR Genes Are Depleted from the Core Genome

Antibiotic resistance genes (AMR genes) are a well-studied case of accessory genome content. Across 14,723 species, AMR genes are markedly depleted from the bacterial core genome (30.3% core vs. 46.8% pangenome baseline, OR=0.49; 2.2x enriched in the auxiliary genome), and this depletion is consistent across 63.7% of 4,252 tested species [\[47\]](#references) [\[48\]](#references). Within species, over 90% of AMR gene occurrences are variable or rare, with strains sharing less than 60% of their AMR repertoire [\[49\]](#references).

The ecological gradient is striking: accessory AMR constitutes 43% of the resistome in soil species, rising to 68% in clinical isolates and 80% in human gut species [\[50\]](#references). Klebsiella pneumoniae exemplifies this: of 1,115 AMR gene clusters, only 7 are core, and its entire effective resistome is accessory [\[51\]](#references). Resistance mechanism determines conservation: efflux and enzymatic resistance genes are overwhelmingly core, while metal resistance genes are 44% accessory [\[52\]](#references). Counterintuitively, core and accessory AMR genes have identical fitness costs (mean -0.024 each, Cohen's d = 0.002), so the accessory/core distinction reflects ecology and acquisition history rather than intrinsic metabolic burden [\[53\]](#references).

## Projects and Evidence

The largest direct contribution to pangenome architecture comes from projects that explicitly cross fitness data with conservation data. The **conservation_fitness_synthesis** project bridges the Fitness Browser (RB-TnSeq experiments across 43 bacteria) with the KBase pangenome, confirming the fitness-conservation gradient across 194,216 genes [\[2\]](#references). The **cog_analysis** project's universal two-speed genome finding across 32 species and 9 phyla establishes the functional template [\[5\]](#references). The **module_conservation** project extends the core-enrichment finding from individual genes to co-regulatory units [\[54\]](#references). The **costly_dispensable_genes** project provides the first cross-organism characterization of the HGT debris class [\[55\]](#references).

Several projects anchor the AMR side: **amr_pangenome_atlas** quantified the intrinsic-acquired dichotomy across 14,723 species simultaneously [\[56\]](#references), **amr_strain_variation** provided the first systematic within-species quantification across 1,305 species [\[57\]](#references), and **amr_fitness_cost** showed that core and accessory AMR genes are equally fit [\[53\]](#references). The **acinetobacter_adp1_explorer** project demonstrated that within the 14 Acinetobacter genomes, core metabolism is 94% shared (1,248/1,330 reactions) [\[58\]](#references). For specific gene families, the **essential_genome** project identified only 15 truly universal single-copy essential families across 48 bacteria [\[31\]](#references).

The **pangenome_pathway_geography** project provides quantitative ecological correlates, linking pangenome openness to niche breadth and metabolic pathway completeness across 1,872 species with complete three-dataset coverage [\[59\]](#references). The **pathway_capability_dependency** project operationalizes the **Black Queen Hypothesis** — the idea that genes encoding shareable metabolic outputs can be lost in some strains if others supply the product — by identifying amino acid biosynthesis pathways as the strongest accessory-dependent pathways, with ~14% of species-level completeness coming from accessory genes [\[60\]](#references) [\[61\]](#references).

Projects on specific gene families illustrate the same architecture at smaller scale. The **snipe_defense_system** project found that the SNIPE anti-phage defense system (DUF4041) spans 1,696 species in 33 phyla but is predominantly accessory (86.7% accessory+singleton), consistent with HGT of defense islands [\[62\]](#references) [\[63\]](#references). The **phb_granule_ecology** project showed PHB (polyhydroxybutyrate) biosynthesis affects 21.9% of species but is phylogenetically concentrated in Pseudomonadota (74.9% of phaC-carrying species), with discordant occurrences showing HGT signatures [\[64\]](#references) [\[65\]](#references). The **plant_microbiome_ecotypes** project established that beneficial plant growth-promoting gene clusters are predominantly core-encoded (64.6% core fraction) while pathogenic clusters are accessory (45.2% core), a striking example of function-specific partitioning [\[66\]](#references).

## Connections

This page connects directly to several adjacent topics. [Gene Fitness](gene-fitness.md) is adjacent because the fitness-conservation gradient is the primary empirical bridge between genome architecture and evolutionary function: fitness data show *why* genes are retained in the core. [Mobile Genetic Elements](mobile-genetic-elements.md) is adjacent because HGT is the primary mechanism populating the accessory genome — novel singleton genes are 10.88% enriched in COG L (mobile elements), and costly dispensable genes are 7.45x enriched in mobile element annotations. [Metabolic Pathways](metabolic-pathways.md) is adjacent because the core genome is functionally defined by metabolic and biosynthetic enrichment, and pathway-level conservation analysis (GapMind, Black Queen) is a major analytical lens. [AMR Resistome](amr-resistome.md) is adjacent because resistance genes are an especially well-studied case of accessory genome content with clear ecological gradients in their core/accessory balance. [Functional Dark Matter](functional-dark-matter.md) is adjacent because novel/singleton genes are disproportionately unannotated (COG S and hypothetical proteins), making pangenome architecture a key driver of how much of the genome remains functionally uncharacterized. [Microbial Ecotypes](microbial-ecotypes.md) is adjacent because within-species metabolic ecotypes — distinct strains with different pathway complements — are directly linked to pangenome openness and accessory gene variation. [Environment Biogeography](environment-biogeography.md) is adjacent because pangenome openness correlates with ecological niche breadth, and the environmental gradient in AMR architecture (soil → clinical) exemplifies how habitat shapes the core/accessory balance. [Microbiome Engineering](microbiome-engineering.md) is adjacent because formulation design exploits the finding that metabolic pathway capabilities are species-level traits: the target pathways in a CF microbiome therapy are 97.4% conserved across 1,796 lung PA genomes [\[67\]](#references), making a single pangenome-aware formulation viable.

The [Adp1 Model System](adp1-model-system.md) is adjacent because the Acinetobacter baylyi ADP1 genome is used as a within-species model for relating transposon fitness measurements to pangenome conservation, and the subsurface genomics topic ([Subsurface Genomics](subsurface-genomics.md)) appears because deep-clay Bacillota_B genomes — which are larger, not smaller, than their soil congeners — show that streamlining is not a universal feature of genome size reduction in environmental bacteria [\[68\]](#references).

## Caveats and Open Directions

Several methodological limitations constrain interpretation. The core/accessory threshold (≥95% prevalence for core) is sensitive to genome count per species: most Fitness Browser species have a median of only 9 genomes, making the threshold imprecise for small-genome-count species [\[69\]](#references). The binary core/auxiliary call discards information about quantitative prevalence that could be recovered with a continuous conservation metric [\[70\]](#references). Gene length confounds both fitness measurement quality and core status (short genes receive fewer transposon insertions; core genes tend to be longer), making gene length a stronger predictor of core status than fitness magnitude in logistic regression [\[71\]](#references) [\[72\]](#references).

The co-inheritance analysis (co-fitness predicting co-occurrence) is limited by a prevalence ceiling: most Fitness Browser genes map to core clusters above 95% prevalence where there is negligible presence/absence variance to detect co-inheritance [\[29\]](#references). The resulting pairwise effect is small, and the strong co-inheritance of accessory modules is partly a mathematical consequence of having more variance in which to detect signal [\[73\]](#references).

The fitness-conservation gradient reported in the synthesis has an internal discrepancy: the prose states essential genes are 82% core and always-neutral 66%, but the figure shows 86% and 78% respectively, because different studies count unmapped genes differently [\[74\]](#references) [\[75\]](#references). These are reporting artifacts, not biological disagreements, but users comparing numbers across projects should be aware of the counting convention.

For pangenome openness specifically, several projects note that genome count per species and phylogenetic non-independence confound openness–ecology correlations [\[76\]](#references) [\[77\]](#references). The correlation between openness and niche breadth should be treated as descriptive until phylogenetic independent contrasts are applied.

A number of projects in this space remain at the proposal or early-execution stage — notably the temporal core dynamics project (which asks whether the core genome changes over sampling time but has not yet produced outputs [\[78\]](#references)) and the openness-functional-composition project (which asks whether COG enrichment scales with openness but has notebooks without outputs [\[79\]](#references)). These are open directions rather than settled findings.

The most important open direction is quantitative: replacing binary core/auxiliary labels with continuous prevalence fractions would substantially increase statistical power for detecting fitness-conservation relationships and co-inheritance signals, and would allow the Black Queen and streamlining hypotheses to be tested at per-gene resolution rather than pathway or genome level.

## References

1. [Resistance Hotspots](../projects/resistance-hotspots.md) — RESEARCH_PLAN.md › "Primary Collections".
2. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — README.md › "Overview".
3. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REPORT.md › "What We Did Not Find".
4. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "Interpretation".
5. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
6. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
7. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
8. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
9. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
10. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Interpretation".
11. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Fitness Distributions by Conservation".
12. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Core Genes Are Not Burdens -- They're More Likely Beneficial".
13. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REPORT.md › "The Gradient".
14. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Interpretation".
15. [Fitness Effects Conservation](../projects/fitness-effects-conservation.md) — REPORT.md › "Breadth of Fitness Effects Predicts Conservation".
16. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Novel Contribution".
17. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Genes Important for Field Conditions Are Significantly More Conserved (NB03)".
18. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Specificity Analysis: Lab-Specific Genes Are Surprisingly More Core".
19. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REPORT.md › "The Paradox".
20. [Core Gene Tradeoffs](../projects/core-gene-tradeoffs.md) — REPORT.md › "The Burden Paradox Is Function-Specific".
21. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REPORT.md › "The Paradox".
22. [Core Gene Tradeoffs](../projects/core-gene-tradeoffs.md) — REPORT.md › "Trade-Off Genes Are Enriched in Core".
23. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REPORT.md › "The Architecture".
24. [Module Conservation](../projects/module-conservation.md) — REPORT.md › "Most Modules Are Core".
25. [Module Conservation](../projects/module-conservation.md) — REPORT.md › "Most Modules Are Core".
26. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Cross-Organism Alignment".
27. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Cross-Organism Alignment".
28. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "ICA Modules Show Co-inheritance, Especially Accessory Modules".
29. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Limitations".
30. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "Only 5% of Ortholog Families Are Universally Essential".
31. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "15 Gene Families Are Essential in All 48 Bacteria".
32. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "Universally Essential Families Are Overwhelmingly Core".
33. [Essential Genome](../projects/essential-genome.md) — REPORT.md › "Variable Essentiality Is the Norm, Not the Exception".
34. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
35. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
36. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "4. Variable Pathways Strongly Correlate with Pangenome Openness".
37. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "6. Metabolic Ecotypes Correlate with Pangenome Openness".
38. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "No Correlation Found".
39. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "No Correlation Found".
40. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "Interpretation".
41. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Costly+Dispensable Genes Are Mobile Genetic Elements".
42. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "They Are Poorly Characterized Recent Acquisitions".
43. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "They Are Poorly Characterized Recent Acquisitions".
44. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Interpretation".
45. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "They Are Poorly Characterized Recent Acquisitions".
46. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Interpretation".
47. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "1. AMR Genes Are Massively Depleted from the Core Genome".
48. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "1. AMR Genes Are Massively Depleted from the Core Genome".
49. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 1: The majority of AMR genes are variable or rare within species".
50. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "2. Clinical species have predominantly acquired resistance; soil/aquatic species have more intrinsic resistance (H2 supported)".
51. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "4. Species with more clinical genomes carry more AMR (H4 proxy — species-level analysis)".
52. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "5. Mechanism is strongly associated with conservation, even though cost is not".
53. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "4. Core and accessory AMR genes have identical fitness costs (H3 not supported)".
54. [Module Conservation](../projects/module-conservation.md) — REPORT.md › "Interpretation".
55. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Novel Contribution".
56. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "The Intrinsic-Acquired Dichotomy".
57. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Novel Contribution".
58. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "7. Highly Conserved Core Metabolism Across 14 Genomes".
59. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
60. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "5. Amino Acid Biosynthesis Pathways Show the Strongest Accessory Dependence".
61. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Accessory Genome as Metabolic Insurance".
62. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "3. SNIPE genes are predominantly accessory (86.7%)".
63. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "2. SNIPE is widespread (1,696 species, 33 phyla)".
64. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 1: PHB pathways are widespread but phylogenetically concentrated".
65. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Phylogenetic Distribution (NB02)".
66. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "2. Beneficial genes are core-encoded; pathogenic genes are accessory (H2)".
67. [Cf Formulation Design](../projects/cf-formulation-design.md) — REPORT.md › "2.13 Formulation Robustness: PA's Amino Acid Core Is Invariant Across Lung Variants".
68. [Bacillota B Subsurface Accessory](../projects/bacillota-b-subsurface-accessory.md) — REPORT.md › "Finding 2 — Deep-clay Bacillota_B genomes are SIGNIFICANTLY LARGER than soil-baseline Bacillota_B, with a 35% mean size difference and ~25% more eggNOG OGs per genome (H2 rejected, opposite direction)".
69. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
70. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Limitations".
71. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Fitness Effects Are Weak Predictors of Core Status".
72. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Limitations".
73. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Interpretation".
74. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REVIEW.md › "Methodology".
75. [Conservation Fitness Synthesis](../projects/conservation-fitness-synthesis.md) — REVIEW.md › "Methodology".
76. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
77. [Openness Functional Composition](../projects/openness-functional-composition.md) — RESEARCH_PLAN.md › "Expected Outcomes".
78. [Temporal Core Dynamics](../projects/temporal-core-dynamics.md) — REVIEW.md › "Summary".
79. [Openness Functional Composition](../projects/openness-functional-composition.md) — README.md › "Status".

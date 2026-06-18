# Kescience Fitnessbrowser

The `kescience_fitnessbrowser` collection is the BERDL-hosted copy of the **Fitness Browser** (fitness.lbl.gov), a compendium of genome-wide gene-fitness measurements produced by the Arkin and Price laboratories at Lawrence Berkeley National Laboratory. The underlying technology is **RB-TnSeq** (randomly barcoded transposon sequencing): a pooled mutant library in which every gene disruption carries a unique DNA barcode, enabling massively parallel competitive growth assays that assign a quantitative fitness score to each gene under each tested condition. The Fitness Browser aggregates these measurements across tens of bacterial and archaeal species, covering thousands of growth conditions — carbon sources, nitrogen sources, stressors, antibiotics, metals, and more. Because this collection ties gene identity to condition-specific phenotype at scale, it serves as a foundational evidence layer for virtually every project in the BERIL research corpus that touches gene function, pangenome conservation, metabolic capability, or antimicrobial resistance. This page explains what the collection contains, how each project in the corpus uses or critiques it, and where its coverage gaps create open research opportunities.

## Overview

The Fitness Browser, as loaded into BERDL, spans **28–48 bacterial and archaeal organisms** depending on the project querying it. [\[1\]](#references) One project treats 48 organisms and finds 228,709 total genes; another focuses on 28 organisms for cofitness network analysis [\[2\]](#references); AMR fitness cost studies use 25 organisms with 27 million fitness measurements [\[3\]](#references). The variation in organism count reflects how different projects drew on the Fitness Browser at different points in time or filtered to organisms with sufficient experimental replication.

Each organism's fitness matrix records a numeric fitness score for each gene under each condition. A score near zero means the gene is dispensable in that environment; a strongly negative score means loss of the gene impairs growth; strongly positive scores indicate the gene suppresses growth when present. These scores are the raw material for three broad analytic strategies used across the corpus: (1) *modules* — grouping genes that co-vary in fitness using independent component analysis; (2) *conservation analysis* — asking whether fitness-important genes tend to be phylogenetically conserved; and (3) *resistance and stress phenotyping* — directly reading off which genes confer tolerance or sensitivity to antibiotics, metals, and other stressors.

The collection is linked to BERDL through the `kescience_fitnessbrowser` identifier. The neighboring [gene-fitness](../topics/gene-fitness.md) topic page collects cross-project findings specifically about what fitness scores reveal about gene function, while [metabolic-pathways](../topics/metabolic-pathways.md) covers how fitness data informs pathway reconstruction.

## Projects Using This Collection

### Fitness Modules (ICA Decomposition)

The **fitness_modules** project applies Robust Independent Component Analysis (rICA) — a blind source separation technique that recovers statistically independent signals from an observed mixture — to each organism's RB-TnSeq matrix from the Fitness Browser [\[4\]](#references). The output is a set of latent modules, each a weighted list of genes whose fitness scores rise and fall together across conditions, capturing co-regulatory programs that sequence similarity alone would miss. Across 32 organisms with at least 100 experiments each, the analysis yielded **1,116 stable modules** [\[5\]](#references), organized into **156 cross-organism families** that align via orthology, including one family spanning 21 species — evidence for a deeply conserved pan-bacterial regulatory program [\[6\]](#references). Within-module cofitness is 2.8× higher than background (mean |r| = 0.34 vs 0.12) [\[7\]](#references), and modules are enriched in genomically adjacent gene pairs, consistent with operon structure. Crucially, module membership was used to generate **6,691 function predictions** for hypothetical proteins [\[8\]](#references), of which 2,455 are supported by cross-organism conservation. A practical caveat: modules derived from organisms with fewer than ~100 experiments tend to be weaker and less interpretable [\[9\]](#references), and ICA captures process-level co-regulation rather than physical molecular interactions [\[10\]](#references).

### AMR Fitness Cost (Pan-Bacterial Meta-Analysis)

The **amr_fitness_cost** project performed the first pan-bacterial meta-analysis of antimicrobial resistance (AMR) gene fitness costs, drawing on 27 million Fitness Browser measurements across 25 organisms [\[3\]](#references). AMR genes carry a real but small fitness cost (mean ~+0.086 in the absence of antibiotics) — small enough to explain why resistance persists long after antibiotics are withdrawn [\[11\]](#references), and uniform enough across resistance mechanisms (efflux pumps, enzymatic inactivation, target modification) to suggest an irreducible metabolic overhead floor [\[12\]](#references). Under antibiotic challenge, 57% of AMR genes undergo a fitness **flip** — becoming relatively beneficial — and broad-spectrum efflux genes flip more strongly than narrow-spectrum enzymatic genes [\[13\]](#references) [\[14\]](#references). Two important caveats limit interpretation: all 25 organisms are lab-adapted strains, so compensatory evolution during laboratory maintenance may have reduced measurable costs compared to wild strains [\[15\]](#references); and approximately 4.6% of AMR genes are putatively essential and therefore absent from fitness matrices entirely, meaning the cost estimate is a lower bound [\[16\]](#references). Resistance mechanism strongly predicts pangenome conservation: metal resistance genes are 44% accessory while efflux and enzymatic genes are overwhelmingly core [\[17\]](#references). The 144 metal resistance genes with fitness data have been flagged for cross-referencing with the metal fitness atlas to ask whether genes costly under standard conditions confer protection under metal stress [\[18\]](#references).

### AMR Pangenome Atlas

The **amr_pangenome_atlas** project overlays AMR gene presence/absence with Fitness Browser fitness measurements across 37 organisms to quantify the relationship between AMR content and fitness burden. The result is that AMR genes impose *slightly less* fitness cost than the non-AMR baseline in standard lab conditions (median fitness −0.007 vs −0.012) [\[19\]](#references), and AMR genes are markedly depleted from the core genome (30.3% core vs 46.8% baseline, OR = 0.49) [\[20\]](#references) — a pattern consistent across 63.7% of 4,252 tested species [\[21\]](#references). A sampling-bias caveat applies: genome databases over-represent clinical pathogens, inflating AMR counts for human-associated species and confounding clinical-versus-environmental comparisons [\[22\]](#references).

### AMR Cofitness Networks

The **amr_cofitness_networks** project extends Fitness Browser data to ask which cellular programs AMR genes co-vary with. It performed the first pan-bacterial mapping of AMR cofitness neighborhoods across 28 organisms [\[23\]](#references). Only 24% of AMR genes fall into ICA fitness modules, but those modules are significantly larger than non-AMR modules (median 46 vs 27 genes) [\[24\]](#references), and nearly all AMR gene-module assignments belong to conserved cross-organism families, indicating ancient co-regulatory relationships [\[25\]](#references). A methodological note: this project found that switching from legacy SEED/KEGG annotations to InterProScan GO annotations on the same data turned a null enrichment result into a significant one [\[26\]](#references), underscoring that cofitness analyses require uniformly computed, high-coverage functional annotations [\[27\]](#references). The organism bias of the Fitness Browser — predominantly Pseudomonas, all lab-adapted — constrains generalizability [\[2\]](#references), and an enrichment of flagellar and biosynthesis genes in AMR support networks may reflect shared dispensability under lab conditions rather than genuine mechanistic coupling [\[28\]](#references).

### Cofitness and Co-inheritance

The **cofitness_coinheritance** project tests whether gene pairs that co-vary in fitness also tend to co-occur across pangenomes. Across nine Fitness Browser organisms, co-fit gene pairs show a weak but consistent positive co-occurrence signal [\[29\]](#references). A nuance: stronger cofitness weakly predicts *lower* co-occurrence because the strongest co-fit pairs are near-universal core genes with little presence/absence variance for co-occurrence detection [\[30\]](#references). ICA-derived multi-gene modules show substantially stronger co-inheritance than pairwise co-fitness scores, with 195 modules across six organisms exceeding null expectations [\[31\]](#references), and accessory modules show the strongest co-inheritance signal (mean delta phi = +0.108) [\[32\]](#references). A prevalence ceiling limits the analysis because most Fitness Browser genes map to core clusters where co-occurrence variance is nearly zero [\[33\]](#references).

### Functional Dark Matter

The **functional_dark_matter** project directly exploits the Fitness Browser to prioritize dark genes — genes with no functional annotation — for experimental follow-up. Across 48 Fitness Browser organisms, 57,011 genes (24.9%) lack functional annotation, and 17,344 of these have experimentally measurable phenotypes (strong fitness effects or essentiality), defining actionable bacterial dark matter [\[1\]](#references). Of those 57,011 dark genes, 6,142 belong to ICA fitness modules, enabling guilt-by-association function predictions [\[34\]](#references). Lab fitness phenotypes predict field environmental distribution for 61.7% of testable dark gene clusters [\[35\]](#references). A caveat: the Fitness Browser corpus is dominated by Proteobacteria [\[36\]](#references), and reannotation with Bakta v1.12 may overestimate remaining darkness by conflating partial functional labels with true unknowns [\[37\]](#references).

### Field vs Lab Fitness

The **field_vs_lab_fitness** project asks whether fitness importance in ecologically realistic conditions (field conditions) predicts pangenome conservation differently from importance in artificial lab conditions. Using 757 RB-TnSeq experiments for *Desulfovibrio vulgaris* Hildenborough from the Fitness Browser, conditions were classified into six ecological-relevance categories yielding a 44.5% field / 55.5% lab split [\[38\]](#references). The dominant result: any fitness importance, regardless of condition type, predicts conservation (OR = 1.35, p = 0.033) [\[39\]](#references), with field-stress genes the most conserved at 83.6% core [\[40\]](#references). Counter-intuitively, genes with fitness defects only under lab conditions are 96.0% core [\[41\]](#references). The 21 conserved "ecological" ICA modules contain 52 unannotated genes that are candidates for novel environmental adaptation functions [\[42\]](#references). Caveats: the analysis covers only a single organism (DvH) with a coarse pangenome proxy [\[43\]](#references), and gene length confounds conservation scores because longer genes are inherently more likely to register fitness effects [\[44\]](#references).

### Genotype-to-Phenotype Enigma

The **genotype_to_phenotype_enigma** project uses Fitness Browser data as one of three anchor datasets — alongside ENIGMA growth curves and genome annotations — to train models predicting binary growth phenotypes from gene content [\[45\]](#references). With 46,000 training pairs the SHAP analysis correctly surfaces condition-specific catabolic genes such as ribose transporters and protocatechuate-pathway enzymes [\[46\]](#references). Binary growth is predictable from gene content on amino acids (AUC 0.775) and nucleosides (0.780) but not metals, antibiotics, or most nitrogen sources [\[47\]](#references). A notable caveat: top SHAP KOs show only 1.19× enrichment for significant Fitness Browser effects, reflecting that gene presence across genera and gene essentiality within a single strain are fundamentally different biological questions [\[48\]](#references).

### FW300 Metabolic Consistency

The **fw300_metabolic_consistency** project was the first to systematically compare Web of Microbes exometabolomic profiles with Fitness Browser gene fitness data, despite both coming from the same ENIGMA/Arkin Lab research program [\[49\]](#references). For *Pseudomonas* FW300-N2E3, 19 metabolites the organism produces in WoM also appear as tested conditions in the Fitness Browser [\[50\]](#references), and all 13 GapMind-matched metabolites had complete predicted pathways and showed growth in Fitness Browser experiments [\[51\]](#references). Across 21 produced metabolites with matching Fitness Browser experiments, the organism showed significant fitness effects for 601 unique genes and 4,764 total gene-condition hits [\[52\]](#references). A critical methodological caveat: WoM exometabolomics was measured on rich R2A medium while Fitness Browser fitness used minimal single C/N-source media, so condition-dependent profiles mean some WoM metabolites may only be produced on rich media [\[53\]](#references).

### Acinetobacter ADP1 Explorer

*Acinetobacter baylyi* ADP1 is **absent from the Fitness Browser**, making the condition-specific mutant growth data in the ADP1 BERDL database a unique fitness resource not available elsewhere in the lakehouse [\[54\]](#references). FBA flux predictions and TnSeq essentiality calls agreed for 73.8% of the 866 ADP1 genes with both measurements [\[55\]](#references). This gap is relevant to the [adp1-model-system](../topics/adp1-model-system.md) topic, where ADP1 serves as a tractable genetic model — its absence from the Fitness Browser means cross-species comparisons that rely on that collection cannot include ADP1 without supplementary data.

### Counter Ion Effects

The **counter_ion_effects** project uses Fitness Browser metal fitness data for *Desulfovibrio vulgaris* Hildenborough to disentangle whether osmotic/ionic stress from counter-ions (e.g., Cl⁻ delivered with metal salts) confounds metal-specific phenotypes. The key finding is that counter-ions are not the driver: zinc sulfate (zero chloride) shows higher NaCl overlap than most chloride-delivered metals [\[56\]](#references). Across 19 organisms and 14 metals, 39.8% of metal-important gene fitness records are also important under NaCl stress [\[57\]](#references), while iron stands apart with low NaCl correlation because it affects specific Fe-dependent enzymes rather than causing general cellular damage [\[58\]](#references).

### Metal Fitness Atlas

The **metal_fitness_atlas** project mines Fitness Browser fitness data across organisms and metals to build an atlas of conserved metal-phenotype gene families. Cross-species metal fitness defects are enriched in core genes, reframing metal tolerance as a core-genome robustness problem rather than an accessory-resistance problem [\[59\]](#references). The atlas identifies conserved gene families including novel candidates prioritized from cross-species evidence [\[60\]](#references). This is directly adjacent to the [metal-resistance](../topics/metal-resistance.md) topic.

### PaperBLAST Explorer

The **paperblast_explorer** project links the Fitness Browser to PaperBLAST via 129,823 VIMSS cross-references, creating a path from literature coverage to experimental fitness phenotypes [\[61\]](#references). This enables identification of genes that are understudied in the literature but show strong fitness phenotypes — the most actionable targets for experimental characterization [\[62\]](#references).

### Other Projects

Several other projects use the Fitness Browser more indirectly. **pathway_capability_dependency** applies Fitness Browser fitness data to validate metabolic capability classifications, though the Tier 1 validation rests on only 7 of 48 organisms with GapMind data, all well-annotated model organisms [\[63\]](#references). **pseudomonas_carbon_ecology** identifies cross-referencing carbon pathway predictions with RB-TnSeq fitness data as an opportunity to experimentally validate which pathways are functionally important in specific carbon sources [\[64\]](#references). **webofmicrobes_explorer** notes that two WoM *Pseudomonas* ENIGMA isolates map directly to Fitness Browser strains, each with over 5,000 genes and more than 100 fitness experiments [\[65\]](#references). **bacdive_phenotype_metal_tolerance** matched twelve Fitness Browser organisms to BacDive phenotype records, finding that all urease-negative organisms are routinely tested against nickel, concordant with pangenome-scale findings [\[66\]](#references).

## Connections

The kescience_fitnessbrowser data collection sits at the hub of several related topic pages in this wiki. The [gene-fitness](../topics/gene-fitness.md) topic page aggregates findings about what fitness scores reveal about gene importance and conservation. [functional-dark-matter](../topics/functional-dark-matter.md) is adjacent because the Fitness Browser provides the primary experimental signal for prioritizing uncharacterized genes: a dark gene with a strong fitness phenotype is immediately actionable. [pangenome-architecture](../topics/pangenome-architecture.md) is adjacent because multiple projects use Fitness Browser fitness importance as a lens on core/accessory genome structure — fitness-important genes tend to be core, and this pattern is exploited by cofitness_coinheritance, field_vs_lab_fitness, and functional_dark_matter. [metabolic-pathways](../topics/metabolic-pathways.md) is adjacent because GapMind pathway predictions, FBA models, and Fitness Browser fitness data are jointly used to resolve annotation gaps and validate metabolic capability. [amr-resistome](../topics/amr-resistome.md) is adjacent because amr_fitness_cost and amr_pangenome_atlas both use the Fitness Browser as their primary source of resistance gene fitness measurements. [metal-resistance](../topics/metal-resistance.md) is adjacent because metal_fitness_atlas and counter_ion_effects are entirely built on Fitness Browser metal fitness data. [microbial-ecotypes](../topics/microbial-ecotypes.md) is adjacent because the field_vs_lab_fitness project uses Fitness Browser condition classification to ask whether field-relevant fitness importance predicts ecotype-level conservation.

## Caveats and Open Directions

Several structural limitations of the Fitness Browser collection propagate across multiple projects in the corpus and deserve explicit acknowledgment.

**Phylogenetic bias.** The Fitness Browser is heavily biased toward Proteobacteria, especially Pseudomonas [\[2\]](#references) [\[36\]](#references). The sole Bacteroidetes organism (B. thetaiotaomicron) showed the lowest functional resolution rate in annotation_gap_discovery [\[67\]](#references), suggesting that findings derived from the collection may transfer poorly to Bacteroidota, Firmicutes, and other ecologically important phyla.

**Lab adaptation.** All Fitness Browser organisms are lab-adapted strains [\[15\]](#references). Compensatory evolution during laboratory maintenance may have eroded measurable fitness costs — whether for AMR genes [\[15\]](#references) or for any conditionally important gene. The field_vs_lab_fitness project finds that lab-specific fitness importance predicts core-genome status comparably to field importance, but this comparison is itself limited to a single organism [\[43\]](#references).

**Sparse pangenome representation.** Most Fitness Browser organisms were profiled from a small number of sequenced genomes (median ~9 per species), making core/accessory distinctions imprecise, particularly for AMR gene classification [\[68\]](#references). The prevalence ceiling — most Fitness Browser genes map to core clusters with near-zero presence/absence variance — limits cofitness-to-co-inheritance analyses [\[33\]](#references).

**Media mismatch.** Fitness Browser experiments use minimal single carbon or nitrogen source media, while companion datasets such as Web of Microbes use rich R2A medium. This mismatch means that metabolite production observed in WoM may not correspond to the condition tested in the Fitness Browser [\[53\]](#references).

**ADP1 gap.** *Acinetobacter baylyi* ADP1 — a well-characterized genetic model with extensive BERDL multi-omic data — is absent from the Fitness Browser entirely [\[54\]](#references), creating a blind spot for projects that rely on cross-referencing ADP1 fitness to other organisms.

**Open directions** emerging from the corpus include: integrating Fitness Browser module predictions with pangenome gene classifications to reveal which fitness modules are enriched in accessory genes [\[69\]](#references); using RB-TnSeq profiling of matched urease-positive and urease-negative strains under nickel to directly test urease-mediated nickel tolerance [\[70\]](#references); expanding the fitness-conservation analysis to quantitative conservation metrics and additional organisms [\[71\]](#references); and validating carbon pathway predictions with existing Fitness Browser RB-TnSeq data for Pseudomonas [\[64\]](#references).

## References

1. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 1: One in four bacterial genes is functionally dark, and 17,344 have experimentally measurable phenotypes".
2. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Limitations".
3. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Novel Contribution".
4. [Fitness Modules](../projects/fitness-modules.md) — README.md › "Overview".
5. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "ICA Decomposition (32 organisms)".
6. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Cross-Organism Alignment".
7. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "ICA Decomposition (32 organisms)".
8. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Function Prediction".
9. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Limitations".
10. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Benchmarking (NB07)".
11. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "The cost of resistance is universal but uniform".
12. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "3. Resistance mechanism does not predict fitness cost (H2 not supported)".
13. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "2. AMR genes become more important under antibiotic pressure (H4 partially supported)".
14. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "2. AMR genes become more important under antibiotic pressure (H4 partially supported)".
15. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
16. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
17. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "5. Mechanism is strongly associated with conservation, even though cost is not".
18. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Future Directions".
19. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "6. AMR Genes Are Not a Fitness Burden in Lab Conditions".
20. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "1. AMR Genes Are Massively Depleted from the Core Genome".
21. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "1. AMR Genes Are Massively Depleted from the Core Genome".
22. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "Limitations".
23. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Novel Contribution".
24. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "1. AMR genes are embedded in larger-than-average co-regulated modules".
25. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "1. AMR genes are embedded in larger-than-average co-regulated modules".
26. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "5. Annotation quality is critical: InterProScan reveals what SEED/KEGG missed".
27. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "5. Annotation quality is critical: InterProScan reveals what SEED/KEGG missed".
28. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "2. AMR support networks are enriched for flagellar motility and amino acid biosynthesis (H1 supported)".
29. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Pairwise Co-fitness Weakly Predicts Co-occurrence".
30. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Co-fitness Strength Weakly Anti-correlates with Co-occurrence".
31. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "ICA Modules Show Co-inheritance, Especially Accessory Modules".
32. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "ICA Modules Show Co-inheritance, Especially Accessory Modules".
33. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Limitations".
34. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 2: 39,532 dark genes link to the pangenome; 6,142 belong to co-regulated fitness modules".
35. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 7: Lab-field concordance rate of 61.7%, with NMDC validation confirming 4/4 pre-registered abiotic predictions".
36. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 10: Phylogenetic gaps — which new organisms would most expand dark gene coverage?".
37. [Functional Dark Matter](../projects/functional-dark-matter.md) — REPORT.md › "Finding 15: Bakta reannotation reclassifies 83.7% of linked dark genes — all 100 top candidates gain functional descriptions".
38. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Condition Classification (NB02)".
39. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Specificity Analysis: Lab-Specific Genes Are Surprisingly More Core".
40. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Genes Important for Field Conditions Are Significantly More Conserved (NB03)".
41. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Specificity Analysis: Lab-Specific Genes Are Surprisingly More Core".
42. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Module-Level Conservation Shows No Field-Lab Difference (NB04)".
43. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Limitations".
44. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Limitations".
45. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Key Findings".
46. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — README.md › "Key Lessons Learned".
47. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Executive Summary".
48. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Act II — Predict and Explain".
49. [Fw300 Metabolic Consistency](../projects/fw300-metabolic-consistency.md) — REPORT.md › "Literature Context".
50. [Webofmicrobes Explorer](../projects/webofmicrobes-explorer.md) — REPORT.md › "3. 19 WoM-Produced Metabolites Are Tested as FB Carbon/Nitrogen Sources".
51. [Fw300 Metabolic Consistency](../projects/fw300-metabolic-consistency.md) — REPORT.md › "3. All 13 GapMind-matched metabolites have complete pathways".
52. [Fw300 Metabolic Consistency](../projects/fw300-metabolic-consistency.md) — REPORT.md › "4. Rich fitness landscapes for produced metabolites".
53. [Fw300 Metabolic Consistency](../projects/fw300-metabolic-consistency.md) — REPORT.md › "Limitations".
54. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "2. Strong BERDL Connectivity: 4 of 5 Connection Types at >90% Match".
55. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "4. FBA and TnSeq Essentiality Agree 74% of the Time".
56. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "2. Counter Ions Are NOT the Primary Driver of the Overlap".
57. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "1. 39.8% of Metal-Important Genes Are Also NaCl-Important".
58. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "A Metal Toxicity Hierarchy Emerges".
59. [Metal Fitness Atlas](../projects/metal-fitness-atlas.md) — REPORT.md › "Metal-Important Genes Are Enriched in the Core Genome".
60. [Metal Fitness Atlas](../projects/metal-fitness-atlas.md) — REPORT.md › "1,182 Conserved Metal Gene Families Identified".
61. [Paperblast Explorer](../projects/paperblast-explorer.md) — REPORT.md › "Novel Contribution".
62. [Paperblast Explorer](../projects/paperblast-explorer.md) — REPORT.md › "Future Directions".
63. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Limitations".
64. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Future Directions".
65. [Webofmicrobes Explorer](../projects/webofmicrobes-explorer.md) — REPORT.md › "2. Two Direct Fitness Browser Strain Matches Plus Two Genus-Level Matches".
66. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "Direct FB-BacDive Validation (n = 12)".
67. [Annotation Gap Discovery](../projects/annotation-gap-discovery.md) — REPORT.md › "Limitations".
68. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
69. [Fitness Modules](../projects/fitness-modules.md) — REPORT.md › "Future Directions".
70. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "Suggested Experiments".
71. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Future Directions".

# Mobile Genetic Elements

Mobile genetic elements (MGEs) are DNA sequences that can move within or between genomes — a category that includes insertion sequences (IS elements), transposons, plasmids, bacteriophages and their remnants (prophages), and integrative conjugative elements (ICEs). They are the engines of bacterial horizontal gene transfer (HGT), the process by which a bacterium acquires genes from an unrelated lineage rather than inheriting them from its parent. This page exists in the wiki because MGE activity cuts across nearly every project in the corpus: it shapes the resistome, remodels pangenome architecture, drives functional innovation, and determines which defense systems spread. Understanding MGEs is therefore a prerequisite for interpreting nearly every other topic covered here.

## Overview

The distinction between the core genome (genes present in all or nearly all strains of a species) and the accessory genome (genes found in only some strains) maps almost exactly onto a functional division between vertical inheritance and horizontal acquisition. Across 32 species spanning 9 bacterial phyla, novel and singleton genes are enriched in mobile-element functions (COG category L) at +10.88% with 100% consistency, and in defense functions (COG V) at +2.83% with 100% consistency [\[1\]](#references) [\[2\]](#references). Core genes by contrast are enriched in translation, energy production, and biosynthesis — the conserved metabolic engine that sustains the cell. This "two-speed genome" pattern is not a phylum-specific quirk; it holds across the bacterial tree and represents what the corpus authors call a fundamental organizing principle [\[3\]](#references).

The genomic debris of this process is directly measurable. A set of 5,526 genes that are simultaneously costly (negative fitness effect when disrupted) and dispensable (not conserved across the pangenome) are 7.45-fold more likely to carry mobile-element keywords and 11.7-fold enriched in the SEED Phages/Prophages/Transposable-elements/Plasmids category, compared to costly-but-conserved genes [\[4\]](#references). These genes are shorter (median 615 bp vs 765 bp for conserved counterparts) [\[5\]](#references), poorly annotated, and taxonomically restricted — the morphological fingerprint of insertion sequences and prophage fragments that impose a metabolic cost but have not yet been purged [\[6\]](#references). In one striking example, *Pseudomonas stutzeri* RCH2 contributes 21.5% of its genes to this costly-dispensable category, far above any other organism in the set, suggesting a recent mobile-element invasion specific to that strain [\[7\]](#references).

## What the Corpus Shows

### HGT is pervasive but opportunistic

A key null result shapes interpretation across several projects: pangenome openness (the fraction of a species' gene complement that is accessory rather than core) does not predict whether environmental or phylogenetic signals dominate gene-content variation [\[8\]](#references). Species with open pangenomes do not preferentially adapt to their local environment through gene acquisition. The implication is that HGT may be fundamentally opportunistic — capturing available genes rather than tracking environmental similarity [\[9\]](#references). A parallel analysis found that between-species gain attribution and within-species pangenome openness are uncorrelated (Spearman r = -0.011 across 894 genera), confirming these are independent evolutionary signals [\[10\]](#references).

This opportunistic framing is consistent with the literature cited across projects, including McInerney et al. (2017), and is reinforced by the finding that open pangenomes are simply hypothesized to reflect generalist species with broader niche breadth and greater metabolic flexibility [\[11\]](#references) — but that correlation is itself an unexecuted hypothesis, pending analysis on BERDL [\[12\]](#references).

### Prophages are universal and modularly organized

All 27,702 species in the BERDL pangenome carry prophage-associated gene clusters. Prophage gene organization follows a two-tier architecture: a core backbone of packaging (module A), lysis (D), and lysogenic regulation (F) modules that are near-universal (99–100% prevalence), plus structurally variable modules — head morphogenesis (B, 56.1%), tail (C, 55.6%), and anti-defense (G, 64.3%) — that carry the most environmental and phylogenetic signal [\[13\]](#references). The universal modules likely include many domesticated prophage remnants under purifying selection, making the variable modules more informative for ecology [\[14\]](#references).

Environment explains more variance in prophage module composition than host phylogeny (PERMANOVA F = 30.04 for environment vs 6.17 for phylogeny). Notably, anti-defense modules are enriched in human-associated bacteria and depleted in freshwater and animal-associated environments, suggesting that the coevolutionary arms race between phages and bacterial immune systems (CRISPR-Cas, restriction-modification) is most intense in the human niche [\[15\]](#references). Cross-validation in NMDC metagenomes confirms that prophage burden correlates positively with pH and temperature, consistent with pH-sensitive stress-induced induction [\[16\]](#references).

### Prophages and AMR are co-mobilized

Prophage density is a powerful species-level predictor of antibiotic resistance (AMR) breadth: Spearman rho = 0.572 (p < 10^-300) between prophage density and AMR breadth across 4,770 species, persisting after controlling for genome count [\[17\]](#references). This extends earlier work (Rendueles et al. 2018, ~100 pangenomes) to much larger scale [\[18\]](#references). Two non-exclusive mechanisms are consistent with the data: prophages directly mobilize resistance genes via specialized or generalized transduction, or species with high recombination potential independently accumulate both prophages and AMR genes [\[19\]](#references). AMR genes themselves are statistically biased toward the accessory genome near prophage regions, though the gene-level co-localization effect is modest (2.1 percentage point difference in accessory fraction) and reverses at very close range (fewer than 5 genes), where immediate neighbors are core phage structural genes rather than cargo [\[20\]](#references).

### AMR elements: a conservation dichotomy

Across the broader resistome, MGE activity creates a sharp dichotomy between intrinsic and acquired resistance. Beta-lactamases are 54.9% core — chromosomally encoded ancestral genes present in most strains — while known mobile elements such as blaTEM, tet(C), and ant(2'')-Ia are 0% core (fully accessory or singleton) [\[21\]](#references). At ecosystem scale, clinical and human gut species have overwhelmingly acquired their AMR through HGT, while soil and aquatic species retain ancient chromosomally encoded intrinsic resistance [\[22\]](#references). *Klebsiella pneumoniae* exemplifies the extreme: 1,115 AMR gene clusters, only 7 of which are core, leaving nearly the entire resistome as accessory [\[23\]](#references).

AMR genes are further organized into 1,517 tightly co-inherited resistance islands across 54% of analyzed species, with a mean phi coefficient of 0.827 indicating very strong within-island co-occurrence [\[24\]](#references). Most islands (88%) combine multiple resistance mechanisms, dominated by efflux pumps and enzymatic inactivation [\[25\]](#references). Counterintuitively, non-core (acquired) AMR genes show stronger phylogenetic signal than intrinsic ones (median Mantel r = 0.222 vs 0.117), suggesting acquired elements are stably vertically transmitted within lineages once fixed — making clonal lineage tracking potentially more informative for surveillance than tracking individual genes [\[26\]](#references) [\[27\]](#references).

The absence of a fitness-cost difference between core and accessory AMR genes suggests that HGT preferentially captures genes already cost-optimized in their donor lineage, or that receiving genomes rapidly compensate [\[28\]](#references).

### Conjugative transfer and CAZy mobility

A separate window onto HGT comes from the co-occurrence of type IV secretion systems (T4SS) — the molecular machinery of bacterial conjugation — with carbohydrate-active enzyme (CAZy) cassettes in environmental metagenome-assembled genomes (MAGs). T4SS are found in 21.8% of environmental MAGs surveyed, while metal resistance genes occur in only 2.8%, confirming that the two features are not uniformly co-distributed [\[29\]](#references). Where T4SS and GT2-family glycosyltransferases co-occur in synteny, phylogenetic incongruence analysis detects 32 cross-phylum HGT events, including a single ancestral node (Node_4915) that spans eight bacterial phyla at a phylogenetic divergence of 4.843 [\[30\]](#references). These events are enriched in marine and rhizosphere biomes [\[31\]](#references) and are mechanistically distinct from the Polysaccharide Utilization Locus (PUL) paradigm used by Bacteroidetes, which relies on TonB-dependent transporters instead [\[32\]](#references).

Crucially, ICEfinder finds no plasmid-borne CAZy genes, and T4SS-positive genomes carry 10-fold higher overall MGE density, pointing toward chromosomal integrative mechanisms (IMEs/ICEs) rather than plasmid mobilization [\[33\]](#references).

### SNIPE: a mobile defense system

SNIPE (a two-component defense system encoded by the DUF4041 protein paired with a nuclease domain) provides a concrete example of a defense island that moves horizontally. It is found in 1,696 species across 33 phyla — more than the original publication reported — and 86.7% of SNIPE gene clusters are accessory or singleton, consistent with defense island carriage on MGEs [\[34\]](#references). The patchy phylogenetic distribution, spanning distant phyla within individual families, is consistent with HGT [\[35\]](#references). Fitness experiments in *Methanococcus maripaludis* confirm that SNIPE provides a positive fitness benefit against phage, resolving the ManYZ transporter trade-off by providing phage defense without sacrificing the transporter function [\[36\]](#references). In *Klebsiella* in particular, SNIPE presence is relevant for phage therapy resistance prediction [\[37\]](#references).

The SNIPE nuclease domain is PF13455 (Mug113, GIY-YIG clan), not the commonly annotated PF01541, a domain-level disambiguation that matters for detection sensitivity [\[38\]](#references).

### Dark genes and MGE neighborhoods

Truly dark genes — genes with no functional annotation across all databases — cluster physically near mobile elements. In ICA-mapped organisms, 12% of truly dark genes are within two genes of a mobile element, and 41% of neighboring genes are themselves hypothetical, forming contiguous "dark islands" that likely represent recently acquired genomic islands or phage-derived regions [\[39\]](#references). The accessory-genome enrichment of dark genes, combined with GC-content deviation and proximity to MGEs, signals recent acquisition rather than ancient annotation gap [\[40\]](#references).

## Projects and Evidence

The evidence base is distributed across nearly 30 projects:

**Prophage ecology and AMR co-mobilization** ([`prophage_ecology`](../projects/prophage-ecology.md), [`prophage_amr_comobilization`](../projects/prophage-amr-comobilization.md)): Large-scale pangenome analyses of prophage gene modules across 27,702 species (prophage_ecology) and prophage-AMR co-occurrence across 4,770 species (prophage_amr_comobilization), both using BERDL genomes and KBase pangenomes.

**AMR pangenome atlas and strain variation** ([`amr_pangenome_atlas`](../projects/amr-pangenome-atlas.md), [`amr_strain_variation`](../projects/amr-strain-variation.md), [`amr_environmental_resistome`](../projects/amr-environmental-resistome.md), [`amr_fitness_cost`](../projects/amr-fitness-cost.md)): Atlas-level characterization of how intrinsic vs acquired AMR genes partition into core and accessory genomes, resistance island co-inheritance patterns, and fitness costs of acquired elements.

**Costly dispensable genes** ([`costly_dispensable_genes`](../projects/costly-dispensable-genes.md)): Direct measurement of fitness cost versus conservation status across FitnessBrowser organisms, showing the metabolic burden carried by MGE debris.

**T4SS-CAZy environmental HGT** ([`t4ss_cazy_environmental_hgt`](../projects/t4ss-cazy-environmental-hgt.md)): Environmental MAG-based study of conjugative machinery co-occurrence with carbohydrate enzyme diversity, including cross-phylum phylogenetic incongruence analysis.

**SNIPE defense system** ([`snipe_defense_system`](../projects/snipe-defense-system.md)): Characterization of a horizontally distributed two-component defense island in 1,696 species.

**HGT functional atlas** ([`gene_function_ecological_agora`](../projects/gene-function-ecological-agora.md)): Cross-genus producer-participation framework for classifying whether gene families are Innovator-Isolated, Innovator-Exchange, or Stable, based on phylogenetic gain/loss inference at GTDB scale. The framework also reveals that architectural promiscuity (number of distinct Pfam domain architectures per KO) correlates with HGT propensity (r = 0.67) [\[41\]](#references).

**Pangenome openness and functional composition** ([`pangenome_openness`](../projects/pangenome-openness.md), [`openness_functional_composition`](../projects/openness-functional-composition.md), [`cog_analysis`](../projects/cog-analysis.md)): Tests of whether open pangenomes specifically accumulate mobile and defense functions in their novel genes, and whether pangenome openness predicts ecological drivers.

**Module conservation and co-inheritance** ([`module_conservation`](../projects/module-conservation.md), [`cofitness_coinheritance`](../projects/cofitness-coinheritance.md)): ICA-based module detection showing that accessory modules co-inherit as functional units — an operonic control confirms that genomic adjacency explains less than 1% of the cofitness signal [\[42\]](#references).

**phaC and PHB granule ecology** ([`phb_granule_ecology`](../projects/phb-granule-ecology.md)): The polyhydroxyalkanoate synthase gene phaC shows discordant presence in 311 species at nearly double the baseline accessory rate (60.1% vs 32.3%), marking likely recent horizontal acquisitions [\[43\]](#references).

**Plant microbiome ecotypes** ([`plant_microbiome_ecotypes`](../projects/plant-microbiome-ecotypes.md)): Mobilome enrichment shows pathogenic clusters co-occur with transposase/integrase singletons at 16-fold excess (OR = 15.95, p = 8.8e-20) [\[44\]](#references), though plant-interaction markers as a class are less mobile than the genomic average, suggesting purifying selection dominates once these genes are acquired [\[45\]](#references).

**IBD phage targeting** ([`ibd_phage_targeting`](../projects/ibd-phage-targeting.md)): Phage-therapy design for Crohn's disease pathobionts, where the mobility of prophages is directly relevant to whether phage-derived tools can work against specific targets. The two highest-priority targets (*H. hathewayi*, *M. gnavus*) face the worst phage coverage [\[46\]](#references), motivating hybrid cocktail designs [\[47\]](#references).

## Connections

Mobile genetic elements are the mechanism through which most other topics in this wiki interact. The [AMR Resistome](../topics/amr-resistome.md) page documents the downstream outcomes of MGE-mediated gene acquisition in resistance genes; the intrinsic/acquired dichotomy described there is mechanistically grounded in MGE biology. The [Pangenome Architecture](../topics/pangenome-architecture.md) page covers the structural consequence of MGE activity — namely, the open/closed pangenome axis and the core/accessory split — which are the genomic signatures that MGE insertion and loss create over evolutionary time.

The [Functional Dark Matter](../topics/functional-dark-matter.md) page is adjacent because dark genes cluster in MGE neighborhoods (dark islands), and synteny-based co-fitness validation helps distinguish truly novel MGE-associated genes from annotation gaps. [Gene Fitness](../topics/gene-fitness.md) connects because the fitness cost of costly-dispensable MGE debris is the measurement that defines the "burden" these elements impose on hosts. [Metabolic Pathways](../topics/metabolic-pathways.md) connects through the T4SS-CAZy story, where HGT distributes carbohydrate-active enzyme diversity that expands metabolic repertoire. [Metal Resistance](../topics/metal-resistance.md) is adjacent because metal resistance genes are disproportionately accessory (71.2% core, below baseline) and AMRFinderPlus-based metal resistance prevalence (2.8%) is far below T4SS prevalence (21.8%), confirming these features are independent. [Microbiome Engineering](../topics/microbiome-engineering.md) intersects because prophage and phage ecology directly determine whether phage therapy strategies can target pathobionts.

The [Environment Biogeography](../topics/environment-biogeography.md) page is adjacent because prophage module composition and HGT event rates are environment-stratified (marine and rhizosphere environments are enriched for T4SS-CAZy HGT; human-associated environments are enriched for anti-defense prophage modules). [Subsurface Genomics](../topics/subsurface-genomics.md) and [Microbial Ecotypes](../topics/microbial-ecotypes.md) are adjacent because mobilome enrichment at the genus level and ecotype-specific AMR profiles both reflect the population-level consequences of MGE dynamics.

## Caveats and Open Directions

Several methodological limitations run across the MGE-related projects:

**Detection sensitivity.** Prophages in two major projects ([`prophage_ecology`](../projects/prophage-ecology.md), [`prophage_amr_comobilization`](../projects/prophage-amr-comobilization.md)) were identified by keyword and Pfam matching on bakta or eggNOG annotations rather than dedicated tools such as geNomad or VIBRANT [\[48\]](#references) [\[49\]](#references). This likely inflates prophage prevalence by including domesticated remnants and bacterial homologs of phage genes, with an uncharacterized false positive rate. The SNIPE detection is similarly limited, with only 54 of 4,572 DUF4041 clusters showing PF13455 co-annotation, likely missing divergent homologs [\[50\]](#references).

**Causality vs association.** The T4SS-CAZy project makes an explicitly associative claim; all cross-phylum HGT inferences await experimental validation [\[51\]](#references). The 10 kb synteny threshold for calling HGT events has not been validated by permutation, and a housekeeping-gene null baseline for the incongruence rate remains unrun [\[52\]](#references). The headline Node_4915 result (8 phyla, divergence 4.843) still requires BLAST verification against NCBI nr [\[53\]](#references).

**Indirect NMDC inference.** Prophage burden scores assigned to NMDC metagenomic samples are derived by taxonomy-based transfer, which assumes genus-level conservation of prophage content and may not hold for recently acquired or lost prophages [\[54\]](#references).

**HGT labeling.** The interpretation that accessory module families represent horizontally transferred units is noted as speculative where no direct phylogenetic incongruence analysis supports it [\[55\]](#references). Similarly, the pqqD gene is an outlier to the general pattern of vertical PGP gene inheritance (55.5% core vs 63–81% for other PGP genes, with the highest singleton fraction at 27.5%) [\[56\]](#references).

**Open directions.** Stratifying HGT rates by function class would allow tests of whether regulatory or metabolic genes transfer at different rates [\[57\]](#references). MGE-context measurement at the whole-pangenome scale is technically feasible but requires Spark for the ~93M gene-cluster join [\[58\]](#references). Dedicated prophage prediction tools integrated with the BERDL pangenome would significantly improve detection sensitivity [\[59\]](#references) [\[60\]](#references). A housekeeping-gene null baseline for the T4SS-CAZy HGT detection rate remains the most immediately actionable validation gap [\[61\]](#references). Co-inheritance networks across modules could be extended to test whether functional gene modules are systematically co-transferred [\[62\]](#references).

## References

1. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
2. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
3. [Cog Analysis](../projects/cog-analysis.md) — REPORT.md › "Interpretation".
4. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Costly+Dispensable Genes Are Mobile Genetic Elements".
5. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "They Are Poorly Characterized Recent Acquisitions".
6. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "Interpretation".
7. [Costly Dispensable Genes](../projects/costly-dispensable-genes.md) — REPORT.md › "*Pseudomonas stutzeri* RCH2 Is an Outlier".
8. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "Interpretation".
9. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "Interpretation".
10. [Gene Function Ecological Agora](../projects/gene-function-ecological-agora.md) — REPORT.md › "Interpretation — M22 and pangenome openness measure distinct evolutionary phenomena".
11. [Pangenome Pathway Ecology](../projects/pangenome-pathway-ecology.md) — README.md › "Overview".
12. [Pangenome Pathway Ecology](../projects/pangenome-pathway-ecology.md) — RESEARCH_PLAN.md › "Hypothesis".
13. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "Novel Contribution".
14. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "1. Prophage gene modules are universal but structurally variable across 27,702 bacterial species".
15. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "3. Tail, head, and anti-defense modules are enriched in human-associated environments beyond phylogenetic expectation".
16. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "NMDC Cross-Validation (NB05)".
17. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Finding 3: Prophage density strongly predicts AMR repertoire breadth (H2)".
18. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Literature Context".
19. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Interpretation".
20. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Finding 1: AMR genes frequently share contigs with prophage markers".
21. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "2. Intrinsic vs Acquired Resistance Creates a Conservation Dichotomy".
22. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "2. Clinical species have predominantly acquired resistance; soil/aquatic species have more intrinsic resistance (H2 supported)".
23. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "4. Species with more clinical genomes carry more AMR (H4 proxy — species-level analysis)".
24. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 2: Resistance islands are widespread and tightly co-inherited".
25. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 2: Resistance islands are widespread and tightly co-inherited".
26. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 3: AMR variation tracks phylogeny in the majority of species — but acquired genes show stronger signal than intrinsic".
27. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Novel Contribution".
28. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "4. Core and accessory AMR genes have identical fitness costs (H3 not supported)".
29. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
30. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REPORT.md › "NB05 Analysis Results".
31. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REPORT.md › "Key Findings".
32. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — README.md › "Claim Framing".
33. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — README.md › "Claim Framing".
34. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "3. SNIPE genes are predominantly accessory (86.7%)".
35. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "2. SNIPE is widespread (1,696 species, 33 phyla)".
36. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "1. SNIPE resolves the phage resistance vs. metabolic cost trade-off".
37. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "6. SNIPE detected in phage therapy target (*Klebsiella*)".
38. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "4. The SNIPE nuclease domain is PF13455 (Mug113), not PF01541 (GIY-YIG)".
39. [Truly Dark Genes](../projects/truly-dark-genes.md) — REPORT.md › "Genomic context".
40. [Truly Dark Genes](../projects/truly-dark-genes.md) — REPORT.md › "Finding 5: Truly dark genes are enriched in accessory genomes and show HGT signatures (H3 supported)".
41. [Gene Function Ecological Agora](../projects/gene-function-ecological-agora.md) — REPORT.md › "Three novel findings the project surfaced".
42. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Operons Are Not a Confound".
43. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 5: Strong signal of horizontal gene transfer in phaC distribution".
44. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "3. Pathogenic gene clusters co-occur with transposases, suggesting HGT (H4 — partial)".
45. [Plant Microbiome Ecotypes](../projects/plant-microbiome-ecotypes.md) — REPORT.md › "3. Pathogenic gene clusters co-occur with transposases, suggesting HGT (H4 — partial)".
46. [Ibd Phage Targeting](../projects/ibd-phage-targeting.md) — REPORT.md › "NB12 — Pathobiont × phage targetability matrix (Pillar 4 opener)".
47. [Ibd Phage Targeting](../projects/ibd-phage-targeting.md) — REPORT.md › "NB15 — UC Davis per-patient profile + cocktail draft (Pillar 5 opener)".
48. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "Limitations".
49. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Limitations".
50. [Snipe Defense System](../projects/snipe-defense-system.md) — REPORT.md › "Limitations".
51. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REPORT.md › "Interpretation".
52. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REVIEW.md › "Methodology".
53. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REVIEW.md › "Methodology".
54. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "Limitations".
55. [Module Conservation](../projects/module-conservation.md) — REVIEW.md › "Findings Assessment".
56. [Pgp Pangenome Ecology](../projects/pgp-pangenome-ecology.md) — REPORT.md › "Vertical inheritance over HGT for PGP genes".
57. [Pangenome Openness](../projects/pangenome-openness.md) — REPORT.md › "Future Directions".
58. [Gene Function Ecological Agora](../projects/gene-function-ecological-agora.md) — REPORT.md › "Future directions (Phase 4)".
59. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Future Directions".
60. [Prophage Ecology](../projects/prophage-ecology.md) — REPORT.md › "Future Directions".
61. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — README.md › "NB05 — Characterisation and Validation Analyses".
62. [Cofitness Coinheritance](../projects/cofitness-coinheritance.md) — REPORT.md › "Future Directions".

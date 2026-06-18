# Metal Resistance

Metal resistance is the capacity of bacteria and archaea to survive, grow, and reproduce in environments containing elevated concentrations of toxic metals — copper, zinc, chromium, lead, uranium, nickel, cobalt, and others. Unlike antibiotic resistance, which is largely a clinical phenomenon driven by recent anthropogenic selection, metal resistance is ancient and ecologically widespread, shaped by the geochemistry of soils, sediments, groundwater, and marine environments over billions of years. This page exists in the wiki because metal resistance sits at the intersection of nearly every line of inquiry in this corpus: genome-scale fitness profiling, pangenome architecture, biogeography, AMR co-selection, field ecology, and the functional consequences of contamination. Understanding which genes confer resistance, how they distribute across the tree of life, and whether genomic predictions translate to real field ecology is essential context for interpreting results from projects spanning the Oak Ridge FRC site to global metagenomic surveys.

## Overview

Bacteria tolerate metals through a small set of well-characterized mechanisms: efflux pumps (particularly RND-family transporters) actively export metal ions; ABC transporters (adenosine triphosphate-binding cassette transporters, a large family of importers and exporters) regulate intracellular concentrations; target modification protects metal-sensitive enzymes; and sequestration proteins such as metallothioneins bind and neutralize ions. RB-TnSeq (randomized barcoded transposon sequencing, a pooled genome-wide screen where each gene is disrupted by an individually barcoded transposon and the fitness cost is measured in parallel across conditions) is the primary experimental tool in this corpus for identifying which genes are truly important for metal survival.

The Metal Fitness Atlas, a cross-project resource derived from RB-TnSeq data across 31 organisms and 16 metals, is the genomic backbone of much downstream analysis. It encodes a functional signature of 1,286 KEGG KO terms that can be projected onto any sequenced genome to produce a metal tolerance score [\[1\]](#references). A key architectural finding is that metal-important genes are predominantly core: even after removing pleiotropic, broadly stress-responsive genes, the remaining metal-specific set is 88% core within species [\[2\]](#references). This robustness means that the Atlas conclusions do not change materially if NaCl-responsive genes are filtered out [\[3\]](#references).

A complementary cross-resistance analysis shows that metal tolerance does not operate independently for each metal. Instead it has a two-layer architecture: a universal layer in which all metals share genetic basis because all metals disrupt the same fundamental cellular processes (protein stability, membrane integrity, cofactor insertion), and a chemistry-specific magnitude layer in which divalent cations competing for the same binding sites (Co, Ni, Zn) show especially strong pairwise correlation [\[4\]](#references). Across the Fitness Browser organism panel, 98.1% of metal-pair fitness correlations are positive [\[5\]](#references).

## What the Corpus Shows

### Gene content rather than phenotype predicts metal tolerance

A consistent theme across projects is that classical microbiology phenotypes — Gram stain, oxygen tolerance, enzyme activities, urease production — capture real biological differences in metal tolerance but add nothing to prediction beyond what phylogeny already provides. An XGBoost model trained on 10 phenotype features from BacDive achieves R² = 0.16 against Metal Fitness Atlas scores, yet when taxonomy is added the phenotype contribution becomes slightly negative (delta R² = -0.009) [\[6\]](#references). The number of metal resistance gene clusters in a genome outperforms all phenotype features combined [\[7\]](#references). One striking example of this phylogenetic confounding is urease: urease-positive organisms have *lower* metal tolerance scores, a reversal driven entirely by the lineage composition of urease-positive taxa rather than any mechanistic connection between urease and metal biology [\[8\]](#references).

Gram-negative bacteria do show higher metal tolerance than Gram-negative-negative counterparts [\[9\]](#references), consistent with the outer membrane acting as a partial barrier to metal entry. However, this association is again largely a phylogenetic signal — Gram-negative Pseudomonadota dominate the contaminated-environment isolate pool and carry inherently larger genomes encoding more metal functions.

### Between-species gene content variation encodes the ecological signal

Although metal tolerance genes are predominantly core within species, the between-species variation in the total number of metal tolerance gene clusters is large enough to predict where a bacterium was isolated. Strains isolated from heavy-metal-contaminated environments score Cohen's d = +1.0 above the environmental baseline in a BacDive-wide analysis spanning 42,227 strains linked to pangenome metal scores [\[10\]](#references). A dose-response gradient supports causality: heavy-metal isolates score higher than waste isolates, which score higher than industrial-contamination isolates, which score higher than uncontaminated environmental isolates [\[11\]](#references). The pangenome signal holds within Pseudomonadota and Actinomycetota after phylum stratification [\[12\]](#references), though not within Bacillota or Bacteroidota where contamination sample sizes are small [\[13\]](#references).

### Soil is metal-enriched; marine is depleted; hotspots exist

At the global scale, a survey of 260,000 MAGs (metagenome-assembled genomes) with coordinates shows that soil biomes are enriched for metal resistance genes while marine environments are depleted [\[14\]](#references). Eleven geographic hotspots were identified, with the Atacama Desert reaching an odds ratio of 9.83 [\[15\]](#references). The genome-resolved MAG approach provides strain-level spatial resolution and direct gene presence/absence determination, complementing rather than duplicating OTU-level 16S surveys [\[16\]](#references).

### Metal-type diversity predicts ecological niche breadth

Using the MicrobeAtlas global OTU database, the breadth of metal types a genus can resist — measured as the number of distinct metal AMR clusters across a genus's genomes — predicts ecological niche breadth across 99,000 OTUs even after phylogenetic correction via PGLS (phylogenetic generalized least squares, a regression method that accounts for shared ancestry) [\[17\]](#references). Critically, it is the *diversity* of metal types rather than the raw count of AMR clusters that drives this association, and the effect is independent of species richness and genome size [\[18\]](#references). Bacterial generalists are distinguished by breadth — ability to resist many metal types — rather than depth within any single metal [\[19\]](#references). The ENIGMA groundwater wells provide a within-study validation of this principle: contaminated plume wells show significantly higher community-weighted mean metal AMR cluster counts than uncontaminated reference wells [\[20\]](#references).

### Metal resistance genes reside in the accessory genome and spread horizontally

Despite the within-species core enrichment of metal tolerance gene *families*, heavy-metal-resistance genes at the level of individual strains have a conservation of only 71.2% in DvH (Desulfovibrio vulgaris Hildenborough), well below the housekeeping gene baseline [\[21\]](#references). This is consistent with metal resistance being carried on mobile genetic elements (MGEs) — plasmids, transposons, genomic islands — that distribute resistance unevenly across strains. A link between GT2 glycosyltransferase (a cell-envelope biosynthesis enzyme family) and metal resistance operons suggests that MGE-mediated acquisition also remodels the cell envelope in ways that confer collateral resistance [\[22\]](#references). The [Mobile Genetic Elements](mobile-genetic-elements.md) page covers the HGT machinery that moves these genes; notably, metal resistance gene prevalence (2.8% of coordinate-bearing MAGs) is far below T4SS (type IV secretion system) prevalence (21.8%), indicating that metal resistance genes and HGT machinery are not uniformly co-distributed [\[23\]](#references).

### Soil functional genomics reveals metal-specific COG signatures

Across 51,748 soil metagenomes, soil metal concentrations are strongly associated with the functional gene content of co-located microbial communities (distance-based RDA, db-RDA, explaining R² = 0.799 of residual variance after conditioning on project batch effects) [\[24\]](#references). Chromium and lead show the strongest overall functional associations [\[25\]](#references). For copper specifically, the COG associations are mechanistically coherent: membrane transport and energy-production COGs are enriched near high-copper soils, consistent with copper's known mechanism of disrupting membrane-bound enzymes [\[26\]](#references). However, the copper association is sensitive to the 10 km proximity criterion used to match soil measurements to KBase genomes [\[27\]](#references), and the directional signal suggests trade-offs between energy production and metal defense under copper stress [\[28\]](#references).

### Mechanism selection is environment-driven

A unifying principle across the AMR-resistome literature is that ecological niche selects resistance mechanism: soil and aquatic bacteria invest heavily in metal resistance while host-associated organisms favor target modification [\[29\]](#references). This explains why metal resistance genes skew accessory — they are only needed in metal-rich environments [\[30\]](#references). Within pangenomes, metal resistance genes form a major component of the accessory fraction [\[31\]](#references), and the AMR pangenome atlas reports enrichment of COG defense categories among metal-tolerant strains [\[32\]](#references).

### Counter-ion artifacts are not the explanation for metal-NaCl gene overlap

About 39.8% of metal-important genes in the Fitness Browser also show importance for NaCl stress. This overlap could in principle reflect chloride counter-ions delivered with metal salts, but zinc sulfate (delivering no chloride) shows 44.6% NaCl overlap — higher than most chloride-delivered metals — ruling out counter-ion confounding [\[33\]](#references). The overlap is instead driven by shared stress biology: cell-envelope damage, ion homeostasis disruption, and general stress response pathways are activated by both metal ions and osmotic stress [\[34\]](#references). A metal toxicity hierarchy emerges from fitness correlation with NaCl across organisms, running from general toxics (Zn, Cu, Co — high NaCl correlation) to pathway-specific toxics (Fe, Mo, W, Cr — low NaCl correlation) [\[35\]](#references). Iron in particular shows pathway-specific biology: its fitness profile correlates poorly with NaCl because it primarily disrupts iron-sulfur cluster assembly rather than general membrane functions [\[36\]](#references).

### ENIGMA site ecology: contamination taxonomic shifts not reflected in bulk functional potential

At the Oak Ridge Field Research Center (ENIGMA), contamination gradient analysis shows that the community taxonomic composition shifts along the gradient, but this does not translate into a robust monotonic shift in inferred stress-related functional potential when communities are profiled at genus resolution using broad COG categories [\[37\]](#references). This is consistent with prior Oak Ridge literature reporting pronounced compositional change alongside only modest functional-diversity decline [\[38\]](#references). The confirmatory null holds across multiple contamination index definitions and is not sensitive to the index construction [\[39\]](#references). An exploratory coverage-aware defense model finds a positive effect that attenuates under global multiple-testing correction [\[40\]](#references).

## Projects and Evidence

**metal_fitness_atlas** is the foundational project, generating the cross-species RB-TnSeq atlas linking 559 metal experiments across 31 organisms and identifying 1,286 KEGG KO terms as the conserved metal gene signature. Metal-important gene families are highly conserved across the 24 organisms with fitness matrices [\[41\]](#references), and core enrichment is robust even under stringent filtering [\[1\]](#references).

**metal_specificity** refines the atlas by separating metal-specific genes from shared-stress-response genes. The metal-specific fraction (genes important for metal but not for NaCl stress) remains 88% core [\[2\]](#references), a fraction whose functional importance is confirmed by gene knockout validation [\[42\]](#references). The metal-specific gene fraction represents about 60% of the metal-important set, with 40% shared with NaCl stress [\[43\]](#references).

**counter_ion_effects** rigorously tests whether the NaCl-metal gene overlap is a counter-ion artifact. Using matched salt experiments and the natural control of zinc sulfate (no chloride), this project confirms the overlap reflects shared stress biology, not chloride delivery [\[33\]](#references). The choline chloride experiments available for some FB organisms provide an alternative chloride control, though at different concentrations from the standard NaCl experiments [\[44\]](#references).

**metal_cross_resistance** maps pairwise fitness correlations across all metal pairs in the Fitness Browser, documenting a universal positivity (98.1% of correlations) and a tier architecture where chemically similar divalent cations show the highest shared responses [\[5\]](#references) [\[45\]](#references).

**bacdive_metal_validation** validates the Metal Fitness Atlas predictions against real ecology by linking 42,227 BacDive strains to pangenome metal tolerance scores and comparing scores across isolation environments. The d = +1.0 effect for heavy-metal isolates over baseline confirms that genome-based predictions capture genuine ecological signal [\[46\]](#references). This project also bridges phenotypes and pangenome scores across databases, linking BacDive taxonomy to GTDB pangenome species [\[47\]](#references).

**bacdive_phenotype_metal_tolerance** tests whether classical phenotypes predict metal tolerance, finding that seven of ten phenotype features individually correlate with metal tolerance scores [\[48\]](#references), but that the aggregate phenotype model adds nothing beyond taxonomy [\[49\]](#references). The dominant predictors in SHAP (SHapley Additive exPlanations) feature attribution are taxonomic identity and total gene count [\[50\]](#references).

**microbeatlas_metal_ecology** scales the question to global ecology using MicrobeAtlas OTU data, demonstrating for the first time that metal AMR type diversity predicts niche breadth across hundreds of thousands of OTUs [\[51\]](#references). The effect is robust to whether genome size and community richness are controlled [\[52\]](#references). The association shows intermediate phylogenetic signal via Pagel's lambda, indicating it is not purely an artifact of shared ancestry [\[53\]](#references).

**metal_resistance_global_biogeography** maps genome-resolved metal resistance using MAG coordinates from MG-RIFY, identifying soil enrichment, marine depletion, and eleven provisional geographic hotspots at strain-level resolution [\[54\]](#references) [\[14\]](#references). MAG coordinate coverage extends across most of the world but has a 30.8% per-sample gap in ENA lat/lon data [\[55\]](#references).

**soil_metal_functional_genomics** links measured soil metal concentrations to metagenome functional gene content across 51,748 samples, finding widespread COG-metal associations across 9 metals and 435 COG categories [\[56\]](#references). A mechanistic classification scheme partitions the associated COGs into resistance, oxidative-stress, membrane-remodeling, energy-metabolism, and unknown categories [\[57\]](#references).

**amr_environmental_resistome** and **amr_pangenome_atlas** situate metal resistance within the broader AMR landscape, documenting its prevalence across pangenomes and its environment-specific enrichment relative to other resistance mechanisms [\[29\]](#references).

**lab_field_ecology** tests whether lab-measured metal tolerance (Fitness Browser scores) predicts field abundance in ENIGMA groundwater communities, finding that the aggregate metal tolerance score does not significantly predict field abundance (rho = 0.50, p = 0.095) [\[58\]](#references), but genus-level uranium correlations are informative: *Caulobacter* and *Sphingomonas* are depleted at high uranium, suggesting sensitivity, while *Herbaspirillum* and *Bacteroides* are enriched, suggesting tolerance [\[59\]](#references).

**enigma_contamination_functional_potential** examines whether ENIGMA contamination gradients predict community-level functional potential at genus resolution, finding a null confirmatory result and an exploratory defense-system signal that depends on coverage specification [\[60\]](#references).

**lanthanide_methylotrophy_atlas** connects lanthanide-handling biology (lanmodulin, a rare earth element binding protein, and xoxF, the lanthanide-dependent methanol dehydrogenase) to metal resistance context. Lanmodulin is phylogenetically restricted to three alpha-Proteobacterial methylotroph families [\[61\]](#references), and bakta annotation is more trustworthy than eggNOG for this gene [\[62\]](#references).

## Connections

Metal resistance is deeply entangled with [AMR Resistome](amr-resistome.md) biology because metal resistance genes and antibiotic resistance genes co-select and are physically co-located on mobile genetic elements; the same plasmids and transposons that carry metal operons also carry beta-lactamases and efflux pumps, meaning metal contamination in the environment can maintain antibiotic resistance without antibiotic selection pressure. The [`amr_fitness_cost`](../projects/amr-fitness-cost.md) project cross-references metal atlas findings to document this interface [\[63\]](#references).

[Gene Fitness](gene-fitness.md) is the methodological foundation for metal resistance quantification in this corpus. RB-TnSeq gene fitness scores are the raw measurements that become the Metal Fitness Atlas; understanding how fitness scores are aggregated, normalized, and projected onto the pangenome is prerequisite to interpreting any downstream metal tolerance claim. The [Gene Fitness](gene-fitness.md) page explains the Fitness Browser data structure that underlies the atlas.

[Pangenome Architecture](pangenome-architecture.md) is adjacent because the central puzzle of metal resistance — how can genes be simultaneously core within species yet vary enough between species to predict ecology? — is resolved only by distinguishing within-species conservation from between-species total content variation. The [Pangenome Architecture](pangenome-architecture.md) page covers the BERDL and GTDB pangenome frameworks used for this resolution [\[64\]](#references).

[Mobile Genetic Elements](mobile-genetic-elements.md) are the vehicles by which metal resistance genes spread horizontally, driving the accessory-genome enrichment observed in pangenome comparisons. The GT2 glycosyltransferase-metal resistance operon link provides one mechanistic example of how MGE transfer packages multiple adaptive traits together [\[22\]](#references).

[Environment Biogeography](environment-biogeography.md) is the ecological complement of metal resistance genomics: this page covers the spatial distribution, biome stratification, and community assembly consequences, while metal resistance focuses on the molecular mechanisms and genomic architecture.

[Subsurface Genomics](subsurface-genomics.md) is adjacent because the Oak Ridge FRC site, the primary field validation site in this corpus, is a subsurface uranium and mixed-metal contamination site. Subsurface metal gradients provide the most concrete ecological context for metal resistance gene predictions.

[Metabolic Pathways](metabolic-pathways.md) connects through the lanthanide biology thread: xoxF-dependent methanol oxidation requires lanthanides as cofactors, placing lanthanide sequestration (lanmodulin) at the interface of metal handling and central carbon metabolism [\[65\]](#references).

[Functional Dark Matter](functional-dark-matter.md) is relevant because a large fraction of metal-associated COGs remain unannotated; the soil functional genomics project identifies unknown COGs as one of its mechanistic classification categories, and the field_vs_lab_fitness project identifies 52 unannotated genes in ecological adaptation modules as candidates for novel metal-relevant functions.

## Caveats and Open Directions

### Methodological limitations in the atlas and validation pipeline

Metal Fitness Atlas scores are genome-based predictions rather than direct metal tolerance measurements, so all phenotype-score associations are phenotype-to-genome correlations rather than phenotype-to-phenotype validations [\[66\]](#references). Species-level matching between BacDive and GTDB is lossy — 56.6% of BacDive strains fail to match any GTDB species because the two databases use different species boundaries [\[67\]](#references), and GCA accession-based matching that could recover additional links has not yet been implemented [\[68\]](#references). BacDive validation of multi-metal cross-resistance scores collapsed to only 20 independent species after collapsing Fitness Browser strains to species level, leaving that validation statistically inconclusive [\[69\]](#references).

The NaCl control used for shared-stress correction is imperfect: NaCl delivers both sodium and chloride, and its fitness profile includes sodium toxicity and osmotic effects beyond chloride [\[70\]](#references). Seven metals are tested in only one organism (DvH), providing no cross-organism replication for their overlap statistics [\[71\]](#references). The psRCH2 organism, the only within-metal counter-ion comparison (CuCl2 vs CuSO4), is severely confounded by aerobic/anaerobic growth differences [\[72\]](#references).

### Statistical issues

The soil functional genomics database-wide analysis identified 2,355 significant COG-metal associations, but effect sizes (Spearman rho) have not been systematically reported, and many may be statistically but not biologically significant [\[73\]](#references). The reported db-RDA R² = 0.799 is conditional on project accession, so the unconditional R² of metals alone is unknown and may be substantially lower [\[74\]](#references). With co-contaminating metals (Cr, Pb, Zn, Cu co-vary in industrial soils), the Benjamini-Hochberg FDR correction is anti-conservative and the true FDR is likely higher than reported [\[75\]](#references). Spatial autocorrelation in soil samples from the same region is a confound that has not yet been tested with Moran's I [\[76\]](#references).

### Causation and directionality

The cross-sectional observational design of the microbeatlas analysis means that the direction of the metal-diversity/niche-breadth association cannot be established — it is equally consistent with metal tolerance enabling range expansion and with ecological generalism enabling metal gene acquisition through more frequent horizontal gene transfer [\[77\]](#references). Archaeal analyses are severely underpowered (n = 48 genera, 11% power at α = 0.05), so the non-significant archaeal result should not be interpreted as evidence against the association in archaea [\[78\]](#references).

### Spatial analyses need validation

The 11 global hotspots identified by the biogeography project are provisional because sampling-effort normalization was not complete at the time of analysis [\[79\]](#references) and expedition-level clustering validation — needed to rule out single-study geographic artifacts — remains pending [\[80\]](#references). The GapMind pathway definition used to assign metal resistance to MAGs may undercount true prevalence because it may not cover all known resistance mechanisms such as efflux pumps, metallothioneins, and metal-sequestering operons [\[81\]](#references).

### Open experimental directions

Several projects identify concrete next steps. RB-TnSeq experiments with La and Ce in organisms that naturally encounter lanthanides would test whether the xoxF dominance finding reflects a fitness benefit in REE-handling contexts [\[82\]](#references). Nickel-urease fitness dissection would resolve whether the urease-reversal at the pangenome scale reflects a mechanistic decoupling or purely lineage effects [\[83\]](#references). Expanding the Oak Ridge field analysis to include *Rhodanobacter*, a genus with known acid-metal tolerance and available Fitness Browser data, would improve the lab-to-field comparison [\[84\]](#references). Microcosm experiments with defined microbial consortia grown in metal-amended media would test the niche-breadth hypothesis causally [\[85\]](#references). Per-metal decomposition of the aggregate metal tolerance score is needed to determine whether metals like uranium rather than the multi-metal aggregate drive individual field predictions [\[86\]](#references).

## References

1. [Metal Fitness Atlas](../projects/metal-fitness-atlas.md) — REPORT.md › "Metal-Important Genes Are Enriched in the Core Genome".
2. [Metal Specificity](../projects/metal-specificity.md) — REPORT.md › "Metal-Specific Genes Are Core-Enriched but Less So Than General Sick Genes".
3. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "The Metal Fitness Atlas Is Validated".
4. [Metal Cross Resistance](../projects/metal-cross-resistance.md) — REPORT.md › "The Two Layers of Cross-Resistance".
5. [Metal Cross Resistance](../projects/metal-cross-resistance.md) — REPORT.md › "Metal cross-resistance is universal and directionally conserved".
6. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "3. Phenotype Features Add Nothing Beyond Taxonomy (Delta R² = -0.009)".
7. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "What Does Predict Metal Tolerance".
8. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "4. Urease-Positive Organisms Have *Lower* Metal Tolerance (H1e Reversed)".
9. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "1. Gram-Negative Bacteria Have Significantly Higher Metal Tolerance Scores (d=-0.61)".
10. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "1. Bacteria From Metal-Contaminated Environments Have Significantly Higher Metal Tolerance Scores".
11. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "1. Bacteria From Metal-Contaminated Environments Have Significantly Higher Metal Tolerance Scores".
12. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "2. The Signal Holds Within Major Phyla".
13. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "2. The Signal Holds Within Major Phyla".
14. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
15. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
16. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — README.md › "Distinction from `microbeatlas_metal_ecology`".
17. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Novel contribution".
18. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "R6. Three-covariate PGLS: metal types independent of both species richness and genome size".
19. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Finding 3: Metal type diversity, not total gene burden, distinguishes broad-niche genera".
20. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Track B: PRJNA1084851 (ENIGMA ORFRC 16S — full pipeline)".
21. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Key Biological Insight".
22. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — REPORT.md › "NB05 Analysis Results".
23. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
24. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
25. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
26. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Interpretation".
27. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Critical Assessment".
28. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
29. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "3. Resistance mechanism composition is strongly environment-dependent (H3 supported)".
30. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "3. Resistance mechanism composition is strongly environment-dependent (H3 supported)".
31. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "Heavy Metal Resistance Is a Major AMR Component".
32. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "4. AMR Genes Are Enriched in Defense and Ion Transport Functions".
33. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "2. Counter Ions Are NOT the Primary Driver of the Overlap".
34. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "2. Counter Ions Are NOT the Primary Driver of the Overlap".
35. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "3. DvH Metal-NaCl Correlation Follows Toxicity Mechanism, Not Chloride Dose".
36. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "A Metal Toxicity Hierarchy Emerges".
37. [Enigma Contamination Functional Potential](../projects/enigma-contamination-functional-potential.md) — REPORT.md › "Interpretation".
38. [Enigma Contamination Functional Potential](../projects/enigma-contamination-functional-potential.md) — REPORT.md › "Literature Context".
39. [Enigma Contamination Functional Potential](../projects/enigma-contamination-functional-potential.md) — REPORT.md › "Contamination-index sensitivity does not change confirmatory outcome".
40. [Enigma Contamination Functional Potential](../projects/enigma-contamination-functional-potential.md) — REPORT.md › "Exploratory defense signal remains strongest in coverage-aware models".
41. [Metal Fitness Atlas](../projects/metal-fitness-atlas.md) — REPORT.md › "1,182 Conserved Metal Gene Families Identified".
42. [Metal Specificity](../projects/metal-specificity.md) — REPORT.md › "Metal-Specific Genes Are Enriched for Metal Resistance Functions".
43. [Metal Specificity](../projects/metal-specificity.md) — REPORT.md › "55% of Metal-Important Genes Are Metal-Specific".
44. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "Future Directions".
45. [Metal Cross Resistance](../projects/metal-cross-resistance.md) — REPORT.md › "Three-tier gene architecture".
46. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "Genome Content Predicts Environmental Metal Tolerance".
47. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "3. 42,227 BacDive Strains Linked to Pangenome Metal Scores".
48. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "2. Seven of Ten Phenotype Features Are Individually Significant After FDR Correction".
49. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "The Phylogenetic Confounding Wall".
50. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "6. SHAP Analysis Confirms Taxonomy and Gene Count Dominate".
51. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Finding 1: Bacterial niche breadth is moderately phylogenetically conserved; metal type diversity predicts it beyond phylogeny".
52. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "R5. Genome size PGLS covariate (new BERDL query)".
53. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Finding 2: Metal AMR traits show intermediate phylogenetic signal — consistent with mixed vertical inheritance and HGT".
54. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "NB02 Spatial Analysis Results".
55. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REPORT.md › "Key Findings".
56. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
57. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — README.md › "NB05 — Validation Analyses".
58. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Lab Metal Tolerance Does Not Significantly Predict Field Abundance Ratio".
59. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Novel Contribution".
60. [Enigma Contamination Functional Potential](../projects/enigma-contamination-functional-potential.md) — REPORT.md › "Confirmatory Spearman tests remain null with confidence intervals and global FDR".
61. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "3. Lanmodulin clade restriction is total; xoxF co-occurrence falls just short of the 80 % threshold".
62. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "7. Marker-source calibration: eggNOG and bakta disagree more than expected".
63. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Future Directions".
64. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "Reconciling With the Core Genome Robustness Model".
65. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "1. xoxF (REE-dependent MDH) outnumbers mxaF (Ca-dependent MDH) by ~19:1 across the BERDL pangenome — H1 strongly supported".
66. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "Limitations".
67. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "Limitations".
68. [Bacdive Metal Validation](../projects/bacdive-metal-validation.md) — REPORT.md › "Future Directions".
69. [Metal Cross Resistance](../projects/metal-cross-resistance.md) — REPORT.md › "BacDive validation is inconclusive at FB organism scale".
70. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "Limitations".
71. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "Limitations".
72. [Counter Ion Effects](../projects/counter-ion-effects.md) — REPORT.md › "6. psRCH2: The Only Within-Metal Counter Ion Comparison".
73. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Interpretation".
74. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Critical Assessment".
75. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Critical Assessment".
76. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — README.md › "NB05 — Validation Analyses".
77. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Causation and directionality".
78. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "R3. Archaeal PGLS and formal power analysis (exploratory, n = 48)".
79. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — README.md › "Reproduction".
80. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REVIEW.md › "Findings Assessment".
81. [Metal Resistance Global Biogeography](../projects/metal-resistance-global-biogeography.md) — REVIEW.md › "Findings Assessment".
82. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "Future Directions".
83. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "Suggested Experiments".
84. [Lab Field Ecology](../projects/lab-field-ecology.md) — REPORT.md › "Future Directions".
85. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Testable hypotheses".
86. [Bacdive Phenotype Metal Tolerance](../projects/bacdive-phenotype-metal-tolerance.md) — REPORT.md › "Future Directions".

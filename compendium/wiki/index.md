# State Of The Science

## Cross-Project Overview

This wiki is a cross-project synthesis of microbial genomics and ecology research, built from 70 computational projects carried out within the BERIL/ENIGMA research ecosystem. It exists to answer a question that no single project can answer on its own: what do we collectively know about the genetic, metabolic, and ecological logic of bacteria, and how do the results of one study constrain or extend another? A scientist-engineer new to this niche can use it as a map — a way to locate the most relevant prior work, identify the strongest consensus findings, and spot where the evidence is thin or contradictory before committing to a new direction.

The corpus spans seven interconnected research topics: how bacterial genes contribute to fitness and which are essential ([gene fitness](topics/gene-fitness.md)), how metabolic pathways are distributed and co-evolve across the pangenome ([metabolic pathways](topics/metabolic-pathways.md) and [pangenome architecture](topics/pangenome-architecture.md)), how resistance to antibiotics and metals is organized ([AMR resistome](topics/amr-resistome.md) and [metal resistance](topics/metal-resistance.md)), how horizontal gene transfer shapes genome evolution ([mobile genetic elements](topics/mobile-genetic-elements.md)), how microbial communities structure themselves across environments ([environment biogeography](topics/environment-biogeography.md), [microbial ecotypes](topics/microbial-ecotypes.md), and [subsurface genomics](topics/subsurface-genomics.md)), how the majority of bacterial genes lack known functions ([functional dark matter](topics/functional-dark-matter.md)), and how this knowledge can be turned into engineered communities for therapeutic and agricultural applications ([microbiome engineering](topics/microbiome-engineering.md)). The *Acinetobacter baylyi* ADP1 strain is a recurring model system for multi-omics integration and is described separately on the [Adp1 Model System](topics/adp1-model-system.md) page.

The 70 projects collectively analyzed hundreds of thousands of bacterial genomes, spanning datasets such as the KBase pangenome collection (over 14,000 species), the NMDC/Arkin metagenomic survey, the ENIGMA subsurface community collection, and the KBase Fitness Browser (48 organisms, 228,709 genes with transposon fitness measurements). Several themes emerge repeatedly across projects. First, the distinction between the *core genome* (genes shared by nearly all members of a species) and the *accessory genome* (variable genes present in some strains) is not just structural but functional: core genes are disproportionately involved in housekeeping and metabolism, are under stronger purifying selection, and impose higher metabolic burden when lost, while accessory genes are enriched for defense, mobile elements, and conditionally useful traits acquired by horizontal transfer [\[1\]](#references) [\[2\]](#references). Second, gene conservation across species is the best single predictor of gene essentiality, but fitness under field-relevant conditions adds independent signal [\[3\]](#references). Third, both resistance genes and many metabolic pathways are distributed non-randomly in the pangenome in ways that track ecology more than phylogeny, a theme that recurs from the AMR resistome to pangenome-pathway geography [\[4\]](#references).

A note on methodology: most cross-species results in this corpus rely on RB-TnSeq (random-barcode transposon sequencing), a technique that creates a genome-wide library of transposon insertion mutants, each tagged with a unique DNA barcode, and tracks their relative growth rates under many conditions simultaneously. A gene's *fitness* in this framework is the log-ratio of barcode counts after vs before selection: negative values mean the mutant grew poorly (the gene contributes to growth), and near-zero values mean the gene was dispensable in that condition. Metabolic pathway coverage is mostly assessed with GapMind, a curated database-and-HMM tool that asks whether a genome encodes complete or near-complete routes to specific biosynthetic goals. Flux balance analysis (FBA) is a constraint-based metabolic modeling technique that predicts growth phenotypes from genome-derived stoichiometric models but depends heavily on gapfilling — with 87% of predictions across 14 genomes requiring at least one gapfilled reaction, accuracy is tightly coupled to gapfilling quality [\[5\]](#references). These methods recur across projects, so caveats about their resolution limits apply broadly.

## Topic Map

### Gene Fitness and Essentiality

The most fundamental question the corpus asks is which genes bacteria actually need, and under what conditions. The answer is nuanced. Across 48 organisms in the Fitness Browser, 1,116 stable co-fitness modules — groups of genes that tend to gain or lose fitness together across conditions — were identified, with most modules concentrated in the core genome [\[6\]](#references). Of roughly 17,000 ortholog families tested across those 48 organisms, only 5% (859 families) qualify as universally essential — a smaller set than computational conservation estimates because experimental essentiality requires loss of viability in every tested organism, a stringent criterion [\[7\]](#references). Essentiality is highly strain-dependent: roughly half of essential genes in one strain are non-essential in a close relative [\[8\]](#references), which has direct implications for broad-spectrum targeting strategies.

Conservation across species is, however, the strongest available proxy for essentiality. Essential genes are significantly enriched in the core genome, and genes with high fitness importance under any tested condition are more likely to be conserved than those with near-zero fitness [\[9\]](#references). Fitness effects from field-relevant stress conditions (metal, temperature, pH) are *more* conserved than lab-specific traits [\[10\]](#references), suggesting that lab fitness data is an impoverished proxy for the selective pressures that actually maintain genes over evolutionary time.

An important complication is the **core genome burden paradox**: core genes are actually *more* likely to impose a metabolic burden (the deletion mutant grows faster, indicating the gene was costly to express) than accessory genes — 24.4% vs 19.9% — yet they are retained, implying that fitness benefits of core genes across natural conditions outweigh their lab-measured costs [\[11\]](#references) [\[12\]](#references). This resolves a long-standing puzzle about why bacteria keep genes that seem to slow growth: they are retained not despite their cost but because they are beneficial under conditions not captured in standard lab experiments.

### Metabolic Pathways and the Pangenome

Metabolic completeness across genomes follows clear evolutionary logic. Amino acid biosynthesis pathways are among the most conserved functional categories: 17 of 18 amino acid biosynthesis pathways are present in all seven core model organisms tested [\[13\]](#references), and the capacity for amino acid prototrophy (self-synthesis) is almost certainly ancestral in bacteria, with auxotrophy representing secondary loss [\[14\]](#references). At the community level, the Black Queen Hypothesis (BQH) — the idea that public-good metabolites allow genomes to shed costly biosynthetic pathways when neighbors supply them — leaves a clear signal: in a 13-ecosystem NMDC metagenomics survey, 11 of 13 amino acid biosynthesis pathways showed negative correlations between community pathway completeness and ambient metabolite abundance, the direction the BQH predicts [\[15\]](#references). Ecosystem type predicts amino acid pathway completeness as strongly as phylogeny, with 17 of 18 pathways showing significant ecosystem-level variation [\[16\]](#references).

The relationship between pangenome openness and metabolic capability is complex. Open-pangenome species show higher enrichment of mobile (L) and defense (V) COG categories in their novel genes, consistent with opportunistic horizontal gene transfer, but pangenome openness does not cleanly predict which metabolic pathways are variable or which ecological niche a species occupies [\[17\]](#references). Ecological diversity — proxied by the range of environments a genus spans in 16S atlases — predicts metabolic completeness better than geographic spread alone [\[4\]](#references), and the fraction of core genes in a pangenome negatively correlates with niche breadth (r = −0.324, p < 1e−46), meaning specialists tend toward closed pangenomes [\[18\]](#references). These results connect pangenome structure to the [environment biogeography](topics/environment-biogeography.md) and [microbial ecotypes](topics/microbial-ecotypes.md) pages.

Within *Pseudomonas* (433 species, 12,732 genomes), the primary axis of metabolic variation is carbon source utilization, particularly the dramatic loss of sugar pathways in host-associated clades versus free-living relatives [\[19\]](#references), marking the first systematic quantification of carbon pathway profiles across a genus at this scale [\[20\]](#references). The ENIGMA/KBase genotype-to-phenotype project provides a complementary view: using 46,000 genotype-phenotype pairs, binary growth outcomes on amino acids and nucleosides are predictable from genome content, but continuous fitness parameters are not — mechanistic prediction requires on the order of 10,000 training examples per phenotype class [\[21\]](#references) [\[22\]](#references).

### AMR Resistome and Metal Resistance

Across 14,723 species, AMR genes are consistently depleted from the core genome and concentrated in the accessory genome. This depletion is not because resistance is fitness-costly under standard conditions — AMR knockouts are more dispensable than average when no antibiotic is present — but under any antibiotic, 57% of AMR genes flip to become fitness-important, which is the evolutionary logic for maintaining them [\[23\]](#references) [\[24\]](#references). The cost that does exist is real but small and does not depend on mechanism type [\[25\]](#references). This is the first pan-bacterial meta-analysis of AMR fitness costs using genome-wide transposon fitness data, and it shows that core and accessory AMR genes have virtually identical fitness distributions [\[26\]](#references) [\[27\]](#references).

For metal resistance specifically, soil metal concentrations strongly predict functional gene content of co-located communities (db-RDA R² = 0.799), with chromium and lead showing the strongest signals [\[28\]](#references). The first analysis linking genus-level metal type diversity to global ecological niche breadth found a significant positive relationship after phylogenetic correction [\[29\]](#references). Metal resistance genes are the dominant fraction of the AMR census — mercury alone accounts for roughly 18% of all AMR annotations — and are far more environment-discriminating than antibiotic resistance genes. These connections are developed further on the [AMR resistome](topics/amr-resistome.md) and [metal resistance](topics/metal-resistance.md) pages.

### Mobile Genetic Elements and Defense Systems

Horizontal gene transfer (HGT) is the primary mechanism by which bacteria innovate genomically, more important than vertical inheritance at pangenome scale [\[2\]](#references). Accessory genome genes carry signatures of recent acquisition — elevated GC content deviation from host genome mean, physical association with transposases and integrases [\[30\]](#references). Defense systems co-localize with mobile elements in "mobile defense islands," a motif particularly enriched in human-associated bacteria engaged in phage arms races [\[31\]](#references) [\[32\]](#references).

SNIPE (the DUF4041 / PF13250 domain, recently renamed by InterPro based on this work) is a nuclease domain found across 1,696 species and 33 phyla [\[33\]](#references). It resolves a fitness tradeoff: rather than deleting the mannose/glucosamine transporter ManYZ to gain phage resistance, SNIPE-bearing strains retain full transporter function while cleaving phage DNA during injection, giving phage resistance without the metabolic cost of losing the transporter [\[34\]](#references). Prophages (integrated viral genomes) add a further layer: species carrying more prophage markers also carry broader AMR repertoires, and over half of AMR gene instances in high-prophage species sit on contigs bearing strict phage markers [\[35\]](#references). Full details are on the [mobile genetic elements](topics/mobile-genetic-elements.md) page.

### Functional Dark Matter

A substantial fraction of bacterial genes have no known function. In the Fitness Browser cohort (48 organisms, 228,709 genes), 24.9% lack functional annotation, and of these, roughly 7,787 show strong fitness effects and 9,557 are essential — together representing about 30% of dark genes that are demonstrably important despite having no annotation [\[36\]](#references). After aggressive re-annotation with Bakta, only 16% (6,427 genes) remain "truly dark" where both the original pipeline and Bakta agree on "hypothetical protein" [\[37\]](#references). Truly dark genes carry stronger GC-content deviations from their host genomes, consistent with recent horizontal acquisition, and are concentrated in the accessory genome [\[30\]](#references). The [functional dark matter](topics/functional-dark-matter.md) page details the tiered census and the prioritization strategy for experimental follow-up.

### Subsurface Genomics and Environment Biogeography

At the ENIGMA Oak Ridge Reservation field site, 16S rRNA community similarity patterns alone can reconstruct subsurface hydrology at meter scale: the U3-M6-L7 corridor of groundwater wells, identified purely from Bray-Curtis dissimilarity, aligns with the expected northeast-to-southwest plume trajectory [\[38\]](#references) [\[39\]](#references). Uranium contamination shifts community composition measurably: five of 14 Fitness Browser genera show significant correlation with uranium concentration after FDR correction, with *Caulobacter* and *Sphingomonas* emerging as potential uranium-sensitive indicators [\[40\]](#references) [\[41\]](#references).

Embeddings of microbial community 16S profiles in a global 464,000-sample atlas (AlphaEarth) capture environment type reliably, and UMAP projections reveal discrete environmental clusters that match habitat categories [\[42\]](#references). These biogeographic tools underpin the metal-resistance analyses (which use niche breadth from 16S atlases as a dependent variable) and the ecotype analyses (which use embedding coordinates to classify strains). Details are on the [environment biogeography](topics/environment-biogeography.md) and [subsurface genomics](topics/subsurface-genomics.md) pages.

### Microbiome Engineering

The cystic fibrosis lung formulation project illustrates how the genomic and ecological knowledge above is applied to therapeutic community design. A five-organism cocktail was designed on the basis of metabolic complementarity and competitive exclusion of *Pseudomonas aeruginosa* PA14, but the project found that no single organism outgrows PA14 in co-culture and that the cocktail composition must account for cohort-to-cohort variation in existing lung microbiome states [\[43\]](#references) [\[44\]](#references). Metabolic overlap between community members predicts competitive inhibition, and state-dependent dosing (matching inoculant composition to the recipient's existing community) improves predicted efficacy [\[45\]](#references) [\[46\]](#references). Plant microbiome engineering (the PGP pangenome ecology project) shows that plant-growth-promoting traits such as ACC deaminase (ACDS) and PQQ-linked systems are predominantly core genes in beneficial bacteria, with open pangenomes showing lower PGP gene prevalence — the opposite of what streamlining theory predicts — suggesting that niche breadth, not genome closedness, predicts PGP capability [\[47\]](#references). The [microbiome engineering](topics/microbiome-engineering.md) page synthesizes both therapeutic and agricultural engineering efforts.

## Author Map

This corpus is the work of a small research team. The [Dileep Kishore](authors/dileep-kishore.md) page is the principal analytical contributor across most projects. [Heather MacGregor](authors/heather-macgregor.md) contributed to several ecological analyses. The AI co-author [Claude](authors/claude.md) assisted with synthesis writing. ORCID-linked author pages index contributions to specific datasets and are cross-referenced from individual topic pages:

- [0000-0001-5810-2497](authors/0000-0001-5810-2497.md)
- [0000-0001-9076-6066](authors/0000-0001-9076-6066.md)
- [0000-0002-0357-1939](authors/0000-0002-0357-1939.md)
- [0000-0002-1927-3565](authors/0000-0002-1927-3565.md)
- [0000-0002-2170-2250](authors/0000-0002-2170-2250.md)
- [0000-0002-2620-8948](authors/0000-0002-2620-8948.md)
- [0000-0002-3405-2744](authors/0000-0002-3405-2744.md)
- [0000-0002-4999-2931](authors/0000-0002-4999-2931.md)
- [0000-0002-6513-7425](authors/0000-0002-6513-7425.md)
- [0000-0002-6601-2165](authors/0000-0002-6601-2165.md)
- [0000-0002-8719-7760](authors/0000-0002-8719-7760.md)
- [0000-0003-2493-234x](authors/0000-0003-2493-234x.md)
- [0000-0003-2728-7622](authors/0000-0003-2728-7622.md)
- [0009-0007-0287-2979](authors/0009-0007-0287-2979.md)

## Data Map

Eight primary data collections appear repeatedly across projects and underpin most analyses:

- **[KBase/BERDL Pangenome](data/kbase-ke-pangenome.md)** — the backbone collection: more than 14,000 species with Roary pangenomes, COG annotations, and core/accessory partitioning. Virtually every cross-species result in this corpus uses this resource.
- **[KBase Fitness Browser](data/kescience-fitnessbrowser.md)** — RB-TnSeq fitness data for 48 organisms across hundreds of conditions. The source of all gene-fitness, essentiality, and cofitness module results.
- **[NMDC/Arkin metagenomic survey](data/nmdc-arkin.md)** — community metagenomes across 13 ecosystem types, used for metabolic-ecology and Black Queen analyses.
- **[ENIGMA CORAL isolate collection](data/enigma-coral.md)** — subsurface groundwater isolates from the Oak Ridge Reservation, the primary source for field fitness, uranium correlation, and community ecology analyses.
- **[KBase MSD Biochemistry](data/kbase-msd-biochemistry.md)** — reaction and compound database used for metabolic model gapfilling and FBA analyses.
- **[KBase UniRef](data/kbase-uniref.md)** — sequence homology resource underpinning annotation transfer and dark matter re-annotation.
- **[KBase Phenotype](data/kbase-phenotype.md)** — growth phenotype database cross-referenced for genotype-to-phenotype prediction projects.
- **[PhageFoundry](data/phagefoundry.md)** — phage genome collection used in the IBD phage targeting and prophage ecology projects.
- **[PROTECT GenomeDepot](data/protect-genomedepot.md)** — additional genome collection for IBD and clinical microbiome analyses.

## Caveats and Open Directions

Several recurrent caveats should be held in mind when reading any individual result in this corpus.

**Sampling bias** is pervasive. NCBI and GTDB systematically over-represent clinical and human-associated isolates, which inflates core-depletion signals for resistance genes and enrichment estimates for human-gut metabolic traits. The Fitness Browser organisms are all lab-adapted strains, meaning fitness measurements may underestimate the benefit of genes whose selective advantage appears only in field conditions. Cofitness — the tendency of two genes to have correlated fitness across conditions — does not equal co-regulation, because genes can share dispensability in lab conditions without being in the same regulatory unit [\[48\]](#references).

**Phylogenetic confounding** affects many cross-species correlations. Most ecology-vs-phylogeny comparisons control for phylogenetic signal via PGLS or permutation tests, but the controls are imperfect for traits that are simultaneously correlated with taxonomy and environment. Several projects note that phylum membership explains substantial variance attributed to environment before controlling for it.

**Methodological resolution limits** are also important. GapMind has known ceiling effects for common pathways and sensitivity limits for pathways with non-canonical enzymes. RB-TnSeq cannot assess truly essential genes because insertion is lethal, creating a systematic gap in the dark-matter and essentiality analyses. The Fitness Browser does not cover *Acinetobacter baylyi* ADP1, making ADP1's rich fitness-by-condition dataset a unique resource not available in the standard cross-species analyses [\[49\]](#references).

**Incomplete projects** are represented throughout. Several projects are at the planning or exploratory stage and have no results yet. The wiki documents these gaps explicitly so that future work can build on the design rather than duplicating the framing.

The most productive open directions are integrative: linking the metal resistance atlas to field fitness measurements, connecting the functional dark matter census to AlphaFold structure predictions for priority candidates, expanding the Black Queen community signal to freshwater and deep subsurface ecosystems not yet covered, and validating community metabolic models with targeted exometabolomics experiments. The [gene fitness](topics/gene-fitness.md), [metabolic pathways](topics/metabolic-pathways.md), [functional dark matter](topics/functional-dark-matter.md), and [pangenome architecture](topics/pangenome-architecture.md) pages each carry more detailed caveats and open-direction lists.

## References

1. [Cog Analysis](projects/cog-analysis.md) — REPORT.md › "Universal Functional Partitioning in Bacterial Pangenomes".
2. [Cog Analysis](projects/cog-analysis.md) — REPORT.md › "Interpretation".
3. [Field Vs Lab Fitness](projects/field-vs-lab-fitness.md) — REPORT.md › "Specificity Analysis: Lab-Specific Genes Are Surprisingly More Core".
4. [Pangenome Pathway Geography](projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
5. [Acinetobacter Adp1 Explorer](projects/acinetobacter-adp1-explorer.md) — REPORT.md › "8. 87% of Growth Predictions Depend on Gapfilled Reactions".
6. [Fitness Modules](projects/fitness-modules.md) — REPORT.md › "ICA Decomposition (32 organisms)".
7. [Essential Genome](projects/essential-genome.md) — REPORT.md › "Only 5% of Ortholog Families Are Universally Essential".
8. [Essential Genome](projects/essential-genome.md) — REPORT.md › "Variable Essentiality Is the Norm, Not the Exception".
9. [Conservation Vs Fitness](projects/conservation-vs-fitness.md) — REPORT.md › "Essential Genes Are Enriched in Core Clusters (Phase 2)".
10. [Field Vs Lab Fitness](projects/field-vs-lab-fitness.md) — REPORT.md › "Genes Important for Field Conditions Are Significantly More Conserved (NB03)".
11. [Conservation Fitness Synthesis](projects/conservation-fitness-synthesis.md) — REPORT.md › "The Paradox".
12. [Conservation Fitness Synthesis](projects/conservation-fitness-synthesis.md) — REPORT.md › "What We Did Not Find".
13. [Essential Metabolome](projects/essential-metabolome.md) — REPORT.md › "High Conservation of Amino Acid Biosynthesis Pathways".
14. [Essential Metabolome](projects/essential-metabolome.md) — REPORT.md › "Near-Universal Amino Acid Biosynthesis".
15. [Nmdc Community Metabolic Ecology](projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 1 — Black Queen dynamics are detectable at community scale".
16. [Nmdc Community Metabolic Ecology](projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 3 — Amino acid pathway completeness differs across ecosystem types for 17 of 18 pathways".
17. [Openness Functional Composition](projects/openness-functional-composition.md) — RESEARCH_PLAN.md › "Hypothesis".
18. [Pangenome Pathway Geography](projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
19. [Pseudomonas Carbon Ecology](projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 4: The Aeruginosa-Fluorescens Split Dominates Carbon Pathway Variation".
20. [Pseudomonas Carbon Ecology](projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Novel Contribution".
21. [Genotype To Phenotype Enigma](projects/genotype-to-phenotype-enigma.md) — README.md › "Key Lessons Learned".
22. [Genotype To Phenotype Enigma](projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Executive Summary".
23. [Amr Pangenome Atlas](projects/amr-pangenome-atlas.md) — REPORT.md › "6. AMR Genes Are Not a Fitness Burden in Lab Conditions".
24. [Amr Fitness Cost](projects/amr-fitness-cost.md) — REPORT.md › "1. Universal cost of resistance across 25 bacterial species (H1 supported)".
25. [Amr Fitness Cost](projects/amr-fitness-cost.md) — REPORT.md › "The cost of resistance is universal but uniform".
26. [Amr Fitness Cost](projects/amr-fitness-cost.md) — REPORT.md › "Novel Contribution".
27. [Amr Fitness Cost](projects/amr-fitness-cost.md) — REPORT.md › "4. Core and accessory AMR genes have identical fitness costs (H3 not supported)".
28. [Soil Metal Functional Genomics](projects/soil-metal-functional-genomics.md) — REPORT.md › "Interpretation".
29. [Microbeatlas Metal Ecology](projects/microbeatlas-metal-ecology.md) — REPORT.md › "Novel contribution".
30. [Truly Dark Genes](projects/truly-dark-genes.md) — REPORT.md › "Finding 5: Truly dark genes are enriched in accessory genomes and show HGT signatures (H3 supported)".
31. [Cog Analysis](projects/cog-analysis.md) — REPORT.md › "Composite COG Categories Are Biologically Meaningful".
32. [Prophage Ecology](projects/prophage-ecology.md) — REPORT.md › "3. Tail, head, and anti-defense modules are enriched in human-associated environments beyond phylogenetic expectation".
33. [Snipe Defense System](projects/snipe-defense-system.md) — REPORT.md › "2. SNIPE is widespread (1,696 species, 33 phyla)".
34. [Snipe Defense System](projects/snipe-defense-system.md) — REPORT.md › "1. SNIPE resolves the phage resistance vs. metabolic cost trade-off".
35. [Prophage Amr Comobilization](projects/prophage-amr-comobilization.md) — REPORT.md › "Novel Contribution".
36. [Functional Dark Matter](projects/functional-dark-matter.md) — REPORT.md › "Finding 1: One in four bacterial genes is functionally dark, and 17,344 have experimentally measurable phenotypes".
37. [Truly Dark Genes](projects/truly-dark-genes.md) — REPORT.md › "Finding 1: Only 16.3% of "dark matter" resists modern annotation".
38. [Enigma Sso Asv Ecology](projects/enigma-sso-asv-ecology.md) — REPORT.md › "Novel Contribution".
39. [Enigma Sso Asv Ecology](projects/enigma-sso-asv-ecology.md) — REPORT.md › "The Contamination Plume Model".
40. [Lab Field Ecology](projects/lab-field-ecology.md) — REPORT.md › "Novel Contribution".
41. [Lab Field Ecology](projects/lab-field-ecology.md) — REPORT.md › "Genus Abundance Correlates with Uranium -- in Both Directions".
42. [Env Embedding Explorer](projects/env-embedding-explorer.md) — REPORT.md › "What do AlphaEarth embeddings represent?".
43. [Cf Formulation Design](projects/cf-formulation-design.md) — REPORT.md › "Summary".
44. [Cf Formulation Design](projects/cf-formulation-design.md) — REPORT.md › "Summary".
45. [Cf Formulation Design](projects/cf-formulation-design.md) — REPORT.md › "Summary".
46. [Ibd Phage Targeting](projects/ibd-phage-targeting.md) — REPORT.md › "NB16 — Patient 6967 longitudinal stability + state-dependent dosing strategy".
47. [Pgp Pangenome Ecology](projects/pgp-pangenome-ecology.md) — REPORT.md › "H3 REJECTED — PGP genes are predominantly core, not accessory: vertical inheritance dominates".
48. [Amr Cofitness Networks](projects/amr-cofitness-networks.md) — REPORT.md › "Limitations".
49. [Acinetobacter Adp1 Explorer](projects/acinetobacter-adp1-explorer.md) — REPORT.md › "2. Strong BERDL Connectivity: 4 of 5 Connection Types at >90% Match".

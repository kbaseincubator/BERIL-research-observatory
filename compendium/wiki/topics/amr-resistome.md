# Amr Resistome

The **resistome** is the complete collection of antibiotic resistance genes (ARGs) — and the genetic potential to develop resistance — carried by a bacterium or a microbial community. This wiki page synthesizes what nine research projects in the BERDL corpus collectively reveal about the distribution, ecology, fitness consequences, and mobility of resistance genes across the bacterial tree of life. It exists because AMR is one of the most pressing public-health challenges of the century, and because these projects, taken together, yield a more coherent picture than any single project provides alone: resistance genes are largely accessory traits shaped by ecology, carry small but real fitness costs, travel with prophages, and form tightly co-inherited genomic islands — observations with direct implications for surveillance strategy and antibiotic stewardship.

## Overview

A fundamental insight running through every project in this corpus is that AMR genes are not evenly distributed across bacterial genomes or across ecosystems. At the broadest scale, AMR genes are markedly depleted from the core genome of bacterial species: across 14,723 species, only 30.3% of AMR gene clusters are core (present in ≥95% of genomes), compared to a 46.8% baseline for the pangenome as a whole, yielding an odds ratio of 0.49 [\[1\]](#references). This depletion is consistent across species — 63.7% of tested species show AMR less core than their own pangenome baseline [\[2\]](#references) — and it is quantified here for the first time simultaneously across bacteria on this scale [\[3\]](#references).

Within that overall depletion there is a sharp mechanistic dichotomy. Intrinsic resistance genes — those that are part of a species' chromosomal heritage — behave very differently from acquired genes brought in by horizontal gene transfer (HGT). Beta-lactamases present in the chromosomal backbone of a species are 54.9% core, while known mobile elements such as blaTEM, tet(C), and ant(2'')-Ia are 0% core [\[4\]](#references). The mechanism strongly predicts where in the pangenome a gene sits: metal resistance genes are 44% accessory, while efflux pump and enzymatic inactivation genes are overwhelmingly core — yet this does not predict how costly the gene is metabolically [\[5\]](#references).

## What the Corpus Shows

### Distribution and ecology

Clinical and human-associated bacteria carry far more AMR genes than environmental species. Across 14,723 species, human/clinical species carry 10.6 AMR clusters per species compared to 4.6 for soil and 3.9 for aquatic species [\[6\]](#references), and their resistance is less deeply embedded in the core genome (30.8% core) than soil AMR (58.1% core). A second analysis covering 14,723 species finds clinical bacteria carry 2.5× more AMR gene clusters than environmental species (median 5 versus 2), a pattern that survives phylogenetic control — 20 of 141 testable bacterial families show significant within-family environment effects [\[7\]](#references) [\[8\]](#references).

Mechanism composition varies strongly by environment. Metal resistance (gene families for mercury, arsenic, and other heavy metals) accounts for ~44–45% of AMR in soil and aquatic species but only 6% in human gut species [\[9\]](#references). Mercury resistance genes alone account for roughly 18% of all AMR annotations in the pan-bacterial census [\[10\]](#references). This pattern has an ecological explanation: efflux pump genes are core in host-associated organisms because they provide broad-condition defense across environments, while metal resistance genes are accessory because they are only needed when metal concentrations are high [\[11\]](#references).

Environmental diversity also matters at a finer grain. AlphaEarth embedding analysis — where each genome is represented as a vector capturing its environmental context — shows that species sampled from more diverse environments accumulate more AMR genes (Spearman rho = 0.466) [\[12\]](#references), and continuous environmental-distance metrics confirm the discrete ecology findings via Mantel test (r = 0.098, p = 0.001) [\[13\]](#references). The implication is that niche breadth enables resistance accumulation: more diverse environments mean more opportunities for HGT and more selective pressures to retain a wider repertoire of defense genes.

### Within-species variation and phylogenetic signal

Most AMR genes are not universal even within a single species. Across 1,305 species and 180,025 genomes, 51.3% of AMR gene-species occurrences are rare (present in ≤5% of strains), 41.3% are variable, and only 7.5% are fixed [\[14\]](#references). This is the first systematic quantification across more than 1,300 species simultaneously [\[15\]](#references). Despite the variability, AMR repertoires are not randomly distributed across the phylogenetic tree: 55.6% of species show significant phylogenetic signal in their AMR profiles by Mantel test [\[16\]](#references). Counterintuitively, acquired (non-core) genes show stronger phylogenetic signal (median Mantel r = 0.222) than intrinsic (core) genes (r = 0.117) [\[17\]](#references). This means that once a lineage acquires a resistance element, it tends to be stably maintained and clonally transmitted rather than frequently exchanged.

Roughly one in five species (19.5% of 974 species with sufficient genomes) form two or more distinct AMR ecotypes — clusters of strains sharing a coherent resistance repertoire [\[18\]](#references). AMR genes are also organized into tightly co-inherited resistance islands: 1,517 such islands were detected across 54% of analyzed species, with a mean phi coefficient of 0.827 indicating very tight co-occurrence [\[19\]](#references). Most of these islands (88%) combine genes from multiple resistance mechanisms, dominated by efflux pumps and enzymatic inactivation, providing coordinated defense against multiple drug classes simultaneously [\[20\]](#references). The atlas-derived conservation class strongly predicts within-species prevalence: 77.3% of Core AMR genes are fixed within species and 78.7% of Singletons are rare, validating that the core/accessory distinction captures real biological variation [\[21\]](#references).

### Fitness cost of resistance

RB-TnSeq (randomly barcoded transposon sequencing) is a high-throughput technique that measures the fitness effect of knocking out each gene by tracking barcode frequencies in a pool of mutants. Across 25 bacterial species and 27 million fitness measurements, this first pan-bacterial meta-analysis of AMR fitness costs finds a consistent, universal result: AMR gene knockouts have systematically higher fitness than non-AMR gene knockouts under non-antibiotic conditions, with a pooled meta-analytic effect of +0.086 fitness units [\[22\]](#references) [\[23\]](#references). The cost is real but small, reconciling why resistance persists long after antibiotic withdrawal while also declining under sustained stewardship [\[24\]](#references).

Surprisingly, the cost does not vary by resistance mechanism (Kruskal-Wallis p = 0.89 across efflux, enzymatic inactivation, and metal resistance) [\[25\]](#references). A uniform "floor" of metabolic overhead appears to apply regardless of how the gene confers resistance. The most parsimonious explanation is that only AMR genes already minimized through compensatory evolution persist in these genomes [\[26\]](#references). Core and accessory AMR genes show virtually identical fitness distributions (Cohen's d = 0.002), suggesting that horizontal transfer preferentially captures genes already cost-optimized in the donor lineage, or that the receiving genome compensates rapidly [\[27\]](#references) [\[28\]](#references). Only 4.6% of AMR genes are putatively essential (absent from fitness matrices), far below the ~14% genome-wide rate, confirming that resistance genes are more dispensable than typical genes [\[29\]](#references).

The picture shifts when antibiotics are present. Under antibiotic conditions, 57% of AMR genes show a "fitness flip" — they become relatively more important rather than burdensome — and this flip is mechanism-dependent: broad-spectrum efflux genes flip much more strongly than narrow-spectrum enzymatic inactivation genes (+0.094 vs −0.001, p = 0.007) [\[30\]](#references) [\[31\]](#references).

### Co-fitness networks and gene co-regulation

ICA (independent component analysis) modules extracted from Fitness Browser data capture groups of genes that vary together in fitness across conditions. AMR genes that fall into such modules (only 24% of AMR genes do) reside in modules that are significantly larger than non-AMR modules (median 46 vs 27 genes), placing them within large multi-function cellular programs [\[32\]](#references). Nearly all of these module assignments fall in cross-organism conserved module families, indicating ancient co-regulatory relationships [\[33\]](#references). This work represents the first pan-bacterial mapping of AMR co-fitness neighborhoods across 28 organisms [\[34\]](#references).

The functional enrichment of AMR support networks reveals flagellar motility and amino acid biosynthesis as the top GO-term categories [\[35\]](#references). Crucially, support networks are organism-specific rather than mechanism-specific: different AMR mechanisms within one organism share more cofitness partners (Jaccard 0.375) than the same mechanism across organisms (Jaccard 0.207), revealing that each organism's regulatory landscape shapes the network far more than the resistance mechanism itself [\[36\]](#references) [\[37\]](#references).

### Prophage co-mobilization

Prophages (viral genomes that integrate into the bacterial chromosome and can later excise and spread) are strongly correlated with AMR breadth across the bacterial tree. A pangenome-scale analysis — the first of its kind across 100 species, 1,953 genomes, and 36,041 AMR gene instances — found that over half (55.7%) of AMR gene instances in the most AMR-burdened species reside on contigs that also carry strict prophage markers [\[38\]](#references) [\[39\]](#references). Species with higher prophage marker density carry significantly broader AMR gene repertoires (Spearman rho = 0.572), explaining approximately 30% of variance in AMR breadth [\[40\]](#references). This association holds after controlling for genome count and is consistent across all five major phyla [\[41\]](#references). The pattern extends prior work from ~100 pangenomes to 4,770 species [\[42\]](#references). Two non-exclusive mechanisms are plausible: prophages directly mobilize resistance genes via transduction, or species with high recombination potential independently accumulate both [\[43\]](#references). Census data confirm the scale: 83,008 AMR gene clusters and 3.47 million prophage marker clusters identified, with 14,669 of 27,702 species carrying both [\[44\]](#references).

## Projects and Evidence

Nine projects contribute to this topic. **amr_pangenome_atlas** provides the broadest census, mapping 83,008 AMR clusters across 14,723 species using uniform annotation (Bakta + AMRFinderPlus), and discovering that Gammaproteobacteria carry 45% of all AMR clusters, with Klebsiella topping genus-level density at 206 AMR clusters per species [\[45\]](#references). Functional annotation shows COG V (Defense mechanisms) is 7.05× enriched in AMR genes and COG P (Inorganic ion transport) 1.93× enriched, the latter driven by mercury and arsenic resistance gene families [\[46\]](#references).

**amr_fitness_cost** uses RB-TnSeq data from the Fitness Browser across 25 organisms to quantify the metabolic burden of carrying AMR genes under non-antibiotic conditions. The key result — a universal but uniform cost of +0.086 fitness units — is consistent with the observation that in the Fitness Browser organisms (predominantly environmental strains), AMR genes appear slightly less costly than the non-AMR baseline [\[47\]](#references). The difference between these results and the +0.086 finding hinges on the exact organisms and gene sets used: the environmental FB strains likely carry well-integrated intrinsic resistance genes rather than recently acquired mobile elements.

**amr_environmental_resistome** examines the ecological gradient in AMR composition, finding the core-versus-accessory split ranges from 57% core in soil to 32% core in clinical species [\[48\]](#references).

**amr_strain_variation** delivers the strain-level view across 1,305 species and 180,025 genomes, showing that clonal lineage tracking may be more informative for AMR surveillance than tracking individual genes [\[49\]](#references).

**amr_cofitness_networks** maps how AMR genes are co-regulated with the rest of the genome using ICA modules and cofitness networks across 28 organisms, finding organism-specific rather than mechanism-specific regulatory neighborhoods.

**prophage_amr_comobilization** establishes the prophage-AMR breadth correlation at pangenome scale.

**field_vs_lab_fitness** contributes the observation that antibiotic-resistance and heavy-metal-resistance genes are the least conserved functional categories in the genome (73.4% and 71.2% core respectively, below baseline), consistent with recent acquisition via mobile genetic elements [\[50\]](#references).

**microbeatlas_metal_ecology** shows that metal AMR traits have intermediate phylogenetic signal (Pagel's λ = 0.26–0.44), consistent with a model of vertically inherited constitutive resistance overlaid by HGT-driven accessory expansion [\[51\]](#references).

**resistance_hotspots** is a planned project targeting AMR hotspots across 293,059 genomes in 27,690 species, proposing to test whether open pangenomes accumulate more ARG diversity and to integrate fitness data from the Fitness Browser [\[52\]](#references) [\[53\]](#references). As of this writing, the project is in the planning stage with skeleton code only [\[54\]](#references) [\[55\]](#references).

## Connections

This topic connects tightly to [Pangenome Architecture](../topics/pangenome-architecture.md), because the core/accessory distinction is the primary lens through which AMR gene conservation is understood — the depletion of AMR from the core genome is itself a pangenome-scale result. The link to [Mobile Genetic Elements](../topics/mobile-genetic-elements.md) is direct: resistance islands, prophage co-mobilization, and the low core fraction of acquired resistance genes all implicate horizontal transfer and mobile element biology as the main drivers of AMR diversity. The [Metal Resistance](../topics/metal-resistance.md) page is adjacent because metal resistance genes constitute a major fraction of the AMR census (mercury alone is ~18% of all hits) and show distinctly different ecological and phylogenetic patterns from antibiotic resistance genes proper.

The connection to [Gene Fitness](../topics/gene-fitness.md) is central: the RB-TnSeq (transposon fitness) framework used to measure AMR gene fitness costs is the same framework used across the broader fitness corpus. The [Microbial Ecotypes](../topics/microbial-ecotypes.md) page is relevant because distinct AMR ecotypes detected within species are likely the within-species manifestation of the ecological gradients described at the species level. The [Environment Biogeography](../topics/environment-biogeography.md) page covers the broader biogeographic patterns of which the AMR ecology findings are a specific example. Finally, [Microbiome Engineering](../topics/microbiome-engineering.md) and [Subsurface Genomics](../topics/subsurface-genomics.md) provide environmental context for why metal resistance dominates AMR in non-clinical habitats.

## Caveats and Open Directions

Several important caveats temper these findings. The "clinical species carry more AMR" result is partly confounded by NCBI sampling bias: clinical isolates are massively overrepresented in public databases, and clinical species are sequenced precisely because they have AMR [\[56\]](#references) [\[57\]](#references). Effect sizes for the ecology findings are modest — environment explains only 2–13% of variance in AMR composition, with phylogeny likely explaining much more [\[58\]](#references). The temporal analysis found no significant trends in AMR accumulation, but this null result probably reflects sparse and noisy NCBI collection-date metadata rather than a biological absence of trends [\[59\]](#references).

For the fitness cost analysis, all 25 organisms are lab-adapted strains; compensatory evolution during laboratory maintenance may have reduced measurable costs below those in wild populations, meaning the +0.086 estimate may be a lower bound relative to natural settings [\[60\]](#references). The ~4.6% of AMR genes absent from fitness matrices because they are putatively essential also makes the cost estimate a lower bound if those censored genes are the most costly [\[61\]](#references). The core/accessory cost comparison is further hampered by imprecise core labels for organisms with few genomes in the BERDL collection (median 9 per species in the Fitness Browser) [\[62\]](#references).

For the co-fitness network enrichment, the flagellar and biosynthesis signal may reflect shared dispensability under lab conditions rather than genuine co-regulation — flagellar genes and AMR genes are both metabolic burdens that are irrelevant in shaken liquid culture [\[63\]](#references). A fitness-matched permutation test (drawing random genes with the same slightly-positive fitness distribution) is needed to distinguish true co-regulation from shared dispensability [\[64\]](#references). Computing cofitness separately for antibiotic versus standard growth conditions would further disambiguate [\[65\]](#references).

For the prophage co-mobilization, the species-level correlation does not prove phage-mediated AMR transfer; open-pangenome species may independently accumulate both prophages and AMR genes [\[66\]](#references). The fitness cost hypothesis (whether prophage-proximal AMR genes are costlier or cheaper) could not be tested because the Fitness Browser covers only 48 model organisms with insufficient overlap with the GTDB pangenome species analyzed [\[67\]](#references), though it can be revisited as fitness browser coverage expands [\[68\]](#references).

Mechanism classification remains incomplete: keyword-based approaches leave 22% of AMR hits as Other/Unclassified, and AMRFinderPlus includes stress-response genes (mercury, arsenic) alongside classical antibiotic resistance, so the headline census numbers are not purely "antibiotic" resistance [\[69\]](#references). Replacing keyword matching with systematic CARD Antibiotic Resistance Ontology (ARO) mapping is a high-priority future direction [\[70\]](#references).

Key open directions include: integrating NMDC/MGnify metagenomes to test whether accessory AMR genes seen in isolate genomes are also prevalent in community DNA [\[71\]](#references); cross-referencing metal resistance genes with the metal fitness atlas project to ask whether genes costly under standard conditions are protective under metal stress [\[72\]](#references); using resistance island co-occurrence structure to predict likely future co-acquisitions [\[73\]](#references); and when mobile genetic element annotations become available in BERDL, testing whether accessory AMR clusters in clinical species are preferentially associated with plasmids versus phages versus integrative elements [\[74\]](#references).

## References

1. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "1. AMR Genes Are Massively Depleted from the Core Genome".
2. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "1. AMR Genes Are Massively Depleted from the Core Genome".
3. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "The Intrinsic-Acquired Dichotomy".
4. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "2. Intrinsic vs Acquired Resistance Creates a Conservation Dichotomy".
5. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "5. Mechanism is strongly associated with conservation, even though cost is not".
6. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "5. Clinical Species Carry 2.7x More AMR — and It's More Acquired".
7. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "1. Clinical species carry 2.5× more AMR gene clusters than environmental species (H1 supported)".
8. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "5. Phylogenetic control confirms environment effects are real".
9. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "3. Resistance mechanism composition is strongly environment-dependent (H3 supported)".
10. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "Heavy Metal Resistance Is a Major AMR Component".
11. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "3. Resistance mechanism composition is strongly environment-dependent (H3 supported)".
12. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "5. Clinical Species Carry 2.7x More AMR — and It's More Acquired".
13. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "6. AlphaEarth continuous environment embeddings confirm discrete findings (supplementary)".
14. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 1: The majority of AMR genes are variable or rare within species".
15. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Novel Contribution".
16. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 3: AMR variation tracks phylogeny in the majority of species — but acquired genes show stronger signal than intrinsic".
17. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 3: AMR variation tracks phylogeny in the majority of species — but acquired genes show stronger signal than intrinsic".
18. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 4: One in five species has distinct AMR ecotypes".
19. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 2: Resistance islands are widespread and tightly co-inherited".
20. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 2: Resistance islands are widespread and tightly co-inherited".
21. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 1: The majority of AMR genes are variable or rare within species".
22. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "1. Universal cost of resistance across 25 bacterial species (H1 supported)".
23. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Novel Contribution".
24. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "The cost of resistance is universal but uniform".
25. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "3. Resistance mechanism does not predict fitness cost (H2 not supported)".
26. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "3. Resistance mechanism does not predict fitness cost (H2 not supported)".
27. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "4. Core and accessory AMR genes have identical fitness costs (H3 not supported)".
28. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "4. Core and accessory AMR genes have identical fitness costs (H3 not supported)".
29. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "1. Universal cost of resistance across 25 bacterial species (H1 supported)".
30. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "2. AMR genes become more important under antibiotic pressure (H4 partially supported)".
31. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "2. AMR genes become more important under antibiotic pressure (H4 partially supported)".
32. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "1. AMR genes are embedded in larger-than-average co-regulated modules".
33. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "1. AMR genes are embedded in larger-than-average co-regulated modules".
34. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Novel Contribution".
35. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "2. AMR support networks are enriched for flagellar motility and amino acid biosynthesis (H1 supported)".
36. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "3. Support networks are organism-specific, not mechanism-specific".
37. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Organism regulatory architecture trumps resistance mechanism (robust finding)".
38. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Finding 1: AMR genes frequently share contigs with prophage markers".
39. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Novel Contribution".
40. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Finding 3: Prophage density strongly predicts AMR repertoire breadth (H2)".
41. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Finding 3: Prophage density strongly predicts AMR repertoire breadth (H2)".
42. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Literature Context".
43. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Interpretation".
44. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Finding 1: AMR genes frequently share contigs with prophage markers".
45. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "3. AMR Hotspots Are Concentrated in Clinical Pathogens".
46. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "4. AMR Genes Are Enriched in Defense and Ion Transport Functions".
47. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "6. AMR Genes Are Not a Fitness Burden in Lab Conditions".
48. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "2. Clinical species have predominantly acquired resistance; soil/aquatic species have more intrinsic resistance (H2 supported)".
49. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Novel Contribution".
50. [Field Vs Lab Fitness](../projects/field-vs-lab-fitness.md) — REPORT.md › "Key Biological Insight".
51. [Microbeatlas Metal Ecology](../projects/microbeatlas-metal-ecology.md) — REPORT.md › "Finding 2: Metal AMR traits show intermediate phylogenetic signal — consistent with mixed vertical inheritance and HGT".
52. [Resistance Hotspots](../projects/resistance-hotspots.md) — README.md › "Research Question".
53. [Resistance Hotspots](../projects/resistance-hotspots.md) — RESEARCH_PLAN.md › "Primary Collections".
54. [Resistance Hotspots](../projects/resistance-hotspots.md) — REVIEW.md › "Summary".
55. [Resistance Hotspots](../projects/resistance-hotspots.md) — REVIEW.md › "No Findings to Assess".
56. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "Limitations".
57. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "Limitations".
58. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "Limitations".
59. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Finding 5: No significant temporal trends in AMR accumulation after multiple-testing correction".
60. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
61. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
62. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Limitations".
63. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "2. AMR support networks are enriched for flagellar motility and amino acid biosynthesis (H1 supported)".
64. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Future Directions".
65. [Amr Cofitness Networks](../projects/amr-cofitness-networks.md) — REPORT.md › "Future Directions".
66. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Limitations".
67. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Finding 4: Fitness cost comparison not testable (H3)".
68. [Prophage Amr Comobilization](../projects/prophage-amr-comobilization.md) — REPORT.md › "Future Directions".
69. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "Limitations".
70. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "Future Directions".
71. [Amr Pangenome Atlas](../projects/amr-pangenome-atlas.md) — REPORT.md › "Future Directions".
72. [Amr Fitness Cost](../projects/amr-fitness-cost.md) — REPORT.md › "Future Directions".
73. [Amr Strain Variation](../projects/amr-strain-variation.md) — REPORT.md › "Future Directions".
74. [Amr Environmental Resistome](../projects/amr-environmental-resistome.md) — REPORT.md › "Future Directions".

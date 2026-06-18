# Metabolic Pathways

Metabolic pathways are the enzyme-catalyzed reaction sequences that allow bacteria to build cellular components (biosynthesis), extract energy from nutrients (catabolism), and recycle cofactors. This page exists in the wiki because metabolic pathway content — which pathways a genome encodes, which it actually uses under different conditions, and which it has lost — is the single most common substrate of inference across the corpus. Nearly every project, from single-organism physiology to cross-ecosystem metagenomics, touches pathway presence, completeness, or fitness importance. Understanding the shared vocabulary of pathway logic is therefore the entry point to reading almost anything else in this collection.

## Overview

The corpus approaches metabolic pathways from three interlocking angles: **conservation** (which pathways are core vs. accessory across lineages), **condition-dependence** (which are actually used vs. silently encoded), and **community context** (how pathway distributions shape ecological interactions). A recurring tool is **GapMind**, a database that scores the completeness of defined metabolic pathways (amino acid biosynthesis, carbon catabolism) in a genome by searching for each enzymatic step; a genome with all steps present gets a high completeness score, while missing steps leave "gaps." Closely related is **flux balance analysis (FBA)**, a computational method that simulates steady-state metabolic flux through a genome-scale model to predict which genes are essential for growth on a given medium. **RB-TnSeq** (randomized barcoded transposon-insertion sequencing) is the high-throughput experimental counterpart: it measures the competitive fitness of thousands of single-gene deletion mutants in parallel, providing direct evidence of which genes matter under specific conditions.

A key finding cutting across many projects is that **pathway completeness does not equal pathway dependence**. Of 161 organism-pathway pairs in a model-organism study, only 35.4% were "Active Dependencies" — pathways where gene loss measurably reduces fitness. An additional 41.0% were genomically complete but fitness-neutral "Latent Capabilities" [\[1\]](#references). Across a broader dataset of 1,695 pathway-organism pairs from 48 organisms, 15.8% of genomically complete pathways were latent, and all latent pairs became fitness-important under at least one condition (most often nitrogen limitation, stress, or carbon limitation), reframing latency as context-dependence rather than genomic baggage [\[2\]](#references) [\[3\]](#references).

## What the Corpus Shows

### Amino acid biosynthesis: conserved and ancestral, yet ecologically labile

Amino acid biosynthesis is the most conserved class of metabolic capability. In a seven-organism pilot study, 17 of 18 amino acid biosynthesis pathways were present in all organisms, and the presence of complete pathways in 6 of 7 organisms suggests amino acid prototrophy (the ability to synthesize all amino acids from scratch) is the ancestral state for free-living bacteria [\[4\]](#references) [\[5\]](#references). No pathway is 100% universal even in this small sample — GapMind predictions are "near-universal rather than strictly universal" with organism-specific gaps [\[6\]](#references). The single exception in that dataset is *Desulfovibrio vulgaris Hildenborough*, which appears to lack a complete serine biosynthesis pathway and may be serine-auxotrophic (i.e., unable to grow without an external serine supply) — a plausible ecological economy in its amino-acid-rich anaerobic habitat [\[7\]](#references) [\[8\]](#references).

At the community scale, amino acid pathway community-completeness scores differ significantly across ecosystem types: 17 of 18 amino acid pathways show significantly different completeness levels between soil and freshwater metagenomes (only tyrosine is not differentiated) [\[9\]](#references). This ecosystem-level patterning is consistent with the **Black Queen Hypothesis** (BQH) — the idea that when an essential metabolite is reliably supplied by community members, individual organisms lose the costly genes to make it themselves. Across 13 testable amino acid biosynthesis pathways, 11 (85%) showed negative correlations between community GapMind completeness and ambient amino acid metabolite intensity, the direction predicted by BQH [\[10\]](#references). Leucine and arginine were the two pathways reaching FDR significance, both energetically expensive to synthesize [\[11\]](#references) [\[12\]](#references).

Evidence for BQH also appears at the genome-dynamics level: the contrast between supported clade-level pangenome openness and unsupported per-pathway conservation rates suggests the BQH signal operates at the level of genome dynamics and community context rather than per-pathway cross-genome conservation ratios [\[13\]](#references). At the strain level, amino acid biosynthesis pathways (leucine, valine, arginine, lysine, threonine) show the strongest dependence on accessory genes, with core-vs-all completeness gaps of ~0.14 — direct evidence that biosynthetic capacity is distributed across strains in the public-goods manner BQH predicts [\[14\]](#references).

### Carbon catabolism: the primary ecological axis

Carbon source utilization pathways load almost entirely on the first principal component (PC1) when PCA is applied to a 220-sample cross-habitat community completeness matrix (49.4% variance in PC1), with soil and freshwater communities occupying nearly non-overlapping PC space [\[15\]](#references) [\[16\]](#references). This places carbon substrate variation — rather than amino acid variation — as the primary ecological differentiator of microbial communities.

Within the *Pseudomonas* genus, the most dramatic carbon-pathway contrast separates the *P. aeruginosa* lineage (Pseudomonas sensu stricto) from the *Pseudomonas*\_E subgenus (*P. fluorescens* group): 43 of 62 GapMind carbon pathways differ significantly, driven by near-complete loss of plant-derived sugar catabolism (xylose, arabinose, myo-inositol: 0% complete in *P. aeruginosa* vs. 59–74% in *P. fluorescens*) [\[17\]](#references) [\[18\]](#references). Notably, this is ancestral streamlining at the lineage level rather than losses acquired during chronic infection: the absent pathways were already absent across thousands of *P. aeruginosa* genomes before any clinical isolate context [\[19\]](#references). Amino acid catabolism (arginine, histidine, serine, glutamate, citrate) remains near-universal (>99%) in both subgenera [\[20\]](#references). Free-living and plant-associated species maintain higher carbon pathway richness (median 57 pathways) than host-associated species (median 55) [\[21\]](#references).

The concept of **latent capabilities** is particularly striking for carbon pathways: carbon source utilization pathways are 3.7-fold more likely to be latent (24.3% latent) than amino acid biosynthesis pathways (6.5% latent) [\[22\]](#references) [\[23\]](#references). This makes intuitive sense — an organism that carries but rarely needs a specific carbon catabolic pathway may maintain it as "metabolic insurance" for rare substrate encounters, while amino acid biosynthesis must always be available unless a community partner reliably provides the amino acid.

### Respiratory chain wiring: condition-dependent, not transcriptionally regulated

*Acinetobacter baylyi* ADP1 carries three parallel NADH dehydrogenases with distinct condition profiles: Complex I (NADH:ubiquinone oxidoreductase, the primary energy-conserving complex), NDH-2 (an alternative NADH dehydrogenase that does not pump protons), and ACIAD3522 (specifically lethal on acetate) [\[24\]](#references). Strikingly, all three are constitutively co-expressed at similar protein levels — the condition-specific respiratory wiring operates as a passive flux-based system at the metabolic level rather than an active transcriptional switch [\[25\]](#references). This means ADP1 uses qualitatively different respiratory configurations for each carbon source [\[26\]](#references).

A key finding is the **rate-vs-yield principle**: aromatic substrates such as quinate, despite yielding fewer total NADH per carbon than simpler substrates, create a concentrated TCA-cycle NADH burst (from β-ketoadipate pathway ring cleavage) that exceeds NDH-2's reoxidation capacity, making Complex I obligatory [\[27\]](#references) [\[28\]](#references). The β-ketoadipate pathway — which converts aromatic ring compounds through protocatechuate and catechol to TCA-cycle intermediates — therefore imposes a specific dependency on Complex I not because aromatics produce more NADH overall, but because they produce it in a burst. FBA misses this entirely: it predicts zero flux through NDH-2 and ACIAD3522 on all standard media because it optimizes for growth rate and routes NADH through the more ATP-efficient Complex I, illustrating a systematic FBA blind spot for capacity constraints [\[29\]](#references).

### Aromatic catabolism: a support network hidden from standard models

Aromatic (quinate) catabolism in ADP1 requires a 51-gene support network beyond the core β-ketoadipate pathway itself, organized into four functional subsystems [\[30\]](#references). Complex I alone accounts for 21 of these 51 quinate-specific genes (41%) [\[31\]](#references). Three β-ketoadipate pathway steps create specific support dependencies: a PQQ-dependent quinate dehydrogenase (requiring PQQ biosynthesis genes), an Fe²⁺-dependent protocatechuate 3,4-dioxygenase (requiring iron acquisition), and TCA-cycle oxidation steps (requiring Complex I) [\[32\]](#references). These four support subsystems occupy distinct chromosomal locations with no cross-category operons — the metabolic dependency emerges from biochemistry, not genomic co-localization [\[33\]](#references).

Aromatic degradation genes are strongly enriched among genes where FBA predictions and TnSeq observations disagree (OR=9.70, q=0.012), and 30 of the 51 quinate-specific genes have no FBA reaction mappings at all [\[34\]](#references) [\[35\]](#references). This is partly because FBA models typically assume minimal media with simple carbon sources, while aromatic catabolism requires trace aromatic compounds; adding such compounds to the in silico media definition could reduce this discordance [\[36\]](#references).

### Cross-genome annotation gaps in metabolic reactions

Resolving which gene catalyzes which metabolic reaction is a persistent gap. An annotation gap discovery project integrating five evidence streams (gapfilling, fitness data, pangenome context, GapMind pathway predictions, and BLAST homology) resolved 47.8% (96 of 201) of gapfilled enzymatic reaction–organism pairs with candidate genes, exceeding a pre-specified 30% threshold [\[37\]](#references). No single evidence stream reached more than 35%; the full integrated pipeline added 13 percentage points over BLAST alone [\[38\]](#references). Branched-chain amino acid (BCAA) biosynthesis reactions dominated the high-confidence resolutions, with two reactions (rxn02185 and rxn03436) resolved in 9 of 14 organisms each [\[39\]](#references). The 50 EC-less "dark reactions" (reactions with no known EC number) remain the hardest targets, resolved only 16% of the time versus 58% for reactions with known EC numbers [\[40\]](#references).

A baseline FBA run across 574 organism-carbon source combinations showed 42.5% accuracy with high recall (86.5%) but low precision (42.5%), reflecting overly permissive draft models that over-predict growth [\[41\]](#references). This asymmetry is partly explained by gapfilling: 87% of 121,519 growth phenotype predictions rely on at least one gapfilled reaction, tightly coupling prediction accuracy to gapfilling quality [\[42\]](#references).

### Polyhydroxybutyrate (PHB) as a metabolic storage strategy

Polyhydroxybutyrate (PHB) is a carbon-storage polymer synthesized by many bacteria when carbon is abundant but growth is nutrient-limited. Across 27,690 GTDB species, 21.9% carry the PHA synthase gene (*phaC*) and 21.7% have a complete PHB biosynthesis pathway — the first precise pan-bacterial prevalence estimate [\[43\]](#references). PHB prevalence follows a >10-fold gradient from temporally variable environments (plant 44%, soil 43.6%) to stable host-associated environments (clinical 7.4%, animal 3.3%), supporting the hypothesis that environmental variability selects for storage capacity [\[44\]](#references). PHB distribution is phylogenetically concentrated, with Pseudomonadota alone accounting for 74.9% of *phaC*-carrying species [\[45\]](#references).

### Subsurface and anaerobic metabolic toolkits

In deep clay-confined subsurface environments, cultured isolates jointly carry the Wood-Ljungdahl pathway (CO₂ fixation) plus group 1 [NiFe]-hydrogenase plus dissimilatory sulfate-reduction toolkit at much higher rates than soil baseline or shallow-clay cohorts (mean toolkit score 1.89 vs. 0.39) [\[46\]](#references). However, a within-phylum control reveals that this signal is largely phylogenetic: Wood-Ljungdahl and [NiFe]-hydrogenase track the Bacillota\_B lineage rather than the deep-clay habitat per se [\[47\]](#references). Only dissimilatory sulfate reduction (dsrAB-aprAB-sat) survives phylogenetic correction, enriched in 5/5 deep Bacillota\_B isolates versus 4/19 soil-baseline Bacillota\_B isolates (OR=infinity, p=0.003) [\[48\]](#references). Separately, the molybdopterin-cofactor orthogroup COG1977 — a cofactor source for anaerobic-respiration enzymes — was present in all ten anchor deep-clay genomes versus only 11 of 62 baseline genomes, marking a strong subsurface-niche signal [\[49\]](#references).

### Pangenome openness and metabolic pathway diversity

Ecological niche breadth (measured by AlphaEarth structural embedding diversity) is the strongest predictor of mean metabolic pathway completeness across 1,872 bacterial species (r=0.392, p=7.1e-70), with embedding variance an even stronger predictor (r=0.412) [\[50\]](#references) [\[51\]](#references). Ecology beats geography: geographic distance alone gives a weaker signal [\[52\]](#references). The number of variable pathways (those not fixed in all strains of a species) correlates with pangenome openness at partial Spearman rho=0.530 (p=2.83e-203) after controlling for genome count [\[53\]](#references). Open pangenomes tend to encode a larger repertoire of metabolic capabilities, consistent with a generalist lifestyle [\[54\]](#references).

## Projects and Evidence

The corpus spans 43 projects contributing to metabolic pathway knowledge. Several clusters of evidence deserve specific mention.

**ADP1 model-system projects** (*acinetobacter\_adp1\_explorer*, *adp1\_triple\_essentiality*, *adp1\_deletion\_phenotypes*, *aromatic\_catabolism\_network*, *respiratory\_chain\_wiring*) together build a multi-resolution portrait of *Acinetobacter baylyi* ADP1. The ADP1 explorer integrates a 15-table SQLite database (461,522 rows) spanning six data modalities including FBA, TnSeq essentiality, proteomics, and growth phenotypes [\[55\]](#references). FBA predictions and TnSeq essentiality agreed for 73.8% of 866 doubly-covered genes [\[56\]](#references). Deletion phenotypes map cleanly to expected pathways: the sole discrete phenotypic module is a set of 24 aromatic-degradation genes with extreme quinate-specific growth defects [\[57\]](#references). Each of 8 carbon sources imposes a largely independent gene requirement set (mean pairwise fitness correlation r=0.44) [\[58\]](#references).

**Metabolic capability dependency projects** (*metabolic\_capability\_dependency*, *pathway\_capability\_dependency*) define and quantify the latent capability framework using RB-TnSeq data from the ENIGMA/Fitness Browser collection. A composite importance score integrating essentiality (40%), fitness breadth (30%), and fitness magnitude (30%) classifies each organism-pathway pair [\[59\]](#references). The fraction of latent capabilities correlates positively with pangenome openness (Spearman rho=0.69, p=0.0004) [\[60\]](#references).

**Community metabolic ecology projects** (*nmdc\_community\_metabolic\_ecology*, *pangenome\_pathway\_geography*, *pangenome\_pathway\_ecology*) scale up to hundreds to thousands of species. The NMDC project provides the first application of GapMind community-weighted pathway completeness scores to cross-habitat environmental metabolomics (305M GapMind records, 220 samples) [\[61\]](#references).

**The Pseudomonas carbon ecology project** (*pseudomonas\_carbon\_ecology*) is the first systematic quantification of carbon pathway profiles across the full *Pseudomonas* genus (433 species, 12,732 genomes) using standardized GapMind predictions [\[62\]](#references). [\[63\]](#references).

**The CF formulation design project** (*cf\_formulation\_design*) demonstrates an applied use of metabolic pathway analysis: designing a five-organism probiotic formulation to competitively suppress *P. aeruginosa* PA14 in cystic fibrosis lungs. The amino acid catabolic pathways targeted are 97.4% conserved across 1,796 lung PA genomes, making the formulation predicted to work broadly across lung variants [\[64\]](#references). Metabolic carbon-source overlap with PA14 significantly predicts commensal inhibition (r=0.384) but explains only ~27% of variance [\[65\]](#references). No single organism outgrows PA14 on any tested carbon substrate, requiring community-level niche coverage [\[66\]](#references).

**Essential metabolome, genotype-to-phenotype, and FW300 metabolic consistency projects** contribute the key insight that production and utilization are distinct metabolic capabilities, and that growth vs. metabolite-production phenotypes require very different feature sets to predict [\[67\]](#references) [\[68\]](#references). Binary growth is predictable from KO gene presence on amino acids (AUC 0.775) and nucleosides (0.780) but not on metals or antibiotics [\[69\]](#references).

**The lanthanide methylotrophy atlas project** (*lanthanide\_methylotrophy\_atlas*) discovers that the lanthanide-dependent methanol dehydrogenase xoxF outnumbers the calcium-dependent mxaF by ~19:1 across 293K genomes [\[70\]](#references), and that the highest per-genome xoxF rates occur in phyla rarely linked to one-carbon metabolism, such as Acidobacteriota at 28.3% [\[71\]](#references).

## Connections

Metabolic pathways is the hub topic in this wiki because it connects to almost every other page. The most direct adjacencies:

- [**Gene Fitness**](../topics/gene-fitness.md): RB-TnSeq fitness data are the primary experimental evidence for pathway dependency vs. latency. Without fitness data, pathway completeness cannot be converted into pathway importance.
- [**Pangenome Architecture**](../topics/pangenome-architecture.md): Pangenome openness and the core/accessory genome split are the structural substrate for understanding why pathways vary across strains and how Black Queen gene loss operates at the genome-dynamics level.
- [**Functional Dark Matter**](../topics/functional-dark-matter.md): Annotation gaps — reactions with no enzyme assignment — are the shadow side of metabolic pathway analysis. The 24.9% of gapfilled reactions that are EC-less represent hard targets for computational and experimental annotation.
- [**Microbial Ecotypes**](../topics/microbial-ecotypes.md): Metabolic ecotypes (within-species pathway heterogeneity) are a documented general feature of diverse bacteria, with all 10 target species showing meaningful metabolic clustering when at least 50 genomes are available [\[72\]](#references).
- [**Subsurface Genomics**](../topics/subsurface-genomics.md): The deep-clay anaerobic toolkit (Wood-Ljungdahl, hydrogenase, sulfate reduction) is a specific metabolic signature of subsurface lineages, linking pathway content to habitat.
- [**Microbiome Engineering**](../topics/microbiome-engineering.md): The CF probiotic formulation design is the clearest example of using metabolic pathway analysis to engineer community composition for therapeutic ends.
- [**Metal Resistance**](../topics/metal-resistance.md): Metal stress (copper, chromium, lead) disrupts specific metabolic pathways — iron-dependent enzymes are particularly vulnerable to iron displacement, and energetic trade-offs under copper stress affect energy production pathways [\[73\]](#references).
- [**Environment Biogeography**](../topics/environment-biogeography.md): Ecosystem type (soil vs. freshwater vs. host-associated) is the dominant driver of metabolic pathway completeness distributions at the community level, making biogeography and metabolic ecology inseparable.
- [**Adp1 Model System**](../topics/adp1-model-system.md): ADP1 is the single organism for which the metabolic pathway analysis is deepest, integrating FBA, TnSeq, proteomics, and deletion phenotypes into a unified multi-omics picture.

Mobile genetic elements (plasmids, transposons) facilitate horizontal gene transfer of metabolic capability, including CAZy polysaccharide-degrading enzymes transferred across phyla via type IV secretion systems — see [**Mobile Genetic Elements**](../topics/mobile-genetic-elements.md) for details [\[74\]](#references).

## Caveats and Open Directions

Several recurring methodological caveats limit the strength of inferences in this area:

**GapMind resolution limits.** GapMind defines 18 amino acid biosynthesis pathways and 62 carbon pathways, but these sets saturate near 18 for cultivable bacteria (limiting resolving power at the upper end) and miss genus-specific catabolic capabilities such as aromatic degradation pathways central to *P. putida* ecology [\[75\]](#references) [\[76\]](#references). GapMind predictions vary in confidence and are probabilistic, not experimental [\[77\]](#references).

**FBA model incompleteness.** Gapfilling introduces circularity: models cannot grow on carbon-source minimal media without gapfilled reactions, making single-gene knockout validation circular [\[78\]](#references). FBA predicts zero essentiality for genes it cannot map to any reaction, creating systematic blind spots for poorly annotated subsystems [\[35\]](#references).

**Genomic potential vs. expression.** GapMind pathway completeness indicates whether biosynthesis genes are present, not whether they are actively expressed [\[79\]](#references). Transcriptomic validation remains a consistently identified next step.

**Condition mismatch between datasets.** The Web of Microbes exometabolomics was measured on rich R2A medium while Fitness Browser fitness data used minimal single C/N-source media, creating condition-dependent artifacts when the two are compared [\[80\]](#references). Cross-dataset condition alignment is currently string-based, yielding only 42 molecular matches; ChEBI-ID-based canonicalization could expand this to 60–80 matches [\[81\]](#references).

**Phylogenetic confounding.** The openness-latency correlation (rho=0.69) has a non-independence problem because multiple Fitness Browser organisms map to the same GapMind species clade and share an identical pangenome openness value [\[82\]](#references). Several pangenome-pathway correlations also do not control for phylogenetic non-independence or uneven genome sampling [\[83\]](#references).

**The Black Queen test is soil-only.** All 33 freshwater samples in the NMDC dataset lacked paired metabolomics, making the Black Queen signal effectively a soil-only test [\[84\]](#references). Extending to freshwater communities is a clear gap.

**Open directions** identified across projects include: longitudinal tracking of gene loss events in latent capability lineages to validate the latent capability framework [\[85\]](#references); querying the full BERDL pangenome for NDH-2 and Complex I co-occurrence across 27K species to test the respiratory compensation hypothesis [\[86\]](#references); replacing coarse COG-fraction proxies with curated metal-stress gene sets for metal-pathway analysis [\[87\]](#references); and building a GapMind pathway-to-metabolite lookup table to unblock the Web of Microbes integration that is currently stalled by a naming-convention mismatch [\[88\]](#references).

## References

1. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "1. Pathway Completeness Alone Is Insufficient to Predict Metabolic Dependency".
2. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "H1 Supported: A Substantial Fraction of Complete Pathways Are Functionally Neutral".
3. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "2. All "Latent Capabilities" Become Important Under Specific Conditions".
4. [Essential Metabolome](../projects/essential-metabolome.md) — REPORT.md › "High Conservation of Amino Acid Biosynthesis Pathways".
5. [Essential Metabolome](../projects/essential-metabolome.md) — REPORT.md › "Near-Universal Amino Acid Biosynthesis".
6. [Essential Metabolome](../projects/essential-metabolome.md) — REPORT.md › "Hypothesis Outcome".
7. [Essential Metabolome](../projects/essential-metabolome.md) — REPORT.md › "*Desulfovibrio vulgaris* Serine Auxotrophy".
8. [Essential Metabolome](../projects/essential-metabolome.md) — REPORT.md › "Ecological Interpretation of DvH Serine Auxotrophy".
9. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 3 — Amino acid pathway completeness differs across ecosystem types for 17 of 18 pathways".
10. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 1 — Black Queen dynamics are detectable at community scale".
11. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 1 — Black Queen dynamics are detectable at community scale".
12. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "H1: Black Queen Signal".
13. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "H2: Mixed Results — Pangenome Openness Supports the Black Queen Framework; Pathway Conservation Does Not".
14. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "5. Amino Acid Biosynthesis Pathways Show the Strongest Accessory Dependence".
15. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Finding 2 — Community metabolic potential separates strongly by ecosystem type".
16. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "H2: Ecosystem Metabolic Niche".
17. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 4: The Aeruginosa-Fluorescens Split Dominates Carbon Pathway Variation".
18. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Hypothesis Assessment".
19. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Literature Context".
20. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 1: Host-Associated Pseudomonas Show Dramatic Loss of Plant-Derived Sugar Pathways".
21. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Finding 3: Free-Living Species Have Greater Pathway Richness Than Host-Associated Species".
22. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "H1 Supported: A Substantial Fraction of Complete Pathways Are Functionally Neutral".
23. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "Novel Contribution".
24. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "2. ADP1 has three parallel NADH dehydrogenases with distinct condition profiles".
25. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "5. Proteomics: respiratory wiring is metabolic, not transcriptional".
26. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "1. Each carbon source uses a distinct respiratory chain configuration".
27. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "3. The quinate-Complex I paradox is resolved by NADH flux rate, not total yield".
28. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "Novel Contribution".
29. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "FBA Model Limitations".
30. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "1. Aromatic catabolism requires a 51-gene support network spanning 4 metabolic subsystems".
31. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "2. Complex I is the largest support subsystem — and invisible to FBA".
32. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "The β-Ketoadipate Pathway and Its Cofactor Requirements".
33. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "3. Support subsystems are genomically independent but metabolically coupled".
34. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Key Findings".
35. [Aromatic Catabolism Network](../projects/aromatic-catabolism-network.md) — REPORT.md › "2. Complex I is the largest support subsystem — and invisible to FBA".
36. [Adp1 Triple Essentiality](../projects/adp1-triple-essentiality.md) — REPORT.md › "Aromatic Catabolism: A Case Study in Model Limitations".
37. [Annotation Gap Discovery](../projects/annotation-gap-discovery.md) — REPORT.md › "1. Evidence Triangulation Resolves 47.8% of Annotation Gaps".
38. [Annotation Gap Discovery](../projects/annotation-gap-discovery.md) — REPORT.md › "2. No Single Evidence Stream Achieves >35% Resolution".
39. [Annotation Gap Discovery](../projects/annotation-gap-discovery.md) — REPORT.md › "4. Two Reactions Dominate High-Confidence Assignments".
40. [Annotation Gap Discovery](../projects/annotation-gap-discovery.md) — REPORT.md › "5. "Dark Reactions" Resist Resolution".
41. [Annotation Gap Discovery](../projects/annotation-gap-discovery.md) — REPORT.md › "Study Design".
42. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "8. 87% of Growth Predictions Depend on Gapfilled Reactions".
43. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 1: PHB pathways are widespread but phylogenetically concentrated".
44. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Finding 2: PHB is enriched in environmentally variable habitats (H1a supported)".
45. [Phb Granule Ecology](../projects/phb-granule-ecology.md) — REPORT.md › "Phylogenetic Distribution (NB02)".
46. [Clay Confined Subsurface](../projects/clay-confined-subsurface.md) — REPORT.md › "Finding 2 — The "anaerobic toolkit" signal is real but largely phylum-driven; only sulfate reduction is genuinely clay-deep enriched after phylogenetic control (H2, partially supported)".
47. [Clay Confined Subsurface](../projects/clay-confined-subsurface.md) — REPORT.md › "Finding 2 — The "anaerobic toolkit" signal is real but largely phylum-driven; only sulfate reduction is genuinely clay-deep enriched after phylogenetic control (H2, partially supported)".
48. [Clay Confined Subsurface](../projects/clay-confined-subsurface.md) — REPORT.md › "Finding 2 — The "anaerobic toolkit" signal is real but largely phylum-driven; only sulfate reduction is genuinely clay-deep enriched after phylogenetic control (H2, partially supported)".
49. [Bacillota B Subsurface Accessory](../projects/bacillota-b-subsurface-accessory.md) — REPORT.md › "Finding 1 — 547 eggNOG OGs are significantly enriched in deep-clay Bacillota_B vs soil-baseline Bacillota_B; the enriched set falls into the pre-registered functional categories (anaerobic respiration, sporulation revival, mineral attachment, regulators, osmoadaptation), with anaerobic respiration the largest hit (H1, strongly supported)".
50. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
51. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
52. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
53. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "4. Variable Pathways Strongly Correlate with Pangenome Openness".
54. [Pangenome Pathway Ecology](../projects/pangenome-pathway-ecology.md) — README.md › "Overview".
55. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "1. Rich Multi-Omics Database with 6 Data Modalities".
56. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "4. FBA and TnSeq Essentiality Agree 74% of the Time".
57. [Adp1 Deletion Phenotypes](../projects/adp1-deletion-phenotypes.md) — REPORT.md › "3. The phenotype landscape is a continuum, not discrete modules".
58. [Acinetobacter Adp1 Explorer](../projects/acinetobacter-adp1-explorer.md) — REPORT.md › "5. Condition-Specific Fitness: Urea and Quinate Stand Apart".
59. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "1. Pathway Completeness Alone Is Insufficient to Predict Metabolic Dependency".
60. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "H2 Mixed: Pathway-Level Conservation Undifferentiated; Pangenome Openness Correlated with Latent Rate".
61. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Novel Contribution".
62. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Novel Contribution".
63. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Data Scale and Environment Classification".
64. [Cf Formulation Design](../projects/cf-formulation-design.md) — REPORT.md › "2.13 Formulation Robustness: PA's Amino Acid Core Is Invariant Across Lung Variants".
65. [Cf Formulation Design](../projects/cf-formulation-design.md) — REPORT.md › "Summary".
66. [Cf Formulation Design](../projects/cf-formulation-design.md) — REPORT.md › "Summary".
67. [Fw300 Metabolic Consistency](../projects/fw300-metabolic-consistency.md) — REPORT.md › "Production vs. utilization: not a contradiction".
68. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Act II — Predict and Explain".
69. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Executive Summary".
70. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "1. xoxF (REE-dependent MDH) outnumbers mxaF (Ca-dependent MDH) by ~19:1 across the BERDL pangenome — H1 strongly supported".
71. [Lanthanide Methylotrophy Atlas](../projects/lanthanide-methylotrophy-atlas.md) — REPORT.md › "2. The most striking xoxF carriers are not classical methylotrophs".
72. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "H3 Supported: All Target Species Show Distinct Metabolic Ecotypes".
73. [Soil Metal Functional Genomics](../projects/soil-metal-functional-genomics.md) — REPORT.md › "Key Findings".
74. [T4Ss Cazy Environmental Hgt](../projects/t4ss-cazy-environmental-hgt.md) — README.md › "Claim Framing".
75. [Clay Confined Subsurface](../projects/clay-confined-subsurface.md) — REPORT.md › "Limitations".
76. [Pseudomonas Carbon Ecology](../projects/pseudomonas-carbon-ecology.md) — REPORT.md › "Limitations".
77. [Pangenome Pathway Ecology](../projects/pangenome-pathway-ecology.md) — RESEARCH_PLAN.md › "Data Limitations".
78. [Annotation Gap Discovery](../projects/annotation-gap-discovery.md) — REPORT.md › "Limitations".
79. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Limitations".
80. [Fw300 Metabolic Consistency](../projects/fw300-metabolic-consistency.md) — REPORT.md › "Limitations".
81. [Genotype To Phenotype Enigma](../projects/genotype-to-phenotype-enigma.md) — REPORT.md › "Limitations".
82. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REVIEW.md › "Findings Assessment".
83. [Pangenome Pathway Geography](../projects/pangenome-pathway-geography.md) — REVIEW.md › "Findings Assessment".
84. [Nmdc Community Metabolic Ecology](../projects/nmdc-community-metabolic-ecology.md) — REPORT.md › "Limitations".
85. [Metabolic Capability Dependency](../projects/metabolic-capability-dependency.md) — REPORT.md › "Future Directions".
86. [Respiratory Chain Wiring](../projects/respiratory-chain-wiring.md) — REPORT.md › "Future Directions".
87. [Enigma Contamination Functional Potential](../projects/enigma-contamination-functional-potential.md) — REPORT.md › "Future Directions".
88. [Webofmicrobes Explorer](../projects/webofmicrobes-explorer.md) — REPORT.md › "Future Directions".

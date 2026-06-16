# Metabolic Pathways

Metabolic pathways are the ordered chains of enzyme-catalyzed reactions by which microbes build essential molecules (biosynthesis) and extract energy and carbon from their environment (catabolism). This page is a cross-cutting synthesis node: more than forty projects in this corpus touch metabolism in some way, and the questions they ask are the same regardless of organism or habitat. Which pathways does a genome carry? Are those pathways actually *used*, or just latent in the DNA? Why do some species keep a biosynthetic route while their neighbors discard it? The page exists to collect what the corpus has learned about how pathway content is distributed across bacteria, how that content maps (or fails to map) onto measured growth and fitness, and where the methods used to infer pathways break down.

## Overview

The recurring tension across the corpus is between **genomic potential** and **realized function**. A pathway can be predicted complete from gene content yet contribute nothing measurable to fitness under the conditions tested. Across 161 organism-pathway pairs in seven model bacteria, only about a third (35.4%) were "active dependencies" — genomically complete and fitness-required — while 41% were complete but fitness-neutral "latent capabilities," directly showing that pathway completeness does not predict metabolic dependency. A broader survey of 1,695 pathway-organism pairs from 48 organisms put the latent fraction near 15.8% of all complete pathways, encoded by the genome but showing no detectable fitness importance under tested conditions. This gap between what a genome *can* do and what it *must* do is the conceptual spine of the page.

Two analytical workhorses appear throughout. **GapMind** is a homology-based tool that scores whether a genome carries a complete biosynthesis or catabolism pathway; the corpus uses it at scales from a 7-organism pilot up to all ~27,690 species in the pangenome resource. **RB-TnSeq** (randomly barcoded transposon sequencing) and the derived Fitness Browser provide the experimental counterweight: genome-wide measurements of how much each gene matters for growth in a specific condition, which is what lets projects ask whether a *predicted* pathway is *actually* load-bearing. Where these two views agree, confidence is high; where they diverge, the corpus treats the discordance as a signal about annotation gaps, regulation, or condition mismatch rather than noise.

## What the Corpus Shows

**Biosynthesis is conserved; catabolism is variable.** Amino acid biosynthesis emerges as the deeply conserved core. In a 7-organism GapMind pilot, 17 of 18 amino acid biosynthesis pathways were present in every organism, and TCA-cycle intermediates, fermentation products, and amino acid catabolism were shared across all of them — evidence that prototrophy is the ancestral state for free-living bacteria and that complete biosynthetic capacity is a minimal repertoire for independent growth. Carbon catabolism behaves oppositely. At the community scale across 220 NMDC samples, carbon-utilization pathways — not amino acid pathways — loaded almost entirely on the first principal component of metabolic variation, making carbon-substrate availability the primary axis that separates ecosystem types, with Soil and Freshwater communities occupying nearly non-overlapping regions of metabolic space. Core genes themselves are enriched for metabolic and biosynthetic functions (nucleotide and coenzyme metabolism) relative to recently acquired novel genes, consistent with an ancient conserved metabolic engine carried in the core genome.

**Pathway variability tracks pangenome openness.** A pangenome is "open" when sequencing more strains of a species keeps revealing new genes, and "closed" when the gene repertoire saturates. Several projects converge on the result that *which* pathways vary within a species is a mechanistically interpretable correlate of openness. Across 2,810 species with at least 10 genomes, the count of variable pathways correlated with openness, strengthening to a partial Spearman rho of 0.530 after controlling for genome count. Aggregating organisms to species clades, the per-clade fraction of latent capabilities rose with openness (rho = 0.69), which the projects read as support for the **Black Queen Hypothesis** — the idea that costly functions are lost from individual genomes when the wider community reliably supplies the product. Amino acid biosynthesis pathways (leucine, valine, arginine, lysine, threonine) showed the strongest dependence on accessory rather than core genes, the precondition for Black Queen public-good metabolism. The community-level NMDC test reinforced this: the two pathways reaching FDR significance for negative completeness-vs-metabolite correlations were leucine and arginine, both energetically expensive to synthesize — exactly the routes predicted to be shed first when environmental supply is reliable.

**Ecology predicts pathway content better than geography.** Across 1,872 bacterial species, ecological niche breadth (diversity of AlphaEarth satellite-derived habitat embeddings) was the strongest predictor of mean pathway completeness (r ≈ 0.392), and embedding *variance* was stronger still (r ≈ 0.412); raw geographic spread gave a weaker signal. The interpretation is that habitat heterogeneity, not distance, shapes what metabolic machinery a lineage keeps.

**Loss is often ancestral, and it has practical consequences.** The *Pseudomonas* work quantified carbon-pathway profiles across 433 species and 12,732 genomes and found that host-associated *P. aeruginosa* has near-completely lost plant-derived sugar catabolism (xylose, arabinose, myo-inositol all near 0% complete versus 59-74% in the *P. fluorescens* group) while retaining near-universal amino acid and organic-acid catabolism. Much of this loss is ancestral streamlining of the lineage rather than adaptation acquired during chronic infection, because the pathways were already absent species-wide across thousands of isolates. The cystic-fibrosis formulation project turned this conserved amino-acid niche into a design target: a five-organism, FDA-safe consortium reaches 100% coverage of PA14's amino acid niche with 78% mean inhibition, and because the targeted catabolic pathways are 97.4% conserved across 1,796 lung *P. aeruginosa* genomes, one formulation is predicted to suppress the pathogen across lung variants.

**Support networks make single pathways expensive.** Looking inside one catabolic route, aromatic (quinate) degradation in *Acinetobacter baylyi* ADP1 requires a 51-gene support network organized into four functional subsystems beyond the core β-ketoadipate pathway, dominated by Complex I (NADH:ubiquinone oxidoreductase, 21 of 51 genes). Crucially, cross-species fitness transfer showed that the Complex I dependency is really about high-NADH-flux substrates in general — its largest defects fell on the non-aromatic substrates acetate and succinate — so the "aromatic" requirement is a downstream consequence of redox load, not aromaticity per se. ADP1's respiratory chain is wired condition-by-condition, carrying three parallel NADH dehydrogenases with distinct non-overlapping condition profiles, a system the project frames as passive flux-based switching rather than transcriptional control.

## Projects and Evidence

The corpus reaches metabolic pathways through several complementary lenses.

*Model-system dissection (Acinetobacter ADP1).* The ADP1 cluster of projects pairs genome-scale metabolic models with RB-TnSeq phenotypes. Flux-balance analysis (FBA — predicting growth by optimizing reaction fluxes under stoichiometric constraints) agreed with TnSeq essentiality calls for 73.8% of genes carrying both measurements, and top condition-specific genes mapped precisely onto expected pathways (urease for urea, protocatechuate/quinate degradation for quinate), recovering ADP1's metabolic architecture from phenotype alone. The discordant minority became the interesting signal: aromatic-degradation genes were strongly enriched among FBA-discordant calls, exposing a systematic gap in the model's environmental assumptions.

*Annotation-gap resolution.* The annotation-gap project integrated five evidence types — gapfilling, fitness, pangenome, GapMind, and BLAST — to assign candidate genes to gapfilled enzymatic reactions, resolving 47.8% of 201 reaction-organism pairs and exceeding its pre-specified 30% threshold. Leave-one-out cross-validation showed each evidence stream contributes uniquely, which is the project's central methodological claim: no single data type resolves metabolic annotation gaps on its own.

*Pan-bacterial pathway censuses.* Several projects scale GapMind across tens of thousands of genomes to estimate prevalence. The lanthanide methylotrophy atlas found the rare-earth-dependent methanol dehydrogenase *xoxF* outnumbers the calcium-dependent *mxaF* roughly 19:1 across 293,000 genomes, reframing which version of a "canonical" pathway actually dominates. The PHB-granule project produced the first precise pan-bacterial estimate that 21.9% of 27,690 species carry the PHA synthase *phaC*, with the pathway phylogenetically concentrated (Pseudomonadota alone account for 74.9% of *phaC* carriers).

*Cross-database concordance.* The FW300 and Web of Microbes projects ask whether independent measurement modalities tell the same metabolic story. For *Pseudomonas* FW300-N2E3, exometabolomic, fitness, utilization, and pathway databases agreed at a 0.94 mean concordance score with no fully discordant metabolites, and curated matching bridged 19 produced metabolites to Fitness Browser carbon/nitrogen conditions. A conceptual caution runs through this work: production and utilization measure fundamentally different capabilities, so a bacterium can secrete a metabolite for ecological reasons without being able to catabolize it for energy.

*Functional-annotation correction.* The SNIPE defense-system project illustrates how fitness data correct mistaken pathway annotations: Fitness Browser data directly contradict a UniProt fructose-transporter label for ManXYZ, showing the mutant grows normally on fructose but is crippled on mannose and glucosamine. That cost-of-loss measurement underpins the project's engineering idea — a system that blocks phage entry at the ManYZ pore while preserving transporter function, resolving the phage-resistance-versus-metabolic-cost trade-off.

## Connections

Metabolic pathway content is downstream of genome structure, so this page is tightly coupled to [Pangenome Architecture](pangenome-architecture.md): the openness-versus-conservation framing, the core/accessory split, and the Black Queen distribution of biosynthetic genes are all pangenome concepts measured here through a metabolic lens. The complementary experimental axis is [Gene Fitness](gene-fitness.md), the RB-TnSeq and Fitness Browser evidence that tells the corpus whether a predicted pathway is actually load-bearing — the latent-versus-active distinction lives at that intersection. Because latent capabilities and within-species pathway heterogeneity define metabolic ecotypes, this page connects to [Microbial Ecotypes](microbial-ecotypes.md), and the habitat-driven loss patterns connect to [Environment Biogeography](environment-biogeography.md), where the AlphaEarth ecology-beats-geography result sits.

Specific application domains branch off as well. The aromatic and respiratory dissections are part of the [Adp1 Model System](adp1-model-system.md). Annotation gaps where genes have no clear pathway assignment shade into [Functional Dark Matter](functional-dark-matter.md). The HGT of CAZy cassettes and the burden of dispensable catabolic genes connect to [Mobile Genetic Elements](mobile-genetic-elements.md), the CF-formulation and PHB work to [Microbiome Engineering](microbiome-engineering.md), and the metal-stress COG associations to [Metal Resistance](metal-resistance.md). The clay-subsurface anaerobic-toolkit findings link to [Subsurface Genomics](subsurface-genomics.md). Underlying all of this are shared data resources: GapMind pathway scores and pangenomes come from [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md), fitness measurements from [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md), reaction/compound references from [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md), and community multi-omics from [Nmdc Arkin](../data/nmdc-arkin.md).

## Caveats and Open Directions

The pathway-inference machinery this page leans on has well-documented failure modes, and the corpus is unusually candid about them.

**GapMind is predictive, not experimental.** Its pathway calls are probabilistic homology inferences that vary in confidence, indicate gene presence rather than active expression, and saturate near the top of their scale (the 18-pathway amino-acid universe maxes out for most cultivable bacteria, blunting the self-sufficiency metric). A practical data pitfall recurs: GapMind stores multiple rows per genome-pathway pair, so correct aggregation requires taking the best (MAX) score per pair or completeness counts corrupt. Inferred auxotrophies can be detection artifacts when an organism uses a divergent enzyme below GapMind's homology threshold, and the carbon-pathway set misses genus-specific routes such as aromatic degradation central to *P. putida* ecology.

**FBA is only as good as its gapfilling.** In the ADP1 work, 87% of growth predictions relied on at least one gapfilled reaction, tightly coupling accuracy to gapfilling quality, and single-gene knockout validation became circular because the models cannot grow on carbon-source minimal media without those gapfilled reactions. A multivariate metabolic-feature model of inhibition that looked predictive in training (R² = 0.274) collapsed to ~0.145 cross-validated, a reminder that apparent metabolic predictors can overfit small cohorts.

**Essentiality and conservation signals are confounded.** Because the underlying RB-TnSeq essential-gene experiments were run in rich media, biosynthetic genes can appear non-essential through nutrient supplementation, confounding interpretation. Importance thresholds can be partly circular — a median-based split divides pathways ~50/50 by construction, so the claim that every latent capability becomes important under *some* condition would need an independent validation set. Phylogeny confounds habitat signals: the subsurface "anaerobic toolkit" largely tracks the Bacillota_B lineage rather than the deep-clay habitat, and pan-genome correlations frequently fail to control for phylogenetic non-independence or uneven genome sampling.

**Scope and sampling limits.** The pilot censuses are small: E. coli is entirely absent from the KBase pangenome GapMind dataset (too many genomes for species-level GTDB analysis), reducing one intended 45-organism survey to 7 organisms. Genome databases are clinically skewed — *P. aeruginosa* alone makes up 53% of *Pseudomonas* genomes — limiting species-level comparisons. And quantitative-genomics linkage can silently fail: an attempt to join Fitness Browser organisms to GapMind clades via NCBI taxonomy IDs returned zero matches because the metadata column held boolean strings rather than taxids. One project openly flagged an effect-size error (a Cohen's d of -7.54 that corrected to about -0.4), underscoring how much of this work is still being checked.

The clearest open directions follow from these limits: replacing string-based metabolite matching with chemical identifiers (InChIKey, ChEBI) to expand cross-database overlap; adding multiple-testing correction and genome-count-stratified analysis to the large correlational surveys; experimentally validating high-confidence gene-reaction assignments and predicted auxotrophies by targeted knockout or minimal-media growth; and scaling the NDH-2/Complex I compensation question and the latent-capability framework to the full pangenome for properly powered, longitudinally validated tests.

## Sources

- [stmt:capability-not-dependency; pathway_capability_dependency]
- [stmt:latent-capability-fraction; metabolic_capability_dependency]
- [stmt:openness-correlates-latent-rate; metabolic_capability_dependency]
- [stmt:novel-latent-fraction-quantification; metabolic_capability_dependency]
- [stmt:amino-acid-accessory-dependence; pathway_capability_dependency]
- [stmt:variable-pathways-open-pangenomes; pathway_capability_dependency]
- [stmt:aa-biosynthesis-high-conservation; essential_metabolome]
- [stmt:aa-prototrophy-ancestral; essential_metabolome]
- [stmt:near-universal-not-strictly-universal; essential_metabolome]
- [stmt:sugar-pathway-loss-host-associated; pseudomonas_carbon_ecology]
- [stmt:amino-acid-pathways-retained; pseudomonas_carbon_ecology]
- [stmt:ancestral-streamlining-claim; pseudomonas_carbon_ecology]
- [stmt:pa-lung-metabolic-streamlining; cf_formulation_design]
- [stmt:five-organism-formulation; cf_formulation_design]
- [stmt:formulation-target-invariant; cf_formulation_design]
- [stmt:support-network-51-genes-finding; aromatic_catabolism_network]
- [stmt:complex-i-dominant-subsystem-finding; aromatic_catabolism_network]
- [stmt:high-nadh-not-aromatic-finding; aromatic_catabolism_network]
- [stmt:condition-specific-respiratory-wiring; respiratory_chain_wiring]
- [stmt:three-parallel-nadh-dehydrogenases; respiratory_chain_wiring]
- [stmt:specific-genes-map-to-pathways; adp1_deletion_phenotypes]
- [stmt:fba-tnseq-concordance; acinetobacter_adp1_explorer]
- [stmt:triangulation-resolves-48pct; annotation_gap_discovery]
- [stmt:five-evidence-integration-novel; annotation_gap_discovery]
- [stmt:xoxf-outnumbers-mxaf-19to1; lanthanide_methylotrophy_atlas]
- [stmt:phb-phylogenetically-concentrated; phb_granule_ecology]
- [stmt:phac-prevalence-21-percent; phb_granule_ecology]
- [stmt:ecosystem-metabolic-separation; nmdc_community_metabolic_ecology]
- [stmt:leucine-arginine-fdr-significant; nmdc_community_metabolic_ecology]
- [stmt:carbon-utilization-primary-axis; nmdc_community_metabolic_ecology]
- [stmt:niche-breadth-pathway-strongest; pangenome_pathway_geography]
- [stmt:ecology-beats-geography; pangenome_pathway_geography]
- [stmt:core-genes-metabolism-enriched; cog_analysis]
- [stmt:high-cross-database-concordance; fw300_metabolic_consistency]
- [stmt:production-not-utilization; fw300_metabolic_consistency]
- [stmt:metabolites-bridge-to-fb-conditions; webofmicrobes_explorer]
- [stmt:manyz-not-fructose-transporter; snipe_defense_system]
- [stmt:snipe-resolves-resistance-cost-tradeoff; snipe_defense_system]
- [stmt:gapfilling-dependence; acinetobacter_adp1_explorer]
- [stmt:knockout-validation-inconclusive; annotation_gap_discovery]
- [stmt:rich-media-essentiality-confound; essential_metabolome]
- [stmt:ecoli-absent-pilot-scope; essential_metabolome]
- [stmt:caveat-predictions-not-experimental; pangenome_pathway_ecology]
- [stmt:gapmind-multirow-pitfall; pangenome_pathway_geography]
- [stmt:caveat-sampling-bias; pseudomonas_carbon_ecology]
- [stmt:unacknowledged-confounders-caveat; pangenome_pathway_geography]
- [stmt:cohen-d-formula-error; plant_microbiome_ecotypes]
- [stmt:toolkit-phylum-confound; clay_confined_subsurface]
- [stmt:caveat-genomic-potential-not-expression; nmdc_community_metabolic_ecology]
- [stmt:metabolic-model-overfits; cf_formulation_design]
- [stmt:threshold-circularity-caveat; pathway_capability_dependency]
- [stmt:taxid-matching-failed-caveat; metabolic_capability_dependency]

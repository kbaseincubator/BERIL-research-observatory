# Microbial Ecotypes

A microbial ecotype is a genetically and functionally distinct subpopulation *within* a named species — a cluster of strains that share a coherent gene-content or metabolic-pathway profile, often interpreted as an adaptation to a particular niche. Because a bacterial "species" is rarely a single uniform genome but rather a pangenome of a stable core plus a fluid accessory complement, the same species can contain several such subpopulations. This page synthesizes what the corpus has learned about those subpopulations: how common they are, how their gene content is organized, and — the question that dominates the evidence — whether and how strongly they are driven by the *environment* a strain was isolated from rather than by its ancestry. The page exists as a cross-cutting topic because nearly every analysis that clusters strains within a species and then asks "why do these clusters exist?" runs into the same answer: within-species structure is real and pervasive, but tying it to environment is hard, and the apparent signal is repeatedly diluted by phylogenetic confounding and biased sampling.

## Overview

The corpus attacks ecotypes from two directions that mostly agree. The first is gene-content-based: take a species with enough sequenced genomes, build presence/absence profiles over its accessory gene clusters, and cluster the strains. The second is pathway-based: score each genome for metabolic-pathway completeness (typically with **GapMind**, which infers whether a genome can carry out a defined catabolic or biosynthetic pathway from its annotated genes) and cluster on those binary capability vectors. Both approaches consistently recover discrete within-species clusters, and both then test the clusters against an isolation-source or environmental label to ask whether the structure is ecological.

Layered on top of these is the question of *what drives* gene-content variation in general — environment or phylogeny. A recurring instrument here is **AlphaEarth**, a set of 64-dimensional embeddings derived from satellite imagery that encode the geographic and environmental context (climate, vegetation, land use) of a genome's sampling location. AlphaEarth converts a latitude/longitude into a continuous environmental descriptor, which lets analyses ask whether environmentally similar strains carry similar genes. The dominant result, returned from several independent angles, is a null or near-null: environmental similarity is a weak predictor of gene content, phylogeny is a far stronger one, and the structural features people expected to amplify the environment signal — open pangenomes, host-versus-environment lifestyle — mostly do not.

## What the Corpus Shows

**Within-species ecotypes are real, widespread, and functionally structured.** This is the firmest positive result in the page. Gene-content ecotypes are recurring across the sampled bacterial species and represent genuine within-species pangenome structure, and that variation is functionally organized rather than random — COG functional categories differentiate consistently across ecotypes in every species sampled, with adaptive functions separating ecotypes more strongly than housekeeping functions even though both classes vary. The metabolic-pathway view agrees: within-species clustering of binary pathway profiles defines a median of four (up to eight) metabolic ecotypes per species, and every one of ten target species with at least 50 genomes and 15 variable pathways showed meaningful clustering (all silhouette scores above 0.2), making within-species metabolic heterogeneity a general feature. Crucially, the number of metabolic ecotypes a species supports correlates with its pangenome openness (partial rho=0.322 after controlling for genome count) — the more fluid the accessory genome, the more sub-niches it can encode. AMR repertoires show the same pattern: roughly one species in five (19.5% of 974 species) forms two or more distinct AMR ecotypes by UMAP-plus-DBSCAN clustering with good cluster quality.

**But phylogeny, not environment, dominates gene content.** When the corpus asks *why* strains differ, ancestry wins. Across species with sufficient data, phylogenetic relatedness predicts gene-content similarity more strongly than environmental similarity does. The headline test — does AlphaEarth environmental-embedding similarity predict gene content? — returns a weak relationship, and a careful reanalysis hardened that into a robust null. Restricting the analysis to environmental species did *not* yield stronger environment-gene-content correlations than human-associated species (Mann-Whitney p=0.83), and a continuous Spearman test confirmed it (rho=-0.085, p=0.25). Contrary to the original hypothesis, human-associated species showed *slightly higher* environment-gene-content partial correlations than environmental species — the opposite of the predicted direction — which the analysis interprets as epidemiological geographic structure in clinical pathogens rather than ecology. A systematic genome-level isolation-source classification reproduced the prior null (p=0.83 vs the earlier p=0.66), so the result survives a more rigorous environment labeling.

**Pangenome openness does not predict the eco-versus-phylo balance.** A natural hypothesis is that open pangenomes — species with high gene turnover and horizontal transfer — should show stronger environment effects. They do not. Whether a species has an open or closed pangenome shows no significant correlation with either environmental or phylogenetic effect size on gene content (environment rho=-0.05, p=0.54; phylogeny rho=0.03, p=0.73), implying that pangenome structure is largely independent of the eco-phylo dynamics governing gene-content variation. The Tettelin open/closed distinction describes how variable gene content is, but not what drives that variability. This null is consequential enough that follow-on work proposes stratifying by gene function instead of treating openness as a whole-genome scalar.

**Niche breadth, however, does track genomic flexibility.** Where openness fails as a predictor of the *driver*, it succeeds as a correlate of ecological *range*. Open-pangenome species exhibit broader ecological niche breadth (r=0.324), and a high core-genome fraction is strongly *negatively* correlated with niche breadth (r=-0.445, p=1.4e-91) — converging evidence that pangenome flexibility, supplied by accessory genes that enable metabolic heterogeneity, is what lets a species span more niches. The plant-growth-promoting case adds a twist: PGP gene richness correlates *negatively* with openness (rho=-0.195), so PGP-rich species tend to have closed pangenomes, consistent with stable specialized niches rather than generalist HGT-driven acquisition.

**Specific systems show interpretable ecotype structure.** Several focused analyses find ecotypes that map cleanly onto biology. In *Pseudomonas*, the primary axis of carbon-pathway variation separates *P. aeruginosa* (Pseudomonas sensu stricto) from the environmental Pseudomonas_E clade, driven by near-complete loss of plant-derived sugar catabolism in the host-associated lineage (43 of 62 GapMind carbon pathways differ between the two subgenera) — though much of that loss reflects *ancestral* metabolic streamlining of the lineage rather than adaptation acquired during infection. Carbon profiles do carry a real environment signal among free-living and plant-associated species (permutation p=0.006), but a Random Forest predicting environment class from those profiles reaches only modest balanced accuracy (0.408 vs 0.250 chance). In the plant microbiome, three markers — nitrogen fixation, ACC deaminase, and the type III secretion system — survive as species-level-robust plant-association signals after cluster-robust and within-genus permutation tests, and canonical pathovar-host specializations (*Xanthomonas campestris* on Brassica, *X. vasicola* on maize) are confirmed genomically. Lung-adapted *P. aeruginosa* loses sugar catabolism under the relaxed selection of amino-acid-rich sputum while keeping amino-acid catabolism invariant, a within-niche metabolic ecotype.

**Ecotypes have clinical traction.** The IBD work is the most applied use of the concept: two independent clustering methods on 8,489 metagenomic samples converge on four reproducible inflammatory-bowel-disease microbiome ecotypes (E0-E3), clinical covariates can separate healthy from IBD but cannot distinguish the transitional E1 from the severe E3 ecotype (so metagenomics is required for ecotype assignment), and the practical consequence is direct — phage cocktails designed at the cohort level will mismatch individual patients unless each patient's ecotype is determined first, and a single patient can even drift between E1 and E3 between visits. Environment also selects resistance strategy at the ecotype scale: clinical and human-gut species carry roughly 2.5x more AMR gene clusters than soil/aquatic species, and different niches favor fundamentally different mechanisms (target modification reaches 44% in human gut versus 6% in aquatic species).

## Projects and Evidence

The evidence spans more than forty projects drawing on several shared data collections. Pangenome-scale ecotype and openness analyses lean on [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) and [Kbase Genomes](../data/kbase-genomes.md), with environmental context supplied by AlphaEarth embeddings; metabolic-capability clustering uses GapMind scores over [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md); within-species fitness and co-inheritance work draws on the [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md); field and community ecotype work uses [Enigma Coral](../data/enigma-coral.md) and [Nmdc Arkin](../data/nmdc-arkin.md) metagenomes; phage-ecotype targeting uses [Phagefoundry](../data/phagefoundry.md) and clinical AMR draws on [Protect Genomedepot](../data/protect-genomedepot.md).

The **core ecotype and environment-reanalysis** projects (`ecotype_analysis`, `ecotype_env_reanalysis`, `ecotype_functional_differentiation`, `env_embedding_explorer`) are the analytical center of gravity. They establish that gene-content ecotypes are widespread and functionally structured, then test the environment hypothesis and return the robust null described above. `env_embedding_explorer` quantifies why: UMAP of the 64-dimensional embeddings yields 320 DBSCAN clusters many dominated by a single environment, but a strong clinical sampling bias may dilute the environment-gene-content relationship because interchangeable hospital environments carry little distinguishing geographic signal.

The **pangenome-openness** projects (`pangenome_openness`, `openness_functional_composition`, `pangenome_pathway_ecology`, `pangenome_pathway_geography`, `pathway_capability_dependency`, `metabolic_capability_dependency`) test openness as a predictor of eco-phylo dynamics (null) and as a correlate of niche breadth (positive), and define metabolic ecotypes whose count tracks openness. `metabolic_capability_dependency` adds that metabolic clusters correlate with isolation environment in copiotrophs (*Salmonella enterica*, *Phenylobacterium*) but not in marine oligotrophs.

The **lineage-specific ecotype** projects (`pseudomonas_carbon_ecology`, `plant_microbiome_ecotypes`, `cf_formulation_design`, `lanthanide_methylotrophy_atlas`, `pgp_pangenome_ecology`) drill into individual systems — *Pseudomonas* subgenus carbon ecology, plant-association markers, CF lung adaptation, the clade-restricted lanmodulin/xoxF methylotrophy signal, and the diazotroph-versus-PGPB guild split — where ecotype structure is most interpretable.

The **AMR and clinical-ecotype** projects (`amr_strain_variation`, `amr_environmental_resistome`, `amr_cofitness_networks`, `ibd_phage_targeting`) connect within-species structure to resistance and disease, from AMR ecotypes and organism-specific cofitness support networks to the four reproducible IBD ecotypes and their phage-cocktail implications.

The **subsurface and field-ecology** projects (`enigma_sso_asv_ecology`, `clay_confined_subsurface`, `bacillota_b_subsurface_accessory`, `lab_field_ecology`, `genotype_to_phenotype_enigma`, `harvard_forest_warming`, `temporal_core_dynamics`) ground the topic in real sites, where vertical zonation dominates subsurface community structure (depth explains 27.5% of variance), deep clay specialists carry expansion rather than streamlining, and field isolates occupy environmental niches underrepresented in NCBI.

## Connections

This topic is tightly coupled to the rest of the wiki because "within-species structure" touches almost every functional axis the corpus measures:

- [Environment Biogeography](environment-biogeography.md) is the most tightly coupled page — the ecotype environment-reanalysis here *is* its test of whether environmental embedding similarity predicts gene content, and the shared null result is central to both pages.
- [Pangenome Architecture](pangenome-architecture.md) supplies the core/accessory framework that makes ecotypes possible; the openness-versus-niche-breadth and openness-versus-eco-phylo results live at the boundary between the two pages.
- [Metabolic Pathways](metabolic-pathways.md) connects through GapMind pathway-completeness scoring — the engine behind metabolic ecotypes and the *Pseudomonas* sugar-catabolism contrast.
- [Amr Resistome](amr-resistome.md) shares the AMR-ecotype and niche-selects-mechanism evidence, where ecological niche strongly predicts resistome size and strategy.
- [Metal Resistance](metal-resistance.md) connects via the metal-tolerance ecotype work, where contamination isolates score higher than environmental ones even within phyla but classical phenotypes add nothing beyond taxonomy.
- [Gene Fitness](gene-fitness.md) supplies the cofitness/co-inheritance and condition-dependent-essentiality structure that underlies organism-specific within-species networks.
- [Subsurface Genomics](subsurface-genomics.md) shares the ENIGMA, Mont Terri, and clay-confined field sites where within-niche ecotypes are tested against real geochemistry.
- [Microbiome Engineering](microbiome-engineering.md) draws on the ecotype-aware phage-cocktail design — the clearest translational use of the concept.
- [Functional Dark Matter](functional-dark-matter.md) connects because the strongest ecotype differences fall in unknown-function and mobile-element categories, leaving much niche-specific signal biologically uninterpreted.
- [Mobile Genetic Elements](mobile-genetic-elements.md) and [Adp1 Model System](adp1-model-system.md) are adjacent through accessory-genome turnover and within-species respiratory-wiring variation respectively.

## Caveats and Open Directions

Honesty about confounding is the defining feature of this topic, and the caveats are load-bearing — in several cases they *are* the result.

**Phylogenetic confounding is pervasive and only partly controlled.** Because phylogeny dominates gene content in most species, almost every environment-ecotype association is entangled with ancestry. Several analyses controlled only for genome count and taxonomic grouping rather than full phylogenetic independent contrasts, so metabolic ecotypes may partly reflect intra-species phylogenetic structure. In *Pseudomonas*, the dominant signal separates subgenera rather than lifestyles, and within Pseudomonas_E lifestyle differences are subtle with no explicit control for phylogenetic non-independence. The plant-microbiome headline compartment effect was largely a sampling artifact — PERMANOVA R2=0.527 collapses to a residual 0.072 once a few genome-rich rhizobial and Pseudomonas clades are excluded, and the location-controlled compartment effect explains only ~6% of variance. Where classical phenotypes were tested directly, BacDive metal-tolerance features added *no* predictive power beyond taxonomy (delta R-squared = -0.009): the phenotypes were noisier proxies for ancestry, not independent predictors.

**The ecotype-environment test is structurally underpowered.** Statistical testing of ecotype-environment association is weakened because 52.7% of genomes lack a classifiable isolation source, leaving only two species with enough within-species environmental diversity for chi-squared testing. Environmental species lose more species to NaN partial correlations (21%) than human-associated ones (7%), and major clinical species are missing outright — *Klebsiella pneumoniae* was excluded because it exceeded Spark's maxResultSize, and the two most diverse *Ralstonia* organisms have zero co-fitness data. Separating environmental from host-associated bacteria did not reveal a stronger environment effect, and the openness analysis is constrained to species having both pangenome and ecotype results, shrinking the sample further. A cofitness "prevalence ceiling" compounds this: most Fitness Browser genes sit in core clusters above 95% prevalence where presence/absence variance is negligible, so the co-inheritance metric is near zero by construction except in the most gene-diverse species.

**Magnitudes are not always comparable, and some signal is uninterpretable.** Median partial correlations in the reanalysis run 27x higher than the original (0.081 vs 0.003) because downsampling was dropped, so absolute magnitudes cannot be compared across runs even though the group comparison holds. AlphaEarth embedding similarity may not equate to ecological relevance at all, since the climate/vegetation/land-use variation it captures need not predict which genes a bacterium carries. And the strongest ecotype differences often fall in unknown-function and mobile-element categories, so much of the niche-specific signal remains biologically opaque.

**Sampling and resolution biases blunt the signal further.** The genome record over-represents clinical pathogens and culturable Proteobacteria — the 48 Fitness Browser organisms skew Proteobacterial, and the top 100 of 15,312 bacterial organisms capture 44% of the literature — so essentiality and ecotype patterns in underrepresented lineages stay uncertain. Field analyses are limited to genus resolution by 16S amplicons, ENIGMA taxonomy resolves only to genus, and naive short-strain-name matching is hazardous (a strain "MT20" once injected 1,751 spurious clinical genomes into environmental profiles before GTDB-Tk correction). Niche breadth itself is frequently a sequencing-effort proxy from OTU detection, and genus-level aggregation can make a genus look broad-niched when really different species occupy different habitats. Several applied claims are explicitly provisional: the CF inhibition assays all used PA14, an ExoU+ strain representing under 5% of CF isolates that are 94% ExoS+, and the E3-ecotype phage target list rests on single-study evidence pending a cohort with enough E3 patients in both diagnosis groups.

The open directions follow directly. The most-repeated is to stop testing environment on whole-genome distance and instead target *functional gene subsets* — transport, secondary metabolism, defense — where environmental selection may be detectable even when it is invisible at the genome scale, and to classify environments with structured ENVO ontology terms rather than keyword-harmonized isolation sources. Others propose re-running the ecotype analysis on environmental-only samples where AlphaEarth carries more geographic information, moving from 16S to metagenomics to recover strain-level matching, correlating metabolic ecotypes with AlphaEarth niche breadth (planned but unexecuted, limited by 28% genome coverage), and running date-shuffling null models for temporal core dynamics to separate genuine population dynamics from sampling effects. Together these would convert a topic currently rich in real-but-uninterpretable structure into one where within-species ecotypes can be tied to measured ecology.

## Sources

- [stmt:ecotype-functional-widespread-finding; ecotype_functional_differentiation]
- [stmt:ecotype-functional-differentiation-finding; ecotype_functional_differentiation]
- [stmt:ecotype-adaptive-effect-claim; ecotype_functional_differentiation]
- [stmt:metabolic-ecotypes; pathway_capability_dependency]
- [stmt:metabolic-ecotypes-widespread; metabolic_capability_dependency]
- [stmt:ecotypes-environment-linked-copiotrophs; metabolic_capability_dependency]
- [stmt:amr-ecotypes; amr_strain_variation]
- [stmt:amr-tracks-phylogeny; amr_strain_variation]
- [stmt:ecotype-phylogeny-dominance-finding; ecotype_analysis]
- [stmt:ecotype-gene-subset-claim; ecotype_analysis]
- [stmt:ecotype-env-null-finding; ecotype_env_reanalysis]
- [stmt:ecotype-continuous-spearman-finding; ecotype_env_reanalysis]
- [stmt:ecotype-opposite-direction-claim; ecotype_env_reanalysis]
- [stmt:ecotype-genome-level-classification-finding; ecotype_env_reanalysis]
- [stmt:ecotype-gene-subset-opportunity; ecotype_env_reanalysis]
- [stmt:openness-does-not-predict-driver; pangenome_openness]
- [stmt:no-correlation-openness-effects; pangenome_openness]
- [stmt:weak-spearman-values; pangenome_openness]
- [stmt:pangenome-niche-breadth; pangenome_pathway_geography]
- [stmt:core-fraction-negative-niche; pangenome_pathway_geography]
- [stmt:openness-negatively-correlates-pgp; pgp_pangenome_ecology]
- [stmt:aeruginosa-fluorescens-split-dominates; pseudomonas_carbon_ecology]
- [stmt:sugar-pathway-loss-host-associated; pseudomonas_carbon_ecology]
- [stmt:carbon-profiles-environment-signal; pseudomonas_carbon_ecology]
- [stmt:ancestral-streamlining-claim; pseudomonas_carbon_ecology]
- [stmt:three-tier-marker-robustness; plant_microbiome_ecotypes]
- [stmt:permanova-sampling-artifact; plant_microbiome_ecotypes]
- [stmt:pa-lung-metabolic-streamlining; cf_formulation_design]
- [stmt:four-ibd-ecotypes; ibd_phage_targeting]
- [stmt:cohort-cocktail-mismatch; ibd_phage_targeting]
- [stmt:clinical-covariates-insufficient; ibd_phage_targeting]
- [stmt:clinical-amr-richness; amr_environmental_resistome]
- [stmt:niche-selects-mechanism; amr_environmental_resistome]
- [stmt:umap-env-clusters; env_embedding_explorer]
- [stmt:bias-explains-weak-ecotype-signal; env_embedding_explorer]
- [stmt:organism-specific-networks; amr_cofitness_networks]
- [stmt:phenotypes-add-nothing-beyond-taxonomy; bacdive_phenotype_metal_tolerance]
- [stmt:depth-dominates-zonation; enigma_sso_asv_ecology]
- [stmt:phylogeny-confound-caveat; pathway_capability_dependency]
- [stmt:caveat-phylogenetic-confounding; pseudomonas_carbon_ecology]
- [stmt:ecotype-env-underpowered; amr_strain_variation]
- [stmt:ecotype-kpneumoniae-excluded-caveat; ecotype_env_reanalysis]
- [stmt:ecotype-27x-discrepancy-caveat; ecotype_env_reanalysis]
- [stmt:ecotype-nan-bias-caveat; ecotype_env_reanalysis]
- [stmt:ecotype-lifestyle-null-caveat; ecotype_analysis]
- [stmt:ecotype-unknown-mobile-caveat; ecotype_functional_differentiation]
- [stmt:ecotype-embedding-ecology-claim; ecotype_env_reanalysis]
- [stmt:prevalence-ceiling-caveat; cofitness_coinheritance]
- [stmt:taxonomic-bias-caveat; essential_genome]
- [stmt:genus-resolution-limitation; lab_field_ecology]
- [stmt:caveat-strain-name-collision; genotype_to_phenotype_enigma]
- [stmt:caveat-niche-breadth-sequencing-proxy; microbeatlas_metal_ecology]
- [stmt:pa14-strain-bias-caveat; cf_formulation_design]
- [stmt:e3-tier-a-provisional; ibd_phage_targeting]
- [stmt:limited-sample-size; pangenome_openness]
- [stmt:alphaearth-niche-opportunity; pathway_capability_dependency]
- [stmt:rerun-ecotype-environmental-only; env_embedding_explorer]
- [stmt:bacterial-pathogen-concentration; paperblast_explorer]

# Pangenome Architecture

A microbial **pangenome** is the union of all genes found across the genomes of a species or clade. It is conventionally partitioned into a **core genome** of genes present in nearly every strain and an **accessory genome** of genes that come and go between strains, down to **singletons** found in only one. "Pangenome architecture" is the study of how genes distribute across that core/accessory axis: which functions are conserved, which are variable, how variable genes are acquired and lost, and what that structure reveals about selection, ecology, and evolution. This page exists because pangenome conservation is the connective tissue running through most of the compendium's projects: nearly every analysis of gene fitness, antimicrobial resistance, metabolic capability, mobile elements, or environmental adaptation eventually asks whether the genes in question sit in the conserved core or the variable accessory genome. The page synthesizes what the corpus collectively shows about that architecture, drawing on the BERDL `kbase_ke_pangenome` resource (gene-cluster conservation across roughly 27,690 microbial species and 293,000 genomes, GTDB r214) cross-referenced with RB-TnSeq fitness data, GapMind pathway predictions, and functional annotations.

## Overview

The corpus repeatedly returns to one organizing idea: the position of a gene on the core/accessory axis is informative but rarely deterministic, and several long-standing intuitions about it turn out to be wrong. Connecting the Fitness Browser (RB-TnSeq fitness for ~194,000 genes across 43 bacteria) to the KBase pangenome shows that the conserved genome is the most functionally *active* part of the genome rather than the most inert. RB-TnSeq is a pooled transposon-mutagenesis assay that measures each gene's fitness contribution across many growth conditions; mapping those genes to pangenome clusters lets the corpus ask whether functional importance predicts conservation. It does, but as a continuous gradient rather than a clean dichotomy. Most genes in well-characterized bacteria are core regardless of their properties, which imposes a ceiling on every enrichment test and is the recurring statistical theme of this page.

Two complementary partitionings recur. The first is the **two-speed genome**: a universal split in which core genes are enriched for ancient metabolic and informational machinery while novel/accessory genes are enriched for mobile elements and defense systems. The second is **pangenome openness** (operationalized as one minus the core gene fraction, or equivalently the accessory-plus-singleton share): a single summary of how variable a species' gene content is. Openness behaves more subtly than its proponents expected, predicting some ecological traits strongly while failing to predict others at all.

## What the Corpus Shows

**A fitness–conservation gradient, but a weak one.** A quantitative gradient runs from essential genes (~82% core) to always-neutral genes (~66% core) across 194,216 protein-coding genes in 43 bacteria, so more important genes are more conserved. The relationship is continuous across the full essential-to-neutral spectrum, not a binary essential/non-essential split, and it strengthens with breadth: conservation rises from 66% for genes important in zero experiments to 79% for genes important in twenty or more. The corpus is honest that this signal is modest. Conservation is only *weakly* predicted by fitness importance, single-gene-knockout measurements miss epistatic interactions, and in direct logistic regression gene length is a far stronger predictor of core status (cross-validated AUC ~0.645) than any fitness effect (AUC near 0.5). The experimentally defined universally essential genome is small and deeply conserved: only 859 of 17,222 cross-organism ortholog families (5.0%) are essential in all 48 tested organisms, dominated by ribosomal proteins plus a handful of housekeeping genes, and conservation breadth tracks essentiality (universally essential genes are 91.7% core versus 80.7% for non-essential).

**The burden paradox.** Against the streamlining model, which casts accessory genes as the metabolic burden a genome would shed if it could, core genes are *more* likely to be costly: 24.4% show positive fitness when deleted (i.e., the cell grows better without them in some condition) versus 19.9% for accessory genes. Core genes also have heavier fitness tails in both directions and are 1.78x more likely to carry strong condition-specific phenotypes. The paradox is function-specific, driven by Protein Metabolism, Motility, and RNA Metabolism, while Cell Wall genes reverse the pattern. A selection-signature matrix crossing lab fitness cost against pangenome conservation identifies 28,017 genes that are simultaneously costly in the lab and conserved in nature as the strongest evidence for purifying selection, and a separate class of 5,526 costly-and-dispensable genes as candidates for ongoing gene loss.

**Costly-and-dispensable genes look like HGT debris.** Those 5,526 genes carry the hallmarks of recently acquired DNA: they are poorly annotated (50.8% with SEED annotations versus 74.9% for costly-and-conserved genes), shorter (median 615 bp versus 765 bp), taxonomically restricted (44.5% orphans), and overwhelmingly mobile genetic elements (11.7x enriched in the SEED Phage/Transposon/Plasmid category). They are depleted in core metabolic categories. Yet 14.1% still carry condition-specific phenotypes, so they are not inert.

**The two-speed genome is universal.** A COG-category analysis across 32 species and 9 phyla finds novel/singleton genes most strongly enriched in mobile-element functions (COG L, +10.88%, 100% cross-species consistency) and defense (COG V, +2.83%, 100% consistency), while core genes are enriched for nucleotide and coenzyme metabolism and most strongly *depleted* of novel-gene signal in translation (COG J, -4.65%). The same mobile/defense signature reappears across analyses: antimicrobial resistance genes, prophage markers, the SNIPE defense system, and pathogenic plant-microbe markers all skew accessory.

**Openness predicts ecology selectively.** Where openness fails: a dedicated project found no significant correlation between openness and either environmental or phylogenetic effect sizes on gene content (Spearman rho near zero, p > 0.5), so whether a species has an open or closed pangenome does not predict whether environment or phylogeny dominates its gene-content variation — consistent with the view of HGT as opportunistic rather than ecologically directed. Where openness succeeds: across 1,872 species, high core fraction is strongly *negatively* correlated with ecological niche breadth (r = -0.445), open pangenomes have broader niche breadth (r = 0.324), and the number of variable metabolic pathways correlates with openness (partial Spearman rho = 0.530 after controlling for genome count). The reconciliation seems to be that openness tracks ecological versatility and metabolic-capability variation but not the abstract eco-versus-phylo decomposition of gene content.

**Conservation extends from genes to modules and pathways.** ICA-derived co-regulated fitness modules are enriched in the core genome (86.0% core versus 81.5% baseline, OR = 1.46, p = 1.6e-87), with 59% of modules more than 90% core, extending the pangenomic concept of "core" from individual genes to functional units. At the pathway level, amino-acid biosynthesis pathways show the strongest dependence on accessory genes (core-vs-all completeness gaps ~0.14), direct evidence for **Black Queen** distribution — the evolutionary loss of costly functions that can be provided by neighboring community members as public goods — of biosynthetic capacity across strains.

## Projects and Evidence

The evidence behind this page spans roughly fifty projects, which cluster into several lines of work.

**Fitness–conservation synthesis.** The `conservation_fitness_synthesis`, `fitness_effects_conservation`, `conservation_vs_fitness`, `costly_dispensable_genes`, and `core_gene_tradeoffs` projects jointly establish the gradient, the burden paradox, and the costly/dispensable class. Mapping Fitness Browser genes to pangenome clusters by sequence alignment produced ~177,863 high-identity links for 44 of 48 organisms, of which 82.0% fell in core clusters; the essential-in-core enrichment is real but modest (median OR = 1.56) precisely because most genes are core anyway. The `essential_genome` project supplies the cross-species essential-gene census.

**Modules and co-inheritance.** `module_conservation`, `fitness_modules`, and `cofitness_coinheritance` show that co-regulated modules are core-enriched, that 156 module families span multiple organisms (one spanning 21), and that co-regulation constrains co-inheritance more than pairwise functional similarity does — though accessory modules show the strongest co-inheritance signal because core genes have too little presence/absence variance to detect.

**Openness and metabolic capability.** `pangenome_openness`, `pangenome_pathway_geography`, `pathway_capability_dependency`, `metabolic_capability_dependency`, `openness_functional_composition`, and `pangenome_pathway_ecology` work through what openness does and does not predict, anchored to GapMind pathway predictions. Several of these are partly or wholly at the proposal/in-progress stage. The Black Queen signal appears at the level of clade openness (latent-capability fraction correlates with openness, rho = 0.69) but not at the per-pathway conservation level, suggesting it operates through genome dynamics rather than per-pathway ratios.

**AMR architecture.** `amr_pangenome_atlas`, `amr_fitness_cost`, `amr_strain_variation`, `amr_environmental_resistome`, and `resistance_hotspots` consistently find AMR genes depleted from the core (30.3% core versus 46.8% baseline, OR = 0.49, universal across 63.7% of tested species), strongly phylogenetically clustered (Klebsiella leading), and highly variable within species (>90% of AMR gene-species occurrences variable or rare). Crucially, core and accessory AMR genes have *identical* fitness distributions, so pangenome location is decoupled from fitness cost; resistance mechanism, not acquisition recency, predicts conservation.

**Mobile elements and defense.** `prophage_amr_comobilization`, `prophage_ecology`, and `snipe_defense_system` map prophages (universal across all species, predominantly accessory) and defense systems (SNIPE 86.7% accessory) and test prophage–AMR co-localization at pangenome scale, finding a species-level association but only weak gene-neighborhood proximity effects.

**Functional dark matter.** `functional_dark_matter`, `truly_dark_genes`, and `paperblast_explorer` use pangenome links to triage uncharacterized genes: 69.3% of 57,011 dark genes link to the pangenome, bakta reannotates most, and only ~6,427 (16.3%) are "truly dark" — these are shorter, less core (43.1%), and bear HGT signatures.

**Organism- and trait-specific studies.** A long tail of projects applies the core/accessory lens to particular systems: PHB granule biosynthesis (`phb_granule_ecology`, phaC in 21.9% of species, HGT-spread when discordant), plant growth promotion (`pgp_pangenome_ecology`, PGP genes predominantly core, rejecting an HGT-spread hypothesis; `plant_microbiome_ecotypes`, beneficial genes core and pathogenic genes accessory), lanthanide methylotrophy, Acinetobacter ADP1, Pseudomonas carbon catabolism, subsurface Bacillota_B, metal ecology, and cystic-fibrosis formulation design, among others.

## Connections

Pangenome architecture is the shared substrate for many other pages in this wiki, which is why it is so heavily backlinked.

- [Gene Fitness](gene-fitness.md) is the closest companion: the fitness–conservation gradient, the burden paradox, and the costly/dispensable class all come from crossing RB-TnSeq fitness with pangenome conservation.
- [Amr Resistome](amr-resistome.md) and [Metal Resistance](metal-resistance.md) depend on the finding that resistance genes are predominantly accessory and decoupled from fitness cost, with intrinsic resistance core and acquired resistance accessory.
- [Mobile Genetic Elements](mobile-genetic-elements.md) is the mechanistic counterpart: the two-speed genome's mobile/defense-enriched accessory genome *is* the mobile-element compartment, and prophage and defense-system distributions track it.
- [Metabolic Pathways](metabolic-pathways.md) and [Microbial Ecotypes](microbial-ecotypes.md) connect through openness: accessory-dependent biosynthesis, Black Queen distribution, and within-species metabolic ecotypes are all read off pangenome structure.
- [Environment Biogeography](environment-biogeography.md) links via the openness–niche-breadth relationship, which is one of the strongest ecological signals openness produces.
- [Functional Dark Matter](functional-dark-matter.md) uses pangenome links and module membership to prioritize uncharacterized genes for study.
- [Microbial Ecotypes](microbial-ecotypes.md), [Subsurface Genomics](subsurface-genomics.md), [Microbiome Engineering](microbiome-engineering.md), and [Adp1 Model System](adp1-model-system.md) each apply the core/accessory framework to specific organisms or habitats.

The primary data underlying the page is the [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) collection, joined with [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md) fitness data, [Kbase Genomes](../data/kbase-genomes.md), and [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md).

## Caveats and Open Directions

The corpus is unusually candid about the limits of pangenome-conservation inference, and three problems recur.

**The ceiling problem.** Because baseline core fractions are high (~81.5% genome-wide for well-studied bacteria, even higher within individual organisms), every enrichment is squeezed against a ceiling. The essential-in-core enrichment is modest for exactly this reason, the module enrichment is bounded by the ~81.5% baseline, and a single-organism study of DvH with a 76.3% baseline core fraction compresses effect sizes. Several projects hit a related **prevalence ceiling** in co-occurrence analyses: most Fitness Browser genes map to core clusters above 95% prevalence where presence/absence variance is negligible, so co-inheritance phi approaches zero for real and random pairs alike. Binary core/auxiliary labels lose resolution that a quantitative per-genome carriage fraction would recover — a frequently noted opportunity.

**Confounders, especially genome size and phylogeny.** Genome size repeatedly turns out to be the dominant driver: it is the single best predictor of prophage burden, it confounds the apparent PHB–niche-breadth link (which vanishes after control, partial rho = -0.047), and it drives a plant-microbe "dual-nature" rate that ranges from 54% to 87% across size quartiles. Phylogeny is the other pervasive confounder: a clay-subsurface "toolkit" signal turns out to track the Bacillota_B lineage rather than habitat, and most projects controlling only for genome count and taxonomy (rather than full phylogenetic independent contrasts) acknowledge residual phylogenetic structure. Gene length is confounded with both fitness-measurement quality and core status, since short genes receive fewer transposon insertions and core genes tend to be longer.

**Data-quality and execution gaps.** Species-level matching across databases is lossy (56.6% of BacDive strains matched no GTDB species; E. coli is entirely absent from the GapMind pangenome dataset because too many genomes existed for species-level analysis, shrinking one study to a 7-organism pilot). Annotation choices matter: bakta reannotates 83.7% of "dark" genes, so older dark-gene counts overestimate true novelty, and a flagged join on the wrong key (`gene_id` instead of `gene_cluster_id`) can silently return wrong annotations. A reported 16-percentage-point fitness gradient is undermined by a figure/text discrepancy traced to computing percentages only over mapped genes, and two essential-core rates (82% vs 86%) are reported without full reconciliation. Several projects (`temporal_core_dynamics`, `pangenome_pathway_ecology`, `openness_functional_composition`) are not yet executed — code without outputs — so their hypotheses about temporal core erosion and openness-modulated COG enrichment remain untested. Practical scale limits also bite: COUNT(*) queries on the billion-row pangenome tables time out, forcing LIMIT-based sampling inside JupyterHub.

The clearest open directions are to replace binary conservation with a quantitative carriage metric, to add proper phylogenetic correction and multiple-testing control throughout, to execute the proposal-stage openness and temporal projects, and to use AlphaFold structure prediction to crack the residual truly-dark protein families.

## Sources

- [stmt:dual-dataset-synthesis; conservation_fitness_synthesis]
- [stmt:fitness-conservation-gradient; conservation_fitness_synthesis]
- [stmt:continuous-not-binary-claim; fitness_effects_conservation]
- [stmt:breadth-predicts-conservation; fitness_effects_conservation]
- [stmt:weak-prediction-caveat; fitness_effects_conservation]
- [stmt:gene-length-stronger-than-fitness; field_vs_lab_fitness]
- [stmt:burden-paradox-core-more-costly; conservation_fitness_synthesis]
- [stmt:core-genes-condition-specific-tradeoffs; conservation_fitness_synthesis]
- [stmt:function-specific-burden-finding; core_gene_tradeoffs]
- [stmt:selection-signature-purifying; conservation_fitness_synthesis]
- [stmt:costly-dispensable-are-mge; costly_dispensable_genes]
- [stmt:hgt-debris-interpretation; costly_dispensable_genes]
- [stmt:five-percent-universally-essential; essential_genome]
- [stmt:essentiality-tracks-core-conservation; essential_genome]
- [stmt:two-speed-genome; cog_analysis]
- [stmt:novel-genes-mobile-enriched; cog_analysis]
- [stmt:novel-genes-defense-enriched; cog_analysis]
- [stmt:module-genes-enriched-core; module_conservation]
- [stmt:most-modules-are-core; module_conservation]
- [stmt:modules-stronger-coinheritance; cofitness_coinheritance]
- [stmt:no-correlation-openness-effects; pangenome_openness]
- [stmt:openness-defined-from-core-fraction; pangenome_openness]
- [stmt:core-fraction-negative-niche; pangenome_pathway_geography]
- [stmt:pangenome-niche-breadth; pangenome_pathway_geography]
- [stmt:variable-pathways-open-pangenomes; pathway_capability_dependency]
- [stmt:amino-acid-accessory-dependence; pathway_capability_dependency]
- [stmt:openness-correlates-latent-rate; metabolic_capability_dependency]
- [stmt:amr-depleted-from-core; amr_pangenome_atlas]
- [stmt:amr-depletion-universal; amr_pangenome_atlas]
- [stmt:amr-core-accessory-identical; amr_fitness_cost]
- [stmt:amr-variable-rare-within-species; amr_strain_variation]
- [stmt:core-accessory-gradient; amr_environmental_resistome]
- [stmt:pangenome-amr-prophage-census; prophage_amr_comobilization]
- [stmt:prophage-modules-universal; prophage_ecology]
- [stmt:snipe-predominantly-accessory; snipe_defense_system]
- [stmt:darkness-spectrum-tiers; functional_dark_matter]
- [stmt:truly-dark-census-16pct; truly_dark_genes]
- [stmt:phac-prevalence-21-percent; phb_granule_ecology]
- [stmt:pgp-genes-predominantly-core; pgp_pangenome_ecology]
- [stmt:beneficial-core-pathogenic-accessory; plant_microbiome_ecotypes]
- [stmt:modest-enrichment-caveat; conservation_vs_fitness]
- [stmt:enrichment-modest-ceiling; module_conservation]
- [stmt:prevalence-ceiling-caveat; cofitness_coinheritance]
- [stmt:binary-conservation-caveat; costly_dispensable_genes]
- [stmt:niche-breadth-confounded-genome-size; phb_granule_ecology]
- [stmt:toolkit-phylum-confound; clay_confined_subsurface]
- [stmt:genome-size-confound-dual-nature; plant_microbiome_ecotypes]
- [stmt:species-matching-lossy; bacdive_metal_validation]
- [stmt:ecoli-absent-pilot-scope; essential_metabolome]
- [stmt:bakta-reannotation-overestimate; functional_dark_matter]
- [stmt:figure1-text-discrepancy; conservation_fitness_synthesis]
- [stmt:analysis-not-executed; temporal_core_dynamics]
- [stmt:caveat-execution-pending; pangenome_pathway_ecology]
- [stmt:count-query-timeout; resistance_hotspots]
- [stmt:quantitative-conservation-metric-opportunity; field_vs_lab_fitness]
- [stmt:opportunity-dark-family-alphafold; paperblast_explorer]

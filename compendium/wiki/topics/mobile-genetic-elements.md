# Mobile Genetic Elements

## Overview

A **mobile genetic element** (MGE) is a stretch of DNA that can move — within a genome or between genomes — independently of the host chromosome's normal vertical inheritance. The category covers plasmids, transposons and insertion sequences, integrative conjugative elements, prophages (bacteriophage genomes integrated into a host), and the type IV secretion systems (T4SS) and integrases that mobilize them. Their importance is that they carry the *mobilome*: the fraction of a bacterial genome that is gained and lost by horizontal gene transfer (HGT) rather than passed strictly from parent to daughter cell. This page exists because roughly thirty independent projects in this corpus, none of them about MGEs as their primary subject, keep arriving at the same place — that the accessory, variable, recently acquired portion of a genome is overwhelmingly mobile, and that mobility is the mechanism behind a startling range of observations from antibiotic resistance to phage defense to carbohydrate metabolism. Collecting those convergences in one place is the point of the page.

The reader who knows genomics but not this niche should hold a few terms in mind. The *core genome* of a species is the set of gene families present in essentially every strain; the *accessory genome* is everything variable, and *pangenome openness* is the tendency of a species to keep accumulating new accessory genes. A *singleton* is a gene family seen in only one genome — the extreme of accessory. Most of the analyses below detect mobility indirectly, by annotation: a gene is called "mobile" if it carries Pfam/COG/SEED signatures of phage, transposase, integrase, or plasmid functions, or if it sits physically next to such a gene. That indirect detection is a strength (it scales to hundreds of thousands of genomes) and a recurring weakness (it conflates active elements with domesticated remnants), and the corpus is unusually honest about the gap.

## What the Corpus Shows

The most reproduced result is a **two-speed genome**: the genes that vary between strains are not a random sample of functions but are sharply enriched for mobility. A COG-category analysis across 32 species and 9 phyla found that novel/singleton genes are most strongly enriched in mobile-element functions (COG L, +10.88% at 100% consistency — the single strongest signal in that study) and secondarily in defense systems (COG V, +2.83%), establishing this as a near-universal pattern. The costly-dispensable-genes project gave the same conclusion a fitness anchor: of 5,526 genes that are simultaneously dispensable (knockout-neutral) and costly to carry, the overwhelming majority are MGEs — 7.45x more likely to carry mobile-element keywords and 11.7x enriched in the SEED Phage/Transposon/Plasmid category than conserved-and-costly genes, with shorter median length (615 vs 765 bp) consistent with insertion sequences and gene fragments. These genes look like the **genomic debris of HGT** — IS elements, prophage remnants, transposases, and defense systems caught in the act of being acquired or shed. The truly-dark-genes project converges from annotation space: unannotatable "dark" genes are 4.2x less likely to have cross-organism orthologs, deviate in GC content from their host genome, and 12% sit within two genes of a mobile element, with contiguous "dark islands" of hypothetical neighbors that look like recently acquired genomic islands outpacing the annotation databases.

A second theme is that **mobility tracks the accessory genome and the functions that ride on it**. Antibiotic- and metal-resistance gene families are the least conserved functional classes (73.4% and 71.2% core, both below baseline), consistent with resistance being disproportionately an accessory, MGE-borne trait. *Klebsiella pneumoniae* is the extreme case — 1,115 AMR gene clusters of which only 7 are core, so nearly its entire resistome is accessory and HGT-driven. The atlas-scale view shows the dichotomy cleanly: intrinsic beta-lactamases are 54.9% core while canonical mobile determinants such as *blaTEM*, *tet(C)*, and *ant(2'')-Ia* are 0% core. Yet the corpus repeatedly resists the naive reading that "accessory equals freshly transferred." Acquired AMR genes carry *stronger* phylogenetic signal than intrinsic ones (Mantel r = 0.222 vs 0.117), AMR genes cluster into 1,517 tightly co-inherited "resistance islands" (mean phi = 0.827, 88% multi-mechanism), and the apparent lesson is that resistance elements, once acquired, are often stably and clonally inherited — which is why several projects argue that tracking clonal lineages may beat tracking individual genes for surveillance.

A third theme is **prophages as both vehicles and ecology**. Two independent prophage censuses agree that prophage-associated gene clusters are essentially universal — all 27,702 species in the BERDL pangenome carry them — but that the informative variation lives in the structurally variable head, tail, and anti-defense modules, not the near-universal packaging/lysis/regulation backbone (which is partly domesticated remnant under purifying selection). Prophage module composition is shaped more by environment than by host phylogeny (PERMANOVA F = 30.04 vs 6.17), and anti-defense modules are enriched in human-associated bacteria beyond phylogenetic expectation, reading as host–phage arms races intensifying where immune systems are under strongest selection. Connecting prophages to resistance, the co-mobilization project found that prophage marker density explains ~30% of variance in AMR breadth and that over half of AMR instances in the most-burdened species share contigs with strict phage markers like terminase — a transduction-consistent signal, though the authors are careful that high-recombination species could independently accumulate both.

Finally, the corpus contributes several **specific mobile systems**. The SNIPE defense project characterized a phage-defense nuclease (diagnostic domain DUF4041/PF13250) across 4,572 gene clusters in 1,696 species and 33 phyla, predominantly accessory (only 13.3% core) with a patchy cross-phylum distribution that points to HGT of defense islands; it elegantly resolves a resistance-versus-cost trade-off by cleaving phage DNA at the ManYZ sugar pore while leaving the transporter functional. The T4SS–CAZy project proposed that conjugative machinery mobilizes carbohydrate-active-enzyme cassettes: ~21.8% of 30,497 environmental MAGs carry T4SS, 92 CAZy families co-occur with T4SS within 10 kb (GT2 glycosyltransferase the top hit), and a GT2 gene tree recovered 77 HGT events including 32 cross-phylum cases — a route mechanistically distinct from the TonB-dependent PUL paradigm. And a domain-wide HGT/innovation atlas of 13.7M producer/participation scores across 18,989 GTDB species formalized the intuition that *modular* systems exchange more: architecturally promiscuous gene families (a median 46 Pfam architectures per KO) are HGT-prone, while strict housekeeping genes are ancient and vertically inherited, with the recent-to-ancient gain ratio itself a function-class signature (CRISPR-Cas 24.5x recent-skewed, housekeeping ~1x).

## Projects and Evidence

The evidence falls into a few clusters. The **functional-composition** group establishes the two-speed genome as the spine: `cog_analysis` produced the COG L/V enrichment, `openness_functional_composition` is the (as-yet-untested) follow-on asking whether that enrichment *scales* with pangenome openness or is flat-out universal, and `costly_dispensable_genes` plus `truly_dark_genes` and `functional_dark_matter` supply the fitness and annotation-space evidence that the accessory tail is mobile debris. `module_conservation` and `cofitness_coinheritance` add that some accessory gene modules are co-regulated and co-inherited but stop short of claiming HGT directly.

The **resistance** group ties mobility to AMR. `amr_strain_variation` resolved the resistance islands and the counterintuitive clonal-inheritance signal; `amr_pangenome_atlas` quantified the intrinsic/acquired dichotomy; `amr_environmental_resistome` showed clinical and gut species acquire resistance by HGT while soil/aquatic species retain intrinsic chromosomal resistance; `amr_fitness_cost` and `field_vs_lab_fitness` contribute the cost-and-conservation framing; and `prophage_amr_comobilization` is the phage–AMR census. `metal_resistance_global_biogeography` and `microbeatlas_metal_ecology` flag that metal resistance and HGT machinery are distinct features (2.8% global metal prevalence vs 21.8% T4SS) with intermediate phylogenetic signal (Pagel's λ = 0.26–0.44) consistent with vertical core resistance plus HGT-driven accessory expansion.

The **prophage and defense** group is `prophage_ecology` (the universal-module census, environment-over-phylogeny, NMDC metagenomic validation), `prophage_amr_comobilization`, `snipe_defense_system`, and `ibd_phage_targeting`. The last is a phage-therapy design project that surfaces an MGE-adjacent caveat: a greedy set-cover yields a 5-phage cocktail covering 94.7% of 188 *E. coli* strains in PhageFoundry, but the two highest-priority Crohn's pathobionts (*H. hathewayi*, *M. gnavus*) have the weakest phage availability, and temperate (lysogenic) targets resist pure-phage treatment. The **HGT-mechanism** group is `gene_function_ecological_agora` (the innovation atlas and the producer/participation framework) and `t4ss_cazy_environmental_hgt` (conjugative CAZy transfer). A long tail of single-statement contributors — `pgp_pangenome_ecology`, `plant_microbiome_ecotypes`, `phb_granule_ecology`, `pangenome_openness`, `pangenome_pathway_ecology`, `temporal_core_dynamics`, `essential_genome`, `conservation_fitness_synthesis`, `amr_pangenome_atlas`, `cf_formulation_design` — each adds a mobility observation from its own functional vantage (PGP genes are mostly *core* despite transposase association; *phaC* shows 311 likely horizontal acquisitions; plant-associated genera carry higher mobilome burden yet their marker genes are under purifying selection).

## Connections

Mobile genetic elements sit underneath most structural topics in this wiki, which is why so many pages link back here. [Pangenome architecture](pangenome-architecture.md) is the closest neighbor: the core/accessory split *is* the substrate on which mobility acts, and the two-speed-genome and openness questions live at that interface. [AMR resistome](amr-resistome.md) is adjacent because MGEs are the *how* of acquired resistance — the resistance islands, the prophage co-mobilization, and the accessory-AMR enrichment all reduce to mobility — and [metal resistance](metal-resistance.md) connects through the GT2-neighborhood MAGs carrying ~11x more metal-resistance genes and through the shared accessory character of metal and antibiotic resistance. [Gene fitness](gene-fitness.md) underwrites the costly-dispensable and SNIPE results via transposon-mutant fitness data (notably the first SNIPE homologue with genome-wide knockout phenotypes, in *Methanococcus maripaludis*). [Functional dark matter](functional-dark-matter.md) overlaps directly: dark genes and recently acquired MGEs are largely the same population, since HGT outpaces annotation. [Microbial ecotypes](microbial-ecotypes.md) connects through the within-species variation that mobility creates, and [microbiome engineering](microbiome-engineering.md) through phage-therapy cocktail design, where prophages and defense systems determine what is treatable. Looser but real links run to [metabolic pathways](metabolic-pathways.md) (T4SS-mobilized CAZy cassettes, *phaC*, PQQ genes), [environment biogeography](environment-biogeography.md) (prophage burden tracking pH and temperature, biome-enriched HGT), and [subsurface genomics](subsurface-genomics.md) (the *Pseudomonas stutzeri* RCH2 mobile-element outlier). The underlying genomic substrate is the [KBase/BERDL pangenome](../data/kbase-ke-pangenome.md), with prophage burden cross-validated against [NMDC metagenomes](../data/nmdc-arkin.md) and phage coverage drawn from [PhageFoundry](../data/phagefoundry.md).

## Caveats and Open Directions

The single biggest caveat is **detection method**. Across the prophage work, prophages were called from eggNOG or keyword/Pfam annotations rather than dedicated predictors, which inflates prevalence by including domesticated remnants and bacterial homologs at an uncharacterized false-positive rate, and may miss divergent prophages entirely. The proposed fix is consistent across projects: run geNomad, VIBRANT, or PHASTER on representative genomes to calibrate false-positive and false-negative rates before trusting the module-prevalence numbers. The same annotation limit hits the SNIPE census — only 54 of 4,572 DUF4041 clusters show the Mug113 (PF13455) nuclease co-annotation, so many SNIPE domains likely go undetected — though the zero co-occurrence with the canonical GIY-YIG family PF01541 is a genuine biological result, not an artifact. The NMDC validation of prophage burden is indirect, assuming genus-level conservation of prophage content that need not hold for recently gained or lost prophages.

Several headline mobility claims are explicitly hedged. The T4SS–CAZy HGT signal is observational: the central claim is associative, the 10-kb synteny threshold and cross-phylum incongruence rate are unvalidated until a permutation test and housekeeping-gene null baseline are run, and the flagship Node_4915 result (35 genes, 8 phyla, divergence 4.843) still needs BLAST verification against NCBI to rule out chimeric or misclassified sequences. The "mobile defense islands" composite-COG category (LV, mobile+defense) is a low-confidence suggestion of functional modularity, and the interpretation that accessory module families are horizontally transferred units is flagged as speculative and not directly supported. The prophage–AMR proximity effect is real but modest and threshold-dependent — absent or reversed at very close range — leaving open whether prophages directly mobilize resistance or high-recombination species simply acquire both. The innovation-atlas project also warns that recent between-species gain and within-species pangenome openness are *uncorrelated* (Spearman r = -0.011 across 894 genera), so openness cannot validate acquisition-depth signals, and that deep-rank verdicts like the cyanobacterial PSII "Innovator" status are strongly rank-dependent and must be set on biological grounds.

There are also informative counter-cases that complicate a simple "accessory = mobile" story. Plant-interaction marker genes are *less* mobile than the genomic average (singleton enrichment ratio 0.78, Wilcoxon p < 1e-300) despite frequent transposase association — purifying selection, not ongoing mobility. PGP genes are predominantly core, rejecting the hypothesis that they spread mainly by HGT, with *pqqD* the lone horizontal outlier (55.5% core). The pre-registered PSII, mycolic-acid, and PUL gene sets carry near-zero MGE-machinery rates against a 1.37% atlas baseline — they are exchanged frequently but are not *themselves* phage or transposon genes. The clearest open directions are mechanistic and integrative: flag phage/plasmid/integron context per HGT gain event to test whether high-exchange genes are MGE-mediated; build composition-based donor inference (currently blocked because per-CDS sequence is not in BERDL queryable schemas); characterize the 7,084 orphan essential genes and the costly-dispensable set for mobile-element residence; and revisit the AMR-on-plasmids question once dedicated mobile-element annotations land in BERDL. Across the board, the recurring obstacle is that mobility is being inferred from annotation, and the recurring remedy is dedicated MGE prediction plus sequence-level validation.

## Sources

- [stmt:novel-genes-mobile-enriched; cog_analysis]
- [stmt:novel-genes-defense-enriched; cog_analysis]
- [stmt:mobile-defense-islands; cog_analysis]
- [stmt:composite-cog-meaningful; cog_analysis]
- [stmt:costly-dispensable-are-mge; costly_dispensable_genes]
- [stmt:hgt-debris-interpretation; costly_dispensable_genes]
- [stmt:shorter-genes; costly_dispensable_genes]
- [stmt:psrch2-outlier; costly_dispensable_genes]
- [stmt:accessory-hgt-signatures; truly_dark_genes]
- [stmt:dark-islands-neighbors; truly_dark_genes]
- [stmt:two-speed-genome-prior; openness_functional_composition]
- [stmt:cog-analysis-untested-openness; openness_functional_composition]
- [stmt:resistance-genes-accessory-mge; field_vs_lab_fitness]
- [stmt:kpneumoniae-accessory-resistome; amr_environmental_resistome]
- [stmt:core-intrinsic-accessory-acquired; amr_environmental_resistome]
- [stmt:intrinsic-acquired-dichotomy; amr_pangenome_atlas]
- [stmt:acquired-stronger-signal; amr_strain_variation]
- [stmt:resistance-islands-coinherited; amr_strain_variation]
- [stmt:clonal-lineage-surveillance; amr_strain_variation]
- [stmt:prophage-density-predicts-amr-breadth; prophage_amr_comobilization]
- [stmt:amr-prophage-contig-sharing; prophage_amr_comobilization]
- [stmt:proximity-threshold-dependence; prophage_amr_comobilization]
- [stmt:caveat-keyword-prophage-detection; prophage_amr_comobilization]
- [stmt:prophage-modules-universal; prophage_ecology]
- [stmt:environment-over-phylogeny; prophage_ecology]
- [stmt:structural-antidefense-human-enriched; prophage_ecology]
- [stmt:universal-modules-domesticated-remnants; prophage_ecology]
- [stmt:caveat-annotation-based-detection; prophage_ecology]
- [stmt:caveat-nmdc-indirect-inference; prophage_ecology]
- [stmt:snipe-widespread-1696-species; snipe_defense_system]
- [stmt:snipe-predominantly-accessory; snipe_defense_system]
- [stmt:snipe-resolves-resistance-cost-tradeoff; snipe_defense_system]
- [stmt:methanococcus-first-snipe-fitness; snipe_defense_system]
- [stmt:caveat-annotation-sensitivity; snipe_defense_system]
- [stmt:t4ss-prevalence-environmental-mags; t4ss_cazy_environmental_hgt]
- [stmt:t4ss-cazy-synteny; t4ss_cazy_environmental_hgt]
- [stmt:cross-phylum-hgt-events; t4ss_cazy_environmental_hgt]
- [stmt:gt2-metal-resistance-link; t4ss_cazy_environmental_hgt]
- [stmt:caveat-associative-not-causal; t4ss_cazy_environmental_hgt]
- [stmt:caveat-threshold-and-null-validation-pending; t4ss_cazy_environmental_hgt]
- [stmt:caveat-node4915-blast-pending; t4ss_cazy_environmental_hgt]
- [stmt:hgt-innovation-atlas; gene_function_ecological_agora]
- [stmt:architectural-promiscuity-hgt; gene_function_ecological_agora]
- [stmt:recent-ancient-ratio-signature; gene_function_ecological_agora]
- [stmt:preregistered-kos-not-phage-borne; gene_function_ecological_agora]
- [stmt:pangenome-openness-distinct-from-m22; gene_function_ecological_agora]
- [stmt:psii-rank-dependence; gene_function_ecological_agora]
- [stmt:five-phage-cocktail-coverage; ibd_phage_targeting]
- [stmt:phage-coverage-gap; ibd_phage_targeting]
- [stmt:markers-under-purifying-selection; plant_microbiome_ecotypes]
- [stmt:mobilome-enrichment-genus-level; plant_microbiome_ecotypes]
- [stmt:pgp-genes-predominantly-core; pgp_pangenome_ecology]
- [stmt:pqqd-hgt-outlier-caveat; pgp_pangenome_ecology]
- [stmt:hgt-phac-acquisition; phb_granule_ecology]
- [stmt:metal-vs-t4ss-distinct; metal_resistance_global_biogeography]
- [stmt:metal-amr-intermediate-phylogenetic-signal; microbeatlas_metal_ecology]
- [stmt:characterize-orphan-essentials-opportunity; essential_genome]
- [stmt:accessory-families-hgt-speculative; module_conservation]
- [stmt:mge-context-mechanism-opportunity; gene_function_ecological_agora]
- [stmt:mobile-element-context; amr_environmental_resistome]

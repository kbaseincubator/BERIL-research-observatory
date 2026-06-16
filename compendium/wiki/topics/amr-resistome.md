# AMR Resistome

## Overview

The **resistome** is the full collection of antimicrobial-resistance (AMR) genes a bacterium carries — both the *intrinsic* resistance functions encoded in its conserved [core genome](pangenome-architecture.md) and the *acquired* genes that arrive later by horizontal transfer and live in the variable accessory genome. This page synthesizes what a cluster of projects in this corpus found when they treated the resistome not as a clinical checklist but as an evolutionary object: a set of genes with a particular distribution across the bacterial pangenome, a particular phylogenetic and ecological signal, and a particular (and surprisingly small) fitness cost. The page exists because nine independent projects, working from the same large genomic resources, converge on a coherent picture of how resistance is organized across the bacterial domain — and because they disagree or hedge in informative ways that are worth recording in one place.

Most of the underlying analyses share a common substrate: AMR genes are detected across hundreds of thousands of genomes (typically with AMRFinderPlus against the [KBase/BERDL pangenome collection](../data/kbase-ke-pangenome.md), GTDB r214), classified by mechanism, and then cross-referenced against transposon-mutant fitness data from the [Fitness Browser](../data/kescience-fitnessbrowser.md). The reader who knows genomics but not this niche should hold three terms in mind. *Pangenome openness* is the ratio of variable (accessory) to conserved (core) genes in a species — open pangenomes accumulate new genes readily. *RB-TnSeq* (random-barcode transposon sequencing) measures the fitness contribution of each gene by knocking it out with a transposon and tracking how the mutant fares; a near-zero fitness value means the gene is dispensable under that condition. *Condition-dependent essentiality* is the idea that a gene that looks useless in rich lab medium can become essential under stress — including under antibiotic — which is exactly the signature one expects of a resistance gene.

## What the Corpus Shows

The single most reproduced result is that **AMR genes are depleted from the bacterial core genome and concentrated in the accessory genome**. Across 14,723 species, the [pangenome atlas project](pangenome-architecture.md) found only 30.3% of AMR genes were core against a 46.8% baseline (odds ratio 0.49), a 2.2-fold enrichment in the auxiliary genome, and the depletion held for 63.7% of the 4,252 species tested individually. The strain-variation project saw the same thing at finer resolution: across 1,305 species and 180,025 genomes, over 90% of AMR gene-by-species occurrences are variable or rare within a species, only 7.5% are fixed, and two strains of one species typically share less than 60% of their resistance repertoire. The environmental-resistome and field-vs-lab projects corroborate the trend, the latter noting that antibiotic-resistance (73.4% core) and heavy-metal-resistance (71.2% core) gene families fall below the conservation baseline, consistent with their being disproportionately accessory traits on [mobile genetic elements](mobile-genetic-elements.md).

That depletion is not uniform across mechanisms — there is an **intrinsic/acquired conservation dichotomy**, quantified for the first time at this scale. Intrinsic beta-lactamases are 54.9% core, while regulatory genes (6.5% core) and canonical mobile resistance determinants such as *blaTEM*, *tet(C)*, and *ant(2'')-Ia* are essentially 0% core. The fitness-cost project sharpened this: resistance mechanism strongly predicts conservation status (chi-square = 69.3), with metal-resistance genes 44% accessory while efflux and enzymatic-inactivation genes are overwhelmingly core. The environmental project supplies the *why*: the pattern is driven by ecology, because efflux pumps serve host-associated organisms across many conditions and so stay core, whereas metal resistance is only needed in metal-rich soils and waters and so remains a dispensable accessory trait — a link developed further on the [metal resistance](metal-resistance.md) page.

The most counterintuitive findings concern **fitness cost**. The textbook expectation is that resistance is costly and that recently acquired genes should be costlier than ancestral ones. Neither held. In a pan-bacterial meta-analysis of 27M fitness measurements across 25 organisms, AMR knockouts had systematically *higher* fitness than non-AMR knockouts under non-antibiotic conditions (pooled effect +0.086, positive in all 25 of 25 organisms) — that is, resistance genes are unusually dispensable when no drug is present. Core (intrinsic) and accessory (acquired) AMR genes had virtually identical fitness distributions (Cohen's d = 0.002, p = 0.33), directly refuting the recency-equals-cost prediction, and baseline cost did not vary by mechanism (Kruskal-Wallis p = 0.89). The cost that exists is *real but small*, which the authors read as reconciling why resistance persists long after antibiotics are withdrawn. Crucially, the picture inverts under selection: under any antibiotic, 57% of AMR genes show a **fitness flip** and become relatively important, and the flip is mechanism-dependent — broad-spectrum efflux genes flip far more strongly than narrow-spectrum enzymatic genes (+0.094 vs -0.001). This is the condition-dependent essentiality signature applied to the resistome, and it ties directly to the broader [gene fitness](gene-fitness.md) page.

Beyond distribution and cost, two organizational themes recur. First, resistance is **physically and clonally clustered**, not scattered. The strain-variation project resolved 1,517 tightly co-inherited "resistance islands" across 54% of species (mean phi = 0.827), 88% of them combining multiple mechanisms — coordinated multi-drug defense modules. Counterintuitively, acquired AMR genes carry *stronger* phylogenetic signal than intrinsic ones (median Mantel r = 0.222 vs 0.117), implying acquired resistance is often clonally inherited within a lineage rather than freshly transferred — which is why the authors argue that tracking clonal lineages may beat tracking individual genes for surveillance. Roughly one in five species even split into two or more discrete AMR *ecotypes* by UMAP+DBSCAN clustering, connecting the resistome to [microbial ecotypes](microbial-ecotypes.md). Second, resistance co-localizes with **prophages**: a 100-species census found that species with higher prophage-marker density carry broader AMR repertoires (prophage density explaining ~30% of variance), and over half of AMR instances in the most-burdened species sit on contigs bearing strict phage markers like terminase — suggestive of transduction-mediated co-mobilization (see [mobile genetic elements](mobile-genetic-elements.md)).

## Projects and Evidence

The corpus splits into completed analyses, exploratory cross-links, and one project still at the planning stage.

The **pangenome atlas** (`amr_pangenome_atlas`) is the census backbone: 83K AMR hits across 14,723 species, the core-depletion result, the COG enrichment for defense systems (7.05x) and inorganic-ion transport, and the striking finding that heavy-metal resistance dominates the census — mercury alone is ~15,000 hits (18% of all AMR annotations) and arsenic adds ~6,000. It also showed AMR density is phylogenetically structured (Klebsiella leads at 206 clusters/species; Gammaproteobacteria carry 45% of all clusters) and that environmental-diversity embeddings from [AlphaEarth](environment-biogeography.md) predict AMR count (rho = 0.466), implying niche breadth enables resistance accumulation.

The **fitness-cost** project (`amr_fitness_cost`) supplies all the cost results above, plus the observation that only 4.6% of AMR genes were putatively essential (versus a ~14% background), reinforcing that resistance genes are more dispensable than typical genes. The **strain-variation** project (`amr_strain_variation`) provides the within-species view — resistance islands, ecotypes, clonal inheritance, and the validation that cross-species conservation class predicts within-species prevalence (77.3% of core AMR genes fixed; 78.7% of singletons rare). The **environmental-resistome** project (`amr_environmental_resistome`) establishes ecology as a predictor of resistome size: clinical and human-gut species carry ~2.5x more AMR clusters than soil/aquatic species, the accessory fraction rises along an ecological gradient (43% accessory in soil to 80% in human gut), and metal resistance is the single most environment-discriminating mechanism (~44–45% of soil/aquatic AMR but 6% in human gut). The **cofitness-networks** project (`amr_cofitness_networks`) maps AMR co-fitness neighborhoods across 28 organisms and finds support networks are organism-specific rather than mechanism-specific, that network size is uncorrelated with fitness cost, and that AMR genes sit inside unusually large multi-function ICA fitness modules.

Two projects are cross-cutting and partial. **Prophage co-mobilization** (`prophage_amr_comobilization`) is the phage-resistance census above, explicitly extending prior capsule-pangenome work to much larger scale. **Field-vs-lab** (`field_vs_lab_fitness`) and **microbeatlas metal ecology** (`microbeatlas_metal_ecology`) each contribute one anchoring result — the conservation ranking of resistance gene families, and the intermediate-but-significant phylogenetic signal of metal-AMR traits (Pagel's λ = 0.26–0.44). Finally, **resistance hotspots** (`resistance_hotspots`) is a planned project: it scopes mapping ARGs across 293,059 genomes and 27,690 species and testing the open-pangenome hypothesis, but it currently has zero completed analysis, skeleton notebooks only, and already hit a wall when the BERDL eggNOG and orthogroup tables proved inaccessible.

## Connections

The resistome touches most of the structural and ecological topics in this wiki. [Pangenome architecture](pangenome-architecture.md) is the most direct neighbor: the entire core-versus-accessory framing of resistance is a special case of pangenome openness, and the open-pangenome-carries-more-ARGs hypothesis lives at that interface. [Mobile genetic elements](mobile-genetic-elements.md) explain *how* accessory resistance moves — plasmids, transposons, integrative elements, and the prophages implicated in co-mobilization. [Metal resistance](metal-resistance.md) is adjacent because heavy-metal genes are the largest and most environment-discriminating slice of the AMR census, and the metal-fitness atlas is the natural place to test whether genes costly under standard conditions become protective under metal stress. [Gene fitness](gene-fitness.md) underwrites every cost and fitness-flip result via RB-TnSeq, and [microbial ecotypes](microbial-ecotypes.md) connects through the discrete AMR ecotypes that emerge within species. [Environment biogeography](environment-biogeography.md) supplies the AlphaEarth embeddings that link niche breadth and environmental distance to resistome composition. Connections to [functional dark matter](functional-dark-matter.md), [metabolic pathways](metabolic-pathways.md), [subsurface genomics](subsurface-genomics.md), and [microbiome engineering](microbiome-engineering.md) are looser but real — unclassified AMR hits overlap dark matter, efflux and metal resistance intersect metabolism, and the environmental gradient extends into subsurface and engineered communities.

## Caveats and Open Directions

Several findings rest on biased sampling and should be read with care. The clinical-carries-more-AMR result is partly an artifact of NCBI over-representing clinical isolates — clinical species are sequenced *because* they have AMR — and the same bias inflates AMR counts for human-associated species in the atlas. The environment–AMR relationship is correlational, with environment explaining only 2–13% of variance in AMR composition; it survives phylogenetic control in 20 of 141 families, but it is not causal. The fitness-cost estimates carry their own qualifiers: all 25 organisms are lab-adapted strains whose compensatory evolution may have eroded measurable cost, the +0.086 figure is a lower bound because ~4.6% of putatively essential AMR genes were censored from the fitness matrices, and the core-versus-accessory null should be read cautiously for species with few genomes (median 9), where the ≥95% core threshold is imprecise. The flagellar/biosynthesis enrichment in cofitness support networks may simply reflect shared dispensability under lab conditions rather than genuine co-regulation — a confound the authors propose to settle with a fitness-matched permutation test or by computing cofitness separately under antibiotic versus standard growth.

Methodological caveats also temper the census. Mechanism classification is keyword-based, leaving 22% of hits Other/Unclassified, and AMRFinderPlus scope includes stress-response genes, so the 83K hits are not all classical antibiotic resistance — a move to systematic CARD ontology mapping is the proposed fix. The lower phylogenetic signal of core AMR genes is partly a statistical artifact of near-zero Jaccard distances, and the absence of temporal trends most likely reflects sparse, noisy NCBI collection-date metadata rather than true stasis. The prophage–AMR association is explicitly correlation, not proof of phage-mediated transfer, since open-pangenome species may independently accumulate both; the fitness-cost angle could not be tested at all because Fitness Browser coverage barely overlaps the GTDB species analyzed. That fitness-mapping gap — different model organisms, different gene-ID schemes — is the recurring obstacle, and it is exactly what blocks the still-unstarted resistance-hotspots project, whose planned keyword-based ARG identification is underspecified and would benefit from sequence-similarity detection against CARD. The clearest open directions are integrative: cross-referencing metal-resistance fitness against the metal atlas, joining environment-AMR profiles to the cost data to ask whether clinical-enriched genes are costlier or merely under stronger selection, and revisiting the prophage and hotspot questions once BERDL mobile-element annotations and broader fitness coverage become available.

## Sources

- [stmt:amr-depleted-from-core; amr_pangenome_atlas]
- [stmt:amr-depletion-universal; amr_pangenome_atlas]
- [stmt:intrinsic-acquired-dichotomy; amr_pangenome_atlas]
- [stmt:dichotomy-quantified-first-time; amr_pangenome_atlas]
- [stmt:amr-cog-defense-enrichment; amr_pangenome_atlas]
- [stmt:metal-resistance-major-component; amr_pangenome_atlas]
- [stmt:amr-hotspots-clinical-pathogens; amr_pangenome_atlas]
- [stmt:alphaearth-diversity-predicts-amr; amr_pangenome_atlas]
- [stmt:clinical-species-more-amr; amr_pangenome_atlas]
- [stmt:sampling-bias-caveat; amr_pangenome_atlas]
- [stmt:mechanism-classification-caveat; amr_pangenome_atlas]
- [stmt:card-ontology-opportunity; amr_pangenome_atlas]
- [stmt:amr-universal-cost; amr_fitness_cost]
- [stmt:amr-core-accessory-identical; amr_fitness_cost]
- [stmt:amr-mechanism-no-cost-difference; amr_fitness_cost]
- [stmt:amr-antibiotic-flip; amr_fitness_cost]
- [stmt:amr-efflux-mechanism-dependent-flip; amr_fitness_cost]
- [stmt:amr-cost-is-small; amr_fitness_cost]
- [stmt:amr-low-essential-rate; amr_fitness_cost]
- [stmt:amr-mechanism-predicts-conservation; amr_fitness_cost]
- [stmt:amr-lab-adaptation-bias; amr_fitness_cost]
- [stmt:amr-essential-censoring-caveat; amr_fitness_cost]
- [stmt:amr-core-label-imprecision; amr_fitness_cost]
- [stmt:amr-cross-ref-metal-atlas; amr_fitness_cost]
- [stmt:amr-variable-rare-within-species; amr_strain_variation]
- [stmt:resistance-islands-coinherited; amr_strain_variation]
- [stmt:islands-multi-mechanism; amr_strain_variation]
- [stmt:acquired-stronger-signal; amr_strain_variation]
- [stmt:atlas-class-predicts-prevalence; amr_strain_variation]
- [stmt:amr-ecotypes; amr_strain_variation]
- [stmt:clonal-lineage-surveillance; amr_strain_variation]
- [stmt:core-signal-artifact; amr_strain_variation]
- [stmt:no-temporal-trend; amr_strain_variation]
- [stmt:clinical-amr-richness; amr_environmental_resistome]
- [stmt:core-accessory-gradient; amr_environmental_resistome]
- [stmt:metal-resistance-soil-aquatic; amr_environmental_resistome]
- [stmt:mechanism-conservation-ecology-link; amr_environmental_resistome]
- [stmt:environment-not-phylogeny-artifact; amr_environmental_resistome]
- [stmt:correlation-modest-effects; amr_environmental_resistome]
- [stmt:ncbi-sampling-bias; amr_environmental_resistome]
- [stmt:integrate-fitness-cost; amr_environmental_resistome]
- [stmt:organism-specific-networks; amr_cofitness_networks]
- [stmt:network-size-no-fitness-cost; amr_cofitness_networks]
- [stmt:amr-larger-modules; amr_cofitness_networks]
- [stmt:dispensability-confound; amr_cofitness_networks]
- [stmt:fitness-matched-permutation-opportunity; amr_cofitness_networks]
- [stmt:prophage-density-predicts-amr-breadth; prophage_amr_comobilization]
- [stmt:amr-prophage-contig-sharing; prophage_amr_comobilization]
- [stmt:extends-rendueles-correlation; prophage_amr_comobilization]
- [stmt:caveat-correlation-not-causation; prophage_amr_comobilization]
- [stmt:caveat-fitness-data-gap; prophage_amr_comobilization]
- [stmt:resistance-genes-accessory-mge; field_vs_lab_fitness]
- [stmt:metal-amr-intermediate-phylogenetic-signal; microbeatlas_metal_ecology]
- [stmt:pangenome-scale; resistance_hotspots]
- [stmt:project-planning-stage; resistance_hotspots]
- [stmt:eggnog-orthogroup-inaccessible; resistance_hotspots]
- [stmt:open-pangenome-hypothesis; resistance_hotspots]
- [stmt:keyword-arg-caveat; resistance_hotspots]
- [stmt:sequence-similarity-opportunity; resistance_hotspots]
- [stmt:no-findings-yet; resistance_hotspots]
- [stmt:fitness-mapping-caveat; resistance_hotspots]

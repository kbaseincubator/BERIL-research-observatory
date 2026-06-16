# Environment Biogeography

Microbial biogeography asks how the genes, taxa, and metabolic capabilities of microbes are distributed across the planet's environments, and what abiotic and ecological forces shape that distribution. This page synthesizes the corpus's evidence on that question: where particular functions are enriched (soil, rhizosphere, groundwater, host tissue, clinical settings), how strongly environment versus phylogeny governs gene content, and how well satellite-derived environmental context can be tied to genomes. It exists as a cross-cutting topic because almost every analysis in this wiki that touches geography, isolation source, or habitat eventually collides with the same two facts: the signal of environment on microbial function is often real but modest, and it is pervasively confounded by *how* and *where* we sample. The page therefore does double duty — it collects the positive biogeographic findings, and it gives an honest accounting of the sampling biases that make those findings hard to interpret.

## Overview

The corpus approaches biogeography from two complementary angles. The first is genome-centric: take large pangenome and isolate databases (hundreds of thousands of genomes), attach an environmental label or coordinate to each genome, and ask whether functional content tracks environment. The second is community-centric: take amplicon (16S) or metagenomic surveys of real communities and ask whether composition and functional potential shift along measured or inferred environmental gradients. A recurring bridge between the two is **AlphaEarth**, a set of 64-dimensional embeddings derived from satellite imagery that encode geographic and environmental context (climate, land use, vegetation) at a genome's sampling location. AlphaEarth lets analyses convert a latitude/longitude into a continuous environmental descriptor, but it covers only about 28% of genomes and is biased toward samples that carry valid coordinates.

The throughline of the page is a tension. On one hand, multiple independent analyses find that environment leaves a detectable imprint on microbial gene content and that it sometimes outweighs phylogeny. On the other hand, the genomes and samples available for study are not a representative sample of the planet — they over-represent clinical pathogens, lab-convenient organisms, and well-funded geographies, so apparent "biogeographic" patterns can be artifacts of who decided to sequence what, and where.

## What the Corpus Shows

**Environment can outweigh phylogeny — sometimes.** The clearest positive signal comes from prophage ecology, where environment explains substantially more variance in prophage module composition than host phylogeny (PERMANOVA F=30.0 for environment versus F=6.2 for phylogeny). Critically, that environmental signal persists within each genome-size quartile, so it is not merely a side-effect of larger genomes carrying more of everything. PHB (polyhydroxybutyrate, a carbon/energy storage polymer) presence shows a similar pattern: it follows a greater-than-tenfold gradient from temporally variable environments (plant 44%, soil 44%) down to stable host-associated niches (clinical 7%, animal 3%), and that enrichment holds within every genome-size quartile. These are cases where the environment-over-phylogeny claim survives the obvious confounders.

**Function tracks habitat in interpretable ways.** Several analyses find specific functions enriched where ecology predicts. Soil and rhizosphere environments strongly select for the plant-growth-promoting genes *acdS* (7x enriched) and *pqqC*, while the methanol-oxidation gene *xoxF* is strongly enriched in soil/sediment and dramatically depleted in host-associated niches — consistent with methylotrophy being a soil process absent from the gut. Type III secretion systems are roughly twice as prevalent in rhizosphere as in bulk soil, marking them as plant-association markers, and T4SS conjugative machinery is enriched in marine sediment and rhizosphere (most strikingly barley rhizosphere). At the community level, carbon-utilization pathway completeness — not amino-acid pathways — loads almost entirely on the primary axis separating ecosystem metabolic types, with soil and freshwater communities occupying nearly non-overlapping regions of pathway space.

**Niche breadth correlates with genomic capacity.** A cluster of results ties ecological generalism to richer gene content. Metal-type diversity (the number of distinct metals a genus can resist) is the only metal-AMR predictor of ecological niche breadth that survives both phylogenetic (PGLS) and Bonferroni correction, and it remains significant after controlling for species richness and genome size — independently validated in 1,624 BERDL groundwater samples. AlphaEarth environmental-diversity embeddings predict AMR count (Spearman rho=0.47) and metabolic pathway completeness (the strongest single predictor, r=0.39) better than raw geographic spread does, suggesting that ecological breadth, not distance per se, is what enables accumulation of accessory functions. Niche breadth itself is strongly phylogenetically conserved (Pagel's lambda ~0.79), which is part of why disentangling it from ancestry is hard.

**Embeddings encode real spatial signal — but unevenly.** AlphaEarth cosine distance increases monotonically with geographic distance across 50,000 genome pairs, confirming the embeddings capture genuine spatially autocorrelated environmental structure rather than noise. But the signal is 3.4x stronger for environmental samples than for human-associated ones (only 2.0x), because hospitals worldwide share similar urban satellite imagery while natural landscapes differentiate sharply. This is the heart of why environment-to-gene-content links are weak in clinically dominated datasets.

**Community structure can map physical environment.** At the field scale, the ENIGMA subsurface work shows 16S Bray-Curtis community similarity tracing a contamination plume flowing through groundwater — wells U3, M6, and L7 form a community-similarity corridor aligned with the expected plume flow path — and groundwater communities sampled nine days apart are remarkably stable (well identity explains 50% of variance, sampling date only 0.8%). A global pH-driven niche partition across 464K 16S samples explains local co-occurrence patterns at Oak Ridge, with an acid-tolerant cluster occupying environments ~1.4 pH units more acidic than its neutral-preferring counterpart.

**Lab fitness predicts field distribution — partially.** Linking Fitness Browser lab phenotypes to field data, dark-gene clusters show lab-to-field concordance for 62% of testable cases, and metal-contaminated isolates carry predicted metal-tolerance scores a full standard deviation above baseline (Cohen's d=+1.0), dose-dependent across contamination intensity. But lab metal tolerance does *not* simply predict field abundance: at Oak Ridge, ENIGMA model organisms *Desulfovibrio* and *Pseudomonas* show no correlation between abundance and uranium, while *Caulobacter* and *Sphingomonas* emerge as sensitive uranium indicators — field niches are multidimensional in ways the lab cannot capture.

**Mapping reveals discovery gaps.** Global maps surface where the genomic record is thin. Eleven metal-resistance hotspots emerge on a 5-degree grid (the Atacama/Andean region strongest), but only 2.8% of coordinate-bearing environmental MAGs carry any metal resistance — it is globally rare. A Genomic Discovery Index (richness divided by mean genome completeness) flags forest and cropland soils as the highest genomic frontiers, with a +0.8 pH-unit discovery bias toward acidic soils leaving alkaline specialists as dark matter.

## Projects and Evidence

The evidence spans more than forty projects drawing on several data collections. Pangenome-scale environmental analyses lean on [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) and [Kbase Genomes](../data/kbase-genomes.md), with environmental context supplied by AlphaEarth embeddings; lab-fitness links draw on the [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md); field community work uses [Enigma Coral](../data/enigma-coral.md) and [Nmdc Arkin](../data/nmdc-arkin.md) metagenomes.

The **embedding and ecotype** projects (`env_embedding_explorer`, `ecotype_env_reanalysis`, `amr_pangenome_atlas`) establish what AlphaEarth can and cannot do. They quantify the 28.4% coverage, the 38% clinical bias in the embedded subset, and the monotonic distance-decay that validates the signal — then show that, contrary to the initial hypothesis, environmental species did *not* show stronger environment-gene-content correlations than human-associated species (Mann-Whitney p=0.83), a robust null that the clinical bias does not fully explain.

The **metal biogeography** cluster (`metal_resistance_global_biogeography`, `microbeatlas_metal_ecology`, `soil_metal_functional_genomics`, `bacdive_metal_validation`) connects metal resistance to geography, niche breadth, and soil chemistry. A community-weighted analysis of 51,748 soil samples found 2,355 significant COG-metal associations across nine metals, with a db-RDA attributing 80% of variance in COG profiles to metals after conditioning on batch — though that figure is conditional on project accession and warrants an unconditional comparison.

The **community metabolic ecology** projects (`nmdc_community_metabolic_ecology`, `prophage_ecology`, `phb_granule_ecology`, `lanthanide_methylotrophy_atlas`, `pgp_pangenome_ecology`, `plant_microbiome_ecotypes`) apply GapMind pathway-completeness scores and pangenome enrichment to NMDC metagenomes and pangenomes, repeatedly finding environment-specific functional signatures and cross-validating pangenome enrichments against independent metagenomic abundance.

The **lab-versus-field** projects (`lab_field_ecology`, `field_vs_lab_fitness`, `core_gene_tradeoffs`, `conservation_fitness_synthesis`, `functional_dark_matter`) probe how well laboratory phenotypes transfer to natural settings. The "core burden paradox" finding — core genes are *more* likely than accessory genes to show positive fitness when deleted in the lab — is reinterpreted as evidence that lab media are an impoverished proxy: costly-but-conserved genes (motility, ribosomal, RNA metabolism) are maintained by purifying selection because they are essential in environments lab experiments never reproduce.

The **subsurface and field** projects (`enigma_sso_asv_ecology`, `clay_confined_subsurface`, `genotype_to_phenotype_enigma`, `soil_frontier_genomics`, `harvard_forest_warming`) ground the topic in specific field sites, from Oak Ridge groundwater plumes to Mont Terri clay porewater to a 25-year Harvard Forest warming experiment that reproduced the published Actinobacteria-up/Acidobacteria-down compositional shift.

## Connections

This topic is the environmental backbone that several other pages lean on, and the adjacencies are mostly "same finding, different lens":

- [Microbial Ecotypes](microbial-ecotypes.md) is the most tightly coupled page — the ecotype reanalysis here *is* the test of whether environmental embedding similarity predicts gene content, and its null result is central to both pages.
- [Gene Fitness](gene-fitness.md) supplies the lab phenotypes that the lab-versus-field projects try to project onto natural niches; the Fitness Browser biases (Pseudomonas-heavy, lab-convenient conditions) are a shared caveat.
- [Metal Resistance](metal-resistance.md) and [Amr Resistome](amr-resistome.md) share the metal-biogeography and AMR-by-environment evidence: clinical species carry 2.7x more (and less core) AMR, a pattern entangled with sampling bias.
- [Metabolic Pathways](metabolic-pathways.md) connects via GapMind pathway-completeness scoring, the engine behind the ecosystem-metabolic-separation and niche-breadth-predicts-completeness results.
- [Pangenome Architecture](pangenome-architecture.md) links through the openness-versus-niche-breadth hypothesis — open pangenomes are proposed to reflect generalist species with wider environmental range.
- [Subsurface Genomics](subsurface-genomics.md) shares the Oak Ridge, ENIGMA, and Mont Terri field sites where community structure maps physical environment.
- [Mobile Genetic Elements](mobile-genetic-elements.md) connects via prophage and T4SS/HGT biogeography, where environment shapes mobile-element content.
- [Functional Dark Matter](functional-dark-matter.md) and [Microbiome Engineering](microbiome-engineering.md) draw on the discovery-frontier maps and the synthetic-community design opportunities surfaced here.

## Caveats and Open Directions

Honesty about sampling bias is the defining feature of this topic, and the caveats are load-bearing rather than decorative.

**The genome record is not a random sample of the planet.** Clinical pathogens are massively over-represented in NCBI because they were sequenced *precisely because* they cause disease, so the "clinical species carry more AMR" finding is partly circular. *P. aeruginosa* alone is 53% of all *Pseudomonas* genomes; the Fitness Browser is 77% Pseudomonadota with Actinobacteria absent. The AlphaEarth embedded subset carries a 38% human/clinical bias, so even continuous environmental analyses may not represent the broader population. These are not minor adjustments — they can invert expected signals (e.g. *nifH* is depleted, not enriched, in soil-classified species because database nitrogen-fixers are mostly aquatic or host-associated).

**Abiotic measurements are frequently missing entirely.** A striking number of analyses had to infer environment from community composition or treatment labels because actual geochemistry was unavailable: the ENIGMA SSO plume model rests on composition alone because geochemistry was never loaded into BERDL; the NMDC 174-sample matrix had no pH, temperature, or organic-carbon data; the Harvard Forest abiotic table was all zeros, leaving only the +5C treatment label. Without abiotic covariates, partial-correlation tests that would control for environmental gradients simply cannot be run.

**Resolution and proxy limitations blunt many signals.** 16S amplicons resolve only to genus, so field taxa cannot be matched to specific lab strains. "Niche breadth" is often a sequencing-effort proxy from OTU detection rather than confirmed ecological range, and genus-level aggregation can make a genus look broad-niched when really different species occupy different habitats. Several apparent associations dissolve under scrutiny: the PHB-niche-breadth link largely disappears after controlling for genome size (partial rho=-0.05), and observational, cross-sectional designs cannot establish causal direction (metal diversity enabling generalism, or generalism enabling metal-gene acquisition, fit the data equally).

**Provisional results awaiting validation.** Metal-resistance hotspots should be treated as provisional until sampling-effort normalization is complete, since many "hotspots" track sequencing effort in Europe, the USA, and East Asia. The negative out-of-sample R-squared in the soil clay-shield work (models predict worse than the training mean) supports a null only if genuine unpredictability can be separated from distributional shift and outliers — a diagnosis that remains incomplete.

The open directions follow directly from these gaps. The most-repeated is to actually load the missing abiotic data — SSO geochemistry into CORAL, freshwater metabolomics into the Black Queen test — so inference can replace inference-from-composition. Others propose moving from 16S to metagenomics to recover strain-level matching, decoding what each of AlphaEarth's 64 dimensions encodes, re-running the ecotype analysis on environmental-only samples where the embeddings carry more signal, and applying spatial-autocorrelation corrections (Moran's I) before trusting soil model contrasts. Together these would convert a topic currently rich in suggestive, confounded patterns into one grounded in measured environmental gradients.

## Sources

- [stmt:geo-signal-monotonic; env_embedding_explorer]
- [stmt:env-vs-human-geo-signal; env_embedding_explorer]
- [stmt:clinical-sampling-bias; env_embedding_explorer]
- [stmt:embeddings-capture-environment; env_embedding_explorer]
- [stmt:ecotype-env-null-finding; ecotype_env_reanalysis]
- [stmt:ecotype-opposite-direction-claim; ecotype_env_reanalysis]
- [stmt:environment-over-phylogeny; prophage_ecology]
- [stmt:genome-size-dominant-env-robust; prophage_ecology]
- [stmt:phb-enriched-variable-environments; phb_granule_ecology]
- [stmt:environment-enrichment-robust-to-size; phb_granule_ecology]
- [stmt:niche-breadth-confounded-genome-size; phb_granule_ecology]
- [stmt:metal-type-diversity-predicts-niche-breadth; microbeatlas_metal_ecology]
- [stmt:caveat-direction-not-established; microbeatlas_metal_ecology]
- [stmt:alphaearth-diversity-predicts-amr; amr_pangenome_atlas]
- [stmt:clinical-species-more-amr; amr_pangenome_atlas]
- [stmt:niche-breadth-pathway-strongest; pangenome_pathway_geography]
- [stmt:ecology-beats-geography; pangenome_pathway_geography]
- [stmt:carbon-utilization-primary-axis; nmdc_community_metabolic_ecology]
- [stmt:ecosystem-metabolic-separation; nmdc_community_metabolic_ecology]
- [stmt:caveat-abiotic-features-missing; nmdc_community_metabolic_ecology]
- [stmt:soil-enriches-acds-pqqc; pgp_pangenome_ecology]
- [stmt:host-associated-xoxf-depleted; lanthanide_methylotrophy_atlas]
- [stmt:t4ss-prevalence-environmental-mags; t4ss_cazy_environmental_hgt]
- [stmt:column3-corridor; enigma_sso_asv_ecology]
- [stmt:no-direct-geochemistry-caveat; enigma_sso_asv_ecology]
- [stmt:genus-abundance-correlates-uranium-bidirectional; lab_field_ecology]
- [stmt:lab-fitness-does-not-simply-predict-field; lab_field_ecology]
- [stmt:core-burden-paradox-claim; core_gene_tradeoffs]
- [stmt:lab-condition-bias-caveat; core_gene_tradeoffs]
- [stmt:eleven-hotspots-atacama; metal_resistance_global_biogeography]
- [stmt:hotspots-provisional; metal_resistance_global_biogeography]
- [stmt:cog-metal-associations; soil_metal_functional_genomics]
- [stmt:metal-contaminated-isolates-higher-scores; bacdive_metal_validation]
- [stmt:clay-shield-null-result; soil_frontier_genomics]
- [stmt:forest-cropland-frontiers; soil_frontier_genomics]
- [stmt:global-ph-niche-partition; genotype_to_phenotype_enigma]
- [stmt:community-actino-up-acido-down; harvard_forest_warming]
- [stmt:caveat-no-in-lakehouse-abiotic; harvard_forest_warming]
- [stmt:ncbi-sampling-bias; amr_environmental_resistome]
- [stmt:proteobacteria-bias-caveat; functional_dark_matter]
- [stmt:caveat-sampling-bias; pseudomonas_carbon_ecology]
- [stmt:nifh-depleted-in-soil; pgp_pangenome_ecology]
- [stmt:caveat-niche-breadth-sequencing-proxy; microbeatlas_metal_ecology]
- [stmt:lab-impoverished-proxy; conservation_fitness_synthesis]
- [stmt:lab-field-concordance-nmdc; functional_dark_matter]
- [stmt:t3ss-rhizosphere-enrichment; plant_microbiome_ecotypes]

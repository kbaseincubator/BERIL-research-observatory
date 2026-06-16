# NMDC + Arkin Field Multi-Omics Collection

## Overview

The `nmdc_arkin` collection is the shared field-data substrate that lets the
projects in this compendium check whether patterns inferred from reference
genomes and laboratory experiments actually hold in the real environments where
microbes live. It bundles two complementary resources hosted in the BERDL data
lakehouse. The first is the environmental multi-omics holdings of the National
Microbiome Data Collaborative (NMDC): metagenomes, metatranscriptomes,
metabolomics, and the associated sample metadata (soil horizon, biome,
treatment, and a smaller set of measured abiotic variables) drawn from soil,
freshwater, and other habitats across many studies. The second is the Arkin
lab's reference-side resources in the same lakehouse — the GTDB-based pangenome
across ~27,700 species, the GapMind pathway-completeness records, and the
RB-TnSeq Fitness Browser (genome-wide transposon-mutant fitness assays in 48
cultured bacteria). The collection exists as a single wiki page because eight
otherwise unrelated projects all reach for the same NMDC tables to do the same
methodological job: take a hypothesis built from genomes or lab phenotypes and
ask whether the predicted signal reappears in independently collected field
samples.

The unifying move across all eight projects is cross-validation by triangulation.
A pangenome or fitness analysis produces a prediction about who should carry a
gene, where a pathway should be incomplete, or which environmental gradient a
trait should track; the NMDC metagenomic and metabolomic tables are then queried
to see whether community-level abundance or measured chemistry agrees. Because
shotgun metagenomes rarely resolve individual genomes, most projects bridge from
NMDC reads to the pangenome through GTDB taxonomy — mapping community abundance
onto pangenome species so that a genome-derived trait can be scored per sample.
One project reports that this NMDC-to-GTDB taxonomy bridge reached a mean
coverage of 94.6% across 220 samples, with 92% of samples mapping at least 85% of
community abundance to pangenome species, which is what makes the inference
tractable at all.

That bridging strategy is also the collection's central caveat, and the projects
are unusually candid about it. Validation against NMDC is typically **indirect**:
prophage burden, for example, is inferred from taxonomy under the assumption that
prophage content is conserved at the genus level — an assumption that breaks down
for recently acquired or lost prophages. The same indirectness applies wherever a
genome-derived trait is projected onto metagenomic abundance rather than detected
in the reads themselves. A recurring structural gap compounds this: the abiotic
metadata that would let analysts control for confounding gradients is often
missing. The `abiotic_features` table is all zeros for the Harvard Forest warming
samples, leaving the +5C treatment label as the only environmental contrast with
no in-lakehouse soil temperature, pH, or nitrogen; pH, temperature, and total
organic carbon were entirely absent for a 174-sample analysis matrix, preventing
partial-correlation tests; and where abiotic correlations do exist they tend to be
modest (|rho| < 0.12), plausibly because the measurements are point-in-time
snapshots rather than measures of the temporal variability the traits actually
respond to. Coverage is also uneven across habitats — all 33 freshwater samples
in one study lacked paired metabolomics, effectively reducing a Black Queen test
to a soil-only test — and metatranscriptome KO counts reflect transcript-pool
composition from contig annotations rather than TPM-quantified expression. The
honest reading is that NMDC here is a powerful concordance check, not a substitute
for direct measurement: it tells you a lab- or genome-derived signal survives
contact with field data, but the effect sizes are often small and the inference
chain has several joints.

## Projects Using This Collection

The eight projects fall into a few groups by how they lean on the collection.

The clearest "genome-prediction meets field-validation" cases are the
environmental-niche and pangenome-trait studies. The **AMR environmental
resistome** project establishes that ecological niche strongly predicts resistome
size — clinical and human-gut species carry roughly 2.5x more AMR gene clusters
than soil and aquatic species, and the intrinsic-versus-acquired composition
shifts along an ecological gradient (43% accessory in soil up to 80% in human
gut), with metal resistance the most environment-discriminating mechanism
(~44–45% of AMR in soil/aquatic species versus 6% in human gut). It uses
continuous AlphaEarth environmental embeddings to confirm the discrete-environment
findings via a Mantel test, and is forthright that the clinical-AMR signal is
partly confounded by NCBI sampling bias (clinical isolates are massively
overrepresented) and that environment explains only 2–13% of AMR-composition
variance. The **PHB granule ecology** project gives the first precise
pan-bacterial prevalence estimate (21.9% of 27,690 GTDB species carry the PHA
synthase phaC) and a >10-fold environmental gradient from variable environments
(soil/plant) to stable host-associated niches; NMDC metagenomic cross-validation
then confirms that PHB-high genera are significantly more abundant than PHB-low
genera (Mann–Whitney p = 8.4e-22), with the apparent niche-breadth association
collapsing once genome size is controlled (partial rho = -0.047). The **prophage
ecology** project finds that all ~27,700 pangenome species carry prophage modules,
that environment explains more module-composition variance than host phylogeny
(PERMANOVA F = 30.04 vs 6.17), and validates this against 6,365 NMDC metagenomes,
where 57 module-abiotic correlations recover concordant head, tail, and
anti-defense signals — while flagging that prophages were called from eggNOG
annotations rather than dedicated tools, likely inflating prevalence.

A second group uses NMDC to ground lab and atlas-scale inferences. The
**functional dark matter** project catalogs the actionable bacterial dark matter
in the Fitness Browser (57,011 unannotated genes across 48 organisms, 17,344 with
measurable phenotypes) and prioritizes candidates for experiments; its lab-to-
field claim rests on NMDC, where lab fitness phenotypes predicted field
distribution for 61.7% of testable dark-gene clusters and all four pre-registered
abiotic predictions (nitrogen, pH, oxygen) were confirmed in NMDC metagenomic
correlations. It is candid that re-annotation with Bakta reclassifies 83.7% of
"dark" genes as not truly hypothetical, and that the 48 Fitness Browser organisms
are 77% Pseudomonadota, biasing discovery. The **gene function ecological agora**
project builds a bacterial-domain HGT/innovation atlas (13.7M producer-
participation scores across 18,989 GTDB species) and grounds its pre-registered
clades in NMDC-style biome metadata, showing Mycobacteriaceae enriched in
host-pathogen niches (7.88x) and Cyanobacteria in photic-aquatic biomes (2.77x),
while warning that several verdicts are strongly rank-dependent and that the
classic Alm 2006 histidine-kinase correlation does not reproduce at GTDB scale.

A third group leans most heavily on the NMDC multi-omics layer itself, treating
the field data as the primary measurement rather than a check. The **NMDC
community metabolic ecology** project is the most direct consumer: it integrates
305M GapMind records with NMDC multi-omics for 220 samples to test the Black Queen
Hypothesis at the community level, finding that 11 of 13 amino-acid biosynthesis
pathways show the predicted negative correlation between community pathway
completeness and ambient metabolite intensity (leucine and arginine reaching FDR
significance), and that carbon utilization, not amino-acid pathways, is the
primary axis separating ecosystem metabolic types. It carries the
genomic-potential caveat explicitly — GapMind completeness reports gene presence,
not expression. The **Harvard Forest warming** project uses NMDC metagenomes and
metatranscriptomes from a 25-year +5C soil-warming experiment to show a real but
modest community shift (Actinobacteria up, Acidobacteria down), carbon-cycling and
methanotrophy responses, and comparable DNA- and RNA-pool treatment effects once a
horizon-by-incubation confound is removed; its caveats are among the page's
sharpest, since all samples come from a single timepoint with small cohorts (n=28
metagenome, n=39 metatranscriptome) and the lakehouse abiotic table is empty for
these samples. Finally, the **plant microbiome ecotypes** project identifies
plant-association marker genes and a beneficial-core/pathogenic-accessory split,
cross-validating type III secretion as a rhizosphere marker against MGnify
metagenomes (roughly 2x enrichment in rhizosphere over bulk soil); it is the
project most marked by corrected effect sizes, including a Cohen's d that fell from
-7.54 to about -0.4 after a formula error was fixed and a headline compartment
effect (PERMANOVA R2 = 0.527) that proved to be largely a taxonomic-sampling
artifact (residual R2 = 0.072).

Across these projects the opportunities also converge on the same data: several
note that adding NMDC quantitative layers (natural organic matter chemistry,
metabolomics, proteomics) or pairing metatranscriptomics with metabolomics would
turn indirect genomic-potential inferences into direct expression tests, and that
extending coverage to under-sampled habitats such as freshwater would let the
field validations generalize beyond soil.

## Connections

The projects sharing this collection are linked through the topics they
investigate, and the NMDC field data is what gives each topic an environmental
dimension. Several projects test how ecological niche shapes gene content, which
connects to [Microbial Ecotypes](../topics/microbial-ecotypes.md) (the AMR,
plant-microbiome, and PHB projects all frame their findings as niche-driven trait
distributions) and to [Environment Biogeography](../topics/environment-biogeography.md),
the topic that captures the recurring "environment over phylogeny" signal validated
against NMDC metagenomes. The resistome and metal-mechanism findings tie this page
to [AMR Resistome](../topics/amr-resistome.md) and
[Metal Resistance](../topics/metal-resistance.md), where the soil-versus-clinical
contrast in intrinsic versus acquired resistance is developed in full.

The pangenome-trait projects connect to [Pangenome Architecture](../topics/pangenome-architecture.md)
through the shared GTDB pangenome that underlies PHB prevalence, prophage module
universality, and dark-gene linkage, and the core-versus-accessory gradients
those analyses report. Horizontal acquisition is a throughline — phaC, AMR
clusters, prophage modules, and plant-interaction cassettes are all examined for
mobility — which links to [Mobile Genetic Elements](../topics/mobile-genetic-elements.md).
The functional dark matter and gene-function projects, both anchored in the
Fitness Browser, connect to [Gene Fitness](../topics/gene-fitness.md) (lab
fitness phenotypes are the predictions that NMDC field distributions test) and to
[Functional Dark Matter](../topics/functional-dark-matter.md). The metabolic-
completeness and warming work connects to [Metabolic Pathways](../topics/metabolic-pathways.md)
via GapMind community completeness, and the plant project's synthetic-community and
biocontrol-design opportunities reach toward
[Microbiome Engineering](../topics/microbiome-engineering.md). The soil-focused
projects also touch [Subsurface Genomics](../topics/subsurface-genomics.md), where
environmental gradients in soil and sediment communities are the shared concern.

## Sources

- [stmt:taxonomy-bridge-coverage; nmdc_community_metabolic_ecology]
- [stmt:caveat-nmdc-indirect-inference; prophage_ecology]
- [stmt:caveat-no-in-lakehouse-abiotic; harvard_forest_warming]
- [stmt:caveat-abiotic-features-missing; nmdc_community_metabolic_ecology]
- [stmt:nmdc-abiotic-modest-effects; phb_granule_ecology]
- [stmt:caveat-freshwater-absent; nmdc_community_metabolic_ecology]
- [stmt:caveat-transcript-pool-composition; harvard_forest_warming]
- [stmt:clinical-amr-richness; amr_environmental_resistome]
- [stmt:core-accessory-gradient; amr_environmental_resistome]
- [stmt:metal-resistance-soil-aquatic; amr_environmental_resistome]
- [stmt:alphaearth-confirms-discrete; amr_environmental_resistome]
- [stmt:ncbi-sampling-bias; amr_environmental_resistome]
- [stmt:correlation-modest-effects; amr_environmental_resistome]
- [stmt:phac-prevalence-21-percent; phb_granule_ecology]
- [stmt:phb-enriched-variable-environments; phb_granule_ecology]
- [stmt:nmdc-cross-validation; phb_granule_ecology]
- [stmt:niche-breadth-confounded-genome-size; phb_granule_ecology]
- [stmt:prophage-modules-universal; prophage_ecology]
- [stmt:environment-over-phylogeny; prophage_ecology]
- [stmt:nmdc-validates-module-signal; prophage_ecology]
- [stmt:caveat-annotation-based-detection; prophage_ecology]
- [stmt:dark-gene-census-actionable; functional_dark_matter]
- [stmt:lab-field-concordance-nmdc; functional_dark_matter]
- [stmt:bakta-reannotation-overestimate; functional_dark_matter]
- [stmt:proteobacteria-bias-caveat; functional_dark_matter]
- [stmt:hgt-innovation-atlas; gene_function_ecological_agora]
- [stmt:biome-enrichment-grounding; gene_function_ecological_agora]
- [stmt:alm-2006-not-reproduced; gene_function_ecological_agora]
- [stmt:first-gapmind-metabolomics-integration; nmdc_community_metabolic_ecology]
- [stmt:black-queen-community-signal; nmdc_community_metabolic_ecology]
- [stmt:leucine-arginine-fdr-significant; nmdc_community_metabolic_ecology]
- [stmt:carbon-utilization-primary-axis; nmdc_community_metabolic_ecology]
- [stmt:caveat-genomic-potential-not-expression; nmdc_community_metabolic_ecology]
- [stmt:community-actino-up-acido-down; harvard_forest_warming]
- [stmt:h1-dna-rna-comparable; harvard_forest_warming]
- [stmt:caveat-single-timepoint-sample-size; harvard_forest_warming]
- [stmt:opportunity-add-arkin-quant-layers; harvard_forest_warming]
- [stmt:beneficial-core-pathogenic-accessory; plant_microbiome_ecotypes]
- [stmt:t3ss-rhizosphere-enrichment; plant_microbiome_ecotypes]
- [stmt:cohen-d-formula-error; plant_microbiome_ecotypes]
- [stmt:permanova-sampling-artifact; plant_microbiome_ecotypes]
- [stmt:syncom-biocontrol-design; plant_microbiome_ecotypes]
- [stmt:opportunity-transcript-validation; nmdc_community_metabolic_ecology]

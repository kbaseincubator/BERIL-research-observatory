# Claude

Claude is an AI contributor in this compendium, credited as the author of the
analyses behind the **prophage_amr_comobilization** project. This page exists to
give a single-glance view of what that contributor worked on: the questions it
posed, the evidence it produced, and the topics it touched. All of the work
attributed here sits at the intersection of bacterial pangenomes, mobile genetic
elements, and antimicrobial resistance, and it leans heavily on honest
accounting of what the data can and cannot show.

## Overview

The contributor's footprint is narrow but deep: one project that asks whether
prophages -- bacteriophage genomes integrated into a bacterial chromosome -- are
associated with the spread of antimicrobial resistance (AMR) genes, examined not
in a handful of strains but across an entire pangenome census. A pangenome is
the union of all genes seen across many genomes of related organisms, split into
a near-universal *core* and a variable *accessory* fraction.

Across this project the work produces a consistent picture. At the broadest
scale, a census of 27,702 species recovered 83,008 AMR gene clusters and millions
of prophage marker clusters, with 14,669 species carrying both, establishing that
the two features genuinely co-occur in the same genomes. Both prophage markers
and AMR genes turn out to live mostly in the accessory genome rather than the
core, with prophage markers the more strongly accessory of the two and often
present as singletons -- exactly the distribution expected for recently acquired,
mobile DNA. Quantitatively, species with denser prophage content carry broader
AMR repertoires, and prophage density alone explains roughly 30% of the
variance in AMR breadth. That breadth signal survives a control for genome count
and holds across all five major phyla examined, which argues against a purely
phylogenetic artifact.

The contributor is careful to bound these claims. The species-level association
does not prove that phages move resistance genes, because species with open
pangenomes -- those whose gene inventory keeps growing as more genomes are
sequenced, indicating frequent horizontal acquisition -- may independently
accumulate both prophages and AMR genes. Prophages here were also detected by
keyword and Pfam matching rather than dedicated prediction software, so the
marker set may include false positives such as phage-defense systems and miss
divergent prophages. And the most direct mechanistic test -- whether
prophage-proximal resistance genes carry distinct fitness costs -- could not be
run at all, because the RB-TnSeq fitness data available cover only a few dozen
model organisms that barely overlap the species analyzed.

## Projects

### prophage_amr_comobilization

This is the contributor's sole project, and it is framed as the first
pangenome-scale analysis of prophage-AMR gene-neighborhood co-localization,
spanning 100 species, 1,953 genomes, and 36,041 AMR gene instances in its focused
neighborhood analysis (atop the much larger census). The data come from the
[Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) collection, which supplies the
genomes and gene-cluster structure the analysis is built on.

The findings build from co-occurrence toward physical linkage. Beyond the
density-versus-breadth relationship, a contig-level analysis shows that in the
most AMR-burdened species, over half of AMR gene instances sit on contigs that
also carry *strict* prophage markers such as terminase (the enzyme that packages
phage DNA into capsids) and phage structural proteins -- placing resistance genes
and phage machinery on the same stretch of DNA. The fine-grained proximity story
is more tempered: prophage-proximal AMR genes are only slightly more likely to be
accessory than distal ones, a statistically significant but modest effect, and
that effect is threshold-dependent and heterogeneous -- absent or even reversed at
very close range and strengthening only at broader gene-distance thresholds. The
contributor reads the density signal as consistent with two distinct mechanisms
it cannot disentangle: prophages directly mobilizing resistance genes via
transduction (phage-mediated DNA transfer between bacteria), or high-recombination
species independently picking up both. In relation to prior literature, the
breadth result is presented as extending earlier capsule-pangenome work, showing
the prophage-AMR correlation at far larger scale and demonstrating that it
persists after controlling for genome count rather than capsule presence -- though
this comparison is held at medium confidence.

The project closes with two concrete next steps rather than overclaiming.
Replacing keyword-based detection with dedicated prophage prediction tools such
as geNomad or PHASTER, and ingesting those results, would sharpen the marker set
and cut false positives. Separately, as fitness-browser coverage from
[Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md) expands to more
species, the unanswered fitness-cost question can be revisited to test whether
prophage-proximal AMR genes behave differently from the rest.

## Topics

The work threads through five topics that together define the contributor's
intellectual footprint.

[Amr Resistome](../topics/amr-resistome.md) and
[Mobile Genetic Elements](../topics/mobile-genetic-elements.md) are the central
pair: nearly every finding pits the AMR gene inventory of a species against its
prophage content, treating prophages as the candidate vehicle and AMR genes as
the cargo. [Pangenome Architecture](../topics/pangenome-architecture.md) supplies
the analytical frame -- the core/accessory split is what makes the accessory-bias
and open-pangenome arguments legible, and it is also the basis for the caution
that open pangenomes could explain the co-occurrence without any phage
involvement. [Functional Dark Matter](../topics/functional-dark-matter.md) enters
through the detection caveat: keyword/Pfam matching of poorly characterized
phage and defense genes is exactly where uncharacterized sequence space muddies
the signal, motivating the move to dedicated predictors. Finally,
[Gene Fitness](../topics/gene-fitness.md) marks the project's honest gap -- the
fitness-cost hypothesis remains untested for lack of overlapping RB-TnSeq data,
and it is flagged as the most natural question to reopen later.

## Sources

- [stmt:pangenome-amr-prophage-census; prophage_amr_comobilization]
- [stmt:prophage-amr-accessory-bias; prophage_amr_comobilization]
- [stmt:prophage-density-predicts-amr-breadth; prophage_amr_comobilization]
- [stmt:density-effect-robust-to-genome-count; prophage_amr_comobilization]
- [stmt:amr-prophage-contig-sharing; prophage_amr_comobilization]
- [stmt:proximity-weak-mobility-effect; prophage_amr_comobilization]
- [stmt:proximity-threshold-dependence; prophage_amr_comobilization]
- [stmt:novel-pangenome-scale; prophage_amr_comobilization]
- [stmt:density-mechanism-interpretation; prophage_amr_comobilization]
- [stmt:extends-rendueles-correlation; prophage_amr_comobilization]
- [stmt:caveat-correlation-not-causation; prophage_amr_comobilization]
- [stmt:caveat-keyword-prophage-detection; prophage_amr_comobilization]
- [stmt:caveat-fitness-data-gap; prophage_amr_comobilization]
- [stmt:opportunity-dedicated-prophage-prediction; prophage_amr_comobilization]
- [stmt:opportunity-expanded-fitness-revisit-h3; prophage_amr_comobilization]

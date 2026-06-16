# Dileep Kishore

## Overview

Dileep Kishore is a contributor to this compendium whose work sits at the
intersection of comparative genomics and experimental gene fitness. This page
exists to gather, in one place, the scientific footprint of that work: a single
but tightly argued project, [Pathway Capability Dependency](#projects), and the
cluster of topics it touches — [Metabolic Pathways](../topics/metabolic-pathways.md),
[Pangenome Architecture](../topics/pangenome-architecture.md),
[Gene Fitness](../topics/gene-fitness.md),
[Microbial Ecotypes](../topics/microbial-ecotypes.md),
[Functional Dark Matter](../topics/functional-dark-matter.md), and
[Environment Biogeography](../topics/environment-biogeography.md).

The throughline of the work is a deceptively simple question: when a bacterium's
genome *encodes* a complete metabolic pathway, does it actually *depend* on that
pathway to grow? The project answers by joining two very different kinds of
evidence. On one side is genomic completeness — whether the genes of a pathway
are present — read out through [GapMind](../data/kescience-fitnessbrowser.md),
a tool that scores how complete an organism's pathway is from its annotation. On
the other side is experimental necessity, measured by RB-TnSeq (random-barcode
transposon sequencing), a genome-wide knockout assay that quantifies how much
each gene matters for growth in a given condition. Kishore's analysis shows that
these two signals diverge sharply, and that the gap between "can do" and "needs
to do" is itself biologically meaningful — it traces the architecture of
pangenomes and the ecological niches strains occupy.

## Projects

### Pathway Capability Dependency

The central result reframes pathway completeness as a poor proxy for metabolic
dependence. Across 161 organism–pathway pairs in 7 well-studied model bacteria,
only about 35% behave as *Active Dependencies* — genomically complete pathways
that the cell genuinely needs, where knocking out the genes hurts fitness.
A larger share, roughly 41%, are *Latent Capabilities*: the genes are all there
and the pathway looks complete, yet removing them does nothing measurable to
growth. The headline conclusion is that having the genes does not predict needing
them.

To make this call reproducibly, the project does not lean on essentiality alone.
It builds a composite importance score that blends three RB-TnSeq–derived
signals: gene essentiality (weighted 40%), fitness breadth — how many conditions
a gene matters across (30%) — and fitness magnitude, the size of the fitness
effect (30%). That single score lets every organism–pathway pair be classified
on a common scale rather than by an ad hoc rule.

A recurring theme is that "latent" is the wrong mental model if it implies dead
weight. When the analysis stratifies by condition type, all 66 Latent Capability
pairs turn out to become fitness-important under at least one condition — most
often nitrogen limitation, stress, or carbon limitation. Latency, in other words,
is context-dependence, not genomic baggage: the pathway is held in reserve for
environments the lab default does not impose. Consistent with this, Active
Dependencies sit slightly but consistently deeper in the core genome (mean core
completeness 0.986) than Latent Capabilities (0.975), matching the expectation
that the genes a cell truly cannot live without are concentrated in the conserved
core rather than the variable accessory genome. This finding draws on metal-stress
fitness data ([Metal Fitness Atlas](../data/kescience-fitnessbrowser.md)) layered
onto the pangenome.

Scaling up from 7 model organisms to 2,810 species (each with at least 10
sequenced genomes) connects the dependency picture to pangenome architecture.
The number of *variable pathways* a species carries correlates with its pangenome
openness — the degree to which adding more genomes keeps revealing new genes
rather than saturating. After controlling for genome count, that relationship is
a robust partial Spearman rho of 0.530 (p ≈ 2.8e-203). The interpretive payoff,
stated as a more tentative claim, is that pathway variation gives a
*mechanistically interpretable* correlate of openness where broader ecological
and phylogenetic variables had failed to explain it in a prior project. In short,
what a pangenome can metabolize, not just where it lives, may govern how open it
stays.

Drilling into which pathways drive the accessory signal points squarely at amino
acid biosynthesis. Leucine, valine, arginine, lysine, and threonine pathways show
the strongest dependence on accessory (non-core) genes, with core-versus-all
completeness gaps of about 0.14 — meaning roughly 14% of species-level pathway
completeness is supplied by genes that only some strains carry. Because different
strains thus carry different biosynthetic capabilities, this is read as direct
evidence for Black Queen–style distribution of biosynthetic capacity across a
species: capabilities become public goods, and any one strain can offload a
costly pathway as long as a neighbor still makes the metabolite. The accessory
genome, on this view, functions as a form of *metabolic insurance* spread across
the population.

The work also defines metabolic ecotypes from the bottom up. Clustering strains
within a species by their binary pathway-presence profiles (using Jaccard
distance) yields a median of 4 — and up to 8 — distinct metabolic ecotypes per
species, and the ecotype count itself correlates with pangenome openness (partial
rho 0.322, p ≈ 8.0e-07) after controlling for genome count. Metabolic
heterogeneity within a species, then, is structured and quantifiable, not noise.

The project is candid about its limits, and several caveats deserve to be read
alongside the findings:

- **Phylogeny is only partially controlled.** Correlations adjusted for genome
  count and taxonomic grouping rather than full phylogenetic independent
  contrasts. Since phylogeny dominates gene content in most species, some of the
  metabolic-ecotype structure may reflect intra-species phylogenetic signal
  rather than independent ecological differentiation.
- **The importance threshold is partly circular.** The median-based cutoff splits
  pathways roughly 50/50 by construction, so the tidy claim that *every* Latent
  Capability becomes important under some condition is partly an artifact of how
  the threshold was set; a defensible cutoff would need an independent validation
  set.
- **The model-organism backbone is thin.** The most confident (Tier 1)
  classification rests on just 7 of 48 Fitness Browser organisms that have GapMind
  data — all well-annotated model organisms whose near-complete core genomes
  compress the very conservation signal the validation depends on.

Two stated opportunities mark where the work points next. First, correlating
metabolic ecotypes with AlphaEarth environmental niche breadth was planned but
not executed, constrained by AlphaEarth covering only 28% of genomes; closing
that loop would test whether metabolic ecotypes map onto real environmental
niches. Second, the 14.9% of organism–pathway pairs that GapMind scores as
*incomplete* yet RB-TnSeq finds *fitness-important* are a flag for annotation
gaps or unmodeled salvage routes — a concrete opening to improve pathway
annotation and chip away at functional dark matter.

## Topics

The project's reach across this wiki's topic graph reflects its method of
joining genomic and experimental evidence:

- **[Metabolic Pathways](../topics/metabolic-pathways.md)** is the central
  organizing unit — every classification (Active Dependency, Latent Capability,
  variable pathway) is made at the pathway level, and the capability-versus-
  dependency distinction is fundamentally a statement about pathways.
- **[Gene Fitness](../topics/gene-fitness.md)** supplies the experimental axis:
  the composite importance score, condition-dependent activation of latent
  pathways, and the core-genome enrichment of active dependencies all rest on
  RB-TnSeq fitness measurements.
- **[Pangenome Architecture](../topics/pangenome-architecture.md)** is where the
  results scale up — pangenome openness, accessory-gene contribution to
  completeness, and the core/accessory split of dependencies all live here, and
  it is the topic most heavily cited by this work.
- **[Microbial Ecotypes](../topics/microbial-ecotypes.md)** captures the
  within-species metabolic heterogeneity the clustering analysis defines, and is
  the locus of both a key finding and the phylogeny caveat.
- **[Functional Dark Matter](../topics/functional-dark-matter.md)** is reached
  through the GapMind coverage limits and the incomplete-but-important pairs that
  expose annotation gaps and salvage pathways.
- **[Environment Biogeography](../topics/environment-biogeography.md)** is a
  forward-looking link only: the AlphaEarth niche-breadth correlation remains a
  planned, unexecuted direction rather than a result.

For the underlying data, this work draws on the
[Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md) collection (the
Fitness Browser, RB-TnSeq, GapMind, and metal-fitness data) and the
[Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) collection (species
pangenomes and gene-presence profiles).

## Sources

- [stmt:capability-not-dependency; pathway_capability_dependency]
- [stmt:composite-importance-score; pathway_capability_dependency]
- [stmt:latent-conditionally-active; pathway_capability_dependency]
- [stmt:active-deps-core-genomes; pathway_capability_dependency]
- [stmt:variable-pathways-open-pangenomes; pathway_capability_dependency]
- [stmt:pathway-variation-openness-correlate; pathway_capability_dependency]
- [stmt:amino-acid-accessory-dependence; pathway_capability_dependency]
- [stmt:accessory-as-insurance; pathway_capability_dependency]
- [stmt:metabolic-ecotypes; pathway_capability_dependency]
- [stmt:phylogeny-confound-caveat; pathway_capability_dependency]
- [stmt:threshold-circularity-caveat; pathway_capability_dependency]
- [stmt:fb-gapmind-coverage-caveat; pathway_capability_dependency]
- [stmt:alphaearth-niche-opportunity; pathway_capability_dependency]
- [stmt:incomplete-but-important-opportunity; pathway_capability_dependency]

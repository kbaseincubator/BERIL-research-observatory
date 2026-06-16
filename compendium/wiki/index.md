# State of the Science

This is the home page of a synthesis wiki that knits together seventy independent
computational microbiology projects into a single, navigable map of what is currently
known, contested, and worth pursuing. Each project mined large public resources — the
[Fitness Browser](data/kescience-fitnessbrowser.md) of RB-TnSeq mutant-fitness data
(genome-wide gene fitness measured by sequencing pooled transposon-insertion mutants
across many growth conditions), the [KBase pangenome](data/kbase-ke-pangenome.md) of gene
clusters across thousands of genomes, and many phenotype, metagenome, and biochemistry
databases — and produced its own findings, caveats, and open questions. This wiki exists
to make those scattered results legible together: to show where independent analyses
converge on the same biology, where they disagree, and where the same shared dataset is
being re-used for very different ends. Read it as an atlas. The pages below are the
regions; this page is the index.

## Overview

A handful of cross-cutting themes recur across the projects and organize the rest of the
wiki. The first is a **two-speed genome**: a deeply conserved core of translation, energy
metabolism, and biosynthesis genes that behaves like an ancient "metabolic engine,"
surrounded by an accessory genome that is recent, variable, and overwhelmingly the product
of horizontal gene transfer (HGT, the movement of DNA between lineages rather than from
parent to offspring) rather than vertical inheritance. This functional partitioning holds
across bacterial phyla, which several projects read as evidence of a deep evolutionary
constraint on how bacterial genomes are built.

The second theme is the tension between **laboratory fitness and natural selection**. By
connecting RB-TnSeq fitness for roughly 194,000 genes across ~43 bacteria to pangenome
conservation, projects show that genes important in the lab are only weakly predictive of
genes conserved over evolutionary time. A striking instance is the "burden paradox": core
genes are *more* likely than accessory genes to look costly (to improve growth when
deleted in the lab), the opposite of what genome-streamlining theory predicts. The
resolution offered repeatedly is that lab media are an impoverished proxy for nature — a
gene that is dead weight in rich medium can be essential in soil, a biofilm, or a host,
which is why purifying selection preserves tens of thousands of "costly-but-conserved"
genes. This caveat about lab conditions is the single most common limitation across the
whole corpus, and it should temper every fitness-based claim here.

The third and fourth themes are **resistance** and **ecology as a predictor of genome
content**. Antimicrobial-resistance (AMR) genes are sharply depleted from the core genome
and concentrated in clinical pathogens, and the intrinsic-versus-acquired distinction maps
cleanly onto conservation. Independently, environmental origin — metal contamination,
subsurface clay, the cystic-fibrosis lung — turns out to predict measurable genome
features, with several projects validating lab-derived metal-tolerance scores against the
real isolation ecology of strains in external databases. These convergences, and the
honest disagreements around them, are what the topic pages below develop in detail.

## Topic Map

- [Pangenome Architecture](topics/pangenome-architecture.md) — core vs. accessory genome
  structure, openness, and the two-speed view of bacterial genomes.
- [Gene Fitness](topics/gene-fitness.md) — RB-TnSeq mutant fitness, essentiality, and how
  lab fitness relates to conservation.
- [Metabolic Pathways](topics/metabolic-pathways.md) — biosynthesis and catabolism,
  GapMind pathway calls, and metabolic modeling/gapfilling.
- [Functional Dark Matter](topics/functional-dark-matter.md) — hypothetical and
  uncharacterized genes, and multi-evidence strategies to annotate them.
- [AMR Resistome](topics/amr-resistome.md) — antimicrobial-resistance gene census,
  conservation, fitness cost, and cofitness networks.
- [Metal Resistance](topics/metal-resistance.md) — metal-tolerance genetics and the link
  between lab tolerance and contaminated-site ecology.
- [Microbial Ecotypes](topics/microbial-ecotypes.md) — environment- and host-associated
  differentiation in gene content and fitness.
- [Environment & Biogeography](topics/environment-biogeography.md) — geographic and
  habitat structure of microbial functional potential.
- [Subsurface Genomics](topics/subsurface-genomics.md) — deep-clay and confined-aquifer
  isolates and the cohorts that BERDL does and does not capture.
- [Mobile Genetic Elements](topics/mobile-genetic-elements.md) — prophages, HGT
  signatures, and co-mobilization of resistance.
- [Microbiome Engineering](topics/microbiome-engineering.md) — designing defined
  consortia, including the cystic-fibrosis formulation work.
- [ADP1 Model System](topics/adp1-model-system.md) — *Acinetobacter baylyi* ADP1 as a
  deeply characterized single-organism testbed.

## Author Map

These author pages collect the statements attributed to each contributor and are the most
useful entry points to the human side of the corpus:

- [Dileep Kishore](authors/dileep-kishore.md)
- [Heather MacGregor](authors/heather-macgregor.md)
- [Claude](authors/claude.md)
- [0000-0002-2170-2250](authors/0000-0002-2170-2250.md)
- [0000-0002-6601-2165](authors/0000-0002-6601-2165.md)
- [0000-0003-2728-7622](authors/0000-0003-2728-7622.md)
- [0000-0002-0357-1939](authors/0000-0002-0357-1939.md)
- [0000-0001-9076-6066](authors/0000-0001-9076-6066.md)

## Data Map

Most projects draw on a small set of shared resources, so the same dataset often underlies
findings on very different pages. These data pages document each source and link back to
the projects that used it:

- [KE Pangenome](data/kbase-ke-pangenome.md) — gene clusters across thousands of genomes;
  the backbone of nearly all conservation and pangenome-architecture work.
- [Fitness Browser](data/kescience-fitnessbrowser.md) — RB-TnSeq mutant-fitness data
  across dozens of bacteria; the basis of the fitness and essentiality analyses.
- [KBase Genomes](data/kbase-genomes.md) — reference genomes underlying annotation and
  comparative work.
- [KBase Phenotype](data/kbase-phenotype.md) — phenotype records used to ground genomic
  predictions in observed biology.
- [MSD Biochemistry](data/kbase-msd-biochemistry.md) — reaction and compound references
  for metabolic modeling.
- [UniRef](data/kbase-uniref.md) — protein clusters for functional annotation.
- [NMDC / Arkin](data/nmdc-arkin.md) — metagenome and environmental-community data.
- [ENIGMA Coral](data/enigma-coral.md) — Oak Ridge field-site community and geochemistry
  context.
- [PhageFoundry](data/phagefoundry.md) — phage and prophage resources for mobile-element
  work.
- [ProtECT GenomeDepot](data/protect-genomedepot.md) — genome resource used in
  comparative analyses.

## Sources

- [stmt:dual-dataset-synthesis; conservation_fitness_synthesis]
- [stmt:lab-impoverished-proxy; conservation_fitness_synthesis]
- [stmt:core-metabolic-engine; cog_analysis]
- [stmt:hgt-primary-innovation; cog_analysis]
- [stmt:patterns-deep-constraint; cog_analysis]
- [stmt:core-burden-paradox-claim; core_gene_tradeoffs]
- [stmt:purifying-selection-claim; core_gene_tradeoffs]
- [stmt:lab-proxy-interpretation-claim; core_gene_tradeoffs]
- [stmt:weak-prediction-caveat; fitness_effects_conservation]
- [stmt:enrichment-robust-across-contexts; conservation_vs_fitness]
- [stmt:amr-depleted-from-core; amr_pangenome_atlas]
- [stmt:amr-depletion-universal; amr_pangenome_atlas]
- [stmt:intrinsic-acquired-dichotomy; amr_pangenome_atlas]
- [stmt:clinical-species-more-amr; amr_pangenome_atlas]
- [stmt:sampling-bias-caveat; amr_pangenome_atlas]
- [stmt:amr-first-pan-bacterial; amr_fitness_cost]
- [stmt:atlas-prediction-validated; bacdive_metal_validation]
- [stmt:metal-contaminated-isolates-higher-scores; bacdive_metal_validation]
- [stmt:phylum-confounding-partial; bacdive_metal_validation]
- [stmt:universal-essentials-only-broad-spectrum-targets; essential_genome]
- [stmt:five-organism-formulation; cf_formulation_design]
- [stmt:planktonic-only-caveat; cf_formulation_design]
- [stmt:cohort-cultured-only-caveat; clay_confined_subsurface]
- [stmt:gapfilling-dependence; acinetobacter_adp1_explorer]
- [stmt:single-condition-caveat; conservation_vs_fitness]
- [stmt:lab-condition-bias-caveat; core_gene_tradeoffs]

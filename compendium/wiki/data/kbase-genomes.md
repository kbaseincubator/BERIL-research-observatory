# KBase Genomes

## Overview

The KBase Genomes collection is the shared library of bacterial (and viral) genome
sequences and their derived annotations that two otherwise unrelated projects in this
compendium both lean on. It is "data" rather than a research finding: a reference layer
of whole-genome assemblies, taxonomic placements, and gene-level feature tables that lets
a project ask, of any clade or strain, *what genes does it carry and where did they come
from?* The page exists because that same genomic substrate underpins both a
domain-spanning study of how bacteria gain genes and a clinical effort to design phage
therapies against gut pathobionts — so the collection is the natural meeting point
between them.

In practice the collection is reached through several standardized resources. Taxonomy
and genome representatives come from **GTDB** (the Genome Taxonomy Database, which assigns
a uniform, sequence-based hierarchy to bacteria); per-genome gene calls and functional
labels come from **Bakta annotations**; ecology metadata about where a genome's relatives
have actually been sampled comes from **MGnify** and **BacDive**; and specialist feature
sets — biosynthetic gene clusters via **MiBIG**, viral sequences via **IMG/VR** and
**INPHARED** — layer on top. Because these resources use different and shifting taxonomic
names, a reusable taxonomy synonymy layer (an NCBI-taxid plus GTDB-version-aware rename
table) is needed to join them, and the projects note this layer generalizes to any
multi-cohort microbiome work rather than being a one-off.

The collection's main genome-scale product is a bacterial-domain horizontal-gene-transfer
(HGT) and innovation atlas built over **18,989 GTDB r214 species representatives**,
carrying 13.7 million producer/participation scores and 17 million Sankoff-parsimony gene
"gain" events with each gain attributed to a recipient taxonomic rank. (Sankoff parsimony
is a method for inferring, from the pattern of which genomes have a gene, the most
economical history of where it was gained or lost along the tree.) This atlas is what
connects genomic data to questions about [mobile genetic elements](../topics/mobile-genetic-elements.md)
and [pangenome architecture](../topics/pangenome-architecture.md) — the latter being the
idea that a species' total gene repertoire (its pangenome) can be "open" (continually
acquiring new accessory genes) or "closed."

A recurring lesson from working with this collection is that genome-derived signals are
**rank- and method-dependent**, and several headline claims have to be reported with
caveats. The HGT atlas convergence is made robust by triangulating three independent
measurement substrates — Sankoff-parsimony effect sizes, sample-biome ecology metadata,
and per-strain phenotype tables — rather than trusting any one. But the same genomic data
can yield opposite verdicts depending on taxonomic resolution: the photosystem II (PSII)
"Innovator" verdict for cyanobacteria is STABLE at genus, Innovator-Exchange at class, and
Innovator-Isolated at phylum, so the correct rank has to be chosen on biological grounds.
A widely cited result also fails to reproduce here: the Alm-2006 r~0.74 correlation between
histidine-kinase (two-component-system) count and lineage-specific expansion drops to only
r=0.10–0.29 across the full 18,989-genome set. And the projects explicitly warn that recent
between-species gene gain and within-species pangenome openness are *uncorrelated*
(Spearman r=-0.011 across 894 genera), so openness cannot be used to cross-validate the
acquisition signal. These cautions are part of what the collection "is": a rich but
double-edged genomic resource.

## Projects Using This Collection

### Gene Function & Ecological AGORA — the HGT/innovation atlas

The [gene_function_ecological_agora](../authors/0000-0002-4999-2931.md) work uses the
genome collection at the broadest possible scope: the whole bacterial domain. Its central
construct is a **Producer × Participation framework**, a direction-agnostic per-clade
categorization (Innovator-Isolated / Innovator-Exchange / Sink-Broker-Exchange / Stable)
that works at deep taxonomic ranks where full gene-tree/species-tree (DTL) reconciliation
is computationally intractable. With this framework the project confirms two
pre-registered cases drawn from genome annotations: **Cyanobacteria are Innovator-Exchange
on PSII at the Cyanobacteriia class rank** (producer effect d=+1.50, consumer d=+0.70 —
the class rank being appropriate because PSII predates Cyanobacteria diversification), and
**Mycobacteriaceae are Innovator-Isolated on the mycolic-acid pathway** (producer d=+0.31,
consumer d=-0.19, i.e. heavy in-clade paralog expansion but little cross-clade exchange).
That mycolic-acid signature is further localized to host-pathogen mycobacteria rather than
soil mycobacteria, refining the original family-level finding — a connection to
[environment & biogeography](../topics/environment-biogeography.md), since the clades are
significantly enriched in their expected biomes (Mycobacteriaceae in host-pathogen niches
at 7.88x, Cyanobacteriia in photic aquatic at 2.77x, Bacteroidota in gut/rumen at 1.40x,
all with extreme p-values).

The atlas also exposes structural correlates of gene mobility. Architectural promiscuity
tracks HGT propensity — mixed-category gene families (KOs) carry a median of 46 Pfam
domain architectures each versus just 1 for PSII, echoing the "modular systems exchange
more" pattern — and the ratio of recent-to-ancient gain events is itself a function-class
signature, with CRISPR-Cas systems sharply recent-skewed (24.5x, HGT-active) and strict
housekeeping genes ancient-skewed (~1x, vertical inheritance). This ties the data directly
to [gene fitness](../topics/gene-fitness.md) and [functional dark matter](../topics/functional-dark-matter.md).
Importantly, a control finding tempers any mechanistic over-reading: all three
pre-registered KO sets (PSII, mycolic-acid, PUL) show near-zero
[mobile-genetic-element](../topics/mobile-genetic-elements.md) machinery rates against a
1.37% atlas baseline, meaning these gene families are not themselves phage, transposase,
integrase, or plasmid genes. Two open directions remain: flagging phage/plasmid/integron
context per gain event to test whether high-exchange KOs are mobile-element-mediated, and
composition-based donor inference at deep ranks — the latter currently blocked because
per-CDS sequence is not in BERDL queryable schemas, so only an exploratory tree-based
donor layer shipped.

### IBD Phage Targeting — genomes behind cocktail design

The [ibd_phage_targeting](../authors/0000-0002-4999-2931.md) project uses the same genomic
substrate at the strain and pathogen level, to engineer phage therapies for inflammatory
bowel disease (IBD). It relies on metagenomic abundance profiles (MetaPhlAn3 over curated
metagenomic data) joined to genome-level annotations, and the taxonomy synonymy layer
above is exactly what makes the multi-cohort join possible. Two independent clustering
methods on 8,489 metagenomic samples converge on **four reproducible IBD microbiome
ecotypes (E0–E3)**, and a confound-free within-substudy Crohn's-vs-nonIBD meta-analysis
across four cohorts recovers the canonical Crohn's signature (pathobionts up, protective
commensals down). A structural caveat shapes that design: in pooled curatedMetagenomicData
the healthy and Crohn's samples come from disjoint source studies, making a pooled
case-vs-control model unidentifiable and forcing the within-substudy comparison.

Genome content then turns ecology into actionable targets, linking the collection to
[microbial ecotypes](../topics/microbial-ecotypes.md) and
[microbiome engineering](../topics/microbiome-engineering.md). Tier-A pathobiont genomes
are strongly enriched for iron-siderophore biosynthetic gene clusters, marking iron
acquisition as a Crohn's-defining genomic capability rather than only a cohort-level
pathway signal; and among the six actionable Tier-A pathobionts, only *E. coli* (the
adherent-invasive AIEC subset) carries the combined iron-siderophore and colibactin
genotoxin gene-cluster signature, localizing iron-driven Crohn's biology to *E. coli*.
For that species a greedy minimum-set-cover design over experimentally tested phage–strain
susceptibility yields a **5-phage cocktail covering 94.7% of 188 E. coli strains** in
PhageFoundry. On the viral side, the Microviridae member Gokushovirus WZ-2015a is robustly
depleted in Crohn's, strongest in the transitional E1 ecotype.

The project is candid about its limits. Cocktails designed at the cohort level mismatch
individual patients unless each patient's ecotype is determined first, and clinical
covariates alone separate healthy from IBD but cannot tell the transitional (E1) from
severe (E3) ecotype — so metagenomics remains required for assignment. A single patient's
ecotype can even drift between E1 and E3 between visits (Jaccard 0.60), motivating
state-dependent rather than fixed cocktail design. The two highest-priority Crohn's targets,
*H. hathewayi* and *M. gnavus*, have the weakest phage availability, creating a coverage
gap for the most actionable species; no E1 Crohn's patient can be treated with a pure phage
cocktail, only a hybrid pairing phages with non-phage alternatives. The 23 UC Davis Crohn's
patients span three ecotypes (none in the Prevotella E2), and the E3 Tier-A target list
rests on single-study evidence and is explicitly provisional. A clear next step is querying
external phage databases (INPHARED and IMG/VR) for gut-anaerobe phages to close that gap and
convert the hybrid framework into a pure-phage cocktail for some patients.

## Connections

- **[Mobile Genetic Elements](../topics/mobile-genetic-elements.md)** — both projects
  read genome content as a record of gene mobility: the AGORA atlas scores HGT and gene
  gain across the bacterial domain, while phage targeting works directly with viral
  genomes (Gokushovirus, candidate cocktail phages).
- **[Pangenome Architecture](../topics/pangenome-architecture.md)** — the collection's
  per-genome gene repertoires feed accessory-vs-core analyses, though the projects caution
  that pangenome openness does *not* track the recent-acquisition signal.
- **[Microbial Ecotypes](../topics/microbial-ecotypes.md)** and
  **[Microbiome Engineering](../topics/microbiome-engineering.md)** — the IBD project turns
  metagenomic ecotypes (E0–E3) plus genomic capability into patient-matched, state-dependent
  cocktail designs.
- **[Environment & Biogeography](../topics/environment-biogeography.md)** — biome-enrichment
  metadata grounds atlas clades in their expected habitats and refines niche-specific
  findings (e.g. host-pathogen vs soil mycobacteria).
- **[Metabolic Pathways](../topics/metabolic-pathways.md)**,
  **[Gene Fitness](../topics/gene-fitness.md)**, and
  **[Functional Dark Matter](../topics/functional-dark-matter.md)** — the atlas treats
  pathway membership, recent-vs-ancient gain ratios, and uncharacterized gene families as
  function-class signatures over genome annotations.
- **[Author: 0000-0002-4999-2931](../authors/0000-0002-4999-2931.md)** — the contributor
  behind both projects that share this collection.

## Sources

- [stmt:hgt-innovation-atlas; gene_function_ecological_agora]
- [stmt:three-substrate-convergence; gene_function_ecological_agora]
- [stmt:producer-participation-framework; gene_function_ecological_agora]
- [stmt:cyanobacteria-psii-innovator-exchange; gene_function_ecological_agora]
- [stmt:mycobacteriaceae-mycolic-innovator-isolated; gene_function_ecological_agora]
- [stmt:mycolic-niche-refinement; gene_function_ecological_agora]
- [stmt:biome-enrichment-grounding; gene_function_ecological_agora]
- [stmt:architectural-promiscuity-hgt; gene_function_ecological_agora]
- [stmt:recent-ancient-ratio-signature; gene_function_ecological_agora]
- [stmt:preregistered-kos-not-phage-borne; gene_function_ecological_agora]
- [stmt:psii-rank-dependence; gene_function_ecological_agora]
- [stmt:alm-2006-not-reproduced; gene_function_ecological_agora]
- [stmt:pangenome-openness-distinct-from-m22; gene_function_ecological_agora]
- [stmt:composition-donor-inference-opportunity; gene_function_ecological_agora]
- [stmt:mge-context-mechanism-opportunity; gene_function_ecological_agora]
- [stmt:four-ibd-ecotypes; ibd_phage_targeting]
- [stmt:canonical-cd-signature; ibd_phage_targeting]
- [stmt:substudy-nesting-unidentifiable; ibd_phage_targeting]
- [stmt:iron-acquisition-genomic; ibd_phage_targeting]
- [stmt:ecoli-carries-iron-genotoxin; ibd_phage_targeting]
- [stmt:five-phage-cocktail-coverage; ibd_phage_targeting]
- [stmt:gokushovirus-cd-down; ibd_phage_targeting]
- [stmt:cohort-cocktail-mismatch; ibd_phage_targeting]
- [stmt:clinical-covariates-insufficient; ibd_phage_targeting]
- [stmt:state-dependent-dosing; ibd_phage_targeting]
- [stmt:phage-coverage-gap; ibd_phage_targeting]
- [stmt:hybrid-cocktail-needed; ibd_phage_targeting]
- [stmt:ucdavis-spans-ecotypes; ibd_phage_targeting]
- [stmt:e3-tier-a-provisional; ibd_phage_targeting]
- [stmt:synonymy-layer-reusable; ibd_phage_targeting]
- [stmt:external-phage-db-opportunity; ibd_phage_targeting]

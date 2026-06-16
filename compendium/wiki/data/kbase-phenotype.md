# Kbase Phenotype

## Overview

This page describes a shared **data collection** — the phenotype-linked
metagenomic and genomic resources organized under "Kbase Phenotype" — and
why it ties together the analyses in the IBD phage-targeting work. The
collection brings together pooled human gut metagenomes annotated with
disease phenotype (healthy, ulcerative colitis, and Crohn's disease),
strain-level genome annotations, and phage-susceptibility data, so that a
single project can move from "which microbes differ in disease" to "which
microbes can be selectively targeted." It exists in this wiki because
several otherwise-separate questions — disease signatures, microbiome
[ecotype](../topics/microbial-ecotypes.md) structure, pathobiont genomics,
and phage-cocktail design — all draw on the same phenotype-anchored data
and only make sense when read together.

The first scientific layer is a confound-aware meta-analysis. Pooling
public metagenomes is treacherous: in the pooled curatedMetagenomicData
resource, healthy and Crohn's samples come from disjoint source studies, so
a naive pooled case-vs-control mixed model is structurally unidentifiable —
study identity and disease status are perfectly entangled. The collection's
analysis therefore forces a within-substudy CD-vs-nonIBD design, comparing
diagnoses only inside studies that contain both. Run this way, a
confound-free meta-analysis across four IBD cohorts recovers the canonical
Crohn's signature — pathobionts (disease-associated commensals that turn
harmful in a dysregulated gut) up and protective commensals down — with
strong sign concordance across cohorts. That concordance is what makes the
downstream targeting credible rather than a single-study artifact.

The second layer is **ecotype** structure: reproducible community states
rather than a binary healthy/disease split. Two independent clustering
methods (LDA and a Gaussian-mixture model) applied to 8,489 MetaPhlAn3
profiles converge on four IBD microbiome ecotypes (E0-E3), with K=4 chosen
by a cross-method parsimony rule on the adjusted Rand index — i.e., the
number of clusters that the two methods most agree on. These ecotypes carry
clinical meaning: in the 23-patient UC Davis Crohn's cohort, patients
distribute non-randomly across three of the ecotypes (none fall in the
Prevotella-dominated E2), and active disease concentrates in the
transitional E1 and severe E3 states. Crucially, clinical covariates alone
separate healthy from IBD but cannot tell E1 from E3, so metagenomic
sequencing remains required to assign a patient's ecotype — the
microbiome-engineering reason this data collection cannot be replaced by
chart review. The phage data even shows depletion of a bacteriophage
itself: the Microviridae member Gokushovirus WZ-2015a is robustly reduced
in Crohn's across ecotypes, strongest in the transitional E1 state.

The third layer connects genomes to mechanism. Among the six actionable
Tier-A pathobionts, the Tier-A genomes are strongly enriched for
iron-siderophore biosynthetic gene clusters — small-molecule iron-scavenging
systems — making iron acquisition a pathobiont-defining genomic capability
rather than merely a cohort-level pathway trend. Within that set the biology
sharpens further: only *E. coli* (specifically the adherent-invasive AIEC
subset) carries both the iron-siderophore and the colibactin genotoxin
gene-cluster signature, localizing the iron-and-genotoxin axis of Crohn's
biology to *E. coli*. This is where the collection links to
[mobile genetic elements](../topics/mobile-genetic-elements.md): the
biosynthetic clusters and the phages used to attack these strains are both
mobile, plasmid- and prophage-borne features of the same genomes.

The final layer is the engineering payoff and its honest limits. A greedy
minimum-set-cover design over experimentally measured phage-strain
susceptibility yields a 5-phage cocktail covering 94.7% of 188 *E. coli*
strains in PhageFoundry — a strong result for the best-characterized target.
But coverage is uneven: the two highest-priority Crohn's pathobionts,
*H. hathewayi* and *M. gnavus*, have the weakest phage availability,
creating a gap precisely for the most actionable species. As a result no E1
Crohn's patient can be treated with a pure phage cocktail; only a hybrid
combining phages with non-phage alternatives for the gap and temperate-only
targets is feasible. And because a single patient's ecotype can drift
between E1 and E3 across visits — moderately changing the optimal cocktail
(Jaccard ~0.60) — the data motivate state-dependent re-design over a fixed
prescription. The overarching design rule is that cohort-level cocktails
will mismatch individuals unless each patient's ecotype is determined first.
Two forward-looking opportunities sit on top of this collection: a reusable
taxonomy-synonymy layer (NCBI taxid plus a GTDB-version-aware rename table)
that any multi-cohort microbiome project needs, and querying external phage
databases (INPHARED and IMG/VR) for gut-anaerobe phages to close the
*H. hathewayi*, *F. plautii*, and *M. gnavus* gap.

Two caveats temper the strongest claims. The E3-ecotype Tier-A target list
rests on single-study evidence and should be treated as provisional until a
cohort with enough E3 patients in both diagnosis groups exists; and the
substudy-nesting constraint above is a structural limit on the data, not a
modeling choice that can be tuned away.

## Projects Using This Collection

A single project currently builds on this collection:
**`ibd_phage_targeting`**. It uses every layer described above in sequence —
the confound-aware within-substudy CD-vs-nonIBD meta-analysis to define the
Crohn's signature; the four-ecotype clustering to stratify patients; the
Tier-A pathobiont genomics (iron-siderophore and colibactin clusters,
*E. coli*/AIEC localization) to choose targets; and the PhageFoundry
susceptibility data plus set-cover optimization to assemble cocktails. The
project's central conclusions — that ecotype must be measured before
prescribing, that the actionable targets have the weakest phage coverage,
and that hybrid, state-dependent cocktails are required — all depend on
having phenotype, ecotype, genome, and phage data co-located in this
collection. The shared taxonomy-synonymy scaffold and the external-database
opportunity are the parts most likely to generalize to future projects that
reuse this data.

## Connections

- [Microbial Ecotypes](../topics/microbial-ecotypes.md) — the collection's
  central organizing concept; the four E0-E3 ecotypes and the requirement to
  measure them from metagenomics come directly from this data.
- [Microbiome Engineering](../topics/microbiome-engineering.md) — the
  collection feeds phage-cocktail and hybrid-intervention design, including
  the set-cover cocktail and the state-dependent dosing logic.
- [Mobile Genetic Elements](../topics/mobile-genetic-elements.md) — the
  pathobiont biosynthetic gene clusters, the colibactin genotoxin signature,
  and the bacteriophages themselves are all mobile features of these
  genomes.
- [0000 0002 4999 2931](../authors/0000-0002-4999-2931.md) — the author
  associated with the project that uses this collection.

## Sources

- [stmt:substudy-nesting-unidentifiable; ibd_phage_targeting]
- [stmt:canonical-cd-signature; ibd_phage_targeting]
- [stmt:four-ibd-ecotypes; ibd_phage_targeting]
- [stmt:ucdavis-spans-ecotypes; ibd_phage_targeting]
- [stmt:clinical-covariates-insufficient; ibd_phage_targeting]
- [stmt:gokushovirus-cd-down; ibd_phage_targeting]
- [stmt:iron-acquisition-genomic; ibd_phage_targeting]
- [stmt:ecoli-carries-iron-genotoxin; ibd_phage_targeting]
- [stmt:five-phage-cocktail-coverage; ibd_phage_targeting]
- [stmt:phage-coverage-gap; ibd_phage_targeting]
- [stmt:hybrid-cocktail-needed; ibd_phage_targeting]
- [stmt:state-dependent-dosing; ibd_phage_targeting]
- [stmt:cohort-cocktail-mismatch; ibd_phage_targeting]
- [stmt:synonymy-layer-reusable; ibd_phage_targeting]
- [stmt:external-phage-db-opportunity; ibd_phage_targeting]
- [stmt:e3-tier-a-provisional; ibd_phage_targeting]

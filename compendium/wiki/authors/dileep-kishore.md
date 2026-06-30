# Dileep Kishore

Dileep Kishore is a researcher whose work in this corpus centers on understanding when microbial metabolic pathways are genuinely required for fitness versus merely encoded in the genome. This page exists in the wiki because all statements in the knowledge graph associated with his name originate from the [`pathway_capability_dependency`](../projects/pathway-capability-dependency.md) project, making him the sole credited contributor to that analytical thread. Readers who want to trace the underlying data or cross-project comparisons should follow the adjacent project and data pages linked below.

## Overview

Kishore's contribution addresses a deceptively simple question: does having a pathway in a genome mean the organism actually depends on it? Using RB-TnSeq (randomized-barcode transposon sequencing, a pooled fitness assay that measures the growth cost of disrupting individual genes across many conditions simultaneously) and GapMind (a tool that predicts pathway completeness from genome annotations), the project classified 161 organism–pathway pairs across 7 model bacteria and 23 GapMind pathways into four categories. Only 35.4% of pairs are Active Dependencies — complete pathways whose genes are also fitness-important — while the largest single category, Latent Capabilities at 41.0%, are pathways that are genomically complete yet show no fitness defect under standard lab conditions [\[1\]](#references). A further 14.9% are "Incomplete but Important," meaning GapMind rates them as incomplete yet their mapped genes still matter for fitness, pointing to annotation gaps or salvage routes that current databases miss [\[2\]](#references).

To rank organism–pathway pairs, the project defines a composite importance score weighting essentiality at 40%, fitness breadth (the fraction of experimental conditions that show a significant phenotype) at 30%, and fitness magnitude at 30% [\[3\]](#references). Fitness breadth is foregrounded because breadth, not magnitude, predicts evolutionary conservation better. The score is computed from Fitness Browser KEGG annotations mapped through to GapMind pathway membership.

## Projects

The single project on this author page is **pathway_capability_dependency**, which integrates two large public resources — the [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md) for gene-level RB-TnSeq fitness scores and the [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) for pangenome conservation data — to ask how pathway-level genomic content relates to functional necessity.

The project's most counterintuitive finding concerns Latent Capabilities. When condition-type stratification separates fitness effects by nitrogen source, carbon source, stress, and other contexts, all 66 Latent Capability pairs become fitness-important under at least one condition type, most often nitrogen limitation or stress [\[4\]](#references). This reframes "latent" as "conditionally active" rather than genomic baggage, consistent with the broader observation that thousands of genes appear costly in the lab yet are conserved in nature. A caveat applies: the median-based importance threshold splits pathways roughly 50/50 by construction, so the universality of this reclassification is partly an artifact of the threshold design and would need validation against an independent set of known essentials to be fully defensible [\[5\]](#references).

On the pangenome side, the project measures how many of a species' GapMind-assessed pathways are "variable" — present in 10–90% of genomes — and correlates that count with pangenome openness (the fraction of gene content that is accessory rather than core). Across 2,810 species with at least 10 sequenced genomes, the partial Spearman correlation after controlling for genome count is rho=0.530 (p=2.83e-203) [\[6\]](#references). This is notable because a prior project found no correlation between pangenome openness and either environment or phylogeny effect sizes; pathway variation provides the mechanistically interpretable link that broader ecological variables could not [\[7\]](#references).

Amino acid biosynthesis pathways show the strongest dependence on the accessory genome (the set of genes present in some but not all strains of a species). Leucine, valine, arginine, lysine, and threonine biosynthesis each show core-versus-all completeness gaps of roughly 0.14, meaning about 14% of a species' apparent biosynthetic capacity for these amino acids sits in accessory genes distributed across strains rather than universally retained [\[8\]](#references). This is direct evidence for Black Queen dynamics — the evolutionary hypothesis that leaky public goods (here, biosynthetic outputs that can be absorbed from neighbors) drive gene loss in the non-producing strains. The accessory genome thus acts as metabolic insurance: roughly 14% of completeness for the top accessory-dependent pathways comes from genes held only in some strains, so that strains with different biosynthetic portfolios cover each other's gaps within the species [\[9\]](#references).

Active Dependencies — the pairs where complete pathways actually carry fitness-important genes — have a mean core-genome completeness of 0.986 versus 0.975 for Latent Capabilities, a small but consistent enrichment [\[10\]](#references). One methodological caveat: only 7 of the 48 Fitness Browser organisms have GapMind data, and all 7 are well-studied model organisms with near-complete core genomes, which compresses the conservation signal and limits how broadly the Tier 1 classification can be generalized [\[11\]](#references).

Within-species diversity is captured through metabolic ecotypes — groups of strains with distinct binary pathway profiles. Using hierarchical Jaccard clustering on 225 species with at least 50 genomes and 3 variable pathways, the project finds a median of 4 ecotypes per species (up to 8). Ecotype count correlates with pangenome openness at partial rho=0.322 (p=8.0e-07) after controlling for genome count [\[12\]](#references). Phylogenetic confounding is a recognized limitation here: correlations were controlled for genome count and checked within taxonomic groups, but full phylogenetic independent contrasts were not computed, and prior work found that phylogeny dominates gene content in 60.5% of species, so some ecotype structure may reflect evolutionary history rather than independent metabolic adaptation [\[13\]](#references).

A planned extension — correlating metabolic ecotypes with AlphaEarth environmental niche breadth to test whether more ecotypically diverse species occupy broader environmental ranges — was not executed. AlphaEarth embeddings cover only 28% of the relevant genomes, which would have severely limited statistical power, and this connection remains an open future direction [\[14\]](#references).

## Topics

Kishore's work touches six thematic areas represented in the wiki.

**[Metabolic Pathways](../topics/metabolic-pathways.md)** is the central topic: the project's main contribution is a classification framework for metabolic pathway dependencies that goes beyond genome-annotation-based completeness scores.

**[Gene Fitness](../topics/gene-fitness.md)** is directly coupled because the entire classification rests on RB-TnSeq fitness measurements — gene disruption fitness scores across hundreds of experimental conditions drawn from the Fitness Browser.

**[Pangenome Architecture](../topics/pangenome-architecture.md)** is adjacent because the core/accessory genome split is essential to understanding which strains carry which pathways and how pathway variation tracks genome fluidity. The [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) data resource is shared across multiple projects in this space.

**[Microbial Ecotypes](../topics/microbial-ecotypes.md)** emerges from the within-species clustering analysis, where distinct pathway profiles define sub-populations with different metabolic phenotypes rather than different species.

**[Functional Dark Matter](../topics/functional-dark-matter.md)** — genes and pathways whose function cannot be assigned from sequence or annotation alone — is implicated by the "Incomplete but Important" category, where GapMind says a pathway is incomplete yet the genes it can identify are still fitness-critical, hinting at unannotated steps or alternative routes.

**[Environment Biogeography](../topics/environment-biogeography.md)** is the most speculative connection: the AlphaEarth analysis that would have linked metabolic ecotypes to environmental distributions was not completed, so this adjacency is prospective rather than realized in the current results.

## References

1. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "1. Pathway Completeness Alone Is Insufficient to Predict Metabolic Dependency".
2. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "1. Pathway Completeness Alone Is Insufficient to Predict Metabolic Dependency".
3. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "1. Pathway Completeness Alone Is Insufficient to Predict Metabolic Dependency".
4. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "2. All "Latent Capabilities" Become Important Under Specific Conditions".
5. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Limitations".
6. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "4. Variable Pathways Strongly Correlate with Pangenome Openness".
7. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "4. Variable Pathways Strongly Correlate with Pangenome Openness".
8. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "5. Amino Acid Biosynthesis Pathways Show the Strongest Accessory Dependence".
9. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Accessory Genome as Metabolic Insurance".
10. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "3. Conservation Validation: Active Dependencies Have Near-Complete Core Genomes".
11. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Limitations".
12. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "6. Metabolic Ecotypes Correlate with Pangenome Openness".
13. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Limitations".
14. [Pathway Capability Dependency](../projects/pathway-capability-dependency.md) — REPORT.md › "Limitations".

# KBase UniRef

## Overview

KBase UniRef is one of the reference data collections in the BERDL (the BER
Data Lakehouse), the shared lakehouse that holds the genomes, gene clusters,
biochemistry, and annotation tables the projects in this compendium query
against. UniRef-style clustering groups protein-coding genes from many genomes
into families of homologous sequences, and within BERDL those families are
indexed by stable cluster and centroid gene identifiers. This page exists
because two otherwise quite different projects, an intensive single-organism
multi-omics study and a domain-wide horizontal-gene-transfer atlas, both lean on
this clustered-gene scaffold to relate their own analyses back to the shared
lakehouse. The collection is what lets a finding about one organism's genes be
expressed in the same identifier space as a survey across nearly nineteen
thousand species.

The depth of that integration is concrete on the single-organism side. The
*Acinetobacter baylyi* ADP1 explorer demonstrated that four of five connection
types between its private database and BERDL collections matched at over 90%,
including a perfect 100% match for genome IDs and compounds and 91% for
reactions. The one place where naive matching failed entirely was gene-cluster
identifiers: the ADP1 database uses mmseqs2-style cluster IDs that share 0%
direct string overlap with BERDL centroid gene IDs. A dedicated gene junction
table closed that gap, mapping all 4,891 BERDL clusters onto 4,081 unique ADP1
clusters and giving a complete bridge between the two identifier systems. That
junction is the practical reason the collection "connects" the projects: it
turns an unmatched ID namespace into a shared coordinate system for genes. This
matters for [pangenome architecture](../topics/pangenome-architecture.md),
because cluster identity is exactly what defines whether a gene belongs to a
species' conserved core or its variable accessory genome.

## Projects Using This Collection

**Acinetobacter baylyi ADP1 explorer.** This project integrates a
user-provided SQLite database of 15 tables (461,522 rows, 135 MB) whose central
`genome_features` table holds 5,852 genes annotated across 51 columns spanning
six data modalities. Because ADP1 is absent from the Fitness Browser, the
condition-specific mutant growth data it contributes is a unique fitness
resource not otherwise available in BERDL, which is what makes it worth
bridging into the shared clustered-gene space rather than analyzing in
isolation. The project connects to several topics this wiki tracks. On
[gene fitness](../topics/gene-fitness.md), it found that essentiality is
media-dependent (499 genes essential on minimal media versus 346 on rich LB,
reflecting the extra biosynthetic burden minimal media imposes), and that
mutant fitness across eight carbon sources was only moderately correlated (mean
pairwise r = 0.44), with urea catabolism standing nearly independent of quinate
and the other conditions. Essential genes are far more annotation-rich than
dispensable ones (33% versus 5% carry COG assignments; 92% versus 53% carry
KEGG KO assignments) and are more likely to sit in the conserved core
pangenome, consistent with the general pattern that conserved genes tend to be
essential, though that core-essentiality link is reported at only medium
confidence.

The ADP1 work also ties into [metabolic pathways](../topics/metabolic-pathways.md)
and the [ADP1 model system](../topics/adp1-model-system.md). Core metabolism is
highly conserved across the 14 *Acinetobacter* genomes, with 1,248 of 1,330
unique reactions (94%) shared by all genomes and only 20 genome-unique. Flux
balance analysis (FBA, which predicts which reactions carry flux when a model is
optimized for growth) and TnSeq essentiality calls agreed for 73.8% of the 866
genes that had both measurements, and the discordant 26% were flagged as
candidates for model refinement or regulatory effects. Two caveats temper the
metabolic modeling, and the context states them plainly. First, 87% of the
121,519 growth phenotype predictions depend on at least one gapfilled reaction
(a reaction added to a draft model to make it produce biomass), so prediction
accuracy is tightly coupled to gapfilling quality. Second, the multi-omics
database is sparse where it matters most: no gene carries data across all six
modalities, and the thin 15% FBA flux coverage limits the model-versus-
experiment concordance analysis to just those 866 genes. Proteomics adds a
narrower but cleaner signal, with protein abundance measured across 7 engineered
strains for 2,383 genes showing high cross-strain correlation, suggesting the
engineered modifications have targeted rather than global proteome effects. The
clearest open lead toward [functional dark matter](../topics/functional-dark-matter.md)
is the roughly 8% of essential genes that lack KEGG KO assignments, which are
promising candidates for discovering novel essential functions.

**Gene function ecological agora.** This project operates at the opposite
scale, building a bacterial-domain HGT/innovation atlas of 13.7M
producer/participation scores and 17M Sankoff-parsimony gain events with
recipient-rank acquisition attribution across 18,989 GTDB r214 species
representatives. Its core contribution to [mobile genetic elements](../topics/mobile-genetic-elements.md)
is the Producer x Participation framework, a direction-agnostic per-clade
categorization (Innovator-Isolated / Innovator-Exchange / Sink-Broker-Exchange /
Stable) that remains usable at deep taxonomic ranks where full
duplication-transfer-loss (DTL) reconciliation is computationally intractable.
Atlas-level findings are made robust by convergence across three independent
measurement substrates: Sankoff effect size, sample-biome ecology metadata, and
per-strain phenotype tables. That ecological grounding is borne out by biome
enrichment, where pre-registered clades land in their expected
[environments and biogeography](../topics/environment-biogeography.md):
Mycobacteriaceae are enriched 7.88x in host-pathogen biomes (p<10^-45),
Cyanobacteriia 2.77x in photic aquatic biomes (p<10^-52), and Bacteroidota
1.40x in gut/rumen (p<10^-35).

Several of the atlas findings sharpen how innovation is read off
[microbial ecotypes](../topics/microbial-ecotypes.md). Cyanobacteria are
confirmed as Innovator-Exchange on photosystem II at the Cyanobacteriia class
rank (producer d=+1.50, consumer d=+0.70), the appropriate rank because PSII
predates Cyanobacteria diversification. Mycobacteriaceae are Innovator-Isolated
on the mycolic-acid pathway at family and order ranks (producer d=+0.31,
consumer d=-0.19), indicating high paralog expansion but little cross-clade
exchange, a signature further refined to host-pathogen-niche mycobacteria
rather than soil mycobacteria. A recurring methodological caution is that these
verdicts are rank-dependent: the PSII verdict shifts from STABLE at genus to
Innovator-Exchange at class to Innovator-Isolated at phylum, so the rank must be
chosen on biological grounds rather than read off any single resolution; this is
flagged at medium confidence. Architecturally, promiscuity tracks HGT
propensity, with mixed-category KOs carrying a median of 46 Pfam domain
architectures per KO versus 1 for PSII, mirroring the "modular systems exchange
more" pattern. Function class also leaves a temporal fingerprint: the
recent-to-ancient gain ratio separates HGT-active CRISPR-Cas (24.5x,
recent-skewed) from strict housekeeping genes (~1x, vertical inheritance).
Importantly, the pre-registered KO sets are not themselves mobile elements, all
three (PSII, mycolic-acid, PUL) show near-zero MGE-machinery rates against the
1.37% atlas baseline, meaning they are not phage, transposase, integrase, or
plasmid genes.

This project is candid about its limits and open directions. Two negative
results matter for how the atlas should and should not be validated. The Alm
2006 r~0.74 correlation between histidine-kinase count and lineage-specific
expansion is *not* reproduced at full GTDB scale, recovering only modest
correlations (r=0.10-0.29) across 18,989 genomes. And recent between-species
gain attribution is uncorrelated with within-species
[pangenome openness](../topics/pangenome-architecture.md) (Spearman r=-0.011
across 894 genera), so pangenome openness is not a valid cross-substrate
validation of the acquisition-depth signal, an honest constraint on what the
atlas can claim. The remaining work is mechanistic: testing whether
high-exchange KOs are mobile-element-mediated by flagging phage, plasmid, and
integron context per gain event is the identified next step toward explaining
cross-clade gene flow, while composition-based donor inference at deep ranks
stays blocked because per-CDS sequence is not in BERDL's queryable schemas, so
only an exploratory tree-based donor-inference layer shipped.

## Connections

The two projects meet on this collection because both express their results in
BERDL's clustered-gene identifier space, but they illuminate different topics
from it. The ADP1 explorer is the wiki's richest anchor for
[gene fitness](../topics/gene-fitness.md) and the
[ADP1 model system](../topics/adp1-model-system.md), supplying condition-
resolved essentiality and a worked
[metabolic pathway](../topics/metabolic-pathways.md) reconciliation between FBA
and TnSeq. The ecological agora anchors
[mobile genetic elements](../topics/mobile-genetic-elements.md) and
[microbial ecotypes](../topics/microbial-ecotypes.md), reading gene gain and
exchange across the GTDB tree. Both reach into
[functional dark matter](../topics/functional-dark-matter.md), one through
unannotated essential genes, the other through the unattributed donors and
blocked composition-based inference at the frontier of the atlas. They also
share [pangenome architecture](../topics/pangenome-architecture.md) as common
ground: ADP1 places essential genes in the conserved core, while the atlas warns
that core/accessory openness does not stand in for acquisition depth, two views
of the same pangenome concept seen at organism and domain scale.

## Sources

- [stmt:adp1-multiomics-database; acinetobacter_adp1_explorer]
- [stmt:berdl-connectivity; acinetobacter_adp1_explorer]
- [stmt:cluster-id-bridge; acinetobacter_adp1_explorer]
- [stmt:adp1-fitness-unique-resource; acinetobacter_adp1_explorer]
- [stmt:essentiality-media-dependence; acinetobacter_adp1_explorer]
- [stmt:condition-specific-fitness; acinetobacter_adp1_explorer]
- [stmt:essential-genes-annotation-rich; acinetobacter_adp1_explorer]
- [stmt:essential-core-pangenome; acinetobacter_adp1_explorer]
- [stmt:conserved-core-metabolism; acinetobacter_adp1_explorer]
- [stmt:fba-tnseq-concordance; acinetobacter_adp1_explorer]
- [stmt:gapfilling-dependence; acinetobacter_adp1_explorer]
- [stmt:modality-overlap-limitation; acinetobacter_adp1_explorer]
- [stmt:proteomics-targeted-effects; acinetobacter_adp1_explorer]
- [stmt:unannotated-essential-genes; acinetobacter_adp1_explorer]
- [stmt:hgt-innovation-atlas; gene_function_ecological_agora]
- [stmt:producer-participation-framework; gene_function_ecological_agora]
- [stmt:three-substrate-convergence; gene_function_ecological_agora]
- [stmt:biome-enrichment-grounding; gene_function_ecological_agora]
- [stmt:cyanobacteria-psii-innovator-exchange; gene_function_ecological_agora]
- [stmt:mycobacteriaceae-mycolic-innovator-isolated; gene_function_ecological_agora]
- [stmt:mycolic-niche-refinement; gene_function_ecological_agora]
- [stmt:psii-rank-dependence; gene_function_ecological_agora]
- [stmt:architectural-promiscuity-hgt; gene_function_ecological_agora]
- [stmt:recent-ancient-ratio-signature; gene_function_ecological_agora]
- [stmt:preregistered-kos-not-phage-borne; gene_function_ecological_agora]
- [stmt:alm-2006-not-reproduced; gene_function_ecological_agora]
- [stmt:pangenome-openness-distinct-from-m22; gene_function_ecological_agora]
- [stmt:mge-context-mechanism-opportunity; gene_function_ecological_agora]
- [stmt:composition-donor-inference-opportunity; gene_function_ecological_agora]

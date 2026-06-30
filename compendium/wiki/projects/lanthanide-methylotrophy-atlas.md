# Lanthanide Methylotrophy Atlas

This project surveyed rare-earth-element (REE) dependent methanol oxidation across the BERDL pangenome—293K bacterial and archaeal genomes—by comparing the prevalence of the lanthanide-dependent enzyme xoxF against the classical calcium-dependent methanol dehydrogenase mxaF. The central finding is stark: xoxF outnumbers mxaF by approximately 19:1 globally, and the signal survives phylogenetic correction, indicating that lanthanide-dependent methanol metabolism has displaced the canonical pathway across the bacterial kingdom. Beyond classical methylotrophs, the highest per-genome xoxF rates appear in non-traditional lineages like Acidobacteriota (28.3%), suggesting the cassette has broader ecological roles in soil and sediment that remain to be characterized.

## Key findings

- REE-impacted samples show a 3.5-fold descriptive elevation in xoxF rate but at n=37 the signal is too small to clear the FDR threshold (p_BH=0.082), so it remains descriptive rather than inferential. *(confidence: medium)*
- xoxF co-occurs with lanmodulin in only 79.0 percent of lanmodulin genomes, just below the pre-registered 80 percent threshold, so lanmodulin presence does not reliably predict a co-located lanthanide-MDH operon. *(confidence: medium)*
- For BERDL pangenome lanmodulin work the bakta product field should be used exclusively, since it matches 62 genomes all in canonical alpha-Proteobacterial methylotroph clades while eggNOG lanM is noise. *(confidence: high)*
- xoxF dominance is robust to phylogenetic correction, with a Bayesian binomial GLMM yielding a phylogeny-corrected ratio of about 143:1 rather than an artifact of one large phylum. *(confidence: high)*
- Across 293K genomes the lanthanide-dependent methanol dehydrogenase xoxF outnumbers the calcium-dependent mxaF by roughly 19:1, strongly supporting that REE-dependent methanol oxidation dominates the canonical pathway. *(confidence: high)*
- Bakta-validated lanmodulin is detected in 62 genomes, all 100 percent confined to three alpha-Proteobacterial methylotroph families, strongly supporting total clade restriction of this lanthanide-binding protein. *(confidence: high)*
- Host-associated environments are dramatically depleted in xoxF (OR=0.058, p_BH=0), consistent with the absence of methylotrophy in the gut and host niche. *(confidence: high)*
- Soil/sediment is the strongest broad-class environmental enrichment for xoxF presence (OR=1.92, p_BH=6e-39 across 13,779 genomes), consistent with methanol oxidation as a known soil process and soil REE mineral reservoirs. *(confidence: high)*
- The 37 REE-acid-mine-drainage MAGs are dominated by acidophilic and metal-tolerant lineages rather than methylotrophs, with only 4 of 37 carrying any xoxF and none carrying validated lanmodulin or xoxJ. *(confidence: high)*
- The apparent xoxF-without-PQQ asymmetry is largely an annotation artifact, as 59 percent of xoxF genomes lacking eggNOG PQQ annotations carry at least one bakta PQQ product that eggNOG misses. *(confidence: high)*
- The highest per-genome xoxF rates occur in phyla rarely linked to one-carbon metabolism, including Acidobacteriota at 28.3 percent, expanding the candidate set of lanthanide-utilizing organisms beyond classical methylotrophs. *(confidence: high)*
- eggNOG and bakta marker calls disagree sharply by marker, with eggNOG Preferred_name lanM producing 505 false positives concentrated in unrelated gut Bacillota that are not lanthanide users. *(confidence: high)*
- Recruiting a larger collection of explicitly REE-impacted metagenomes from sequence archives would convert the descriptive REE-impacted enrichment signal into an inferential test of whether REE supply selects for the cassette. *(confidence: medium)*
- Targeted RB-TnSeq under lanthanum or cerium chloride stress in the FitnessBrowser organism panel would identify the first transposon-validated REE-tolerance gene set in soil organisms that already carry xoxF. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [David Lyon](../authors/0000-0002-1927-3565.md)

[Open the full report →](../../../projects/lanthanide_methylotrophy_atlas/REPORT.md)

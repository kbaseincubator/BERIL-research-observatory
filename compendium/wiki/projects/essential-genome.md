# Essential Genome

This project mapped the pan-bacterial essential genome by analyzing RB-TnSeq transposon insertion data across 48 phylogenetically diverse bacteria and archaea to determine which genes are required for survival. The core finding is that only 859 ortholog families (5%) are universally essential, with just 15 gene families—dominated by ribosomal proteins and key metabolic enzymes—essential in every organism, while the vast majority of essential genes are context-dependent, essential in some organisms but dispensable in others based on pangenome composition. This reveals that true bacterial essentiality is genomic-context-dependent and that the irreducible functional core of bacterial life is far smaller than previously estimated.

## Key findings

- Connected-component ortholog grouping can over-merge: transitive BBH-graph connections may combine unrelated genes into one ortholog group, especially for multi-domain proteins. *(confidence: medium)*
- The 48 Fitness Browser organisms are biased toward culturable Proteobacteria, so essentiality patterns in underrepresented lineages remain uncertain. *(confidence: medium)*
- Because most essential gene families are essential in only a minority of organisms, only the 859 universally essential families are reliable broad-spectrum antibiotic targets. *(confidence: medium)*
- Cross-species RB-TnSeq data extend the principle that the pan-genome makes essentiality strain-dependent and evolvable from within a single species to 48 phylogenetically diverse bacteria and archaea. *(confidence: medium)*
- The experimentally defined universally essential bacterial genome is small and deeply conserved, smaller than computational minimal-gene-set estimates because it requires transposon disruption to be lethal across all 48 tested organisms. *(confidence: medium)*
- Conservation breadth tracks essentiality: universally essential genes are 91.7% core versus 80.7% for non-essential, while orphan essentials are only 49.5% core, indicating strain-specific essential functions. *(confidence: high)*
- Fifteen gene families -- dominated by ribosomal proteins plus groEL, pyrG, fusA, and valS -- are essential in every one of the 48 surveyed bacteria, forming the irreducible core of bacterial life. *(confidence: high)*
- Only 859 of 17,222 cross-organism ortholog families (5.0%) are universally essential, the great majority being strict single-copy families. *(confidence: high)*
- The 7,084 essential genes lacking orthologs in any other Fitness Browser organism are 58.7% hypothetical, far more uncharacterized than universally essential genes (8.2%), marking a frontier of unknown essential biology. *(confidence: high)*
- Transferring functional context from non-essential orthologs in ICA fitness modules produced 1,382 family-backed function predictions for hypothetical essential genes (35.3% of predictable targets). *(confidence: high)*
- Variably essential families -- essential in some organisms but dispensable in others -- are the largest class at 4,799 families (27.9%), making context-dependent essentiality the norm rather than the exception. *(confidence: high)*
- Characterizing the 7,084 orphan essential genes -- testing whether they sit on mobile elements, are recently acquired, or are rapidly evolving -- is a key direction for mapping unknown essential biology. *(confidence: medium)*
- The 1,382 module-transfer function predictions could be experimentally validated via CRISPRi knockdown under the specific conditions implied by their module context. *(confidence: medium)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/essential_genome/REPORT.md)

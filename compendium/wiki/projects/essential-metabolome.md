# Essential Metabolome

This project mapped the minimal metabolic repertoire that bacteria require for independent growth by linking genome-wide metabolic pathway completeness predictions to experimentally identified essential genes. Analyzing seven organisms with available fitness data, the study found that 17 of 18 amino acid biosynthesis pathways are nearly universally conserved, suggesting amino acid prototrophy is an ancestral trait in free-living bacteria—though one anaerobic organism (Desulfovibrio vulgaris) lacks serine biosynthesis, likely reflecting adaptation to amino-acid-rich environments where streamlined metabolism is advantageous. The results reveal a core minimal metabolome while highlighting how ecological context shapes metabolic gene content.

## Key findings

- Because the underlying RB-TnSeq essential gene experiments were conducted in rich media, biosynthetic genes may appear non-essential due to nutrient supplementation, confounding essentiality interpretation. *(confidence: medium)*
- Escherichia coli genomes are completely absent from the KBase pangenome GapMind dataset because too many E. coli genomes existed for species-level GTDB analysis, restricting the study to a 7-organism pilot rather than the intended 45-organism survey. *(confidence: high)*
- The inferred D. vulgaris serine auxotrophy may be a GapMind detection artifact, as the organism could use a non-canonical pathway or divergent enzymes that fall below GapMind's homology threshold. *(confidence: medium)*
- The apparent serine auxotrophy of D. vulgaris is ecologically plausible because its amino-acid-rich anaerobic habitats could make loss of biosynthetic capacity advantageous through genomic economy. *(confidence: low)*
- The presence of complete pathways for all 18 amino acids in 6 of 7 organisms suggests amino acid prototrophy is the ancestral state for free-living bacteria, forming a minimal metabolic repertoire for independent growth. *(confidence: medium)*
- Desulfovibrio vulgaris is the only one of the 7 organisms lacking a complete serine biosynthesis pathway according to GapMind, suggesting a potential metabolic serine auxotrophy. *(confidence: medium)*
- No metabolic pathway is truly universal at 100% completeness even in this small sample, so the data reveal near-universal rather than strictly universal pathway completeness with organism-specific gaps. *(confidence: high)*
- Of 18 amino acid biosynthesis pathways, 17 are present in all 7 bacterial organisms analyzed, indicating high conservation of amino acid biosynthesis within the sample. *(confidence: high)*
- TCA cycle intermediates, fermentation products, and amino acid catabolism are conserved across all 7 organisms, indicating a shared central catabolic capacity for breaking down common organic compounds. *(confidence: high)*
- Experimentally testing D. vulgaris growth on serine-free minimal media would confirm whether the GapMind-predicted serine auxotrophy is genuine. *(confidence: medium)*
- Using eggNOG EC-to-KEGG pathway annotations could extend the analysis to all 45 Fitness Browser organisms including E. coli, overcoming GapMind's coverage gap. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/essential_metabolome/REPORT.md)

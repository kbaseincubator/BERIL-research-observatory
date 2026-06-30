# Paperblast Explorer

This analysis provides the first comprehensive characterization of the BERDL-hosted PaperBLAST database at the protein family level, quantifying the "dark matter" of protein biology. Using sequence clustering and text-mining literature coverage data, we found that 55% of protein families are functionally dark or dim in the literature: 9.2% have zero papers, and 46.1% have exactly one. By linking PaperBLAST to the Fitness Browser via 129,823 VIMSS cross-references, we created a resource for discovering genes with experimental fitness signatures but little or no literature—the highest-value candidates for functional characterization.

## Key findings

- A text-mined gene-paper link does not imply functional characterization, and the 65.6% of genes with a single paper likely include many incidental mentions. *(confidence: high)*
- Only about 19% of SwissProt is present in PaperBLAST because many reviewed entries lack matching PMC full text, so curated knowledge exists for proteins PaperBLAST cannot connect to. *(confidence: medium)*
- PaperBLAST mines only PubMed Central open-access full text, so paywalled papers are missed, creating a systematic bias against fields and journals with lower open-access rates. *(confidence: high)*
- 129,823 VIMSS cross-references connect PaperBLAST to the Fitness Browser, creating a path from literature coverage to experimental fitness phenotypes for identifying understudied but functionally important genes. *(confidence: medium)*
- This work provides the first protein-family-level characterization of the BERDL PaperBLAST collection, quantifying 5,218 multi-member protein families at 50% identity with zero literature coverage as the dark matter of protein biology. *(confidence: medium)*
- Among 15,312 bacterial organisms the top 100 capture 44.3% of bacterial literature, led by pathogens and model organisms, leaving environmental and non-pathogenic bacteria dramatically underrepresented. *(confidence: high)*
- At 50% identity, 9.2% of protein families (31,653) have zero papers and 46.1% have exactly one, so 55% of protein families are functionally dark or dim in the literature. *(confidence: high)*
- Homo sapiens alone accounts for 46.7% of all gene-paper records in PaperBLAST, and the top five organisms capture 72.8%, reflecting extreme organism-level literature concentration. *(confidence: high)*
- Literature attention is extremely unequal, with a Gini coefficient of 0.967 across organisms and 0.669 across genes, mirroring wealth-inequality patterns. *(confidence: high)*
- MMseqs2 clustering of 815,571 PaperBLAST protein sequences yields 628K clusters at 90% identity, 345K protein families at 50%, and 215K superfamilies at 30% identity. *(confidence: high)*
- Of 841K genes with any text-mined paper link, 551K (65.6%) have exactly one paper, while just 6% of genes account for 57.7% of all gene-paper links. *(confidence: high)*
- Protein family size correlates positively with literature coverage, yet 4.6% of multi-member 50% identity clusters (5,218 families) remain genuinely unstudied, dominated by REBASE methyltransferases and biolip structural entries. *(confidence: medium)*
- The kescience_paperblast collection on BERDL contains 12.4 million rows across 14 tables, linking genes to papers via text mining of PubMed Central full-text plus curated and structural annotations. *(confidence: high)*
- The 130K VIMSS links to the Fitness Browser can be used to identify fitness-important genes that lack literature, surfacing high-impact understudied genes. *(confidence: medium)*
- The 5,218 dark protein families could be functionally annotated using AlphaFold structure prediction and domain annotation to infer putative functions. *(confidence: medium)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/paperblast_explorer/REPORT.md)

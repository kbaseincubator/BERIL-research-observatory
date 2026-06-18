# Resistance Hotspots

This project maps antibiotic resistance genes across nearly 300,000 microbial genomes to identify which species and ecological environments harbor the highest concentrations of resistance and whether resistance accumulation can be predicted from evolutionary or environmental features. Currently in the planning stage with no completed analyses, the project has identified critical technical challenges in accessing pangenome databases and mapping fitness data that must be resolved before implementation can proceed. The planned approach—testing whether open pangenomes preferentially accumulate resistance genes and evaluating fitness trade-offs of carrying resistance mutations—offers a novel perspective on resistance evolution at the species level.

## Key findings

- COUNT(*) and SHOW TABLES queries on the billion-row pangenome tables time out, so large-table exploration must rely on LIMIT-based sampling run inside JupyterHub with Spark SQL rather than the REST API. *(confidence: high)*
- Environmental hotspot analysis will be limited because AlphaEarth embeddings cover only 28.4% of genomes and NCBI environment metadata is sparse and stored in an entity-attribute-value format. *(confidence: medium)*
- Mapping pangenome ARG genes to fitness data is problematic because the Fitness Browser uses different model organisms (e.g., E. coli K12) and gene ID schemes than the wild-type strains in the pangenome collection. *(confidence: high)*
- The planned ARG identification by keyword matching of gene descriptions is underspecified and is expected to yield high false-positive and false-negative rates, with no defined validation strategy to confirm true resistance genes. *(confidence: medium)*
- The project has zero completed analysis, so no conclusions, visualizations, or results currently exist to evaluate. *(confidence: high)*
- A central planned analysis is to test whether antibiotic resistance genes are preferentially core or accessory genes and to relate pangenome openness to ARG diversity. *(confidence: medium)*
- The analysis is designed to map antibiotic resistance genes across 293,059 genomes spanning 27,690 microbial species in the BERDL kbase_ke_pangenome collection (GTDB r214). *(confidence: high)*
- The plan proposes cross-referencing ARG-containing genes against kescience_fitnessbrowser transposon-mutant fitness data to evaluate fitness trade-offs of carrying resistance genes. *(confidence: medium)*
- The project aims to identify which microbial species and ecological environments harbor the highest concentration of antibiotic resistance genes and whether resistance accumulation can be predicted from phylogenetic and ecological features. *(confidence: high)*
- The project is currently in the planning stage with no analysis implemented: all six notebooks contain only skeleton code with TODO placeholders, no data files have been generated, and no findings exist. *(confidence: high)*
- Validation against the BERDL API revealed that the eggnog_mapper_annotations table times out via REST API and the orthogroup table does not exist or is inaccessible, blocking the planned ARG-annotation queries. *(confidence: high)*
- eggNOG functional annotations join on gene_cluster_id rather than gene_id and gene clusters are species-specific, so the recommended approach is to use the gene_cluster table with species-level grouping instead of the non-existent orthogroup table. *(confidence: medium)*
- A testable hypothesis worth pursuing is that species with open pangenomes (high accessory:core ratio) carry higher ARG diversity than species with closed pangenomes, enabling statistical testing of resistance accumulation. *(confidence: medium)*
- ARG detection could be made more robust by using sequence similarity (BLAST/DIAMOND) against CARD protein sequences with an identity threshold rather than relying on keyword matching of annotations. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [William J. Riehl](../authors/0000-0002-3405-2744.md)

[Open the full report →](../../../projects/resistance_hotspots/REPORT.md)

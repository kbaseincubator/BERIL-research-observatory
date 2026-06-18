# Env Embedding Explorer

This project analyzed AlphaEarth embeddings—64-dimensional environmental representations derived from satellite imagery at microbial genome sampling locations—to understand what geographic and ecological signal they encode. The analysis revealed that environmental samples (soil, marine, freshwater) show a 3.4-fold stronger geographic distance-embedding distance relationship than human-associated samples (clinical, gut), confirming the embeddings capture real spatially-varying environmental features like climate, land use, and vegetation type. It also identified substantial limitations: only 28% of the pangenome has embeddings, 38% of that subset comes from human clinical samples, and 36% of coordinates map to likely institutional addresses rather than true field sites.

## Key findings

- Because AlphaEarth coverage is only 28.4% of genomes and the subset carries a 38% human/clinical bias, the embedded population may not represent the overall NCBI or pangenome population. *(confidence: high)*
- The coordinate QC heuristic is crude and mislabels several legitimate field research sites (e.g., the DOE Rifle groundwater site and Saanich Inlet) as institutional addresses, requiring refinement using isolation-source homogeneity. *(confidence: high)*
- AlphaEarth embeddings encode geographic and environmental context derived from satellite imagery, capturing spatially varying features such as climate, land use, and vegetation, and are most informative for environmental samples and least informative for clinical isolates. *(confidence: medium)*
- The strong clinical sampling bias may partially explain why the ecotype_analysis project found AlphaEarth environment similarity to be only a weak predictor of gene content, since interchangeable hospital environments dilute the environment-gene-content relationship. *(confidence: medium)*
- A heuristic flagged 36.6% of embedded genomes (30,469) as clustering at shared coordinates indicative of institutional addresses rather than true sampling sites. *(confidence: medium)*
- A reusable harmonization mapped 5,774 unique free-text isolation_source values to 12 broad environment categories, capturing 71% of labeled genomes while 17% remained as an Other tail. *(confidence: medium)*
- AlphaEarth embedding cosine distance increases monotonically with geographic distance across 50,000 sampled genome pairs, confirming the embeddings encode real spatially autocorrelated environmental signal rather than noise. *(confidence: high)*
- AlphaEarth embeddings cover only 83,287 genomes (28.4% of the 293,059-genome pangenome database) and are biased toward genomes with valid lat/lon metadata. *(confidence: high)*
- Environmental samples show 3.4x stronger geographic signal in AlphaEarth embeddings than human-associated samples (2.0x), because hospitals share similar urban satellite imagery worldwide while natural landscapes differentiate strongly. *(confidence: high)*
- The AlphaEarth subset is dominated by a clinical/human sampling bias, with 38% of the 83,287 embedded genomes being human-associated, reflecting NCBI's overall bias toward pathogen sequencing. *(confidence: high)*
- The embedding space also shows taxonomic structure when colored by phylum, though this is partially confounded with environment since some taxa are predominantly tied to specific habitats. *(confidence: medium)*
- UMAP reduction of the 64-dimensional embeddings reveals substantial structure with 320 DBSCAN clusters, many dominated by a single environment category, with rare environment types concentrating in just a few clusters. *(confidence: medium)*
- Correlating the 64 individual embedding dimensions (A00–A63) with latitude, temperature, precipitation, NDVI, or land cover could reveal what environmental feature each dimension encodes. *(confidence: low)*
- Re-running the ecotype analysis restricted to environmental-only samples could reveal a stronger environment-gene-content signal where the embeddings carry more geographic information. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/env_embedding_explorer/REPORT.md)

# Pangenome Pathway Geography

This project tested whether genetic flexibility in bacterial pangenomes enables metabolic pathway diversity and broader ecological niches across 1,872 species. The key finding: ecological niche breadth, captured through satellite-derived environmental embeddings, was the strongest predictor of metabolic pathway completeness (r=0.412), outperforming geographic distance alone—showing that environment rather than location shapes microbial metabolism. All three hypotheses linking pangenome openness, pathway completeness, and niche adaptation received significant support, supporting a model where flexible gene content allows bacteria to occupy diverse ecological niches.

## Key findings

- Correct GapMind pathway aggregation requires taking the best (MAX) score per genome-pathway pair, because GapMind stores multiple rows per genome-pathway pair (one per step) which can otherwise corrupt completeness counts. *(confidence: high)*
- Only 6.8% of species (1,872/27,690) had complete data across all three datasets, because AlphaEarth embeddings cover just 28% of genomes (83K/293K), limiting generalizability. *(confidence: high)*
- The correlations do not control for phylogenetic non-independence or for genome count per species, so shared ancestry and uneven sampling intensity could confound the reported relationships. *(confidence: medium)*
- Accessory genes are interpreted to enable metabolic heterogeneity within a species, consistent with open pangenomes supporting niche-specific metabolic strategies. *(confidence: medium)*
- Ecological diversity captured by AlphaEarth embeddings predicts metabolic pathway completeness better than spatial spread, since geographic distance alone gave a weaker signal (r=0.360). *(confidence: high)*
- Pangenome flexibility is interpreted to enable ecological adaptation, linking open gene content to wider environmental niches. *(confidence: medium)*
- A high core genome fraction was strongly negatively correlated with ecological niche breadth (r=-0.445, p=1.4e-91), providing converging evidence that pangenome flexibility enables ecological adaptation. *(confidence: high)*
- All three hypotheses linking pangenome openness, metabolic pathway completeness, and ecological niche breadth showed statistically significant support across 1,872 bacterial species. *(confidence: high)*
- Ecological niche breadth (AlphaEarth embedding diversity) was the strongest predictor of mean metabolic pathway completeness, with a moderate positive correlation (r=0.392, p=7.1e-70). *(confidence: high)*
- Embedding variance was an even stronger predictor of pathway completeness (r=0.412, p=1.8e-77) than the composite niche breadth score. *(confidence: high)*
- Open pangenome species exhibited broader ecological niche breadth, a moderate positive correlation between pangenome openness and niche breadth (r=0.324, p=5.6e-47). *(confidence: high)*
- Pangenome openness correlated only weakly with metabolic pathway completeness across species (r=0.107, p=3.6e-06). *(confidence: medium)*
- Partial correlation and stratified analysis by genome-count bins could test whether the pangenome-niche-pathway relationships persist after controlling for sampling intensity. *(confidence: medium)*
- The three-stage GapMind aggregation pipeline (305M rows to 27.6M genome-pathway pairs to 293K genomes to 27.7K species) provides a reusable, well-optimized pattern for analyzing the 305M-row pathway table at scale. *(confidence: high)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Christopher Neely](../authors/0000-0002-2620-8948.md)

[Open the full report →](../../../projects/pangenome_pathway_geography/REPORT.md)

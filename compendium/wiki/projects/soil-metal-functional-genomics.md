# Soil Metal Functional Genomics

This project tested whether soil metal contamination shapes the functional gene repertoire of microbial communities across 51,748 samples spanning nine metals. A distance-based redundancy analysis found that metal concentrations alone explain 80% of the variance in community COG (Clusters of Orthologous Groups) profiles, with chromium and lead showing the strongest associations and copper enriching genes involved in membrane transport and energy metabolism. However, co-contamination by multiple metals confounds whether individual gene associations are metal-specific or reflect generic multi-metal stress responses, and effect sizes across the 2,355 significant associations remain to be systematically reported.

## Key findings

- All associations are observational and co-contamination by co-varying metals (Cr, Cu, Pb, Zn) in industrial soils confounds whether COG-metal associations are metal-specific or reflect a generic multi-metal stress response. *(confidence: high)*
- Effect sizes (Spearman rho) have not been systematically reported across the 2,355 associations, so many statistically significant hits may be biologically small. *(confidence: high)*
- Soil samples within a region share geology and land use, so spatial autocorrelation in COG-metal residuals should be tested with Moran's I and corrected via spatial eigenvector filtering if significant. *(confidence: medium)*
- The reported db-RDA R squared of 0.799 is conditional on project accession and may describe residual rather than total variance, so the unconditional R squared of metals alone must be reported alongside it. *(confidence: high)*
- With a 60% discovery rate across 3,915 non-independent tests, Benjamini-Hochberg FDR correction is anti-conservative under positive correlation among co-contaminating metals, so the true FDR is likely higher than reported. *(confidence: medium)*
- Soil metal concentrations are strongly associated with the functional gene content of co-located microbial communities and this relationship is not a statistical artefact of batch effects. *(confidence: medium)*
- The direction of COG associations with copper (energetic trade-offs and membrane transport enrichment) is consistent with known copper toxicity mechanisms in bacteria. *(confidence: medium)*
- A community-weighted Spearman analysis of 51,748 soil samples found 2,355 significant COG-metal associations (FDR < 0.05) across nine metals. *(confidence: high)*
- A distance-based RDA reports R squared of 0.799 (p = 0.005), indicating metal concentrations explain 80% of variance in community COG profiles after conditioning on batch/project effects. *(confidence: medium)*
- Biome-stratified PGLS shows soil, marine, and wastewater communities have distinct metal-COG relationships, indicating environment-specific functional responses rather than a universal resistance programme. *(confidence: medium)*
- Chromium and lead drive the strongest COG signals, with transporters (ABC, RND) and biosynthesis genes dominating the top associations. *(confidence: medium)*
- Copper-specific analysis of 116 significant COGs shows positive enrichment of cell division and nucleotide transport alongside negative associations with energy production, suggesting energetic trade-offs under copper stress. *(confidence: medium)*
- Classifying each significant COG into metal resistance, oxidative stress, membrane remodelling, energy metabolism, or unknown categories would provide biological interpretation beyond the correlations. *(confidence: medium)*
- The copper analysis uses a 10 km proximity criterion to match samples to KBase genomes, and a sensitivity analysis at 5 km and 20 km thresholds is needed before COG-copper associations can be attributed to the measured sites. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Heather MacGregor](../authors/heather-macgregor.md)

[Open the full report →](../../../projects/soil_metal_functional_genomics/REPORT.md)

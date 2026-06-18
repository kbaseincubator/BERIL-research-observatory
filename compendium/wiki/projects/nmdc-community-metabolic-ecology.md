# Nmdc Community Metabolic Ecology

This project tested whether the Black Queen Hypothesis—that microbial communities lose expensive biosynthetic genes when their environment reliably supplies the metabolites—operates at environmental community scale by integrating GapMind pangenome pathway completeness with NMDC metabolomics across 220 soil and freshwater samples. The analysis revealed consistent Black Queen dynamics: 11 of 13 amino acid biosynthesis pathways showed negative correlations between community pathway completeness and ambient metabolite abundance (p = 0.011), with leucine and arginine reaching FDR significance, and found that carbon utilization capacity is the primary axis differentiating community metabolic type between soil and freshwater ecosystems. This work demonstrates the first scalable integration of pangenome pathway prediction with environmental metabolomics, establishing that metabolic gene content aggregates into meaningful ecosystem-level signals.

## Key findings

- Abiotic features such as pH, temperature, and total organic carbon were entirely absent for the 174-sample analysis matrix, preventing partial correlation tests controlling for environmental gradients that could confound the results. *(confidence: high)*
- All 33 Freshwater samples lacked paired metabolomics in NMDC, so the Black Queen test is effectively a soil-only test and whether the dynamics operate in freshwater communities at the same scale is untested. *(confidence: high)*
- GapMind pathway completeness indicates whether biosynthesis genes are present, not whether they are actively expressed, so transcriptomic data would be needed to determine whether expressed biosynthesis correlates more strongly with metabolite pools. *(confidence: high)*
- Carbon utilization pathways, not amino acid pathways, load almost entirely on PC1, suggesting carbon substrate availability is the primary axis differentiating ecosystem metabolic type at the community level. *(confidence: medium)*
- The two FDR-significant Black Queen pathways, leucine and arginine, are both energetically expensive to synthesise, consistent with the prediction that costly biosynthetic functions are most likely to be lost when environmental supply is reliable. *(confidence: medium)*
- This is the first application of GapMind community-weighted pathway completeness scores to predict environmental metabolomics across a large cross-habitat NMDC dataset, integrating 305M GapMind records with NMDC multi-omics for 220 samples. *(confidence: medium)*
- Across 13 testable amino acid biosynthesis pathways, 11 (85%) showed negative correlations between community pathway completeness and ambient amino acid metabolite intensity, the direction predicted by the Black Queen Hypothesis (binomial sign test p = 0.011). *(confidence: medium)*
- Leucine and arginine biosynthesis were the two amino acid pathways reaching FDR significance, both showing negative completeness-vs-metabolite correlations (leucine r = -0.390, q = 0.022; arginine r = -0.297, q = 0.049). *(confidence: high)*
- PCA of the 220-sample x 80-pathway community completeness matrix captured 49.4% of variance in PC1, with Soil and Freshwater communities occupying nearly non-overlapping regions of PC space (Kruskal-Wallis p < 0.0001). *(confidence: high)*
- Per-pathway Kruskal-Wallis tests showed that 17 of 18 amino acid pathways have significantly different community completeness levels across ecosystem types, with only tyrosine not significantly differentiated. *(confidence: high)*
- The Black Queen signal is robust to sensitivity checks: it is unchanged when restricted to Soil-ecosystem samples, and the H1 dataset is effectively single-study (95% of samples from one NMDC study), so cross-study protocol heterogeneity is not a confounder for leucine. *(confidence: medium)*
- The NMDC-to-GTDB taxonomy bridge achieved a mean coverage of 94.6% across all 220 samples, with 92% of samples mapping at least 85% of community abundance to GTDB pangenome species. *(confidence: high)*
- Obtaining or generating metabolomics data for the 33 Freshwater NMDC samples would allow a direct test of whether Black Queen dynamics differ between aquatic and terrestrial communities. *(confidence: medium)*
- Pairing metatranscriptomics with metabolomics for a subset of NMDC samples would allow comparison of expressed pathway completeness versus genomic potential versus metabolite abundance, directly testing whether expression drives the Black Queen signal. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Christopher Neely](../authors/0000-0002-2620-8948.md)

[Open the full report →](../../../projects/nmdc_community_metabolic_ecology/REPORT.md)

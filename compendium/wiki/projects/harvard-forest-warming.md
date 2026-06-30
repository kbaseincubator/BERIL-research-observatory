# Harvard Forest Warming

This 25-year soil warming experiment at Harvard Forest Barre Woods investigated whether microbial transcripts shift more than genomic DNA in response to sustained +5°C heating—testing whether fast regulatory responses precede slower community turnover. Instead, DNA and RNA functional gene pools responded comparably (~11–13% explained variance for treatment), while specific carbon-cycling pathways emerged as warming signatures: methanotrophy genes (pmoA/pmoB) upregulated across both soil horizons and the glyoxylate cycle activated in heated mineral soils, suggesting that after 25 years, the community has compositionally reorganized around warming-selected lineages with distinct carbon-utilization strategies.

## Key findings

- All samples come from a single timepoint (2017-05-24) and small omics cohorts (n=28 metagenome, n=39 metatranscriptome), limiting per-KO FDR power and precluding detection of seasonal effects. *(confidence: high)*
- Coverage is unbalanced because the NMDC pipeline did not produce metagenomes for organic-direct samples, which confounds horizon with incubation and drives the H1 sensitivity caveat. *(confidence: high)*
- Metatranscriptome KO counts are transcript-pool composition from contig annotations rather than TPM-quantified expression and are biased by assembly quality. *(confidence: medium)*
- The abiotic_features table is all zeros for these samples, leaving the +5C treatment label as the only environmental contrast with no in-lakehouse soil temperature, pH, or nitrogen. *(confidence: high)*
- This is the first explicit paired-sample comparison of DNA-pool and RNA-pool warming response variance at Harvard Forest, showing the apparent DNA-vs-RNA imbalance is largely a horizon-by-incubation artifact. *(confidence: medium)*
- After 25 years of +5C warming the soil community shows a real but modest compositional shift, with Actinobacteria up and Acidobacteria down, reproducing the published signal for this site. *(confidence: high)*
- Curated C-cycling KOs are significantly enriched among heated-up genes in the DNA-organic samples (Fisher OR=2.78, p=0.042), partially supporting the carbon-degradation hypothesis. *(confidence: medium)*
- Heated mineral soils have significantly fewer detectable metabolites than controls (155 vs 167 ChEBI per sample, MW p=0.012), consistent with faster substrate turnover under warming. *(confidence: medium)*
- Methanotrophy genes pmoA/pmoB are upregulated in heated soils across both horizons and the glyoxylate cycle is upregulated in heated mineral soil, identifying specific carbon-cycling warming responses. *(confidence: medium)*
- Most warming responses are horizon-specific, with roughly 39% of DNA KOs being organic-only, mineral-only, or sign-flipping between horizons. *(confidence: high)*
- The DNA and RNA functional pools show comparable treatment R2 (10-13%) once a horizon-by-incubation confound is removed, so the transcript pool is not more warming-sensitive than the genome pool. *(confidence: high)*
- Adding the excluded nmdc_arkin quantitative layers (NOM, metabolomics, proteomics) would strengthen the carbon-cycling findings with direct soil organic matter chemistry. *(confidence: medium)*
- Linking to other NMDC warming studies (SPRUCE peatland and Alaskan permafrost thaw) could test whether the methanotrophy-up signature is reproducible across sites. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)

## Data

- [Nmdc Arkin](../data/nmdc-arkin.md)

## Authors

- [Chris Mungall](../authors/0000-0002-6601-2165.md)

[Open the full report →](../../../projects/harvard_forest_warming/REPORT.md)

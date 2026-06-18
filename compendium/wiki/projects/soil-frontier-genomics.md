# Soil Frontier Genomics

This project tested whether clay content shields soil microbiomes from industrial and geochemical stressors, and mapped genomic discovery gaps across global soil biomes. Across 5,441 soil samples, clay showed no protective effect on microbial functional potential at global scale, but the project identified forest and cropland soils as genomic frontiers—regions with high observed microbial diversity but sparse reference genome databases—and revealed a systematic discovery bias toward acidic soils in public genomic datasets.

## Key findings

- The Forest (902.36) vs Cropland (890.82) GDI difference is only 1.3% and without bootstrap confidence intervals these biomes are not meaningfully distinguishable, so the claim should be framed as jointly highest rather than a ranked ordering. *(confidence: high)*
- The GDI formula is a novel index without published precedent that conflates sampling gap and OTU richness into one number potentially dominated by the richness term, so separate reporting of richness and completeness would be more interpretable. *(confidence: high)*
- The negative out-of-sample R² diagnosis is incomplete because distributional shift, outlier leverage, and genuine unpredictability have not been distinguished, and only true unpredictability supports a strong null result interpretation. *(confidence: high)*
- The GDI results reveal a systematic alkaline-soil sampling gap in public genomic datasets, with implications for any study drawing functional inferences from genome reference databases in forest and cropland biomes. *(confidence: medium)*
- The clay shield hypothesis is not supported at global scale, with the functional potential variable being unpredictable from measured stressors likely due to spatial autocorrelation, batch effects, and unmeasured confounders. *(confidence: medium)*
- Across 5,441 soil samples, clay content does not detectably buffer industrial or geochemical stress effects on microbial functional potential at global scale. *(confidence: high)*
- All three predictive model families (soil/climate, geochemical, industrial) achieve negative out-of-sample R², meaning they predict microbial functional potential worse than the training mean. *(confidence: high)*
- Clay appears as a consistent model feature (importance ≈ 0.14) but does not improve predictive accuracy in high-clay soils relative to low-clay soils. *(confidence: medium)*
- Forest (GDI 902.36) and Cropland (890.82) soils are the highest-GDI genomic frontiers, with high observed species richness but sparse genome reference databases, while Grassland (503.42) and Wetland (525.13) are relatively well-mapped. *(confidence: high)*
- Genomic databases show a +0.8 pH unit discovery bias toward acidic soils (frontier areas mean pH 6.74 vs mapped areas 5.94), leaving alkaline-specialist microbes disproportionately as dark matter. *(confidence: medium)*
- The Genomic Discovery Index (GDI = OTU Richness / (Mean Genome Completeness + 1)) quantifies the gap between observed microbial diversity and genomic reference coverage at 1° spatial bins. *(confidence: high)*
- The shield efficiency test shows low-clay and high-clay cross-validation R² differ by only 0.024 with a 95% confidence interval that includes zero, so the difference is not significant. *(confidence: high)*
- Computing Moran's I on the clay-model residuals and applying spatial correction before re-testing the shield efficiency contrast would establish whether the null result survives spatial autocorrelation. *(confidence: medium)*
- Controlling for the number of 16S samples in each pH bin before computing GDI would distinguish true assembly/annotation gaps from mere sampling-effort bias in the apparent pH discovery bias. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Heather MacGregor](../authors/heather-macgregor.md)

[Open the full report →](../../../projects/soil_frontier_genomics/REPORT.md)

# Bacdive Metal Validation

This project tested whether a genome-based metal tolerance prediction method (derived from cross-species fitness data and KEGG functional annotations) reflects real environmental patterns, by linking 42,227 BacDive strains to their isolation sources and predicted metal tolerance scores. Bacteria isolated from heavy metal contamination sites showed significantly higher predicted metal tolerance than environmental baseline (Cohen's d = +1.00, p=0.006), validating the prediction method and revealing a dose-dependent signal across contamination intensity.

## Key findings

- Metal utilization phenotype validation was inconclusive because only 24 BacDive metal utilization records matched scored strains, leaving the comparison underpowered. *(confidence: high)*
- Species-level matching is lossy: 56.6% of BacDive strains matched no GTDB species, primarily because GTDB uses different species boundaries than LPSN/DSMZ. *(confidence: high)*
- The metal tolerance signal is absent in Bacillota and Bacteroidota, so phylogenetic confounding is only partially controlled and may reflect both real biology and limited power. *(confidence: medium)*
- With only 10 heavy metal isolates, the analysis was at the detection limit (minimum detectable d about 0.93), so the observed d=1.00 effect size is imprecise. *(confidence: high)*
- Although metal tolerance genes are largely core within species, between-species variation in the total number of metal tolerance genes creates the environmental signal. *(confidence: medium)*
- The cross-database concordance between predicted metal tolerance and real isolation ecology validates the Metal Fitness Atlas's genome-based prediction method. *(confidence: high)*
- This larger BacDive analysis provides stronger evidence for the lab-metal-tolerance-to-field-abundance hypothesis than the prior suggestive Oak Ridge correlation, reflecting a gain in statistical power. *(confidence: medium)*
- Bacteria isolated from heavy metal contamination sites have predicted metal tolerance scores a full standard deviation (Cohen's d = +1.00, p=0.006) above the environmental baseline. *(confidence: high)*
- Contamination isolates retain significantly higher metal scores than environmental isolates within Pseudomonadota and Actinomycetota, showing the signal exceeds phylogenetic structure. *(confidence: high)*
- Host-associated bacteria score slightly higher than environmental ones (d=+0.14), contrary to prediction, likely due to genome-size confounding from large-genome Pseudomonadota pathogens. *(confidence: medium)*
- Species name matching linked 42,227 BacDive strains (43.4% of 97,334) to pangenome metal tolerance scores across 6,426 unique GTDB species. *(confidence: high)*
- The metal tolerance signal is dose-dependent across contamination intensity, with heavy metal sites scoring highest and industrial sites lowest. *(confidence: high)*
- Cross-referencing with ENIGMA community data at the Oak Ridge metal-contaminated site offers a complementary field validation of the prediction method. *(confidence: medium)*
- Matching BacDive GCA accessions directly to pangenome genome IDs via a Spark query could recover much of the 56.6% of currently unmatched strains. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/bacdive_metal_validation/REPORT.md)

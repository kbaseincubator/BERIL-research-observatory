# Bacdive Phenotype Metal Tolerance

This project tested whether classical bacterial phenotypes—such as Gram stain, oxygen tolerance, and enzyme activities—captured in the BacDive database predict a species' tolerance to toxic metals, using genome-based metal tolerance predictions and genetic data from 5,647 bacterial species. Although seven of ten phenotypes showed individual statistical significance, they added no predictive power beyond what bacterial taxonomy (phylum/class/order) already explained, a finding that starkly illustrates the pervasive problem of phylogenetic confounding in microbial ecology. The true predictor of metal tolerance proved to be the organism's genome-encoded metal resistance gene content, which alone outperformed all phenotype features combined and raised predictive accuracy to R² = 0.63.

## Key findings

- BacDive-to-pangenome linkage relies on species name matching that recovers only 38.4% of GTDB species (5,647/27,702), with GCA accession matching left unimplemented. *(confidence: high)*
- Metal tolerance scores from the Metal Fitness Atlas are genome-based predictions rather than direct metal tolerance measurements, so phenotype-score associations are ultimately phenotype-to-genome correlations. *(confidence: high)*
- The H2S production signal is unreliable because only 8 H2S-negative species are in the matched set, making the large effect size (d = -0.87) likely inflated by small-sample bias. *(confidence: high)*
- Classical microbiology phenotypes capture real biological differences in metal tolerance, but those differences are entirely explained by phylogenetic structure, making the phenotypes noisier proxies for taxonomy rather than independent predictors. *(confidence: high)*
- In twelve Fitness Browser organisms matched to BacDive, all urease-negative organisms are routinely tested against nickel, directly concordant with the pangenome-scale finding that urease status does not predict metal tolerance. *(confidence: low)*
- Catalase exhibits Simpson's paradox: the marginally positive overall effect (d = +0.10) reverses within every major class, where catalase-negative species score higher, exposing the apparent association as a between-class artifact. *(confidence: medium)*
- Classical BacDive phenotype features add no predictive power for bacterial metal tolerance beyond taxonomy, with the combined taxonomy-plus-phenotype model performing slightly worse than taxonomy alone (delta R-squared = -0.009). *(confidence: high)*
- Contrary to the prediction that urease-positive organisms tolerate nickel better, urease-positive species have significantly lower metal tolerance (d = -0.18, p < 1e-5), a reversal driven by lineage composition rather than nickel biology. *(confidence: medium)*
- Genome-encoded metal resistance gene content (n_metal_clusters from the Metal Fitness Atlas) is the true predictor of metal tolerance, raising the full model to R-squared = 0.63 and explaining more variance than all phenotype features combined. *(confidence: high)*
- Gram-negative species show the largest univariate phenotype effect on metal tolerance, scoring higher than Gram-positive species (Cohen's d = -0.61, p < 1e-60, n = 3,272 species). *(confidence: high)*
- SHAP importance from the full XGBoost model is dominated by taxonomic class/order codes and metal resistance gene count, while phenotype features contribute minimally once taxonomy is included. *(confidence: high)*
- Seven of ten BacDive phenotype features (Gram stain, oxidase, motility, urease, enzyme breadth, nitrate reduction, and catalase) are individually significant predictors of metal tolerance after FDR correction at q < 0.05. *(confidence: high)*
- The anaerobe-versus-aerobe difference in metal tolerance is negligible (d = -0.016, p = 0.55) despite 3,751 species with oxygen tolerance data, failing to support the hypothesis that redox lifestyle confers metal tolerance. *(confidence: high)*
- RB-TnSeq profiling of matched urease-positive and urease-negative strains under nickel versus other metals would directly test whether urease enables nickel-specific tolerance. *(confidence: medium)*
- Testing whether specific phenotypes predict tolerance to specific metals (e.g., catalase to copper, urease to nickel) using per-metal scores could recover signal masked by composite metal tolerance scores. *(confidence: medium)*

## Topics

- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/bacdive_phenotype_metal_tolerance/REPORT.md)

# Adp1 Triple Essentiality

This project compared three computational and experimental methods for predicting gene essentiality in *Acinetobacter baylyi* ADP1: flux balance analysis (FBA), knockout experiments, and RB-TnSeq fitness measurements, supplemented with proteomics validation. The central finding is that each method measures a distinct biological property—FBA captures metabolic necessity, complete gene deletion reveals lethality, transposon-based fitness measures growth cost under partial disruption, and protein expression correlates with essential function—meaning no single approach serves as an ground truth. Continuous fitness scores outperform binary classifications, and systematic gaps like aromatic degradation pathway under-prediction reveal opportunities to refine metabolic models by matching in silico assumptions to experimental conditions.

## Key findings

- Binary essentiality_fraction should not be used as an essentiality classifier because it performs worse than random against knockout truth (AUC=0.34-0.40), aggregating across too many diverse conditions. *(confidence: high)*
- Transposon insertion is not equivalent to gene deletion: some knockout-essential genes appear TnSeq-dispensable because partial or truncated protein function suffices, limiting RB-TnSeq as a lethality proxy. *(confidence: medium)*
- Knockout, FBA, RB-TnSeq, proteomics, and mutant growth assays each measure a distinct facet of gene importance (lethality, metabolic necessity, fitness cost, expression requirement, and condition-specific optimization), so no single method serves as ground truth. *(confidence: medium)*
- Across all genes, FBA shows moderate concordance with experimental knockout lethality (Cohen's kappa approximately 0.49, F1 approximately 0.62-0.67), making it a useful first-pass computational screen for essential genes. *(confidence: high)*
- Among 478 TnSeq-dispensable, triple-covered ADP1 genes, FBA essentiality class was not significantly associated with measured growth-defect status (chi-squared=0.93, p=0.63). *(confidence: high)*
- Aromatic degradation genes, including beta-ketoadipate pathway enzymes, are strongly enriched among FBA-discordant ADP1 genes (OR=9.70, q=0.012), revealing a systematic gap in the model's environmental assumptions. *(confidence: high)*
- Continuous RB-TnSeq fitness scores are the best predictor of gene essentiality in Acinetobacter baylyi ADP1 (AUC=0.70-0.73), whereas binary essentiality_fraction performs worse than random (AUC<0.5). *(confidence: high)*
- Only 7.9% (18/229) of knockout-essential ADP1 genes are flagged as essential by RB-TnSeq at the optimal threshold, with 211 KO-essential genes called TnSeq-dispensable and 293 KO-dispensable genes called TnSeq-essential. *(confidence: high)*
- Protein expression strongly correlates with essentiality (r=0.35, AUC=0.74), with essential ADP1 genes expressed about 6.5-fold higher than dispensable genes (Mann-Whitney p=9.91e-59). *(confidence: high)*
- RB-TnSeq systematically disagrees with knockout experiments across all tested thresholds (negative Cohen's kappa), capturing fitness cost rather than lethality. *(confidence: high)*
- The lack of association between FBA class and growth defects is robust to the growth-defect threshold, with chi-squared p>0.05 across Q10-Q35 cutoffs and a threshold-independent Kruskal-Wallis test also non-significant (H=1.67, p=0.43). *(confidence: high)*
- A machine-learning predictor integrating FBA, fitness, and proteomics may outperform any single method for predicting ADP1 gene essentiality. *(confidence: low)*
- Adding trace aromatic compounds to the FBA minimal-media definition could resolve the systematic discordance in beta-ketoadipate pathway genes and better match in silico to experimental conditions. *(confidence: medium)*

## Topics

- [Topic: Adp1 Model System](../topics/adp1-model-system.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/adp1_triple_essentiality/REPORT.md)

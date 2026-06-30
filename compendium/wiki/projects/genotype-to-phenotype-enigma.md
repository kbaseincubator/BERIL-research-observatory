# Genotype To Phenotype Enigma

This project sought to predict bacterial growth phenotypes directly from genome content for ENIGMA's subsurface field isolates, combining 46K training pairs across growth curves, Fitness Browser transposon screens, and exometabolomic data. The centerpiece result is that binary growth is mechanistically predictable on amino acids and nucleosides (AUC 0.78–0.93) through condition-specific catabolic genes like ribose transporters and aromatic-degradation enzymes, but only with sufficient training data: n=7 strains learns spurious genome-scale artifacts while n=46K pairs surfaces the correct biology. This identifies the sample-size threshold for genotype-to-phenotype inference and demonstrates that different analytical questions (growth capability vs. metabolite production) require fundamentally different features.

## Key findings

- Cross-dataset condition alignment is string-based, yielding only 42 molecular matches via normalized names; ChEBI-ID-based canonicalization would likely expand this to 60-80 matches and enlarge the anchor frame. *(confidence: medium)*
- Linking ENIGMA field isolates to reference databases by short strain identifiers is hazardous: names like MT20 matched unrelated NCBI organisms such as Streptococcus pneumoniae and injected 1,751 spurious clinical genomes into environmental profiles before being corrected with GTDB-Tk taxonomy. *(confidence: high)*
- Growth-predictive KOs across genera and metabolite-production-associated KOs within genus are essentially uncorrelated feature sets (Spearman rho=0.043) that answer different biological questions, yet gene content explains both when analyzed with the method appropriate to the sample size. *(confidence: medium)*
- Mechanistic, condition-specific genotype-to-phenotype prediction requires on the order of 10^4 training pairs: with n=7 strains the model learns genome-scale artifacts while at 46K pairs the same architecture surfaces condition-specific catabolic genes. *(confidence: high)*
- Top SHAP KOs show only 1.19x enrichment for significant Fitness Browser fitness effects over a random baseline, reflecting that gene presence across genera and gene essentiality within one strain are fundamentally different biological questions rather than indicating non-mechanistic features. *(confidence: medium)*
- A global pH-driven niche partition across 464K worldwide 16S samples explains local Oak Ridge co-occurrence, with the acid-tolerant Cluster B (Rhodanobacter-Ralstonia-Dyella) occupying environments averaging pH 5.4, about 1.35 units more acidic and 6.9 degrees C warmer than neutral-preferring Cluster A. *(confidence: high)*
- All ENIGMA Pseudomonas isolates belong to the environmental Pseudomonas_E (fluorescens/protegens) clade rather than the clinically dominant lineage, meaning these subsurface field isolates occupy environmental niches underrepresented in NCBI genome collections. *(confidence: medium)*
- Binary bacterial growth is predictable from KO gene presence/absence on amino acids (AUC 0.775) and nucleosides (0.780) and moderately on carbon sources (0.695), but is not predictable on metals, antibiotics, or nitrogen from KO content alone. *(confidence: high)*
- Continuous growth parameters (maximum growth rate, lag time, and yield) are not predictable from KO content or bulk genomic features under cross-genus holdout, a fundamental biological limitation because gene presence encodes metabolic capability rather than kinetic rate. *(confidence: high)*
- Multivariate GBDT fails to predict exometabolomic output at n=6 strains, but univariate per-metabolite point-biserial correlation recovers 940 strong gene-metabolite associations (454 production, 486 consumption) across all 62 variable metabolites. *(confidence: medium)*
- The ENIGMA growth-curve corpus of 27,632 curves across 123 strains aligns with Fitness Browser RB-TnSeq data through 486 strain-by-condition anchor pairs spanning 7 strains and 72 conditions where growth, gene fitness, and genome annotations coexist. *(confidence: high)*
- With 46K training pairs the full-corpus SHAP analysis surfaces condition-specific catabolic genes such as rbsC (K10440, ribose transporter), proP (K03762, proline/betaine transporter), and pcaB (K01857, protocatechuate cycloisomerase), the mechanistically correct transporters and enzymes for each substrate. *(confidence: high)*
- Field-relevance-weighted active learning proposes a concrete 50-experiment next round for ENIGMA prioritizing organic acids such as fumaric and melibionic acid, nitrate, and low-pH-relevant substrates where the model is least confident and Oak Ridge geochemistry matters most. *(confidence: medium)*
- Linking strain-isolation well coordinates to per-well uranium, nitrate, and metal concentrations available in CORAL bricks 10/80 would let the project test whether acid-tolerant Cluster B strains originate from higher-contamination wells locally, not just globally. *(confidence: low)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Enigma Coral](../data/enigma-coral.md)
- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/genotype_to_phenotype_enigma/REPORT.md)

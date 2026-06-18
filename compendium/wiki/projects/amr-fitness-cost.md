# Amr Fitness Cost

This project performed a pan-bacterial meta-analysis of fitness costs imposed by antimicrobial resistance genes, analyzing 27 million transposon fitness measurements across 25 diverse bacterial species from the Fitness Browser. Using genome-wide knockout fitness data, the team showed that resistance genes impose a small but universal metabolic cost (effect size +0.086) consistent across all 25 species and independent of resistance mechanism, reconciling why resistance costs are real enough to drive decline under stewardship yet small enough for resistance to persist long after antibiotic withdrawal.

## Key findings

- All 25 organisms are lab-adapted strains, so compensatory evolution during laboratory maintenance may have reduced measurable costs below what wild strains experience. *(confidence: high)*
- Because ~4.6% of AMR genes are putatively essential and absent from the fitness matrices, the +0.086 cost estimate is a lower bound if those censored genes are the most costly. *(confidence: medium)*
- Most Fitness Browser species have few genomes (median 9), making the >=95% prevalence threshold for core designation imprecise, so the core-versus-accessory null result should be interpreted cautiously for species with under 20 genomes. *(confidence: medium)*
- The absence of a core-versus-accessory cost difference suggests horizontal transfer preferentially captures genes already cost-optimized in the donor lineage, or that the receiving genome rapidly compensates. *(confidence: medium)*
- The fitness cost of resistance is real but small, reconciling the persistence of resistance long after antibiotic withdrawal with its measurable cost under stewardship. *(confidence: medium)*
- The uniform modest cost across mechanisms may represent an irreducible floor of metabolic overhead, with only AMR genes whose cost has been minimized through compensatory evolution persisting in these genomes. *(confidence: medium)*
- This is the first pan-bacterial meta-analysis of AMR fitness costs using genome-wide transposon fitness data, leveraging 27M fitness measurements across 25 diverse bacteria. *(confidence: medium)*
- AMR gene knockouts have systematically higher fitness than non-AMR gene knockouts under non-antibiotic conditions, with a pooled meta-analytic effect of +0.086 and all 25 of 25 organisms showing a positive shift. *(confidence: high)*
- Core (intrinsic) and accessory (acquired) AMR genes have virtually identical fitness distributions (mean -0.024 vs -0.024, Cohen's d = 0.002, MWU p = 0.33), refuting the prediction that recently acquired genes are costlier. *(confidence: high)*
- Only 4.6% of AMR genes were absent from the fitness matrices (putatively essential), substantially below the ~14% background essential rate, consistent with AMR genes being more dispensable than typical genes. *(confidence: high)*
- Resistance mechanism strongly predicts conservation status (chi-square = 69.3, p = 1.4e-13)-metal resistance genes are 44% accessory while efflux and enzymatic genes are overwhelmingly core-decoupling pangenome location from fitness cost. *(confidence: high)*
- The antibiotic-induced fitness flip is mechanism-dependent: broad-spectrum efflux genes flip significantly more strongly than narrow-spectrum enzymatic inactivation genes (+0.094 vs -0.001, MWU p = 0.007). *(confidence: high)*
- The baseline fitness cost of AMR genes does not vary by resistance mechanism (Kruskal-Wallis H = 0.65, p = 0.89), refuting the hypothesis that mechanism predicts cost. *(confidence: high)*
- Under any antibiotic, 57% of AMR genes show a fitness flip, becoming relatively more important when knocked out compared to non-antibiotic conditions (Wilcoxon p = 0.0001, N = 797). *(confidence: high)*
- The 144 metal resistance genes with fitness data could be cross-referenced against the metal_fitness_atlas project to test whether genes costly under standard conditions are protective under metal stress. *(confidence: medium)*
- The analysis could be scaled from 25 Fitness Browser organisms to all 293K BERDL genomes by predicting AMR cost from gene cluster conservation patterns. *(confidence: low)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/amr_fitness_cost/REPORT.md)

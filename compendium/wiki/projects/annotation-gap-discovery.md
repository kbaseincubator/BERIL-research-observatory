# Annotation Gap Discovery

This project sought to assign genes to gapfilled metabolic reactions across 14 bacteria by integrating five independent evidence streams: flux balance analysis error patterns, gene fitness data, pangenome conservation, pathway completeness scores, and sequence homology. By triangulating these complementary signals, the team resolved 47.8% of the 201 annotated gaps with confidence scoring—a substantial improvement over any single method (best alone: 34.8% via BLAST)—and identified annotation-resistant "dark reactions" as high-value targets for experimental enzyme discovery.

## Key findings

- FBA gene-knockout validation was inconclusive because models cannot grow on carbon-source minimal media without the gapfilled reactions, making single-gene knockout analysis circular. *(confidence: high)*
- Twelve of 14 organisms are Proteobacteria, limiting generalizability, and the sole Bacteroidetes (B. thetaiotaomicron) had the lowest resolution rate, suggesting the approach may be less effective for phylogenetically distant clades. *(confidence: high)*
- Leave-one-out cross-validation shows each evidence stream contributes uniquely, demonstrating that no single data type is sufficient to resolve metabolic annotation gaps. *(confidence: high)*
- This is the first systematic integration of five evidence types (gapfilling, fitness, pangenome, GapMind, and BLAST) to resolve metabolic annotation gaps across multiple organisms simultaneously. *(confidence: medium)*
- Baseline FBA across 574 organism-carbon source combinations gave 42.5% accuracy with high recall (86.5%) but low precision (42.5%), reflecting overly permissive draft models that over-predict growth. *(confidence: high)*
- DIAMOND BLAST against 328 Swiss-Prot exemplars yielded 154 hits, with high-confidence hits (>=30% identity, >=70% coverage, e-value <=1e-10) concentrated in branched-chain amino acid biosynthesis and polyamine metabolism reactions. *(confidence: medium)*
- EC-less "dark reactions" (50 of 201, 24.9%) were resolved only 16% of the time versus 58.3% for reactions with known EC numbers, making them the hardest annotation gaps. *(confidence: high)*
- GapMind pathway predictions partially corroborated gapfilling, flagging pathways as incomplete for many of the same carbon sources requiring gapfilling, though concordance was limited by GapMind's pathway-level granularity. *(confidence: medium)*
- Integrating five evidence types resolved 47.8% (96 of 201) of gapfilled enzymatic reaction-organism pairs with candidate genes, exceeding the pre-specified 30% threshold. *(confidence: high)*
- No single evidence stream resolved more than 35% of gaps; BLAST homology alone reached 34.8% while the full integrated pipeline added 13 percentage points to reach 47.8%. *(confidence: high)*
- Per-organism resolution rates varied 3.5-fold, from 20% in Bacteroides thetaiotaomicron to 71% in Klebsiella michiganensis, tracking reference-genome annotation quality and Fitness Browser coverage. *(confidence: high)*
- Two sequential branched-chain amino acid biosynthesis reactions (rxn02185 and rxn03436) were each resolved with high confidence in 9 of 14 organisms, with their co-resolution validating the triangulation approach. *(confidence: medium)*
- The 44 high-confidence gene-reaction assignments are directly testable via targeted gene knockouts such as CRISPRi, with rxn02185 and rxn03436 across 9 organisms as priority validation targets. *(confidence: medium)*
- The 50 EC-less gapfilled reactions and 105 unresolved pairs are high-value targets for computational enzyme prediction tools and experimental enzyme characterization. *(confidence: medium)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Janaka N. Edirisinghe](../authors/0000-0003-2493-234x.md)

[Open the full report →](../../../projects/annotation_gap_discovery/REPORT.md)
